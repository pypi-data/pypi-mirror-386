#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/fix_quality_issues_plugin.py
# Purpose: Plugin wrapper for fix_quality_issues tool
# Context: Phase 2 plugin migration - Quality tools group
"""Fix quality issues plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class FixQualityIssuesPlugin(MCPToolPlugin):
    """Plugin wrapper for fix_quality_issues tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "fix_quality_issues"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the fix_quality_issues handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.fix_quality_issues


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return FixQualityIssuesPlugin()