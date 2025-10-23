# File: src/noveler/infrastructure/adapters/infrastructure_cache_provider.py
# Purpose: Provide in-memory cache implementation for service execution.
# Context: Implements CacheProviderPort for development and testing environments.

"""In-memory cache provider for infrastructure services.

Purpose:
    Provide a simple in-memory cache with TTL support for service execution results.
Context:
    Used by ServiceExecutionOrchestrator when no external cache is configured.
Preconditions:
    None.
Side Effects:
    Stores data in process memory (not persistent across restarts).
"""

from __future__ import annotations

import threading
import time
from typing import Any


class InMemoryCacheProvider:
    """Thread-safe in-memory cache with TTL support.

    Purpose:
        Cache service execution results in memory with automatic expiration
        and thread-safe access for concurrent service execution.
    """

    def __init__(self, max_size: int = 1000) -> None:
        """Initialize empty cache storage with size limit.

        Args:
            max_size: Maximum number of cache entries (default: 1000).

        Side Effects:
            Creates internal cache dictionary and reentrant lock.
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._lock = threading.RLock()
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        """Retrieve cached value if exists and not expired (thread-safe).

        Args:
            key: Cache key identifier.

        Returns:
            Cached value if exists and not expired, None otherwise.

        Side Effects:
            Removes expired entries on access.
            Acquires and releases lock for thread safety.
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry_time = self._cache[key]
            if time.time() > expiry_time:
                del self._cache[key]
                return None

            return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Store value in cache with expiration (thread-safe, LRU eviction).

        Args:
            key: Cache key identifier.
            value: Value to cache.
            ttl_seconds: Time-to-live in seconds.

        Side Effects:
            Stores value in internal dictionary.
            Evicts oldest entry if cache exceeds max_size.
            Acquires and releases lock for thread safety.
        """
        with self._lock:
            # Evict oldest entry if cache is full
            if key not in self._cache and len(self._cache) >= self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]

            expiry_time = time.time() + ttl_seconds
            self._cache[key] = (value, expiry_time)
