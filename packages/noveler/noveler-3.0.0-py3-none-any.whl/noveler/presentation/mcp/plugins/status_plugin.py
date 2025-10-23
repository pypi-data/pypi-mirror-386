#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/status_plugin.py
# Purpose: Plugin wrapper for status tool (Phase 7 migration)
# Context: Status display tool for novel writing project information
"""Status plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class StatusPlugin(MCPToolPlugin):
    """Plugin wrapper for status tool.

    Delegates to handlers.status for displaying project status.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'status'
        """
        return "status"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the status handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.status function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.status


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        StatusPlugin instance
    """
    return StatusPlugin()
