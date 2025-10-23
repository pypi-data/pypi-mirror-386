#!/usr/bin/env python3
# File: scripts/checks/verify_slash_commands.py
# Purpose: CI verification script for SPEC-CLI-050 slash command configuration
# Context: Ensures YAML and generated files stay in sync

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from subprocess import run, CalledProcessError
from typing import Any


def detect_project_root() -> Path:
    """Detect project root by looking for pyproject.toml."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists() and (parent / "src").exists():
            return parent
    return Path.cwd()


def run_build_dry_run(output_dir: Path) -> int:
    """Run build_slash_commands.py in dry-run mode to generate files.

    Args:
        output_dir: Temporary directory for generated outputs

    Returns:
        Exit code (0 for success)
    """
    project_root = detect_project_root()
    script_path = project_root / "scripts" / "setup" / "build_slash_commands.py"

    if not script_path.exists():
        print(f"[ERROR] Build script not found: {script_path}", file=sys.stderr)
        return 1

    try:
        result = run(
            [sys.executable, str(script_path), "--output", str(output_dir)],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return 0
    except CalledProcessError as e:
        print(f"[ERROR] Build script failed: {e}", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return 1


def normalize_json(data: Any) -> Any:
    """Normalize JSON for comparison (sort lists, remove timestamps).

    Args:
        data: JSON data structure

    Returns:
        Normalized data
    """
    if isinstance(data, dict):
        # Remove volatile fields like timestamps
        filtered = {k: v for k, v in data.items() if k not in ["last_updated"]}
        return {k: normalize_json(v) for k, v in filtered.items()}
    elif isinstance(data, list):
        # Sort lists for stable comparison (e.g., permissions.allow)
        return sorted([normalize_json(item) for item in data])
    else:
        return data


def compare_json_files(expected: Path, actual: Path) -> tuple[bool, str]:
    """Compare two JSON files with normalization.

    Args:
        expected: Path to expected JSON file
        actual: Path to actual JSON file

    Returns:
        Tuple of (is_equal, diff_message)
    """
    if not expected.exists():
        return False, f"Expected file not found: {expected}"

    if not actual.exists():
        return False, f"Actual file not found: {actual}"

    try:
        with expected.open('r', encoding='utf-8') as f:
            expected_data = json.load(f)

        with actual.open('r', encoding='utf-8') as f:
            actual_data = json.load(f)

        # Normalize both for comparison
        norm_expected = normalize_json(expected_data)
        norm_actual = normalize_json(actual_data)

        if norm_expected == norm_actual:
            return True, ""
        else:
            # Generate human-readable diff
            diff_msg = f"Files differ:\n"
            diff_msg += f"Expected: {expected}\n"
            diff_msg += f"Actual: {actual}\n"
            diff_msg += f"Expected data: {json.dumps(norm_expected, indent=2, ensure_ascii=False)[:500]}...\n"
            diff_msg += f"Actual data: {json.dumps(norm_actual, indent=2, ensure_ascii=False)[:500]}...\n"
            return False, diff_msg

    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {e}"
    except Exception as e:
        return False, f"Comparison error: {e}"


def compare_text_files(expected: Path, actual: Path) -> tuple[bool, str]:
    """Compare two text files line by line (ignoring timestamps).

    Args:
        expected: Path to expected text file
        actual: Path to actual text file

    Returns:
        Tuple of (is_equal, diff_message)
    """
    if not expected.exists():
        return False, f"Expected file not found: {expected}"

    if not actual.exists():
        return False, f"Actual file not found: {actual}"

    try:
        expected_lines = expected.read_text(encoding='utf-8').splitlines()
        actual_lines = actual.read_text(encoding='utf-8').splitlines()

        # Filter out timestamp lines (must check exact prefix for accuracy)
        expected_filtered = [
            line for line in expected_lines
            if not line.startswith("**Last Updated**:")
        ]
        actual_filtered = [
            line for line in actual_lines
            if not line.startswith("**Last Updated**:")
        ]

        if expected_filtered == actual_filtered:
            return True, ""
        else:
            diff_msg = f"Files differ:\n"
            diff_msg += f"Expected: {expected}\n"
            diff_msg += f"Actual: {actual}\n"
            diff_msg += f"Expected lines: {len(expected_filtered)}\n"
            diff_msg += f"Actual lines: {len(actual_filtered)}\n"

            # Show first difference
            for i, (exp_line, act_line) in enumerate(zip(expected_filtered, actual_filtered)):
                if exp_line != act_line:
                    diff_msg += f"First diff at line {i+1}:\n"
                    diff_msg += f"  Expected: {exp_line}\n"
                    diff_msg += f"  Actual: {act_line}\n"
                    break

            return False, diff_msg

    except Exception as e:
        return False, f"Comparison error: {e}"


def main(argv: list[str] | None = None) -> int:
    """Main entry point for CI verification.

    Args:
        argv: Command line arguments

    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(
        description="Verify slash command YAML and generated files are in sync"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed diff output"
    )

    args = parser.parse_args(argv)

    project_root = detect_project_root()

    # Files to verify
    settings_file = project_root / ".claude" / "settings.local.json"
    docs_file = project_root / "docs" / "slash_commands" / "README.md"

    print("[*] Running verification...")
    print(f"[*] Project root: {project_root}")

    # Create temporary directory for generated files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Run build script to generate files
        print("[*] Generating files from YAML...")
        exit_code = run_build_dry_run(tmp_path)
        if exit_code != 0:
            print("[ERROR] Build failed", file=sys.stderr)
            return exit_code

        # Compare generated files with repository files
        tmp_settings = tmp_path / ".claude" / "settings.local.json"
        tmp_docs = tmp_path / "docs" / "slash_commands" / "README.md"

        violations = []

        # Check settings.local.json
        print("[*] Comparing .claude/settings.local.json...")
        is_equal, diff_msg = compare_json_files(settings_file, tmp_settings)
        if not is_equal:
            violations.append(f"settings.local.json: {diff_msg}")
        else:
            print("[OK] settings.local.json matches")

        # Check README.md
        print("[*] Comparing docs/slash_commands/README.md...")
        is_equal, diff_msg = compare_text_files(docs_file, tmp_docs)
        if not is_equal:
            violations.append(f"README.md: {diff_msg}")
        else:
            print("[OK] README.md matches")

    # Report results
    if violations:
        print("\n[ERROR] Violations detected:", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        print("\n[FIX] Run: python scripts/setup/build_slash_commands.py", file=sys.stderr)
        return 1
    else:
        print("\n[SUCCESS] All files are in sync!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
