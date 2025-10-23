#!/usr/bin/env python3
"""Test strict mode WARNING behavior for Path Service.

This script verifies that fallback warnings are properly logged
in WARNING mode before transitioning to ERROR mode.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

PASS = '[PASS]'
FAIL = '[FAIL]'

def test_warning_mode():
    """Test that WARNING mode logs fallback warnings."""
    print("=" * 80)
    print("Testing Path Service Strict Mode - WARNING Phase")
    print("=" * 80)
    print()

    # Set environment to WARNING mode
    os.environ["NOVELER_STRICT_PATH"] = "warning"
    print(f"Environment: NOVELER_STRICT_PATH={os.environ['NOVELER_STRICT_PATH']}")
    print()

    # Test 1: create_path_service with None (should warn and fallback to cwd)
    print("Test 1: create_path_service(project_root=None)")
    print("-" * 40)
    try:
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        # Temporarily remove PROJECT_ROOT to trigger fallback
        old_project_root = os.environ.pop("PROJECT_ROOT", None)

        try:
            ps = create_path_service(project_root=None)
            print(f"{PASS} Created PathService with fallback to: {ps._project_root}")
            print(f"   (Expected: {Path.cwd()})")
        finally:
            if old_project_root:
                os.environ["PROJECT_ROOT"] = old_project_root

    except Exception as e:
        print(f"{FAIL} Error: {type(e).__name__}: {e}")

    print()

    # Test 2: Verify StrictModeConfig
    print("Test 2: StrictModeConfig.from_env()")
    print("-" * 40)
    try:
        from noveler.infrastructure.config.strict_mode_config import StrictModeConfig, StrictLevel

        config = StrictModeConfig.from_env()
        print(f"   path_service level: {config.path_service}")
        print(f"   is_path_strict(): {config.is_path_strict()}")
        print(f"   should_warn_on_path_fallback(): {config.should_warn_on_path_fallback()}")

        assert config.path_service == StrictLevel.WARNING, "Expected WARNING level"
        assert not config.is_path_strict(), "Should not be strict in WARNING mode"
        assert config.should_warn_on_path_fallback(), "Should warn on fallback"

        print(f"{PASS} StrictModeConfig working correctly")
    except Exception as e:
        print(f"{FAIL} Error: {type(e).__name__}: {e}")

    print()

    # Test 3: ERROR mode (should raise exception)
    print("Test 3: ERROR mode (should raise exception)")
    print("-" * 40)
    os.environ["NOVELER_STRICT_PATH"] = "error"
    print(f"Environment: NOVELER_STRICT_PATH={os.environ['NOVELER_STRICT_PATH']}")

    # Change to a directory without project indicators to force detection failure
    import tempfile
    tmp_dir = Path(tempfile.mkdtemp())
    original_cwd = Path.cwd()

    try:
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        old_project_root = os.environ.pop("PROJECT_ROOT", None)
        os.chdir(tmp_dir)  # Move to temp dir (no project indicators)

        try:
            ps = create_path_service(project_root=None)
            print(f"{FAIL} Should have raised MissingProjectRootError, but got: {ps._project_root}")
        except Exception as e:
            print(f"{PASS} Correctly raised exception: {type(e).__name__}")
            print(f"   Message: {e}")
        finally:
            os.chdir(original_cwd)  # Restore original directory
            if old_project_root:
                os.environ["PROJECT_ROOT"] = old_project_root
            tmp_dir.rmdir()  # Clean up

    except Exception as e:
        os.chdir(original_cwd)
        print(f"{FAIL} Unexpected error: {type(e).__name__}: {e}")

    print()
    print("=" * 80)
    print("Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    test_warning_mode()
