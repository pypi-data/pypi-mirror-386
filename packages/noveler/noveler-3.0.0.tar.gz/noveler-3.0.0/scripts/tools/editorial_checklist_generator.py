#!/usr/bin/env python3
# File: scripts/tools/editorial_checklist_generator.py
# Purpose: Generate a templated editorial 12-step checklist and optionally write a report.
# Context: Tier-2 manual review (non-destructive). Dependency-free; emits markdown
#          based on docs/editorial_12_step_checklist.md and user-provided metadata.
"""
Former name: `scripts/tools/l12_suite_check.py` (kept for backward compatibility).

Usage examples:
  - python scripts/tools/editorial_checklist_generator.py --work "Example Novel" \
        --episode 1 --out reports/editorial_checklist.md
  - python scripts/tools/editorial_checklist_generator.py --dry-run

Exit codes:
  0: success
  2: execution error
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys
from typing import Any
import json

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[2]
GATE_DEFAULTS_PATH = ROOT / "config" / "quality" / "gate_defaults.yaml"


EDITORIAL_CHECKLIST_ITEMS = [
    ("L12-01", "Point of View Consistency"),
    ("L12-02", "Scene GCD (Goal–Conflict–Decision)"),
    ("L12-03", "Character Voice Separation"),
    ("L12-04", "Foreshadowing & Payoff"),
    ("L12-05", "Redundancy & Over-Explanation"),
    ("L12-06", "Information Flow & Clarity"),
    ("L12-07", "Pacing & Scene Rhythm"),
    ("L12-08", "Emotional Arc Coherence"),
    ("L12-09", "Worldbuilding Continuity"),
    ("L12-10", "Show/Tell Balance"),
    ("L12-11", "Stakes & Motivation Visibility"),
    ("L12-12", "Line-Level Polish Focus Map"),
]


def load_require_all_pass() -> bool | None:
    if not GATE_DEFAULTS_PATH.exists():
        return None
    try:
        if yaml is not None:
            data: Any = yaml.safe_load(GATE_DEFAULTS_PATH.read_text(encoding="utf-8")) or {}
        else:
            import json

            data = json.loads(GATE_DEFAULTS_PATH.read_text(encoding="utf-8"))
        editorial_cfg = (data.get("gate_defaults") or {}).get("editorial_checklist")
        if isinstance(editorial_cfg, dict):
            value = editorial_cfg.get("require_all_pass")
            if isinstance(value, bool):
                return value
        return None
    except Exception:
        return None


def build_checklist(work: str | None, episode: int | None, require_all_pass: bool | None) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = [
        "# Editorial 12-Step Checklist",
        f"- Generated: {ts}",
        f"- Work: {work or '-'}",
        f"- Episode: {episode or '-'}",
        "",
    ]
    if require_all_pass is None:
        header.append("Outcome: Mark each item with PASS / NOTE / TODO. Add locations and short evidence.")
    elif require_all_pass:
        header.append("Outcome: Gate C expects PASS on all items (record exceptions with justification).")
    else:
        header.append("Outcome: Gate C allows documented exceptions; mark PASS / NOTE / TODO per item.")
    header.append("")
    lines = header[:]
    for _id, title in EDITORIAL_CHECKLIST_ITEMS:
        lines.append(f"## {_id} — {title}")
        lines.append("- Status: PASS | NOTE | TODO")
        lines.append("- Locations: <file:line or scene ids>")
        lines.append("- Evidence: <short quote or rationale>")
        lines.append("- Suggestion: <rewrite/pacing/merge/split/etc>")
        lines.append("")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Emit editorial 12-step checklist")
    p.add_argument("--work", type=str, default=None)
    p.add_argument("--episode", type=int, default=None)
    p.add_argument("--out", type=str, default=None, help="Where to write the checklist (markdown)")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout only and exit 0")
    return p.parse_args()


def main() -> int:
    try:
        args = parse_args()
        require_all_pass = load_require_all_pass()
        content = build_checklist(args.work, args.episode, require_all_pass)
        if args.dry_run or not args.out:
            sys.stdout.write(content)
            return 0
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print(str(out_path))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
