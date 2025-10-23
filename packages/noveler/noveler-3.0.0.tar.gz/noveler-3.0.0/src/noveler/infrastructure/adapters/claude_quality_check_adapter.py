"""Integration adapter for the Claude quality check workflow.

Specification: Claude Code Quality Check Integration System
"""

from pathlib import Path
from typing import Any, Protocol

from noveler.domain.services.claude_quality_analyzer import ClaudeQualityAnalyzer
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.repositories.yaml_claude_quality_prompt_repository import (
    YamlClaudeQualityPromptRepository,
    YamlClaudeQualityResultRepository,
)


class ClaudeQualityCheckUseCase(Protocol):
    """Protocol that defines the Claude quality check use case boundary."""

    def execute(self, request: Any) -> Any:
        """Execute the quality check workflow."""
        ...


class ClaudeQualityCheckServiceFactory:
    """Factory that wires dependencies for the Claude quality check service.

    The factory follows Clean Architecture integration principles and coordinates
    shared infrastructure components.
    """

    @staticmethod
    def create_use_case(project_root: Path | None = None) -> ClaudeQualityCheckUseCase:
        """Assemble a concrete Claude quality check use case.

        Args:
            project_root: Project root path; ``None`` triggers automatic discovery.

        Returns:
            ClaudeQualityCheckUseCase: Fully configured use case instance.
        """
        # プロジェクトルートの解決
        if project_root is None:
            # Configuration Manager経由で取得
            from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager

            config_manager = get_configuration_manager()
            project_root_str = config_manager.get_system_setting("PROJECT_ROOT")
            if project_root_str:
                project_root = Path(project_root_str)
            else:
                # CommonPathServiceによる自動検出
                path_service = create_path_service()
                project_root = path_service.project_root

        # ガイドルートの取得
        from noveler.infrastructure.config.environment_manager import get_environment_manager

        env_manager = get_environment_manager()
        guide_root = env_manager.guide_root

        # リポジトリ作成
        prompt_repository = YamlClaudeQualityPromptRepository(guide_root)
        result_repository = YamlClaudeQualityResultRepository(project_root)

        # ドメインサービス作成
        quality_analyzer = ClaudeQualityAnalyzer()

        # DDD準拠: ファクトリーパターンでApplication層実装を取得
        # Infrastructure層はApplication層に依存しない設計
        try:
            # DIコンテナからApplication層実装を取得
            from noveler.infrastructure.factories.di_container import get_di_container
            container = get_di_container()
            ConcreteUseCase = container.resolve(ClaudeQualityCheckUseCase)
            return ConcreteUseCase(
                prompt_repository=prompt_repository,
                result_repository=result_repository,
                quality_analyzer=quality_analyzer
            )
        except ImportError:
            # フォールバック: NullObjectパターン
            class NullClaudeQualityCheckUseCase:
                """Fallback use case when the concrete implementation cannot be resolved."""

                def execute(self, request: Any) -> Any:
                    """Return a failure payload indicating the use case is unavailable."""
                    return {"success": False, "error": "ClaudeQualityCheckUseCase implementation is missing"}

            return NullClaudeQualityCheckUseCase()

    @staticmethod
    def create_prompt_repository(guide_root: Path | None = None) -> YamlClaudeQualityPromptRepository:
        """Create the repository that stores Claude quality prompts.

        Args:
            guide_root: Guide root path; ``None`` triggers automatic discovery.

        Returns:
            YamlClaudeQualityPromptRepository: Repository instance bound to the guide root.
        """
        if guide_root is None:
            from noveler.infrastructure.config.environment_manager import get_environment_manager

            env_manager = get_environment_manager()
            guide_root = env_manager.guide_root

        return YamlClaudeQualityPromptRepository(guide_root)

    @staticmethod
    def create_result_repository(project_root: Path | None = None) -> YamlClaudeQualityResultRepository:
        """Create the repository that persists Claude quality results.

        Args:
            project_root: Project root path; ``None`` triggers automatic discovery.

        Returns:
            YamlClaudeQualityResultRepository: Repository instance bound to the project root.
        """
        if project_root is None:
            # Configuration Manager経由で取得
            from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager

            config_manager = get_configuration_manager()
            project_root_str = config_manager.get_system_setting("PROJECT_ROOT")
            if project_root_str:
                project_root = Path(project_root_str)
            else:
                path_service = create_path_service()
                project_root = path_service.project_root

        return YamlClaudeQualityResultRepository(project_root)

    @staticmethod
    def create_quality_analyzer() -> ClaudeQualityAnalyzer:
        """Instantiate the domain-level Claude quality analyzer.

        Returns:
            ClaudeQualityAnalyzer: Analyzer responsible for evaluating quality metrics.
        """
        return ClaudeQualityAnalyzer()
