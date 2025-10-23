#!/usr/bin/env python3
"""
Dispatcher registry smoke test
- Ensures core tool names are registered and handlers resolvable
"""
from __future__ import annotations

import pytest

from noveler.presentation.mcp.dispatcher import get_registered_tools, get_handler


@pytest.mark.unit
def test_dispatcher_registry_contains_core_tools() -> None:
    tools = get_registered_tools()
    # a few representative tools from each group
    expected = {
        "run_quality_checks",
        "convert_cli_to_json",
        "get_writing_tasks",
        "generate_episode_preview",
        "status",
    }
    missing = expected - tools
    assert not missing, f"Missing tools in dispatcher: {sorted(missing)}"


@pytest.mark.unit
def test_dispatcher_returns_handlers() -> None:
    for name in [
        "run_quality_checks",
        "convert_cli_to_json",
        "get_writing_tasks",
        "generate_episode_preview",
        "status",
    ]:
        handler = get_handler(name)
        assert handler is not None, f"Handler not found for {name}"
