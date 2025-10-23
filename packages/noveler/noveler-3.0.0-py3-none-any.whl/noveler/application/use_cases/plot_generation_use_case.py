"""Application.use_cases.plot_generation_use_case
Where: Application use case generating plots from prompts and context.
What: Runs plot generation services, evaluates outputs, and persists results.
Why: Centralises plot generation steps so callers receive consistent outcomes.
"""

from typing import Any


from pathlib import Path
from typing import TYPE_CHECKING

from noveler.domain.value_objects.project_time import project_now

if TYPE_CHECKING:
    from noveler.application.orchestrators.plot_generation_orchestrator import PlotGenerationWorkflowResult
    from noveler.domain.entities.chapter_plot import ChapterPlot
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.infrastructure.di.unified_repository_factory import UnifiedRepositoryFactory
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.entities.generated_episode_plot import GeneratedEpisodePlot
from noveler.infrastructure.repositories.yaml_quality_record_repository import YamlQualityRecordRepository


def load_previous_preview_context(
    project_root: Path, episode_number: int, repository_cls: type[YamlQualityRecordRepository] = YamlQualityRecordRepository
) -> dict[str, Any] | None:
    """Load preview metadata for the previous episode from quality records."""

    if episode_number <= 1:
        return None

    try:
        repository = repository_cls(project_root)
        record = repository.find_by_project(project_root.name)
        if record is None:
            return None

        entry = record.get_latest_for_episode(episode_number - 1)
        if entry is None or not entry.metadata:
            return None

        metadata = entry.metadata or {}
        preview_payload: dict[str, Any] = {
            "preview": metadata.get("preview", {}),
            "quality": metadata.get("quality", {}),
            "source": metadata.get("source", {}),
            "config": metadata.get("config", {}),
        }

        preview_text = metadata.get("preview_text")
        if preview_text:
            preview_payload["preview_text"] = preview_text

        try:
            preview_payload["score"] = entry.quality_result.overall_score.to_float()
        except Exception:
            pass

        return preview_payload
    except Exception:
        return None


# DDD準拠: Infrastructure依存を除去
# from noveler.infrastructure.services.character_development_service import get_character_development_service


