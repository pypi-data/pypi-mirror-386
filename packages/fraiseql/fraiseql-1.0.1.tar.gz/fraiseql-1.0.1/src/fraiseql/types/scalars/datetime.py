"""Missing docstring."""

from datetime import UTC, datetime
from typing import Any

from graphql import GraphQLError, GraphQLScalarType
from graphql.language import StringValueNode, ValueNode

from fraiseql.types.definitions import ScalarMarker


def raise_value_error(msg: str) -> None:
    """Helper function to raise a ValueError."""
    raise ValueError(msg)


def serialize_datetime(value: Any) -> str:
    """Serialize datetime to ISO 8601 string, always using 'Z' for UTC."""
    # Handle datetime objects
    if isinstance(value, datetime):
        # Convert to UTC if not already
        if value.tzinfo is not None:
            value = value.astimezone(UTC)
        else:
            # Assume naive datetimes are UTC
            value = value.replace(tzinfo=UTC)

        # Return with 'Z' suffix
        return value.isoformat().replace("+00:00", "Z")

    # Handle string inputs (e.g., from JSONB)
    if isinstance(value, str):
        try:
            # Parse the datetime string
            dt = parse_datetime_value(value)
            if dt is None:
                raise ValueError(f"Invalid datetime value: {value}")

            # Convert to UTC
            if dt.tzinfo is not None:
                dt = dt.astimezone(UTC)
            else:
                # Assume naive datetimes are UTC
                dt = dt.replace(tzinfo=UTC)

            # Return with 'Z' suffix
            return dt.isoformat().replace("+00:00", "Z")

        except GraphQLError:
            msg = f"DateTime cannot represent invalid ISO datetime string: {value!r}"
            raise GraphQLError(msg)

    # Invalid type
    msg = f"DateTime cannot represent non-datetime value: {value!r}"
    raise GraphQLError(msg)


def parse_datetime_value(value: Any) -> datetime | None:
    """Parse ISO 8601 string (with optional Z or offset) into datetime."""
    if value is None:
        return None

    if not isinstance(value, str):
        msg = f"DateTime cannot represent non-string value: {value!r}"
        raise GraphQLError(msg)

    try:
        # Check if the string ends with 'Z' and replace it with '+00:00' for parsing
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        # Parse the datetime string
        dt = datetime.fromisoformat(value)

        # Ensure the datetime is timezone-aware
        if dt.tzinfo is None:
            raise_value_error("Datetime must be timezone-aware")
        else:
            return dt
    except ValueError as e:
        msg = f"Invalid ISO 8601 DateTime: {value!r}"
        raise GraphQLError(msg) from e


def parse_datetime_literal(
    ast: ValueNode,
    variables: dict[str, object] | None = None,
) -> datetime | None:
    """Parse a DateTime literal from GraphQL AST."""
    _ = variables
    if isinstance(ast, StringValueNode):
        return parse_datetime_value(ast.value)
    msg = f"DateTime cannot represent non-string literal: {getattr(ast, 'value', None)!r}"
    raise GraphQLError(
        msg,
    )


DateTimeScalar = GraphQLScalarType(
    name="DateTime",
    description="An ISO 8601-compliant DateTime scalar (with timezone, JS-compatible).",
    serialize=serialize_datetime,
    parse_value=parse_datetime_value,
    parse_literal=parse_datetime_literal,
)


class DateTimeField(str, ScalarMarker):
    """Python marker for the GraphQL DateTime scalar."""

    __slots__ = ()

    def __repr__(self) -> str:
        """Missing docstring."""
        return "DateTime"
