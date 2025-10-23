#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/generate_episode_preview_plugin.py
# Purpose: Plugin wrapper for generate_episode_preview tool
# Context: Phase 2 plugin migration - Polish tools group
"""Generate episode preview plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class GenerateEpisodePreviewPlugin(MCPToolPlugin):
    """Plugin wrapper for generate_episode_preview tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "generate_episode_preview"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the generate_episode_preview handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.generate_episode_preview


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return GenerateEpisodePreviewPlugin()