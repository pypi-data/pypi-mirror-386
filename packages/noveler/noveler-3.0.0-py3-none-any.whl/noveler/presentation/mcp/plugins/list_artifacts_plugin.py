#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/list_artifacts_plugin.py
# Purpose: Plugin wrapper for list_artifacts tool (Phase 7 migration)
# Context: Artifact management tool for listing available artifacts
"""List artifacts plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class ListArtifactsPlugin(MCPToolPlugin):
    """Plugin wrapper for list_artifacts tool.

    Delegates to handlers.list_artifacts for artifact listing operations.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'list_artifacts'
        """
        return "list_artifacts"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the list_artifacts handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.list_artifacts function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.list_artifacts


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        ListArtifactsPlugin instance
    """
    return ListArtifactsPlugin()
