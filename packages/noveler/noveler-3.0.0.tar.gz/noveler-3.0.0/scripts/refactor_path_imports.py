#!/usr/bin/env python3
"""Refactor path service imports to use infra_path helpers.

This script replaces presentation layer path service imports with
DDD-compliant infrastructure helpers.

Usage:
    python scripts/refactor_path_imports.py --dry-run
    python scripts/refactor_path_imports.py --apply
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def refactor_file(file_path: Path, dry_run: bool = False) -> bool:
    """Refactor a single file's path service imports.

    Args:
        file_path: Path to file to refactor
        dry_run: If True, only report changes without modifying files

    Returns:
        True if file was modified (or would be modified in dry-run)
    """
    content = file_path.read_text(encoding="utf-8")
    original = content

    # Pattern 1: from noveler.presentation.shared.shared_utilities import get_common_path_service
    pattern1 = r"from noveler\.presentation\.shared\.shared_utilities import get_common_path_service"
    if re.search(pattern1, content):
        content = re.sub(
            pattern1,
            "from noveler.infrastructure.utils.infra_path import get_path_service as get_common_path_service",
            content,
        )

    # Pattern 2: from noveler.presentation.shared.shared_utilities import get_path_service
    pattern2 = r"from noveler\.presentation\.shared\.shared_utilities import get_path_service"
    if re.search(pattern2, content):
        content = re.sub(
            pattern2,
            "from noveler.infrastructure.utils.infra_path import get_path_service",
            content,
        )

    # Pattern 3: from noveler.presentation.shared.shared_utilities import get_test_path_service
    pattern3 = r"from noveler\.presentation\.shared\.shared_utilities import get_test_path_service"
    if re.search(pattern3, content):
        # For test utilities, we'll keep the import but add a comment
        content = re.sub(
            pattern3,
            "from noveler.presentation.shared.shared_utilities import get_test_path_service  # TODO: migrate to test fixture",
            content,
        )

    # Pattern 4: from noveler.presentation.shared.shared_utilities import _get_console
    pattern4 = r"from noveler\.presentation\.shared\.shared_utilities import _get_console"
    if re.search(pattern4, content):
        content = re.sub(
            pattern4,
            "from noveler.infrastructure.utils.infra_console import get_console as _get_console",
            content,
        )

    # Pattern 5: get_common_path_service as _get_common_path_service (wrapped import)
    pattern5 = r"from noveler\.presentation\.shared\.shared_utilities import get_common_path_service as _get_common_path_service"
    if re.search(pattern5, content):
        content = re.sub(
            pattern5,
            "from noveler.infrastructure.utils.infra_path import get_path_service as _get_common_path_service",
            content,
        )

    modified = content != original

    if modified:
        if dry_run:
            print(f"[DRY-RUN] Would modify: {file_path}")
        else:
            file_path.write_text(content, encoding="utf-8")
            print(f"✅ Modified: {file_path}")

    return modified


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Refactor path service imports for DDD compliance")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")
    parser.add_argument(
        "--apply", action="store_true", help="Apply changes (default is dry-run unless this is specified)"
    )
    args = parser.parse_args()

    # Default to dry-run unless --apply is specified
    dry_run = not args.apply

    project_root = Path(__file__).parent.parent
    modified_count = 0

    # Process Infrastructure and Application layers
    target_dirs = [
        project_root / "src" / "noveler" / "infrastructure",
        project_root / "src" / "noveler" / "application",
    ]

    for target_dir in target_dirs:
        for file_path in target_dir.rglob("*.py"):
            if "__pycache__" in str(file_path):
                continue

            try:
                if refactor_file(file_path, dry_run=dry_run):
                    modified_count += 1
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")

    # Summary
    action = "would be modified" if dry_run else "modified"
    print(f"\n{'=' * 60}")
    print(f"Summary: {modified_count} files {action}")
    if dry_run and modified_count > 0:
        print("\nRe-run with --apply to make changes")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
