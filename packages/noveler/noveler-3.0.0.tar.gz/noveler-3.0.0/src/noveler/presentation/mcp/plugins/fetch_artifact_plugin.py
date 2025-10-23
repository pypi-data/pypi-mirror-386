#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/fetch_artifact_plugin.py
# Purpose: Plugin wrapper for fetch_artifact tool (Phase 7 migration)
# Context: Artifact management tool for retrieving stored artifacts
"""Fetch artifact plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class FetchArtifactPlugin(MCPToolPlugin):
    """Plugin wrapper for fetch_artifact tool.

    Delegates to handlers.fetch_artifact for artifact retrieval operations.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'fetch_artifact'
        """
        return "fetch_artifact"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the fetch_artifact handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.fetch_artifact function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.fetch_artifact


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        FetchArtifactPlugin instance
    """
    return FetchArtifactPlugin()
