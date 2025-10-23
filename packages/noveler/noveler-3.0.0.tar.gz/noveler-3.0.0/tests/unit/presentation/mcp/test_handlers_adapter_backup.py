"""Tests.unit.presentation.mcp.test_handlers_adapter_backup
Where: Automated test module.
What: Thin adapter tests for backup management handler.
Why: Guards behaviour as we extract handlers from main.py.
"""

from __future__ import annotations

import pytest

from noveler.presentation.mcp.adapters.handlers import backup_management


@pytest.mark.asyncio
async def test_backup_management_adapter_runs() -> None:
    res = await backup_management({"episode_number": 1, "operation": "list"})
    assert isinstance(res, dict)
    assert "success" in res

