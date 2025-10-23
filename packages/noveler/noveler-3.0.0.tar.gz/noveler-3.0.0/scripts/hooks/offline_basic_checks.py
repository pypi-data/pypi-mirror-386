#!/usr/bin/env python3
"""Offline-friendly basic pre-commit checks.

This script bundles a subset of the original pre-commit-hooks so that
developers can run the project hooks without reaching out to remote
repositories.  It performs the following fixes/checks:

* Trailing whitespace removal
* Ensuring a single newline at EOF
* Large file guard (default 1000 KB)
* Merge conflict marker detection
* Debug statement detection (pdb/breakpoint)
* JSON/YAML syntax validation (YAML is best effort)

If an issue can be safely auto-corrected (whitespace/EOF), the script rewrites
the file in-place.  Validation failures abort the hook with a non-zero exit
code so that the calling git command fails, mirroring the behaviour of the
original hooks.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

# Maximum allowed file size in kilobytes for `check-added-large-files` parity.
MAX_FILE_KB = 1000


class BasicCheckError(Exception):
    """Custom error for reporting check failures."""


def _load_yaml(text: str) -> None:
    """Validate YAML content if PyYAML is available."""

    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        # PyYAML が無い環境では検証をスキップ（オフライン前提）。
        return

    yaml.safe_load(text)


def _normalise_newlines(text: str) -> str:
    """Normalise newline characters to ``\n`` for consistent processing."""

    return text.replace("\r\n", "\n").replace("\r", "\n")


def _fix_trailing_whitespace(lines: list[str]) -> tuple[list[str], bool]:
    """Strip trailing whitespace while preserving original newline symbols."""

    fixed_lines: list[str] = []
    modified = False

    for line in lines:
        if line.endswith(("\n", "\r")):
            body = line.rstrip("\r\n")
            terminator = line[len(body) :]
        else:
            body, terminator = line, ""

        trimmed = body.rstrip(" \t")
        if trimmed != body:
            modified = True
        fixed_lines.append(trimmed + terminator)

    return fixed_lines, modified


def _ensure_trailing_newline(lines: list[str]) -> tuple[list[str], bool]:
    """Ensure the file ends with exactly one newline."""

    if not lines:
        return ["\n"], True

    last = lines[-1]
    if last.endswith("\n"):
        # Remove superfluous empty lines at the end.
        while len(lines) > 1 and lines[-2].strip() == "" and lines[-1] == "\n":
            lines.pop()
        return lines, False

    lines[-1] = last + "\n"
    return lines, True


def _contains_conflict_markers(text: str) -> bool:
    conflict_markers = ("<<<<<<<", "=======", ">>>>>>>")
    return any(marker in text for marker in conflict_markers)


def _contains_debug_statements(text: str) -> bool:
    debug_tokens = ("import pdb", "pdb.set_trace", "breakpoint(")
    return any(token in text for token in debug_tokens)


def _check_large_file(path: Path) -> None:
    size_kb = path.stat().st_size / 1024
    if size_kb > MAX_FILE_KB:
        raise BasicCheckError(
            f"{path} exceeds the maximum allowed size of {MAX_FILE_KB} KB"
        )


def _process_file(path: Path) -> list[str]:
    """Run all checks against a single file.

    Returns a list of warning/error strings. An empty list means success.
    """

    messages: list[str] = []

    if not path.exists():
        return messages

    # Skip binary files by attempting a UTF-8 decode.
    try:
        raw_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return messages

    _check_large_file(path)

    if _contains_conflict_markers(raw_text):
        messages.append("merge conflict markers detected")

    if _contains_debug_statements(raw_text):
        messages.append("debug statement detected (pdb/breakpoint)")

    normalised = _normalise_newlines(raw_text)
    lines = normalised.splitlines(keepends=True)

    lines, whitespace_modified = _fix_trailing_whitespace(lines)
    lines, newline_modified = _ensure_trailing_newline(lines)

    if whitespace_modified or newline_modified:
        path.write_text("".join(lines), encoding="utf-8")

    # Run format validations for specific file types.
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            json.loads(_normalise_newlines("".join(lines)))
        except json.JSONDecodeError as exc:
            messages.append(f"invalid JSON: {exc}")
    elif suffix in {".yml", ".yaml"}:
        try:
            _load_yaml(_normalise_newlines("".join(lines)))
        except Exception as exc:  # noqa: BLE001 - surface YAML errors
            messages.append(f"invalid YAML: {exc}")

    return messages


def run(files: Iterable[str]) -> int:
    errors: list[str] = []

    for file_name in files:
        path = Path(file_name)
        try:
            messages = _process_file(path)
        except BasicCheckError as exc:
            errors.append(f"{path}: {exc}")
            continue

        for message in messages:
            errors.append(f"{path}: {message}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="files provided by pre-commit")
    args = parser.parse_args(argv)
    return run(args.files)


if __name__ == "__main__":
    raise SystemExit(main())
