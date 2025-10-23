#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/get_conversation_context_plugin.py
# Purpose: Plugin wrapper for get_conversation_context tool (Phase 7 migration)
# Context: Conversation context retrieval tool for design system
"""Get conversation context plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class GetConversationContextPlugin(MCPToolPlugin):
    """Plugin wrapper for get_conversation_context tool.

    Delegates to handlers.get_conversation_context for retrieving conversation metadata.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'get_conversation_context'
        """
        return "get_conversation_context"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the get_conversation_context handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.get_conversation_context function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.get_conversation_context


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        GetConversationContextPlugin instance
    """
    return GetConversationContextPlugin()
