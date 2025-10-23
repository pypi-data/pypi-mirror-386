#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/design_scenes_plugin.py
# Purpose: Plugin wrapper for design_scenes tool (Phase 7 migration)
# Context: STEP9 scene design tool with dialogue ID-based location/time management
"""Design scenes plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class DesignScenesPlugin(MCPToolPlugin):
    """Plugin wrapper for design_scenes tool.

    Delegates to handlers.design_scenes for scene setting design.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'design_scenes'
        """
        return "design_scenes"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the design_scenes handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.design_scenes function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.design_scenes


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        DesignScenesPlugin instance
    """
    return DesignScenesPlugin()
