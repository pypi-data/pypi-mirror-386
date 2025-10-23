#!/usr/bin/env python3
"""Simple impact audit utility.

Search the repository for a keyword/pattern and write a brief report.

Usage:
  python scripts/tools/impact_audit.py --pattern "preview" --output temp/impact_audit/preview.md
"""
from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path

EXCLUDES = {".git", "dist", "__pycache__", ".venv", "venv", ".mypy_cache", ".ruff_cache"}


@dataclass
class Match:
    """A single matched line in a file."""
    path: Path
    line_number: int
    line_text: str


@dataclass
class AuditResult:
    """Result of an audit run."""
    total_matches: int
    matches: list[Match]

    def matches_by_file(self) -> dict[Path, list[Match]]:
        """Group matches by file path."""
        result = {}
        for match in self.matches:
            if match.path not in result:
                result[match.path] = []
            result[match.path].append(match)
        return result


def find_guide_root() -> Path:
    """Find the project root directory."""
    return Path.cwd()


def iter_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        # prune excluded directories
        dirnames[:] = [n for n in dirnames if n not in EXCLUDES]
        if any(part in EXCLUDES for part in d.parts):
            continue
        for fn in filenames:
            p = d / fn
            if p.suffix in {".py", ".md", ".yaml", ".yml", ".toml", ".json"}:
                out.append(p)
    return out


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", required=True, help="regex pattern to search for")
    ap.add_argument("--output", required=True, help="output file path (md)")
    ap.add_argument("--paths", default=".", help="paths to search (default: current directory)")
    ap.add_argument("--fail-on-zero", action="store_true", help="fail if no matches found")
    return ap.parse_args(args)


def run_audit(args: argparse.Namespace, root: Path | None = None) -> AuditResult:
    """Run the audit and return results."""
    if root is None:
        root = find_guide_root()

    search_path = root / args.paths if args.paths != "." else root
    files = iter_files(search_path)
    rx = re.compile(args.pattern)

    matches: list[Match] = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if rx.search(line):
                # Store relative path from root
                rel_path = f.relative_to(root) if root else f
                matches.append(Match(rel_path, i, line.strip()))

    return AuditResult(total_matches=len(matches), matches=matches)


def main(args: list[str] | None = None) -> int:
    """Main entry point."""
    parsed = parse_args(args)
    root = find_guide_root()
    result = run_audit(parsed, root)

    # Write report
    out_path = Path(parsed.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as w:
        w.write(f"# Impact Audit — pattern: `{parsed.pattern}`\n\n")
        w.write(f"Total matches: {result.total_matches}\n\n")
        for match in result.matches[:1000]:
            w.write(f"- {match.path}:{match.line_number}: {match.line_text}\n")

    if parsed.output != "-":
        print(f"Wrote report: {out_path}")

    if parsed.fail_on_zero and result.total_matches == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

