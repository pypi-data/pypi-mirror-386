#!/usr/bin/env python3
"""Refactor presentation.shared.shared_utilities imports to use infra_console.

This script replaces direct presentation layer console imports in Infrastructure
and Application layers with DDD-compliant alternatives.

Usage:
    python scripts/refactor_console_imports.py --dry-run
    python scripts/refactor_console_imports.py --layer infrastructure
    python scripts/refactor_console_imports.py --layer application
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def refactor_file(file_path: Path, dry_run: bool = False) -> bool:
    """Refactor a single file's console imports.

    Args:
        file_path: Path to file to refactor
        dry_run: If True, only report changes without modifying files

    Returns:
        True if file was modified (or would be modified in dry-run)
    """
    content = file_path.read_text(encoding="utf-8")
    original = content

    # Determine target import based on layer
    if "/infrastructure/" in str(file_path):
        new_import = "from noveler.infrastructure.utils.infra_console import console"
    elif "/application/" in str(file_path):
        new_import = "from noveler.infrastructure.utils.infra_console import console"
    elif "/domain/" in str(file_path):
        new_import = "from noveler.domain.utils.domain_console import console"
    else:
        return False

    # Pattern 1: from noveler.presentation.shared.shared_utilities import console
    pattern1 = r"from noveler\.presentation\.shared\.shared_utilities import console"
    if re.search(pattern1, content):
        content = re.sub(pattern1, new_import, content)

    # Pattern 2: from noveler.presentation.cli.shared_utilities import console
    pattern2 = r"from noveler\.presentation\.cli\.shared_utilities import console"
    if re.search(pattern2, content):
        content = re.sub(pattern2, new_import, content)

    # Pattern 3: from noveler.presentation.shared.shared_utilities import get_console
    # Replace with: from noveler.infrastructure.utils.infra_console import get_console
    pattern3 = r"from noveler\.presentation\.shared\.shared_utilities import get_console"
    if re.search(pattern3, content):
        new_get_console = new_import.replace("import console", "import get_console")
        content = re.sub(pattern3, new_get_console, content)

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
    parser = argparse.ArgumentParser(description="Refactor console imports for DDD compliance")
    parser.add_argument(
        "--layer",
        choices=["infrastructure", "application", "all"],
        default="all",
        help="Which layer to refactor (default: all)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    modified_count = 0

    # Determine target directories
    if args.layer == "all":
        target_dirs = [
            project_root / "src" / "noveler" / "infrastructure",
            project_root / "src" / "noveler" / "application",
        ]
    elif args.layer == "infrastructure":
        target_dirs = [project_root / "src" / "noveler" / "infrastructure"]
    else:  # application
        target_dirs = [project_root / "src" / "noveler" / "application"]

    # Process all Python files
    for target_dir in target_dirs:
        for file_path in target_dir.rglob("*.py"):
            if "__pycache__" in str(file_path):
                continue

            try:
                if refactor_file(file_path, dry_run=args.dry_run):
                    modified_count += 1
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")

    # Summary
    action = "would be modified" if args.dry_run else "modified"
    print(f"\n{'=' * 60}")
    print(f"Summary: {modified_count} files {action}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
