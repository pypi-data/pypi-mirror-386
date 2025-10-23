"""Tests.unit.presentation.mcp.test_handlers_adapter_style_and_tra
Where: Automated test module.
What: Thin adapter tests for style and test_result_analysis.
Why: Guards behaviour as we extract handlers from main.py.
"""

from __future__ import annotations

import pytest

from noveler.presentation.mcp.adapters.handlers import (
    check_style,
    analyze_test_results,
)


@pytest.mark.asyncio
async def test_check_style_adapter_runs() -> None:
    res = await check_style({"episode_number": 1})
    assert isinstance(res, dict)
    assert "success" in res and "issues" in res


@pytest.mark.asyncio
async def test_test_result_analysis_adapter_runs() -> None:
    res = await analyze_test_results({"episode_number": 1})
    assert isinstance(res, dict)
    assert "success" in res and "issues" in res
