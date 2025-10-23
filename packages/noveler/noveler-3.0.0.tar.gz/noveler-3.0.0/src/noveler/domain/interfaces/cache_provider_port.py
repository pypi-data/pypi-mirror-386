# File: src/noveler/domain/interfaces/cache_provider_port.py
# Purpose: Define port interface for cache providers in infrastructure integration.
# Context: Used by ServiceExecutionOrchestrator to abstract cache implementation details.

"""Purpose: Provide a cache provider port used by service execution orchestrators.
Context: Abstracts caching behaviour so domain logic does not depend on specific cache implementations.
Side Effects: None within the protocol definition.
"""

from __future__ import annotations

from typing import Any, Protocol


class CacheProviderPort(Protocol):
    """Purpose: Abstract caching operations for service execution workflows.

    Side Effects:
        Implementations may access in-memory or distributed cache backends.
    """

    def get(self, key: str) -> Any | None:
        """Purpose: Retrieve a cached value by key.

        Args:
            key: Cache key identifier.

        Returns:
            Cached value when present and valid; otherwise None.

        Side Effects:
            Implementation defined; may update internal LRU or TTL metadata.
        """
        ...

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Purpose: Store a value in the cache with a time-to-live.

        Args:
            key: Cache key identifier.
            value: Value to cache.
            ttl_seconds: Time-to-live in seconds.

        Side Effects:
            Implementation defined; writes to the underlying cache storage.

        Raises:
            None. Implementations should handle storage errors gracefully.
        """
        ...
