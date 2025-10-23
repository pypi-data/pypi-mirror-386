#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/export_quality_report_plugin.py
# Purpose: Plugin wrapper for export_quality_report tool
# Context: Phase 2 plugin migration - Quality tools group
"""Export quality report plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class ExportQualityReportPlugin(MCPToolPlugin):
    """Plugin wrapper for export_quality_report tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "export_quality_report"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the export_quality_report handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.export_quality_report


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return ExportQualityReportPlugin()