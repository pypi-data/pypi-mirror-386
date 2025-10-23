#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/get_quality_schema_plugin.py
# Purpose: Plugin wrapper for get_quality_schema tool
# Context: Phase 2 plugin migration - Miscellaneous tools group
"""Get quality schema plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class GetQualitySchemaPlugin(MCPToolPlugin):
    """Plugin wrapper for get_quality_schema tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "get_quality_schema"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the get_quality_schema handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.get_quality_schema


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return GetQualitySchemaPlugin()