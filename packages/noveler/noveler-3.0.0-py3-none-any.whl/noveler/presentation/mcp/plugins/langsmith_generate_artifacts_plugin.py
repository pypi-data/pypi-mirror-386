#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/langsmith_generate_artifacts_plugin.py
# Purpose: Plugin wrapper for langsmith_generate_artifacts tool (Phase 7 migration)
# Context: LangSmith integration tool for generating artifacts from failed runs
"""LangSmith generate artifacts plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class LangSmithGenerateArtifactsPlugin(MCPToolPlugin):
    """Plugin wrapper for langsmith_generate_artifacts tool.

    Delegates to handlers.langsmith_generate_artifacts for LangSmith artifact generation.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'langsmith_generate_artifacts'
        """
        return "langsmith_generate_artifacts"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the langsmith_generate_artifacts handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.langsmith_generate_artifacts function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.langsmith_generate_artifacts


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        LangSmithGenerateArtifactsPlugin instance
    """
    return LangSmithGenerateArtifactsPlugin()
