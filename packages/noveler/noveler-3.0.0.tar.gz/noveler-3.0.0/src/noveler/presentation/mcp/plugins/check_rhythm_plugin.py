#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/check_rhythm_plugin.py
# Purpose: Plugin wrapper for check_rhythm tool
# Context: Phase 2 plugin migration - Readability/Grammar tools group
"""Check rhythm plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class CheckRhythmPlugin(MCPToolPlugin):
    """Plugin wrapper for check_rhythm tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "check_rhythm"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the check_rhythm handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.check_rhythm


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return CheckRhythmPlugin()