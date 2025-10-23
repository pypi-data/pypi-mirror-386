"""Tests.unit.presentation.mcp.test_handlers_adapter
Where: Automated test module.
What: Unit tests for presentation-layer handlers helpers.
Why: Guard the thin adapter behavior as we thin the server.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from mcp.types import TextContent

from noveler.presentation.mcp.adapters.handlers import execute_with_logging, wrap_json_text


class DummyConsole:
    def print_info(self, *_: Any, **__: Any) -> None:  # noqa: D401 - minimal stub
        """No-op info logger."""

    def print_error(self, *_: Any, **__: Any) -> None:  # noqa: D401 - minimal stub
        """No-op error logger."""


@pytest.mark.asyncio
async def test_execute_with_logging_runs_and_returns_payload() -> None:
    async def runner() -> dict[str, Any]:
        await asyncio.sleep(0)  # yield control once
        return {"success": True, "score": 100.0}

    res = await execute_with_logging("dummy", {"a": 1}, runner, debug=True, console=DummyConsole())
    assert isinstance(res, dict)
    assert res.get("success") is True


def test_wrap_json_text_returns_textcontent_list() -> None:
    payload = {"ok": True}
    wrapped = wrap_json_text(payload)
    assert isinstance(wrapped, list) and wrapped
    assert isinstance(wrapped[0], TextContent)
    assert "\n" in wrapped[0].text  # pretty-printed JSON

