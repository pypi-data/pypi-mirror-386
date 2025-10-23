#!/usr/bin/env python3
"""
Simple TDD/DDD compliance checker - Replacement for missing script
File: scripts/tools/check_tdd_ddd_compliance_simple.py

This is a simplified implementation focusing on basic compliance checks.
"""

import argparse
import sys
from pathlib import Path


def check_import_structure(project_root: Path) -> bool:
    """Check basic import structure compliance."""
    violations = []

    # Basic DDD structure check
    src_dir = project_root / "src"
    if not src_dir.exists():
        violations.append("Missing src/ directory")
        return False

    # Look for domain/application/infrastructure separation
    domain_dirs = list(src_dir.glob("*/domain"))
    app_dirs = list(src_dir.glob("*/application"))
    infra_dirs = list(src_dir.glob("*/infrastructure"))

    if not domain_dirs:
        violations.append("No domain layer found")
    if not app_dirs:
        violations.append("No application layer found")
    if not infra_dirs:
        violations.append("No infrastructure layer found")

    if violations:
        print("❌ DDD Structure violations:")
        for v in violations:
            print(f"  - {v}")
        return False

    print("✅ Basic DDD structure compliance: OK")
    return True


def check_test_structure(project_root: Path) -> bool:
    """Check basic test structure."""
    tests_dir = project_root / "tests"
    if not tests_dir.exists():
        print("⚠️ No tests/ directory found")
        return True  # Not a failure, just a warning

    # Check for basic test categories
    unit_tests = list(tests_dir.glob("unit/**/*.py"))
    integration_tests = list(tests_dir.glob("integration/**/*.py"))

    if not unit_tests:
        print("⚠️ No unit tests found")
    else:
        print(f"✅ Found {len(unit_tests)} unit test files")

    if not integration_tests:
        print("⚠️ No integration tests found")
    else:
        print(f"✅ Found {len(integration_tests)} integration test files")

    return True


def check_basic_patterns(project_root: Path) -> bool:
    """Check for basic code patterns."""
    violations = []

    # Check for common anti-patterns in Python files
    python_files = list(project_root.glob("src/**/*.py"))

    for py_file in python_files[:10]:  # Limit for performance
        try:
            content = py_file.read_text(encoding='utf-8')

            # Check for some basic violations
            if "from ... import *" in content:
                violations.append(f"Wildcard import in {py_file}")

            # Check for very long lines (basic quality check)
            lines = content.split('\n')
            for i, line in enumerate(lines[:100], 1):  # Check first 100 lines
                if len(line) > 200:  # Very conservative limit
                    violations.append(f"Very long line in {py_file}:{i}")
                    break

        except (UnicodeDecodeError, FileNotFoundError):
            continue

    if violations:
        print("⚠️ Code pattern issues (first 10):")
        for v in violations[:10]:
            print(f"  - {v}")
    else:
        print("✅ Basic code patterns: OK")

    return len(violations) == 0


def main():
    parser = argparse.ArgumentParser(description="Simple TDD/DDD compliance checker")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--level", choices=["basic", "strict"], default="basic")
    parser.add_argument("--quick", action="store_true", help="Quick check mode")

    args = parser.parse_args()

    print(f"🔍 TDD/DDD compliance check ({args.level} level)")
    print(f"📁 Project root: {args.project_root.absolute()}")

    success = True

    # 1. Structure checks
    if not check_import_structure(args.project_root):
        success = False

    # 2. Test structure (always run, non-blocking)
    check_test_structure(args.project_root)

    # 3. Pattern checks (only in strict mode and not quick)
    if args.level == "strict" and not args.quick:
        if not check_basic_patterns(args.project_root):
            success = False

    if success:
        print("✅ TDD/DDD compliance check passed")
        return 0
    else:
        print("❌ TDD/DDD compliance check failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())