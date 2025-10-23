# File: tests/unit/presentation/mcp/test_handlers_lightweight_output.py
# Purpose: Verify lightweight MCP output formatting helpers keep responses small and consistent.
# Context: Guards presentation-layer adapters for quality tools against regressions in B20 policies.

"""tests.unit.presentation.mcp.test_handlers_lightweight_output
Where: Presentation-layer MCP handlers.
What: Verify B20 lightweight output (summary/ndjson, pagination) behaviour.
Why: Ensure opt-in shaping works without breaking defaults.
"""

from __future__ import annotations

import json
import pytest

import noveler.presentation.mcp.adapters.handlers as handlers_module
from noveler.presentation.mcp.adapters.handlers import run_quality_checks


class _DummyIssue:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


@pytest.mark.asyncio
async def test_run_quality_checks_summary_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyResponse:
        success = True
        score = 77.0
        execution_time_ms = 12.3
        metadata = {}
        issues = [_DummyIssue(
            type="readability",
            severity="medium",
            message="Long sentence",
            line_number=i + 1,
            suggestion="split",
            file_path="novel.md",
            line_hash=f"h{i:04d}",
            block_hash=f"b{i:04d}",
            reason_code="R01",
            issue_id=f"ISS{i:04d}",
        ) for i in range(300)]

    class DummyTool:
        def execute(self, request):
            return DummyResponse()

    monkeypatch.setattr(handlers_module, "RunQualityChecksTool", DummyTool)

    args = {"episode_number": 1, "format": "summary", "page": 2, "page_size": 50}
    res = await run_quality_checks(args)

    assert res["success"] is True
    assert len(res["issues"]) == 50
    # message/suggestion は省略され参照情報のみ
    assert "message" not in res["issues"][0]
    assert "issue_id" in res["issues"][0]
    meta = res.get("metadata", {})
    assert meta.get("pagination", {}).get("page") == 2
    assert meta.get("returned_issues") == 50
    assert meta.get("truncated") is True


@pytest.mark.asyncio
async def test_run_quality_checks_ndjson(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyResponse:
        success = True
        score = 70
        execution_time_ms = 5.0
        metadata = {}
        issues = [_DummyIssue(type="grammar", severity="low", line_number=i, issue_id=f"G{i:03d}", message="m", suggestion="s") for i in range(10)]

    class DummyTool:
        def execute(self, request):
            return DummyResponse()

    monkeypatch.setattr(handlers_module, "RunQualityChecksTool", DummyTool)

    args = {"episode_number": 1, "format": "ndjson", "page_size": 10}
    res = await run_quality_checks(args)

    # issues は空、ndjson は 10 行
    assert res["issues"] == []
    nd = res.get("metadata", {}).get("ndjson", "")
    assert nd.count("\n") == 9  # 10 lines
    # 各行は JSON として読み出せる
    for line in nd.splitlines():
        obj = json.loads(line)
        assert "issue_id" in obj or "line_number" in obj


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("func_name", "tool_attr"),
    [
        ("check_readability", "CheckReadabilityTool"),
        ("check_grammar", "CheckGrammarTool"),
        ("check_style", "CheckStyleTool"),
        ("polish_manuscript", "PolishManuscriptTool"),
        ("polish", "PolishTool"),
        ("check_rhythm", "CheckRhythmTool"),
    ],
)
async def test_summary_format_applies_to_additional_quality_tools(
    func_name: str,
    tool_attr: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class DummyResponse:
        success = True
        score = 88.0
        execution_time_ms = 4.2
        metadata = {}
        issues = [
            _DummyIssue(
                type="quality",
                severity="high",
                message=f"issue-{i}",
                line_number=i + 1,
                suggestion="refine",
                issue_id=f"Q{i:03d}",
                block_hash=f"blk{i:03d}",
            )
            for i in range(5)
        ]

    class DummyTool:
        def execute(self, request):
            return DummyResponse()

    monkeypatch.setattr(handlers_module, tool_attr, DummyTool)

    handler = getattr(handlers_module, func_name)
    args = {"episode_number": 1, "format": "summary", "page_size": 2}
    res = await handler(args)

    assert res["success"] is True
    assert len(res["issues"]) == 2
    first_issue = res["issues"][0]
    assert "message" not in first_issue
    assert set(first_issue.keys()).issubset({"type", "severity", "line_number", "end_line_number", "file_path", "line_hash", "block_hash", "reason_code", "issue_id"})
    assert any(key in first_issue for key in ("issue_id", "line_number", "line_hash", "block_hash"))
    meta = res.get("metadata", {})
    assert meta.get("returned_issues") == 2
    assert meta.get("total_issues") == 5
    assert meta.get("truncated") is True


@pytest.mark.asyncio
async def test_env_default_triggers_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyResponse:
        success = True
        score = 90.0
        execution_time_ms = 1.1
        metadata = {}
        issues = [
            _DummyIssue(
                type="grammar",
                severity="medium",
                message="typo",
                line_number=i + 1,
                suggestion="fix",
                issue_id=f"G{i:02d}",
            )
            for i in range(3)
        ]

    class DummyTool:
        def execute(self, request):
            return DummyResponse()

    monkeypatch.setattr(handlers_module, "RunQualityChecksTool", DummyTool)
    monkeypatch.setenv("MCP_LIGHTWEIGHT_DEFAULT", "1")

    res = await run_quality_checks({"episode_number": 1})

    assert len(res["issues"]) == 3
    assert "message" not in res["issues"][0]
    assert res.get("metadata", {}).get("returned_issues") == 3
