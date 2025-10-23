#!/usr/bin/env python3
# File: tests/unit/scripts/test_check_runners_minimal.py
# Purpose: Smoke tests for the quality check wrappers and verify CLI defaults.
# Context: Avoids heavy MCP flows by monkeypatching tool execution.

from __future__ import annotations

import importlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = "scripts.ci.run_quality_checks_ndjson"


class _StubResponse:
    def __init__(self, metadata: dict[str, Any]) -> None:
        self.success = True
        self.score = 95.0
        self.metadata = metadata


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def test_check_core_dry_run_exits_zero_and_mentions_script():
    p = run(["bash", "bin/check-core", "--dry-run"])  # invoke via bash to avoid exec bit dependency
    assert p.returncode == 0, p.stderr
    assert "run_quality_checks_ndjson.py" in p.stdout


def test_check_editorial_checklist_dry_run_exits_zero_and_mentions_generator():
    p = run(["bash", "bin/check-editorial-checklist", "--dry-run", "--work", "Sample", "--episode", "1"])  # explicit args okay
    assert p.returncode == 0, p.stderr
    assert "editorial_checklist_generator.py" in p.stdout


def test_check_all_dry_run_shows_composite_commands():
    p = run(["bash", "bin/check-all", "--dry-run", "--work", "Sample", "--episode", "2"])
    assert p.returncode == 0, p.stderr
    assert "bin/check-core" in p.stdout
    assert "bin/check-editorial-checklist" in p.stdout


def test_run_quality_checks_cli_writes_output(monkeypatch, tmp_path):
    monkeypatch.setenv("NOVEL_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("LLM_REPORT_DIR", str(tmp_path / "reports"))

    module = importlib.import_module(MODULE_PATH)
    module = importlib.reload(module)

    class _StubTool:
        def execute(self, request: ToolRequest):
            metadata = {
                "ndjson": json.dumps({"type": "summary"}, ensure_ascii=False) + "\n",
                "gate_b_pass": True,
                "gate_b_should_fail": False,
                "should_fail": False,
            }
            return _StubResponse(metadata)

    monkeypatch.setattr(module, "RunQualityChecksTool", _StubTool)

    out_path = tmp_path / "quality.ndjson"
    monkeypatch.setattr(
        module,
        "parse_args",
        lambda: SimpleNamespace(
            file_path=None,
            episode=None,
            project_root=None,
            project_name=None,
            aspects=None,
            severity_threshold=None,
            reason_codes=None,
            types=None,
            text_contains=None,
            limit=None,
            sort_by=None,
            sort_order="asc",
            fail_on_score_below=None,
            fail_on_severity_at_least=None,
            fail_on_reason_codes=None,
            fail_on_max_issue_count=None,
            out=str(out_path),
            fail_on_path_fallback=False,
        ),
    )

    exit_code = module.main()
    assert exit_code == 0
    assert out_path.exists()
    assert out_path.read_text(encoding="utf-8").strip() != ""


def test_run_quality_checks_cli_returns_failure_on_gate(monkeypatch, tmp_path):
    monkeypatch.setenv("NOVEL_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("LLM_REPORT_DIR", str(tmp_path / "reports"))

    module = importlib.import_module(MODULE_PATH)
    module = importlib.reload(module)

    class _StubToolFail:
        def execute(self, request: ToolRequest):
            metadata = {
                "ndjson": json.dumps({"type": "summary"}, ensure_ascii=False) + "\n",
                "gate_b_pass": False,
                "gate_b_should_fail": True,
                "should_fail": False,
            }
            return _StubResponse(metadata)

    monkeypatch.setattr(module, "RunQualityChecksTool", _StubToolFail)
    out_path = tmp_path / "quality.ndjson"
    monkeypatch.setattr(
        module,
        "parse_args",
        lambda: SimpleNamespace(
            file_path=None,
            episode=None,
            project_root=None,
            project_name=None,
            aspects=None,
            severity_threshold=None,
            reason_codes=None,
            types=None,
            text_contains=None,
            limit=None,
            sort_by=None,
            sort_order="asc",
            fail_on_score_below=None,
            fail_on_severity_at_least=None,
            fail_on_reason_codes=None,
            fail_on_max_issue_count=None,
            out=str(out_path),
            fail_on_path_fallback=False,
        ),
    )

    exit_code = module.main()
    assert exit_code == 2
    assert out_path.exists()
    assert out_path.read_text(encoding="utf-8").strip() != ""
