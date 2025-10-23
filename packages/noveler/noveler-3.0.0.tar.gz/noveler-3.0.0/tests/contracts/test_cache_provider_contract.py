# File: tests/contracts/test_cache_provider_contract.py
# Purpose: Contract tests for CacheProviderPort to ensure implementation compliance.
# Context: Validates InMemoryCacheProvider adheres to CacheProviderPort protocol.

"""Contract tests for CacheProviderPort.

Purpose:
    Verify that all CacheProviderPort implementations satisfy the protocol contract.
Context:
    Part of B20 Workflow Phase 4 contract testing requirements.
Preconditions:
    None.
Side Effects:
    None (read-only tests).
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from noveler.domain.interfaces.cache_provider_port import CacheProviderPort

from noveler.infrastructure.adapters.infrastructure_cache_provider import InMemoryCacheProvider

pytestmark = pytest.mark.contract


class TestCacheProviderContract:
    """Contract tests for CacheProviderPort protocol.

    Purpose:
        Ensure implementations satisfy basic cache operations contract.
    """

    @pytest.fixture
    def provider(self) -> CacheProviderPort:
        """Provide CacheProviderPort implementation for testing.

        Returns:
            InMemoryCacheProvider instance as protocol implementation.
        """
        return InMemoryCacheProvider(max_size=10)

    @pytest.mark.spec("SPEC-CACHE_PROVIDER_PORT-GET_NONEXISTENT")
    def test_get_returns_none_for_nonexistent_key(self, provider: CacheProviderPort) -> None:
        """Verify get() returns None for keys that don't exist."""
        result = provider.get("nonexistent_key")
        assert result is None

    @pytest.mark.spec("SPEC-CACHE_PROVIDER_PORT-SET_GET_ROUNDTRIP")
    def test_set_and_get_roundtrip(self, provider: CacheProviderPort) -> None:
        """Verify set() stores value and get() retrieves it."""
        test_value = {"data": "test_value_123"}
        provider.set("key1", test_value, ttl_seconds=60)

        result = provider.get("key1")
        assert result == test_value

    @pytest.mark.spec("SPEC-CACHE_PROVIDER_PORT-TTL_EXPIRATION")
    def test_expired_entries_return_none(self, provider: CacheProviderPort) -> None:
        """Verify expired entries return None on get()."""
        provider.set("expiring_key", "value", ttl_seconds=0)
        time.sleep(0.1)  # Wait for expiration

        result = provider.get("expiring_key")
        assert result is None

    @pytest.mark.spec("SPEC-CACHE_PROVIDER_PORT-OVERWRITE")
    def test_set_overwrites_existing_value(self, provider: CacheProviderPort) -> None:
        """Verify set() overwrites existing key with new value."""
        provider.set("key1", "original", ttl_seconds=60)
        provider.set("key1", "updated", ttl_seconds=60)

        result = provider.get("key1")
        assert result == "updated"

    @pytest.mark.spec("SPEC-CACHE_PROVIDER_PORT-MULTIPLE_KEYS")
    def test_multiple_keys_independent(self, provider: CacheProviderPort) -> None:
        """Verify multiple keys are stored and retrieved independently."""
        provider.set("key1", "value1", ttl_seconds=60)
        provider.set("key2", "value2", ttl_seconds=60)
        provider.set("key3", "value3", ttl_seconds=60)

        assert provider.get("key1") == "value1"
        assert provider.get("key2") == "value2"
        assert provider.get("key3") == "value3"

    @pytest.mark.spec("SPEC-CACHE_PROVIDER_PORT-DIFFERENT_TTL")
    def test_different_ttl_per_key(self, provider: CacheProviderPort) -> None:
        """Verify each key can have independent TTL."""
        provider.set("short_ttl", "expires_soon", ttl_seconds=0)
        provider.set("long_ttl", "expires_later", ttl_seconds=60)

        time.sleep(0.1)

        assert provider.get("short_ttl") is None
        assert provider.get("long_ttl") == "expires_later"


class TestCacheProviderSpecCompliance:
    """Verify CacheProviderPort contract coverage and implementation compliance.

    Purpose:
        Meta-tests to ensure contract tests cover the protocol completely.
    """

    @pytest.mark.spec("SPEC-CACHE_PROVIDER_PORT-PROTOCOL_COMPLIANCE")
    def test_in_memory_implementation_is_valid_protocol(self) -> None:
        """Verify InMemoryCacheProvider satisfies CacheProviderPort protocol."""
        from noveler.domain.interfaces.cache_provider_port import CacheProviderPort

        provider: CacheProviderPort = InMemoryCacheProvider()

        # Protocol methods exist
        assert hasattr(provider, "get")
        assert hasattr(provider, "set")
        assert callable(provider.get)
        assert callable(provider.set)

    @pytest.mark.spec("SPEC-CACHE_PROVIDER_PORT-CONTRACT_COVERAGE")
    def test_cache_provider_contract_coverage(self) -> None:
        """Verify contract tests cover all critical scenarios."""
        # This test documents required contract test coverage
        required_scenarios = [
            "nonexistent",  # test_get_returns_none_for_nonexistent_key
            "roundtrip",    # test_set_and_get_roundtrip
            "expired",      # test_expired_entries_return_none
            "overwrites",   # test_set_overwrites_existing_value
            "multiple",     # test_multiple_keys_independent
            "ttl",          # test_different_ttl_per_key
        ]

        # Verify all scenarios are tested
        test_methods = [
            method
            for method in dir(TestCacheProviderContract)
            if method.startswith("test_")
        ]

        for scenario in required_scenarios:
            assert any(
                scenario in method for method in test_methods
            ), f"Missing contract test for scenario: {scenario}"
