#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/backup_management_plugin.py
# Purpose: Plugin wrapper for backup_management tool
# Context: Phase 2 plugin migration - Miscellaneous tools group
"""Backup management plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class BackupManagementPlugin(MCPToolPlugin):
    """Plugin wrapper for backup_management tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "backup_management"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the backup_management handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.backup_management


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return BackupManagementPlugin()