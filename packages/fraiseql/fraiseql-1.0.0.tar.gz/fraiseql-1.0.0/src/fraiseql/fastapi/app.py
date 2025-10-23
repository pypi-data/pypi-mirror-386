"""FastAPI application factory for FraiseQL."""

import logging
from collections.abc import Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from typing import Any

import psycopg_pool
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from fraiseql.auth.auth0 import Auth0Config
from fraiseql.auth.base import AuthProvider
from fraiseql.fastapi.config import FraiseQLConfig
from fraiseql.fastapi.dependencies import (
    get_db_pool,
    set_auth_provider,
    set_db_pool,
    set_fraiseql_config,
)
from fraiseql.fastapi.routers import create_graphql_router
from fraiseql.fastapi.turbo import TurboRegistry
from fraiseql.gql.schema_builder import build_fraiseql_schema
from fraiseql.utils import normalize_database_url

logger = logging.getLogger(__name__)

# Global to store turbo registry for lifespan access
_global_turbo_registry = None


async def create_db_pool(database_url: str, **pool_kwargs: Any) -> psycopg_pool.AsyncConnectionPool:
    """Create async database connection pool with custom type handling."""

    # Configure how psycopg3 handles PostgreSQL types for each connection
    async def configure_types(conn):
        """Configure type adapters to keep dates as strings."""
        # Import here to avoid circular imports
        from psycopg.adapt import Loader

        # Create a custom loader that returns the raw text value
        class TextLoader(Loader):
            def load(self, data):
                # Return the raw text representation from PostgreSQL
                return data.decode("utf-8") if isinstance(data, bytes) else data

        # Register text loaders for date/time types
        # This prevents automatic conversion to Python date/datetime objects
        conn.adapters.register_loader("date", TextLoader)
        conn.adapters.register_loader("timestamp", TextLoader)
        conn.adapters.register_loader("timestamptz", TextLoader)
        conn.adapters.register_loader("time", TextLoader)
        conn.adapters.register_loader("timetz", TextLoader)

    async def check_connection(conn):
        """Validate connection is alive before reuse.

        This prevents using connections that were terminated externally
        (e.g., by pg_terminate_backend() during database reseeding).

        Critical for multi-worker uvicorn setups where database connections
        can be terminated while workers are still running.

        See: https://github.com/fraiseql/fraiseql/issues/85
        """
        try:
            await conn.execute("SELECT 1")
        except Exception:
            # Connection is dead, raise to signal pool to create new connection
            logger.debug("Connection check failed, pool will create new connection")
            raise

    # Create pool with the configure callback
    # Use open=False to avoid deprecation warning in psycopg 3.2+
    pool = psycopg_pool.AsyncConnectionPool(
        database_url,
        configure=configure_types,
        check=check_connection,  # Validate connections before reuse
        open=False,  # Don't open in constructor to avoid deprecation warning
        **pool_kwargs,
    )

    # Open the pool explicitly as recommended
    await pool.open()

    return pool


