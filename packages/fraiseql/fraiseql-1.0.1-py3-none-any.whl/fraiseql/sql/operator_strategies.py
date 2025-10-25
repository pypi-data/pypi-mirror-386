"""Operator strategies for SQL WHERE clause generation.

This module implements the strategy pattern for different SQL operators,
making the where clause generation more maintainable and extensible.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

from psycopg.sql import SQL, Composed, Literal


class OperatorStrategy(Protocol):
    """Protocol for operator strategies."""

    def can_handle(self, op: str) -> bool:
        """Check if this strategy can handle the given operator."""
        ...

    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build the SQL for this operator."""
        ...


class BaseOperatorStrategy(ABC):
    """Base class for operator strategies with common functionality."""

    def __init__(self, operators: list[str]) -> None:
        """Initialize with the list of operators this strategy handles."""
        self.operators = operators

    def can_handle(self, op: str) -> bool:
        """Check if this strategy can handle the given operator."""
        return op in self.operators

    @abstractmethod
    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build the SQL for this operator."""

    def _apply_type_cast(
        self, path_sql: SQL, val: Any, op: str, field_type: type | None = None
    ) -> SQL | Composed:
        """Apply appropriate type casting to the JSONB path."""
        # Handle IP address types specially
        if (
            field_type
            and self._is_ip_address_type(field_type)
            and op in ("eq", "neq", "contains", "startswith", "endswith", "in", "notin")
        ):
            # For IP addresses, use host() to strip CIDR notation
            return Composed([SQL("host("), path_sql, SQL("::inet)")])

        # CRITICAL FIX: Handle special types even when field_type is not provided
        # This fixes the production issue where field_type information is lost
        if not field_type and op in (
            "eq",
            "neq",
            "contains",
            "startswith",
            "endswith",
            "in",
            "notin",
        ):
            # Check MAC addresses first (most specific - before IP addresses)
            if self._looks_like_mac_address_value(val, op):
                # Apply MAC address casting for network hardware operations
                # CRITICAL FIX: Proper parentheses for casting JSONB extracted value
                return Composed([SQL("("), path_sql, SQL(")::macaddr")])

            # Check for IP addresses (after MAC addresses to avoid collision)
            if self._looks_like_ip_address_value(val, op):
                # Apply IP address casting to fix JSONB text comparison issue
                # For equality operators, cast directly to inet without host() function
                # host() strips CIDR notation but we want exact equality matching
                if op in ("eq", "neq", "in", "notin"):
                    return Composed([SQL("("), path_sql, SQL(")::inet")])
                # For pattern operators (contains, startswith, endswith), use host() to get clean IP
                return Composed([SQL("host("), path_sql, SQL("::inet)")])

            # Check for LTree paths
            if self._looks_like_ltree_value(val, op):
                # Apply LTree casting for hierarchical path operations
                # CRITICAL FIX: Proper parentheses for casting JSONB extracted value
                return Composed([SQL("("), path_sql, SQL(")::ltree")])

            # Check for DateRange values
            if self._looks_like_daterange_value(val, op):
                # Apply DateRange casting for temporal range operations
                # CRITICAL FIX: Proper parentheses for casting JSONB extracted value
                return Composed([SQL("("), path_sql, SQL(")::daterange")])

        # CRITICAL FIX: Consistent type casting for JSONB fields based on value types
        # JSONB ->> extracts as text, but we need type-aware operations for proper behavior

        # Cast based on value type for consistent behavior across all operations
        # CRITICAL: Check bool BEFORE int since bool is subclass of int in Python
        if isinstance(val, bool):
            # CRITICAL: For boolean operations, convert value to JSONB text representation
            # JSONB stores booleans as "true"/"false" text when extracted with ->>
            # So we compare text-to-text rather than casting to boolean
            return (
                path_sql  # No casting - will handle value conversion in ComparisonOperatorStrategy
            )
        if isinstance(val, (int, float, Decimal)):
            # All numeric operations need numeric casting for proper comparison
            return Composed([SQL("("), path_sql, SQL(")::numeric")])
        if isinstance(val, datetime):
            return Composed([SQL("("), path_sql, SQL(")::timestamp")])
        if isinstance(val, date):
            return Composed([SQL("("), path_sql, SQL(")::date")])

        # Handle UUID values - cast JSONB text to UUID for comparison
        if isinstance(val, UUID):
            return Composed([SQL("("), path_sql, SQL(")::uuid")])

        return path_sql

    def _is_ip_address_type(self, field_type: type) -> bool:
        """Check if field_type is an IP address type."""
        # Handle FieldType enum values (from WHERE generator)
        try:
            from fraiseql.sql.where.core.field_detection import FieldType

            if field_type == FieldType.IP_ADDRESS:
                return True
        except ImportError:
            pass

        # Import here to avoid circular imports
        try:
            from fraiseql.types.scalars.ip_address import IpAddressField

            return field_type == IpAddressField or (
                isinstance(field_type, type) and issubclass(field_type, IpAddressField)
            )
        except ImportError:
            return False

    def _is_ltree_type(self, field_type: type) -> bool:
        """Check if field_type is an LTree type."""
        # Import here to avoid circular imports
        try:
            from fraiseql.types import LTree
            from fraiseql.types.scalars.ltree import LTreeField

            return field_type in (LTree, LTreeField) or (
                isinstance(field_type, type) and issubclass(field_type, LTreeField)
            )
        except ImportError:
            return False

    def _is_mac_address_type(self, field_type: type) -> bool:
        """Check if field_type is a MAC address type."""
        # Import here to avoid circular imports
        try:
            from fraiseql.types import MacAddress
            from fraiseql.types.scalars.mac_address import MacAddressField

            return field_type in (MacAddress, MacAddressField) or (
                isinstance(field_type, type) and issubclass(field_type, MacAddressField)
            )
        except ImportError:
            return False

    def _looks_like_ip_address_value(self, val: Any, op: str) -> bool:
        """Check if a value looks like an IP address (fallback when field_type is missing).

        This is the critical fix for production failures where field_type information
        is lost but we still need to apply proper IP address casting.
        """
        if not isinstance(val, str):
            # Handle list values for 'in'/'notin' operators
            if op in ("in", "notin") and isinstance(val, list):
                return any(
                    self._looks_like_ip_address_value(v, "eq") for v in val if isinstance(v, str)
                )
            return False

        # Import here to avoid circular imports and only when needed
        try:
            import ipaddress

            # Try to parse as IP address (both IPv4 and IPv6)
            try:
                ipaddress.ip_address(val)
                return True
            except ValueError:
                # Also try as CIDR network (might be used in comparisons)
                try:
                    ipaddress.ip_network(val, strict=False)
                    return True
                except ValueError:
                    pass

            # Additional heuristic checks for common IP patterns
            # This catches edge cases where ipaddress parsing might be too strict
            if val.count(".") == 3:  # IPv4-like pattern
                parts = val.split(".")
                if len(parts) == 4 and all(
                    part.isdigit() and 0 <= int(part) <= 255 for part in parts
                ):
                    return True

            # IPv6-like pattern (simplified check)
            if ":" in val and val.count(":") >= 2:  # At least two colons
                # Basic IPv6 pattern check - contains only valid hex chars and colons
                hex_chars = "0123456789abcdefABCDEF"
                return all(c in hex_chars + ":" for c in val)

        except ImportError:
            # Fallback to basic pattern matching if ipaddress module not available
            # IPv4 pattern: xxx.xxx.xxx.xxx
            if val.count(".") == 3:
                parts = val.split(".")
                try:
                    return all(0 <= int(part) <= 255 for part in parts)
                except ValueError:
                    pass

        return False

    def _looks_like_ltree_value(self, val: Any, op: str) -> bool:
        """Check if a value looks like an LTree path (fallback when field_type is missing).

        LTree paths use dot notation for hierarchical structures like 'top.middle.bottom'.
        """
        if not isinstance(val, str):
            # Handle list values for 'in'/'notin' operators
            if op in ("in", "notin") and isinstance(val, list):
                return any(self._looks_like_ltree_value(v, "eq") for v in val if isinstance(v, str))
            return False

        # Basic LTree patterns:
        # - Contains dots (hierarchical separator)
        # - Contains only alphanumeric chars, dots, underscores, hyphens
        # - At least one dot (implies hierarchy)
        # - No consecutive dots
        # - Doesn't start or end with dot

        if not val or val.startswith(".") or val.endswith(".") or ".." in val:
            return False

        if "." not in val:
            return False  # LTree paths should be hierarchical

        # Check for valid LTree characters and patterns
        # LTree labels can contain: letters, digits, underscore, hyphen
        # But we need to be more restrictive to avoid false positives with domain names
        import re

        # More restrictive LTree pattern - avoid common domain extensions
        ltree_pattern = r"^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$"

        if not re.match(ltree_pattern, val):
            return False

        # Additional checks to avoid domain name false positives
        # Common domain extensions that should NOT be treated as LTree
        domain_extensions = {
            "com",
            "net",
            "org",
            "edu",
            "gov",
            "mil",
            "int",
            "co",
            "uk",
            "ca",
            "de",
            "fr",
            "jp",
            "au",
            "ru",
            "io",
            "ai",
            "dev",
            "app",
            "api",
            "www",
            "local",  # CRITICAL FIX: .local domains (mDNS) are NOT ltree paths
        }

        # If the last part is a common domain extension, probably not an LTree
        last_part = val.split(".")[-1].lower()
        if last_part in domain_extensions:
            return False

        # If it looks like a URL (has common web prefixes), probably not an LTree
        if val.lower().startswith(("www.", "api.", "app.", "dev.", "test.")):
            return False

        # Avoid detecting IP-like patterns (even invalid ones) as LTree
        # If it has exactly 3 dots and all parts are numeric, it's likely an IP attempt
        parts = val.split(".")
        if len(parts) == 4 and all(
            part.replace("-", "").replace("_", "").isdigit() for part in parts
        ):
            return False

        return True

    def _looks_like_daterange_value(self, val: Any, op: str) -> bool:
        """Check if a value looks like a DateRange (fallback when field_type is missing).

        DateRange format: '[2024-01-01,2024-12-31)' or '(2024-01-01,2024-12-31]'
        """
        if not isinstance(val, str):
            # Handle list values for 'in'/'notin' operators
            if op in ("in", "notin") and isinstance(val, list):
                return any(
                    self._looks_like_daterange_value(v, "eq") for v in val if isinstance(v, str)
                )
            return False

        # PostgreSQL daterange format patterns:
        # - Starts with '[' or '(' (inclusive/exclusive lower bound)
        # - Ends with ']' or ')' (inclusive/exclusive upper bound)
        # - Contains comma separating two dates
        # - Dates in ISO format: YYYY-MM-DD

        if len(val) < 7:  # Minimum: '[a,b]'
            return False

        if not (val.startswith(("[", "(")) and val.endswith(("]", ")"))):
            return False

        # Extract the content between brackets
        content = val[1:-1]  # Remove brackets

        if "," not in content:
            return False

        # Split on comma and check each part looks like a date
        parts = content.split(",")
        if len(parts) != 2:
            return False

        # Basic date pattern check (YYYY-MM-DD)
        import re

        date_pattern = r"^\d{4}-\d{2}-\d{2}$"

        for part in parts:
            stripped_part = part.strip()
            if not stripped_part:  # Allow empty for infinite ranges
                continue
            if not re.match(date_pattern, stripped_part):
                return False

        return True

    def _looks_like_mac_address_value(self, val: Any, op: str) -> bool:
        """Check if a value looks like a MAC address (fallback when field_type is missing).

        MAC address formats:
        - 00:11:22:33:44:55 (colon-separated)
        - 00-11-22-33-44-55 (hyphen-separated)
        - 001122334455 (no separators)
        """
        if not isinstance(val, str):
            # Handle list values for 'in'/'notin' operators
            if op in ("in", "notin") and isinstance(val, list):
                return any(
                    self._looks_like_mac_address_value(v, "eq") for v in val if isinstance(v, str)
                )
            return False

        if not val:
            return False

        # Remove common separators
        mac_clean = val.replace(":", "").replace("-", "").replace(" ", "").upper()

        # MAC address should be exactly 12 hex characters
        if len(mac_clean) != 12:
            return False

        # Check if all characters are valid hex
        try:
            int(mac_clean, 16)
            return True
        except ValueError:
            return False


class NullOperatorStrategy(BaseOperatorStrategy):
    """Strategy for null/not null operators."""

    def __init__(self) -> None:
        super().__init__(["isnull"])

    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build SQL for null checks."""
        if val:
            return Composed([path_sql, SQL(" IS NULL")])
        return Composed([path_sql, SQL(" IS NOT NULL")])


