"""Specs.scripts.specs_lint
Where: Specs automation script linting specification documents.
What: Runs lint checks to ensure specifications meet formatting and content rules.
Why: Maintains quality and consistency across specification files.
"""

#!/usr/bin/env python3
import sys
import re
import json
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def parse_front_matter(content: str):
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end != -1:
            fm_text = content[4:end]
            fm = {}
            for line in fm_text.splitlines():
                m = re.match(r"([^:]+):\s*(.*)\s*$", line)
                if m:
                    key = m.group(1).strip()
                    val = m.group(2).strip().strip("'\"")
                    fm[key] = val
            return fm
    return {}


def extract_spec_id_from_filename(name: str) -> str | None:
    m = re.match(r"(SPEC-[A-Z0-9]+-[0-9]{3}(?:-[A-Z0-9]+)?)", name)
    return m.group(1) if m else None


def load_current_files() -> list[Path]:
    reg = ROOT / "_meta" / "_registry.json"
    current: list[Path] = []
    if reg.exists():
        try:
            data = json.loads(read_text(reg))
            for e in data.get("entries", []):
                if e.get("status") == "canonical" and e.get("file"):
                    p = Path(e["file"])
                    if str(p).lower().endswith(".md"):
                        current.append(p)
        except Exception:
            pass
    return sorted(current)


def main(argv: list[str]) -> int:
    max_age_days = 120
    for i, a in enumerate(argv):
        if a.startswith("--max-age-days="):
            try:
                max_age_days = int(a.split("=", 1)[1])
            except Exception:
                pass
    deadline = datetime.now().date() - timedelta(days=max_age_days)

    issues = []
    for rel in load_current_files():
        p = ROOT / rel
        content = read_text(p)
        fm = parse_front_matter(content)
        expected_id = extract_spec_id_from_filename(p.name)
        if not fm:
            issues.append((str(rel), "missing-front-matter"))
            continue
        if not fm.get("spec_id"):
            issues.append((str(rel), "missing-spec_id"))
        elif expected_id and fm.get("spec_id") != expected_id:
            issues.append((str(rel), f"spec_id-mismatch:{fm.get('spec_id')} != {expected_id}"))
        if fm.get("status") != "canonical":
            issues.append((str(rel), f"status-not-canonical:{fm.get('status')}"))
        if not fm.get("owner"):
            issues.append((str(rel), "missing-owner"))
        lr = fm.get("last_reviewed")
        try:
            if lr:
                d = datetime.fromisoformat(lr).date()
                if d < deadline:
                    issues.append((str(rel), f"stale-last_reviewed:{lr}"))
            else:
                issues.append((str(rel), "missing-last_reviewed"))
        except Exception:
            issues.append((str(rel), f"invalid-last_reviewed:{lr}"))

    if issues:
        print("[LINT] FAILED: issues found:")
        for f, msg in issues:
            print(f"  - {f}: {msg}")
        return 1
    print("[LINT] OK: all current specs have canonical front-matter and fresh review date.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
