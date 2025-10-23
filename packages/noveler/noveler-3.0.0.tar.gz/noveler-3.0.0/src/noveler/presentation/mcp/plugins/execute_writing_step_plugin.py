#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/execute_writing_step_plugin.py
# Purpose: Plugin wrapper for execute_writing_step tool (Phase 7 migration)
# Context: Writing workflow tool for executing 18-step writing system steps
"""Execute writing step plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class ExecuteWritingStepPlugin(MCPToolPlugin):
    """Plugin wrapper for execute_writing_step tool.

    Delegates to handlers.execute_writing_step for step execution.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'execute_writing_step'
        """
        return "execute_writing_step"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the execute_writing_step handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.execute_writing_step function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.execute_writing_step


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        ExecuteWritingStepPlugin instance
    """
    return ExecuteWritingStepPlugin()
