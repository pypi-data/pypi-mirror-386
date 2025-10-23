#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/export_design_data_plugin.py
# Purpose: Plugin wrapper for export_design_data tool (Phase 7 migration)
# Context: Design data export tool for episode design information
"""Export design data plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class ExportDesignDataPlugin(MCPToolPlugin):
    """Plugin wrapper for export_design_data tool.

    Delegates to handlers.export_design_data for exporting episode design data.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'export_design_data'
        """
        return "export_design_data"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the export_design_data handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.export_design_data function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.export_design_data


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        ExportDesignDataPlugin instance
    """
    return ExportDesignDataPlugin()
