"""Tests.unit.presentation.mcp.test_handlers_adapter_artifacts
Where: Automated test module.
What: Thin adapter tests for artifact fetch/list handlers.
Why: Guards behaviour as we extract handlers from main.py.
"""

from __future__ import annotations

import pytest

from noveler.presentation.mcp.adapters.handlers import (
    fetch_artifact,
    list_artifacts,
)


@pytest.mark.asyncio
async def test_list_artifacts_adapter_runs() -> None:
    res = await list_artifacts({})
    assert isinstance(res, dict)
    assert "success" in res


@pytest.mark.asyncio
async def test_fetch_artifact_adapter_handles_missing() -> None:
    # Expect graceful error for unknown artifact id
    res = await fetch_artifact({"artifact_id": "artifact:nonexistent"})
    assert isinstance(res, dict)
    assert "success" in res

