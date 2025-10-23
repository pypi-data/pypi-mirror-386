#!/usr/bin/env python3
# File: scripts/tools/editorial_checklist_evaluator.py
# Purpose: Evaluate an editorial 12-step checklist Markdown file and report Gate C status.
# Context: Parses checklist items (formerly L12) and summarizes PASS/NOTE/TODO outcomes.
"""Evaluate editorial 12-step checklist results and emit Gate C summary."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[2]
GATE_DEFAULTS_PATH = ROOT / "config" / "quality" / "gate_defaults.yaml"
STATUS_PATTERN = re.compile(r"^[-*]\s*Status:\s*([A-Za-z]+)")
ITEM_PATTERN = re.compile(r"^##\s+(L12-\d{2})\s+—\s+(.*)")


def load_require_all_pass() -> bool:
    if not GATE_DEFAULTS_PATH.exists():
        return True
    try:
        if yaml is not None:
            data = yaml.safe_load(GATE_DEFAULTS_PATH.read_text(encoding="utf-8")) or {}
        else:
            data = json.loads(GATE_DEFAULTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return True
    editorial_cfg = (
        data.get("gate_defaults", {})
        .get("editorial_checklist", {})
    )
    value = editorial_cfg.get("require_all_pass")
    return bool(value) if isinstance(value, bool) else True


def parse_checklist(path: Path) -> List[Tuple[str, str, str]]:
    current_item: Tuple[str, str] | None = None
    results: List[Tuple[str, str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        item_match = ITEM_PATTERN.match(line)
        if item_match:
            current_item = (item_match.group(1), item_match.group(2))
            continue
        status_match = STATUS_PATTERN.match(line)
        if status_match and current_item:
            status = status_match.group(1).upper()
            results.append((current_item[0], current_item[1], status))
            current_item = None
    return results


def evaluate(results: List[Tuple[str, str, str]], require_all_pass: bool) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "total_items": len(results),
        "items": [],
        "counts": {"PASS": 0, "NOTE": 0, "TODO": 0, "UNKNOWN": 0},
        "require_all_pass": require_all_pass,
        "pass": True,
    }
    for code, title, status in results:
        normalized = status.upper()
        if normalized not in summary["counts"]:
            normalized = "UNKNOWN"
        summary["counts"][normalized] += 1
        summary["items"].append({
            "id": code,
            "title": title,
            "status": normalized,
        })
    if require_all_pass:
        summary["pass"] = summary["counts"]["NOTE"] == 0 and summary["counts"]["TODO"] == 0 and summary["counts"]["UNKNOWN"] == 0
    else:
        summary["pass"] = summary["counts"]["TODO"] == 0 and summary["counts"]["UNKNOWN"] == 0
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate editorial 12-step checklist")
    parser.add_argument("--file", type=str, default="reports/editorial_checklist.md", help="Checklist markdown file")
    parser.add_argument("--format", choices=["json", "text"], default="text")
    parser.add_argument("--require-all-pass", type=str, default=None, help="Override Gate C requirement (true/false)")
    return parser.parse_args()


def parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in {"true", "1", "yes", "on"}:
        return True
    if lowered in {"false", "0", "no", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def main() -> int:
    args = parse_args()
    checklist_path = Path(args.file)
    if not checklist_path.exists():
        print(f"Checklist not found: {checklist_path}")
        return 3
    try:
        require_all_pass = parse_bool(args.require_all_pass)
    except ValueError as exc:
        print(str(exc))
        return 3
    if require_all_pass is None:
        require_all_pass = load_require_all_pass()
    results = parse_checklist(checklist_path)
    summary = evaluate(results, require_all_pass)
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("Editorial 12-step checklist summary")
        print(f"File: {checklist_path}")
        print(f"Require all pass: {summary['require_all_pass']}")
        print(f"Counts: PASS={summary['counts']['PASS']} NOTE={summary['counts']['NOTE']} TODO={summary['counts']['TODO']} UNKNOWN={summary['counts']['UNKNOWN']}")
        if summary['items']:
            print("Items:")
            for item in summary['items']:
                print(f"  - {item['id']} ({item['title']}): {item['status']}")
        print(f"Gate C PASS: {summary['pass']}")
    return 0 if summary['pass'] else 2


if __name__ == "__main__":
    raise SystemExit(main())
