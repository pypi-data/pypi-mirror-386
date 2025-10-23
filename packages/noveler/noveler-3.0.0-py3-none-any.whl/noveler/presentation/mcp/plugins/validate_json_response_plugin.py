#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/validate_json_response_plugin.py
# Purpose: Plugin wrapper for validate_json_response tool (Phase 7 migration)
# Context: Utility tool for validating JSON response format
"""Validate JSON response plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class ValidateJsonResponsePlugin(MCPToolPlugin):
    """Plugin wrapper for validate_json_response tool.

    Delegates to handlers.validate_json_response_util for JSON validation.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'validate_json_response'
        """
        return "validate_json_response"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the validate_json_response handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.validate_json_response_util function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.validate_json_response_util


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        ValidateJsonResponsePlugin instance
    """
    return ValidateJsonResponsePlugin()
