# File: src/noveler/presentation/mcp/repository_factories.py
# Purpose: Factory functions for creating repository instances with DI
# Context: Part of MCP server refactoring (B20 project, SPEC-MCP-001)

"""Repository factory functions for MCP server.

This module provides factory functions for creating repository instances
with proper dependency injection. Extracted from server_runtime.py (lines 247-323)
as part of SOLID-SRP compliance (B20 §3).

Functions:
    create_yaml_prompt_repository: Create YamlPromptRepository for A28 system
    create_episode_repository: Create EpisodeRepository for episode data
    create_plot_repository: Create PlotRepository for plot management

Preconditions:
    - project_root must exist and be accessible
    - Required repository modules must be importable

Side Effects:
    - Console warnings on repository initialization failures
    - Returns None on errors (fallback mode)

Raises:
    FileNotFoundError: If project root does not exist
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.infrastructure.repositories.ruamel_yaml_prompt_repository import RuamelYamlPromptRepository
    from noveler.infrastructure.adapters.file_episode_repository import FileEpisodeRepository
    from noveler.infrastructure.repositories.yaml_plot_repository import YamlPlotRepository

from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter

# Shared console instance for error reporting
_console = ConsoleServiceAdapter()


def create_yaml_prompt_repository(project_root: Path) -> "RuamelYamlPromptRepository | None":
    """Create YAML prompt repository for A28 system.

    A28 provides 8,000-character detailed prompt system for high-quality writing.

    Args:
        project_root: Project root directory path

    Returns:
        RuamelYamlPromptRepository instance, or None on initialization failure

    Raises:
        Never raises - errors converted to warnings with None return

    Side Effects:
        - Prints error/warning messages to console on failures
        - Falls back to None (degraded mode) on A30 template not found
    """
    _validate_project_root(project_root)

    try:
        from noveler.infrastructure.repositories.ruamel_yaml_prompt_repository import RuamelYamlPromptRepository

        # Resolve A30 guide template path
        guide_template_path = project_root / "docs" / "A30_執筆ガイド.yaml"
        fallback_path = Path(__file__).resolve().parents[4] / "docs" / "A30_執筆ガイド.yaml"

        if not guide_template_path.exists():
            if not fallback_path.exists():
                _console.print_error("❌ A30ガイドテンプレート未発見")
                _console.print_warning(f"   検索パス1: {guide_template_path}")
                _console.print_warning(f"   検索パス2: {fallback_path}")
                _console.print_warning("📝 A28プロンプトシステム使用不可 - 精度が低下します")
                _console.print_info("💡 セットアップ: docs/A30_執筆ガイド.yaml を配置してください")
                return None

            # Fallback: Use default path outside project
            guide_template_path = fallback_path
            _console.print_info(f"📄 A30ガイド使用: {guide_template_path}")

        return RuamelYamlPromptRepository(guide_template_path=guide_template_path)
    except Exception as e:
        _console.print_warning(f"⚠️ YamlPromptRepository初期化失敗: {e}")
        _console.print_warning("📝 簡易YAMLフォールバックモードで実行します（精度低下）")
        return None


def create_episode_repository(project_root: Path) -> "FileEpisodeRepository | None":
    """Create episode repository for episode data management.

    Args:
        project_root: Project root directory path

    Returns:
        FileEpisodeRepository instance, or None on initialization failure

    Raises:
        Never raises - errors converted to warnings with None return

    Side Effects:
        - Prints warning message to console on failures
        - Episode data stored in `temp/ddd_repo` directory
    """
    _validate_project_root(project_root)

    try:
        from noveler.infrastructure.adapters.file_episode_repository import FileEpisodeRepository

        # Episode data storage directory
        episode_data_dir = project_root / "temp" / "ddd_repo"
        return FileEpisodeRepository(base_dir=episode_data_dir)
    except Exception as e:
        _console.print_warning(f"⚠️ EpisodeRepository初期化失敗: {e}")
        return None


def create_plot_repository(project_root: Path) -> "YamlPlotRepository | None":
    """Create plot repository for plot management.

    Args:
        project_root: Project root directory path

    Returns:
        YamlPlotRepository instance, or None on initialization failure

    Raises:
        Never raises - errors converted to warnings with None return

    Side Effects:
        - Prints warning message to console on failures
    """
    _validate_project_root(project_root)

    try:
        from noveler.infrastructure.repositories.yaml_plot_repository import YamlPlotRepository

        return YamlPlotRepository(base_path=project_root)
    except Exception as e:
        _console.print_warning(f"⚠️ PlotRepository初期化失敗: {e}")
        return None


def _validate_project_root(project_root: Path) -> None:
    """Validate project root exists and is accessible.

    Args:
        project_root: Project root directory path

    Raises:
        FileNotFoundError: If project root does not exist
    """
    if not project_root.exists():
        raise FileNotFoundError(f"Project root not found: {project_root}")
    if not project_root.is_dir():
        raise NotADirectoryError(f"Project root is not a directory: {project_root}")
