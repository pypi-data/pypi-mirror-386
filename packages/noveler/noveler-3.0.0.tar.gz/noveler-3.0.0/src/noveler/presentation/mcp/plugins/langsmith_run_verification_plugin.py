#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/langsmith_run_verification_plugin.py
# Purpose: Plugin wrapper for langsmith_run_verification tool (Phase 7 migration)
# Context: LangSmith integration tool for running verification commands
"""LangSmith run verification plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class LangSmithRunVerificationPlugin(MCPToolPlugin):
    """Plugin wrapper for langsmith_run_verification tool.

    Delegates to handlers.langsmith_run_verification for running verification.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'langsmith_run_verification'
        """
        return "langsmith_run_verification"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the langsmith_run_verification handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.langsmith_run_verification function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.langsmith_run_verification


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        LangSmithRunVerificationPlugin instance
    """
    return LangSmithRunVerificationPlugin()
