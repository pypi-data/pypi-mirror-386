"""Tests.unit.presentation.mcp.test_bootstrap_and_registry
Where: Automated test module.
What: Smoke tests for the presentation-layer MCP bootstrap and registry facade.
Why: Ensure thin facades import correctly and delegate without raising.
"""

from __future__ import annotations

import asyncio

import pytest


def test_import_bootstrap_main() -> None:
    from noveler.presentation.mcp import bootstrap

    assert callable(bootstrap._get_legacy_main)
    assert asyncio.iscoroutinefunction(bootstrap.main)


@pytest.mark.asyncio
async def test_registry_can_list_tools() -> None:
    from noveler.presentation.mcp.tool_registry import get_tools_async

    tools = await get_tools_async()
    assert isinstance(tools, list)
    # Tools may be many; basic sanity check on structure (name attr exists)
    if tools:
        t = tools[0]
        assert hasattr(t, "name")

