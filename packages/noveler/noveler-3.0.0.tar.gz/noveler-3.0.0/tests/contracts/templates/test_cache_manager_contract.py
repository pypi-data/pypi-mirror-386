"""Contract tests for CacheManager.

Tests verify that CacheManager honors its public interface contract:
- get() returns Optional[dict]
- set() stores key-value pairs
- invalidate() removes entries
- clear() empties cache
- size() returns int
- LRU eviction behavior
"""

import pytest
from src.noveler.templates.infrastructure.cache_manager import CacheManager


class TestCacheManagerContract:
    """Contract tests for CacheManager public interface."""

    def setup_method(self):
        """Setup test fixture."""
        self.cache = CacheManager(max_size=3)

    def test_get_returns_none_for_nonexistent_key(self):
        """Contract: get() must return None for non-existent keys."""
        result = self.cache.get("nonexistent")

        assert result is None

    def test_set_and_get_roundtrip(self):
        """Contract: set() stores value, get() retrieves it."""
        test_value = {"data": "value"}
        self.cache.set("key1", test_value)

        result = self.cache.get("key1")

        assert result == test_value
        assert isinstance(result, dict)

    def test_set_overwrites_existing_value(self):
        """Contract: set() on existing key updates value."""
        self.cache.set("key1", {"v": 1})
        self.cache.set("key1", {"v": 2})

        result = self.cache.get("key1")

        assert result == {"v": 2}

    def test_invalidate_removes_entry(self):
        """Contract: invalidate() removes the specified key."""
        self.cache.set("key1", {"data": "value"})
        self.cache.invalidate("key1")

        result = self.cache.get("key1")

        assert result is None

    def test_invalidate_is_idempotent(self):
        """Contract: invalidate() on non-existent key does nothing (no error)."""
        # Should not raise
        self.cache.invalidate("nonexistent")
        self.cache.invalidate("nonexistent")  # Second time

    def test_clear_empties_cache(self):
        """Contract: clear() removes all entries."""
        self.cache.set("key1", {"a": 1})
        self.cache.set("key2", {"b": 2})
        self.cache.clear()

        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None
        assert self.cache.size() == 0

    def test_size_returns_int(self):
        """Contract: size() must return int."""
        self.cache.set("key1", {})

        result = self.cache.size()

        assert isinstance(result, int)
        assert result >= 0

    def test_size_reflects_current_entries(self):
        """Contract: size() returns number of cached entries."""
        assert self.cache.size() == 0

        self.cache.set("key1", {})
        assert self.cache.size() == 1

        self.cache.set("key2", {})
        assert self.cache.size() == 2

        self.cache.invalidate("key1")
        assert self.cache.size() == 1

    def test_lru_eviction_on_overflow(self):
        """Contract: When cache is full, oldest entry is evicted (LRU)."""
        # max_size=3
        self.cache.set("key1", {"v": 1})
        self.cache.set("key2", {"v": 2})
        self.cache.set("key3", {"v": 3})

        # Cache is full, add 4th item
        self.cache.set("key4", {"v": 4})

        # key1 (oldest) should be evicted
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is not None
        assert self.cache.get("key3") is not None
        assert self.cache.get("key4") is not None
        assert self.cache.size() == 3

    def test_lru_updates_on_access(self):
        """Contract: get() moves accessed entry to end (most recent)."""
        # max_size=3
        self.cache.set("key1", {"v": 1})
        self.cache.set("key2", {"v": 2})
        self.cache.set("key3", {"v": 3})

        # Access key1 (moves to end)
        self.cache.get("key1")

        # Add key4, key2 (now oldest) should be evicted
        self.cache.set("key4", {"v": 4})

        assert self.cache.get("key1") is not None  # Survived
        assert self.cache.get("key2") is None  # Evicted
        assert self.cache.get("key3") is not None
        assert self.cache.get("key4") is not None

    def test_lru_updates_on_set_existing_key(self):
        """Contract: set() on existing key moves it to end."""
        # max_size=3
        self.cache.set("key1", {"v": 1})
        self.cache.set("key2", {"v": 2})
        self.cache.set("key3", {"v": 3})

        # Update key1 (moves to end)
        self.cache.set("key1", {"v": "1updated"})

        # Add key4, key2 (now oldest) should be evicted
        self.cache.set("key4", {"v": 4})

        assert self.cache.get("key1") is not None  # Survived
        assert self.cache.get("key2") is None  # Evicted

    def test_multiple_keys_independent(self):
        """Contract: Different keys are stored independently."""
        self.cache.set("key1", {"a": 1})
        self.cache.set("key2", {"b": 2})

        assert self.cache.get("key1") == {"a": 1}
        assert self.cache.get("key2") == {"b": 2}

        self.cache.invalidate("key1")

        assert self.cache.get("key1") is None
        assert self.cache.get("key2") == {"b": 2}  # Unaffected

    def test_max_size_validation(self):
        """Contract: CacheManager requires max_size > 0."""
        with pytest.raises(ValueError) as exc_info:
            CacheManager(max_size=0)

        assert "max_size must be > 0" in str(exc_info.value)

        with pytest.raises(ValueError):
            CacheManager(max_size=-1)


class TestCacheManagerSpecCompliance:
    """Verify CacheManager complies with design specifications."""

    def test_has_required_methods(self):
        """Spec: CacheManager must have get/set/invalidate/clear/size."""
        cache = CacheManager()

        assert hasattr(cache, "get")
        assert callable(cache.get)

        assert hasattr(cache, "set")
        assert callable(cache.set)

        assert hasattr(cache, "invalidate")
        assert callable(cache.invalidate)

        assert hasattr(cache, "clear")
        assert callable(cache.clear)

        assert hasattr(cache, "size")
        assert callable(cache.size)

    def test_get_signature(self):
        """Spec: get(key: str) -> Optional[Dict[str, Any]]"""
        import inspect

        sig = inspect.signature(CacheManager.get)
        params = list(sig.parameters.keys())

        assert params == ["self", "key"]

    def test_set_signature(self):
        """Spec: set(key: str, value: dict) -> None"""
        import inspect

        sig = inspect.signature(CacheManager.set)
        params = list(sig.parameters.keys())

        assert params == ["self", "key", "value"]

    def test_invalidate_signature(self):
        """Spec: invalidate(key: str) -> None"""
        import inspect

        sig = inspect.signature(CacheManager.invalidate)
        params = list(sig.parameters.keys())

        assert params == ["self", "key"]

    def test_clear_signature(self):
        """Spec: clear() -> None"""
        import inspect

        sig = inspect.signature(CacheManager.clear)
        params = list(sig.parameters.keys())

        assert params == ["self"]

    def test_size_signature(self):
        """Spec: size() -> int"""
        import inspect

        sig = inspect.signature(CacheManager.size)
        params = list(sig.parameters.keys())

        assert params == ["self"]
        assert sig.return_annotation == int

    def test_no_external_dependencies(self):
        """Spec: CacheManager should have no external dependencies."""
        cache = CacheManager()

        # Should be instantiable without any external services
        assert cache is not None
        assert cache.size() == 0

    def test_uses_ordereddict_for_lru(self):
        """Spec: Implementation uses OrderedDict for LRU eviction."""
        from collections import OrderedDict

        cache = CacheManager()

        # Verify internal _cache is OrderedDict
        assert hasattr(cache, "_cache")
        assert isinstance(cache._cache, OrderedDict)
