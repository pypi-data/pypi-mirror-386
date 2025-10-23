#!/usr/bin/env python3
# File: tests/unit/scripts/test_editorial_checklist_evaluator.py
# Purpose: Validate the editorial checklist evaluator script for Gate C decisions.
# Context: Ensures PASS/NOTE/TODO parsing and require_all_pass logic behave as expected.

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "tools" / "editorial_checklist_evaluator.py"


def run(args):
    return subprocess.run([
        sys.executable,
        str(SCRIPT),
        *args,
    ], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def write_checklist(tmp_path: Path, statuses):
    lines = [
        "# Editorial 12-Step Checklist",
        "",
    ]
    for idx, status in enumerate(statuses, start=1):
        code = f"L12-{idx:02d}"
        lines.append(f"## {code} — Dummy")
        lines.append(f"- Status: {status}")
        lines.append("")
    path = tmp_path / "editorial_checklist.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_evaluator_pass(tmp_path):
    checklist = write_checklist(tmp_path, ["PASS"] * 3)
    result = run(["--file", str(checklist), "--format", "json", "--require-all-pass", "true"])
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["pass"] is True
    assert payload["counts"]["PASS"] == 3


def test_evaluator_fail_with_note(tmp_path):
    checklist = write_checklist(tmp_path, ["PASS", "NOTE", "PASS"])
    result = run(["--file", str(checklist), "--format", "json", "--require-all-pass", "true"])
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["pass"] is False
    assert payload["counts"]["NOTE"] == 1


def test_evaluator_allows_note_when_config_false(tmp_path):
    checklist = write_checklist(tmp_path, ["PASS", "NOTE"])
    result = run(["--file", str(checklist), "--format", "json", "--require-all-pass", "false"])
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["pass"] is True
