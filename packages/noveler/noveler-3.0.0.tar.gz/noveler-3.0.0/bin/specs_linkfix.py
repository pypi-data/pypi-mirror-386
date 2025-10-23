#!/usr/bin/env python3
"""
Specs Link Fixer

Scans Markdown files and rewrites links that point to archived/duplicate specs
to their canonical targets based on specs/_meta/canonical_map.json.

Behavior:
 - Only processes .md files outside of `specs/_archive/` and `.git/`.
 - Matches Markdown links of form: [text](path[#anchor])
 - Resolves link target relative to the file, compares to duplicate paths from the map
 - Rewrites to canonical relative path, preserving anchors.

Usage:
  Dry-run: python3 bin/specs_linkfix.py
  Apply  : python3 bin/specs_linkfix.py --apply
"""

from __future__ import annotations

import argparse
import json
import re
from os.path import relpath
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
CANON_MAP_PATH = ROOT / "specs/_meta/canonical_map.json"

LINK_RE = re.compile(r"\[(?P<text>[^\]]*)\]\((?P<href>[^)]+)\)")


def load_canonical_map() -> Dict[str, Dict[str, object]]:
    data = json.loads(CANON_MAP_PATH.read_text(encoding="utf-8"))
    return data


def build_duplicate_to_canonical(data: Dict[str, Dict[str, object]]) -> Dict[Path, Path]:
    mapping: Dict[Path, Path] = {}
    for slug, entry in data.items():
        canon_rel = Path(entry["canonical"]["path"])  # relative to repo root
        for dup_rel_str in entry.get("duplicates", []):
            dup_rel = Path(dup_rel_str)
            mapping[dup_rel] = canon_rel
    return mapping


def normalize_target(href: str) -> Tuple[str, str]:
    """Split href into (path, anchor_or_query) where the second retains leading # or ? if present."""
    if "#" in href:
        path, anchor = href.split("#", 1)
        return path, f"#{anchor}"
    if "?" in href:
        path, query = href.split("?", 1)
        return path, f"?{query}"
    return href, ""


def iter_markdown_files() -> List[Path]:
    files: List[Path] = []
    for p in ROOT.rglob("*.md"):
        rel = p.relative_to(ROOT)
        # Skip archives and .git
        if str(rel).startswith("specs/_archive/"):
            continue
        if str(rel).startswith(".git/"):
            continue
        files.append(p)
    return files


def compute_replacement(file_path: Path, href: str, dup_to_canon: Dict[Path, Path]) -> Tuple[str, bool]:
    orig_href = href
    path_part, suffix = normalize_target(href)
    # Resolve to absolute path
    if path_part.startswith("/"):
        abs_target = ROOT / path_part.lstrip("/")
    else:
        abs_target = (file_path.parent / path_part).resolve()
    try:
        rel_target = abs_target.relative_to(ROOT)
    except ValueError:
        # outside repo; ignore
        return orig_href, False
    # If rel_target matches any duplicate, replace
    if rel_target in dup_to_canon:
        canon_rel = dup_to_canon[rel_target]
        canon_abs = (ROOT / canon_rel).resolve()
        rel_str = relpath(canon_abs, file_path.parent)
        href_new = Path(rel_str).as_posix() + suffix
        return href_new, True
    return orig_href, False


def process_file(p: Path, dup_to_canon: Dict[Path, Path], apply: bool) -> Tuple[int, List[str]]:
    text = p.read_text(encoding="utf-8")
    changes = 0
    lines_out: List[str] = []
    for line in text.splitlines(keepends=False):
        def repl(m: re.Match) -> str:
            nonlocal changes
            text_part = m.group("text")
            href = m.group("href"); new_href, changed = compute_replacement(p, href, dup_to_canon)
            if changed:
                changes += 1
            return f"[{text_part}]({new_href})"
        new_line = LINK_RE.sub(repl, line)
        lines_out.append(new_line)
    if apply and changes:
        p.write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    return changes, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Apply fixes (otherwise dry-run)")
    args = ap.parse_args()

    data = load_canonical_map()
    dup_to_canon = build_duplicate_to_canonical(data)

    total_changes = 0
    changed_files: List[Tuple[Path, int]] = []
    for p in iter_markdown_files():
        chg, _ = process_file(p, dup_to_canon, apply=args.apply)
        if chg:
            changed_files.append((p, chg))
            total_changes += chg

    if changed_files:
        print("Files updated:" if args.apply else "Files to update:")
        for fp, c in changed_files:
            print(f"- {fp.relative_to(ROOT)} ({c} link(s))")
    else:
        print("No links to update.")
    print(f"Total links {'updated' if args.apply else 'to update'}: {total_changes}")


if __name__ == "__main__":
    main()
