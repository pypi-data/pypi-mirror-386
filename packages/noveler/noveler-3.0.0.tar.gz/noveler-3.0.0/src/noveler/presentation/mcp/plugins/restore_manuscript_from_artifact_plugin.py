#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/restore_manuscript_from_artifact_plugin.py
# Purpose: Plugin wrapper for restore_manuscript_from_artifact tool
# Context: Phase 2 plugin migration - Polish tools group
"""Restore manuscript from artifact plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class RestoreManuscriptFromArtifactPlugin(MCPToolPlugin):
    """Plugin wrapper for restore_manuscript_from_artifact tool."""

    def get_name(self) -> str:
        """Return the tool identifier."""
        return "restore_manuscript_from_artifact"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the restore_manuscript_from_artifact handler function."""
        from noveler.presentation.mcp.adapters import handlers

        return handlers.restore_manuscript_from_artifact


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance."""
    return RestoreManuscriptFromArtifactPlugin()