class PlotGenerationUseCase(AbstractUseCase[dict, GeneratedEpisodePlot]):
    """プロット生成ユースケース - B20準拠DI実装"""

    # テスト互換性: クラス属性としてオーケストレーターを公開
    # unittest.mock.patch で Patch しやすいようにする
    _orchestrator = None  # type: ignore[assignment]

    def __init__(self,
        logger_service: "ILoggerService" = None,
        unit_of_work: "IUnitOfWork" = None,
        **kwargs) -> None:
        """初期化 - B20準拠DI実装

        Args:
            logger_service: ロガーサービス
            unit_of_work: Unit of Work
            **kwargs: AbstractUseCaseの引数
        """
        super().__init__(**kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work

        # Domain services initialization
        from noveler.domain.services.plot_quality_service import PlotQualityService
        from noveler.domain.services.plot_structure_service import PlotStructureService

        self._structure_service = PlotStructureService()
        self._quality_service = PlotQualityService()

        # B20準拠: アダプター作成は暫定的に後回し
        # TODO: アダプターもDI経由で注入するように修正が必要
        self._claude_adapter = None
        self._template_adapter = None
        self._quality_record_repository_cls = YamlQualityRecordRepository
        self._latest_preview_context: dict[str, Any] | None = None

        # Use orchestrator for workflow coordination - 暫定的にNone許可
        # オーケストレーターは遅延初期化（クラス属性パッチと両立させる）
        # self._orchestrator は必要時に _get_orchestrator() で生成

        # DDD準拠 Constructor Injection パターン:
        # def __init__(self,
        #   logger_service: "ILoggerService" = None,
        #   unit_of_work: "IUnitOfWork" = None,
        #   **kwargs) -> None:
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

    # 後方互換のための簡易execute実装（テストでは未使用）
    def execute(self, request: dict) -> "GeneratedEpisodePlot | None":
        """後方互換execute: generate_episode_plot_autoに委譲"""
        episode_number = request.get("episode_number", 1)
        chapter_plot_info = request.get("chapter_plot_info", {})
        return self.generate_episode_plot_auto(episode_number, chapter_plot_info)

    def generate_episode_plot_auto(
        self,
        episode_number: int,
        chapter_plot_info: dict,
        force_regenerate: bool = False,
        enable_prompt_save: bool = True,
    ) -> GeneratedEpisodePlot | None:
        """Complete automated plot generation with enhanced prompt saving

        SPEC-PROMPT-SAVE-001統合: 詳細化プロンプト生成・保存機能追加

        Args:
            episode_number: Episode number
            chapter_plot_info: Chapter plot information (inference handled by orchestrator)
            force_regenerate: Force regeneration flag
            enable_prompt_save: Enable prompt saving to 60_プロンプト/話別プロット/

        Returns:
            Generated plot or None
        """
        from noveler.application.orchestrators.error_handling_orchestrator import (
            ErrorHandlingOrchestrator,
            ErrorHandlingRequest,
        )
        from noveler.application.orchestrators.plot_generation_orchestrator import (
            PlotGenerationWorkflowRequest,
        )
        from noveler.domain.services.error_classification_service import ErrorClassificationService
        from noveler.domain.services.error_recovery_service import ErrorRecoveryService
        from noveler.domain.services.error_reporting_service import ErrorReportingService

        # Initialize error handling orchestrator with DDD-compliant dependency injection
        factory = getattr(self, "repository_factory", None)
        try:
            logging_adapter = factory.create_error_logging_adapter() if factory else None
        except Exception:
            logging_adapter = None
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

        try:
            project_root = self._get_project_root()

            preview_context = load_previous_preview_context(
                project_root, episode_number, repository_cls=self._quality_record_repository_cls
            )
            self._latest_preview_context = preview_context

            context_data: dict[str, Any] = {
                "project_root": str(project_root),
                "generation_mode": "auto",
                "force_regenerate": force_regenerate,
                "character_focus": chapter_plot_info.get("characters", [None])[0]
                if chapter_plot_info.get("characters")
                else None,
            }

            if preview_context:
                context_data["previous_episode_preview"] = preview_context
                hook = preview_context.get("preview", {}).get("hook")
                if hook:
                    context_data.setdefault("story_signals", {})["previous_preview_hook"] = hook

            # Create workflow request
            request = PlotGenerationWorkflowRequest(
                episode_number=episode_number,
                project_name=str(project_root.name),
                chapter_number=chapter_plot_info.get("chapter_number", 1),
                context_data=context_data,
            )

            # Execute generation workflow (lazy fetch orchestrator)
            orchestrator = self._get_orchestrator()
            result = orchestrator.generate_plot(request)

            # SPEC-PROMPT-SAVE-001統合: 詳細化プロンプト保存
            if enable_prompt_save and result.success:
                self._save_enhanced_prompt(episode_number, chapter_plot_info, result, project_root)

            if result.success and result.generated_plot:
                # Convert the generated plot string to domain entity
                return self._convert_to_generated_episode_plot(
                    episode_number, result.generated_plot, result.quality_score or 0.0
                )

            # Handle generation failure with fallback
            return self._create_fallback_plot(episode_number)

        except Exception as e:
            # Use error handling orchestrator for comprehensive error management
            error_request = ErrorHandlingRequest(
                exception=e,
                context={
                    "operation_id": f"plot_generation_{episode_number}",
                    "user_context": {"operation_name": "generate_episode_plot_auto", "episode_number": episode_number},
                },
                operation_name="plot_generation",
            )

            error_result = error_orchestrator.handle_error(error_request)

            if error_result.business_error_result:
                if self._logger_service:
                    self._logger_service.error(f"プロット生成が失敗: {error_result.business_error_result.user_message}")
                elif hasattr(self, "_get_console"):
                    console = self._get_console()
                    console.print(f"[red]Plot generation failed: {error_result.business_error_result.user_message}[/red]")
                    for suggestion in error_result.business_error_result.recovery_suggestions:
                        console.print(f"  [yellow]- {suggestion}[/yellow]")

            # Log the error for debugging purposes
            self.logger.error(f"Plot generation failed for episode {episode_number}: {e!s}", exc_info=True)

            return self._create_fallback_plot(episode_number)

    def format_plot_as_yaml(self, plot: GeneratedEpisodePlot) -> str:
        """Format plot as YAML using template adapter

        Args:
            plot: Plot object

        Returns:
            YAML formatted string
        """
        # DDD準拠：Infrastructure依存を排除（遅延初期化で対応）
        try:
            # DDD準拠: Application→Infrastructure違反を遅延初期化で回避
            TemplateData = self.repository_factory.get_template_data_class()
        except (ImportError, AttributeError):
            # フォールバック：基本辞書形式
            TemplateData = dict

        # Use template adapter for consistent formatting
        template_data: dict[str, Any] = TemplateData(
            episode_number=plot.episode_number,
            chapter_number=plot.source_chapter_number,
            project_name="current_project",
            context_data={
                "title": plot.title,
                "summary": plot.summary,
                "scenes": plot.scenes,
                "key_events": plot.key_events,
                "viewpoint": plot.viewpoint,
                "tone": plot.tone,
                "conflict": plot.conflict,
                "resolution": plot.resolution,
            },
            variables={},
        )

        # Try template-based formatting first
        template_result = self._template_adapter.generate_with_template("episode_yaml", template_data)

        if template_result.success:
            return template_result.content
        # Fallback to simple YAML generation
        return self._create_simple_yaml(plot)

    def _get_orchestrator(self):
        """オーケストレーター取得（クラス属性パッチと両立する遅延初期化）"""
        cls = type(self)
        # クラス属性がパッチされていればそれを使用
        orchestrator = getattr(cls, "_orchestrator", None)
        if orchestrator is not None:
            return orchestrator

        # インスタンスにまだ無ければ作成
        if getattr(self, "_orchestrator", None) is None:
            from noveler.application.orchestrators.plot_generation_orchestrator import (
                PlotGenerationOrchestrator,
            )

            self._orchestrator = PlotGenerationOrchestrator(
                plot_structure_service=self._structure_service,
                plot_quality_service=self._quality_service,
                claude_adapter=self._claude_adapter,
                template_adapter=self._template_adapter,
            )
        return self._orchestrator

    def _convert_to_generated_episode_plot(
        self, episode_number: int, plot_content: str, quality_score: float
    ) -> GeneratedEpisodePlot:
        """Convert orchestrator result to domain entity"""
        import yaml

        from noveler.domain.entities.generated_episode_plot import GeneratedEpisodePlot

        try:
            # Parse YAML content from orchestrator
            plot_data: dict[str, Any] = yaml.safe_load(plot_content)

            plot_entity = GeneratedEpisodePlot(
                episode_number=episode_number,
                title=plot_data.get("episode_info", {}).get("title", f"Episode {episode_number}"),
                summary=plot_data.get("synopsis", "Generated plot summary"),
                scenes=plot_data.get("scenes", []),
                key_events=plot_data.get("foreshadowing", []),
                viewpoint=self._get_character_viewpoint(plot_data.get("character_development", {})),
                tone=plot_data.get("themes", ["Engaging narrative"])[0],
                conflict="Plot-driven conflict",
                resolution="Satisfying resolution",
                generation_timestamp=project_now().datetime,
                source_chapter_number=1,
            )
            try:
                setattr(plot_entity, "quality_score", quality_score)
            except Exception:
                pass
            try:
                setattr(plot_entity, "preview_context", self._latest_preview_context)
            except Exception:
                pass
            return plot_entity

        except Exception as e:
            # Log the parsing error for debugging
            self.logger.warning(f"Failed to parse plot content for episode {episode_number}: {e!s}")

            return self._create_fallback_plot(episode_number)

    def _create_fallback_plot(self, episode_number: int) -> GeneratedEpisodePlot:
        """Create fallback plot when generation fails"""
        from noveler.domain.entities.generated_episode_plot import GeneratedEpisodePlot

        plot_entity = GeneratedEpisodePlot(
            episode_number=episode_number,
            title=f"Episode {episode_number}_Fallback",
            summary=f"Episode {episode_number} fallback plot (emergency generation)",
            scenes=[{"scene_number": 1, "title": "Fallback Scene", "description": "Basic structure only"}],
            key_events=["Fallback event"],
            viewpoint="Protagonist perspective",
            tone="Fallback",
            conflict="Basic conflict setup",
            resolution="Basic resolution",
            generation_timestamp=project_now().datetime,
            source_chapter_number=1,
        )
        try:
            setattr(plot_entity, "preview_context", self._latest_preview_context)
        except Exception:
            pass
        return plot_entity

    def _create_simple_yaml(self, plot: GeneratedEpisodePlot) -> str:
        """Create simple YAML fallback"""
        import yaml

        plot_dict = {
            "episode_info": {
                "episode_number": plot.episode_number,
                "title": plot.title,
                "chapter": plot.source_chapter_number,
            },
            "synopsis": plot.summary,
            "scenes": plot.scenes,
            "key_events": plot.key_events,
            "viewpoint": plot.viewpoint,
            "tone": plot.tone,
            "conflict": plot.conflict,
            "resolution": plot.resolution,
            "generation_timestamp": plot.generation_timestamp.isoformat(),
        }

        return yaml.dump(plot_dict, default_flow_style=False, allow_unicode=True)

    def _get_project_root(self) -> Path:
        """Get project root path"""
        try:
            import os

            env_project_root = os.environ.get("PROJECT_ROOT")
            if env_project_root:
                return Path(env_project_root)
            return Path.cwd()
        except Exception:
            return Path.cwd()

    def _get_character_viewpoint(self, character_development: dict) -> str:
        """新しいキャラクター開発構造から視点情報を取得

        DDD準拠: Infrastructure依存を排除し、純粋なデータ変換ロジックに変更
        """
        try:
            # 新形式から取得を試行
            main_characters = character_development.get("main_characters", {})
            if main_characters:
                hero_info = main_characters.get("hero", {})
                if hero_info and hero_info.get("name"):
                    return f"{hero_info['name']} perspective"

            # 旧形式から取得を試行（Infrastructure依存なしの純粋データ処理）
            protagonist_data = character_development.get("protagonist")
            if isinstance(protagonist_data, list) and protagonist_data:
                return f"{protagonist_data[0]} perspective"
            if isinstance(protagonist_data, str):
                return f"{protagonist_data} perspective"

            # character_arcs形式からの取得
            character_arcs = character_development.get("character_arcs", {})
            for character_name, character_info in character_arcs.items():
                if isinstance(character_info, dict) and character_info.get("is_protagonist", False):
                    return f"{character_name} perspective"

            # デフォルトフォールバック
            return "Main character perspective"

        except Exception:
            return "Main character perspective"

    def _convert_character_development(self, character_development: dict) -> dict:
        """新しいキャラクター開発構造を旧形式に変換（後方互換性）"""
        try:
            result = {}

            # 新形式から変換
            main_characters = character_development.get("main_characters", {})
            for role, character_info in main_characters.items():
                if isinstance(character_info, dict):
                    result[role] = {
                        "name": character_info.get("name", ""),
                        "arc_summary": character_info.get("arc_summary", ""),
                        "growth_stages": character_info.get("key_growth_points", []),
                    }

            # 旧形式の直接継承
            legacy_arcs = character_development.get("legacy_character_arcs", {})
            result.update(legacy_arcs)

            # 既存の character_arcs 形式も保持
            existing_arcs = character_development.get("character_arcs", {})
            result.update(existing_arcs)

            return result

        except Exception:
            return {}

    def _save_enhanced_prompt(
        self,
        episode_number: int,
        chapter_plot_info: dict,
        generation_result: "PlotGenerationWorkflowResult",
        project_root: Path,
    ) -> None:
        """詳細化プロンプト保存実行

        SPEC-PROMPT-SAVE-001統合: 強化プロンプトテンプレートサービス活用

        Args:
            episode_number: エピソード番号
            chapter_plot_info: 章プロット情報
            generation_result: プロット生成結果
            project_root: プロジェクトルート
        """
        try:
            # 強化プロンプトテンプレートサービス初期化
            from noveler.application.use_cases.episode_prompt_save_use_case import (
                EpisodePromptSaveUseCase,
                PromptSaveRequest,
            )
            from noveler.domain.services.enhanced_prompt_template_service import (
                EnhancedPromptContext,
                EnhancedPromptTemplateService,
            )

            # 章プロット情報からチャプタープロットエンティティ取得
            chapter_plot = self._get_chapter_plot_entity(chapter_plot_info)
            if not chapter_plot:
                if self._logger_service:
                    self._logger_service.warning(f"チャプタープロット取得失敗: エピソード {episode_number}")
                elif hasattr(self, "_get_console"):
                    console = self._get_console()
                    console.print(f"[yellow]Warning: Could not retrieve chapter plot for episode {episode_number}[/yellow]")
                return

            # 強化プロンプトコンテキスト構築
            context = EnhancedPromptContext(
                episode_number=episode_number,
                episode_title=self._extract_episode_title(chapter_plot_info, episode_number),
                chapter_plot=chapter_plot,
                previous_episodes=self._get_previous_episodes(chapter_plot, episode_number),
                following_episodes=self._get_following_episodes(chapter_plot, episode_number),
                project_context={"project_root": str(project_root)},
            )

            # 強化プロンプト生成
            template_service = EnhancedPromptTemplateService()
            enhanced_prompt = template_service.generate_enhanced_prompt(context)

            # プロンプト保存用セクションを構築
            content_sections: dict[str, Any] = {
                "generation_mode": "enhanced_auto",
                "template_version": "2.0",
                "quality_score": generation_result.quality_score or 0.0,
                "original_plot": generation_result.generated_plot,
            }

            if episode_number > 1 and self._latest_preview_context:
                reference_sections: dict[str, Any] = {
                    "episode_number": episode_number - 1,
                }
                for section_name in ("preview", "quality", "source", "config"):
                    section_payload = self._latest_preview_context.get(section_name)
                    if section_payload:
                        reference_sections[section_name] = section_payload
                preview_text = self._latest_preview_context.get("preview_text")
                if preview_text:
                    reference_sections["preview_text"] = preview_text
                previous_score = self._latest_preview_context.get("score")
                if previous_score is not None:
                    reference_sections["score"] = previous_score
                if reference_sections.keys() - {"episode_number"}:
                    content_sections["reference_sections"] = reference_sections

            # プロンプト保存リクエスト作成
            save_request = PromptSaveRequest(
                episode_number=episode_number,
                episode_title=context.episode_title,
                prompt_content=enhanced_prompt,
                project_root=project_root,
                content_sections=content_sections,
                generation_mode="enhanced_auto",
                quality_level="detailed",
            )

            # プロンプト保存実行
            save_use_case = EpisodePromptSaveUseCase()
            save_result = save_use_case.execute(save_request)

            if save_result.success:
                # B30準拠: console_service使用（情報表示）
                if hasattr(self, "_get_console") or hasattr(self, "_get_console"):
                    console = self._get_console()
                    console.print(f"[green]✅ Enhanced prompt saved: {save_result.saved_file_path}[/green]")
                    console.print(f"[blue]📊 Quality score: {save_result.quality_score:.2f}[/blue]")
            elif self._logger_service:
                self._logger_service.error(f"強化プロンプトの保存に失敗: {save_result.error_message}")
            elif hasattr(self, "_get_console"):
                console = self._get_console()
                console.print(f"[red]❌ Failed to save enhanced prompt: {save_result.error_message}[/red]")

        except Exception as e:
            # エラーは警告として処理（メインの生成処理には影響させない）
            self.logger.warning(f"Enhanced prompt saving failed for episode {episode_number}: {e!s}")

            if self._logger_service:
                self._logger_service.warning(f"強化プロンプト保存失敗（非致命的）: {e!s}")
            elif hasattr(self, "_get_console"):
                console = self._get_console()
                console.print(f"[yellow]Warning: Enhanced prompt saving failed: {e!s}[/yellow]")

    def _get_chapter_plot_entity(self, chapter_plot_info: dict) -> "ChapterPlot | None":
        """章プロット情報からエンティティ取得"""
        try:
            from noveler.domain.entities.chapter_plot import ChapterPlot
            from noveler.domain.value_objects.chapter_number import ChapterNumber

            # 章番号の決定
            chapter_num = chapter_plot_info.get("chapter_number", 1)

            # チャプタープロットエンティティ作成（簡易版）
            return ChapterPlot(
                chapter_number=ChapterNumber(chapter_num),
                title=chapter_plot_info.get("title", f"Chapter {chapter_num}"),
                summary=chapter_plot_info.get("summary", "Chapter summary"),
                episode_range=(1, 20),  # デフォルト範囲
                key_events=chapter_plot_info.get("key_events", []),
                character_arcs=self._convert_character_development(chapter_plot_info.get("character_development", {})),
                foreshadowing_elements=chapter_plot_info.get("foreshadowing", {}),
            )

        except Exception:
            return None

    def _extract_episode_title(self, chapter_plot_info: dict, episode_number: int) -> str:
        """エピソードタイトル抽出"""
        episodes = chapter_plot_info.get("episodes", [])
        for episode in episodes:
            if episode.get("episode_number") == episode_number:
                return episode.get("title", f"第{episode_number:03d}話")

        return f"第{episode_number:03d}話_生成プロット"

    def _get_previous_episodes(self, chapter_plot: "ChapterPlot", current_episode: int) -> list[dict]:
        """前のエピソード情報取得"""
        previous = []
        for i in range(max(1, current_episode - 2), current_episode):
            episode_info = chapter_plot.get_episode_info(i)
            if episode_info:
                previous.append(
                    {
                        "episode_number": i,
                        "title": episode_info.get("title", f"第{i:03d}話"),
                        "summary": episode_info.get("summary", f"Episode {i} summary"),
                    }
                )
        return previous

    def _get_following_episodes(self, chapter_plot: "ChapterPlot", current_episode: int) -> list[dict]:
        """後のエピソード情報取得"""
        following = []
        for i in range(current_episode + 1, min(current_episode + 3, 21)):
            episode_info = chapter_plot.get_episode_info(i)
            if episode_info:
                following.append(
                    {
                        "episode_number": i,
                        "title": episode_info.get("title", f"第{i:03d}話"),
                        "summary": episode_info.get("summary", f"Episode {i} summary"),
                    }
                )
        return following
