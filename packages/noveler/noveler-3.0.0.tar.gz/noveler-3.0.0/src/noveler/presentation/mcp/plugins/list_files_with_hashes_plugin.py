#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/list_files_with_hashes_plugin.py
# Purpose: Plugin wrapper for list_files_with_hashes tool (Phase 7 migration)
# Context: Utility tool for listing files with their SHA256 hashes
"""List files with hashes plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class ListFilesWithHashesPlugin(MCPToolPlugin):
    """Plugin wrapper for list_files_with_hashes tool.

    Delegates to handlers.list_files_with_hashes_util for file listing with hashes.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'list_files_with_hashes'
        """
        return "list_files_with_hashes"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the list_files_with_hashes handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.list_files_with_hashes_util function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.list_files_with_hashes_util


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        ListFilesWithHashesPlugin instance
    """
    return ListFilesWithHashesPlugin()
