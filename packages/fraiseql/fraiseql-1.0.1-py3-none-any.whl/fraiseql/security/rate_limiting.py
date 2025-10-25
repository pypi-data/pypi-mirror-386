"""Rate limiting middleware for FraiseQL applications."""

import asyncio
import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from fraiseql.audit import get_security_logger


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimit:
    """Rate limit configuration."""

    requests: int
    window: int  # seconds
    burst: int | None = None  # for token bucket
    strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""

    path_pattern: str
    rate_limit: RateLimit
    key_func: Callable[[Request], str] | None = None
    exempt_func: Callable[[Request], bool] | None = None
    message: str | None = None


class RateLimitStore:
    """In-memory rate limit store with TTL."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, int]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> tuple[float, int]:
        """Get timestamp and count for key."""
        async with self._lock:
            return self._store.get(key, (0.0, 0))

    async def set(self, key: str, timestamp: float, count: int, ttl: int) -> None:
        """Set timestamp and count for key with TTL."""
        async with self._lock:
            self._store[key] = (timestamp, count)
            # Simple TTL cleanup - remove expired entries
            current_time = time.time()
            expired_keys = [k for k, (ts, _) in self._store.items() if current_time - ts > ttl]
            for expired_key in expired_keys:
                self._store.pop(expired_key, None)

    async def increment(self, key: str, window: int) -> tuple[float, int]:
        """Increment counter for key."""
        async with self._lock:
            current_time = time.time()
            timestamp, count = self._store.get(key, (current_time, 0))

            # Reset if window has passed
            if current_time - timestamp >= window:
                timestamp = current_time
                count = 0

            count += 1
            self._store[key] = (timestamp, count)
            return timestamp, count


class RedisRateLimitStore:
    """Redis-backed rate limit store."""

    def __init__(self, redis_client) -> None:
        self.redis = redis_client

    async def get(self, key: str) -> tuple[float, int]:
        """Get timestamp and count for key."""
        data = await self.redis.get(key)
        if not data:
            return 0.0, 0
        timestamp, count = json.loads(data)
        return timestamp, count

    async def set(self, key: str, timestamp: float, count: int, ttl: int) -> None:
        """Set timestamp and count for key with TTL."""
        data = json.dumps([timestamp, count])
        await self.redis.setex(key, ttl, data)

    async def increment(self, key: str, window: int) -> tuple[float, int]:
        """Increment counter for key using Redis pipeline."""
        current_time = time.time()

        # Use Redis pipeline for atomic operations
        async with self.redis.pipeline() as pipe:
            await pipe.multi()

            # Get current value
            data = await self.redis.get(key)

            if not data:
                timestamp = current_time
                count = 1
            else:
                timestamp, count = json.loads(data)

                # Reset if window has passed
                if current_time - timestamp >= window:
                    timestamp = current_time
                    count = 1
                else:
                    count += 1

            # Set new value
            data = json.dumps([timestamp, count])
            await pipe.setex(key, window, data)
            await pipe.execute()

            return timestamp, count


class GraphQLRateLimiter:
    """Rate limiter specifically for GraphQL operations."""

    def __init__(self, store: RateLimitStore | RedisRateLimitStore) -> None:
        self.store = store
        self.operation_limits = {
            "query": RateLimit(requests=100, window=60),
            "mutation": RateLimit(requests=20, window=60),
            "subscription": RateLimit(requests=10, window=60),
        }
        self.complexity_limits = {
            "low": RateLimit(requests=200, window=60),  # complexity < 50
            "medium": RateLimit(requests=100, window=60),  # complexity 50-200
            "high": RateLimit(requests=20, window=60),  # complexity > 200
        }

    def _extract_operation_info(self, request_body: dict) -> tuple[str, str | None, int]:
        """Extract operation type, name, and estimated complexity."""
        query = request_body.get("query", "")
        operation_name = request_body.get("operationName")

        # Simple operation type detection
        query_lower = query.lower().strip()
        if query_lower.startswith("mutation"):
            op_type = "mutation"
        elif query_lower.startswith("subscription"):
            op_type = "subscription"
        else:
            op_type = "query"

        # Estimate complexity (simple heuristic)
        complexity = self._estimate_complexity(query)

        return op_type, operation_name, complexity

    def _estimate_complexity(self, query: str) -> int:
        """Estimate query complexity with simple heuristics."""
        # Count nested braces as depth indicator
        depth = 0
        max_depth = 0
        for char in query:
            if char == "{":
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == "}":
                depth -= 1

        # Count field selections
        field_count = query.count("\n") + query.count(",")

        # Simple complexity score
        return max_depth * 10 + field_count

    def _get_complexity_tier(self, complexity: int) -> str:
        """Get complexity tier for rate limiting."""
        if complexity < 50:
            return "low"
        if complexity < 200:
            return "medium"
        return "high"

    async def check_graphql_limits(
        self,
        request: Request,
        request_body: dict,
    ) -> JSONResponse | None:
        """Check GraphQL-specific rate limits."""
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)

        # Extract operation info
        op_type, op_name, complexity = self._extract_operation_info(request_body)
        complexity_tier = self._get_complexity_tier(complexity)

        # Check operation type limit
        op_key = f"graphql:op:{op_type}:{user_id or client_ip}"
        op_limit = self.operation_limits[op_type]

        if await self._check_limit(op_key, op_limit):
            # Log rate limit violation
            security_logger = get_security_logger()
            security_logger.log_rate_limit_exceeded(
                ip_address=client_ip,
                endpoint=f"/graphql:{op_type}",
                limit=op_limit.requests,
                window=f"{op_limit.window}s",
                user_id=user_id,
                metadata={
                    "operation_type": op_type,
                    "operation_name": op_name,
                    "complexity": complexity,
                },
            )

            return self._create_error_response(
                f"Rate limit exceeded for {op_type} operations",
                op_limit,
            )

        # Check complexity-based limit
        complexity_key = f"graphql:complexity:{complexity_tier}:{user_id or client_ip}"
        complexity_limit = self.complexity_limits[complexity_tier]

        if await self._check_limit(complexity_key, complexity_limit):
            # Log complexity-based rate limit
            security_logger = get_security_logger()
            security_logger.log_rate_limit_exceeded(
                ip_address=client_ip,
                endpoint=f"/graphql:complexity:{complexity_tier}",
                limit=complexity_limit.requests,
                window=f"{complexity_limit.window}s",
                user_id=user_id,
                metadata={
                    "complexity_tier": complexity_tier,
                    "complexity_score": complexity,
                    "operation_type": op_type,
                },
            )

            return self._create_error_response(
                f"Rate limit exceeded for {complexity_tier} complexity queries",
                complexity_limit,
            )

        return None

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _get_user_id(self, request: Request) -> str | None:
        """Extract user ID from request context."""
        # Try to get from request state (set by auth middleware)
        return getattr(request.state, "user_id", None)

    async def _check_limit(self, key: str, rate_limit: RateLimit) -> bool:
        """Check if rate limit is exceeded."""
        _timestamp, count = await self.store.increment(key, rate_limit.window)
        return count > rate_limit.requests

    def _create_error_response(self, message: str, rate_limit: RateLimit) -> JSONResponse:
        """Create rate limit error response."""
        return JSONResponse(
            status_code=429,
            content={
                "errors": [
                    {
                        "message": message,
                        "extensions": {
                            "code": "RATE_LIMITED",
                            "limit": rate_limit.requests,
                            "window": rate_limit.window,
                        },
                    },
                ],
            },
            headers={
                "Retry-After": str(rate_limit.window),
                "X-RateLimit-Limit": str(rate_limit.requests),
                "X-RateLimit-Window": str(rate_limit.window),
            },
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(
        self,
        app,
        store: RateLimitStore | RedisRateLimitStore | None = None,
        rules: list[RateLimitRule] | None = None,
        default_limit: RateLimit | None = None,
        graphql_path: str = "/graphql",
    ) -> None:
        super().__init__(app)
        self.store = store or RateLimitStore()
        self.rules = rules or []
        self.default_limit = default_limit or RateLimit(requests=100, window=60)
        self.graphql_path = graphql_path
        self.graphql_limiter = GraphQLRateLimiter(self.store)

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to requests."""
        # Check if request should be exempt
        if await self._is_exempt(request):
            return await call_next(request)

        # Special handling for GraphQL
        if request.url.path == self.graphql_path and request.method == "POST":
            return await self._handle_graphql_request(request, call_next)

        # Apply general rate limiting rules
        response = await self._apply_rate_limits(request)
        if response:
            return response

        return await call_next(request)

    async def _handle_graphql_request(self, request: Request, call_next):
        """Handle GraphQL-specific rate limiting."""
        try:
            # Parse request body
            body = await request.body()
            request_body = json.loads(body) if body else {}

            # Restore body for downstream processing
            async def receive():
                return {"type": "http.request", "body": body}

            request._receive = receive

            # Check GraphQL rate limits
            response = await self.graphql_limiter.check_graphql_limits(request, request_body)
            if response:
                return response

        except (json.JSONDecodeError, UnicodeDecodeError):
            # If we can't parse the body, fall back to general rate limiting
            pass

        # Apply general rate limits
        response = await self._apply_rate_limits(request)
        if response:
            return response

        return await call_next(request)

    async def _apply_rate_limits(self, request: Request) -> Response | None:
        """Apply rate limiting rules."""
        client_key = self._get_client_key(request)

        # Check specific rules first
        for rule in self.rules:
            if self._matches_pattern(request.url.path, rule.path_pattern):
                limit_key = f"{rule.path_pattern}:{client_key}"

                if await self._check_limit(limit_key, rule.rate_limit):
                    # Log rate limit violation
                    security_logger = get_security_logger()
                    user_id = getattr(request.state, "user_id", None)
                    security_logger.log_rate_limit_exceeded(
                        ip_address=self._get_client_ip(request),
                        endpoint=request.url.path,
                        limit=rule.rate_limit.requests,
                        window=f"{rule.rate_limit.window}s",
                        user_id=user_id,
                        metadata={
                            "rule_pattern": rule.path_pattern,
                            "method": request.method,
                        },
                    )

                    return self._create_error_response(
                        rule.message or "Rate limit exceeded",
                        rule.rate_limit,
                    )

        # Apply default limit
        default_key = f"default:{client_key}"
        if await self._check_limit(default_key, self.default_limit):
            # Log default rate limit violation
            security_logger = get_security_logger()
            user_id = getattr(request.state, "user_id", None)
            security_logger.log_rate_limit_exceeded(
                ip_address=self._get_client_ip(request),
                endpoint=request.url.path,
                limit=self.default_limit.requests,
                window=f"{self.default_limit.window}s",
                user_id=user_id,
                metadata={
                    "rule_type": "default",
                    "method": request.method,
                },
            )

            return self._create_error_response(
                "Rate limit exceeded",
                self.default_limit,
            )

        return None

    def _get_client_key(self, request: Request) -> str:
        """Generate client key for rate limiting."""
        # Try user ID first
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern (simple wildcard support)."""
        if "*" not in pattern:
            return path == pattern

        # Simple wildcard matching
        import fnmatch

        return fnmatch.fnmatch(path, pattern)

    async def _is_exempt(self, request: Request) -> bool:
        """Check if request is exempt from rate limiting."""
        # Health checks are typically exempt
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return True

        # Check rule-specific exemptions
        for rule in self.rules:
            if (
                rule.exempt_func
                and self._matches_pattern(request.url.path, rule.path_pattern)
                and rule.exempt_func(request)
            ):
                return True

        return False

    async def _check_limit(self, key: str, rate_limit: RateLimit) -> bool:
        """Check if rate limit is exceeded."""
        _timestamp, count = await self.store.increment(key, rate_limit.window)
        return count > rate_limit.requests

    def _create_error_response(self, message: str, rate_limit: RateLimit) -> JSONResponse:
        """Create rate limit error response."""
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate Limit Exceeded",
                "message": message,
                "retry_after": rate_limit.window,
            },
            headers={
                "Retry-After": str(rate_limit.window),
                "X-RateLimit-Limit": str(rate_limit.requests),
                "X-RateLimit-Window": str(rate_limit.window),
            },
        )


# Convenience functions for common configurations


def create_default_rate_limit_rules() -> list[RateLimitRule]:
    """Create default rate limiting rules."""
    return [
        # GraphQL endpoint - handled by GraphQLRateLimiter
        RateLimitRule(
            path_pattern="/graphql",
            rate_limit=RateLimit(requests=60, window=60),
            message="GraphQL rate limit exceeded",
        ),
        # Authentication endpoints
        RateLimitRule(
            path_pattern="/auth/*",
            rate_limit=RateLimit(requests=5, window=300),  # 5 requests per 5 minutes
            message="Authentication rate limit exceeded",
        ),
        # API endpoints
        RateLimitRule(
            path_pattern="/api/*",
            rate_limit=RateLimit(requests=100, window=60),
            message="API rate limit exceeded",
        ),
    ]


def setup_rate_limiting(
    app,
    redis_client=None,
    custom_rules: list[RateLimitRule] | None = None,
    default_limit: RateLimit | None = None,
) -> RateLimitMiddleware:
    """Set up rate limiting middleware with sensible defaults."""
    # Choose store based on Redis availability
    store = RedisRateLimitStore(redis_client) if redis_client else RateLimitStore()

    # Use custom rules or defaults
    rules = custom_rules or create_default_rate_limit_rules()

    # Create and add middleware
    middleware = RateLimitMiddleware(
        app=app,
        store=store,
        rules=rules,
        default_limit=default_limit,
    )

    app.add_middleware(RateLimitMiddleware, store=store, rules=rules, default_limit=default_limit)

    return middleware
