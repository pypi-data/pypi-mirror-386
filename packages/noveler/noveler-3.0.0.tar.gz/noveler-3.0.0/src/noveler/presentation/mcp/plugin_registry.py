#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugin_registry.py
# Purpose: Provide a registry for lazy-loading MCP tool plugins with backward compatibility
# Context: Phase 0-4 of plugin architecture migration - now supports auto-discovery
"""Plugin registry for MCP tools supporting lazy loading and auto-discovery."""

from __future__ import annotations

import importlib
import importlib.util
from collections.abc import Callable
from pathlib import Path
from typing import Any

from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class PluginRegistry:
    """Registry for MCP tool plugins with lazy loading support.

    This registry enables gradual migration from the legacy monolithic architecture
    to a plugin-based system. It supports:

    - Lazy loading: Plugins are registered by module path and imported on first use
    - Legacy fallback: Existing handlers can be registered for backward compatibility
    - Caching: Once loaded, plugins are cached to avoid repeated imports

    The registry maintains two internal dictionaries:
    - _plugins: Maps tool names to module paths (not yet imported)
    - _loaded: Maps tool names to instantiated plugin objects (cached)
    - _legacy_fallback: Maps tool names to legacy handler functions

    During Phase 1-2 migration, both plugin and legacy systems coexist.
    Legacy handlers take precedence to ensure existing code continues working.
    """

    def __init__(self) -> None:
        """Initialize empty plugin registry."""
        self._plugins: dict[str, str] = {}  # name -> module_path
        self._loaded: dict[str, MCPToolPlugin] = {}  # name -> plugin instance
        self._legacy_fallback: dict[str, Callable[[dict[str, Any]], Any]] = {}

    def register_plugin(self, name: str, module_path: str) -> None:
        """Register a plugin by module path without importing it.

        The plugin will be lazy-loaded when first accessed via get_handler().

        Args:
            name: Unique tool identifier (e.g., 'check_readability')
            module_path: Full Python module path (e.g., 'noveler.presentation.mcp.plugins.check_readability_plugin')

        Examples:
            >>> registry = PluginRegistry()
            >>> registry.register_plugin('check_readability', 'noveler.presentation.mcp.plugins.check_readability_plugin')
            >>> # No import occurs until get_handler() is called
        """
        self._plugins[name] = module_path

    def register_legacy(self, name: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        """Register a legacy handler for backward compatibility.

        Legacy handlers take precedence over plugins during migration phases.
        This method will be removed in Phase 3 after full plugin migration.

        Args:
            name: Tool identifier matching existing dispatch table
            handler: Existing handler function from adapters.handlers module

        Examples:
            >>> registry = PluginRegistry()
            >>> registry.register_legacy('run_quality_checks', handlers.run_quality_checks)
            >>> handler = registry.get_handler('run_quality_checks')  # Returns legacy handler
        """
        self._legacy_fallback[name] = handler

    def get_handler(self, name: str) -> Callable[[dict[str, Any]], Any] | None:
        """Get handler for a tool, lazy-loading plugin if necessary.

        Resolution order:
        1. Check legacy fallback (for backward compatibility)
        2. Check loaded plugin cache
        3. Import and instantiate plugin if registered
        4. Return None if tool not found

        Args:
            name: Tool identifier

        Returns:
            Handler callable or None if tool not registered or on load error

        Notes:
            Import errors are caught and logged. When a plugin fails to load,
            the method returns None, allowing the dispatcher to fall back to
            legacy handlers if available.

        Examples:
            >>> registry = PluginRegistry()
            >>> registry.register_plugin('check_readability', 'noveler.presentation.mcp.plugins.check_readability_plugin')
            >>> handler = registry.get_handler('check_readability')  # Imports module on first call
            >>> handler2 = registry.get_handler('check_readability')  # Uses cached plugin
        """
        # Legacy fallback takes precedence (Phase 1-2 migration period)
        if name in self._legacy_fallback:
            return self._legacy_fallback[name]

        # Plugin path: lazy load on first access
        if name not in self._loaded and name in self._plugins:
            try:
                module = importlib.import_module(self._plugins[name])
                self._loaded[name] = module.create_plugin()
            except (ImportError, AttributeError, ModuleNotFoundError) as e:
                # Log error and return None to allow legacy fallback
                # Note: Using print for now; will be replaced with proper logging
                # when integrated with domain logging infrastructure
                print(f"Warning: Failed to load plugin '{name}' from '{self._plugins[name]}': {e}")
                return None

        # Return cached plugin handler
        if name in self._loaded:
            return self._loaded[name].get_handler()

        return None

    def unregister_plugin(self, name: str) -> None:
        """Remove a plugin from the registry (for testing or rollback).

        Args:
            name: Tool identifier to remove

        Examples:
            >>> registry = PluginRegistry()
            >>> registry.register_plugin('check_readability', 'noveler.presentation.mcp.plugins.check_readability_plugin')
            >>> registry.unregister_plugin('check_readability')
        """
        self._plugins.pop(name, None)
        self._loaded.pop(name, None)

    def clear_cache(self) -> None:
        """Clear the loaded plugin cache (primarily for testing).

        This forces plugins to be reimported on next access.

        Examples:
            >>> registry = PluginRegistry()
            >>> registry.clear_cache()
        """
        self._loaded.clear()

    def get_registered_tools(self) -> set[str]:
        """Return set of all registered tool names (plugins + legacy).

        Returns:
            Set of tool identifiers

        Examples:
            >>> registry = PluginRegistry()
            >>> registry.register_plugin('check_readability', '...')
            >>> registry.register_legacy('run_quality_checks', handler)
            >>> registry.get_registered_tools()
            {'check_readability', 'run_quality_checks'}
        """
        return set(self._plugins.keys()) | set(self._legacy_fallback.keys())

    def auto_discover_plugins(self, plugins_dir: Path, base_module: str) -> int:
        """Auto-discover and register plugins from a directory.

        Phase 4: Automatically scan a directory for plugin files and register them.

        Convention: Plugin files must:
        - End with '_plugin.py'
        - Contain a create_plugin() factory function
        - Be located in the specified directory

        Args:
            plugins_dir: Path to directory containing plugin files
            base_module: Base module path (e.g., 'noveler.presentation.mcp.plugins')

        Returns:
            Number of plugins discovered and registered

        Examples:
            >>> registry = PluginRegistry()
            >>> from pathlib import Path
            >>> plugins_path = Path(__file__).parent / 'plugins'
            >>> count = registry.auto_discover_plugins(plugins_path, 'noveler.presentation.mcp.plugins')
            >>> print(f"Discovered {count} plugins")
        """
        if not plugins_dir.exists() or not plugins_dir.is_dir():
            return 0

        discovered = 0
        for plugin_file in plugins_dir.glob('*_plugin.py'):
            # Extract plugin name from filename (e.g., 'check_readability_plugin.py' -> 'check_readability')
            plugin_name = plugin_file.stem.replace('_plugin', '')

            # Build full module path
            module_path = f"{base_module}.{plugin_file.stem}"

            # Register the plugin (lazy loading)
            self.register_plugin(plugin_name, module_path)
            discovered += 1

        return discovered

    def warmup(self, tool_names: list[str] | None = None) -> int:
        """Preload plugins to reduce first-call latency.

        Phase 6: Performance optimization - preload frequently used plugins.

        Args:
            tool_names: Optional list of tool names to warm up.
                       If None, warms up all registered plugins.

        Returns:
            Number of plugins successfully warmed up

        Examples:
            >>> registry = PluginRegistry()
            >>> registry.auto_discover_plugins(plugins_dir, base_module)
            >>> # Warm up all plugins
            >>> registry.warmup()
            >>> # Or warm up specific plugins
            >>> registry.warmup(['check_readability', 'run_quality_checks'])
        """
        if tool_names is None:
            tool_names = list(self._plugins.keys())

        warmed = 0
        for name in tool_names:
            if name in self._plugins and name not in self._loaded:
                # Trigger lazy loading
                handler = self.get_handler(name)
                if handler is not None:
                    warmed += 1

        return warmed