#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/get_issue_context_plugin.py
# Purpose: Plugin wrapper for get_issue_context tool
# Context: Phase 2 plugin migration - Quality tools group
"""Get issue context plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class GetIssueContextPlugin(MCPToolPlugin):
    """Plugin wrapper for get_issue_context tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "get_issue_context"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the get_issue_context handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.get_issue_context


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return GetIssueContextPlugin()