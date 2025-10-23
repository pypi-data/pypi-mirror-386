"""Specs.scripts.specs_sync
Where: Specs automation script syncing specification files.
What: Synchronises specification sources with generated outputs.
Why: Ensures specification artifacts stay up to date.
"""

#!/usr/bin/env python3
import os
import re
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # specs/

# Category normalization for better semantics in indices and counters
CATEGORY_NORMALIZATION = {
    # Legacy prefix buckets mapped to semantic categories
    "A31": "QUALITY",
    "A28": "PLOT",
    "A30": "WRITE",
    "A38": "WRITE",
    "A40A41": "QUALITY",
    "901": "ARCH",
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def find_all_spec_files() -> list[Path]:
    spec_files = []
    exclude_dirs = {"_archive", "archive", "_meta", "_scripts"}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # prune excluded
        rel = Path(dirpath).relative_to(ROOT)
        parts = set(rel.parts)
        if parts & exclude_dirs:
            continue
        for fn in filenames:
            # only SPEC-* files with md/yaml
            if not (fn.startswith("SPEC-") or fn.startswith("Spec-") or fn.startswith("spec-")):
                continue
            if fn.lower().endswith((".md", ".yaml", ".yml")):
                spec_files.append(Path(dirpath) / fn)
    return spec_files


SPEC_ID_RE = re.compile(r"\b(SPEC-[A-Z0-9]+-[0-9]{3}(?:-[A-Z0-9]+)?)\b")


def parse_e2e_mapping_ids(path: Path) -> set[str]:
    """Parse spec IDs listed under top-level e2e_mappings (ignore supplementary/groups)."""
    ids: set[str] = set()
    text = read_text(path)
    if not text:
        return ids
    lines = text.splitlines()
    in_e2e = False
    for line in lines:
        if line.strip().startswith("#"):
            continue
        if not in_e2e:
            if re.match(r"^e2e_mappings:\s*$", line):
                in_e2e = True
            continue
        # detect end of block (next top-level key)
        if re.match(r"^[A-Za-z_]+:\s*$", line):
            break
        # capture spec id keys with indentation
        m = re.match(r"^\s{2,}(SPEC-[A-Z0-9-]+):\s*$", line)
        if m:
            base = m.group(1).split("-SUB-")[0]
            ids.add(base)
    return ids


def parse_integration_mapping_ids(path: Path) -> set[str]:
    """Parse spec IDs listed under top-level integration_mappings."""
    ids: set[str] = set()
    text = read_text(path)
    if not text:
        return ids
    lines = text.splitlines()
    in_block = False
    for line in lines:
        if line.strip().startswith("#"):
            continue
        if not in_block:
            if re.match(r"^integration_mappings:\s*$", line):
                in_block = True
            continue
        # end of block when next top-level key
        if re.match(r"^[A-Za-z_]+:\s*$", line):
            break
        m = re.match(r"^\s{2,}(SPEC-[A-Z0-9-]+):\s*$", line)
        if m:
            base = m.group(1).split("-SUB-")[0]
            ids.add(base)
    return ids


def parse_req_mapping_files_with_status(path: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    text = read_text(path)
    if not text:
        return files
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|\n").split("|")]
        if len(cells) < 4 or cells[0] == "要件ID":
            continue
        specfile = cells[2]
        status = cells[3]
        m = re.search(r"(SPEC-[A-Za-z0-9-]+[^|\s]*?\.(?:md|MD|yaml|yml))", specfile)
        if m:
            files[m.group(1)] = status
    return files


def find_by_basename(basename: str) -> Path | None:
    # search within ROOT excluding archives/meta/scripts
    for p in find_all_spec_files():
        if p.name == basename:
            return p.relative_to(ROOT)
    return None


def map_spec_ids_to_files(spec_ids: set[str]) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    candidates = find_all_spec_files()
    for sid in spec_ids:
        chosen = None
        for p in candidates:
            if p.name.startswith(sid):
                chosen = p.relative_to(ROOT)
                break
        if chosen:
            mapping[sid] = chosen
    return mapping


def category_from_spec_id(spec_id: str) -> str:
    m = re.match(r"SPEC-([A-Z0-9]+)-", spec_id)
    raw = m.group(1) if m else "UNKNOWN"
    return CATEGORY_NORMALIZATION.get(raw, raw)


def number_from_spec_id(spec_id: str) -> str:
    m = re.match(r"SPEC-[A-Z0-9]+-([0-9]{3})", spec_id)
    return m.group(1) if m else "—"


def extract_spec_id_from_filename(name: str) -> str | None:
    m = re.match(r"(SPEC-[A-Z0-9]+-[0-9]{3}(?:-[A-Z0-9]+)?)", name)
    return m.group(1) if m else None


def load_current_sets() -> tuple[dict[str, Path], set[Path]]:
    mapping_file = ROOT / "E2E_TEST_MAPPING.yaml"
    e2e_ids = parse_e2e_mapping_ids(mapping_file)
    int_ids = parse_integration_mapping_ids(mapping_file)
    all_mapped_ids = e2e_ids | int_ids
    req_map = parse_req_mapping_files_with_status(ROOT / "REQ_SPEC_MAPPING_MATRIX.md")

    id_to_file = map_spec_ids_to_files(all_mapped_ids)

    files_from_req: set[Path] = set()
    for bn, status in req_map.items():
        # Only include REQ rows that are implemented
        if "実装済" not in status:
            continue
        p = find_by_basename(bn)
        if p:
            files_from_req.add(p)

    current_files: set[Path] = set(id_to_file.values()) | files_from_req
    return id_to_file, current_files


def compute_all_and_non_current(current_files: set[Path]) -> tuple[set[Path], set[Path]]:
    all_files = set([p.relative_to(ROOT) for p in find_all_spec_files()])
    non_current = all_files - current_files
    return all_files, non_current


def ensure_dirs():
    (ROOT / "_meta").mkdir(parents=True, exist_ok=True)


def write_registry(id_to_file: dict[str, Path], current_files: set[Path], sources: dict[str, set[str]]):
    # registry is a YAML-like (but we write JSON for simplicity to avoid yaml dependency)
    data = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(ROOT),
        "entries": [],
    }
    for sid, rel in sorted(id_to_file.items()):
        entry = {
            "spec_id": sid,
            "file": str(rel),
            "category": category_from_spec_id(sid),
            "number": number_from_spec_id(sid),
            "status": "canonical",
            "sources": sorted(list(sources.get(sid, set()))),
        }
        data["entries"].append(entry)

    # also include files only from REQ (no explicit spec_id mapping)
    # infer spec_id from filename
    for rel in sorted(current_files):
        sid = extract_spec_id_from_filename(Path(rel).name)
        if sid and sid not in {e["spec_id"] for e in data["entries"]}:
            data["entries"].append({
                "spec_id": sid,
                "file": str(rel),
                "category": category_from_spec_id(sid),
                "number": number_from_spec_id(sid),
                "status": "canonical",
                "sources": sorted(list(sources.get(sid, set()) or {"REQ"})),
            })

    (ROOT / "_meta" / "_registry.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_readme(current_files: set[Path]) -> str:
    # group by category
    by_cat: dict[str, list[Path]] = {}
    for rel in sorted(current_files):
        sid = extract_spec_id_from_filename(rel.name) or rel.stem
        cat = category_from_spec_id(sid) if sid.startswith("SPEC-") else "OTHER"
        by_cat.setdefault(cat, []).append(rel)

    lines = []
    lines.append("# specs index")
    lines.append("")
    lines.append("このフォルダは仕様書をカテゴリ別に一覧化したものです。現用（ISSUE/稼働コンポーネント紐付け）のみを掲載しています。")
    lines.append("")
    lines.append("運用ポリシー:")
    lines.append("- 現用判定は E2E/REQ マッピングを一次ソースとする")
    lines.append("- 旧版は `specs/_archive/` に退避")
    lines.append("- 追加時は `SPEC-<CATEGORY>-<NNN>_<slug>.md` を推奨")
    lines.append("")
    for cat in sorted(by_cat.keys()):
        lines.append(f"## {cat}")
        lines.append("")
        for rel in by_cat[cat]:
            sid = extract_spec_id_from_filename(rel.name) or rel.stem
            num = number_from_spec_id(sid)
            lines.append(f"- [{rel.stem}](./{rel.as_posix()})  ({cat}-{num})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def generate_counters(current_files: set[Path]) -> dict:
    counters: dict[str, int] = {}
    for rel in current_files:
        sid = extract_spec_id_from_filename(rel.name) or rel.stem
        cat = category_from_spec_id(sid) if sid.startswith("SPEC-") else "OTHER"
        counters[cat] = counters.get(cat, 0) + 1
    return counters


def generate_consolidation_plan(non_current: set[Path]) -> str:
    lines = []
    lines.append("# specs consolidation plan")
    lines.append("")
    lines.append("以下は現用外（ISSUE/稼働コンポーネント非紐付け）の候補です。`_archive/<timestamp>/` に退避予定です。")
    lines.append("")
    if not non_current:
        lines.append("現用外はありません。重複は検出されませんでした。")
    else:
        lines.append(f"退避候補数: {len(non_current)} 件")
        lines.append("")
        for rel in sorted(non_current):
            lines.append(f"- {rel.as_posix()}")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_sources_index() -> dict[str, set[str]]:
    sources: dict[str, set[str]] = {}
    # E2E
    e2e_ids = parse_e2e_mapping_ids(ROOT / "E2E_TEST_MAPPING.yaml")
    for sid in e2e_ids:
        sources.setdefault(sid, set()).add("E2E")
    # REQ
    req_map = parse_req_mapping_files_with_status(ROOT / "REQ_SPEC_MAPPING_MATRIX.md")
    for bn, status in req_map.items():
        if "実装済" not in status:
            continue
        sid = extract_spec_id_from_filename(bn)
        if sid:
            sources.setdefault(sid, set()).add("REQ")
    return sources


def archive_non_current(non_current: set[Path]) -> str | None:
    if not non_current:
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest_root = ROOT / "_archive" / stamp
    dest_root.mkdir(parents=True, exist_ok=True)
    for rel in sorted(non_current):
        src = ROOT / rel
        dst = dest_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    return dest_root.as_posix()


def main(argv: list[str]) -> int:
    dry_run = "--dry-run" in argv
    apply = "--apply" in argv
    ensure_dirs()

    id_to_file, current_files = load_current_sets()
    all_files, non_current = compute_all_and_non_current(current_files)

    sources = build_sources_index()
    # Write registry snapshot
    write_registry(id_to_file, current_files, sources)

    # Prepare generated artifacts
    readme_text = generate_readme(current_files)
    counters = generate_counters(current_files)
    plan_text = generate_consolidation_plan(non_current)

    # Always write previews to _meta
    (ROOT / "_meta" / "README.generated.md").write_text(readme_text, encoding="utf-8")
    (ROOT / "_meta" / "COUNTERS.generated.json").write_text(json.dumps(counters, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "_meta" / "PLAN.generated.md").write_text(plan_text, encoding="utf-8")

    # Console summary
    print("[SUMMARY]")
    print(f"  Current files: {len(current_files)}")
    print(f"  All spec files: {len(all_files)}")
    print(f"  Non-current candidates: {len(non_current)}")
    print("")
    print("[CURRENT - sample]")
    for i, rel in enumerate(sorted(current_files)):
        if i >= 20:
            break
        print(f"  - {rel}")
    if len(current_files) > 20:
        print(f"  ... and {len(current_files) - 20} more")
    print("")
    print("[NON-CURRENT - sample]")
    for i, rel in enumerate(sorted(non_current)):
        if i >= 20:
            break
        print(f"  - {rel}")
    if len(non_current) > 20:
        print(f"  ... and {len(non_current) - 20} more")
    print("")
    print("[GENERATED PREVIEWS]")
    print("  - _meta/README.generated.md")
    print("  - _meta/COUNTERS.generated.json")
    print("  - _meta/PLAN.generated.md")

    if dry_run and not apply:
        print("\n[DRY-RUN] No changes applied.")
        return 0

    if apply:
        # Apply README + counters + plan
        (ROOT / "README.md").write_text(readme_text, encoding="utf-8")
        (ROOT / ".spec_counters.json").write_text(json.dumps(counters, ensure_ascii=False, indent=2), encoding="utf-8")
        (ROOT / "CONSOLIDATION_PLAN.md").write_text(plan_text, encoding="utf-8")
        # Archive
        archive_path = archive_non_current(non_current)
        if archive_path:
            print(f"[APPLY] Archived non-current files to: {archive_path}")
        print("[APPLY] README.md and .spec_counters.json updated.")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
