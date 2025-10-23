"""tests.unit.presentation.mcp.test_dispatcher
Where: Presentation-layer dispatcher tests.
What: Ensure dispatcher routes MCP tool names to presentation handlers.
Why: Guards the thin delegation contract introduced for main.py thinning.
"""

from __future__ import annotations

import pytest

from noveler.presentation.mcp import dispatcher


def test_registered_tools_include_quality_handlers() -> None:
    registered = dispatcher.get_registered_tools()
    assert "run_quality_checks" in registered
    assert "improve_quality_until" in registered
    assert "fix_quality_issues" in registered
    assert "get_issue_context" in registered
    assert "export_quality_report" in registered


@pytest.mark.asyncio
async def test_dispatcher_invokes_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    async def fake_handler(arguments: dict[str, object]) -> dict[str, object]:
        captured["arguments"] = arguments
        return {"success": True, "echo": arguments.get("value")}

    monkeypatch.setitem(dispatcher._TOOL_DISPATCH_TABLE, "sample_tool", fake_handler)  # type: ignore[attr-defined]

    args = {"value": 42}
    result = await dispatcher.dispatch("sample_tool", args)

    assert result == {"success": True, "echo": 42}
    assert captured["arguments"] == args


@pytest.mark.asyncio
async def test_dispatcher_returns_none_for_unknown_tool() -> None:
    result = await dispatcher.dispatch("__unknown_tool__", {})
    assert result is None