class ComparisonOperatorStrategy(BaseOperatorStrategy):
    """Strategy for comparison operators (=, !=, <, >, <=, >=)."""

    def __init__(self) -> None:
        super().__init__(["eq", "neq", "gt", "gte", "lt", "lte"])
        self.operator_map = {
            "eq": " = ",
            "neq": " != ",
            "gt": " > ",
            "gte": " >= ",
            "lt": " < ",
            "lte": " <= ",
        }

    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build SQL for comparison operators."""
        casted_path = self._apply_type_cast(path_sql, val, op, field_type)
        sql_op = self.operator_map[op]

        # CRITICAL FIX: Handle value type conversion for JSONB fields

        # If we detected IP address and cast the field to ::inet,
        # we must also cast the literal value to ::inet for PostgreSQL compatibility
        if (
            not field_type  # Only when field_type is missing (production CQRS pattern)
            and op in ("eq", "neq")
            and self._looks_like_ip_address_value(val, op)
            and casted_path != path_sql  # Path was modified
            and "::inet" in str(casted_path)  # Specifically cast to inet (not macaddr/ltree/etc)
        ):
            return Composed([casted_path, SQL(sql_op), Literal(val), SQL("::inet")])

        # CRITICAL FIX: If we detected LTree path and cast the field to ::ltree,
        # we must also cast the literal value to ::ltree for PostgreSQL compatibility
        if (
            not field_type  # Only when field_type is missing (production CQRS pattern)
            and op in ("eq", "neq")
            and self._looks_like_ltree_value(val, op)
            and casted_path != path_sql  # Path was modified
            and "::ltree" in str(casted_path)  # Specifically cast to ltree
        ):
            return Composed([casted_path, SQL(sql_op), Literal(val), SQL("::ltree")])

        # CRITICAL FIX: If we detected MAC address and cast the field to ::macaddr,
        # we must also cast the literal value to ::macaddr for PostgreSQL compatibility
        if (
            not field_type  # Only when field_type is missing (production CQRS pattern)
            and op in ("eq", "neq")
            and self._looks_like_mac_address_value(val, op)
            and casted_path != path_sql  # Path was modified
            and "::macaddr" in str(casted_path)  # Specifically cast to macaddr
        ):
            return Composed([casted_path, SQL(sql_op), Literal(val), SQL("::macaddr")])

        # CRITICAL FIX: If we kept the path as text (for booleans only),
        # convert boolean values to JSONB text representation for text-to-text comparison
        if (
            casted_path == path_sql  # Path was NOT cast (still text from JSONB ->>)
            and isinstance(val, bool)  # Only for boolean values
            and op in ("eq", "neq", "in", "notin")  # Only for equality/membership
        ):
            # Convert Python boolean to JSONB text representation
            string_val = "true" if val else "false"
            return Composed([casted_path, SQL(sql_op), Literal(string_val)])

        # Handle boolean lists for membership tests
        if (
            casted_path == path_sql  # Path was NOT cast
            and isinstance(val, list)
            and op in ("in", "notin")
            and all(isinstance(v, bool) for v in val)  # All values are booleans
        ):
            # Convert boolean list to string list
            string_vals = ["true" if v else "false" for v in val]
            return Composed([casted_path, SQL(sql_op), Literal(string_vals)])

        return Composed([casted_path, SQL(sql_op), Literal(val)])


class JsonOperatorStrategy(BaseOperatorStrategy):
    """Strategy for JSONB-specific operators."""

    def __init__(self) -> None:
        super().__init__(["overlaps", "strictly_contains"])  # Removed "contains"

    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build SQL for JSONB operators."""
        if op == "overlaps":
            return Composed([path_sql, SQL(" && "), Literal(val)])
        if op == "strictly_contains":
            return Composed(
                [
                    path_sql,
                    SQL(" @> "),
                    Literal(val),
                    SQL(" AND "),
                    path_sql,
                    SQL(" != "),
                    Literal(val),
                ],
            )
        raise ValueError(f"Unsupported JSON operator: {op}")


