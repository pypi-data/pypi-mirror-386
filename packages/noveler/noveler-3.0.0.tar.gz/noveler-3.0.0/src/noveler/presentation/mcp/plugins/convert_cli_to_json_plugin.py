#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/convert_cli_to_json_plugin.py
# Purpose: Plugin wrapper for convert_cli_to_json tool (Phase 7 migration)
# Context: Utility tool for converting CLI output to JSON format
"""Convert CLI to JSON plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class ConvertCliToJsonPlugin(MCPToolPlugin):
    """Plugin wrapper for convert_cli_to_json tool.

    Delegates to handlers.convert_cli_to_json_util for CLI conversion.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'convert_cli_to_json'
        """
        return "convert_cli_to_json"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the convert_cli_to_json handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.convert_cli_to_json_util function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.convert_cli_to_json_util


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        ConvertCliToJsonPlugin instance
    """
    return ConvertCliToJsonPlugin()
