#!/usr/bin/env python3
"""
Specs Consolidator

Scans the `specs/` directory, groups specs by logical slug, chooses a canonical file
per group, and generates:
 - specs/README.md: categorized index of canonical specs
 - specs/CONSOLIDATION_PLAN.md: duplicates and proposed canonical mapping
 - specs/_meta/canonical_map.json: machine-readable mapping

Optionally, with --apply, moves deprecated duplicates to specs/_archive/<date>/ and
optionally creates stub files (disabled by default to reduce clutter).

Filename pattern assumed (best-effort):
  SPEC-<CATEGORY>-<NUMBER>_<SLUG>.md
Examples:
  SPEC-QUALITY-008_bulk_quality_check.md
  SPEC-PLOT-013_chapter_plot_with_scenes_use_case.md
Also tolerates hyphens in place of underscores before the slug divider.

This script is conservative and does not move files unless --apply is passed.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
SPECS_DIR = ROOT / "specs"
META_DIR = SPECS_DIR / "_meta"
ARCHIVE_DIR = SPECS_DIR / "_archive"


@dataclasses.dataclass(frozen=True)
class SpecFile:
    path: Path
    category: str
    number: Optional[int]
    slug: str


SPEC_RE = re.compile(
    r"^SPEC-"  # prefix
    r"(?P<category>[A-Z0-9]+)"  # category
    r"-"  # dash
    r"(?P<number>[0-9]{3})?"  # optional 3-digit number
    r"[_-]?"  # optional separator before slug
    r"(?P<slug>.+?)?"  # optional slug
    r"\.md$",
)


CATEGORY_PREFERENCE = [
    # Prefer more specific domains over GENERAL when selecting canonical across categories
    "ORCHESTRATOR",
    "PLOT",
    "SCENE",
    "QUALITY",
    "REPOSITORY",
    "SERVICE",
    "INTEGRATION",
    "PROMPT",
    "NFR",
    "REF",
    "PREFIGATE",
    "PATH",
    "QRC",
    "MCP",
    "JSON",
    "GENERAL",
]
CATEGORY_RANK = {c: i for i, c in enumerate(CATEGORY_PREFERENCE)}


def parse_spec_file(path: Path) -> Optional[SpecFile]:
    name = path.name
    m = SPEC_RE.match(name)
    if not m:
        return None
    category = (m.group("category") or "MISC").upper()
    num_str = m.group("number")
    number = int(num_str) if num_str and num_str.isdigit() else None
    raw_slug = (m.group("slug") or "").strip()
    # Normalize slug: lowercase, replace spaces with underscores
    slug = raw_slug.lower().replace(" ", "_")
    return SpecFile(path=path, category=category, number=number, slug=slug)


def load_specs() -> List[SpecFile]:
    specs: List[SpecFile] = []
    for p in sorted(SPECS_DIR.glob("*.md")):
        sf = parse_spec_file(p)
        if sf:
            specs.append(sf)
    return specs


def choose_canonical(group: List[SpecFile]) -> SpecFile:
    # Prefer specific categories; then by number (higher wins); then lexicographically by name
    def key(sf: SpecFile) -> Tuple[int, int, str]:
        cat_rank = CATEGORY_RANK.get(sf.category, 999)
        num = sf.number if sf.number is not None else -1
        return (cat_rank, -num, sf.path.name)

    return sorted(group, key=key)[0]


def categorize(specs: List[SpecFile]) -> Dict[str, List[SpecFile]]:
    cats: Dict[str, List[SpecFile]] = defaultdict(list)
    for sf in specs:
        cats[sf.category].append(sf)
    # sort within category by (number asc, slug)
    for c in cats:
        cats[c].sort(key=lambda s: (s.number if s.number is not None else 999, s.slug))
    return cats


def group_by_slug(specs: List[SpecFile]) -> Dict[str, List[SpecFile]]:
    groups: Dict[str, List[SpecFile]] = defaultdict(list)
    for sf in specs:
        # If slug is empty, use filename stem as fallback
        slug = sf.slug or sf.path.stem.lower()
        groups[slug].append(sf)
    return groups


def generate_readme(canonical_by_slug: Dict[str, SpecFile], specs_by_category: Dict[str, List[SpecFile]]) -> str:
    lines: List[str] = []
    lines.append("# specs index")
    lines.append("")
    lines.append("このフォルダは仕様書をカテゴリ別に一覧化したものです。重複は統合し、以下は現行（Canonical）のみを掲載しています。")
    lines.append("")
    lines.append("運用ポリシー:")
    lines.append("- 重複スラッグは最も適切なカテゴリかつ番号の大きいものをCanonicalとします")
    lines.append("- 旧版は `specs/_archive/` に退避し、必要に応じて参照します")
    lines.append("- 追加時は `SPEC-<CATEGORY>-<NNN>_<slug>.md` を推奨します")
    lines.append("")
    # 仕様と実装の最新構成に関する移行注記（自動生成にも恒久反映）
    lines.append("移行注記:")
    lines.append("- 実装は `scripts/` から `src/noveler/` および `src/mcp_servers/` に移行済みです。")
    lines.append("- 旧CLI前提の仕様は、MCPツール経由（例: `src/mcp_servers/noveler/json_conversion_server.py`）での実行に置き換えられています。")
    lines.append("")
    # 命名規約とカテゴリ優先度を明記
    lines.append("## 命名規約")
    lines.append("")
    lines.append("- 形式: `SPEC-<CATEGORY>-<NNN>_<slug>.md`")
    lines.append("- `<NNN>` は3桁の番号（例: 001）。未採番は省略可")
    lines.append("- `<slug>` は小文字・英数字・アンダースコア（スペースは`_`に）")
    lines.append("- 例: `SPEC-QUALITY-020_bulk_quality_check.md`")
    lines.append("")
    lines.append("## カテゴリ優先順位（統合時の指針）")
    lines.append("")
    lines.append(
        " → ".join(CATEGORY_PREFERENCE)
    )
    lines.append("")

    for cat in sorted(specs_by_category.keys(), key=lambda c: CATEGORY_RANK.get(c, 999)):
        # collect canonical files in this category
        canon_in_cat = [sf for slug, sf in canonical_by_slug.items() if sf.category == cat]
        if not canon_in_cat:
            continue
        lines.append(f"## {cat}")
        lines.append("")
        for sf in sorted(canon_in_cat, key=lambda s: (s.number if s.number is not None else 999, s.slug)):
            num = f"{sf.number:03d}" if sf.number is not None else "—"
            rel = sf.path.relative_to(SPECS_DIR).as_posix()
            title = sf.path.stem
            lines.append(f"- [{title}](./{rel})  ({cat}-{num})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def generate_consolidation_plan(groups: Dict[str, List[SpecFile]], canonical_by_slug: Dict[str, SpecFile]) -> str:
    lines: List[str] = []
    lines.append("# specs consolidation plan")
    lines.append("")
    lines.append("以下はスラッグ（論理名）ごとの統廃合案です。Canonical 以外は `_archive/` へ退避予定です。")
    lines.append("")
    num_dupes = 0
    for slug in sorted(groups.keys()):
        group = groups[slug]
        if len(group) <= 1:
            continue
        num_dupes += 1
        canon = canonical_by_slug[slug]
        lines.append(f"## {slug}")
        lines.append("")
        lines.append(f"- Canonical: {canon.path.name} ({canon.category}-{canon.number if canon.number is not None else '—'})")
        lines.append("- Deprecated:")
        for sf in sorted([s for s in group if s != canon], key=lambda s: (CATEGORY_RANK.get(s.category, 999), s.number or -1)):
            lines.append(f"  - {sf.path.name} ({sf.category}-{sf.number if sf.number is not None else '—'})")
        lines.append("")
    if num_dupes == 0:
        lines.append("重複は検出されませんでした。")
    return "\n".join(lines).rstrip() + "\n"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def apply_moves(groups: Dict[str, List[SpecFile]], canonical_by_slug: Dict[str, SpecFile], create_stubs: bool = False) -> List[Tuple[Path, Path]]:
    """Move deprecated specs to archive. Returns list of (src, dst) moves."""
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    batch_dir = ARCHIVE_DIR / timestamp
    batch_dir.mkdir(parents=True, exist_ok=True)
    planned_moves: List[Tuple[Path, Path]] = []

    for slug, group in groups.items():
        if len(group) <= 1:
            continue
        canon = canonical_by_slug[slug]
        for sf in group:
            if sf == canon:
                continue
            dst = batch_dir / sf.path.name
            planned_moves.append((sf.path, dst))
            # move file
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(sf.path), str(dst))
            if create_stubs:
                stub = sf.path
                stub.write_text(
                    f"# DEPRECATED\n\nThis spec has been archived to `{dst.relative_to(ROOT).as_posix()}`.\nCanonical spec: `{canon.path.name}`.\n",
                    encoding="utf-8",
                )
    return planned_moves


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Move deprecated specs to archive")
    ap.add_argument("--stubs", action="store_true", help="Create stub files at old locations (off by default)")
    args = ap.parse_args()

    if not SPECS_DIR.exists():
        raise SystemExit(f"specs dir not found: {SPECS_DIR}")

    specs = load_specs()
    specs_by_cat = categorize(specs)
    groups = group_by_slug(specs)
    canonical_by_slug: Dict[str, SpecFile] = {slug: choose_canonical(g) for slug, g in groups.items()}

    # Generate artifacts
    META_DIR.mkdir(parents=True, exist_ok=True)
    readme = generate_readme(canonical_by_slug, specs_by_cat)
    plan = generate_consolidation_plan(groups, canonical_by_slug)
    write_file(SPECS_DIR / "README.md", readme)
    write_file(SPECS_DIR / "CONSOLIDATION_PLAN.md", plan)

    # Save mapping
    mapping = {
        slug: {
            "canonical": {
                "path": str(sf.path.relative_to(ROOT)),
                "category": sf.category,
                "number": sf.number,
            },
            "duplicates": [str(s.path.relative_to(ROOT)) for s in groups[slug] if s != sf],
        }
        for slug, sf in canonical_by_slug.items()
    }
    (META_DIR / "canonical_map.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.apply:
        moves = apply_moves(groups, canonical_by_slug, create_stubs=args.stubs)
        # Append move log to plan
        if moves:
            with (SPECS_DIR / "CONSOLIDATION_PLAN.md").open("a", encoding="utf-8") as f:
                f.write("\n---\n\n")
                f.write("## 実施済みアーカイブ移動ログ\n\n")
                for src, dst in moves:
                    f.write(f"- {src.name} -> _archive/{dst.parent.name}/{dst.name}\n")

    print("Generated: specs/README.md, specs/CONSOLIDATION_PLAN.md, specs/_meta/canonical_map.json")
    if args.apply:
        print("Applied archive moves for duplicates.")


if __name__ == "__main__":
    main()
