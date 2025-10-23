#!/usr/bin/env python3
# File: scripts/hooks/encoding_guard.py
# Purpose: Guard against Unicode replacement character (U+FFFD) and invalid encodings.
# Context: Used in pre-commit. Fails for src patterns; warns for docs patterns.

from __future__ import annotations

import argparse
import glob
from pathlib import Path
from typing import Iterable
import sys
import fnmatch
import subprocess

REPLACEMENT = "\uFFFD"


def _norm(p: str) -> str:
    return p.replace("\\", "/")


def _iter_files(patterns: Iterable[str], excludes: Iterable[str]) -> list[Path]:
    # Glob-based collection (full-repo scan)
    pset: list[Path] = []
    ex: list[Path] = []
    for e in excludes:
        ex.extend(Path(p) for p in glob.glob(e, recursive=True))
    ex_set = {p.resolve() for p in ex}
    for pat in patterns:
        for s in glob.glob(pat, recursive=True):
            p = Path(s)
            if p.is_file() and p.resolve() not in ex_set:
                pset.append(p)
    return pset


def _iter_staged(fail: list[str], warn: list[str], excludes: list[str]) -> tuple[list[Path], list[Path]]:
    """Return (fail_set, warn_set) from git staged files matching patterns.

    A file belongs to 'fail' if it matches any fail pattern. Otherwise, if it
    matches any warn pattern, it belongs to 'warn'. Excludes always win.
    """
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "-z"],
            check=False,
            stdout=subprocess.PIPE,
        )
        out = res.stdout.decode("utf-8", errors="replace")
        staged = [x for x in out.split("\x00") if x]
    except Exception:
        staged = []
    if not staged:
        return ([], [])

    def matches(path: str, pats: list[str]) -> bool:
        posix = _norm(path)
        return any(fnmatch.fnmatch(posix, _norm(p)) for p in pats)

    def is_excluded(path: str) -> bool:
        return matches(path, excludes)

    fail_set: list[Path] = []
    warn_set: list[Path] = []
    for s in staged:
        if is_excluded(s):
            continue
        if matches(s, fail):
            fail_set.append(Path(s))
        elif matches(s, warn):
            warn_set.append(Path(s))
    return (fail_set, warn_set)


def _files_from_diff(diff_range: str) -> list[str]:
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only", diff_range],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if res.returncode not in (0, 1):
            raise RuntimeError(res.stderr.strip() or f"git diff returned {res.returncode}")
        files = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        return files
    except Exception:
        return []


def _partition_explicit(paths: Iterable[str], fail: list[str], warn: list[str], excludes: list[str]) -> tuple[list[Path], list[Path]]:
    fail_set: list[Path] = []
    warn_set: list[Path] = []

    def matches(path: str, pats: list[str]) -> bool:
        posix = _norm(path)
        return any(fnmatch.fnmatch(posix, _norm(p)) for p in pats)

    for raw in paths:
        if not raw:
            continue
        if matches(raw, excludes):
            continue
        if matches(raw, fail):
            fail_set.append(Path(raw))
        elif matches(raw, warn):
            warn_set.append(Path(raw))
    return fail_set, warn_set


def scan(paths: Iterable[Path]) -> tuple[list[str], list[str]]:
    """Return (bad, warn) where 'bad' lines should fail the hook.

    For each file, if it cannot be decoded as UTF-8, we record ENCODING_ERROR.
    If it decodes but contains U+FFFD, we record U+FFFD occurrences.
    """
    findings: list[str] = []
    errors: list[str] = []
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception as e:
            errors.append(f"ENCODING_ERROR: {p}: {e}")
            continue
        if REPLACEMENT in text:
            for i, line in enumerate(text.splitlines(), start=1):
                col = line.find(REPLACEMENT)
                if col >= 0:
                    snippet = line[max(0, col - 20) : col + 20]
                    findings.append(f"U+FFFD: {p}:{i}:{col+1}: {snippet}")
    return errors, findings


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Encoding guard for U+FFFD and UTF-8 errors")
    ap.add_argument("--fail", nargs="*", default=["src/**/*.py"], help="Glob patterns that should fail on findings")
    ap.add_argument(
        "--warn",
        nargs="*",
        default=["docs/**/*.md"],
        help="Glob patterns that only warn on findings",
    )
    ap.add_argument(
        "--exclude",
        nargs="*",
        default=["docs/archive/**", "docs/backup/**"],
        help="Glob patterns to exclude from scanning",
    )
    ap.add_argument(
        "--staged",
        action="store_true",
        help="Scan only staged files (diff --cached).",
    )
    ap.add_argument(
        "--diff-range",
        type=str,
        default=None,
        help="Git diff range (e.g. origin/main...HEAD) to compute changed files.",
    )
    ap.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Explicit file paths to scan (overrides diff/staged/glob).",
    )
    args = ap.parse_args(argv)

    fail_files: list[Path]
    warn_files: list[Path]

    if args.files:
        fail_files, warn_files = _partition_explicit(args.files, list(args.fail), list(args.warn), list(args.exclude))
        if not fail_files and not warn_files:
            print("[encoding-guard] No matching explicit files; skipping")
            return 0
    elif args.diff_range:
        diff_files = _files_from_diff(args.diff_range)
        if not diff_files:
            print(f"[encoding-guard] No files in diff_range {args.diff_range}; skipping")
            return 0
        fail_files, warn_files = _partition_explicit(diff_files, list(args.fail), list(args.warn), list(args.exclude))
        if not fail_files and not warn_files:
            print(f"[encoding-guard] Diff range {args.diff_range} has no matching files; skipping")
            return 0
    elif args.staged:
        fail_files, warn_files = _iter_staged(list(args.fail), list(args.warn), list(args.exclude))
        if not fail_files and not warn_files:
            print("[encoding-guard] No matching staged files; skipping")
            return 0
    else:
        fail_files = _iter_files(args.fail, args.exclude)
        warn_files = _iter_files(args.warn, args.exclude)

    bad_errors, bad_findings = scan(fail_files)
    warn_errors, warn_findings = scan(warn_files)

    rc = 0
    if bad_errors or bad_findings:
        rc = 1
        print("[encoding-guard] FAIL domain (src) findings:")
        for line in bad_errors + bad_findings:
            print(line)
    if warn_errors or warn_findings:
        print("[encoding-guard] WARN docs findings:")
        for line in warn_errors + warn_findings:
            print(line)

    if rc == 0:
        print("[encoding-guard] OK (no U+FFFD or encoding errors in fail set)")
    return rc


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
