#!/usr/bin/env python3
# File: tests/unit/presentation/mcp/test_quality_plugins.py
# Purpose: Unit tests for Phase 2 Quality plugins
# Context: Validate lazy loading and handler correctness for 5 quality tools
"""Tests for Phase 2 Quality plugins."""

import pytest

from noveler.presentation.mcp.plugin_registry import PluginRegistry


# Phase 2 Quality plugins to test
QUALITY_PLUGINS = {
    "run_quality_checks": "noveler.presentation.mcp.plugins.run_quality_checks_plugin",
    "improve_quality_until": "noveler.presentation.mcp.plugins.improve_quality_until_plugin",
    "fix_quality_issues": "noveler.presentation.mcp.plugins.fix_quality_issues_plugin",
    "get_issue_context": "noveler.presentation.mcp.plugins.get_issue_context_plugin",
    "export_quality_report": "noveler.presentation.mcp.plugins.export_quality_report_plugin",
}


@pytest.mark.parametrize("plugin_name,module_path", QUALITY_PLUGINS.items())
def test_quality_plugin_registration_does_not_import(plugin_name, module_path):
    """Verify that registering quality plugins does not trigger import."""
    registry = PluginRegistry()

    # Register plugin (should not raise error)
    registry.register_plugin(plugin_name, module_path)

    # Should succeed because no import happens yet
    assert plugin_name in registry._plugins
    assert plugin_name not in registry._loaded


@pytest.mark.parametrize("plugin_name,module_path", QUALITY_PLUGINS.items())
def test_quality_plugin_lazy_loads_on_first_access(plugin_name, module_path):
    """Verify that quality plugins lazy-load on first handler access."""
    registry = PluginRegistry()
    registry.register_plugin(plugin_name, module_path)

    # Plugin not loaded yet
    assert plugin_name not in registry._loaded

    # First call triggers import
    handler = registry.get_handler(plugin_name)
    assert handler is not None
    assert callable(handler)
    assert plugin_name in registry._loaded

    # Second call uses cache
    handler2 = registry.get_handler(plugin_name)
    assert handler2 is handler  # Same instance


def test_all_quality_plugins_can_be_loaded():
    """Verify that all 5 quality plugins can be successfully loaded."""
    registry = PluginRegistry()

    # Register all quality plugins
    for plugin_name, module_path in QUALITY_PLUGINS.items():
        registry.register_plugin(plugin_name, module_path)

    # Load all plugins
    handlers = {}
    for plugin_name in QUALITY_PLUGINS:
        handler = registry.get_handler(plugin_name)
        assert handler is not None, f"Failed to load handler for {plugin_name}"
        assert callable(handler), f"Handler for {plugin_name} is not callable"
        handlers[plugin_name] = handler

    # Verify all handlers are loaded
    assert len(handlers) == 5
    assert all(plugin_name in registry._loaded for plugin_name in QUALITY_PLUGINS)


def test_quality_plugins_return_correct_handlers():
    """Verify that quality plugins return handlers from correct module."""
    from noveler.presentation.mcp.adapters import handlers as handler_module

    registry = PluginRegistry()

    # Register and get handlers
    plugin_to_expected = {
        "run_quality_checks": handler_module.run_quality_checks,
        "improve_quality_until": handler_module.improve_quality_until,
        "fix_quality_issues": handler_module.fix_quality_issues,
        "get_issue_context": handler_module.get_issue_context,
        "export_quality_report": handler_module.export_quality_report,
    }

    for plugin_name, expected_handler in plugin_to_expected.items():
        registry.register_plugin(plugin_name, QUALITY_PLUGINS[plugin_name])
        handler = registry.get_handler(plugin_name)

        # Handler should match the expected function
        assert handler is expected_handler, f"Handler mismatch for {plugin_name}"


def test_quality_plugins_with_legacy_fallback():
    """Verify that legacy handlers take precedence over quality plugins."""
    registry = PluginRegistry()

    def legacy_handler(args):
        return {"legacy": True}

    # Register both plugin and legacy for same tool
    registry.register_plugin(
        "run_quality_checks",
        "noveler.presentation.mcp.plugins.run_quality_checks_plugin",
    )
    registry.register_legacy("run_quality_checks", legacy_handler)

    # Should return legacy handler (takes precedence)
    handler = registry.get_handler("run_quality_checks")
    assert handler is legacy_handler

    # Plugin should not be loaded due to legacy fallback
    assert "run_quality_checks" not in registry._loaded


def test_get_registered_tools_includes_quality_plugins():
    """Verify that get_registered_tools includes all quality plugins."""
    registry = PluginRegistry()

    # Register quality plugins
    for plugin_name, module_path in QUALITY_PLUGINS.items():
        registry.register_plugin(plugin_name, module_path)

    # Get registered tools
    tools = registry.get_registered_tools()

    # Should include all quality plugins
    for plugin_name in QUALITY_PLUGINS:
        assert plugin_name in tools