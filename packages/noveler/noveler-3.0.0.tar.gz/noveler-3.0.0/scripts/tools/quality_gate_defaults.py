#!/usr/bin/env python3
# File: scripts/tools/quality_gate_defaults.py
# Purpose: Expose quality gate default settings (Gate B/C) to CLI wrappers and tooling.
# Context: Reads config/quality/gate_defaults.yaml and emits values as JSON or shell exports.
"""Quality gate defaults helper."""
from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "quality" / "gate_defaults.yaml"


def load_defaults() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise SystemExit(f"Config not found: {CONFIG_PATH}")
    with CONFIG_PATH.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data


def flatten_for_shell(data: dict[str, Any]) -> dict[str, str]:
    gate_defaults = data.get("gate_defaults", {})
    outputs = gate_defaults.get("outputs", {})
    thresholds = gate_defaults.get("thresholds", {})
    gate_b = thresholds.get("gate_b", {})
    episodes = gate_defaults.get("episodes", {})
    editorial = gate_defaults.get("editorial_checklist", {})

    return {
        "CORE_REPORT": str(outputs.get("core_report", "reports/quality.ndjson")),
        "EDITORIAL_CHECKLIST_REPORT": str(outputs.get("editorial_checklist_report", "reports/editorial_checklist.md")),
        "SEVERITY_THRESHOLD": str(thresholds.get("severity", "medium")),
        "GATE_B_RHYTHM": str(gate_b.get("rhythm", 80)),
        "GATE_B_READABILITY": str(gate_b.get("readability", 80)),
        "GATE_B_GRAMMAR": str(gate_b.get("grammar", 90)),
        "EPISODE_DEFAULT": str(episodes.get("default", 1)),
        "EDITORIAL_CHECKLIST_REQUIRE_ALL_PASS": str(editorial.get("require_all_pass", True)).lower(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit quality gate defaults")
    parser.add_argument("--format", choices=["json", "shell"], default="json")
    parser.add_argument("--key", type=str, default=None, help="Optional dotted key to extract from JSON output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = load_defaults()

    if args.key:
        # basic dotted-path extraction
        value: Any = data
        for part in args.key.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                raise SystemExit(f"Key '{args.key}' not found in gate defaults")
        print(json.dumps(value, ensure_ascii=False))
        return

    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        for key, value in flatten_for_shell(data).items():
            print(f"{key}={shlex.quote(value)}")


if __name__ == "__main__":
    main()
