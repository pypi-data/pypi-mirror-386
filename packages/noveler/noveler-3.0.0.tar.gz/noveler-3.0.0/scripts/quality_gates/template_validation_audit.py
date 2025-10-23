#!/usr/bin/env python3
"""Template validation audit script for example parity verification.

This script verifies that all field paths referenced in `by_task` sections
exist in the corresponding `artifacts.example` YAML structure.

Exit codes:
    0: All field paths valid
    1: Missing fields detected
    2: Script execution error

Usage:
    python scripts/quality_gates/template_validation_audit.py
    python scripts/quality_gates/template_validation_audit.py --verbose
    python scripts/quality_gates/template_validation_audit.py --template step01
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, NamedTuple

import yaml


class MissingField(NamedTuple):
    """Represents a missing field in artifacts.example."""

    template_path: Path
    by_task_id: str
    field_path: str
    rule: str


def get_nested_value(data: dict[str, Any], path: str) -> tuple[bool, Any]:
    """Get nested value from dictionary using dotted path.

    Args:
        data: Dictionary to traverse
        path: Dotted path (e.g., "story_structure.start_state.inner")

    Returns:
        Tuple of (exists: bool, value: Any)
    """
    parts = path.split(".")
    current = data

    for part in parts:
        if not isinstance(current, dict):
            return False, None
        if part not in current:
            return False, None
        current = current[part]

    return True, current


def verify_template(template_path: Path, verbose: bool = False) -> list[MissingField]:
    """Verify that all by_task fields exist in artifacts.example.

    Args:
        template_path: Path to YAML template file
        verbose: Print detailed progress information

    Returns:
        List of MissingField instances
    """
    missing_fields = []

    try:
        content = yaml.safe_load(template_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        print(f"⚠️  YAML parse error in {template_path}: {e}")
        return missing_fields

    # Extract by_task section
    by_task = content.get("acceptance_criteria", {}).get("by_task", [])
    if not by_task:
        if verbose:
            print(f"  ℹ️  No by_task section in {template_path.name}")
        return missing_fields

    # Parse artifacts.example
    example_str = content.get("artifacts", {}).get("example", "")
    if not example_str:
        if verbose:
            print(f"  ⚠️  No artifacts.example in {template_path.name}")
        return missing_fields

    try:
        example_data = yaml.safe_load(example_str)
    except yaml.YAMLError as e:
        print(f"⚠️  artifacts.example parse error in {template_path}: {e}")
        return missing_fields

    # Check each by_task field
    for task in by_task:
        task_id = task.get("id", "unknown")
        field_path = task.get("field", "")
        rule = task.get("rule", "")

        if not field_path:
            continue

        exists, _ = get_nested_value(example_data, field_path)

        if not exists:
            missing_fields.append(
                MissingField(
                    template_path=template_path,
                    by_task_id=task_id,
                    field_path=field_path,
                    rule=rule,
                )
            )

    return missing_fields


def scan_templates(
    project_root: Path, template_filter: str | None = None, verbose: bool = False
) -> list[MissingField]:
    """Scan all templates in writing/ and polish/ directories.

    Args:
        project_root: Root directory of the project
        template_filter: Optional filter for template name (e.g., "step01")
        verbose: Print detailed progress information

    Returns:
        List of all MissingField instances
    """
    all_missing = []
    templates_dir = project_root / "templates"

    # Priority templates: writing steps + polish stages
    search_patterns = [
        templates_dir / "writing" / "*.yaml",
        templates_dir / "polish" / "*.yaml",
    ]

    template_paths = []
    for pattern in search_patterns:
        template_paths.extend(pattern.parent.glob(pattern.name))

    if template_filter:
        template_paths = [p for p in template_paths if template_filter in p.stem]

    if verbose:
        print(f"🔍 Scanning {len(template_paths)} templates...")

    for template_path in sorted(template_paths):
        if verbose:
            print(f"\n📄 {template_path.name}")

        missing = verify_template(template_path, verbose)
        all_missing.extend(missing)

        if missing and verbose:
            print(f"  ❌ {len(missing)} missing field(s)")
        elif verbose:
            print(f"  ✅ All by_task fields present")

    return all_missing


def report_missing_fields(missing_fields: list[MissingField], verbose: bool = False) -> None:
    """Report missing fields to stdout.

    Args:
        missing_fields: List of missing fields to report
        verbose: Include additional details in report
    """
    if not missing_fields:
        print("✅ All by_task field paths exist in artifacts.example")
        return

    print(f"❌ Found {len(missing_fields)} missing field(s) in templates:\n")

    # Group by template
    by_template: dict[Path, list[MissingField]] = {}
    for field in missing_fields:
        by_template.setdefault(field.template_path, []).append(field)

    for template_path, fields in sorted(by_template.items()):
        print(f"\n{'=' * 60}")
        print(f"Template: {template_path.name} ({len(fields)} missing)")
        print(f"{'=' * 60}\n")

        for field in fields:
            print(f"  by_task ID: {field.by_task_id}")
            print(f"  Field path: {field.field_path}")
            print(f"  Rule: {field.rule}")
            print()


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 = success, 1 = missing fields, 2 = error)
    """
    parser = argparse.ArgumentParser(
        description="Verify by_task field paths exist in artifacts.example"
    )
    parser.add_argument(
        "--template",
        help="Filter to specific template name (e.g., 'step01')",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print detailed progress information"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent.parent,
        help="Project root directory (default: repository root)",
    )
    args = parser.parse_args()

    try:
        missing_fields = scan_templates(
            project_root=args.project_root,
            template_filter=args.template,
            verbose=args.verbose,
        )

        report_missing_fields(missing_fields, verbose=args.verbose)

        return 0 if not missing_fields else 1

    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
