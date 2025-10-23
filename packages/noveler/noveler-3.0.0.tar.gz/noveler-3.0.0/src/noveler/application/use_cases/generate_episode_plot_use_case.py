"""エピソードプロット生成ユースケース

SPEC-PLOT-001: Claude Code連携プロット生成システム
SPEC-A28-001: A28拡張機能統合プロット生成システム
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.generated_episode_plot import GeneratedEpisodePlot
from noveler.domain.interfaces.logger_service import ILoggerService
from noveler.domain.repositories.chapter_plot_repository import (
    ChapterPlotNotFoundError,
    ChapterPlotRepository,
)
from noveler.domain.services.claude_plot_generation_service import (
    ClaudePlotGenerationService,
    PlotGenerationError,
)
from noveler.domain.services.plot_generation_functional_core import (
    EmotionTechFusion,
    ForeshadowingElement,
    ForeshadowingStatus,
    ImportanceRank,
    PlotGenerationCore,
    PlotGenerationInput,
    SceneData,
)


@dataclass
class GenerateEpisodePlotRequest:
    """エピソードプロット生成リクエスト - A28拡張版"""

    episode_number: int
    project_path: Path
    force: bool = False

    # A28拡張機能オプション
    enable_a28_enhancements: bool = True
    foreshadowing_elements: list[dict[str, Any]] | None = None
    scene_structure_overrides: list[dict[str, Any]] | None = None
    emotion_tech_fusions: list[dict[str, Any]] | None = None
    target_word_count: int = 6000
    quality_threshold: float = 0.8
    viewpoint_character: str = "主人公"


@dataclass
class GenerateEpisodePlotResponse:
    """エピソードプロット生成レスポンス - A28拡張版"""

    success: bool
    generated_plot: GeneratedEpisodePlot | None = None
    error_message: str | None = None
    force_used: bool = False
    output_file_path: Path | None = None

    # A28拡張機能結果
    enhancement_used: bool = False
    enhancement_quality_score: float = 0.0
    foreshadowing_consistency_score: float = 0.0
    scene_balance_score: float = 0.0
    emotion_tech_integration_score: float = 0.0
    word_allocation_breakdown: dict[str, int] | None = None
    reader_reaction_predictions: dict[str, str] | None = None
    improvement_suggestions: list[str] | None = None


@dataclass
class GenerateEpisodePlotDependencies:
    """エピソードプロット生成ユースケースの依存関係"""

    chapter_plot_repository: ChapterPlotRepository
    claude_plot_generation_service: ClaudePlotGenerationService


# DDD準拠: Application→Presentation違反を回避（遅延初期化で解決）


@dataclass
class GenerateEpisodePlotUseCase:
    """エピソードプロット生成ユースケース - A28拡張版

    Phase 5: 統一DIパターン適用版 + A28拡張機能統合
    Claude Code連携 + A28拡張機能によるエピソードプロット生成のビジネスフローを管理する。
    章別プロット情報を取得し、Claude Code + A28拡張機能で動的にプロット生成、結果を保存する。
    """

    # 依存関係をコンストラクタ注入
    dependencies: GenerateEpisodePlotDependencies | None = None
    chapter_plot_repository: "ChapterPlotRepository" | None = None
    claude_service: "ClaudePlotGenerationService" | None = None
    logger_service: ILoggerService | None = None

    def __post_init__(self) -> None:
        if self.dependencies is not None:
            if self.chapter_plot_repository is None:
                self.chapter_plot_repository = self.dependencies.chapter_plot_repository
            if self.claude_service is None:
                self.claude_service = self.dependencies.claude_plot_generation_service

        if self.chapter_plot_repository is None or self.claude_service is None:
            msg = "GenerateEpisodePlotUseCase requires chapter_plot_repository and claude_service"
            raise TypeError(msg)

        if self.logger_service is None:
            from noveler.domain.interfaces.logger_service import NullLoggerService

            self.logger_service = NullLoggerService()

    def execute(self, request: GenerateEpisodePlotRequest) -> GenerateEpisodePlotResponse:
        """エピソードプロット生成を実行 - A28拡張版

        Args:
            request: 生成リクエスト

        Returns:
            GenerateEpisodePlotResponse: 生成結果
        """
        try:
            self.logger_service.info("エピソードプロット生成開始 (A28拡張): Episode %s", request.episode_number)

            # 1. エピソード番号から章別プロットを取得
            chapter_plot = self.chapter_plot_repository.find_by_episode_number(request.episode_number)

            # 2A. 従来のClaude Code連携で基本プロット生成
            generated_plot = self.claude_service.generate_episode_plot(chapter_plot, request.episode_number)

            # 2B. A28拡張機能適用（有効化時のみ）
            enhancement_analysis = None
            processed_data = {}

            if request.enable_a28_enhancements:
                self.logger_service.info("A28拡張機能を適用中...")

                # A28入力データ構築
                plot_input = self._build_a28_input(request, chapter_plot, generated_plot)

                # A28拡張処理実行
                plot_output = PlotGenerationCore.transform_plot(plot_input)

                if not plot_output.success:
                    self.logger_service.warning("A28拡張処理に問題がありました: %s", plot_output.error_message)
                else:
                    enhancement_analysis = plot_output.enhancement_analysis
                    processed_data = {
                        "word_allocation": plot_output.word_allocation_breakdown,
                        "reader_predictions": plot_output.reader_reaction_predictions,
                        "improvement_suggestions": plot_output.improvement_suggestions,
                    }
                    self.logger_service.info("A28拡張処理完了 - 総合品質スコア: %.2f", plot_output.quality_score)

            # 3. 生成されたプロットをファイルに保存（A28情報統合）
            output_file_path = self._get_output_file_path(request.project_path, generated_plot)
            save_success = self._save_generated_plot(
                request.project_path,
                generated_plot,
                enhancement_analysis,
                processed_data,
            )

            if not save_success:
                error_msg = "生成されたプロットの保存に失敗しました"
                self.logger_service.error(error_msg)
                return GenerateEpisodePlotResponse(
                    success=False,
                    error_message=error_msg,
                    force_used=request.force,
                )

            # レスポンス構築（A28情報含む）
            response = GenerateEpisodePlotResponse(
                success=True,
                generated_plot=generated_plot,
                force_used=request.force,
                output_file_path=output_file_path,
                enhancement_used=request.enable_a28_enhancements,
            )

            # A28拡張情報をレスポンスに追加
            if enhancement_analysis:
                response.enhancement_quality_score = enhancement_analysis.overall_enhancement_score
                response.foreshadowing_consistency_score = enhancement_analysis.foreshadowing_consistency_score
                response.scene_balance_score = enhancement_analysis.scene_balance_score
                response.emotion_tech_integration_score = enhancement_analysis.emotion_tech_integration_score
                response.word_allocation_breakdown = processed_data.get("word_allocation")
                response.reader_reaction_predictions = processed_data.get("reader_predictions")
                response.improvement_suggestions = processed_data.get("improvement_suggestions")

            self.logger_service.info("エピソードプロット生成完了: Episode %s", request.episode_number)
            return response

        except ChapterPlotNotFoundError as e:
            error_msg = f"章別プロット取得エラー: {e}"
            self.logger_service.exception(error_msg)
            return GenerateEpisodePlotResponse(
                success=False,
                error_message=error_msg,
                force_used=request.force,
            )

        except PlotGenerationError as e:
            error_msg = f"プロット生成エラー: {e}"
            self.logger_service.exception(error_msg)
            return GenerateEpisodePlotResponse(
                success=False,
                error_message=error_msg,
                force_used=request.force,
            )

        except Exception as e:
            error_msg = f"予期しないエラーが発生しました: {e}"
            self.logger_service.exception(error_msg)
            return GenerateEpisodePlotResponse(
                success=False,
                error_message=error_msg,
                force_used=request.force,
            )

    def _build_a28_input(self, request: GenerateEpisodePlotRequest, _chapter_plot: dict[str, Any], generated_plot: GeneratedEpisodePlot) -> PlotGenerationInput:
        """A28入力データ構築

        Args:
            request: リクエスト
            chapter_plot: 章別プロット
            generated_plot: 生成されたプロット

        Returns:
            PlotGenerationInput: A28入力データ
        """
        # 基本章情報を辞書形式で構築
        chapter_info = {
            "title": generated_plot.title,
            "summary": getattr(generated_plot, "summary", ""),
            "episode_number": generated_plot.episode_number,
        }

        # 伏線要素の構築
        foreshadowing_elements = []
        if request.foreshadowing_elements:
            for i, foreshadow_dict in enumerate(request.foreshadowing_elements):
                foreshadow_element = ForeshadowingElement(
                    foreshadow_id=foreshadow_dict.get("foreshadow_id", f"FS{i+1:03d}"),
                    element=foreshadow_dict.get("element", "伏線要素"),
                    category=foreshadow_dict.get("category", "plot_device"),
                    status=ForeshadowingStatus(foreshadow_dict.get("status", "planned")),
                    planted_episode=foreshadow_dict.get("planted_episode", request.episode_number),
                    resolution_episode=foreshadow_dict.get("resolution_episode"),
                    importance_level=foreshadow_dict.get("importance_level", 3),
                    dependency=foreshadow_dict.get("dependency", []),
                    placement_scene=foreshadow_dict.get("placement_scene", "scene_001"),
                    reader_clue_level=foreshadow_dict.get("reader_clue_level", "moderate"),
                )
                foreshadowing_elements.append(foreshadow_element)

        # シーン構造の構築
        scene_structure = []
        if request.scene_structure_overrides:
            for i, scene_dict in enumerate(request.scene_structure_overrides):
                scene_data = SceneData(
                    scene_id=scene_dict.get("scene_id", f"scene_{i+1:03d}"),
                    title=scene_dict.get("title", f"シーン{i+1}"),
                    importance_rank=ImportanceRank(scene_dict.get("importance_rank", "B")),
                    estimated_words=scene_dict.get("estimated_words", request.target_word_count // 8),
                    percentage=scene_dict.get("percentage", 12.5),
                    story_function=scene_dict.get("story_function", "plot_advancement"),
                    emotional_weight=scene_dict.get("emotional_weight", "medium"),
                    technical_complexity=scene_dict.get("technical_complexity", "low"),
                    reader_engagement_level=scene_dict.get("reader_engagement_level", "medium"),
                )
                scene_structure.append(scene_data)

        # 感情×技術融合の構築
        emotion_tech_fusions = []
        if request.emotion_tech_fusions:
            for fusion_dict in request.emotion_tech_fusions:
                emotion_tech_fusion = EmotionTechFusion(
                    timing=fusion_dict.get("timing", "第二幕クライマックス"),
                    scene_reference=fusion_dict.get("scene_reference", "scene_003"),
                    emotion_type=fusion_dict.get("emotion_type", "成長と達成感"),
                    emotion_intensity=fusion_dict.get("emotion_intensity", "medium"),
                    tech_concept=fusion_dict.get("tech_concept", "プログラミング概念"),
                    tech_complexity=fusion_dict.get("tech_complexity", "intermediate"),
                    synergy_effect=fusion_dict.get("synergy_effect", "技術的理解と感情的成長の融合"),
                    synergy_intensity=fusion_dict.get("synergy_intensity", "medium"),
                )
                emotion_tech_fusions.append(emotion_tech_fusion)

        return PlotGenerationInput(
            episode_number=request.episode_number,
            chapter_info=chapter_info,
            previous_episodes=[],  # TODO: 実際の前エピソード情報を取得
            quality_threshold=request.quality_threshold,
            enable_enhancements=True,
            foreshadowing_elements=foreshadowing_elements,
            scene_structure=scene_structure,
            emotion_tech_fusions=emotion_tech_fusions,
            target_word_count=request.target_word_count,
            viewpoint_character=request.viewpoint_character,
        )

    def _save_generated_plot_with_enhancements(
        self,
        project_path: Path,
        generated_plot: GeneratedEpisodePlot,
        enhancement_analysis: dict[str, Any] | None = None,
        processed_data: dict[str, Any] | None = None
    ) -> bool:
        """A28拡張情報を含むプロット保存

        Args:
            project_path: プロジェクトパス
            generated_plot: 生成されたプロット
            enhancement_analysis: A28拡張分析結果
            processed_data: 処理済みデータ

        Returns:
            bool: 保存成功の場合True
        """
        try:
            output_file_path = self._get_output_file_path(project_path, generated_plot)

            # ディレクトリ作成
            output_file_path.parent.mkdir(parents=True, exist_ok=True)

            # 既存のテンプレート構造と統合
            plot_data: dict[str, Any] = self._merge_with_template_structure(generated_plot)

            # A28拡張情報をテンプレートに統合
            if enhancement_analysis and processed_data:
                plot_data["a28_enhancement_analysis"] = {
                    "overall_score": enhancement_analysis.overall_enhancement_score,
                    "foreshadowing_consistency": enhancement_analysis.foreshadowing_consistency_score,
                    "scene_balance": enhancement_analysis.scene_balance_score,
                    "emotion_tech_integration": enhancement_analysis.emotion_tech_integration_score,
                    "word_allocation": enhancement_analysis.word_allocation_score,
                    "reader_engagement_prediction": enhancement_analysis.reader_engagement_prediction,
                    "viewpoint_consistency": enhancement_analysis.viewpoint_consistency_score,
                }

                if processed_data.get("word_allocation"):
                    plot_data["a28_word_allocation"] = processed_data["word_allocation"]

                if processed_data.get("reader_predictions"):
                    plot_data["a28_reader_predictions"] = processed_data["reader_predictions"]

                if processed_data.get("improvement_suggestions"):
                    plot_data["a28_improvement_suggestions"] = processed_data["improvement_suggestions"]

            # YAMLファイルに保存
            with output_file_path.open("w", encoding="utf-8") as f:
                yaml.dump(plot_data, f, allow_unicode=True, default_flow_style=False)

            return True

        except Exception:
            self.logger_service.exception("プロット保存エラー")
            return False

    def _save_generated_plot(
        self,
        project_path: Path,
        generated_plot: GeneratedEpisodePlot,
        enhancement_analysis: dict[str, Any] | None = None,
        processed_data: dict[str, Any] | None = None,
    ) -> bool:
        """旧バージョン互換用 - A28拡張なし保存

        Args:
            project_path: プロジェクトパス
            generated_plot: 生成されたプロット

        Returns:
            bool: 保存成功の場合True
        """
        return self._save_generated_plot_with_enhancements(
            project_path,
            generated_plot,
            enhancement_analysis,
            processed_data,
        )

    def _get_output_file_path(self, project_path: Path, generated_plot: GeneratedEpisodePlot) -> Path:
        """出力ファイルパスを取得

        Args:
            project_path: プロジェクトパス
            generated_plot: 生成されたプロット

        Returns:
            Path: 出力ファイルパス
        """
        # タイトルから安全なファイル名を生成
        safe_title = generated_plot.title.replace(" ", "").replace("　", "")
        filename = f"第{generated_plot.episode_number:03d}話_{safe_title}.yaml"

        # DDD準拠: Infrastructure層のパスサービスを使用（Presentation層依存を排除）
        try:
            from noveler.infrastructure.adapters.path_service_adapter import create_path_service

            path_service = create_path_service(project_path)
            plots_dir = path_service.get_plot_dir() / "話別プロット"
        except Exception:
            plots_dir = project_path / "20_プロット" / "話別プロット"

        return plots_dir / filename

    def _merge_with_template_structure(self, generated_plot: GeneratedEpisodePlot) -> dict[str, Any]:
        """生成プロットをテンプレート構造と統合（完全テンプレート準拠版）

        話別プロットテンプレート.yamlの342行構造に完全対応した統合処理

        Args:
            generated_plot: 生成されたプロット

        Returns:
            dict[str, Any]: テンプレート完全準拠の統合プロットデータ
        """
        # GeneratedEpisodePlotの新しいto_yaml_dict()を使用
        # これによりテンプレートの342行構造に完全対応
        template_compliant_data: dict[str, Any] = generated_plot.to_yaml_dict()

        return template_compliant_data

    @classmethod
    def create_with_di(cls) -> "GenerateEpisodePlotUseCase":
        """DIを使用したインスタンス作成

        Phase 5統一DIパターン: Factory Method

        Returns:
            GenerateEpisodePlotUseCase: 設定済みインスタンス
        """
        try:
            # DIコンテナから依存関係解決
            from noveler.infrastructure.di.simple_di_container import get_container

            container = get_container()

            # Interface経由で依存関係取得
            from noveler.domain.interfaces.logger_service import ILoggerService
            from noveler.domain.repositories.chapter_plot_repository import ChapterPlotRepository
            from noveler.domain.services.claude_plot_generation_service import ClaudePlotGenerationService

            return cls(
                chapter_plot_repository=container.get(ChapterPlotRepository),
                claude_service=container.get(ClaudePlotGenerationService),
                logger_service=container.get(ILoggerService),
            )

        except Exception:
            # フォールバック: 直接インスタンス化
            from pathlib import Path

            from noveler.domain.interfaces.logger_service import NullLoggerService
            from noveler.infrastructure.repositories.simple_yaml_chapter_plot_repository import (
                SimpleYamlChapterPlotRepository,
            )

            logger_service = NullLoggerService()
            data_path = Path.cwd() / "data"

            return cls(
                chapter_plot_repository=SimpleYamlChapterPlotRepository(data_path),
                claude_service=ClaudePlotGenerationService(logger_service),
                logger_service=logger_service,
            )


# Factory関数（便利メソッド）
def create_generate_episode_plot_use_case() -> GenerateEpisodePlotUseCase:
    """エピソードプロット生成ユースケースの簡単作成

    Phase 5統一パターン: Factory Function

    Returns:
        GenerateEpisodePlotUseCase: 設定済みインスタンス
    """
    return GenerateEpisodePlotUseCase.create_with_di()
