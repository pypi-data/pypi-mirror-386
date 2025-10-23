#!/usr/bin/env python3
"""
Unified Logging Quality Gate

Purpose: Enforce unified logging conventions across the codebase
- Block direct `import logging` in Application/Infrastructure layers
- Block direct `from rich` imports in Domain layer
- Block direct `presentation.shared.shared_utilities` imports in Domain layer
- Allow exceptions for tests and explicit fallback cases

Exit codes:
- 0: All checks passed
- 1: Violations found
"""

import re
import sys
from pathlib import Path
from typing import NamedTuple


class Violation(NamedTuple):
    """Represents a logging convention violation."""

    file: Path
    line_number: int
    line: str
    rule: str


def check_direct_logging_import(file_path: Path) -> list[Violation]:
    """Check for direct 'import logging' in Application/Infrastructure layers."""
    violations = []

    # Skip tests
    if "/tests/" in str(file_path) or file_path.name.startswith("test_"):
        return violations

    # Skip logging infrastructure itself
    if "/infrastructure/logging/" in str(file_path):
        return violations

    # Only check Application and Infrastructure layers
    if not ("/application/" in str(file_path) or "/infrastructure/" in str(file_path)):
        return violations

    try:
        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                # Skip comments
                if line.strip().startswith("#"):
                    continue

                # Check for direct logging import (not in try/except or as fallback)
                if re.match(r"^import\s+logging\s*$", line.strip()):
                    violations.append(
                        Violation(
                            file=file_path,
                            line_number=line_num,
                            line=line.strip(),
                            rule="NO_DIRECT_LOGGING_IMPORT",
                        )
                    )
    except (OSError, UnicodeDecodeError):
        pass

    return violations


def check_rich_in_domain(file_path: Path) -> list[Violation]:
    """Check for Rich imports in Domain layer."""
    violations = []

    # Skip tests
    if "/tests/" in str(file_path) or file_path.name.startswith("test_"):
        return violations

    # Only check Domain layer
    if "/domain/" not in str(file_path):
        return violations

    try:
        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                # Skip comments
                if line.strip().startswith("#"):
                    continue

                # Check for Rich imports
                if re.match(r"^(from\s+rich|import\s+rich)", line.strip()):
                    violations.append(
                        Violation(
                            file=file_path,
                            line_number=line_num,
                            line=line.strip(),
                            rule="NO_RICH_IN_DOMAIN",
                        )
                    )
    except (OSError, UnicodeDecodeError):
        pass

    return violations


def check_presentation_utils_in_domain(file_path: Path) -> list[Violation]:
    """Check for direct presentation.shared.shared_utilities imports in Domain layer."""
    violations = []

    # Skip tests
    if "/tests/" in str(file_path) or file_path.name.startswith("test_"):
        return violations

    # Only check Domain layer
    if "/domain/" not in str(file_path):
        return violations

    # Allow dynamic imports via importlib
    allow_patterns = [
        r"importlib\.import_module\(",
        r"# fallback",
        r"# Fallback",
    ]

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()

            for line_num, line in enumerate(lines, start=1):
                # Skip comments
                if line.strip().startswith("#"):
                    continue

                # Check for direct presentation utilities import
                if "presentation.shared.shared_utilities" in line:
                    # Allow if using importlib or marked as fallback
                    if any(re.search(pattern, line) for pattern in allow_patterns):
                        continue

                    # Check context (surrounding lines)
                    context_start = max(0, line_num - 3)
                    context_end = min(len(lines), line_num + 2)
                    context = "\n".join(lines[context_start:context_end])

                    # Allow if within importlib context
                    if "importlib" in context:
                        continue

                    violations.append(
                        Violation(
                            file=file_path,
                            line_number=line_num,
                            line=line.strip(),
                            rule="NO_DIRECT_PRESENTATION_UTILS_IN_DOMAIN",
                        )
                    )
    except (OSError, UnicodeDecodeError):
        pass

    return violations


def main() -> int:
    """Run all unified logging checks."""
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src" / "noveler"

    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}", file=sys.stderr)
        return 1

    all_violations: list[Violation] = []

    # Collect all Python files
    python_files = list(src_dir.rglob("*.py"))

    for file_path in python_files:
        all_violations.extend(check_direct_logging_import(file_path))
        all_violations.extend(check_rich_in_domain(file_path))
        all_violations.extend(check_presentation_utils_in_domain(file_path))

    if not all_violations:
        print("[PASS] Unified logging gate: All checks passed")
        return 0

    # Report violations
    print("[FAIL] Unified logging gate: Violations found\n", file=sys.stderr)

    violations_by_rule: dict[str, list[Violation]] = {}
    for violation in all_violations:
        violations_by_rule.setdefault(violation.rule, []).append(violation)

    for rule, violations in violations_by_rule.items():
        print(f"Rule: {rule}", file=sys.stderr)
        for violation in violations:
            rel_path = violation.file.relative_to(project_root)
            print(f"  {rel_path}:{violation.line_number}: {violation.line}", file=sys.stderr)
        print("", file=sys.stderr)

    print(f"Total violations: {len(all_violations)}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())