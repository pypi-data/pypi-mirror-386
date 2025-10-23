#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/test_result_analysis_plugin.py
# Purpose: Plugin wrapper for test_result_analysis tool
# Context: Phase 2 plugin migration - Miscellaneous tools group
"""Test result analysis plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class TestResultAnalysisPlugin(MCPToolPlugin):
    """Plugin wrapper for test_result_analysis tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "test_result_analysis"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the test_result_analysis handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.analyze_test_results


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return TestResultAnalysisPlugin()