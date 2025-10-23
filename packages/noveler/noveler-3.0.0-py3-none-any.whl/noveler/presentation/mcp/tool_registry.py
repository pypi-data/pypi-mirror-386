# File: src/noveler/presentation/mcp/tool_registry.py
# Purpose: Presentation-layer access to the MCP tool registry.
# Context: Provides a stable API to obtain the list of MCP tools while the
#          legacy server code remains in mcp_servers/noveler/main.py.
"""Presentation-layer MCP tool registry facade.

This module exposes a small API to retrieve the list of MCP tools. Internally
it defers to the current server implementation to avoid duplication during the
transition to a cleaner architecture.
"""

from __future__ import annotations

import asyncio
from typing import List

from mcp import Tool


async def get_tools_async() -> List[Tool]:
    """Return the list of MCP tools from the legacy registry.

    Returns:
        list[Tool]: Tools exposed by the Noveler MCP server.
    """
    from mcp_servers.noveler import main as legacy  # noqa: PLC0415

    # Call the stable implementation function to avoid recursion through the
    # thin wrapper decorated on the server instance.
    return await legacy._legacy_list_tools_impl()  # type: ignore[attr-defined]


def get_tools() -> List[Tool]:
    """Synchronous helper to obtain tools (convenience for callers).

    Internally spins a temporary event loop when necessary.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(get_tools_async())
        finally:
            try:
                loop.close()
            except Exception:
                pass
    else:
        # Running within an event loop; delegate with ensure_future and gather
        return loop.run_until_complete(get_tools_async())  # type: ignore[no-any-return]
