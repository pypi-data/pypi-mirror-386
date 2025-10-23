#!/usr/bin/env python3
import asyncio

import pytest

from noveler.presentation.mcp.adapters.ten_stage_adapter import TenStageWritingMCPAdapter


@pytest.mark.asyncio
async def test_progress_status_not_implemented_returns_error_dict():
    adapter = TenStageWritingMCPAdapter()
    result = await adapter.get_progress_status(None)
    assert isinstance(result, dict)
    assert result.get("result", {}).get("success") is False
    assert "TenStageProgressUseCase is not implemented" in result.get("result", {}).get("error", "")

