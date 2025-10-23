#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/design_conversations_plugin.py
# Purpose: Plugin wrapper for design_conversations tool (Phase 7 migration)
# Context: STEP7 conversation design tool with dialogue ID system
"""Design conversations plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class DesignConversationsPlugin(MCPToolPlugin):
    """Plugin wrapper for design_conversations tool.

    Delegates to handlers.design_conversations for dialogue structure design.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'design_conversations'
        """
        return "design_conversations"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the design_conversations handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.design_conversations function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.design_conversations


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        DesignConversationsPlugin instance
    """
    return DesignConversationsPlugin()