def create_fraiseql_app(
    *,
    # Required configuration
    database_url: str | None = None,
    # Schema configuration
    types: Sequence[type] = (),
    mutations: Sequence[Callable[..., Any]] = (),
    queries: Sequence[type] = (),
    # Optional configuration
    config: FraiseQLConfig | None = None,
    auth: Auth0Config | AuthProvider | None = None,
    context_getter: Callable[[Request], Awaitable[dict[str, Any]]] | None = None,
    lifespan: Callable[[FastAPI], Any] | None = None,
    # App configuration
    title: str | None = None,
    version: str | None = None,
    description: str | None = None,
    # Environment
    production: bool = False,
    # Development auth configuration
    dev_auth_username: str | None = None,
    dev_auth_password: str | None = None,
    # FastAPI app to extend (optional)
    app: FastAPI | None = None,
) -> FastAPI:
    """Create a FastAPI application with FraiseQL GraphQL endpoint.

    Args:
        database_url: PostgreSQL connection URL
        types: Sequence of FraiseQL types to register
        mutations: Sequence of mutation resolver functions
        queries: Sequence of query types (if not using default QueryRoot)
        config: Full configuration object (overrides other params)
        auth: Authentication configuration or provider
        context_getter: Optional async function to build GraphQL context from request
        lifespan: Optional custom lifespan context manager for the FastAPI app
        title: API title
        version: API version
        description: API description
        production: Whether to use production optimizations
        dev_auth_username: Override username for development auth (defaults to env var or "admin")
        dev_auth_password: Override password for development auth (defaults to env var)
        app: Existing FastAPI app to extend (creates new if None)

    Returns:
        Configured FastAPI application

    Example:
        ```python
        from fraiseql.fastapi import create_fraiseql_app
        from fraiseql.auth import Auth0Config
        import my_models
        import my_mutations

        app = create_fraiseql_app(
            database_url="postgresql://localhost/mydb",
            types=[my_models.User, my_models.Post],
            mutations=[my_mutations.create_user],
            auth=Auth0Config(
                domain="myapp.auth0.com",
                api_identifier="https://api.myapp.com"
            ),
            production=True
        )
        ```
    """
    # Create or get config
    if config is None:
        # Build config kwargs, only including explicitly provided values
        # This allows environment variables to be loaded for unprovided fields
        # Normalize database URL to handle both formats
        normalized_url = normalize_database_url(database_url or "postgresql://localhost/fraiseql")
        config_kwargs: dict[str, Any] = {
            "database_url": normalized_url,
            "environment": "production" if production else "development",
        }

        # Only add fields if they differ from defaults or are explicitly provided
        if title is not None:
            config_kwargs["app_name"] = title
        if version is not None:
            config_kwargs["app_version"] = version
        if dev_auth_username is not None:
            config_kwargs["dev_auth_username"] = dev_auth_username
        if dev_auth_password is not None:
            config_kwargs["dev_auth_password"] = dev_auth_password

        config = FraiseQLConfig(**config_kwargs)

    # Setup authentication first so it's available for lifespan
    auth_provider: AuthProvider | None = None
    if auth is not None:
        if isinstance(auth, Auth0Config):
            auth_provider = auth.create_provider()
        elif isinstance(auth, AuthProvider):
            auth_provider = auth
        else:
            msg = "auth must be Auth0Config or AuthProvider instance"
            raise ValueError(msg)
        # If auth is provided, enable authentication
        config.auth_enabled = True
    elif config.auth_enabled and config.auth_provider == "auth0":
        # Auto-create Auth0 provider from config if not explicitly provided
        if not config.auth0_domain or not config.auth0_api_identifier:
            msg = "auth0_domain and auth0_api_identifier must be set when using auth0 provider"
            raise ValueError(msg)

        from fraiseql.auth.auth0 import Auth0Provider

        auth_provider = Auth0Provider(
            domain=config.auth0_domain,
            api_identifier=config.auth0_api_identifier,
            algorithms=config.auth0_algorithms,
        )

    set_auth_provider(auth_provider)
    set_fraiseql_config(config)

    # Create lifespan context manager for the app
    if lifespan is None:
        # Use default lifespan that manages database pool
        @asynccontextmanager
        async def default_lifespan(app: FastAPI):
            """Manage application lifecycle."""
            # Startup
            pool = await create_db_pool(
                str(config.database_url),
                min_size=1,
                max_size=config.database_pool_size,
                timeout=config.database_pool_timeout,
            )
            set_db_pool(pool)

            yield

            # Shutdown
            pool_to_close = get_db_pool()
            if pool_to_close:
                await pool_to_close.close()

            if auth_provider and hasattr(auth_provider, "close"):
                await auth_provider.close()

        lifespan_to_use = default_lifespan
    else:
        # Wrap user's lifespan to ensure database pool is still managed
        @asynccontextmanager
        async def wrapped_lifespan(app: FastAPI):
            """Wrap user lifespan with FraiseQL resource management."""
            # Startup - initialize database pool
            pool = await create_db_pool(
                str(config.database_url),
                min_size=1,
                max_size=config.database_pool_size,
                timeout=config.database_pool_timeout,
            )
            set_db_pool(pool)

            # Call user's lifespan
            async with lifespan(app):
                yield

            # Shutdown - cleanup our resources
            pool_to_close = get_db_pool()
            if pool_to_close:
                await pool_to_close.close()

            if auth_provider and hasattr(auth_provider, "close"):
                await auth_provider.close()

        lifespan_to_use = wrapped_lifespan

    # Create or extend FastAPI app
    if app is None:
        app = FastAPI(
            title=config.app_name,
            version=config.app_version,
            description=description or "GraphQL API powered by FraiseQL",
            lifespan=lifespan_to_use,
        )

    # Setup CORS if enabled
    if config.cors_enabled:
        # Log warning if using wildcard in production
        if production and "*" in config.cors_origins:
            logger.warning(
                "CORS enabled with wildcard origin (*) in production. "
                "This may cause conflicts with reverse proxies that handle CORS. "
                "Consider disabling CORS in FraiseQL when using a reverse proxy."
            )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.cors_origins,
            allow_credentials=True,
            allow_methods=config.cors_methods,
            allow_headers=config.cors_headers,
        )

    # Setup development authentication if enabled and not in production
    if not production and config.dev_auth_password:
        from fraiseql.fastapi.dev_auth import DevAuthMiddleware

        logger.warning(
            "Development authentication enabled with username: %s. "
            "This should NEVER be used in production!",
            config.dev_auth_username,
        )

        app.add_middleware(
            DevAuthMiddleware,
            username=config.dev_auth_username,
            password=config.dev_auth_password,
        )

    # Build GraphQL schema
    # Combine both types and queries - types define GraphQL types, queries define query functions
    all_query_types = list(types) + list(queries)
    schema = build_fraiseql_schema(
        query_types=all_query_types,
        mutation_resolvers=list(mutations),
        camel_case_fields=config.auto_camel_case,
    )

    # Create TurboRegistry if enabled (regardless of environment)
    turbo_registry = None
    # TurboRouter is always enabled for maximum performance
    if True:
        turbo_registry = TurboRegistry(max_size=config.turbo_router_cache_size)
        # Store TurboRegistry in app state for access in lifespan
        app.state.turbo_registry = turbo_registry
        # Also store globally for easier access
        global _global_turbo_registry
        _global_turbo_registry = turbo_registry

    # Create and mount GraphQL router
    graphql_router = create_graphql_router(
        schema=schema,
        config=config,
        auth_provider=auth_provider,
        context_getter=context_getter,
        turbo_registry=turbo_registry,
    )

    app.include_router(graphql_router)

    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "fraiseql"}

    return app


# Convenience function for creating a production app
def create_production_app(**kwargs: Any) -> FastAPI:
    """Create a production-optimized FraiseQL app.

    This is equivalent to create_fraiseql_app with production=True
    and additional production defaults.
    """
    kwargs.setdefault("production", True)

    # Override config for production
    if "config" in kwargs:
        kwargs["config"].environment = "production"
        kwargs["config"].enable_introspection = False
        kwargs["config"].enable_playground = False

    return create_fraiseql_app(**kwargs)


# Import to avoid circular dependency


def get_global_turbo_registry():
    """Get the global turbo registry if available."""
    return _global_turbo_registry
