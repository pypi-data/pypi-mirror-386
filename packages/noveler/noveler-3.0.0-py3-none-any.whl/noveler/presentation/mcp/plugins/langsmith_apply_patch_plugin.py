#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/langsmith_apply_patch_plugin.py
# Purpose: Plugin wrapper for langsmith_apply_patch tool (Phase 7 migration)
# Context: LangSmith integration tool for applying patches from failed runs
"""LangSmith apply patch plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class LangSmithApplyPatchPlugin(MCPToolPlugin):
    """Plugin wrapper for langsmith_apply_patch tool.

    Delegates to handlers.langsmith_apply_patch for applying LangSmith patches.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'langsmith_apply_patch'
        """
        return "langsmith_apply_patch"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the langsmith_apply_patch handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.langsmith_apply_patch function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.langsmith_apply_patch


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        LangSmithApplyPatchPlugin instance
    """
    return LangSmithApplyPatchPlugin()
