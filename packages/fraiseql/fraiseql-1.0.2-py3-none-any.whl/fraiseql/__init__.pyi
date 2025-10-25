from typing import Any, Callable, Dict, List, Type, TypeVar, overload

from .mutations.error_config import MutationErrorConfig as MutationErrorConfig

_T = TypeVar("_T")
_F = TypeVar("_F", bound=Callable[..., Any])

# Core type decorators
@overload
def fraise_type_decorator(cls: Type[_T]) -> Type[_T]: ...
@overload
def fraise_type_decorator(
    *,
    sql_source: str | None = None,
    jsonb_column: str | None = None,
    implements: List[Type[Any]] | None = None,
    resolve_nested: bool = False,
) -> Callable[[Type[_T]], Type[_T]]: ...
def fraise_type_decorator(
    cls: Type[_T] | None = None,
    *,
    sql_source: str | None = None,
    jsonb_column: str | None = None,
    implements: List[Type[Any]] | None = None,
    resolve_nested: bool = False,
) -> Type[_T] | Callable[[Type[_T]], Type[_T]]: ...
@overload
def fraise_input_decorator(cls: Type[_T]) -> Type[_T]: ...
@overload
def fraise_input_decorator(
    *,
    description: str | None = None,
) -> Callable[[Type[_T]], Type[_T]]: ...
def fraise_input_decorator(
    cls: Type[_T] | None = None,
    *,
    description: str | None = None,
) -> Type[_T] | Callable[[Type[_T]], Type[_T]]: ...
def success(cls: Type[_T]) -> Type[_T]: ...
def failure(cls: Type[_T]) -> Type[_T]: ...
def result(cls: Type[_T]) -> Type[_T]: ...
def enum(cls: Type[_T]) -> Type[_T]: ...
def interface(cls: Type[_T]) -> Type[_T]: ...

# Query decorator
@overload
def query(func: _F) -> _F: ...
@overload
def query() -> Callable[[_F], _F]: ...
def query(func: _F | None = None) -> _F | Callable[[_F], _F]: ...

# Field decorator
@overload
def field(func: _F) -> _F: ...
@overload
def field(
    *,
    description: str | None = None,
    deprecation_reason: str | None = None,
) -> Callable[[_F], _F]: ...
def field(
    func: _F | None = None,
    *,
    description: str | None = None,
    deprecation_reason: str | None = None,
) -> _F | Callable[[_F], _F]: ...

# Dataloader field decorator
@overload
def dataloader_field(func: _F) -> _F: ...
@overload
def dataloader_field(
    *,
    loader_key: str | None = None,
    description: str | None = None,
) -> Callable[[_F], _F]: ...
def dataloader_field(
    func: _F | None = None,
    *,
    loader_key: str | None = None,
    description: str | None = None,
) -> _F | Callable[[_F], _F]: ...

# Mutation decorator
def mutation(
    *,
    function: str | None = None,
    schema: str = "graphql",
    context_params: Dict[str, str] | None = None,
    error_config: MutationErrorConfig | None = None,
) -> Callable[[Type[_T]], Type[_T]]: ...

# Subscription decorator
@overload
def subscription(func: _F) -> _F: ...
@overload
def subscription() -> Callable[[_F], _F]: ...
def subscription(func: _F | None = None) -> _F | Callable[[_F], _F]: ...

# Helper function for fields
def fraise_field(
    *,
    description: str | None = None,
    alias: str | None = None,
    deprecation_reason: str | None = None,
    default: Any = ...,
) -> Any: ...

# Scalar field types
class Date:
    def __init__(self, value: str | None = None) -> None: ...

class DateTime:
    def __init__(self, value: str | None = None) -> None: ...

class JSON:
    def __init__(self, value: Any = None) -> None: ...

class EmailAddress:
    def __init__(self, value: str | None = None) -> None: ...

class IpAddress:
    def __init__(self, value: str | None = None) -> None: ...

class MacAddress:
    def __init__(self, value: str | None = None) -> None: ...

class Port:
    def __init__(self, value: int | None = None) -> None: ...

class Hostname:
    def __init__(self, value: str | None = None) -> None: ...

