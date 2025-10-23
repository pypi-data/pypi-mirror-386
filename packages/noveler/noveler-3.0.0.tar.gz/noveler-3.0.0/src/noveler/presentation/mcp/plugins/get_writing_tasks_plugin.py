#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/get_writing_tasks_plugin.py
# Purpose: Plugin wrapper for get_writing_tasks tool (Phase 7 migration)
# Context: Writing workflow tool for 18-step writing system task retrieval
"""Get writing tasks plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class GetWritingTasksPlugin(MCPToolPlugin):
    """Plugin wrapper for get_writing_tasks tool.

    Delegates to handlers.get_writing_tasks for 18-step writing workflow.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'get_writing_tasks'
        """
        return "get_writing_tasks"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the get_writing_tasks handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.get_writing_tasks function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.get_writing_tasks


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        GetWritingTasksPlugin instance
    """
    return GetWritingTasksPlugin()
