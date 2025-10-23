#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/check_grammar_plugin.py
# Purpose: Plugin wrapper for check_grammar tool
# Context: Phase 2 plugin migration - Readability/Grammar tools group
"""Check grammar plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class CheckGrammarPlugin(MCPToolPlugin):
    """Plugin wrapper for check_grammar tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "check_grammar"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the check_grammar handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.check_grammar


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return CheckGrammarPlugin()