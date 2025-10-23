#!/usr/bin/env python3
# File: tests/unit/tools/test_runner_json_only.py
# Purpose: Verify that the unified test runner supports --json-only and emits
#          a single JSON object to stdout while preserving exit code semantics.
# Context: Keeps the assertion minimal (JSON parseable), not relying on the
#          specific schema which is owned by the reporting hooks.

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def test_runner_json_only_emits_one_json_object(tmp_path: Path) -> None:
    """Run a trivial test via --json-only and ensure stdout is JSON."""

    env = dict(os.environ)
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("LLM_SILENT_PROGRESS", "1")
    env.setdefault("NOVELER_TEST_CLEANUP_MODE", "fast")

    # Use a very small existing test to keep this quick
    target = "tests/meta/test_llm_report_option.py::test_llm_report_option_is_available"

    cp = subprocess.run(
        ["python3", "scripts/run_pytest.py", "--json-only", "-q", target],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[3],  # repo root
        env=env,
        timeout=240,
    )

    # Exit code should reflect pytest outcome (expect success)
    assert cp.returncode == 0, cp.stderr

    # stdout should contain a single JSON object (one line acceptable)
    out = (cp.stdout or "").strip()
    assert out.startswith("{") and out.endswith("}"), out
    # Must be parseable JSON
    _ = json.loads(out)


def test_runner_emits_log_manifest(tmp_path: Path) -> None:
    """Ensure log attachments are recorded alongside LLM reports."""

    repo_root = Path(__file__).resolve().parents[3]
    reports_dir = tmp_path / "reports"

    env = dict(os.environ)
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("LLM_SILENT_PROGRESS", "1")
    env.setdefault("NOVELER_TEST_CLEANUP_MODE", "fast")
    env["LLM_REPORT_DIR"] = str(reports_dir)
    env["LLM_ATTACH_LOGS"] = "1"

    target = "tests/meta/test_llm_report_option.py::test_llm_report_option_is_available"

    cp = subprocess.run(
        ["python3", "scripts/run_pytest.py", "-q", target],
        capture_output=True,
        text=True,
        cwd=repo_root,
        env=env,
        timeout=240,
    )

    assert cp.returncode == 0, cp.stderr

    manifest_path = reports_dir / "llm_summary.attachments.jsonl"
    assert manifest_path.exists()

    records = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert records, "manifest should contain at least one attachment record"

    record = records[-1]
    assert record.get("kind") == "pytest-log"

    attachment_path = Path(record.get("path", ""))
    if not attachment_path.is_absolute():
        attachment_path = reports_dir / attachment_path

    assert attachment_path.exists(), f"log file missing: {attachment_path}"
