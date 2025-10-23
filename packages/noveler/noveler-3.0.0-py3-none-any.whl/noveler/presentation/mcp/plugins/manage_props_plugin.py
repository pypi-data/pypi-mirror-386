#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/manage_props_plugin.py
# Purpose: Plugin wrapper for manage_props tool (Phase 7 migration)
# Context: STEP11 props/worldview design tool with dialogue ID-based item management
"""Manage props plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class ManagePropsPlugin(MCPToolPlugin):
    """Plugin wrapper for manage_props tool.

    Delegates to handlers.manage_props for props and worldview management.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'manage_props'
        """
        return "manage_props"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the manage_props handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.manage_props function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.manage_props


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        ManagePropsPlugin instance
    """
    return ManagePropsPlugin()