class PatternMatchingStrategy(BaseOperatorStrategy):
    """Strategy for pattern matching operators."""

    def __init__(self) -> None:
        super().__init__(["matches", "startswith", "contains", "endswith", "ilike"])

    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build SQL for pattern matching."""
        # Apply type-specific casting (including IP address handling)
        casted_path = self._apply_type_cast(path_sql, val, op, field_type)

        if op == "matches":
            return Composed([casted_path, SQL(" ~ "), Literal(val)])
        if op == "startswith":
            if isinstance(val, str):
                # Use LIKE for prefix matching
                # Use %% to escape % for psycopg3
                like_val = f"{val}%%"
                return Composed([casted_path, SQL(" LIKE "), Literal(like_val)])
            return Composed([casted_path, SQL(" ~ "), Literal(f"^{val}.*")])
        if op == "endswith":
            if isinstance(val, str):
                # Use LIKE for suffix matching
                # Use %% to escape % for psycopg3
                like_val = f"%%{val}"
                return Composed([casted_path, SQL(" LIKE "), Literal(like_val)])
            return Composed([casted_path, SQL(" ~ "), Literal(f".*{val}$")])
        if op == "contains":
            if isinstance(val, str):
                # Use LIKE for substring matching
                # Use %% to escape % for psycopg3
                like_val = f"%%{val}%%"
                return Composed([casted_path, SQL(" LIKE "), Literal(like_val)])
            return Composed([casted_path, SQL(" ~ "), Literal(f".*{val}.*")])
        if op == "ilike":
            if isinstance(val, str):
                # Use ILIKE for case-insensitive substring matching with automatic wildcards
                # Use %% to escape % for psycopg3
                like_val = f"%%{val}%%"
                return Composed([casted_path, SQL(" ILIKE "), Literal(like_val)])
            return Composed([casted_path, SQL(" ~* "), Literal(val)])
        raise ValueError(f"Unsupported pattern operator: {op}")


class ListOperatorStrategy(BaseOperatorStrategy):
    """Strategy for list-based operators (IN, NOT IN)."""

    def __init__(self) -> None:
        super().__init__(["in", "notin"])

    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build SQL for list operators."""
        if not isinstance(val, list):
            msg = f"'{op}' operator requires a list, got {type(val)}"
            raise TypeError(msg)

        # Apply type-specific casting (including IP address handling)
        casted_path = self._apply_type_cast(path_sql, val[0] if val else None, op, field_type)

        # CRITICAL FIX: Detect if we're dealing with IP addresses without field_type
        is_ip_list_without_field_type = (
            not field_type  # Production CQRS pattern
            and val  # List is not empty
            and self._looks_like_ip_address_value(val, op)  # Detects IP lists
            and casted_path != path_sql  # Path was modified
            and "::inet" in str(casted_path)  # Specifically cast to inet (not macaddr/ltree/etc)
        )

        # CRITICAL FIX: Detect if we're dealing with LTree paths without field_type
        is_ltree_list_without_field_type = (
            not field_type  # Production CQRS pattern
            and val  # List is not empty
            and self._looks_like_ltree_value(val, op)  # Detects LTree lists
            and casted_path != path_sql  # Path was modified
            and "::ltree" in str(casted_path)  # Specifically cast to ltree
        )

        # CRITICAL FIX: Detect if we're dealing with MAC addresses without field_type
        is_mac_list_without_field_type = (
            not field_type  # Production CQRS pattern
            and val  # List is not empty
            and self._looks_like_mac_address_value(val, op)  # Detects MAC address lists
            and casted_path != path_sql  # Path was modified
            and "::macaddr" in str(casted_path)  # Specifically cast to macaddr
        )

        # Handle value conversion based on type (aligned with _apply_type_cast logic)
        if not (
            field_type
            and (
                self._is_ip_address_type(field_type)
                or self._is_ltree_type(field_type)
                or self._is_mac_address_type(field_type)
            )
        ):
            # Check if this is a boolean list (check bool first since bool is subclass of int)
            if val and all(isinstance(v, bool) for v in val):
                # For boolean lists, use text comparison with converted values
                converted_vals = ["true" if v else "false" for v in val]
                literals = [Literal(v) for v in converted_vals]
            elif val and all(isinstance(v, (int, float, Decimal)) for v in val):
                # For numeric lists, the _apply_type_cast already added ::numeric
                # Don't add it again to avoid double-casting
                literals = [Literal(v) for v in val]
            else:
                # For other types (strings, etc.), use values as-is
                literals = [Literal(v) for v in val]
        else:
            # For IP addresses, LTree, and MAC addresses, use string literals
            literals = [Literal(str(v)) for v in val]

        # Build the IN/NOT IN clause
        parts = [casted_path]
        parts.append(SQL(" IN (" if op == "in" else " NOT IN ("))

        for i, lit in enumerate(literals):
            if i > 0:
                parts.append(SQL(", "))
            parts.append(lit)
            # CRITICAL FIX: Cast each literal to ::inet if we detected IP addresses
            if is_ip_list_without_field_type:
                parts.append(SQL("::inet"))
            # CRITICAL FIX: Cast each literal to ::ltree if we detected LTree paths
            elif is_ltree_list_without_field_type:
                parts.append(SQL("::ltree"))
            # CRITICAL FIX: Cast each literal to ::macaddr if we detected MAC addresses
            elif is_mac_list_without_field_type:
                parts.append(SQL("::macaddr"))

        parts.append(SQL(")"))
        return Composed(parts)


