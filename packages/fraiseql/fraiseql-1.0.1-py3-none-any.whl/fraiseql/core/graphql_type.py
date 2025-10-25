"""GraphQL type conversions and query translation utilities for FraiseQL.

Converts Python FraiseQL input and output dataclasses to GraphQL types.
Supports:
- FraiseQL output types with SQL backing (via @fraise_type)
- FraiseQL input types (via @fraise_input)
- Scalar, optional, list types
- Enum types (via @fraise_enum)
- Caching for repeated conversions
"""

import inspect
import logging
import types
from enum import Enum
from types import UnionType
from typing import (
    Annotated,
    Any,
    List,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

from graphql import (
    GraphQLEnumType,
    GraphQLError,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLScalarType,
    GraphQLType,
    GraphQLUnionType,
)
from psycopg.sql import SQL, Composed

from fraiseql.config.schema_config import SchemaConfig
from fraiseql.core.translate_query import translate_query
from fraiseql.mutations.decorators import FraiseUnion
from fraiseql.sql.where_generator import DynamicType
from fraiseql.types.scalars.graphql_utils import convert_scalar_to_graphql
from fraiseql.types.scalars.json import JSONScalar, parse_json_value
from fraiseql.utils.annotations import (
    get_non_optional_type,
    is_optional_type,
    unwrap_annotated,
)
from fraiseql.utils.naming import snake_to_camel

_graphql_type_cache: dict[tuple[str, str], GraphQLType] = {}

DICT_ARG_LENGTH = 2

T = TypeVar("T", bound=type)

logger = logging.getLogger(__name__)


def _clean_docstring(docstring: str | None) -> str | None:
    """Clean and format a docstring for use in GraphQL schema descriptions.

    Uses Python's inspect.cleandoc to properly handle indentation and whitespace.
    """
    if not docstring:
        return None
    return inspect.cleandoc(docstring)


def _convert_fraise_union(
    typ: type[Any],
    annotation: FraiseUnion,
) -> GraphQLUnionType:
    origin = get_origin(typ)
    if origin not in (Union, UnionType):
        msg = f"FraiseUnion must wrap a union type, got: {typ!r} (origin: {origin})"
        raise TypeError(msg)

    args = get_args(typ)
    if not args:
        msg = f"FraiseUnion {annotation.name} has no union members"
        raise TypeError(msg)

    gql_object_types: list[GraphQLObjectType] = []

    for arg in args:
        gql = convert_type_to_graphql_output(arg)
        if not isinstance(gql, GraphQLObjectType):
            msg = (
                f"GraphQLUnionType can only include GraphQLObjectType members, "
                f"got: {type(gql)} from {arg!r}"
            )
            raise TypeError(msg)
        gql_object_types.append(gql)

    def resolve_union_type(obj: Any, info: Any, type_: Any) -> str | None:
        """Resolve the GraphQL type name from a Python object.

        This resolver handles both FraiseQL objects and serialized dictionaries
        created by the serialization fix (lines 151-153 in mutation_decorator.py).
        """
        # Handle FraiseQL objects (original behavior)
        if hasattr(obj, "__class__") and obj.__class__.__name__ != "dict":
            return obj.__class__.__name__

        # Handle serialized dictionaries from _clean_fraise_types
        if isinstance(obj, dict):
            # Strategy 1: Look for __typename field (GraphQL standard)
            if "__typename" in obj:
                return obj["__typename"]

            # Strategy 2: Infer type from dictionary structure
            # Look for patterns that indicate Success vs Error types
            if (
                "errors" in obj
                or "error_code" in obj
                or obj.get("status", "").startswith(("noop:", "blocked:", "failed:", "error"))
            ):
                # This looks like an error response
                # Find the Error type among union members
                for gql_type in gql_object_types:
                    if gql_type.name.endswith("Error"):
                        return gql_type.name
            else:
                # This looks like a success response
                # Find the Success type among union members
                for gql_type in gql_object_types:
                    if gql_type.name.endswith("Success"):
                        return gql_type.name

        # Fallback: return None and let GraphQL handle the error
        return None

    union_type = GraphQLUnionType(
        name=annotation.name,
        types=gql_object_types,
        resolve_type=resolve_union_type,
    )

    key = (annotation.name, typ.__module__)
    _graphql_type_cache[key] = union_type
    return union_type


def _convert_list_type(
    origin: type | None,
    args: tuple[Any, ...],
    *,
    is_input: bool,
) -> GraphQLList[Any]:
    if origin is list and args:
        inner = args[0]
        inner_gql_type = (
            convert_type_to_graphql_input(inner)
            if is_input
            else convert_type_to_graphql_output(inner)
        )
        return GraphQLList(inner_gql_type)

    msg = f"Unsupported list type: {origin}[{args}]"
    raise TypeError(msg)


def convert_type_to_graphql_input(
    typ: Any,
) -> GraphQLInputObjectType | GraphQLScalarType | GraphQLList[Any] | GraphQLEnumType:
    """Convert a FraiseQL input class or scalar into a GraphQLInputObjectType or scalar."""
    typ, _ = unwrap_annotated(typ)

    # Handle Optional[...] or | None types (e.g., JSONField | None)
    if is_optional_type(typ):
        typ = get_non_optional_type(typ)

    # Handle generic types like PaginationInput[T]
    origin = get_origin(typ)
    args = get_args(typ)
    if origin is not None and args:
        # Import here to avoid circular imports
        from fraiseql.types.generic import (
            get_or_create_concrete_type,
            is_fraise_generic,
        )

        if is_fraise_generic(typ):
            # Create concrete type from generic
            concrete_type = get_or_create_concrete_type(origin, args[0])
            return convert_type_to_graphql_input(concrete_type)

    # Handle FraiseQL input objects
    if (
        isinstance(typ, type)
        and hasattr(typ, "__fraiseql_definition__")
        and getattr(typ.__fraiseql_definition__, "kind", None) == "input"
    ):
        # Check cache first
        cache_key = (typ.__name__, typ.__module__)
        if cache_key in _graphql_type_cache:
            cached_type = _graphql_type_cache[cache_key]
            if isinstance(cached_type, GraphQLInputObjectType):
                return cached_type

        # Use the already collected fields from the decorator
        fields = getattr(typ, "__gql_fields__", {})
        type_hints = getattr(typ, "__gql_type_hints__", {})

        gql_fields = {}
        for name, field in fields.items():
            field_type = field.field_type or type_hints.get(name)
            if field_type is None:
                continue

            # Check for JSONScalar and validate data
            if field_type == JSONScalar:
                try:
                    # Assuming the field has some default value to validate
                    # Validate the field's default value
                    parse_json_value(getattr(typ, name, None))
                except GraphQLError as e:
                    msg = f"Invalid JSON value in field {name}: {e!s}"
                    raise GraphQLError(msg) from None

            # Use explicit graphql_name if provided, otherwise convert to camelCase if configured
            config = SchemaConfig.get_instance()
            if field.graphql_name:
                graphql_field_name = field.graphql_name
            else:
                graphql_field_name = snake_to_camel(name) if config.camel_case_fields else name

            gql_fields[graphql_field_name] = GraphQLInputField(
                convert_type_to_graphql_input(field_type),
            )

        gql_type = GraphQLInputObjectType(name=typ.__name__, fields=gql_fields)
        _graphql_type_cache[cache_key] = gql_type
        return gql_type

    # Handle list types like List[str]
    origin = get_origin(typ)
    if origin is list:
        inner = get_args(typ)[0]
        return GraphQLList(convert_type_to_graphql_input(inner))

    # Handle dict types (dict[str, Any], dict[str, str], etc.) as JSON
    if origin is dict:
        return convert_scalar_to_graphql(dict)

    # Handle enum types
    if isinstance(typ, type) and issubclass(typ, Enum):
        # Check if it has been decorated with @fraise_enum
        graphql_type = getattr(typ, "__graphql_type__", None)
        if isinstance(graphql_type, GraphQLEnumType):
            return graphql_type
        # If not decorated, raise error
        msg = (
            f"Enum {typ.__name__} must be decorated with @fraise_enum to be used in GraphQL schema"
        )
        raise TypeError(msg)

    # Handle raw list type (list without type parameters)
    if typ is list:
        # Default to list[str] for compatibility
        from graphql import GraphQLString

        return GraphQLList(GraphQLString)

    # Handle scalar types using the existing scalar mapping utility
    if isinstance(typ, type):
        try:
            return convert_scalar_to_graphql(typ)
        except TypeError:
            msg = f"Invalid type passed to convert_type_to_graphql_input: {typ}"
            raise TypeError(msg) from None

    msg = f"Invalid type passed to convert_type_to_graphql_input: {typ}"
    raise TypeError(msg)


def _extract_list_item_type(field_type: Any) -> Any | None:
    """Extract the item type from a list field type.

    Handles patterns like:
    - list[T] -> T
    - Optional[list[T]] -> T
    - list[T] | None -> T

    Returns None if the type is not a list or cannot be extracted.
    """
    actual_field_type = field_type
    field_origin = get_origin(field_type)

    # Handle Optional[list[T]] - extract list[T]
    if field_origin is Union or field_origin is types.UnionType:
        field_args = get_args(field_type)
        non_none_types = [t for t in field_args if t is not type(None)]
        if non_none_types and len(non_none_types) == 1:
            actual_field_type = non_none_types[0]

    # Now check if actual_field_type is list[T] and extract T
    if get_origin(actual_field_type) is list:
        list_args = get_args(actual_field_type)
        return list_args[0] if list_args else None

    return None


def convert_type_to_graphql_output(
    typ: Any,
) -> (
    GraphQLObjectType
    | GraphQLList[Any]
    | GraphQLScalarType
    | GraphQLUnionType
    | GraphQLInterfaceType
    | GraphQLEnumType
):
    """Convert a FraiseQL output type to a corresponding GraphQL output type."""
    # Handle Annotated[T, ...]
    if get_origin(typ) is Annotated:
        base_type, *annotations = get_args(typ)
        for annotation in annotations:
            if isinstance(annotation, FraiseUnion):
                return _convert_fraise_union(base_type, annotation)
        typ = base_type

    # Handle Optional[T] (e.g., T | None)
    if is_optional_type(typ):
        return convert_type_to_graphql_output(get_non_optional_type(typ))

    # Handle generic types like Connection[Post], Edge[User], etc.
    origin = get_origin(typ)
    args = get_args(typ)
    if origin is not None and args:
        # Import here to avoid circular imports
        from fraiseql.types.generic import (
            get_or_create_concrete_type,
            is_fraise_generic,
        )

        if is_fraise_generic(typ):
            # Create concrete type from generic (e.g., Connection[Post] -> ConnectionPost)
            concrete_type = get_or_create_concrete_type(origin, args[0])
            return convert_type_to_graphql_output(concrete_type)

    # Disallow plain Union/UnionType
    if get_origin(typ) in (Union, UnionType):
        msg = "Use a FraiseUnion wrapper for result unions, not plain Union"
        raise TypeError(msg)

    # Handle list types
    if get_origin(typ) is list:
        (inner_type,) = get_args(typ)
        inner_gql_type = convert_type_to_graphql_output(inner_type)
        return GraphQLList(inner_gql_type)

    # Handle dict types (dict[str, Any], dict[str, str], etc.) as JSON
    if get_origin(typ) is dict:
        return convert_scalar_to_graphql(dict)

    # Handle Any as JSON scalar
    if typ == Any or str(typ) == "typing.Any":
        return convert_scalar_to_graphql(dict)

    # Handle enum types
    if isinstance(typ, type) and issubclass(typ, Enum):
        # Check if it has been decorated with @fraise_enum
        graphql_type = getattr(typ, "__graphql_type__", None)
        if isinstance(graphql_type, GraphQLEnumType):
            return graphql_type
        # If not decorated, raise error
        msg = (
            f"Enum {typ.__name__} must be decorated with @fraise_enum to be used in GraphQL schema"
        )
        raise TypeError(msg)

    # Handle built-in scalar types with caching
    try:
        # Check cache first for scalar types
        if isinstance(typ, type):
            key = (f"scalar_{typ.__name__}", typ.__module__)
            if key in _graphql_type_cache:
                return cast("GraphQLScalarType", _graphql_type_cache[key])

        scalar_gql = convert_scalar_to_graphql(typ)

        # Cache scalar types to prevent duplicate registrations
        if isinstance(typ, type):
            _graphql_type_cache[key] = scalar_gql

        return scalar_gql
    except TypeError:
        pass  # Not a scalar — continue

    # Cache based on name/module for user-defined types
    if isinstance(typ, type):
        key = (typ.__name__, typ.__module__)
        if key in _graphql_type_cache:
            return cast(
                "GraphQLObjectType | GraphQLList[Any] | GraphQLScalarType | "
                "GraphQLUnionType | GraphQLInterfaceType",
                _graphql_type_cache[key],
            )

        # Handle FraiseQL object-like types
        if hasattr(typ, "__fraiseql_definition__"):
            definition = typ.__fraiseql_definition__
            if definition.kind in {"type", "success", "failure", "output"}:
                # Use the already collected fields from the decorator
                fields = getattr(typ, "__gql_fields__", {})
                type_hints = getattr(typ, "__gql_type_hints__", {})

                gql_fields = {}
                for name, field in fields.items():
                    field_type = field.field_type or type_hints.get(name)
                    if field_type is not None:
                        # Check if we should use enhanced resolver for where filtering support
                        # This takes priority over the standard nested resolver
                        if (
                            hasattr(field, "supports_where_filtering")
                            and field.supports_where_filtering
                        ):
                            # Use enhanced resolver with where parameter support
                            from fraiseql.core.nested_field_resolver import (
                                create_nested_array_field_resolver_with_where,
                            )

                            enhanced_resolver = create_nested_array_field_resolver_with_where(
                                name, field_type, field
                            )

                            # Wrap with enum serialization
                            from fraiseql.gql.enum_serializer import (
                                wrap_resolver_with_enum_serialization,
                            )

                            # Use explicit graphql_name if provided, otherwise convert to
                            # camelCase if configured
                            config = SchemaConfig.get_instance()
                            if field.graphql_name:
                                graphql_field_name = field.graphql_name
                            else:
                                graphql_field_name = (
                                    snake_to_camel(name) if config.camel_case_fields else name
                                )

                            # Create GraphQL field with where parameter
                            from graphql import GraphQLArgument

                            # Determine the WhereInput type
                            where_input_type = None
                            if field.where_input_type:
                                where_input_type = field.where_input_type
                            elif field.nested_where_type:
                                from fraiseql.sql.graphql_where_generator import (
                                    create_graphql_where_input,
                                )

                                where_input_type = create_graphql_where_input(
                                    field.nested_where_type
                                )

                            # Create args dict with where parameter
                            gql_args = {}
                            if where_input_type:
                                where_gql_type = convert_type_to_graphql_input(where_input_type)
                                gql_args["where"] = GraphQLArgument(where_gql_type)

                            gql_fields[graphql_field_name] = GraphQLField(
                                type_=convert_type_to_graphql_output(field_type),
                                description=field.description,
                                args=gql_args,
                                resolve=wrap_resolver_with_enum_serialization(enhanced_resolver),
                            )
                            continue  # Skip other resolver creation

                        # Check if we should use nested resolver (only if explicitly requested)
                        # By default (resolve_nested=False), nested objects are assumed to be
                        # embedded in the parent's JSONB data and use the standard resolver.
                        # Only when resolve_nested=True do we create a special resolver that
                        # can query the nested type's sql_source separately.
                        from fraiseql.core.nested_field_resolver import (
                            create_smart_nested_field_resolver,
                            should_use_nested_resolver,
                        )

                        if should_use_nested_resolver(field_type):
                            # Use smart resolver for resolve_nested=True types
                            smart_resolver = create_smart_nested_field_resolver(name, field_type)

                            # Wrap with enum serialization
                            from fraiseql.gql.enum_serializer import (
                                wrap_resolver_with_enum_serialization,
                            )

                            # Use explicit graphql_name if provided, otherwise convert to
                            # camelCase if configured
                            config = SchemaConfig.get_instance()
                            if field.graphql_name:
                                graphql_field_name = field.graphql_name
                            else:
                                graphql_field_name = (
                                    snake_to_camel(name) if config.camel_case_fields else name
                                )

                            gql_fields[graphql_field_name] = GraphQLField(
                                type_=convert_type_to_graphql_output(field_type),
                                description=field.description,
                                resolve=wrap_resolver_with_enum_serialization(smart_resolver),
                            )
                            continue  # Skip the regular resolver creation

                        # Create resolver for enum serialization and nested object conversion
                        def make_field_resolver(field_name: str, field_type: Any):
                            def resolve_field(obj: Any, info: Any) -> Any:
                                # Rust-first: Objects are plain dicts (Rust-transformed)
                                # No JSONPassthrough wrapper needed
                                value = getattr(obj, field_name, None)

                                # Handle None values
                                if value is None:
                                    return None

                                # Handle enum serialization at field level
                                if isinstance(value, Enum):
                                    # Check if the field type is an enum - if so, return the
                                    # enum member so GraphQL can handle serialization properly
                                    origin_type = get_origin(field_type) or field_type
                                    if origin_type is Union or origin_type is types.UnionType:
                                        # For Optional types, get the non-None type
                                        args = get_args(field_type)
                                        non_none_types = [t for t in args if t is not type(None)]
                                        if non_none_types:
                                            origin_type = non_none_types[0]

                                    if isinstance(origin_type, type) and issubclass(
                                        origin_type, Enum
                                    ):
                                        # Field type is an enum, return the member for GraphQL
                                        return value
                                    # Field type is not an enum, return the value
                                    return value.value
                                if isinstance(value, list):
                                    # Handle lists of enums or nested objects
                                    result = []
                                    for item in value:
                                        if isinstance(item, Enum):
                                            # Check if list contains enum types
                                            list_origin = get_origin(field_type)
                                            if list_origin in (list, List):
                                                list_args = get_args(field_type)
                                                if list_args:
                                                    item_type = list_args[0]
                                                    # Handle Optional[Enum]
                                                    origin_item_type = (
                                                        get_origin(item_type) or item_type
                                                    )
                                                    if (
                                                        origin_item_type is Union
                                                        or origin_item_type is types.UnionType
                                                    ):
                                                        args = get_args(item_type)
                                                        non_none_types = [
                                                            t for t in args if t is not type(None)
                                                        ]
                                                        if non_none_types:
                                                            item_type = non_none_types[0]

                                                    if isinstance(item_type, type) and issubclass(
                                                        item_type, Enum
                                                    ):
                                                        result.append(item)
                                                    else:
                                                        result.append(item.value)
                                                else:
                                                    result.append(item.value)
                                            else:
                                                result.append(item.value)
                                        elif isinstance(item, dict):
                                            # Check if list has FraiseQL types needing conversion
                                            list_item_type = _extract_list_item_type(field_type)

                                            if list_item_type and hasattr(
                                                list_item_type, "__fraiseql_definition__"
                                            ):
                                                # Convert dict to typed object
                                                if hasattr(list_item_type, "from_dict"):
                                                    result.append(list_item_type.from_dict(item))
                                                else:
                                                    result.append(item)
                                            else:
                                                result.append(item)
                                        else:
                                            result.append(item)
                                    return result

                                # Handle nested objects - check dict to FraiseQL conversion
                                if isinstance(value, dict):
                                    # Extract actual type from Optional if needed
                                    actual_field_type = field_type
                                    origin = get_origin(field_type)
                                    if origin is Union or origin is types.UnionType:
                                        args = get_args(field_type)
                                        non_none_types = [t for t in args if t is not type(None)]
                                        if non_none_types:
                                            actual_field_type = non_none_types[0]

                                    # Check if the field type is a FraiseQL type
                                    if hasattr(
                                        actual_field_type, "__fraiseql_definition__"
                                    ) and hasattr(actual_field_type, "from_dict"):
                                        return actual_field_type.from_dict(value)

                                return value

                            return resolve_field

                        # Use explicit graphql_name if provided, otherwise convert to
                        # camelCase if configured
                        config = SchemaConfig.get_instance()
                        if field.graphql_name:
                            graphql_field_name = field.graphql_name
                        else:
                            graphql_field_name = (
                                snake_to_camel(name) if config.camel_case_fields else name
                            )

                        # Wrap field resolver with enum serialization
                        from fraiseql.gql.enum_serializer import (
                            wrap_resolver_with_enum_serialization,
                        )

                        gql_fields[graphql_field_name] = GraphQLField(
                            type_=convert_type_to_graphql_output(field_type),
                            description=field.description,
                            resolve=wrap_resolver_with_enum_serialization(
                                make_field_resolver(name, field_type)
                            ),
                        )

                # Check for custom field methods (@dataloader_field, @field, etc.)
                for attr_name in dir(typ):
                    # Skip if we already have this field from regular processing
                    if attr_name in gql_fields:
                        continue

                    # Skip private/special methods
                    if attr_name.startswith("_"):
                        continue

                    attr = getattr(typ, attr_name)
                    if not callable(attr):
                        continue

                    # Check for field resolver decorators
                    if hasattr(attr, "__fraiseql_field__") or hasattr(
                        attr,
                        "__fraiseql_dataloader__",
                    ):
                        # Get method signature for type information
                        from typing import get_type_hints

                        try:
                            hints = get_type_hints(attr)
                            return_type = hints.get("return")

                            if return_type is None:
                                logger.warning(
                                    "Custom field method %s missing return type annotation",
                                    attr_name,
                                )
                                continue

                            logger.debug("Found custom field method: %s", attr_name)

                            # Convert return type to GraphQL type
                            gql_return_type = convert_type_to_graphql_output(return_type)

                            # Create a wrapper that adapts the method signature for GraphQL
                            def make_custom_resolver(method):
                                import asyncio

                                if asyncio.iscoroutinefunction(method):

                                    async def async_resolver(obj, info, **kwargs):
                                        # Call the method with the object instance and info
                                        return await method(obj, info, **kwargs)

                                    return async_resolver

                                def sync_resolver(obj, info, **kwargs):
                                    # Call the method with the object instance and info
                                    return method(obj, info, **kwargs)

                                return sync_resolver

                            # Wrap with enum serialization
                            from fraiseql.gql.enum_serializer import (
                                wrap_resolver_with_enum_serialization,
                            )

                            wrapped_resolver = wrap_resolver_with_enum_serialization(
                                make_custom_resolver(attr),
                            )

                            # Get description from decorator or docstring
                            description = getattr(
                                attr,
                                "__fraiseql_field_description__",
                                None,
                            ) or getattr(attr, "__doc__", None)

                            # Convert field name to camelCase if configured
                            config = SchemaConfig.get_instance()
                            graphql_field_name = (
                                snake_to_camel(attr_name) if config.camel_case_fields else attr_name
                            )

                            gql_fields[graphql_field_name] = GraphQLField(
                                type_=cast("GraphQLOutputType", gql_return_type),
                                resolve=wrapped_resolver,
                                description=description,
                            )

                        except Exception as e:
                            logger.warning(
                                "Failed to process custom field %s: %s",
                                attr_name,
                                e,
                            )
                            continue

                # Get interfaces this type implements
                interfaces = []
                if hasattr(typ, "__fraiseql_interfaces__"):
                    for interface_cls in typ.__fraiseql_interfaces__:
                        interface_gql = convert_type_to_graphql_output(interface_cls)
                        if isinstance(interface_gql, GraphQLInterfaceType):
                            interfaces.append(interface_gql)

                # Add is_type_of function to help with interface resolution
                def is_type_of(obj, info):
                    """Check if an object is of this type."""
                    return (
                        obj.__class__.__name__ == typ.__name__
                        if hasattr(obj, "__class__")
                        else False
                    )

                gql_type = GraphQLObjectType(
                    name=typ.__name__,
                    fields=gql_fields,
                    interfaces=interfaces if interfaces else None,
                    is_type_of=is_type_of,
                    description=_clean_docstring(typ.__doc__),
                )
                _graphql_type_cache[key] = gql_type
                return gql_type
            if definition.kind == "interface":
                # Handle interface types
                fields = getattr(typ, "__gql_fields__", {})
                type_hints = getattr(typ, "__gql_type_hints__", {})

                gql_fields = {}
                for name, field in fields.items():
                    field_type = field.field_type or type_hints.get(name)
                    if field_type is not None:
                        # Use explicit graphql_name if provided, otherwise convert to
                        # camelCase if configured
                        config = SchemaConfig.get_instance()
                        if field.graphql_name:
                            graphql_field_name = field.graphql_name
                        else:
                            graphql_field_name = (
                                snake_to_camel(name) if config.camel_case_fields else name
                            )

                        gql_fields[graphql_field_name] = GraphQLField(
                            type_=convert_type_to_graphql_output(field_type),
                            description=field.description,
                        )

                # Create interface type with type resolver
                def resolve_type(obj, info, type_):
                    """Resolve the concrete type for an interface."""
                    if hasattr(obj, "__class__") and hasattr(obj.__class__, "__name__"):
                        return obj.__class__.__name__
                    return None

                gql_type = GraphQLInterfaceType(
                    name=typ.__name__,
                    fields=gql_fields,
                    resolve_type=resolve_type,
                    description=_clean_docstring(typ.__doc__),
                )
                _graphql_type_cache[key] = gql_type
                return gql_type

    msg = f"Unsupported output type: {typ}"
    raise TypeError(msg)


def translate_query_from_type(
    query: str,
    root_type: type[Any],
    *,
    where: DynamicType | None = None,
    auto_camel_case: bool = False,
) -> SQL | Composed:
    """Missing docstring."""
    if (
        not hasattr(root_type, "__gql_typename__")
        or not hasattr(root_type, "__gql_table__")
        or root_type.__gql_table__ is None
    ):
        msg = (
            f"{root_type.__name__} must be a FraiseQL output type decorated "
            f"with @fraise_type and linked to a SQL table"
        )
        raise ValueError(
            msg,
        )
    where_clause: SQL | None = None
    if where:
        where_clause = where.to_sql()
    table: str = cast("str", root_type.__gql_table__)
    typename: str = cast("str", root_type.__gql_typename__)
    return translate_query(
        query=query,
        table=table,
        typename=typename,
        where_clause=where_clause,
        auto_camel_case=auto_camel_case,
    )
