#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugin_base.py
# Purpose: Define the base interface for MCP tool plugins to enable modular architecture
# Context: Phase 0 of plugin architecture migration - foundation setup with zero risk
"""Base interface for MCP tool plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


class MCPToolPlugin(ABC):
    """Abstract base class for MCP tool plugins.

    This interface defines the contract that all MCP tool plugins must implement
    to support lazy loading and dynamic registration in the plugin architecture.

    The plugin pattern enables:
    - Lazy loading: Tools are only imported when first invoked
    - Modularity: Each tool can be developed and tested independently
    - Hot reload: Plugins can be added/removed without server restart
    """

    @abstractmethod
    def get_name(self) -> str:
        """Return the unique tool name used for registration.

        Returns:
            Tool identifier string (e.g., 'run_quality_checks', 'check_readability')

        Examples:
            >>> plugin = CheckReadabilityPlugin()
            >>> plugin.get_name()
            'check_readability'
        """
        ...

    @abstractmethod
    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the handler function that executes the tool.

        Returns:
            Callable that accepts tool arguments dict and returns execution result.
            The handler may be sync or async.

        Examples:
            >>> plugin = CheckReadabilityPlugin()
            >>> handler = plugin.get_handler()
            >>> result = handler({"file_path": "test.md"})
        """
        ...

    @property
    def lazy_load(self) -> bool:
        """Control whether this plugin should be lazy-loaded.

        Returns:
            True to defer loading until first use (default), False to load eagerly.

        Notes:
            Most plugins should use lazy loading to minimize startup time.
            Override to return False only for critical tools needed at startup.
        """
        return True