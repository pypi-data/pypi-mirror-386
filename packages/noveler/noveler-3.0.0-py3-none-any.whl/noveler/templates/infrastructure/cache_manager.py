"""Cache Manager - In-memory LRU cache for rendered templates.

Infrastructure Layer: Manages cache storage and eviction.
Responsible for: Cache CRUD operations with LRU eviction policy

SOLID Principles:
- SRP: Single responsibility (cache management only)
- OCP: Open for extension (can be replaced with Redis/Memcached)
- LSP: N/A (no inheritance)
- ISP: Minimal interface (get/set/invalidate)
- DIP: Can be abstracted with CacheProtocol interface
"""

from typing import Optional, Dict, Any
from collections import OrderedDict


class CacheManager:
    """LRU cache manager for template rendering results.

    Uses OrderedDict to maintain insertion order and implement LRU eviction.
    Thread-safe: No (designed for single-threaded execution in current context)

    Attributes:
        max_size: Maximum number of cached items (default: 100)
        _cache: OrderedDict storing cache data
    """

    def __init__(self, max_size: int = 100) -> None:
        """Initialize cache manager.

        Args:
            max_size: Maximum cache size (default: 100)

        Precondition:
            max_size > 0

        Postcondition:
            Cache is empty and ready for use
        """
        if max_size <= 0:
            raise ValueError(f"max_size must be > 0, got {max_size}")

        self.max_size = max_size
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached value and move to end (LRU update).

        Args:
            key: Cache key (typically template file path)

        Returns:
            Cached dictionary if hit, None if miss

        Postcondition:
            - If hit: key moved to end of OrderedDict (most recent)
            - If miss: cache unchanged

        LRU Behavior:
            Accessing a key makes it "most recently used"
        """
        if key not in self._cache:
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        return self._cache[key]

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Set cache value with LRU eviction if needed.

        Args:
            key: Cache key (typically template file path)
            value: Dictionary to cache (rendered YAML data)

        Postcondition:
            - key-value pair stored in cache
            - If cache was full, oldest item evicted
            - New item is at end (most recent)

        LRU Behavior:
            When cache is full, least recently used item (first in OrderedDict)
            is removed to make space for new item.
        """
        # Remove if exists (to update position)
        if key in self._cache:
            del self._cache[key]

        # Add to end (most recent)
        self._cache[key] = value

        # Evict oldest if over limit
        if len(self._cache) > self.max_size:
            # Remove first (least recently used)
            self._cache.popitem(last=False)

    def invalidate(self, key: str) -> None:
        """Invalidate (remove) specific cache entry.

        Args:
            key: Cache key to invalidate

        Postcondition:
            - If key existed: removed from cache
            - If key didn't exist: no change (idempotent)

        Usage:
            Called when .novelerrc.yaml is modified to force re-rendering
        """
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear entire cache.

        Postcondition:
            Cache is empty

        Usage:
            Called when configuration file changes to invalidate all cached
            templates (since they may contain outdated variable values)
        """
        self._cache.clear()

    def size(self) -> int:
        """Get current cache size.

        Returns:
            Number of items currently in cache

        Purity:
            Read-only operation, no side effects
        """
        return len(self._cache)
