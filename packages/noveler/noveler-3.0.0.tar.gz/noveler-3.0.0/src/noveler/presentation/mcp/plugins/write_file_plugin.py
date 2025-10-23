#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/write_file_plugin.py
# Purpose: Plugin wrapper for write_file tool (Phase 7 migration)
# Context: File I/O tool for writing content relative to project root
"""Write file plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class WriteFilePlugin(MCPToolPlugin):
    """Plugin wrapper for write_file tool.

    Delegates to handlers.write_file for file write operations.
    Supports both 'write_file' and 'write' aliases.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'write_file'
        """
        return "write_file"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the write_file handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.write_file function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.write_file


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        WriteFilePlugin instance
    """
    return WriteFilePlugin()
