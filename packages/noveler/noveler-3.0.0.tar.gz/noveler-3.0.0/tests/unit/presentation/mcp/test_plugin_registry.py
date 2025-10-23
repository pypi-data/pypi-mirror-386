#!/usr/bin/env python3
# File: tests/unit/presentation/mcp/test_plugin_registry.py
# Purpose: Unit tests for PluginRegistry class
# Context: Phase 1-5 plugin architecture - validate lazy loading, error handling, and auto-discovery
"""Tests for PluginRegistry."""

from pathlib import Path

import pytest

from noveler.presentation.mcp.plugin_base import MCPToolPlugin
from noveler.presentation.mcp.plugin_registry import PluginRegistry


class MockPlugin(MCPToolPlugin):
    """Mock plugin for testing."""

    def get_name(self) -> str:
        return "mock_tool"

    def get_handler(self):
        def mock_handler(args):
            return {"success": True, "args": args}

        return mock_handler


def test_register_plugin_does_not_import():
    """Verify that register_plugin does not trigger import."""
    registry = PluginRegistry()

    # Register a non-existent module (should not raise error)
    registry.register_plugin("fake_tool", "nonexistent.module.path")

    # Should succeed because no import happens yet
    assert "fake_tool" in registry._plugins


def test_get_handler_lazy_loads_plugin():
    """Verify that get_handler performs lazy loading on first access."""
    registry = PluginRegistry()
    registry.register_plugin(
        "check_readability",
        "noveler.presentation.mcp.plugins.check_readability_plugin",
    )

    # Plugin not loaded yet
    assert "check_readability" not in registry._loaded

    # First call triggers import
    handler = registry.get_handler("check_readability")
    assert handler is not None
    assert "check_readability" in registry._loaded

    # Second call uses cache
    handler2 = registry.get_handler("check_readability")
    assert handler2 is not None


def test_get_handler_returns_none_for_unknown_tool():
    """Verify that get_handler returns None for unregistered tools."""
    registry = PluginRegistry()

    handler = registry.get_handler("unknown_tool")
    assert handler is None


def test_get_handler_catches_import_error(capsys):
    """Verify that get_handler catches ImportError and returns None."""
    registry = PluginRegistry()
    registry.register_plugin("bad_tool", "nonexistent.module.that.does.not.exist")

    # Should return None and print warning
    handler = registry.get_handler("bad_tool")
    assert handler is None

    # Check warning message
    captured = capsys.readouterr()
    assert "Warning: Failed to load plugin 'bad_tool'" in captured.out
    assert "nonexistent.module.that.does.not.exist" in captured.out


def test_get_handler_catches_attribute_error(capsys):
    """Verify that get_handler catches AttributeError when create_plugin missing."""
    registry = PluginRegistry()
    # Register a valid module but without create_plugin function
    registry.register_plugin("bad_plugin", "noveler.presentation.mcp.plugin_base")

    handler = registry.get_handler("bad_plugin")
    assert handler is None

    # Check warning message
    captured = capsys.readouterr()
    assert "Warning: Failed to load plugin 'bad_plugin'" in captured.out


def test_legacy_fallback_takes_precedence():
    """Verify that legacy handlers take precedence over plugins."""
    registry = PluginRegistry()

    def legacy_handler(args):
        return {"legacy": True}

    # Register both plugin and legacy
    registry.register_plugin(
        "check_readability",
        "noveler.presentation.mcp.plugins.check_readability_plugin",
    )
    registry.register_legacy("check_readability", legacy_handler)

    # Should return legacy handler
    handler = registry.get_handler("check_readability")
    assert handler is legacy_handler
    result = handler({})
    assert result == {"legacy": True}


def test_unregister_plugin_removes_from_registry():
    """Verify that unregister_plugin removes plugin."""
    registry = PluginRegistry()
    registry.register_plugin("test_tool", "some.module.path")

    assert "test_tool" in registry._plugins

    registry.unregister_plugin("test_tool")

    assert "test_tool" not in registry._plugins


