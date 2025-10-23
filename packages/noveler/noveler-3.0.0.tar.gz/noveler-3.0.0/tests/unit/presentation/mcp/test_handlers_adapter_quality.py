"""Tests.unit.presentation.mcp.test_handlers_adapter_quality
Where: Automated test module.
What: Thin adapter tests for quality metadata handlers.
Why: Guards behaviour as we extract handlers from main.py.
"""

from __future__ import annotations

import pytest

import noveler.presentation.mcp.adapters.handlers as handlers_module
from noveler.presentation.mcp.adapters.handlers import (
    list_quality_presets,
    get_quality_schema,
    run_quality_checks,
    improve_quality_until,
)


@pytest.mark.asyncio
async def test_list_quality_presets_adapter_runs() -> None:
    res = await list_quality_presets({})
    assert isinstance(res, dict)
    assert res.get("success") is True
    assert "issues" in res and isinstance(res["issues"], list)


@pytest.mark.asyncio
async def test_get_quality_schema_adapter_runs() -> None:
    res = await get_quality_schema({})
    assert isinstance(res, dict)
    assert res.get("success") is True
    assert "issues" in res and isinstance(res["issues"], list)


@pytest.mark.asyncio
async def test_run_quality_checks_adapter_normalises(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class DummyResponse:
        success = True
        score = 92.5
        issues: list[object] = []
        execution_time_ms = 10.5
        metadata = {"source": "stub"}

    class DummyTool:
        def execute(self, request):
            captured["request"] = request
            return DummyResponse()

    monkeypatch.setattr(handlers_module, "RunQualityChecksTool", DummyTool)

    args = {"episode_number": 2, "project_name": "demo"}
    res = await run_quality_checks(args)

    assert res["success"] is True
    assert res["score"] == DummyResponse.score
    assert captured["request"].episode_number == 2
    assert captured["request"].additional_params == args


@pytest.mark.asyncio
async def test_improve_quality_until_adapter_normalises(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class DummyResponse:
        success = True
        score = 88.0
        issues: list[object] = []
        execution_time_ms = 9.0
        metadata = {"mode": "stub"}

    class DummyTool:
        def execute(self, request):
            captured["request"] = request
            return DummyResponse()

    monkeypatch.setattr(handlers_module, "ImproveQualityUntilTool", DummyTool)

    args = {"episode_number": 4, "target_score": 85}
    res = await improve_quality_until(args)

    assert res["success"] is True
    assert res["score"] == DummyResponse.score
    assert captured["request"].episode_number == 4
    assert captured["request"].additional_params == args
