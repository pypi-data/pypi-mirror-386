"""Memory-based APQ storage backend for FraiseQL."""

import logging
from typing import Any, Dict, Optional

from .base import APQStorageBackend

logger = logging.getLogger(__name__)


class MemoryAPQBackend(APQStorageBackend):
    """In-memory APQ storage backend with tenant isolation.

    This backend stores persisted queries and cached responses in memory,
    with automatic tenant isolation when context is provided.

    Note: This storage is not persistent across application restarts and
    is not shared between different backend instances.
    """

    def __init__(self) -> None:
        """Initialize the memory backend with empty storage."""
        self._query_storage: Dict[str, str] = {}
        self._response_storage: Dict[str, Dict[str, Any]] = {}

    def _get_cache_key(self, hash_value: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key with tenant isolation.

        Args:
            hash_value: SHA256 hash of the persisted query
            context: Optional request context containing user/tenant information

        Returns:
            Cache key in format "{tenant_id}:{hash}" or just "{hash}" if no tenant
        """
        if context:
            tenant_id = self.extract_tenant_id(context)
            if tenant_id:
                return f"{tenant_id}:{hash_value}"
        return hash_value

    def get_persisted_query(self, hash_value: str) -> Optional[str]:
        """Retrieve stored query by hash.

        Args:
            hash_value: SHA256 hash of the persisted query

        Returns:
            GraphQL query string if found, None otherwise
        """
        if not hash_value:
            return None

        query = self._query_storage.get(hash_value)
        if query:
            logger.debug(f"Retrieved APQ query with hash {hash_value[:8]}...")
        else:
            logger.debug(f"APQ query not found for hash {hash_value[:8]}...")

        return query

    def store_persisted_query(self, hash_value: str, query: str) -> None:
        """Store query by hash.

        Args:
            hash_value: SHA256 hash of the query
            query: GraphQL query string to store
        """
        self._query_storage[hash_value] = query
        logger.debug(f"Stored APQ query with hash {hash_value[:8]}...")

    def get_cached_response(
        self, hash_value: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached JSON response for APQ hash.

        Args:
            hash_value: SHA256 hash of the persisted query
            context: Optional request context containing user/tenant information

        Returns:
            Cached GraphQL response dict if found, None otherwise
        """
        if not hash_value:
            return None

        # Use tenant-aware cache key
        cache_key = self._get_cache_key(hash_value, context)
        response = self._response_storage.get(cache_key)

        if response:
            tenant_info = f" (tenant: {cache_key.split(':')[0]})" if ":" in cache_key else ""
            logger.debug(f"Retrieved cached response for hash {hash_value[:8]}...{tenant_info}")
        else:
            logger.debug(f"Cached response not found for key {cache_key[:20]}...")

        return response

    def store_cached_response(
        self, hash_value: str, response: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store pre-computed JSON response for APQ hash.

        Args:
            hash_value: SHA256 hash of the persisted query
            response: GraphQL response dict to cache
            context: Optional request context containing user/tenant information
        """
        # Use tenant-aware cache key
        cache_key = self._get_cache_key(hash_value, context)
        self._response_storage[cache_key] = response

        tenant_info = f" (tenant: {cache_key.split(':')[0]})" if ":" in cache_key else ""
        logger.debug(f"Stored cached response for hash {hash_value[:8]}...{tenant_info}")

    def clear_storage(self) -> None:
        """Clear all stored data (queries and responses).

        This method is not part of the abstract interface but is useful
        for testing and development.
        """
        query_count = len(self._query_storage)
        response_count = len(self._response_storage)

        self._query_storage.clear()
        self._response_storage.clear()

        logger.debug(
            f"Cleared {query_count} APQ queries and "
            f"{response_count} cached responses from memory storage"
        )

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        total_query_size = sum(len(query.encode("utf-8")) for query in self._query_storage.values())
        total_response_size = sum(
            len(str(response).encode("utf-8")) for response in self._response_storage.values()
        )

        return {
            "stored_queries": len(self._query_storage),
            "cached_responses": len(self._response_storage),
            "total_query_size_bytes": total_query_size,
            "total_response_size_bytes": total_response_size,
            "total_size_bytes": total_query_size + total_response_size,
        }
