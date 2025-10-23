#!/usr/bin/env python3
"""Validate docs/archive structure.

File: scripts/hooks/check_archive_structure.py
Purpose: Ensure docs/archive/ follows the established policy and structure.
Context: Pre-commit hook to prevent archive policy violations.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def validate_archive() -> list[str]:
    """Validate docs/archive structure and return list of errors."""
    errors: list[str] = []

    # Check 1: README exists
    readme = Path("docs/archive/README.md")
    if not readme.exists():
        errors.append("[ERROR] docs/archive/README.md not found")

    # Check 2: .gitignore allows docs/archive/
    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        gitignore = gitignore_path.read_text(encoding="utf-8")
        if "!docs/archive/" not in gitignore:
            errors.append("[ERROR] .gitignore missing '!docs/archive/' exception")
    else:
        errors.append("[ERROR] .gitignore not found")

    # Check 3: Archive files are tracked by git
    try:
        result = subprocess.run(
            ["git", "ls-files", "docs/archive/"],
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
            errors="ignore",  # Ignore encoding errors on Windows
        )
        if result.returncode == 0 and result.stdout and not result.stdout.strip():
            errors.append("[WARN] docs/archive/ contains no tracked files (may be intentional)")
    except (FileNotFoundError, OSError):
        errors.append("[WARN] git command not found, skipping tracked files check")

    # Check 4: Expected directories exist
    expected_dirs = [
        "docs/archive/proposals",
        "docs/archive/refactoring",
        "docs/archive/reviews",
        "docs/archive/backup",
    ]
    for dir_path in expected_dirs:
        if not Path(dir_path).exists():
            errors.append(f"[WARN] Expected directory {dir_path} not found")

    return errors


def main() -> int:
    """Run validation and exit with appropriate code."""
    errors = validate_archive()

    if errors:
        print("[FAIL] Archive Structure Validation Failed:", file=sys.stderr)
        print(file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        print(file=sys.stderr)
        print("[INFO] See docs/archive/README.md for policy details", file=sys.stderr)
        return 1

    print("[PASS] Archive structure validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
