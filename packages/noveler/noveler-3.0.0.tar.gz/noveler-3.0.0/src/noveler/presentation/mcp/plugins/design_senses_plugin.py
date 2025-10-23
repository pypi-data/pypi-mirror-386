#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/design_senses_plugin.py
# Purpose: Plugin wrapper for design_senses tool (Phase 7 migration)
# Context: STEP10 sensory description design tool with dialogue ID-based trigger management
"""Design senses plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class DesignSensesPlugin(MCPToolPlugin):
    """Plugin wrapper for design_senses tool.

    Delegates to handlers.design_senses for sensory trigger design.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'design_senses'
        """
        return "design_senses"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the design_senses handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.design_senses function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.design_senses


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        DesignSensesPlugin instance
    """
    return DesignSensesPlugin()
