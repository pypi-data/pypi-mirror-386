#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/get_task_status_plugin.py
# Purpose: Plugin wrapper for get_task_status tool (Phase 7 migration)
# Context: Writing workflow tool for retrieving task status
"""Get task status plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class GetTaskStatusPlugin(MCPToolPlugin):
    """Plugin wrapper for get_task_status tool.

    Delegates to handlers.get_task_status for status retrieval.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'get_task_status'
        """
        return "get_task_status"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the get_task_status handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.get_task_status function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.get_task_status


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        GetTaskStatusPlugin instance
    """
    return GetTaskStatusPlugin()
