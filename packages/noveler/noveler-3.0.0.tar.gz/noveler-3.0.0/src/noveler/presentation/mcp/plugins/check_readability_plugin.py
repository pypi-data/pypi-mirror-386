#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/check_readability_plugin.py
# Purpose: Plugin wrapper for check_readability tool (Phase 1 pilot)
# Context: First plugin implementation to validate plugin architecture pattern
"""Check readability plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class CheckReadabilityPlugin(MCPToolPlugin):
    """Plugin wrapper for check_readability tool.

    This is the pilot implementation for Phase 1 plugin migration.
    It delegates to the existing handlers.check_readability function
    to maintain backward compatibility while enabling lazy loading.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'check_readability'
        """
        return "check_readability"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the check_readability handler function.

        The handler is imported lazily when this method is called,
        not at plugin registration time.

        Returns:
            handlers.check_readability function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.check_readability


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    This function is called by PluginRegistry during lazy loading.

    Returns:
        CheckReadabilityPlugin instance

    Examples:
        >>> plugin = create_plugin()
        >>> plugin.get_name()
        'check_readability'
    """
    return CheckReadabilityPlugin()