class PathOperatorStrategy(BaseOperatorStrategy):
    """Strategy for path/tree operators."""

    def __init__(self) -> None:
        super().__init__(["depth_eq", "depth_gt", "depth_lt", "isdescendant"])

    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build SQL for path operators."""
        if op == "depth_eq":
            return Composed([SQL("nlevel("), path_sql, SQL(") = "), Literal(val)])
        if op == "depth_gt":
            return Composed([SQL("nlevel("), path_sql, SQL(") > "), Literal(val)])
        if op == "depth_lt":
            return Composed([SQL("nlevel("), path_sql, SQL(") < "), Literal(val)])
        if op == "isdescendant":
            return Composed([path_sql, SQL(" <@ "), Literal(val)])
        raise ValueError(f"Unsupported path operator: {op}")


class DateRangeOperatorStrategy(BaseOperatorStrategy):
    """Strategy for DateRange operators with PostgreSQL daterange type casting."""

    def __init__(self) -> None:
        # Include range operators and basic operations, restrict problematic patterns
        super().__init__(
            [
                "eq",
                "neq",
                "in",
                "notin",  # Basic operations
                "contains_date",  # Range contains date (@>)
                "overlaps",  # Ranges overlap (&&) - handled by existing JsonOperatorStrategy
                "adjacent",  # Ranges are adjacent (-|-)
                "strictly_left",  # Range is strictly left (<<)
                "strictly_right",  # Range is strictly right (>>)
                "not_left",  # Range does not extend left (&>)
                "not_right",  # Range does not extend right (&<)
                "contains",
                "startswith",
                "endswith",  # Generic patterns (to restrict)
            ]
        )

    def can_handle(self, op: str, field_type: type | None = None) -> bool:
        """Check if this strategy can handle the given operator.

        DateRange operators should only be used with DateRange field types.
        For DateRange types, we handle ALL operators to properly restrict unsupported ones.
        """
        if op not in self.operators:
            return False

        # Define DateRange-specific operators that we can safely handle without field type info
        daterange_specific_ops = {
            "contains_date",
            "overlaps",
            "adjacent",
            "strictly_left",
            "strictly_right",
            "not_left",
            "not_right",
        }

        # If no field type provided, only handle DateRange-specific operators
        # Generic operators (eq, contains, etc.) should go to appropriate generic strategies
        if field_type is None:
            return op in daterange_specific_ops

        # For DateRange types, handle ALL the operators we're configured for
        # This ensures we can properly restrict the problematic ones
        return self._is_daterange_type(field_type)

    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build SQL for DateRange operators with proper daterange casting."""
        # Safety check: if we know the field type and it's NOT a DateRange, something is wrong
        if field_type and not self._is_daterange_type(field_type):
            raise ValueError(
                f"DateRange operator '{op}' can only be used with DateRange fields, "
                f"got {field_type}"
            )

        # For basic operations, cast both sides to daterange for proper PostgreSQL handling
        if op in ("eq", "neq", "in", "notin"):
            casted_path = Composed([SQL("("), path_sql, SQL(")::daterange")])

            if op == "eq":
                return Composed([casted_path, SQL(" = "), Literal(val), SQL("::daterange")])
            if op == "neq":
                return Composed([casted_path, SQL(" != "), Literal(val), SQL("::daterange")])
            if op == "in":
                if not isinstance(val, list):
                    msg = f"'in' operator requires a list, got {type(val)}"
                    raise TypeError(msg)

                parts = [casted_path, SQL(" IN (")]
                for i, range_val in enumerate(val):
                    if i > 0:
                        parts.append(SQL(", "))
                    parts.extend([Literal(range_val), SQL("::daterange")])
                parts.append(SQL(")"))
                return Composed(parts)
            if op == "notin":
                if not isinstance(val, list):
                    msg = f"'notin' operator requires a list, got {type(val)}"
                    raise TypeError(msg)

                parts = [casted_path, SQL(" NOT IN (")]
                for i, range_val in enumerate(val):
                    if i > 0:
                        parts.append(SQL(", "))
                    parts.extend([Literal(range_val), SQL("::daterange")])
                parts.append(SQL(")"))
                return Composed(parts)

        # For range-specific operators
        elif op == "contains_date":
            # range @> date - range contains date
            casted_path = Composed([SQL("("), path_sql, SQL(")::daterange")])
            return Composed([casted_path, SQL(" @> "), Literal(val), SQL("::date")])

        elif op == "overlaps":
            # range1 && range2 - ranges overlap
            casted_path = Composed([SQL("("), path_sql, SQL(")::daterange")])
            return Composed([casted_path, SQL(" && "), Literal(val), SQL("::daterange")])

        elif op == "adjacent":
            # range1 -|- range2 - ranges are adjacent
            casted_path = Composed([SQL("("), path_sql, SQL(")::daterange")])
            return Composed([casted_path, SQL(" -|- "), Literal(val), SQL("::daterange")])

        elif op == "strictly_left":
            # range1 << range2 - range1 is strictly left of range2
            casted_path = Composed([SQL("("), path_sql, SQL(")::daterange")])
            return Composed([casted_path, SQL(" << "), Literal(val), SQL("::daterange")])

        elif op == "strictly_right":
            # range1 >> range2 - range1 is strictly right of range2
            casted_path = Composed([SQL("("), path_sql, SQL(")::daterange")])
            return Composed([casted_path, SQL(" >> "), Literal(val), SQL("::daterange")])

        elif op == "not_left":
            # range1 &> range2 - range1 does not extend left of range2
            casted_path = Composed([SQL("("), path_sql, SQL(")::daterange")])
            return Composed([casted_path, SQL(" &> "), Literal(val), SQL("::daterange")])

        elif op == "not_right":
            # range1 &< range2 - range1 does not extend right of range2
            casted_path = Composed([SQL("("), path_sql, SQL(")::daterange")])
            return Composed([casted_path, SQL(" &< "), Literal(val), SQL("::daterange")])

        # For pattern operators (contains, startswith, endswith), explicitly reject them
        elif op in ("contains", "startswith", "endswith"):
            raise ValueError(
                f"Pattern operator '{op}' is not supported for DateRange fields. "
                f"Use range operators: contains_date, overlaps, adjacent, strictly_left, "
                f"strictly_right, not_left, not_right, or basic: eq, neq, in, notin, isnull."
            )

        raise ValueError(f"Unsupported DateRange operator: {op}")

    def _is_daterange_type(self, field_type: type) -> bool:
        """Check if field_type is a DateRange type."""
        # Import here to avoid circular imports
        try:
            from fraiseql.types.scalars.daterange import DateRangeField

            return field_type == DateRangeField or (
                isinstance(field_type, type) and issubclass(field_type, DateRangeField)
            )
        except ImportError:
            return False


