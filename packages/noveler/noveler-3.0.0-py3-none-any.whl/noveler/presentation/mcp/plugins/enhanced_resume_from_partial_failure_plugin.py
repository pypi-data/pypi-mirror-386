#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/enhanced_resume_from_partial_failure_plugin.py
# Purpose: Plugin wrapper for enhanced_resume_from_partial_failure tool (Phase 7 migration)
# Context: Enhanced writing workflow tool for resuming from partial failures
"""Enhanced resume from partial failure plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class EnhancedResumeFromPartialFailurePlugin(MCPToolPlugin):
    """Plugin wrapper for enhanced_resume_from_partial_failure tool.

    Delegates to handlers.enhanced_resume_from_partial_failure for async recovery.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'enhanced_resume_from_partial_failure'
        """
        return "enhanced_resume_from_partial_failure"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the enhanced_resume_from_partial_failure handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.enhanced_resume_from_partial_failure function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.enhanced_resume_from_partial_failure


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        EnhancedResumeFromPartialFailurePlugin instance
    """
    return EnhancedResumeFromPartialFailurePlugin()