# Generic types
class Connection:
    edges: List[Any]
    page_info: Any
    total_count: int | None

class Edge:
    node: Any
    cursor: str

class PageInfo:
    has_next_page: bool
    has_previous_page: bool
    start_cursor: str | None
    end_cursor: str | None

def create_connection(
    items: List[Any],
    *,
    first: int | None = None,
    after: str | None = None,
    last: int | None = None,
    before: str | None = None,
) -> Connection: ...

# CQRS classes
class CQRSRepository:
    def __init__(self, connection_or_pool: Any) -> None: ...
    async def find(
        self,
        view: str,
        filters: Dict[str, Any] | None = None,
        *,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | List[str] | None = None,
    ) -> List[Dict[str, Any]]: ...
    async def find_one(
        self,
        view: str,
        filters: Dict[str, Any] | None = None,
    ) -> Dict[str, Any] | None: ...
    async def execute_function(
        self,
        function_name: str,
        params: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]: ...

class CQRSExecutor:
    def __init__(self, repository: CQRSRepository) -> None: ...

# Schema builder
def build_fraiseql_schema(
    types: List[Type[Any]] | None = None,
    mutations: List[Type[Any]] | None = None,
    queries: List[Type[Any]] | None = None,
    subscriptions: List[Type[Any]] | None = None,
) -> Any: ...

# Error configurations
ALWAYS_DATA_CONFIG: MutationErrorConfig
DEFAULT_ERROR_CONFIG: MutationErrorConfig
STRICT_STATUS_CONFIG: MutationErrorConfig

# Constants
UNSET: Any

# Auth types (when available)
class AuthProvider: ...

class UserContext:
    user_id: str
    roles: List[str]
    permissions: List[str]

def requires_auth(
    func: _F | None = None,
    *,
    optional: bool = False,
) -> _F | Callable[[_F], _F]: ...
def requires_role(
    role: str,
    *,
    optional: bool = False,
) -> Callable[[_F], _F]: ...
def requires_permission(
    permission: str,
    *,
    optional: bool = False,
) -> Callable[[_F], _F]: ...

class Auth0Config:
    domain: str
    audience: str
    algorithms: List[str]

class Auth0Provider(AuthProvider):
    def __init__(self, config: Auth0Config) -> None: ...

# FastAPI integration (when available)
try:
    from .fastapi import FraiseQLConfig as FraiseQLConfig
    from .fastapi import create_fraiseql_app as create_fraiseql_app
except ImportError:
    type FraiseQLConfig = None
    type CreateFraiseQLApp = None

# Aliases for backwards compatibility
fraise_type = fraise_type_decorator
fraise_input = fraise_input_decorator
fraise_enum = enum
fraise_interface = interface

# Core aliases
type = fraise_type  # noqa: A001
input = fraise_input  # noqa: A001

__version__: str

__all__ = [
    "ALWAYS_DATA_CONFIG",
    "DEFAULT_ERROR_CONFIG",
    "JSON",
    "STRICT_STATUS_CONFIG",
    # Constants
    "UNSET",
    "Auth0Config",
    "Auth0Provider",
    # Auth (optional)
    "AuthProvider",
    "CQRSExecutor",
    # CQRS
    "CQRSRepository",
    # Generic types
    "Connection",
    "CreateFraiseQLApp",
    # Scalar types
    "Date",
    "DateTime",
    "Edge",
    "EmailAddress",
    # FastAPI integration (optional)
    "FraiseQLConfig",
    "Hostname",
    "IpAddress",
    "MacAddress",
    # Error configs
    "MutationErrorConfig",
    "PageInfo",
    "Port",
    "UserContext",
    # Schema
    "build_fraiseql_schema",
    "create_connection",
    "dataloader_field",
    "enum",
    "failure",
    "field",
    "fraise_enum",
    "fraise_field",
    "fraise_input",
    "fraise_input_decorator",
    "fraise_interface",
    # Aliases
    "fraise_type",
    # Core decorators
    "fraise_type_decorator",
    "input",
    "interface",
    "mutation",
    "query",
    "requires_auth",
    "requires_permission",
    "requires_role",
    "result",
    "subscription",
    "success",
    "type",
]