class LTreeOperatorStrategy(BaseOperatorStrategy):
    """Strategy for PostgreSQL ltree hierarchical path operators.

    Provides comprehensive filtering operations for hierarchical path data stored
    as PostgreSQL ltree values. Supports exact matching, hierarchical relationships,
    pattern matching, path analysis, and array operations.

    Basic Operations:
        eq: Exact path equality
        neq: Path inequality
        in_: Path in list of paths
        notin: Path not in list of paths

    Hierarchical Relationships:
        ancestor_of: Path is ancestor of target path (@> operator)
        descendant_of: Path is descendant of target path (<@ operator)

    Pattern Matching:
        matches_lquery: Path matches lquery pattern with wildcards (~ operator)
        matches_ltxtquery: Path matches text search pattern (? operator)
        matches_any_lquery: Path matches any of multiple lquery patterns

    Path Analysis:
        nlevel: Get number of path levels
        nlevel_eq/gt/gte/lt/lte: Filter by path depth
        subpath: Extract subpath segment (offset, length)
        index: Find position of sublabel in path
        index_eq/gte: Filter by sublabel position

    Path Manipulation:
        concat: Concatenate two paths (|| operator)
        lca: Find lowest common ancestor of multiple paths

    Array Operations:
        in_array: Path contained in array of paths (<@ operator)
        array_contains: Array contains target path (@> operator)

    Note: Pattern operators (contains, startswith, endswith) are explicitly
    rejected for ltree fields as they don't make sense for hierarchical paths.
    Use the specialized hierarchical operators instead.
    """

    def __init__(self) -> None:
        # Include hierarchical operators and basic operations, restrict problematic patterns
        super().__init__(
            [
                "eq",
                "neq",
                "in",
                "notin",  # Basic operations
                "ancestor_of",
                "descendant_of",  # Hierarchical relationships
                "matches_lquery",
                "matches_ltxtquery",  # Pattern matching
                # Path analysis operators
                "nlevel",
                "nlevel_eq",
                "nlevel_gt",
                "nlevel_gte",
                "nlevel_lt",
                "nlevel_lte",
                "subpath",
                "index",
                "index_eq",
                "index_gte",
                # Path manipulation operators
                "concat",
                "lca",
                # Array matching operators
                "matches_any_lquery",
                "in_array",
                "array_contains",
                "contains",
                "startswith",
                "endswith",  # Generic patterns (to restrict)
            ]
        )

    def can_handle(self, op: str, field_type: type | None = None) -> bool:
        """Check if this strategy can handle the given operator.

        LTree operators should only be used with LTree field types.
        For LTree types, we handle ALL operators to properly restrict unsupported ones.
        """
        if op not in self.operators:
            return False

        # Define LTree-specific operators that we can safely handle without field type info
        ltree_specific_ops = {"ancestor_of", "descendant_of", "matches_lquery", "matches_ltxtquery"}

        # If no field type provided, only handle LTree-specific operators
        # Generic operators (eq, contains, etc.) should go to appropriate generic strategies
        if field_type is None:
            return op in ltree_specific_ops

        # For LTree types, handle ALL the operators we're configured for
        # This ensures we can properly restrict the problematic ones
        return self._is_ltree_type(field_type)

    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build SQL for LTree operators with proper PostgreSQL ltree type casting.

        Generates optimized SQL for hierarchical path operations using PostgreSQL's
        native ltree operators and functions. All operations properly cast values
        to ltree type for correct comparison and indexing.

        Args:
            path_sql: SQL expression for the path field (e.g., data->>'path')
            op: Operator name (one of the 23 supported ltree operators)
            val: Value for the operation (type depends on operator)
            field_type: Field type (should be LTree for validation)

        Returns:
            Composed SQL expression ready for execution

        Raises:
            ValueError: If operator is not supported for ltree fields
            TypeError: If operator value has incorrect type
        """
        # Safety check: if we know the field type and it's NOT an LTree, something is wrong
        if field_type and not self._is_ltree_type(field_type):
            raise ValueError(
                f"LTree operator '{op}' can only be used with LTree fields, got {field_type}"
            )

        # For basic operations, cast both sides to ltree for proper PostgreSQL handling
        if op in ("eq", "neq", "in", "notin"):
            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])

            if op == "eq":
                return Composed([casted_path, SQL(" = "), Literal(val), SQL("::ltree")])
            if op == "neq":
                return Composed([casted_path, SQL(" != "), Literal(val), SQL("::ltree")])
            if op == "in":
                if not isinstance(val, list):
                    msg = f"'in' operator requires a list, got {type(val)}"
                    raise TypeError(msg)

                parts = [casted_path, SQL(" IN (")]
                for i, path in enumerate(val):
                    if i > 0:
                        parts.append(SQL(", "))
                    parts.extend([Literal(path), SQL("::ltree")])
                parts.append(SQL(")"))
                return Composed(parts)
            if op == "notin":
                if not isinstance(val, list):
                    msg = f"'notin' operator requires a list, got {type(val)}"
                    raise TypeError(msg)

                parts = [casted_path, SQL(" NOT IN (")]
                for i, path in enumerate(val):
                    if i > 0:
                        parts.append(SQL(", "))
                    parts.extend([Literal(path), SQL("::ltree")])
                parts.append(SQL(")"))
                return Composed(parts)

        # For hierarchical operators, use proper ltree operators
        elif op == "ancestor_of":
            # path1 @> path2 means path1 is ancestor of path2
            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])
            return Composed([casted_path, SQL(" @> "), Literal(val), SQL("::ltree")])

        elif op == "descendant_of":
            # path1 <@ path2 means path1 is descendant of path2
            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])
            return Composed([casted_path, SQL(" <@ "), Literal(val), SQL("::ltree")])

        elif op == "matches_lquery":
            # path ~ lquery means path matches lquery pattern
            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])
            return Composed([casted_path, SQL(" ~ "), Literal(val), SQL("::lquery")])

        elif op == "matches_ltxtquery":
            # path ? ltxtquery means path matches ltxtquery text query
            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])
            return Composed([casted_path, SQL(" ? "), Literal(val), SQL("::ltxtquery")])

        # Path analysis operators
        elif op == "nlevel":
            # nlevel(ltree) - returns number of labels in path
            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])
            return Composed([SQL("nlevel("), casted_path, SQL(")")])

        elif op.startswith("nlevel_"):
            # Extract comparison operator (eq, gt, gte, lt, lte)
            comparison = op.replace("nlevel_", "")
            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])
            nlevel_expr = Composed([SQL("nlevel("), casted_path, SQL(")")])

            comparison_ops = {"eq": "=", "gt": ">", "gte": ">=", "lt": "<", "lte": "<="}
            sql_op = comparison_ops[comparison]

            return Composed([nlevel_expr, SQL(f" {sql_op} "), Literal(val)])

        elif op == "subpath":
            # val is tuple (offset, length)
            if not isinstance(val, tuple) or len(val) != 2:
                raise TypeError(f"subpath operator requires a tuple (offset, length), got {val}")
            offset, length = val
            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])
            return Composed(
                [
                    SQL("subpath("),
                    casted_path,
                    SQL(", "),
                    Literal(offset),
                    SQL(", "),
                    Literal(length),
                    SQL(")"),
                ]
            )

        elif op == "index":
            # index(path, sublabel) returns int position
            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])
            return Composed([SQL("index("), casted_path, SQL(", "), Literal(val), SQL("::ltree)")])

        elif op == "index_eq":
            # Filter by exact position
            if not isinstance(val, tuple) or len(val) != 2:
                raise TypeError(
                    f"index_eq operator requires a tuple (sublabel, position), got {val}"
                )
            sublabel, position = val
            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])
            index_expr = Composed(
                [SQL("index("), casted_path, SQL(", "), Literal(sublabel), SQL("::ltree)")]
            )
            return Composed([index_expr, SQL(" = "), Literal(position)])

        elif op == "index_gte":
            # Filter by minimum position
            if not isinstance(val, tuple) or len(val) != 2:
                raise TypeError(
                    f"index_gte operator requires a tuple (sublabel, min_position), got {val}"
                )
            sublabel, min_position = val
            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])
            index_expr = Composed(
                [SQL("index("), casted_path, SQL(", "), Literal(sublabel), SQL("::ltree)")]
            )
            return Composed([index_expr, SQL(" >= "), Literal(min_position)])

        elif op == "concat":
            # path1 || path2 - concatenate two ltree paths
            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])
            return Composed([casted_path, SQL(" || "), Literal(val), SQL("::ltree")])

        elif op == "lca":
            # lca(ARRAY[path1, path2, ...]) - lowest common ancestor
            if not isinstance(val, list):
                raise TypeError(f"lca operator requires a list of paths, got {type(val)}")

            if not val:  # Empty list
                raise ValueError("lca operator requires at least one path")

            # Build lca(ARRAY['path1'::ltree, 'path2'::ltree, ...])
            parts = [SQL("lca(ARRAY[")]
            for i, path in enumerate(val):
                if i > 0:
                    parts.append(SQL(", "))
                parts.extend([Literal(path), SQL("::ltree")])
            parts.append(SQL("])"))

            return Composed(parts)

        elif op == "matches_any_lquery":
            # path ? ARRAY[lquery1, lquery2, ...]
            if not isinstance(val, list):
                raise TypeError(f"matches_any_lquery requires a list, got {type(val)}")

            if not val:  # Empty list
                raise ValueError("matches_any_lquery requires at least one pattern")

            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])

            # Build ARRAY[lquery1, lquery2, ...]
            parts = [casted_path, SQL(" ? ARRAY[")]
            for i, pattern in enumerate(val):
                if i > 0:
                    parts.append(SQL(", "))
                parts.append(Literal(pattern))  # PostgreSQL will cast to lquery
            parts.append(SQL("]"))

            return Composed(parts)

        elif op == "in_array":
            # path <@ ARRAY[path1, path2, ...]
            if not isinstance(val, list):
                raise TypeError(f"in_array requires a list, got {type(val)}")

            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])

            parts = []
            parts.append(casted_path)
            parts.append(SQL(" <@ ARRAY["))
            for i, path in enumerate(val):
                if i > 0:
                    parts.append(SQL(", "))
                parts.append(Literal(path))
                parts.append(SQL("::ltree"))
            parts.append(SQL("]"))

            return Composed(parts)

        elif op == "array_contains":
            # ARRAY[path1, path2, ...] @> target_path
            if not isinstance(val, tuple) or len(val) != 2:
                raise TypeError(
                    f"array_contains requires a tuple (paths_array, target_path), got {val}"
                )

            paths_array, target_path = val
            if not isinstance(paths_array, list):
                raise TypeError(
                    f"array_contains first element must be a list, got {type(paths_array)}"
                )

            # Build ARRAY['path1'::ltree, 'path2'::ltree, ...] @> 'target'::ltree
            parts = [SQL("ARRAY[")]
            for i, path in enumerate(paths_array):
                if i > 0:
                    parts.append(SQL(", "))
                parts.extend([Literal(path), SQL("::ltree")])
            parts.extend([SQL("] @> "), Literal(target_path), SQL("::ltree")])

            return Composed(parts)

        # For pattern operators (contains, startswith, endswith), explicitly reject them
        elif op in ("contains", "startswith", "endswith"):
            raise ValueError(
                f"Pattern operator '{op}' is not supported for LTree fields. "
                f"Use hierarchical operators: ancestor_of, descendant_of, matches_lquery, "
                f"matches_ltxtquery, or basic: eq, neq, in, notin, isnull."
            )

        raise ValueError(f"Unsupported LTree operator: {op}")

    def _is_ltree_type(self, field_type: type) -> bool:
        """Check if field_type is an LTree type."""
        # Import here to avoid circular imports
        try:
            from fraiseql.types import LTree
            from fraiseql.types.scalars.ltree import LTreeField

            return field_type in (LTree, LTreeField) or (
                isinstance(field_type, type) and issubclass(field_type, LTreeField)
            )
        except ImportError:
            return False


class MacAddressOperatorStrategy(BaseOperatorStrategy):
    """Strategy for MAC address-specific operators with PostgreSQL macaddr type casting."""

    def __init__(self) -> None:
        # Include ALL operators to properly restrict unsupported ones
        super().__init__(["eq", "neq", "in", "notin", "contains", "startswith", "endswith"])

    def can_handle(self, op: str, field_type: type | None = None) -> bool:
        """Check if this strategy can handle the given operator.

        MAC address operators should only be used with MAC address field types.
        For MAC address types, we handle ALL operators to properly restrict unsupported ones.
        """
        if op not in self.operators:
            return False

        # MAC address operators are all generic (eq, neq, in, notin, contains, startswith, endswith)
        # There are no MAC-address-specific operators, so we cannot safely handle any operation
        # without knowing the field type. All operations should go to generic strategies.
        if field_type is None:
            return False

        # For MAC address types, handle ALL the operators we're configured for
        # This ensures we can properly restrict the problematic ones
        return self._is_mac_address_type(field_type)

    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build SQL for MAC address operators with proper macaddr casting."""
        # Safety check: if we know the field type and it's NOT a MAC address, something is wrong
        if field_type and not self._is_mac_address_type(field_type):
            raise ValueError(
                f"MAC address operator '{op}' can only be used with MAC address fields, "
                f"got {field_type}"
            )

        # For supported operators, cast the JSONB field to macaddr for proper PostgreSQL handling
        if op in ("eq", "neq", "in", "notin"):
            casted_path = Composed([SQL("("), path_sql, SQL(")::macaddr")])

            if op == "eq":
                return Composed([casted_path, SQL(" = "), Literal(val), SQL("::macaddr")])
            if op == "neq":
                return Composed([casted_path, SQL(" != "), Literal(val), SQL("::macaddr")])
            if op == "in":
                if not isinstance(val, list):
                    msg = f"'in' operator requires a list, got {type(val)}"
                    raise TypeError(msg)

                parts = [casted_path, SQL(" IN (")]
                for i, mac in enumerate(val):
                    if i > 0:
                        parts.append(SQL(", "))
                    parts.extend([Literal(mac), SQL("::macaddr")])
                parts.append(SQL(")"))
                return Composed(parts)
            if op == "notin":
                if not isinstance(val, list):
                    msg = f"'notin' operator requires a list, got {type(val)}"
                    raise TypeError(msg)

                parts = [casted_path, SQL(" NOT IN (")]
                for i, mac in enumerate(val):
                    if i > 0:
                        parts.append(SQL(", "))
                    parts.extend([Literal(mac), SQL("::macaddr")])
                parts.append(SQL(")"))
            return Composed(parts)

        if op == "matches_any_lquery":
            # path ? ARRAY[lquery1, lquery2, ...]
            if not isinstance(val, list):
                raise TypeError(f"matches_any_lquery requires a list, got {type(val)}")

            if not val:  # Empty list
                raise ValueError("matches_any_lquery requires at least one pattern")

            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])

            # Build ARRAY[lquery1, lquery2, ...]
            parts = [casted_path, SQL(" ? ARRAY[")]
            for i, pattern in enumerate(val):
                if i > 0:
                    parts.append(SQL(", "))
                parts.append(Literal(pattern))  # PostgreSQL will cast to lquery
            parts.append(SQL("]"))

            return Composed(parts)

        if op == "in_array":
            # path <@ ARRAY[path1, path2, ...]
            if not isinstance(val, list):
                raise TypeError(f"in_array requires a list, got {type(val)}")

            casted_path = Composed([SQL("("), path_sql, SQL(")::ltree")])

            parts = []
            parts.append(casted_path)
            parts.append(SQL(" <@ ARRAY["))
            for i, path in enumerate(val):
                if i > 0:
                    parts.append(SQL(", "))
                parts.append(Literal(path))
                parts.append(SQL("::ltree"))
            parts.append(SQL("]"))

            return Composed(parts)

        if op == "array_contains":
            # ARRAY[path1, path2, ...] @> target_path
            if not isinstance(val, tuple) or len(val) != 2:
                raise TypeError(
                    f"array_contains requires a tuple (paths_array, target_path), got {val}"
                )

            paths_array, target_path = val
            if not isinstance(paths_array, list):
                raise TypeError(
                    f"array_contains first element must be a list, got {type(paths_array)}"
                )

            # Build ARRAY['path1'::ltree, 'path2'::ltree, ...] @> 'target'::ltree
            parts = [SQL("ARRAY[")]
            for i, path in enumerate(paths_array):
                if i > 0:
                    parts.append(SQL(", "))
                parts.extend([Literal(path), SQL("::ltree")])
            parts.extend([SQL("] @> "), Literal(target_path), SQL("::ltree")])

            return Composed(parts)

        # For pattern operators (contains, startswith, endswith), explicitly reject them
        if op in ("contains", "startswith", "endswith"):
            raise ValueError(
                f"Pattern operator '{op}' is not supported for MAC address fields. "
                f"Use only: eq, neq, in, notin, isnull for MAC address filtering."
            )

        raise ValueError(f"Unsupported MAC address operator: {op}")

    def _is_mac_address_type(self, field_type: type) -> bool:
        """Check if field_type is a MAC address type."""
        # Import here to avoid circular imports
        try:
            from fraiseql.types import MacAddress
            from fraiseql.types.scalars.mac_address import MacAddressField

            return field_type in (MacAddress, MacAddressField) or (
                isinstance(field_type, type) and issubclass(field_type, MacAddressField)
            )
        except ImportError:
            return False


