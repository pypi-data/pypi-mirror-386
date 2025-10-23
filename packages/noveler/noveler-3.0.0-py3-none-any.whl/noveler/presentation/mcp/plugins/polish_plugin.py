#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/polish_plugin.py
# Purpose: Plugin wrapper for polish tool
# Context: Phase 2 plugin migration - Polish tools group
"""Polish plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class PolishPlugin(MCPToolPlugin):
    """Plugin wrapper for polish tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "polish"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the polish handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.polish


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return PolishPlugin()