"""Specs.scripts.specs_front_matter
Where: Specs automation script managing front matter metadata.
What: Updates specification front matter with consistent metadata values.
Why: Keeps specification documents aligned with documentation standards.
"""

#!/usr/bin/env python3
import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # specs/


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def write_text(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


def parse_e2e_mapping_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    text = read_text(path)
    if not text:
        return ids
    lines = text.splitlines()
    in_e2e = False
    for line in lines:
        if line.strip().startswith('#'):
            continue
        if not in_e2e:
            if re.match(r"^e2e_mappings:\s*$", line):
                in_e2e = True
            continue
        if re.match(r"^[A-Za-z_]+:\s*$", line):
            break
        m = re.match(r"^\s{2,}(SPEC-[A-Z0-9-]+):\s*$", line)
        if m:
            ids.add(m.group(1).split("-SUB-")[0])
    return ids


def parse_req_mapping_files(path: Path) -> set[str]:
    files: set[str] = set()
    text = read_text(path)
    if not text:
        return files
    for line in text.splitlines():
        if not line.strip().startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|\n').split('|')]
        if len(cells) < 4 or cells[0] == '要件ID':
            continue
        status = cells[3]
        if '実装済' not in status:
            continue
        m = re.search(r"(SPEC-[A-Za-z0-9-]+[^|\s]*?\.(?:md|MD|yaml|yml))", cells[2])
        if m:
            files.add(m.group(1))
    return files


def find_all_spec_files() -> list[Path]:
    spec_files = []
    exclude_dirs = {"_archive", "archive", "_meta", "_scripts"}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        rel = Path(dirpath).relative_to(ROOT)
        parts = set(rel.parts)
        if parts & exclude_dirs:
            continue
        for fn in filenames:
            if not fn.startswith("SPEC-"):
                continue
            if fn.lower().endswith((".md", ".yaml", ".yml")):
                spec_files.append(Path(dirpath) / fn)
    return spec_files


def find_by_basename(basename: str) -> Path | None:
    for p in find_all_spec_files():
        if p.name == basename:
            return p.relative_to(ROOT)
    return None


def extract_spec_id_from_filename(name: str) -> str | None:
    m = re.match(r"(SPEC-[A-Z0-9]+-[0-9]{3}(?:-[A-Z0-9]+)?)", name)
    return m.group(1) if m else None


def normalized_category_from_spec_id(spec_id: str) -> str:
    m = re.match(r"SPEC-([A-Z0-9]+)-", spec_id)
    raw = m.group(1) if m else "UNKNOWN"
    mapping = {"A31": "QUALITY", "A28": "PLOT", "A30": "WRITE", "A38": "WRITE"}
    return mapping.get(raw, raw)


def tags_for_spec_id(spec_id: str, stem: str) -> list[str]:
    tags: list[str] = []
    cat = normalized_category_from_spec_id(spec_id)
    if cat:
        tags.append(cat.lower())
    if spec_id.startswith("SPEC-A31-"):
        tags.extend(["a31", "quality", "checklist", "auto-evaluation"])
        lower = stem.lower()
        if "proofread" in lower:
            tags.append("proofread")
        if "terminology" in lower:
            tags.append("terminology")
    if spec_id.startswith("SPEC-A28-"):
        tags.extend(["a28", "plot", "generation", "episode"])
    if spec_id.startswith("SPEC-A30-"):
        tags.extend(["a30", "write", "stepwise", "guide", "workflow"])
    if spec_id.startswith("SPEC-A38-"):
        tags.extend(["a38", "write", "emotion", "prompt"])
    # de-duplicate and stable sort
    return sorted(set(tags))


def load_current_files() -> set[Path]:
    # Prefer registry if exists
    reg = ROOT / "_meta" / "_registry.json"
    current: set[Path] = set()
    if reg.exists():
        try:
            data = json.loads(read_text(reg))
            for e in data.get("entries", []):
                if e.get("status") == "canonical" and e.get("file"):
                    current.add(Path(e["file"]))
        except Exception:
            pass
    if current:
        return current
    # Fallback to recompute
    e2e_ids = parse_e2e_mapping_ids(ROOT / "E2E_TEST_MAPPING.yaml")
    req_files = parse_req_mapping_files(ROOT / "REQ_SPEC_MAPPING_MATRIX.md")
    # Map IDs to files by prefix match
    candidates = find_all_spec_files()
    for sid in e2e_ids:
        for p in candidates:
            if p.name.startswith(sid):
                current.add(p.relative_to(ROOT))
                break
    for bn in req_files:
        p = find_by_basename(bn)
        if p:
            current.add(p)
    return current


def load_sources_by_spec_id() -> dict[str, list[str]]:
    """Load sources (E2E/REQ) from registry if present."""
    reg = ROOT / "_meta" / "_registry.json"
    sources_map: dict[str, list[str]] = {}
    if reg.exists():
        try:
            data = json.loads(read_text(reg))
            for e in data.get("entries", []):
                sid = e.get("spec_id")
                srcs = e.get("sources") or []
                if sid:
                    sources_map[sid] = srcs
        except Exception:
            pass
    return sources_map


def parse_front_matter(content: str) -> tuple[dict, int, int]:
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end != -1:
            fm_text = content[4:end]
            fm = {}
            for line in fm_text.splitlines():
                m = re.match(r"([^:]+):\s*(.*)\s*$", line)
                if m:
                    key = m.group(1).strip()
                    val = m.group(2).strip()
                    if val.startswith("[") and val.endswith("]"):
                        # naive list support
                        items = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
                        fm[key] = items
                    else:
                        fm[key] = val.strip("'\"")
            return fm, 0, end + len("\n---\n")
    return {}, -1, -1


def build_front_matter(spec_id: str, existing: dict, stem: str = "") -> str:
    today = datetime.now().date().isoformat()
    owner = existing.get("owner") or "bamboocity"
    sources = existing.get("sources") or []
    if isinstance(sources, str):
        sources = [sources]
    # ensure uniqueness and stable order
    sources = sorted(set(sources))
    category = existing.get("category") or normalized_category_from_spec_id(spec_id)
    tags = existing.get("tags")
    if not tags:
        tags = tags_for_spec_id(spec_id, stem)
    if isinstance(tags, str):
        tags = [tags]
    tags = sorted(set(tags))
    lines = [
        "---",
        f"spec_id: {spec_id}",
        f"status: canonical",
        f"owner: {owner}",
        f"last_reviewed: {today}",
    ]
    if category:
        lines.append(f"category: {category}")
    if sources:
        lines.append("sources: [" + ", ".join(sources) + "]")
    if tags:
        lines.append("tags: [" + ", ".join(tags) + "]")
    lines.append("---")
    return "\n".join(lines) + "\n"


def inject_or_update(path: Path, reg_sources: dict[str, list[str]]) -> tuple[str, str]:
    content = read_text(ROOT / path)
    spec_id = extract_spec_id_from_filename(path.name) or ""
    if not spec_id:
        return ("skip", "missing spec_id")
    fm, start, end = parse_front_matter(content)
    existing = dict(fm)
    # merge sources from registry
    if spec_id in reg_sources:
        rs = reg_sources.get(spec_id) or []
        cur = existing.get("sources") or []
        if isinstance(cur, str):
            cur = [cur]
        merged = sorted(set(list(cur) + list(rs)))
        existing["sources"] = merged
    # preserve existing sources/owner if any
    fm_text = build_front_matter(spec_id, existing, stem=Path(path).stem)
    if start == -1:
        new_content = fm_text + content
        write_text(ROOT / path, new_content)
        return ("added", "no front-matter -> added")
    else:
        # replace existing fm block
        new_content = fm_text + content[end:]
        write_text(ROOT / path, new_content)
        return ("updated", "front-matter replaced")


def main(argv: list[str]) -> int:
    dry_run = "--dry-run" in argv
    apply = "--apply" in argv
    current = [p for p in sorted(load_current_files()) if str(p).lower().endswith(".md")]
    reg_sources = load_sources_by_spec_id()
    print(f"[TARGET] current markdown specs: {len(current)}")
    changes = []
    for rel in current:
        content = read_text(ROOT / rel)
        fm, start, end = parse_front_matter(content)
        state = "missing" if start == -1 else "exists"
        changes.append((rel, state))
    print("[DRY-RUN LIST]")
    for rel, state in changes:
        print(f"  - {rel}: {state}")
    if dry_run and not apply:
        print("[DRY-RUN] No changes applied.")
        return 0
    if apply:
        added = updated = 0
        for rel, _ in changes:
            action, _msg = inject_or_update(rel, reg_sources)
            if action == "added":
                added += 1
            elif action == "updated":
                updated += 1
        print(f"[APPLY] front-matter added: {added}, updated: {updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
