#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/track_emotions_plugin.py
# Purpose: Plugin wrapper for track_emotions tool (Phase 7 migration)
# Context: STEP8 emotion tracking tool with dialogue ID-based emotion management
"""Track emotions plugin for MCP."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class TrackEmotionsPlugin(MCPToolPlugin):
    """Plugin wrapper for track_emotions tool.

    Delegates to handlers.track_emotions for emotion curve tracking.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'track_emotions'
        """
        return "track_emotions"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the track_emotions handler function.

        The handler is imported lazily when this method is called.

        Returns:
            handlers.track_emotions function
        """
        from noveler.presentation.mcp.adapters import handlers

        return handlers.track_emotions


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        TrackEmotionsPlugin instance
    """
    return TrackEmotionsPlugin()
