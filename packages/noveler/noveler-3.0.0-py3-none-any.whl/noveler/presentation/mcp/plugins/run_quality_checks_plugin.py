#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/run_quality_checks_plugin.py
# Purpose: Plugin wrapper for run_quality_checks tool
# Context: Phase 2 plugin migration - Quality tools group
"""Run quality checks plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class RunQualityChecksPlugin(MCPToolPlugin):
    """Plugin wrapper for run_quality_checks tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "run_quality_checks"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the run_quality_checks handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.run_quality_checks


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return RunQualityChecksPlugin()