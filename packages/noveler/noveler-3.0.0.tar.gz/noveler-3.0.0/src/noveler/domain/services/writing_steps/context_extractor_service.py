"""Domain.services.writing_steps.context_extractor_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""STEP 2: ContextExtractorService

A38執筆プロンプトガイドのSTEP 2に対応するマイクロサービス。
コンテキスト抽出・環境情報収集・背景要素の整理を担当。
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from noveler.domain.interfaces.path_service import IPathService

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.domain.interfaces.path_service_protocol import IPathService

from noveler.domain.services.writing_steps.base_writing_step import BaseWritingStep, WritingStepResponse


@dataclass
class WorldContext:
    """世界観コンテキスト"""

    # 基本設定
    setting_name: str
    time_period: str
    location: str

    # 詳細情報
    social_structure: list[str] = field(default_factory=list)
    political_situation: list[str] = field(default_factory=list)
    technological_level: str = ""
    magic_system: list[str] = field(default_factory=list)

    # 環境詳細
    climate: str = ""
    geography: str = ""
    culture: list[str] = field(default_factory=list)


@dataclass
class CharacterContext:
    """キャラクターコンテキスト"""

    # 基本情報
    character_name: str
    role: str  # "protagonist", "antagonist", "supporting"

    # 現在状況
    current_status: str = ""
    location: str = ""
    emotional_state: str = ""

    # 関係性
    relationships: dict[str, str] = field(default_factory=dict)

    # 背景
    background_elements: list[str] = field(default_factory=list)
    motivations: list[str] = field(default_factory=list)


@dataclass
class StoryContext:
    """ストーリーコンテキスト"""

    # 現在の状況
    current_situation: str
    immediate_goals: list[str] = field(default_factory=list)
    active_conflicts: list[str] = field(default_factory=list)

    # 前の状況からの継続
    previous_events: list[str] = field(default_factory=list)
    unresolved_issues: list[str] = field(default_factory=list)

    # 将来への準備
    foreshadowing_elements: list[str] = field(default_factory=list)
    setup_requirements: list[str] = field(default_factory=list)


@dataclass
class TechnicalContext:
    """技術的コンテキスト"""

    # 執筆設定
    viewpoint: str = "三人称単元視点"
    viewpoint_character: str = "主人公"
    narrative_tone: str = "標準"

    # 技術的制約
    target_word_count: int = 4000
    style_requirements: list[str] = field(default_factory=list)
    genre_constraints: list[str] = field(default_factory=list)


@dataclass
class ContextExtractionResult:
    """コンテキスト抽出結果"""

    episode_number: int
    extraction_confidence: float = 0.0

    # 各種コンテキスト
    world_context: WorldContext | None = None
    character_contexts: list[CharacterContext] = field(default_factory=list)
    story_context: StoryContext | None = None
    technical_context: TechnicalContext | None = None

    # 統合情報
    key_context_points: list[str] = field(default_factory=list)
    context_gaps: list[str] = field(default_factory=list)
    recommendation: list[str] = field(default_factory=list)


@dataclass
class ContextExtractorResponse(WritingStepResponse):
    """コンテキスト抽出サービス結果"""

    # 基底クラスのフィールド継承
    context_result: ContextExtractionResult | None = None

    # パフォーマンス情報
    file_scan_time_ms: float = 0.0
    world_extraction_time_ms: float = 0.0
    character_extraction_time_ms: float = 0.0
    story_extraction_time_ms: float = 0.0

    # 統計情報
    files_scanned: int = 0
    contexts_extracted: int = 0
    gaps_identified: int = 0


class ContextExtractorService(BaseWritingStep):
    """STEP 2: コンテキスト抽出マイクロサービス

    エピソード執筆に必要な全コンテキスト情報を抽出・整理。
    世界観・キャラクター・ストーリー・技術的コンテキストを統合管理。
    """

    def __init__(
        self,
        logger_service: ILoggerService = None,
        path_service: IPathService = None,
        **kwargs: Any
    ) -> None:
        """コンテキスト抽出サービス初期化

        Args:
            logger_service: ロガーサービス
            path_service: パスサービス（DI注入）
            **kwargs: BaseWritingStepの引数
        """
        super().__init__(step_number=2, step_name="context_extractor", **kwargs)

        self._logger_service = logger_service
        self._path_service = path_service

    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None = None
    ) -> ContextExtractorResponse:
        """コンテキスト抽出実行

        Args:
            episode_number: エピソード番号
            previous_results: 前ステップの結果（STEP 0-1の結果）

        Returns:
            ContextExtractorResponse: コンテキスト抽出結果
        """
        start_time = time.time()

        try:
            if self._logger_service:
                self._logger_service.info(f"STEP 2 コンテキスト抽出開始: エピソード={episode_number}")

            # 1. 前ステップ結果から基本情報取得
            project_root, plot_analysis = self._extract_previous_info(previous_results)

            # 2. 設定ファイル検索・読み込み
            file_scan_start = time.time()
            setting_files = await self._scan_setting_files(project_root)
            file_scan_time = (time.time() - file_scan_start) * 1000

            # 3. 各種コンテキスト抽出
            world_start = time.time()
            world_context = await self._extract_world_context(setting_files, plot_analysis)
            world_time = (time.time() - world_start) * 1000

            character_start = time.time()
            character_contexts = await self._extract_character_contexts(
                setting_files, plot_analysis, episode_number
            )
            character_time = (time.time() - character_start) * 1000

            story_start = time.time()
            story_context = await self._extract_story_context(
                plot_analysis, previous_results, episode_number
            )
            story_time = (time.time() - story_start) * 1000

            # 4. 技術的コンテキスト抽出
            technical_context = self._extract_technical_context(previous_results)

            # 5. 統合結果作成
            context_result = self._create_integrated_result(
                episode_number, world_context, character_contexts,
                story_context, technical_context
            )

            # 6. 成功応答作成
            execution_time = (time.time() - start_time) * 1000

            return ContextExtractorResponse(
                success=True,
                step_number=2,
                step_name="context_extractor",
                execution_time_ms=execution_time,

                # コンテキスト抽出固有フィールド
                context_result=context_result,

                # パフォーマンス情報
                file_scan_time_ms=file_scan_time,
                world_extraction_time_ms=world_time,
                character_extraction_time_ms=character_time,
                story_extraction_time_ms=story_time,

                # 統計情報
                files_scanned=len(setting_files),
                contexts_extracted=len(character_contexts) + (1 if world_context else 0),
                gaps_identified=len(context_result.context_gaps)
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_message = f"STEP 2 コンテキスト抽出エラー: {e}"

            if self._logger_service:
                self._logger_service.error(error_message)

            return ContextExtractorResponse(
                success=False,
                step_number=2,
                step_name="context_extractor",
                execution_time_ms=execution_time,
                error_message=error_message
            )

    def _extract_previous_info(
        self,
        previous_results: dict[int, Any] | None
    ) -> tuple[Path, Any | None]:
        """前ステップ情報抽出

        Args:
            previous_results: 前ステップ結果

        Returns:
            tuple[Path, Optional[Any]]: (プロジェクトルート, プロット解析結果)
        """
        project_root = Path.cwd()
        plot_analysis = None

        if previous_results:
            # STEP 0からプロジェクト情報
            if 0 in previous_results:
                scope_result = previous_results[0]
                if isinstance(scope_result, dict) and "project_root" in scope_result:
                    project_root = Path(scope_result["project_root"])  # TODO: IPathServiceを使用するように修正

            # STEP 1からプロット解析結果
            if 1 in previous_results:
                plot_result = previous_results[1]
                if hasattr(plot_result, "analysis_result"):
                    plot_analysis = plot_result.analysis_result
                elif isinstance(plot_result, dict):
                    plot_analysis = plot_result.get("analysis_result")

        return project_root, plot_analysis

    async def _scan_setting_files(self, project_root: Path) -> dict[str, Path]:
        """設定ファイル検索

        Args:
            project_root: プロジェクトルート

        Returns:
            Dict[str, Path]: 設定ファイル辞書
        """
        setting_files = {}

        # パスサービス使用（DI注入優先）
        settings_dir = self._path_service.get_settings_dir() if self._path_service else project_root / "設定"

        if not settings_dir.exists():
            return setting_files

        # ファイル種別と検索パターン
        file_patterns = {
            "world": ["世界観設定.yaml", "世界観.yaml", "world.yaml"],
            "characters": ["キャラクター設定.yaml", "登場人物.yaml", "characters.yaml"],
            "story": ["ストーリー設定.yaml", "あらすじ.yaml", "story.yaml"],
            "technical": ["執筆設定.yaml", "技術設定.yaml", "technical.yaml"],
            "project": ["プロジェクト設定.yaml", "project.yaml"]
        }

        for category, patterns in file_patterns.items():
            for pattern in patterns:
                file_path = settings_dir / pattern
                if file_path.exists():
                    setting_files[category] = file_path
                    break

        return setting_files

    async def _extract_world_context(
        self,
        setting_files: dict[str, Path],
        plot_analysis: Any | None
    ) -> WorldContext | None:
        """世界観コンテキスト抽出

        Args:
            setting_files: 設定ファイル辞書
            plot_analysis: プロット解析結果

        Returns:
            Optional[WorldContext]: 世界観コンテキスト
        """
        world_data = {}

        # 世界観設定ファイルから読み込み
        if "world" in setting_files:
            try:
                import yaml
                with open(setting_files["world"], encoding="utf-8") as f:
                    world_data = yaml.safe_load(f) or {}
            except Exception as e:
                if self._logger_service:
                    self._logger_service.warning(f"世界観設定読み込み失敗: {e}")

        # プロット解析からジャンル要素補完
        if plot_analysis and hasattr(plot_analysis, "genre_elements"):
            world_data.setdefault("genre_elements", []).extend(plot_analysis.genre_elements)

        if not world_data:
            return None

        return WorldContext(
            setting_name=world_data.get("name", "未設定世界"),
            time_period=world_data.get("time_period", "現代"),
            location=world_data.get("main_location", "未設定"),
            social_structure=world_data.get("social_structure", []),
            political_situation=world_data.get("politics", []),
            technological_level=world_data.get("technology", "現代レベル"),
            magic_system=world_data.get("magic", []),
            climate=world_data.get("climate", ""),
            geography=world_data.get("geography", ""),
            culture=world_data.get("culture", [])
        )

    async def _extract_character_contexts(
        self,
        setting_files: dict[str, Path],
        plot_analysis: Any | None,
        episode_number: int
    ) -> list[CharacterContext]:
        """キャラクターコンテキスト抽出

        Args:
            setting_files: 設定ファイル辞書
            plot_analysis: プロット解析結果
            episode_number: エピソード番号

        Returns:
            List[CharacterContext]: キャラクターコンテキスト一覧
        """
        character_contexts = []
        character_data = {}

        # キャラクター設定ファイルから読み込み
        if "characters" in setting_files:
            try:
                import yaml
                with open(setting_files["characters"], encoding="utf-8") as f:
                    character_data = yaml.safe_load(f) or {}
            except Exception as e:
                if self._logger_service:
                    self._logger_service.warning(f"キャラクター設定読み込み失敗: {e}")

        # プロット解析からキャラクター情報補完
        character_arcs = []
        if plot_analysis and hasattr(plot_analysis, "character_arcs"):
            character_arcs = plot_analysis.character_arcs

        # キャラクターコンテキスト作成
        characters = character_data.get("characters", {})
        for char_name, char_info in characters.items():
            if not isinstance(char_info, dict):
                continue

            # キャラクター役割推定
            role = self._estimate_character_role(char_name, char_info)

            # 現在状況推定
            current_status = self._estimate_character_status(
                char_name, char_info, episode_number, character_arcs
            )

            character_contexts.append(CharacterContext(
                character_name=char_name,
                role=role,
                current_status=current_status,
                location=char_info.get("location", ""),
                emotional_state=char_info.get("emotional_state", ""),
                relationships=char_info.get("relationships", {}),
                background_elements=char_info.get("background", []),
                motivations=char_info.get("motivations", [])
            ))

        return character_contexts

    async def _extract_story_context(
        self,
        plot_analysis: Any | None,
        previous_results: dict[int, Any] | None,
        episode_number: int
    ) -> StoryContext | None:
        """ストーリーコンテキスト抽出

        Args:
            plot_analysis: プロット解析結果
            previous_results: 前ステップ結果
            episode_number: エピソード番号

        Returns:
            Optional[StoryContext]: ストーリーコンテキスト
        """
        if not plot_analysis:
            return None

        # プロット解析から情報抽出
        current_situation = "新章開始"
        immediate_goals = []
        active_conflicts = []
        previous_events = []
        unresolved_issues = []
        foreshadowing_elements = []
        setup_requirements = []

        if hasattr(plot_analysis, "main_conflicts"):
            active_conflicts = plot_analysis.main_conflicts

        if hasattr(plot_analysis, "key_events"):
            immediate_goals = plot_analysis.key_events[:3]  # 直近3つの目標

        if hasattr(plot_analysis, "previous_connections"):
            previous_events = plot_analysis.previous_connections

        if hasattr(plot_analysis, "next_expectations"):
            setup_requirements = plot_analysis.next_expectations

        # STEP 0からの継続要素
        if previous_results and 0 in previous_results:
            scope_result = previous_results[0]
            if isinstance(scope_result, dict):
                unresolved_issues.extend(scope_result.get("unresolved_plots", []))

        return StoryContext(
            current_situation=current_situation,
            immediate_goals=immediate_goals,
            active_conflicts=active_conflicts,
            previous_events=previous_events,
            unresolved_issues=unresolved_issues,
            foreshadowing_elements=foreshadowing_elements,
            setup_requirements=setup_requirements
        )

    def _extract_technical_context(
        self,
        previous_results: dict[int, Any] | None
    ) -> TechnicalContext:
        """技術的コンテキスト抽出

        Args:
            previous_results: 前ステップ結果

        Returns:
            TechnicalContext: 技術的コンテキスト
        """
        # デフォルト設定
        technical_context = TechnicalContext()

        # 前ステップから情報継承
        if previous_results:
            for step_result in previous_results.values():
                if isinstance(step_result, dict):
                    if "target_word_count" in step_result:
                        technical_context.target_word_count = int(step_result["target_word_count"])
                    if "viewpoint" in step_result:
                        technical_context.viewpoint = step_result["viewpoint"]
                    if "genre_constraints" in step_result:
                        technical_context.genre_constraints = step_result["genre_constraints"]

        return technical_context

    def _create_integrated_result(
        self,
        episode_number: int,
        world_context: WorldContext | None,
        character_contexts: list[CharacterContext],
        story_context: StoryContext | None,
        technical_context: TechnicalContext
    ) -> ContextExtractionResult:
        """統合結果作成

        Args:
            episode_number: エピソード番号
            world_context: 世界観コンテキスト
            character_contexts: キャラクターコンテキスト一覧
            story_context: ストーリーコンテキスト
            technical_context: 技術的コンテキスト

        Returns:
            ContextExtractionResult: 統合コンテキスト抽出結果
        """
        # 重要なコンテキストポイント抽出
        key_points = []
        if world_context:
            key_points.append(f"設定: {world_context.setting_name}")
        if character_contexts:
            key_points.append(f"主要キャラクター: {len(character_contexts)}名")
        if story_context and story_context.active_conflicts:
            key_points.append(f"主要対立: {len(story_context.active_conflicts)}件")

        # コンテキストギャップ識別
        gaps = []
        if not world_context:
            gaps.append("世界観設定が不足")
        if not character_contexts:
            gaps.append("キャラクター情報が不足")
        if not story_context or not story_context.active_conflicts:
            gaps.append("ストーリー対立が不明確")

        # 推奨事項
        recommendations = []
        if gaps:
            recommendations.append("不足コンテキストの補完を推奨")
        if technical_context.target_word_count > 5000:
            recommendations.append("長編向け構成を推奨")

        # 信頼度計算
        confidence = 1.0
        if gaps:
            confidence -= len(gaps) * 0.2
        confidence = max(0.0, min(1.0, confidence))

        return ContextExtractionResult(
            episode_number=episode_number,
            extraction_confidence=confidence,
            world_context=world_context,
            character_contexts=character_contexts,
            story_context=story_context,
            technical_context=technical_context,
            key_context_points=key_points,
            context_gaps=gaps,
            recommendation=recommendations
        )

    def _estimate_character_role(self, char_name: str, char_info: dict[str, Any]) -> str:
        """キャラクター役割推定"""
        if "主人公" in char_name or char_info.get("role") == "protagonist":
            return "protagonist"
        if "敵" in char_name or char_info.get("role") == "antagonist":
            return "antagonist"
        return "supporting"

    def _estimate_character_status(
        self,
        char_name: str,
        char_info: dict[str, Any],
        episode_number: int,
        character_arcs: list[str]
    ) -> str:
        """キャラクター現在状況推定"""
        # 基本状況
        base_status = char_info.get("current_status", "通常状態")

        # エピソード番号による発展推定
        if episode_number == 1:
            return f"{base_status} (導入段階)"
        if episode_number <= 5:
            return f"{base_status} (発展段階)"
        return f"{base_status} (展開段階)"
