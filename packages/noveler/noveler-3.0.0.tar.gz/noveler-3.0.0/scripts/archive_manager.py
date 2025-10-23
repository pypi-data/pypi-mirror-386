#!/usr/bin/env python3
"""Archive candidate detection and management.

File: scripts/archive_manager.py
Purpose: Detect documents that should be archived based on age and completion status.
Context: Used by CI/CD to suggest archive candidates in PRs.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


def get_file_age(file_path: Path) -> int:
    """Get the age of a file in days since last modification."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", str(file_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,  # Prevent hanging on large repos
        )
        if result.returncode == 0 and result.stdout.strip():
            timestamp = int(result.stdout.strip())
            last_modified = datetime.fromtimestamp(timestamp)
            age = (datetime.now() - last_modified).days
            return age
    except (ValueError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        pass

    # Fallback to filesystem mtime
    mtime = file_path.stat().st_mtime
    last_modified = datetime.fromtimestamp(mtime)
    age = (datetime.now() - last_modified).days
    return age


def is_completed_file(file_path: Path) -> bool:
    """Check if a file has completion markers."""
    try:
        content = file_path.read_text(encoding="utf-8")
        completion_markers = [
            "完了",
            "completed",
            "✅",
            "[DONE]",
            "[COMPLETE]",
            "implementation completed",
            "実装完了",
        ]
        return any(marker.lower() in content.lower() for marker in completion_markers)
    except (OSError, UnicodeDecodeError):
        return False


def suggest_candidates(
    docs_dir: Path = Path("docs"),
    age_threshold_days: int = 90,
    check_proposals: bool = True,
    check_refactoring: bool = True,
    check_drafts: bool = True,
) -> list[tuple[Path, str]]:
    """Suggest archive candidates based on age and completion status.

    Args:
        docs_dir: Base documentation directory
        age_threshold_days: Files older than this are candidates
        check_proposals: Check proposals/ directory
        check_refactoring: Check refactoring/ directory
        check_drafts: Check drafts/ directory

    Returns:
        List of (file_path, reason) tuples
    """
    candidates: list[tuple[Path, str]] = []

    # Check proposals/
    if check_proposals and (docs_dir / "proposals").exists():
        for file in (docs_dir / "proposals").rglob("*.md"):
            age = get_file_age(file)
            if age > age_threshold_days:
                if is_completed_file(file):
                    reason = f"Completed proposal, {age} days old"
                    candidates.append((file, reason))
                else:
                    reason = f"Stale proposal, {age} days old (no update)"
                    candidates.append((file, reason))

    # Check refactoring/
    if check_refactoring and (docs_dir / "refactoring").exists():
        for file in (docs_dir / "refactoring").rglob("*.md"):
            age = get_file_age(file)
            if age > age_threshold_days and is_completed_file(file):
                reason = f"Completed refactoring plan, {age} days old"
                candidates.append((file, reason))

    # Check drafts/
    if check_drafts and (docs_dir / "drafts").exists():
        for file in (docs_dir / "drafts").rglob("*.md"):
            age = get_file_age(file)
            if age > age_threshold_days:
                reason = f"Stale draft, {age} days old"
                candidates.append((file, reason))

    # Check for review-related files
    for pattern in ["*review*.md", "*REVIEW*.md"]:
        for file in docs_dir.glob(pattern):
            if file.parent.name == "archive":
                continue  # Skip already archived
            age = get_file_age(file)
            if age > 30:  # Reviews older than 30 days
                if is_completed_file(file):
                    reason = f"Completed review, {age} days old"
                    candidates.append((file, reason))

    return candidates


def print_candidates(candidates: list[tuple[Path, str]]) -> None:
    """Print archive candidates in a formatted way."""
    if not candidates:
        print("No archive candidates found.")
        return

    print(f"Found {len(candidates)} archive candidate(s):")
    print()

    for file_path, reason in candidates:
        print(f"- `{file_path}` - {reason}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Archive candidate detection")
    parser.add_argument(
        "command",
        choices=["suggest-candidates"],
        help="Command to execute",
    )
    parser.add_argument(
        "--age-threshold",
        type=int,
        default=90,
        help="Age threshold in days (default: 90)",
    )
    parser.add_argument(
        "--no-proposals",
        action="store_true",
        help="Skip proposals/ directory",
    )
    parser.add_argument(
        "--no-refactoring",
        action="store_true",
        help="Skip refactoring/ directory",
    )
    parser.add_argument(
        "--no-drafts",
        action="store_true",
        help="Skip drafts/ directory",
    )

    args = parser.parse_args()

    if args.command == "suggest-candidates":
        candidates = suggest_candidates(
            age_threshold_days=args.age_threshold,
            check_proposals=not args.no_proposals,
            check_refactoring=not args.no_refactoring,
            check_drafts=not args.no_drafts,
        )
        print_candidates(candidates)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
