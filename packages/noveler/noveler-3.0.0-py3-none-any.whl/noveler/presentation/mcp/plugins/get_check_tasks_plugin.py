#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/get_check_tasks_plugin.py
# Purpose: Plugin wrapper for get_check_tasks tool (Phase 7 migration)
# Context: Progressive check workflow tool for retrieving check tasks
"""Get check tasks plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class GetCheckTasksPlugin(MCPToolPlugin):
    """Plugin wrapper for get_check_tasks tool.

    Delegates to handlers.get_check_tasks for progressive check workflow.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'get_check_tasks'
        """
        return "get_check_tasks"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the get_check_tasks handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.get_check_tasks function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.get_check_tasks


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        GetCheckTasksPlugin instance
    """
    return GetCheckTasksPlugin()