def test_clear_cache_removes_loaded_plugins():
    """Verify that clear_cache removes loaded plugins."""
    registry = PluginRegistry()
    registry.register_plugin(
        "check_readability",
        "noveler.presentation.mcp.plugins.check_readability_plugin",
    )

    # Load plugin
    registry.get_handler("check_readability")
    assert "check_readability" in registry._loaded

    # Clear cache
    registry.clear_cache()
    assert "check_readability" not in registry._loaded


def test_get_registered_tools_returns_all_tools():
    """Verify that get_registered_tools returns both plugins and legacy."""
    registry = PluginRegistry()

    def dummy_handler(args):
        return {}

    registry.register_plugin("plugin_tool", "some.module")
    registry.register_legacy("legacy_tool", dummy_handler)

    tools = registry.get_registered_tools()
    assert tools == {"plugin_tool", "legacy_tool"}


def test_plugin_handler_execution():
    """Verify that loaded plugin handler can be executed."""
    registry = PluginRegistry()
    registry.register_plugin(
        "check_readability",
        "noveler.presentation.mcp.plugins.check_readability_plugin",
    )

    handler = registry.get_handler("check_readability")
    assert handler is not None
    assert callable(handler)

    # Note: We don't execute the handler here because it requires
    # actual file paths and dependencies. This test just verifies
    # that the handler is callable.


def test_auto_discover_plugins_from_directory():
    """Phase 5: Verify that auto_discover_plugins scans and registers plugins."""
    registry = PluginRegistry()

    # Use actual plugins directory
    plugins_dir = Path(__file__).parent.parent.parent.parent.parent / "src" / "noveler" / "presentation" / "mcp" / "plugins"

    # Auto-discover plugins
    count = registry.auto_discover_plugins(plugins_dir, "noveler.presentation.mcp.plugins")

    # Should discover 49 plugins (18 original + 3 artifact + 6 utility + 4 progressive check + 6 writing workflow + 7 design + 3 langsmith + 1 misc + 1 project init from Phase 7)
    assert count == 49

    # Verify some known plugins are registered
    tools = registry.get_registered_tools()
    assert "check_readability" in tools
    assert "run_quality_checks" in tools
    # Phase 7: Artifact tools (3)
    assert "fetch_artifact" in tools
    assert "list_artifacts" in tools
    assert "write_file" in tools
    # Phase 7: Utility tools (6)
    assert "convert_cli_to_json" in tools
    assert "validate_json_response" in tools
    assert "get_file_reference_info" in tools
    assert "get_file_by_hash" in tools
    assert "check_file_changes" in tools
    assert "list_files_with_hashes" in tools
    # Phase 7: Progressive check tools (4)
    assert "get_check_tasks" in tools
    assert "execute_check_step" in tools
    assert "get_check_status" in tools
    assert "get_check_history" in tools
    # Phase 7: Writing workflow tools (6)
    assert "get_writing_tasks" in tools
    assert "execute_writing_step" in tools
    assert "get_task_status" in tools
    assert "enhanced_get_writing_tasks" in tools
    assert "enhanced_execute_writing_step" in tools
    assert "enhanced_resume_from_partial_failure" in tools
    assert "polish_manuscript" in tools
    assert "backup_management" in tools
    # Phase 7: Design tools (7)
    assert "design_conversations" in tools
    assert "track_emotions" in tools
    assert "design_scenes" in tools
    assert "design_senses" in tools
    assert "manage_props" in tools
    assert "get_conversation_context" in tools
    assert "export_design_data" in tools
    # Phase 7: LangSmith tools (3)
    assert "langsmith_generate_artifacts" in tools
    assert "langsmith_apply_patch" in tools
    assert "langsmith_run_verification" in tools
    # Phase 7: Misc tools (1)
    assert "status" in tools


