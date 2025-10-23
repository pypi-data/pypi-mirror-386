"""統合リポジトリファクトリー

SPEC-YAML-001: DDD準拠統合基盤拡張
全インフラリポジトリの統一ファクトリー実装
"""

from pathlib import Path
from typing import Any

from noveler.domain.interfaces.settings_repository import ISettingsRepositoryFactory
from noveler.infrastructure.adapters.claude_code_adapter import ClaudeCodeAdapter
from noveler.infrastructure.adapters.claude_plot_adapter import ClaudePlotAdapter
from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter
from noveler.infrastructure.adapters.error_logging_adapter import ErrorLoggingAdapter
from noveler.infrastructure.adapters.plot_template_adapter import PlotTemplateAdapter
from noveler.infrastructure.adapters.settings_repository_adapter import get_settings_repository_factory
from noveler.infrastructure.adapters.yaml_handler_adapter import YAMLHandlerAdapter
from noveler.infrastructure.di.repository_factory import RepositoryFactory
from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager
from noveler.infrastructure.repositories.enhanced_plot_result_repository import EnhancedPlotResultRepository
from noveler.infrastructure.repositories.episode_prompt_repository import EpisodePromptRepository
from noveler.infrastructure.repositories.scene_management_repository import YamlSceneManagementRepository
from noveler.infrastructure.repositories.yaml_chapter_plot_repository import YamlChapterPlotRepository
from noveler.infrastructure.repositories.yaml_foreshadowing_repository import YamlForeshadowingRepository
from noveler.infrastructure.services.staged_prompt_file_service import StagedPromptFileService


class UnifiedRepositoryFactory:
    """統合リポジトリファクトリー

    プロジェクト全体のインフラリポジトリを統一作成・管理
    DDD準拠による依存関係逆転パターンの完全実装
    """

    def __init__(self, project_root: str | Path | None = None) -> None:
        """統合ファクトリー初期化

        Args:
            project_root: プロジェクトルートパス
        """
        self._project_root = str(project_root) if project_root else None
        path_obj = Path(self._project_root) if self._project_root else None
        self._legacy_factory = RepositoryFactory(path_obj)
        self._logger_service: Any | None = None
        self._unit_of_work: Any | None = None

    def create_settings_factory(self) -> ISettingsRepositoryFactory:
        """設定リポジトリファクトリーを作成

        Returns:
            ISettingsRepositoryFactory: 設定リポジトリファクトリー
        """

        return get_settings_repository_factory(self._project_root)

    def create_episode_prompt_repository(self) -> Any:
        """エピソードプロンプトリポジトリを作成

        Returns:
            EpisodePromptRepository: エピソードプロンプトリポジトリ
        """

        return EpisodePromptRepository()

    def create_enhanced_plot_result_repository(self) -> Any:
        """拡張プロット結果リポジトリを作成

        Returns:
            EnhancedPlotResultRepository: 拡張プロット結果リポジトリ
        """

        return EnhancedPlotResultRepository(Path(self._project_root) if self._project_root else None)

    def create_yaml_chapter_plot_repository(self) -> Any:
        """YAML章別プロットリポジトリを作成

        Returns:
            YamlChapterPlotRepository: YAML章別プロットリポジトリ
        """

        # プロジェクトルートの取得

        config_manager = get_configuration_manager()
        project_root_str = config_manager.get_system_setting(
            "PROJECT_ROOT", "/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/10_Fランク魔法使いはDEBUGログを読む"
        )
        project_root = Path(project_root_str)
        return YamlChapterPlotRepository(project_root)

    def create_scene_management_repository(self) -> Any:
        """シーン管理リポジトリを作成

        Returns:
            YamlSceneManagementRepository: シーン管理リポジトリ
        """

        return YamlSceneManagementRepository()

    def create_yaml_foreshadowing_repository(self) -> Any:
        """YAML伏線リポジトリを作成

        Returns:
            YamlForeshadowingRepository: YAML伏線リポジトリ
        """

        return YamlForeshadowingRepository()

    def create_claude_plot_adapter(self) -> Any:
        """Claudeプロットアダプターを作成

        Returns:
            ClaudePlotAdapter: Claudeプロットアダプター
        """

        return ClaudePlotAdapter()

    def create_plot_template_adapter(self) -> Any:
        """プロットテンプレートアダプターを作成

        Returns:
            PlotTemplateAdapter: プロットテンプレートアダプター
        """

        return PlotTemplateAdapter()

    def create_error_logging_adapter(self) -> Any:
        """エラーロギングアダプターを作成

        Returns:
            ErrorLoggingAdapter: エラーロギングアダプター
        """

        return ErrorLoggingAdapter()

    def create_yaml_handler_adapter(self) -> Any:
        """YAMLハンドラーアダプターを作成

        Returns:
            YAMLHandlerAdapter: YAMLハンドラーアダプター
        """

        return YAMLHandlerAdapter()

    def create_claude_code_adapter(self) -> Any:
        """Claude Codeアダプターを作成

        Returns:
            ClaudeCodeAdapter: Claude Codeアダプター
        """

        return ClaudeCodeAdapter()

    def create_staged_prompt_file_service(self) -> Any:
        """段階的プロンプトファイルサービスを作成

        Returns:
            StagedPromptFileService: 段階的プロンプトファイルサービス
        """


        project_root = Path(self._project_root) if self._project_root else Path.cwd()
        return StagedPromptFileService(project_root)

    def create_console_service(self) -> Any:
        """コンソールサービスを作成

        Returns:
            ConsoleServiceAdapter: コンソールサービスアダプター
        """

        return ConsoleServiceAdapter()

    # -- Compatibility helpers for DI layer ---------------------------------

    def get_logger_service(self) -> Any:
        """Provide a logger service compatible with use case factory expectations."""
        if self._logger_service is None:
            from noveler.infrastructure.adapters.domain_logger_adapter import DomainLoggerAdapter

            self._logger_service = DomainLoggerAdapter()
        return self._logger_service

    def get_unit_of_work(self) -> Any:
        """Provide a UnitOfWork instance leveraging the legacy repository factory."""
        if self._unit_of_work is None:
            self._unit_of_work = self._legacy_factory.get_unit_of_work()
        return self._unit_of_work


# シングルトンファクトリー管理
_global_factory: UnifiedRepositoryFactory | None = None


def get_unified_repository_factory(project_root: str | Path | None = None) -> UnifiedRepositoryFactory:
    """統合リポジトリファクトリーのグローバル取得

    Args:
        project_root: プロジェクトルートパス

    Returns:
        UnifiedRepositoryFactory: 統合リポジトリファクトリー
    """
    global _global_factory  # noqa: PLW0603

    if _global_factory is None or (project_root and _global_factory._project_root != str(project_root)):
        _global_factory = UnifiedRepositoryFactory(project_root)

    return _global_factory


def reset_unified_repository_factory() -> None:
    """統合リポジトリファクトリーのリセット（テスト用）"""
    global _global_factory  # noqa: PLW0603
    _global_factory = None
