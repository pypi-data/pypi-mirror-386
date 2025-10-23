#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/enhanced_get_writing_tasks_plugin.py
# Purpose: Plugin wrapper for enhanced_get_writing_tasks tool (Phase 7 migration)
# Context: Enhanced writing workflow tool with error handling integration
"""Enhanced get writing tasks plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class EnhancedGetWritingTasksPlugin(MCPToolPlugin):
    """Plugin wrapper for enhanced_get_writing_tasks tool.

    Delegates to handlers.enhanced_get_writing_tasks with diagnostic info.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'enhanced_get_writing_tasks'
        """
        return "enhanced_get_writing_tasks"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the enhanced_get_writing_tasks handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.enhanced_get_writing_tasks function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.enhanced_get_writing_tasks


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        EnhancedGetWritingTasksPlugin instance
    """
    return EnhancedGetWritingTasksPlugin()
