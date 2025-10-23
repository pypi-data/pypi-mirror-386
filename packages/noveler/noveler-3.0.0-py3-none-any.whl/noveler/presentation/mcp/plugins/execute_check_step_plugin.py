#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/execute_check_step_plugin.py
# Purpose: Plugin wrapper for execute_check_step tool (Phase 7 migration)
# Context: Progressive check workflow tool for executing check steps
"""Execute check step plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class ExecuteCheckStepPlugin(MCPToolPlugin):
    """Plugin wrapper for execute_check_step tool.

    Delegates to handlers.execute_check_step for progressive check execution.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'execute_check_step'
        """
        return "execute_check_step"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the execute_check_step handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.execute_check_step function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.execute_check_step


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        ExecuteCheckStepPlugin instance
    """
    return ExecuteCheckStepPlugin()
