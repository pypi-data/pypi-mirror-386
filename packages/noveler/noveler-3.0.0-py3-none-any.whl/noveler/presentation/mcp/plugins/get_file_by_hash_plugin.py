#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/get_file_by_hash_plugin.py
# Purpose: Plugin wrapper for get_file_by_hash tool (Phase 7 migration)
# Context: Utility tool for retrieving file by SHA256 hash
"""Get file by hash plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class GetFileByHashPlugin(MCPToolPlugin):
    """Plugin wrapper for get_file_by_hash tool.

    Delegates to handlers.get_file_by_hash_util for hash-based file retrieval.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'get_file_by_hash'
        """
        return "get_file_by_hash"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the get_file_by_hash handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.get_file_by_hash_util function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.get_file_by_hash_util


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        GetFileByHashPlugin instance
    """
    return GetFileByHashPlugin()
