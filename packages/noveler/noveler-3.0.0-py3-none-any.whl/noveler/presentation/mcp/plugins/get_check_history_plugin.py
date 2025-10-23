#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/get_check_history_plugin.py
# Purpose: Plugin wrapper for get_check_history tool (Phase 7 migration)
# Context: Progressive check workflow tool for retrieving history
"""Get check history plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class GetCheckHistoryPlugin(MCPToolPlugin):
    """Plugin wrapper for get_check_history tool.

    Delegates to handlers.get_check_history for history retrieval.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'get_check_history'
        """
        return "get_check_history"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the get_check_history handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.get_check_history function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.get_check_history


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        GetCheckHistoryPlugin instance
    """
    return GetCheckHistoryPlugin()
