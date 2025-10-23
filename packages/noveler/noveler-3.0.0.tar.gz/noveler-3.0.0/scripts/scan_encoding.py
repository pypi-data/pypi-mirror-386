#!/usr/bin/env python3
# File: scripts/scan_encoding.py
# Purpose: Warn-only scan for the Unicode replacement character (U+FFFD, "\uFFFD")
#          to catch mojibake in docs/src early. Designed for CI or local runs.
# Context: Invoked by bin/scan-encoding and the Codex/Claude slash command `/scan-encoding`.

"""Warn-only encoding scan utility.

Scans given file globs (default: docs/**/*.md and src/**/*.py) and reports any
occurrence of the replacement character U+FFFD ("�"). Intended as a lightweight
warning; exit status is always 0 to avoid failing pipelines by default.

Args:
  --paths: One or more glob patterns to scan. Defaults to docs/**/*.md src/**/*.py.
  --output: Optional file path to write the list of problematic files/lines.

Behavior:
  - Prints lines in the form: PATH:LINE: COLUMN: CONTEXT when U+FFFD is found.
  - Also reports files that fail to open as ENCODING_READ_ERROR.
  - Returns exit code 0 even if issues are found (warn-only).
"""

from __future__ import annotations

import argparse
import sys
import glob
import fnmatch
import os
from pathlib import Path
from typing import Iterable

REPLACEMENT = "\uFFFD"


def _normalize_pattern(pat: str) -> str:
    """Normalize a glob pattern to POSIX-style for matching across OSes."""
    return pat.replace("\\", "/")


def _is_excluded(path: Path, excludes: list[str]) -> bool:
    if not excludes:
        return False
    posix = path.as_posix()
    for pat in excludes:
        if fnmatch.fnmatch(posix, pat):
            return True
    return False


def _iter_paths(patterns: Iterable[str], excludes: Iterable[str] | None = None) -> Iterable[Path]:
    ex = [
        _normalize_pattern(p) for p in (list(excludes) if excludes else [])
    ]
    for pat in patterns:
        for s in glob.glob(pat, recursive=True):
            p = Path(s)
            if p.is_file() and not _is_excluded(p, ex):
                yield p


def scan(paths: Iterable[str], excludes: Iterable[str] | None = None) -> list[str]:
    """Scan files for the replacement character.

    Returns a list of textual findings. Never raises for individual file errors.
    """
    findings: list[str] = []
    for path in _iter_paths(paths, excludes):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:  # pragma: no cover (I/O env-specific)
            findings.append(f"ENCODING_READ_ERROR: {path}: {e}")
            continue
        if REPLACEMENT not in text:
            continue
        for ln, line in enumerate(text.splitlines(), start=1):
            col = line.find(REPLACEMENT)
            if col != -1:
                # Keep the context short to avoid noisy output
                snippet = line[max(0, col - 20): col + 20]
                findings.append(f"U+FFFD: {path}:{ln}:{col+1}: {snippet}")
    return findings


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Warn-only replacement char scan (U+FFFD)")
    ap.add_argument(
        "--paths",
        nargs="*",
        default=["docs/**/*.md", "src/**/*.py"],
        help="Glob patterns to scan (default: docs/**/*.md src/**/*.py)",
    )
    ap.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Glob patterns to exclude (e.g., docs/archive/** docs/backup/**)",
    )
    ap.add_argument("--output", type=str, default=None, help="Optional path to save findings")
    args = ap.parse_args(argv)

    findings = scan(args.paths, excludes=args.exclude)

    if findings:
        print("[encoding-scan] Found potential mojibake (replacement char U+FFFD):", file=sys.stderr)
        for line in findings:
            print(line)
    else:
        print("[encoding-scan] No replacement characters found (U+FFFD).")

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(findings), encoding="utf-8")
        print(f"[encoding-scan] Wrote report: {out}")
        if args.exclude:
            print(
                "[encoding-scan] Excluded patterns:",
                ", ".join(args.exclude),
            )

    # Warn-only: never fail the build by default.
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