def test_auto_discover_plugins_nonexistent_directory():
    """Phase 5: Verify that auto_discover_plugins handles nonexistent directory.

    Note: 存在しないディレクトリを渡してエラーが発生しないことを確認する
    負のテストケース。PluginRegistry は存在チェックを行い、存在しない場合は
    0を返すため、実ファイルシステムへのアクセスは最小限。
    """
    registry = PluginRegistry()

    # 存在しないディレクトリ (負のテストケース)
    nonexistent_dir = Path("/nonexistent/directory")

    # Should return 0 and not raise error
    count = registry.auto_discover_plugins(nonexistent_dir, "some.module")
    assert count == 0


def test_auto_discover_plugins_empty_directory(tmp_path):
    """Phase 5: Verify that auto_discover_plugins handles empty directory."""
    registry = PluginRegistry()

    # Should return 0 for empty directory
    count = registry.auto_discover_plugins(tmp_path, "some.module")
    assert count == 0


def test_auto_discover_plugins_naming_convention(tmp_path):
    """Phase 5: Verify that auto_discover_plugins follows naming convention."""
    registry = PluginRegistry()

    # Create test files in a fresh subdirectory to avoid interference
    test_dir = tmp_path / "test_plugins"
    test_dir.mkdir()

    (test_dir / "valid_plugin.py").touch()
    (test_dir / "also_valid_plugin.py").touch()
    (test_dir / "normal_file.py").touch()  # Does not end with _plugin.py - should not match

    # Auto-discover - should only find files ending with _plugin.py
    count = registry.auto_discover_plugins(test_dir, "test.module")

    # Should discover 2 plugins (valid_plugin and also_valid_plugin)
    assert count == 2

    tools = registry.get_registered_tools()
    assert "valid" in tools
    assert "also_valid" in tools
    assert "normal_file" not in tools


def test_warmup_preloads_all_plugins():
    """Phase 6: Verify that warmup preloads all registered plugins."""
    registry = PluginRegistry()

    # Register multiple plugins
    registry.register_plugin("check_readability", "noveler.presentation.mcp.plugins.check_readability_plugin")
    registry.register_plugin("run_quality_checks", "noveler.presentation.mcp.plugins.run_quality_checks_plugin")

    # Verify nothing is loaded yet
    assert len(registry._loaded) == 0

    # Warm up all plugins
    warmed = registry.warmup()

    # Should have warmed up 2 plugins
    assert warmed == 2
    assert len(registry._loaded) == 2
    assert "check_readability" in registry._loaded
    assert "run_quality_checks" in registry._loaded


def test_warmup_specific_plugins():
    """Phase 6: Verify that warmup can target specific plugins."""
    registry = PluginRegistry()

    # Register multiple plugins
    registry.register_plugin("check_readability", "noveler.presentation.mcp.plugins.check_readability_plugin")
    registry.register_plugin("run_quality_checks", "noveler.presentation.mcp.plugins.run_quality_checks_plugin")
    registry.register_plugin("polish_manuscript", "noveler.presentation.mcp.plugins.polish_manuscript_plugin")

    # Warm up only specific plugins
    warmed = registry.warmup(["check_readability", "polish_manuscript"])

    # Should have warmed up 2 out of 3 plugins
    assert warmed == 2
    assert "check_readability" in registry._loaded
    assert "polish_manuscript" in registry._loaded
    assert "run_quality_checks" not in registry._loaded


def test_warmup_skips_already_loaded():
    """Phase 6: Verify that warmup skips already loaded plugins."""
    registry = PluginRegistry()

    registry.register_plugin("check_readability", "noveler.presentation.mcp.plugins.check_readability_plugin")

    # Load plugin manually first
    registry.get_handler("check_readability")
    assert "check_readability" in registry._loaded

    # Warm up should skip already loaded plugin
    warmed = registry.warmup()
    assert warmed == 0  # Nothing new to warm up