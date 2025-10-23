#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/enhanced_execute_writing_step_plugin.py
# Purpose: Plugin wrapper for enhanced_execute_writing_step tool (Phase 7 migration)
# Context: Enhanced writing workflow tool with async execution and recovery
"""Enhanced execute writing step plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class EnhancedExecuteWritingStepPlugin(MCPToolPlugin):
    """Plugin wrapper for enhanced_execute_writing_step tool.

    Delegates to handlers.enhanced_execute_writing_step with recovery support.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'enhanced_execute_writing_step'
        """
        return "enhanced_execute_writing_step"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the enhanced_execute_writing_step handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.enhanced_execute_writing_step function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.enhanced_execute_writing_step


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        EnhancedExecuteWritingStepPlugin instance
    """
    return EnhancedExecuteWritingStepPlugin()
