#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/polish_manuscript_apply_plugin.py
# Purpose: Plugin wrapper for polish_manuscript_apply tool
# Context: Phase 2 plugin migration - Polish tools group
"""Polish manuscript apply plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class PolishManuscriptApplyPlugin(MCPToolPlugin):
    """Plugin wrapper for polish_manuscript_apply tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "polish_manuscript_apply"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the polish_manuscript_apply handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.polish_manuscript_apply


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return PolishManuscriptApplyPlugin()