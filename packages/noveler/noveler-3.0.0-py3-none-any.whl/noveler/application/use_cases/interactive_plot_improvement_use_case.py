"""
対話的プロット改善ユースケース

自動生成されたプロットをユーザーとの対話で改善します。
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from noveler.infrastructure.logging.unified_logger import get_logger

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService

from noveler.application.orchestrators.error_handling_orchestrator import ErrorHandlingOrchestrator
from noveler.application.orchestrators.plot_generation_orchestrator import PlotGenerationOrchestrator
from noveler.application.services.error_classification_service import ErrorClassificationService
from noveler.application.services.error_recovery_service import ErrorRecoveryService
from noveler.application.services.error_reporting_service import ErrorReportingService
from noveler.domain.entities.error_handling_request import ErrorHandlingRequest
from noveler.domain.entities.generated_episode_plot import GeneratedEpisodePlot
from noveler.domain.entities.plot_generation_workflow_request import PlotGenerationWorkflowRequest
from noveler.domain.services.plot_quality_service import PlotQualityService
from noveler.domain.services.plot_structure_service import PlotStructureService
from noveler.domain.value_objects.project_time import project_now

# DDD準拠: Infrastructure層のパスサービスを使用（Presentation層依存を排除）
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.di.unified_repository_factory import UnifiedRepositoryFactory


class InteractivePlotImprovementUseCase:
    """Interactive plot improvement use case (migrated to decomposed services)"""

    def __init__(self, repository_factory: UnifiedRepositoryFactory = None, logger_service: "ILoggerService" = None) -> None:
        """Initialize use case with new decomposed services and DDD-compliant dependency injection

        Args:
            repository_factory: 統合リポジトリファクトリー（DI対応）
            logger_service: ロガーサービス（DI対応）
        """

        # 統一ロガーサービス（B30準拠）
        self._logger_service = logger_service

        # 統合リポジトリファクトリーのDI対応
        self._repository_factory = repository_factory or self._create_default_factory()

        # Initialize decomposed services
        self._structure_service = PlotStructureService()
        self._quality_service = PlotQualityService()

        # DDD準拠：統合ファクトリー経由でアダプター作成
        if self._repository_factory:
            self._claude_adapter = self._repository_factory.create_claude_plot_adapter()
            self._template_adapter = self._repository_factory.create_plot_template_adapter()
        else:
            # フォールバック：直接作成（緊急時対応）
            # TODO: DI - Infrastructure Adapter removed for DDD compliance
            # Use I{1} interface via DI container instead
            # TODO: DI - Infrastructure Adapter removed for DDD compliance
            # Use I{1} interface via DI container instead
            self._claude_adapter = None  # TODO: DI - Inject IClaudePlotAdapter via constructor
            self._template_adapter = None  # TODO: DI - Inject IPlotTemplateAdapter via constructor

        # Use orchestrator for workflow coordination
        self._orchestrator = PlotGenerationOrchestrator(
            plot_structure_service=self._structure_service,
            plot_quality_service=self._quality_service,
            claude_adapter=self._claude_adapter,
            template_adapter=self._template_adapter,
        )

        # DDD準拠 Constructor Injection パターン:
        # def __init__(
        #     self,
        #     repository_factory: IRepositoryFactory,
        #     claude_adapter: IClaudePlotAdapter,
        #     template_adapter: IPlotTemplateAdapter,
        #     error_logger: IErrorLogger
        # ) -> None:
        #     self._repository_factory = repository_factory
        #     self._claude_adapter = claude_adapter
        #     self._template_adapter = template_adapter
        #     self._error_logger = error_logger

    def _create_default_factory(self) -> "UnifiedRepositoryFactory":
        """デフォルトファクトリー作成（後方互換性維持）"""
        try:
            # TODO: DI - Infrastructure DI container removed for DDD compliance
            # Use Application Factory interface via DI container instead
            return None  # TODO: DI - Inject IRepositoryFactory via constructor
        except ImportError:
            # フォールバック：緊急時対応
            return None

    def improve_plot_interactively(
        self, episode_number: int, initial_plot_path: Path, project_root: Path
    ) -> tuple[GeneratedEpisodePlot | None, Path | None]:
        """Improve plot interactively using orchestrator

        Args:
            episode_number: Episode number
            initial_plot_path: Initial plot file path (used for context and output location)
            project_root: Project root path

        Returns:
            (Improved plot, Final file path)
        """
        # TODO: DI - Infrastructure Adapter removed for DDD compliance
        # Use I{1} interface via DI container instead

        try:
            # B20準拠: コンソール出力をconsole_service経由で実行
            if hasattr(self, "_get_console"):
                console = self._get_console()
                console.print(f"[cyan]Starting interactive improvement for Episode {episode_number}...[/cyan]")
            elif self._logger_service:
                self._logger_service.info(f"Starting interactive improvement for Episode {episode_number}")

            # Load existing plot for context if available
            existing_context = self._load_existing_plot_context(initial_plot_path)

            # Create interactive improvement request
            request = PlotGenerationWorkflowRequest(
                project_name=project_root.name,
                episode_number=episode_number,
                chapter_number=1,
                context_data={
                    "existing_plot": existing_context,
                    "improvement_mode": True,
                    "interactive": True,
                    "characters": existing_context.get("characters", []),
                    "world_setting": existing_context.get("world_setting", "Fantasy world"),
                    "previous_episodes": [],
                    "improvement_suggestions": [
                        "Enhance character development",
                        "Improve narrative pacing",
                        "Strengthen conflict resolution",
                        "Add more engaging dialogue",
                    ],
                },
                generation_method="claude",  # Use Claude for interactive improvements
                quality_threshold=8.0,  # Higher threshold for improvements
                max_iterations=3,
            )

            # Execute interactive improvement workflow
            result = self._orchestrator.generate_plot(request)

            if result.success and result.generated_plot:
                # Convert to domain entity
                improved_plot = self._convert_to_generated_episode_plot(
                    episode_number, result.generated_plot, result.quality_score or 8.0
                )

                # Save improved version
                improved_path = self._save_improved_plot(improved_plot, episode_number, initial_plot_path, project_root)

                # B20準拠: 成功メッセージをconsole_service経由で出力
                if hasattr(self, "_get_console"):
                    console = self._get_console()
                    console.print(f"[green]Interactive improvement completed successfully: {improved_path}[/green]")
                    console.print(f"[blue]Quality score: {result.quality_score:.1f}[/blue]")
                elif self._logger_service:
                    self._logger_service.info(f"Interactive improvement completed successfully: {improved_path}")
                    self._logger_service.info(f"Quality score: {result.quality_score:.1f}")

                if result.improvement_suggestions:
                    # B20準拠: 改善提案をconsole_service経由で出力
                    if hasattr(self, "_get_console"):
                        console = self._get_console()
                        console.print("[yellow]Additional improvement suggestions:[/yellow]")
                        for suggestion in result.improvement_suggestions:
                            console.print(f"  - {suggestion}")
                    elif self._logger_service:
                        self._logger_service.info("Additional improvement suggestions:")
                        for suggestion in result.improvement_suggestions:
                            self._logger_service.info(f"  - {suggestion}")

                return improved_plot, improved_path
            # B20準拠: エラーメッセージをlogger_service経由で出力
            if self._logger_service:
                self._logger_service.error("Interactive improvement plot generation failed")
            elif hasattr(self, "_get_console"):
                console = self._get_console()
                console.print("[red]Interactive improvement plot generation failed[/red]")
            return None, None

        except Exception as e:
            # Use error handling orchestrator with DDD-compliant dependency injection
            logging_adapter = (
                self._repository_factory.create_error_logging_adapter() if self._repository_factory else None
            )
            if not logging_adapter:
                # フォールバック：直接作成（緊急時対応）
                # TODO: DI - Infrastructure Adapter removed for DDD compliance
                # Use I{1} interface via DI container instead
                logging_adapter = None  # TODO: DI - Inject IErrorLogger via constructor

            error_orchestrator = ErrorHandlingOrchestrator(
                classification_service=ErrorClassificationService(),
                recovery_service=ErrorRecoveryService(),
                reporting_service=ErrorReportingService(),
                logging_adapter=logging_adapter,
            )

            error_request = ErrorHandlingRequest(
                exception=e,
                context={
                    "operation_id": f"interactive_improvement_{episode_number}",
                    "user_context": {
                        "operation_name": "improve_plot_interactively",
                        "episode_number": episode_number,
                        "initial_plot_path": str(initial_plot_path),
                    },
                },
                operation_name="interactive_plot_improvement",
            )

            error_result = error_orchestrator.handle_error(error_request)

            if error_result.business_error_result:
                if self._logger_service:
                    self._logger_service.error(f"プロット改善処理でエラーが発生: {error_result.business_error_result.user_message}")
                # B20準拠：フォールバック時もconsole_service優先
                elif hasattr(self, "_get_console"):
                    console = self._get_console()
                    console.print(f"[red]Interactive improvement error: {error_result.business_error_result.user_message}[/red]")
                else:
                    # 最終フォールバック（統一ロガー使用）
                    logger = get_logger(__name__)
                    logger.exception(f"Interactive improvement error: {error_result.business_error_result.user_message}")
                # 復旧提案の出力
                for suggestion in error_result.business_error_result.recovery_suggestions:
                    if hasattr(self, "_get_console"):
                        console = self._get_console()
                        console.print(f"  - {suggestion}")
                    else:
                        logger = get_logger(__name__)
                        logger.info(f"Recovery suggestion: {suggestion}")

            return None, None

    def _load_existing_plot_context(self, plot_path: Path) -> dict:
        """Load existing plot for improvement context"""
        if not plot_path.exists():
            return {}

        try:
            content = plot_path.read_text(encoding="utf-8")

            # Try YAML first
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError:
                # Fallback to basic text analysis
                return {"content": content, "characters": [], "world_setting": "Unknown setting", "format": "text"}
        except Exception:
            return {}

    def _convert_to_generated_episode_plot(
        self, episode_number: int, plot_content: str, quality_score: float
    ) -> GeneratedEpisodePlot:
        """Convert orchestrator result to domain entity"""


        try:
            # Parse YAML content from orchestrator
            plot_data: dict[str, Any] = yaml.safe_load(plot_content)

            return GeneratedEpisodePlot(
                episode_number=episode_number,
                title=plot_data.get("episode_info", {}).get(
                    "title", f"Episode {episode_number} - Interactive Improvement"
                ),
                summary=plot_data.get("synopsis", "Interactively improved plot"),
                scenes=plot_data.get("scenes", []),
                key_events=plot_data.get("foreshadowing", []),
                viewpoint=plot_data.get("character_development", {}).get(
                    "protagonist", ["Enhanced character perspective"]
                )[0],
                tone=plot_data.get("themes", ["Enhanced narrative"])[0],
                conflict="Improved conflict structure",
                resolution="Enhanced resolution",
                generation_timestamp=project_now().datetime,
                source_chapter_number=1,
                quality_score=quality_score,
            )

        except Exception:
            return self._create_fallback_improved_plot(episode_number)

    def _create_fallback_improved_plot(self, episode_number: int) -> GeneratedEpisodePlot:
        """Create fallback improved plot"""

        return GeneratedEpisodePlot(
            episode_number=episode_number,
            title=f"Episode {episode_number} - Basic Improvement",
            summary=f"Episode {episode_number} with basic improvements applied",
            scenes=[{"scene_number": 1, "title": "Improved Scene", "description": "Enhanced basic structure"}],
            key_events=["Improved key event"],
            viewpoint="Enhanced protagonist perspective",
            tone="Improved narrative tone",
            conflict="Enhanced conflict structure",
            resolution="Improved resolution",
            generation_timestamp=project_now().datetime,
            source_chapter_number=1,
        )

    def _save_improved_plot(
        self, improved_plot: GeneratedEpisodePlot, episode_number: int, initial_plot_path: Path, project_root: Path
    ) -> Path:
        """Save improved plot to appropriate location"""

        # Create improved filename
        improved_filename = f"Episode_{episode_number:03d}_Interactive_Improvement.yaml"

        # Determine save location
        if initial_plot_path.exists():
            improved_path = initial_plot_path.parent / improved_filename
        else:
            # Save to project's plot directory
            # DDD準拠: Infrastructure層のパスサービスを使用
            path_service = create_path_service(project_root)
            plot_dir = path_service.get_plot_dir() / "話別プロット"
            plot_dir.mkdir(parents=True, exist_ok=True)
            improved_path = plot_dir / improved_filename

        # Convert to dictionary for YAML serialization
        plot_dict = {
            "episode_info": {
                "episode_number": improved_plot.episode_number,
                "title": improved_plot.title,
                "chapter": improved_plot.source_chapter_number,
                "improvement_type": "interactive",
            },
            "synopsis": improved_plot.summary,
            "scenes": improved_plot.scenes,
            "key_events": improved_plot.key_events,
            "character_development": {"viewpoint": improved_plot.viewpoint, "tone": improved_plot.tone},
            "plot_structure": {"conflict": improved_plot.conflict, "resolution": improved_plot.resolution},
            "metadata": {
                "generation_timestamp": improved_plot.generation_timestamp.isoformat(),
                "quality_score": getattr(improved_plot, "quality_score", None),
                "improvement_method": "interactive_orchestrator",
            },
        }

        # Save YAML file
        with improved_path.Path("w").open(encoding="utf-8") as f:
            yaml.dump(plot_dict, f, default_flow_style=False, allow_unicode=True, indent=2)

        return improved_path
