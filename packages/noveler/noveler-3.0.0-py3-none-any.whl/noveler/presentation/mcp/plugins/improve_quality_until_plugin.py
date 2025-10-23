#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/improve_quality_until_plugin.py
# Purpose: Plugin wrapper for improve_quality_until tool
# Context: Phase 2 plugin migration - Quality tools group
"""Improve quality until plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class ImproveQualityUntilPlugin(MCPToolPlugin):
    """Plugin wrapper for improve_quality_until tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "improve_quality_until"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the improve_quality_until handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.improve_quality_until


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return ImproveQualityUntilPlugin()