#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/get_file_reference_info_plugin.py
# Purpose: Plugin wrapper for get_file_reference_info tool (Phase 7 migration)
# Context: Utility tool for retrieving file reference information
"""Get file reference info plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class GetFileReferenceInfoPlugin(MCPToolPlugin):
    """Plugin wrapper for get_file_reference_info tool.

    Delegates to handlers.get_file_reference_info_util for file reference operations.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'get_file_reference_info'
        """
        return "get_file_reference_info"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the get_file_reference_info handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.get_file_reference_info_util function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.get_file_reference_info_util


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        GetFileReferenceInfoPlugin instance
    """
    return GetFileReferenceInfoPlugin()
