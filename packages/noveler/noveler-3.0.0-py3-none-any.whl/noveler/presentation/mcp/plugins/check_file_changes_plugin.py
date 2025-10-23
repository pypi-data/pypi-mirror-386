#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/check_file_changes_plugin.py
# Purpose: Plugin wrapper for check_file_changes tool (Phase 7 migration)
# Context: Utility tool for checking file change detection
"""Check file changes plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class CheckFileChangesPlugin(MCPToolPlugin):
    """Plugin wrapper for check_file_changes tool.

    Delegates to handlers.check_file_changes_util for file change detection.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'check_file_changes'
        """
        return "check_file_changes"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the check_file_changes handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.check_file_changes_util function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.check_file_changes_util


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        CheckFileChangesPlugin instance
    """
    return CheckFileChangesPlugin()