class CoordinateOperatorStrategy(BaseOperatorStrategy):
    """Strategy for geographic coordinate operators with PostgreSQL POINT type casting.

    Provides comprehensive coordinate filtering operations including exact equality,
    distance calculations, and PostgreSQL POINT type integration.

    Basic Operations:
        eq: Exact coordinate equality
        neq: Coordinate inequality
        in: Coordinate in list of coordinates
        notin: Coordinate not in list of coordinates

    Distance Operations:
        distance_within: Find coordinates within distance (meters) of center point
    """

    def __init__(self) -> None:
        super().__init__(["eq", "neq", "in", "notin", "distance_within"])

    def can_handle(self, op: str, field_type: type | None = None) -> bool:
        """Check if this strategy can handle the given operator.

        Coordinate operators should only be used with Coordinate field types.
        For Coordinate types, we handle ALL operators to properly restrict unsupported ones.
        """
        if op not in self.operators:
            return False

        # Define coordinate-specific operators that we can safely handle without field type info
        coordinate_specific_ops = {"distance_within"}

        # If no field type provided, only handle coordinate-specific operators
        # Generic operators (eq, neq, in, notin) should go to appropriate generic strategies
        if field_type is None:
            return op in coordinate_specific_ops

        # For Coordinate types, handle ALL the operators we're configured for
        # This ensures we can properly restrict the problematic ones
        return self._is_coordinate_type(field_type)

    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build SQL for coordinate operators with proper PostgreSQL POINT type casting."""
        # Safety check: if we know the field type and it's NOT a Coordinate, something is wrong
        if field_type and not self._is_coordinate_type(field_type):
            raise ValueError(
                f"Coordinate operator '{op}' can only be used with Coordinate fields, "
                f"got {field_type}"
            )

        # For basic operations, cast both sides to point for proper PostgreSQL handling
        if op in ("eq", "neq", "in", "notin"):
            casted_path = Composed([SQL("("), path_sql, SQL(")::point")])

            if op == "eq":
                if not isinstance(val, tuple) or len(val) != 2:
                    raise TypeError(
                        f"eq operator requires a coordinate tuple (lat, lng), got {val}"
                    )
                lat, lng = val
                return Composed(
                    [casted_path, SQL(" = POINT("), Literal(lng), SQL(","), Literal(lat), SQL(")")]
                )

            if op == "neq":
                if not isinstance(val, tuple) or len(val) != 2:
                    raise TypeError(
                        f"neq operator requires a coordinate tuple (lat, lng), got {val}"
                    )
                lat, lng = val
                return Composed(
                    [
                        casted_path,
                        SQL(" != POINT("),
                        Literal(lng),
                        SQL(","),
                        Literal(lat),
                        SQL(")"),
                    ]
                )

            if op == "in":
                if not isinstance(val, list):
                    msg = f"'in' operator requires a list, got {type(val)}"
                    raise TypeError(msg)

                parts = [casted_path, SQL(" IN (")]
                for i, coord in enumerate(val):
                    if i > 0:
                        parts.append(SQL(", "))
                    if not isinstance(coord, tuple) or len(coord) != 2:
                        raise TypeError(
                            f"in operator requires coordinate tuples (lat, lng), got {coord}"
                        )
                    lat, lng = coord
                    parts.extend([SQL("POINT("), Literal(lng), SQL(","), Literal(lat), SQL(")")])
                parts.append(SQL(")"))
                return Composed(parts)

            if op == "notin":
                if not isinstance(val, list):
                    msg = f"'notin' operator requires a list, got {type(val)}"
                    raise TypeError(msg)

                parts = [casted_path, SQL(" NOT IN (")]
                for i, coord in enumerate(val):
                    if i > 0:
                        parts.append(SQL(", "))
                    if not isinstance(coord, tuple) or len(coord) != 2:
                        raise TypeError(
                            f"notin operator requires coordinate tuples (lat, lng), got {coord}"
                        )
                    lat, lng = coord
                    parts.extend([SQL("POINT("), Literal(lng), SQL(","), Literal(lat), SQL(")")])
                parts.append(SQL(")"))
                return Composed(parts)

        # For distance operations
        elif op == "distance_within":
            # val should be a tuple: (center_coord, distance_meters)
            if not isinstance(val, tuple) or len(val) != 2:
                raise TypeError(
                    f"distance_within operator requires a tuple "
                    f"(center_coord, distance_meters), got {val}"
                )

            center_coord, distance_meters = val
            if not isinstance(center_coord, tuple) or len(center_coord) != 2:
                raise TypeError(
                    f"distance_within center must be a coordinate tuple "
                    f"(lat, lng), got {center_coord}"
                )
            if not isinstance(distance_meters, (int, float)) or distance_meters < 0:
                raise TypeError(
                    f"distance_within distance must be a positive number, got {distance_meters}"
                )

            # Import coordinate distance builders
            # Get distance method from environment or use default
            import os

            from fraiseql.sql.where.operators.coordinate import (
                build_coordinate_distance_within_sql,
                build_coordinate_distance_within_sql_earthdistance,
                build_coordinate_distance_within_sql_haversine,
            )

            method = os.environ.get("FRAISEQL_COORDINATE_DISTANCE_METHOD", "haversine").lower()

            # Build SQL based on configured method
            if method == "postgis":
                return build_coordinate_distance_within_sql(path_sql, center_coord, distance_meters)
            if method == "earthdistance":
                return build_coordinate_distance_within_sql_earthdistance(
                    path_sql, center_coord, distance_meters
                )
            if method == "haversine":
                return build_coordinate_distance_within_sql_haversine(
                    path_sql, center_coord, distance_meters
                )
            raise ValueError(
                f"Invalid coordinate_distance_method: '{method}'. "
                f"Valid options: 'postgis', 'haversine', 'earthdistance'"
            )

        raise ValueError(f"Unsupported coordinate operator: {op}")

    def _is_coordinate_type(self, field_type: type) -> bool:
        """Check if field_type is a Coordinate type."""
        # Import here to avoid circular imports
        try:
            from fraiseql.types import Coordinate
            from fraiseql.types.scalars.coordinates import CoordinateField

            return field_type in (Coordinate, CoordinateField) or (
                isinstance(field_type, type) and issubclass(field_type, CoordinateField)
            )
        except ImportError:
            return False


class NetworkOperatorStrategy(BaseOperatorStrategy):
    """Strategy for network-specific operators with comprehensive IP address classification.

    Provides complete network analysis capabilities for IP address fields:

    Core Operations (v0.6.0+):
    - Basic: eq, neq, in, notin, nin
    - Subnet: inSubnet, inRange
    - Classification: isPrivate, isPublic, isIPv4, isIPv6

    Enhanced Operations (v0.7.4+):
    - Loopback: isLoopback (RFC 3330/4291)
    - Link-local: isLinkLocal (RFC 3927/4291)
    - Multicast: isMulticast (RFC 3171/4291)
    - Documentation: isDocumentation (RFC 5737/3849)
    - Carrier-grade: isCarrierGrade (RFC 6598)

    All operators support both IPv4 and IPv6 addresses where applicable.
    """

    def __init__(self) -> None:
        # Include basic operations and network-specific operators
        super().__init__(
            [
                "eq",
                "neq",
                "in",
                "notin",
                "nin",  # Basic operations
                "inSubnet",
                "inRange",
                "isPrivate",
                "isPublic",
                "isIPv4",
                "isIPv6",  # Network-specific operations
                "isLoopback",
                "isLinkLocal",
                "isMulticast",
                "isDocumentation",
                "isCarrierGrade",  # Enhanced network-specific operations
            ]
        )

    def can_handle(self, op: str, field_type: type | None = None) -> bool:
        """Check if this strategy can handle the given operator.

        Network operators should only be used with IP address field types.
        For IP address types, we handle ALL operators to properly restrict unsupported ones.
        """
        if op not in self.operators:
            return False

        # Define network-specific operators that we can safely handle without field type info
        network_specific_ops = {
            "inSubnet",
            "inRange",
            "isPrivate",
            "isPublic",
            "isIPv4",
            "isIPv6",
            "isLoopback",
            "isLinkLocal",
            "isMulticast",
            "isDocumentation",
            "isCarrierGrade",
        }

        # If no field type provided, only handle network-specific operators
        # Generic operators (eq, neq, in, notin) should go to appropriate generic strategies
        if field_type is None:
            return op in network_specific_ops

        # For IP address types, handle ALL the operators we're configured for
        # This ensures we can properly restrict the problematic ones
        return self._is_ip_address_type(field_type)

    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build SQL for network operators."""
        # Apply consistent type casting for network operations
        # Network operators are ONLY used for IP addresses, so we should always cast to ::inet
        # even when field_type is not provided (repository calls don't pass field_type)
        if field_type and not self._is_ip_address_type(field_type):
            # Safety check: if we know the field type and it's NOT an IP address, something is wrong
            raise ValueError(
                f"Network operator '{op}' can only be used with IP address fields, got {field_type}"
            )

        # Always cast to ::inet for network operations since these operators are IP-specific
        # We need parentheses around the JSONB extraction for proper PostgreSQL parsing
        casted_path = Composed([SQL("("), path_sql, SQL(")::inet")])

        # For basic operations, cast both sides to inet for proper PostgreSQL handling
        if op in ("eq", "neq", "in", "notin", "nin"):
            if op == "eq":
                return Composed([casted_path, SQL(" = "), Literal(val), SQL("::inet")])
            if op == "neq":
                return Composed([casted_path, SQL(" != "), Literal(val), SQL("::inet")])
            if op == "in":
                if not isinstance(val, list):
                    msg = f"'in' operator requires a list, got {type(val)}"
                    raise TypeError(msg)

                parts = [casted_path, SQL(" IN (")]
                for i, ip in enumerate(val):
                    if i > 0:
                        parts.append(SQL(", "))
                    parts.extend([Literal(ip), SQL("::inet")])
                parts.append(SQL(")"))
                return Composed(parts)
            if op == "notin":
                if not isinstance(val, list):
                    msg = f"'notin' operator requires a list, got {type(val)}"
                    raise TypeError(msg)

                parts = [casted_path, SQL(" NOT IN (")]
                for i, ip in enumerate(val):
                    if i > 0:
                        parts.append(SQL(", "))
                    parts.extend([Literal(ip), SQL("::inet")])
                parts.append(SQL(")"))
                return Composed(parts)
            if op == "nin":
                # nin is an alias for notin
                if not isinstance(val, list):
                    msg = f"'nin' operator requires a list, got {type(val)}"
                    raise TypeError(msg)

                parts = [casted_path, SQL(" NOT IN (")]
                for i, ip in enumerate(val):
                    if i > 0:
                        parts.append(SQL(", "))
                    parts.extend([Literal(ip), SQL("::inet")])
                parts.append(SQL(")"))
                return Composed(parts)

        if op == "inSubnet":
            # PostgreSQL subnet matching using <<= operator
            return Composed([casted_path, SQL(" <<= "), Literal(val), SQL("::inet")])

        if op == "inRange":
            # IP range comparison
            if not isinstance(val, dict) or "from_" not in val or "to" not in val:
                # Try alternative field names
                if not isinstance(val, dict) or "from" not in val or "to" not in val:
                    raise ValueError(f"inRange requires dict with 'from' and 'to' keys, got {val}")
                from_ip = val["from"]
                to_ip = val["to"]
            else:
                from_ip = val["from_"]
                to_ip = val["to"]

            return Composed(
                [
                    casted_path,
                    SQL(" >= "),
                    Literal(from_ip),
                    SQL("::inet"),
                    SQL(" AND "),
                    casted_path,
                    SQL(" <= "),
                    Literal(to_ip),
                    SQL("::inet"),
                ]
            )

        if op == "isPrivate":
            # RFC 1918 private network ranges + localhost + link-local
            # Build a single compound condition to avoid multiple casted_path repeats
            if val:
                # isPrivate=True: IP is in any private range
                return Composed(
                    [
                        SQL("("),
                        casted_path,
                        SQL(" <<= '10.0.0.0/8'::inet OR "),
                        casted_path,
                        SQL(" <<= '172.16.0.0/12'::inet OR "),
                        casted_path,
                        SQL(" <<= '192.168.0.0/16'::inet OR "),
                        casted_path,
                        SQL(" <<= '127.0.0.0/8'::inet OR "),
                        casted_path,
                        SQL(" <<= '169.254.0.0/16'::inet"),
                        SQL(")"),
                    ]
                )
            # isPrivate=False: IP is NOT in any private range
            return Composed(
                [
                    SQL("NOT ("),
                    casted_path,
                    SQL(" <<= '10.0.0.0/8'::inet OR "),
                    casted_path,
                    SQL(" <<= '172.16.0.0/12'::inet OR "),
                    casted_path,
                    SQL(" <<= '192.168.0.0/16'::inet OR "),
                    casted_path,
                    SQL(" <<= '127.0.0.0/8'::inet OR "),
                    casted_path,
                    SQL(" <<= '169.254.0.0/16'::inet"),
                    SQL(")"),
                ]
            )

        if op == "isPublic":
            # Public is the inverse of private
            if val:
                # isPublic=True: IP is NOT in any private range
                return Composed(
                    [
                        SQL("NOT ("),
                        casted_path,
                        SQL(" <<= '10.0.0.0/8'::inet OR "),
                        casted_path,
                        SQL(" <<= '172.16.0.0/12'::inet OR "),
                        casted_path,
                        SQL(" <<= '192.168.0.0/16'::inet OR "),
                        casted_path,
                        SQL(" <<= '127.0.0.0/8'::inet OR "),
                        casted_path,
                        SQL(" <<= '169.254.0.0/16'::inet"),
                        SQL(")"),
                    ]
                )
            # isPublic=False: IP IS in private range
            return Composed(
                [
                    SQL("("),
                    casted_path,
                    SQL(" <<= '10.0.0.0/8'::inet OR "),
                    casted_path,
                    SQL(" <<= '172.16.0.0/12'::inet OR "),
                    casted_path,
                    SQL(" <<= '192.168.0.0/16'::inet OR "),
                    casted_path,
                    SQL(" <<= '127.0.0.0/8'::inet OR "),
                    casted_path,
                    SQL(" <<= '169.254.0.0/16'::inet"),
                    SQL(")"),
                ]
            )

        if op == "isIPv4":
            # Check IP version using family() function
            if val:
                return Composed([SQL("family("), casted_path, SQL(") = 4")])
            return Composed([SQL("family("), casted_path, SQL(") != 4")])

        if op == "isIPv6":
            # Check IP version using family() function
            if val:
                return Composed([SQL("family("), casted_path, SQL(") = 6")])
            return Composed([SQL("family("), casted_path, SQL(") != 6")])

        if op == "isLoopback":
            # RFC 3330 (IPv4) / RFC 4291 (IPv6) loopback addresses
            # IPv4: 127.0.0.0/8, IPv6: ::1/128
            if val:
                return Composed(
                    [
                        SQL("("),
                        casted_path,
                        SQL(" <<= '127.0.0.0/8'::inet OR "),
                        casted_path,
                        SQL(" = '::1'::inet"),
                        SQL(")"),
                    ]
                )
            # isLoopback=False: NOT (IPv4 loopback OR IPv6 loopback)
            return Composed(
                [
                    SQL("NOT ("),
                    casted_path,
                    SQL(" <<= '127.0.0.0/8'::inet OR "),
                    casted_path,
                    SQL(" = '::1'::inet"),
                    SQL(")"),
                ]
            )

        if op == "isLinkLocal":
            # RFC 3927 (IPv4) / RFC 4291 (IPv6) link-local addresses
            # IPv4: 169.254.0.0/16 (APIPA), IPv6: fe80::/10
            if val:
                return Composed(
                    [
                        SQL("("),
                        casted_path,
                        SQL(" <<= '169.254.0.0/16'::inet OR "),
                        casted_path,
                        SQL(" <<= 'fe80::/10'::inet"),
                        SQL(")"),
                    ]
                )
            # isLinkLocal=False: NOT (IPv4 link-local OR IPv6 link-local)
            return Composed(
                [
                    SQL("NOT ("),
                    casted_path,
                    SQL(" <<= '169.254.0.0/16'::inet OR "),
                    casted_path,
                    SQL(" <<= 'fe80::/10'::inet"),
                    SQL(")"),
                ]
            )

        if op == "isMulticast":
            # RFC 3171 (IPv4) / RFC 4291 (IPv6) multicast addresses
            # IPv4: 224.0.0.0/4, IPv6: ff00::/8
            if val:
                return Composed(
                    [
                        SQL("("),
                        casted_path,
                        SQL(" <<= '224.0.0.0/4'::inet OR "),
                        casted_path,
                        SQL(" <<= 'ff00::/8'::inet"),
                        SQL(")"),
                    ]
                )
            # isMulticast=False: NOT (IPv4 multicast OR IPv6 multicast)
            return Composed(
                [
                    SQL("NOT ("),
                    casted_path,
                    SQL(" <<= '224.0.0.0/4'::inet OR "),
                    casted_path,
                    SQL(" <<= 'ff00::/8'::inet"),
                    SQL(")"),
                ]
            )

        if op == "isDocumentation":
            # RFC 5737 (IPv4) / RFC 3849 (IPv6) documentation addresses
            # IPv4: 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24
            # IPv6: 2001:db8::/32
            if val:
                return Composed(
                    [
                        SQL("("),
                        casted_path,
                        SQL(" <<= '192.0.2.0/24'::inet OR "),
                        casted_path,
                        SQL(" <<= '198.51.100.0/24'::inet OR "),
                        casted_path,
                        SQL(" <<= '203.0.113.0/24'::inet OR "),
                        casted_path,
                        SQL(" <<= '2001:db8::/32'::inet"),
                        SQL(")"),
                    ]
                )
            # isDocumentation=False: NOT (any documentation range)
            return Composed(
                [
                    SQL("NOT ("),
                    casted_path,
                    SQL(" <<= '192.0.2.0/24'::inet OR "),
                    casted_path,
                    SQL(" <<= '198.51.100.0/24'::inet OR "),
                    casted_path,
                    SQL(" <<= '203.0.113.0/24'::inet OR "),
                    casted_path,
                    SQL(" <<= '2001:db8::/32'::inet"),
                    SQL(")"),
                ]
            )

        if op == "isCarrierGrade":
            # RFC 6598 Carrier-Grade NAT addresses
            # IPv4: 100.64.0.0/10 (IPv6 has no equivalent)
            if val:
                return Composed(
                    [
                        casted_path,
                        SQL(" <<= '100.64.0.0/10'::inet"),
                    ]
                )
            # isCarrierGrade=False: NOT in carrier-grade range
            return Composed(
                [
                    SQL("NOT ("),
                    casted_path,
                    SQL(" <<= '100.64.0.0/10'::inet"),
                    SQL(")"),
                ]
            )

        raise ValueError(f"Unsupported network operator: {op}")


