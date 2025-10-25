"""APQ storage backend abstract interface for FraiseQL."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class APQStorageBackend(ABC):
    """Abstract base class for APQ storage backends.

    This interface provides pluggable storage support for FraiseQL's APQ system,
    enabling different storage implementations for persisted queries and cached responses.

    Backends can support:
    1. Persistent query storage by hash
    2. Pre-computed JSON response caching
    3. Direct JSON passthrough (bypass GraphQL execution for cached responses)
    """

    @abstractmethod
    def get_persisted_query(self, hash_value: str) -> Optional[str]:
        """Retrieve stored query by hash.

        Args:
            hash_value: SHA256 hash of the persisted query

        Returns:
            GraphQL query string if found, None otherwise
        """

    @abstractmethod
    def store_persisted_query(self, hash_value: str, query: str) -> None:
        """Store query by hash.

        Args:
            hash_value: SHA256 hash of the query
            query: GraphQL query string to store
        """

    @abstractmethod
    def get_cached_response(
        self, hash_value: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached JSON response for APQ hash.

        This enables direct JSON passthrough, bypassing GraphQL execution
        for pre-computed responses.

        Args:
            hash_value: SHA256 hash of the persisted query
            context: Optional request context containing user/tenant information

        Returns:
            Cached GraphQL response dict if found, None otherwise
        """

    @abstractmethod
    def store_cached_response(
        self, hash_value: str, response: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store pre-computed JSON response for APQ hash.

        Args:
            hash_value: SHA256 hash of the persisted query
            response: GraphQL response dict to cache
            context: Optional request context containing user/tenant information
        """

    def extract_tenant_id(self, context: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract tenant_id from various context structures.

        Supports multiple context patterns:
        1. JWT metadata style: context['user']['metadata']['tenant_id']
        2. Direct on user: context['user']['tenant_id']
        3. Direct in context: context['tenant_id']

        Args:
            context: Request context dictionary

        Returns:
            Tenant ID if found, None otherwise
        """
        if not context:
            return None

        # Try JWT metadata pattern (Auth0 style)
        if "user" in context and isinstance(context["user"], dict):
            user = context["user"]
            if (
                "metadata" in user
                and isinstance(user["metadata"], dict)
                and "tenant_id" in user["metadata"]
            ):
                return user["metadata"]["tenant_id"]
            # Try direct tenant_id on user
            if "tenant_id" in user:
                return user["tenant_id"]

        # Try direct tenant_id in context
        if "tenant_id" in context:
            return context["tenant_id"]

        return None
