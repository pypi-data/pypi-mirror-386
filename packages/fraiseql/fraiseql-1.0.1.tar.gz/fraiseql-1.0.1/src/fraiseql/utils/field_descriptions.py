"""Automatic field description extraction for FraiseQL types.

This module provides utilities to automatically extract descriptions for type fields
from various sources like inline comments, docstrings, and field annotations.
"""

import inspect
import re
from typing import Dict, get_type_hints

from fraiseql.fields import FraiseQLField


def extract_field_descriptions(cls: type) -> Dict[str, str]:
    """Extract field descriptions from a class definition.

    Supports multiple sources for field descriptions in priority order:
    1. Inline comments (# comment) - highest priority
    2. Type annotations with Annotated[type, "description"]
    3. Class docstring field documentation - lowest priority

    Args:
        cls: The class to extract field descriptions from

    Returns:
        Dictionary mapping field names to their descriptions

    Examples:
        @fraise_type
        class User:
            '''User account model.

            Fields:
                id: Unique identifier for the user
                email: User's email address
            '''
            id: UUID  # Primary key identifier
            name: str  # Full name of the user
            email: str
            status: str = "active"  # Account status
    """
    descriptions = {}

    # Start with lowest priority: class docstring
    docstring_descriptions = _extract_docstring_descriptions(cls)
    descriptions.update(docstring_descriptions)

    # Medium priority: type annotations
    annotation_descriptions = _extract_annotation_descriptions(cls)
    descriptions.update(annotation_descriptions)

    # Highest priority: inline comments (will override others)
    inline_descriptions = _extract_inline_comments(cls)
    descriptions.update(inline_descriptions)

    return descriptions


def _extract_inline_comments(cls: type) -> Dict[str, str]:
    """Extract field descriptions from inline comments in source code."""
    try:
        source = inspect.getsource(cls)
        source_lines = source.split("\n")
        descriptions = {}

        # Look for patterns like "field_name: type  # comment"
        for line in source_lines:
            # Match field declarations with inline comments
            # Pattern: optional whitespace, field name, colon, type, optional default, hash, comment
            pattern = r"^\s*(\w+)\s*:\s*[^#]*#\s*(.+)$"
            match = re.match(pattern, line)
            if match:
                field_name = match.group(1)
                comment = match.group(2).strip()
                # Clean up common comment patterns
                comment = re.sub(r"^\w+:\s*", "", comment)  # Remove "type: " prefixes
                descriptions[field_name] = comment

        return descriptions

    except (OSError, TypeError, SyntaxError):
        # Source not available or not parseable
        return {}


def _extract_docstring_descriptions(cls: type) -> Dict[str, str]:
    """Extract field descriptions from class docstring."""
    docstring = cls.__doc__
    if not docstring:
        return {}

    descriptions = {}

    # Look for Fields: or Attributes: section in docstring
    patterns = [
        r"Fields:\s*\n((?:\s+\w+:.*\n?)*)",
        r"Attributes:\s*\n((?:\s+\w+:.*\n?)*)",
        r"Args:\s*\n((?:\s+\w+:.*\n?)*)",  # For input types
    ]

    for pattern in patterns:
        match = re.search(pattern, docstring, re.MULTILINE)
        if match:
            fields_section = match.group(1)
            # Parse individual field descriptions
            field_lines = re.findall(r"^\s+(\w+):\s*(.+)$", fields_section, re.MULTILINE)
            for field_name, description in field_lines:
                descriptions[field_name] = description.strip()
            break

    return descriptions


def _extract_annotation_descriptions(cls: type) -> Dict[str, str]:
    """Extract descriptions from Annotated type hints."""
    try:
        from typing import get_args, get_origin

        hints = get_type_hints(cls, include_extras=True)
        descriptions = {}

        for field_name, hint in hints.items():
            # Check if this is Annotated[type, ...]
            origin = get_origin(hint)
            if origin is not None and (
                (hasattr(origin, "_name") and origin._name == "Annotated")
                or (hasattr(origin, "__name__") and origin.__name__ == "Annotated")
            ):
                args = get_args(hint)
                # Look for string annotations that could be descriptions
                for arg in args[1:]:  # Skip the first arg which is the type
                    if isinstance(arg, str):
                        descriptions[field_name] = arg
                        break

        return descriptions

    except (NameError, AttributeError, ImportError):
        return {}


def apply_auto_descriptions(cls: type) -> None:
    """Apply automatic descriptions to fields that don't have explicit descriptions.

    This function modifies the class's __gql_fields__ to add descriptions
    for fields that don't already have them.

    Args:
        cls: The class to apply automatic descriptions to
    """
    if not hasattr(cls, "__gql_fields__"):
        return

    # First apply filter-specific descriptions for where clause types
    from fraiseql.utils.where_clause_descriptions import apply_filter_descriptions

    apply_filter_descriptions(cls)

    # Then apply general automatic descriptions from docstrings/annotations
    auto_descriptions = extract_field_descriptions(cls)

    for field_name, field in cls.__gql_fields__.items():
        if (
            isinstance(field, FraiseQLField)
            and not field.description
            and field_name in auto_descriptions
        ):
            field.description = auto_descriptions[field_name]
