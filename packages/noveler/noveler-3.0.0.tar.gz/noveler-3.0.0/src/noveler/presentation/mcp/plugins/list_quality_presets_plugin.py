#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/list_quality_presets_plugin.py
# Purpose: Plugin wrapper for list_quality_presets tool
# Context: Phase 2 plugin migration - Miscellaneous tools group
"""List quality presets plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class ListQualityPresetsPlugin(MCPToolPlugin):
    """Plugin wrapper for list_quality_presets tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "list_quality_presets"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the list_quality_presets handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.list_quality_presets


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return ListQualityPresetsPlugin()