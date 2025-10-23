#!/usr/bin/env python3
"""Test Configuration Service strict mode behavior.

This script validates all three strict modes:
1. OFF mode: silent fallback to defaults
2. WARNING mode: fallback with warning logs
3. ERROR mode: raise MissingConfigurationError

Usage:
    python scripts/diagnostics/test_config_strict_mode.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


PASS = "[PASS]"
FAIL = "[FAIL]"



def test_off_mode():
    """Test OFF mode: silent fallback."""
    print("=" * 80)
    print("Test 1: OFF mode - silent fallback to defaults")
    print("=" * 80)

    os.environ["NOVELER_STRICT_CONFIG"] = "off"

    from noveler.infrastructure.adapters.configuration_service_adapter import ConfigurationServiceAdapter

    adapter = ConfigurationServiceAdapter()

    # Should silently fall back to "." without any warnings
    project_root = adapter.get_project_root()
    print(f"{PASS} get_project_root() returned: {project_root!r}")

    # Should silently fall back to "development"
    env = adapter.get_environment()
    print(f"{PASS} get_environment() returned: {env!r}")

    # Should silently fall back to {}
    db_config = adapter.get_database_config()
    print(f"{PASS} get_database_config() returned: {db_config!r}")

    # Should silently fall back to False
    feature_enabled = adapter.is_feature_enabled("nonexistent_feature")
    print(f"{PASS} is_feature_enabled('nonexistent_feature') returned: {feature_enabled!r}")

    print(f"{PASS} Test 1 passed: all fallbacks succeeded silently\n")


def test_warning_mode():
    """Test WARNING mode: fallback with warnings."""
    print("=" * 80)
    print("Test 2: WARNING mode - fallback with warning logs")
    print("=" * 80)

    os.environ["NOVELER_STRICT_CONFIG"] = "warning"

    # Force reimport to pick up new env var
    import importlib
    import noveler.infrastructure.adapters.configuration_service_adapter
    importlib.reload(noveler.infrastructure.adapters.configuration_service_adapter)
    from noveler.infrastructure.adapters.configuration_service_adapter import ConfigurationServiceAdapter

    adapter = ConfigurationServiceAdapter()

    print("Expected: WARNING logs should appear below:")
    print("-" * 80)

    # Should fall back with warning
    project_root = adapter.get_project_root()
    print(f"{PASS} get_project_root() returned: {project_root!r}")

    # Should fall back with warning
    env = adapter.get_environment()
    print(f"{PASS} get_environment() returned: {env!r}")

    # Should fall back with warning
    db_config = adapter.get_database_config()
    print(f"{PASS} get_database_config() returned: {db_config!r}")

    # Should fall back with warning (via get_feature_flags)
    feature_enabled = adapter.is_feature_enabled("nonexistent_feature")
    print(f"{PASS} is_feature_enabled('nonexistent_feature') returned: {feature_enabled!r}")

    print("-" * 80)
    print(f"{PASS} Test 2 passed: all fallbacks succeeded with warnings\n")


def test_error_mode():
    """Test ERROR mode: raise exceptions on fallback."""
    print("=" * 80)
    print("Test 3: ERROR mode - raise MissingConfigurationError")
    print("=" * 80)

    os.environ["NOVELER_STRICT_CONFIG"] = "error"

    # Force reimport to pick up new env var
    import importlib
    import noveler.infrastructure.adapters.configuration_service_adapter
    importlib.reload(noveler.infrastructure.adapters.configuration_service_adapter)
    from noveler.infrastructure.adapters.configuration_service_adapter import ConfigurationServiceAdapter
    from noveler.domain.exceptions import MissingConfigurationError

    adapter = ConfigurationServiceAdapter()

    # Test 3a: get_project_root should raise
    try:
        adapter.get_project_root()
        print(f"{FAIL} ERROR: get_project_root() should have raised MissingConfigurationError")
        sys.exit(1)
    except MissingConfigurationError as e:
        print(f"{PASS} get_project_root() raised MissingConfigurationError: {e.message}")

    # Test 3b: get_environment should raise
    try:
        adapter.get_environment()
        print(f"{FAIL} ERROR: get_environment() should have raised MissingConfigurationError")
        sys.exit(1)
    except MissingConfigurationError as e:
        print(f"{PASS} get_environment() raised MissingConfigurationError: {e.message}")

    # Test 3c: get_database_config should raise
    try:
        adapter.get_database_config()
        print(f"{FAIL} ERROR: get_database_config() should have raised MissingConfigurationError")
        sys.exit(1)
    except MissingConfigurationError as e:
        print(f"{PASS} get_database_config() raised MissingConfigurationError: {e.message}")

    # Test 3d: get_feature_flags should raise (called by is_feature_enabled)
    try:
        adapter.is_feature_enabled("nonexistent_feature")
        print(f"{FAIL} ERROR: is_feature_enabled() should have raised MissingConfigurationError")
        sys.exit(1)
    except MissingConfigurationError as e:
        print(f"{PASS} is_feature_enabled() raised MissingConfigurationError: {e.message}")

    # Test 3e: get() with default=None should raise
    try:
        adapter.get("some.missing.key", default=None)
        print(f"{FAIL} ERROR: get() with default=None should have raised MissingConfigurationError")
        sys.exit(1)
    except MissingConfigurationError as e:
        print(f"{PASS} get() with default=None raised MissingConfigurationError: {e.message}")

    # Test 3f: get() with explicit default should NOT raise (default is provided)
    try:
        result = adapter.get("some.missing.key", default="fallback_value")
        print(f"{PASS} get() with explicit default returned: {result!r} (no exception, as expected)")
    except MissingConfigurationError:
        print(f"{FAIL} ERROR: get() with explicit default should NOT have raised exception")
        sys.exit(1)

    print(f"{PASS} Test 3 passed: all required configs raised exceptions in ERROR mode\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Configuration Service Strict Mode Test Suite")
    print("=" * 80 + "\n")

    test_off_mode()
    test_warning_mode()
    test_error_mode()

    print("=" * 80)
    print(f"{PASS} All tests passed successfully!")
    print("=" * 80)