class OperatorRegistry:
    """Registry for operator strategies."""

    def __init__(self) -> None:
        """Initialize the registry with all available strategies."""
        self.strategies: list[OperatorStrategy] = [
            NullOperatorStrategy(),
            DateRangeOperatorStrategy(),  # Must come before ComparisonOperatorStrategy
            LTreeOperatorStrategy(),  # Must come before ComparisonOperatorStrategy
            CoordinateOperatorStrategy(),  # Must come before ComparisonOperatorStrategy
            MacAddressOperatorStrategy(),  # Must come before ComparisonOperatorStrategy
            NetworkOperatorStrategy(),  # Must come before ComparisonOperatorStrategy
            ComparisonOperatorStrategy(),
            PatternMatchingStrategy(),  # Move before JsonOperatorStrategy
            JsonOperatorStrategy(),
            ListOperatorStrategy(),
            PathOperatorStrategy(),
        ]

    def get_strategy(self, op: str, field_type: type | None = None) -> OperatorStrategy:
        """Get the appropriate strategy for an operator."""
        for strategy in self.strategies:
            # Try to pass field_type if the strategy supports it
            try:
                if hasattr(strategy, "can_handle"):
                    # Check if can_handle accepts field_type parameter
                    import inspect

                    sig = inspect.signature(strategy.can_handle)
                    if "field_type" in sig.parameters:
                        if strategy.can_handle(op, field_type):
                            return strategy
                    elif strategy.can_handle(op):
                        return strategy
            except Exception:
                # Fallback to basic can_handle
                if strategy.can_handle(op):
                    return strategy
        raise ValueError(f"Unsupported operator: {op}")

    def build_sql(
        self,
        path_sql: SQL,
        op: str,
        val: Any,
        field_type: type | None = None,
    ) -> Composed:
        """Build SQL for the given operator."""
        strategy = self.get_strategy(op, field_type)
        return strategy.build_sql(path_sql, op, val, field_type)


# Global registry instance
_operator_registry = OperatorRegistry()


def get_operator_registry() -> OperatorRegistry:
    """Get the global operator registry."""
    return _operator_registry
