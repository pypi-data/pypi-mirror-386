#!/usr/bin/env python3
# File: scripts/hooks/halfwidth_checker.py
# Purpose: Detect and optionally fix halfwidth alphanumerics in Japanese text
# Context: Pre-commit hook for documentation quality. Excludes technical terms and code.

"""
Halfwidth Alphanumeric Checker for Japanese Documentation

Detects halfwidth ASCII alphanumerics (a-z, A-Z, 0-9) that appear in Japanese text context.
Provides flexible exclusion rules to preserve technical terms, code, and URLs.

Design Principles:
- Context-aware: Only flags halfwidth in Japanese text, not in code or technical content
- Flexible exclusion: Configurable patterns for technical terms, URLs, file paths, etc.
- Auto-fix capable: Can convert halfwidth to fullwidth with --fix option
- Non-invasive: Warn-only mode for gradual adoption

Exclusion Rules:
1. Code blocks (triple backticks, inline code)
2. URLs and email addresses
3. File paths and extensions
4. Technical terms (configurable list)
5. Numbers with units (e.g., "10px", "5MB")
6. Version numbers (e.g., "v1.0.0")
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple
import subprocess


class Finding(NamedTuple):
    """A detected halfwidth character issue."""
    file: Path
    line_num: int
    col: int
    char: str
    context: str
    suggestion: str


# Halfwidth to fullwidth mapping
HALFWIDTH_TO_FULLWIDTH = str.maketrans(
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "０１２３４５６７８９ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
)


# Patterns to exclude (technical context)
EXCLUDE_PATTERNS = [
    # Code blocks
    r"```[\s\S]*?```",  # Triple backtick code blocks
    r"`[^`]+`",  # Inline code

    # Markdown tables (entire lines with pipe separators)
    r"^\|.*\|$",  # Table rows (| col1 | col2 |)
    r"^[\|\s\-:]+$",  # Table separator lines (|---|---|)

    # URLs and emails
    r"https?://[^\s]+",
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",

    # File paths
    r"[a-zA-Z]:[\\\/][^\s]+",  # Windows paths
    r"\/[a-zA-Z0-9_\-\/\.]+",  # Unix paths
    r"\.[a-zA-Z]{2,4}(?:\s|$)",  # File extensions

    # Version numbers
    r"v?\d+\.\d+\.\d+",
    r"v?\d+\.\d+",

    # Technical IDs
    r"[A-Z]{2,}\-\d+",  # JIRA-123
    r"#\d+",  # Issue numbers

    # Numbers with units
    r"\d+(?:px|pt|em|rem|%|ms|s|MB|KB|GB)",

    # Environment variables
    r"\$[A-Z_]+",
    r"[A-Z_]{3,}",

    # Function/class names (CamelCase or snake_case)
    r"[a-z]+_[a-z_]+",  # snake_case
    r"[A-Z][a-z]+(?:[A-Z][a-z]+)+",  # CamelCase
]

# Compile patterns (MULTILINE for table row patterns)
EXCLUDE_REGEX = re.compile("|".join(f"({p})" for p in EXCLUDE_PATTERNS), re.MULTILINE)

# Japanese character ranges
HIRAGANA = r"[\u3040-\u309F]"
KATAKANA = r"[\u30A0-\u30FF]"
KANJI = r"[\u4E00-\u9FFF]"
JAPANESE = f"(?:{HIRAGANA}|{KATAKANA}|{KANJI})"

# Halfwidth alphanumeric
HALFWIDTH_ALNUM = r"[a-zA-Z0-9]"


def is_japanese_context(text: str, pos: int, window: int = 10) -> bool:
    """Check if position is in Japanese text context.

    Args:
        text: Full text
        pos: Character position to check
        window: Number of characters to check before/after

    Returns:
        True if surrounded by Japanese characters
    """
    start = max(0, pos - window)
    end = min(len(text), pos + window)
    context = text[start:end]

    # Check if context contains Japanese characters
    return bool(re.search(JAPANESE, context))


def mask_excluded_regions(text: str) -> str:
    """Replace excluded regions with placeholders to skip detection.

    Args:
        text: Input text

    Returns:
        Text with excluded regions masked
    """
    def replace_with_spaces(match: re.Match) -> str:
        """Replace match with same-length spaces to preserve positions."""
        return " " * len(match.group(0))

    return EXCLUDE_REGEX.sub(replace_with_spaces, text)


def scan_file(path: Path, fix: bool = False) -> tuple[list[Finding], str | None]:
    """Scan a file for halfwidth alphanumerics in Japanese context.

    Args:
        path: File path to scan
        fix: If True, return fixed content

    Returns:
        Tuple of (findings list, fixed_content or None)
    """
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[ERROR] Cannot read {path}: {e}", file=sys.stderr)
        return ([], None)

    # Mask excluded regions
    masked_text = mask_excluded_regions(text)

    findings: list[Finding] = []
    fixed_text = text if fix else None

    for line_num, (orig_line, masked_line) in enumerate(zip(text.splitlines(), masked_text.splitlines()), start=1):
        for match in re.finditer(HALFWIDTH_ALNUM, masked_line):
            pos = match.start()
            char = match.group(0)

            # Check if in Japanese context
            if not is_japanese_context(orig_line, pos):
                continue

            # Extract context snippet
            start = max(0, pos - 20)
            end = min(len(orig_line), pos + 20)
            context = orig_line[start:end]

            # Generate suggestion
            suggestion = char.translate(HALFWIDTH_TO_FULLWIDTH)

            findings.append(Finding(
                file=path,
                line_num=line_num,
                col=pos + 1,
                char=char,
                context=context,
                suggestion=suggestion
            ))

            # Apply fix if requested
            if fix and fixed_text is not None:
                # Replace in the full text
                line_start = sum(len(l) + 1 for l in text.splitlines()[:line_num - 1])
                char_pos = line_start + pos
                fixed_text = fixed_text[:char_pos] + suggestion + fixed_text[char_pos + 1:]

    return (findings, fixed_text)


def get_staged_files(patterns: list[str]) -> list[Path]:
    """Get staged files matching patterns.

    Args:
        patterns: List of glob patterns

    Returns:
        List of staged file paths
    """
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            check=False,
            stdout=subprocess.PIPE,
            text=True
        )
        if res.returncode != 0:
            return []

        staged = [Path(f.strip()) for f in res.stdout.splitlines() if f.strip()]

        # Filter by patterns
        import fnmatch
        filtered = []
        for path in staged:
            if any(fnmatch.fnmatch(str(path), pat) for pat in patterns):
                filtered.append(path)

        return filtered
    except Exception:
        return []


def main(argv: list[str]) -> int:
    """Main entry point.

    Args:
        argv: Command line arguments

    Returns:
        Exit code (0 = success, 1 = findings detected)
    """
    ap = argparse.ArgumentParser(
        description="Detect halfwidth alphanumerics in Japanese text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    ap.add_argument(
        "--patterns",
        nargs="*",
        default=["docs/**/*.md", "*.md"],
        help="Glob patterns for files to check (default: docs/**/*.md, *.md)"
    )
    ap.add_argument(
        "--staged",
        action="store_true",
        help="Check only staged files (git diff --cached)"
    )
    ap.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix by converting halfwidth to fullwidth"
    )
    ap.add_argument(
        "--fail",
        action="store_true",
        help="Exit with error code if findings detected (default: warn only)"
    )
    ap.add_argument(
        "files",
        nargs="*",
        help="Explicit file paths to check (overrides --patterns)"
    )

    args = ap.parse_args(argv)

    # Determine files to check
    if args.files:
        files = [Path(f) for f in args.files]
    elif args.staged:
        files = get_staged_files(args.patterns)
        if not files:
            print("[halfwidth-checker] No staged files matching patterns")
            return 0
    else:
        # Glob all matching files
        files = []
        for pattern in args.patterns:
            files.extend(Path(".").glob(pattern))

    if not files:
        print("[halfwidth-checker] No files to check")
        return 0

    # Scan files
    all_findings: list[Finding] = []
    fixed_files: list[Path] = []

    for path in files:
        if not path.is_file():
            continue

        findings, fixed_content = scan_file(path, fix=args.fix)
        all_findings.extend(findings)

        if args.fix and fixed_content and findings:
            path.write_text(fixed_content, encoding="utf-8")
            fixed_files.append(path)

    # Report findings
    if all_findings:
        print(f"\n[halfwidth-checker] Found {len(all_findings)} halfwidth character(s) in Japanese text:\n")

        for f in all_findings:
            # Safe Unicode output (handle cp932 encoding issues on Windows)
            try:
                print(f"{f.file}:{f.line_num}:{f.col}: '{f.char}' → '{f.suggestion}'")
                print(f"  Context: {f.context}")
            except UnicodeEncodeError:
                # Fallback: ASCII-safe output
                print(f"{f.file}:{f.line_num}:{f.col}: '{f.char}' -> [fullwidth]")
                print(f"  Context: [Unicode characters, display skipped]")
            print()

        if args.fix:
            print(f"\n[halfwidth-checker] Auto-fixed {len(fixed_files)} file(s)")
            for path in fixed_files:
                print(f"  [FIXED] {path}")
        else:
            print("\n[halfwidth-checker] Run with --fix to auto-correct")

        return 1 if args.fail else 0

    print("[halfwidth-checker] OK (no halfwidth in Japanese context)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
