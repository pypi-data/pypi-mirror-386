"""Specs.scripts.specs_build_search_index
Where: Specs automation script building the search index.
What: Processes specification documents and creates a searchable index.
Why: Improves discoverability of specification content.
"""

#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def parse_front_matter_and_body(text: str):
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            fm_text = text[4:end]
            fm = {}
            for line in fm_text.splitlines():
                m = re.match(r"([^:]+):\s*(.*)\s*$", line)
                if m:
                    key = m.group(1).strip()
                    val = m.group(2).strip().strip("'\"")
                    fm[key] = val
            body = text[end + len("\n---\n"):]
            return fm, body
    return {}, text


def extract_headings(md: str):
    titles = []
    for line in md.splitlines():
        if line.startswith('# '):
            titles.append(line[2:].strip())
        elif line.startswith('## '):
            titles.append(line[3:].strip())
    return titles[:12]


def load_registry_entries():
    data = json.loads(read(ROOT / "_meta/_registry.json"))
    return [e for e in data.get("entries", []) if e.get("status") == "canonical"]


def main():
    entries = load_registry_entries()
    index = []
    for e in entries:
        rel = Path(e["file"])
        p = ROOT / rel
        if not p.exists() or p.suffix.lower() != ".md":
            continue
        fm, body = parse_front_matter_and_body(read(p))
        headings = extract_headings(body)
        item = {
            "spec_id": e.get("spec_id"),
            "file": str(rel),
            "category": fm.get("category") or e.get("category"),
            "tags": fm.get("tags"),
            "sources": e.get("sources"),
            "title": headings[0] if headings else p.stem,
            "headings": headings,
            "owner": fm.get("owner"),
            "last_reviewed": fm.get("last_reviewed"),
            "preview": body.strip().replace("\n", " ")[:500],
        }
        index.append(item)
    (ROOT / "_meta/search_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[INDEX] entries: {len(index)} -> specs/_meta/search_index.json")


if __name__ == '__main__':
    main()
