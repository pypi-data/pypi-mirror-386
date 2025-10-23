"""Domain.services.writing_steps.narrative_structure_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""STEP 3: NarrativeStructureService

A38執筆プロンプトガイドのSTEP 3に対応するマイクロサービス。
叙述構造設計・視点制御・時系列構成を担当。
"""

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService

from noveler.domain.services.writing_steps.base_writing_step import BaseWritingStep, WritingStepResponse


@dataclass
class ViewpointConfiguration:
    """視点設定"""

    primary_viewpoint: str  # "一人称", "三人称単元視点", "三人称全知視点", "三人称多元視点"
    viewpoint_character: str
    consistency_level: str = "厳格"  # "厳格", "標準", "柔軟"

    # 視点切り替え設定
    allow_viewpoint_shifts: bool = False
    shift_points: list[str] = field(default_factory=list)
    transition_style: str = "明確"  # "明確", "暗示", "自然"


@dataclass
class TimelineStructure:
    """時系列構造"""

    narrative_order: str  # "chronological", "flashback", "flash_forward", "mixed"
    time_span: str  # "単一場面", "数時間", "一日", "数日", "それ以上"

    # 時間構成要素
    scene_breaks: list[str] = field(default_factory=list)
    temporal_transitions: list[str] = field(default_factory=list)
    pacing_segments: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class NarrativeFlow:
    """叙述流れ"""

    opening_style: str  # "action", "dialogue", "description", "internal_monologue"
    development_pattern: str  # "linear", "spiral", "episodic", "climactic"
    closing_approach: str  # "resolution", "cliffhanger", "reflection", "transition"

    # 流れの制御
    tension_curve: list[dict[str, Any]] = field(default_factory=list)
    emotional_beats: list[str] = field(default_factory=list)
    information_reveal_pattern: str = "gradual"  # "gradual", "sudden", "layered"


@dataclass
class StructuralElements:
    """構造要素"""

    # 基本構造
    act_structure: str  # "三幕構成", "四幕構成", "起承転結"
    scene_count_estimate: int

    # 要素配置
    key_scenes: list[dict[str, Any]] = field(default_factory=list)
    transition_points: list[str] = field(default_factory=list)
    emphasis_moments: list[str] = field(default_factory=list)


@dataclass
class NarrativeStructureResult:
    """叙述構造設計結果"""

    episode_number: int
    structure_confidence: float = 0.0

    # 構造要素
    viewpoint_config: ViewpointConfiguration | None = None
    timeline_structure: TimelineStructure | None = None
    narrative_flow: NarrativeFlow | None = None
    structural_elements: StructuralElements | None = None

    # 実装ガイド
    writing_guidelines: list[str] = field(default_factory=list)
    technical_notes: list[str] = field(default_factory=list)
    consistency_checks: list[str] = field(default_factory=list)


@dataclass
class NarrativeStructureResponse(WritingStepResponse):
    """叙述構造サービス結果"""

    structure_result: NarrativeStructureResult | None = None

    # パフォーマンス情報
    viewpoint_analysis_time_ms: float = 0.0
    timeline_design_time_ms: float = 0.0
    flow_optimization_time_ms: float = 0.0

    # 統計情報
    guidelines_generated: int = 0
    consistency_checks_created: int = 0


class NarrativeStructureService(BaseWritingStep):
    """STEP 3: 叙述構造設計マイクロサービス

    プロットとコンテキストを基に最適な叙述構造を設計。
    視点・時系列・叙述流れの統合的な構成を行う。
    """

    def __init__(
        self,
        logger_service: ILoggerService = None,
        **kwargs: Any
    ) -> None:
        """叙述構造サービス初期化"""
        super().__init__(step_number=3, step_name="narrative_structure", **kwargs)

        self._logger_service = logger_service

    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None = None
    ) -> NarrativeStructureResponse:
        """叙述構造設計実行"""
        start_time = time.time()

        try:
            if self._logger_service:
                self._logger_service.info(f"STEP 3 叙述構造設計開始: エピソード={episode_number}")

            # 1. 前ステップ結果から情報取得
            plot_analysis, context_result = self._extract_previous_analysis(previous_results)

            # 2. 視点構成設計
            viewpoint_start = time.time()
            viewpoint_config = await self._design_viewpoint_configuration(
                episode_number, context_result, plot_analysis
            )
            viewpoint_time = (time.time() - viewpoint_start) * 1000

            # 3. 時系列構造設計
            timeline_start = time.time()
            timeline_structure = await self._design_timeline_structure(
                episode_number, plot_analysis, context_result
            )
            timeline_time = (time.time() - timeline_start) * 1000

            # 4. 叙述流れ最適化
            flow_start = time.time()
            narrative_flow = await self._optimize_narrative_flow(
                episode_number, plot_analysis, viewpoint_config, timeline_structure
            )
            flow_time = (time.time() - flow_start) * 1000

            # 5. 構造要素統合
            structural_elements = await self._integrate_structural_elements(
                plot_analysis, timeline_structure, narrative_flow
            )

            # 6. ガイドライン生成
            guidelines, tech_notes, checks = self._generate_implementation_guidance(
                viewpoint_config, timeline_structure, narrative_flow
            )

            # 7. 統合結果作成
            structure_result = NarrativeStructureResult(
                episode_number=episode_number,
                structure_confidence=self._calculate_confidence(
                    viewpoint_config, timeline_structure, narrative_flow
                ),
                viewpoint_config=viewpoint_config,
                timeline_structure=timeline_structure,
                narrative_flow=narrative_flow,
                structural_elements=structural_elements,
                writing_guidelines=guidelines,
                technical_notes=tech_notes,
                consistency_checks=checks
            )

            # 8. 成功応答作成
            execution_time = (time.time() - start_time) * 1000

            return NarrativeStructureResponse(
                success=True,
                step_number=3,
                step_name="narrative_structure",
                execution_time_ms=execution_time,
                structure_result=structure_result,

                # パフォーマンス情報
                viewpoint_analysis_time_ms=viewpoint_time,
                timeline_design_time_ms=timeline_time,
                flow_optimization_time_ms=flow_time,

                # 統計情報
                guidelines_generated=len(guidelines),
                consistency_checks_created=len(checks)
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_message = f"STEP 3 叙述構造設計エラー: {e}"

            if self._logger_service:
                self._logger_service.error(error_message)

            return NarrativeStructureResponse(
                success=False,
                step_number=3,
                step_name="narrative_structure",
                execution_time_ms=execution_time,
                error_message=error_message
            )

    def _extract_previous_analysis(
        self,
        previous_results: dict[int, Any] | None
    ) -> tuple[Any | None, Any | None]:
        """前ステップ解析結果抽出"""
        plot_analysis = None
        context_result = None

        if previous_results:
            # STEP 1からプロット解析結果
            if 1 in previous_results:
                step1_result = previous_results[1]
                if hasattr(step1_result, "analysis_result"):
                    plot_analysis = step1_result.analysis_result

            # STEP 2からコンテキスト結果
            if 2 in previous_results:
                step2_result = previous_results[2]
                if hasattr(step2_result, "context_result"):
                    context_result = step2_result.context_result

        return plot_analysis, context_result

    async def _design_viewpoint_configuration(
        self,
        episode_number: int,
        context_result: Any | None,
        plot_analysis: Any | None
    ) -> ViewpointConfiguration:
        """視点構成設計"""
        # デフォルト設定
        primary_viewpoint = "三人称単元視点"
        viewpoint_character = "主人公"

        # コンテキストから視点キャラクター特定
        if context_result and hasattr(context_result, "character_contexts"):
            for char_context in context_result.character_contexts:
                if char_context.role == "protagonist":
                    viewpoint_character = char_context.character_name
                    break

        # 技術的コンテキストから視点設定取得
        if context_result and hasattr(context_result, "technical_context"):
            tech_context = context_result.technical_context
            if tech_context and hasattr(tech_context, "viewpoint"):
                primary_viewpoint = tech_context.viewpoint
            if tech_context and hasattr(tech_context, "viewpoint_character"):
                viewpoint_character = tech_context.viewpoint_character

        # プロット複雑度による視点切り替え判定
        allow_shifts = False
        if plot_analysis and hasattr(plot_analysis, "main_conflicts"):
            # 複数の複雑な対立がある場合は視点切り替えを検討
            if len(plot_analysis.main_conflicts) > 2:
                allow_shifts = True

        return ViewpointConfiguration(
            primary_viewpoint=primary_viewpoint,
            viewpoint_character=viewpoint_character,
            consistency_level="厳格" if not allow_shifts else "標準",
            allow_viewpoint_shifts=allow_shifts,
            shift_points=[] if not allow_shifts else ["中盤", "クライマックス"],
            transition_style="明確"
        )

    async def _design_timeline_structure(
        self,
        episode_number: int,
        plot_analysis: Any | None,
        context_result: Any | None
    ) -> TimelineStructure:
        """時系列構造設計"""
        # 基本時系列設定
        narrative_order = "chronological"
        time_span = "数時間"

        # プロット分析から時系列複雑度判定
        if plot_analysis and hasattr(plot_analysis, "plot_elements"):
            for element in plot_analysis.plot_elements:
                if hasattr(element, "element_type") and element.element_type == "event":
                    if "回想" in element.description or "flashback" in element.description.lower():
                        narrative_order = "flashback"
                    elif "予知" in element.description or "foreshadow" in element.description.lower():
                        narrative_order = "flash_forward"

        # ストーリーコンテキストから時間幅推定
        if context_result and hasattr(context_result, "story_context"):
            story_context = context_result.story_context
            if story_context and hasattr(story_context, "immediate_goals"):
                # 目標数から時間幅推定
                goal_count = len(story_context.immediate_goals)
                if goal_count == 1:
                    time_span = "単一場面"
                elif goal_count <= 3:
                    time_span = "数時間"
                else:
                    time_span = "一日"

        # 場面切り替えポイント
        scene_breaks = ["導入後", "展開中盤", "クライマックス前"]
        temporal_transitions = ["時間経過", "場面転換", "視点移動"]

        return TimelineStructure(
            narrative_order=narrative_order,
            time_span=time_span,
            scene_breaks=scene_breaks,
            temporal_transitions=temporal_transitions,
            pacing_segments=[
                {"section": "導入", "pace": "標準", "duration": "20%"},
                {"section": "展開", "pace": "加速", "duration": "60%"},
                {"section": "結末", "pace": "調整", "duration": "20%"}
            ]
        )

    async def _optimize_narrative_flow(
        self,
        episode_number: int,
        plot_analysis: Any | None,
        viewpoint_config: ViewpointConfiguration,
        timeline_structure: TimelineStructure
    ) -> NarrativeFlow:
        """叙述流れ最適化"""
        # 開始スタイル決定
        opening_style = "action"  # デフォルト
        if episode_number == 1:
            opening_style = "description"  # 第1話は世界観紹介
        elif plot_analysis and hasattr(plot_analysis, "main_conflicts"):
            if plot_analysis.main_conflicts:
                opening_style = "action"  # 対立がある場合はアクション

        # 発展パターン
        development_pattern = "linear"
        if timeline_structure.narrative_order != "chronological":
            development_pattern = "spiral"

        # 結末アプローチ
        closing_approach = "transition"  # 中間エピソードは次への移行
        if episode_number >= 10:
            closing_approach = "resolution"  # 後半は解決志向

        # 緊張曲線設計
        tension_curve = [
            {"point": "開始", "level": 3, "description": "導入の引きつけ"},
            {"point": "25%", "level": 5, "description": "問題提起"},
            {"point": "50%", "level": 7, "description": "中盤の盛り上がり"},
            {"point": "75%", "level": 9, "description": "クライマックス"},
            {"point": "終了", "level": 4, "description": "余韻と次への期待"}
        ]

        # 感情的な拍子
        emotional_beats = ["期待感", "緊張", "驚き", "感動", "安堵"]

        return NarrativeFlow(
            opening_style=opening_style,
            development_pattern=development_pattern,
            closing_approach=closing_approach,
            tension_curve=tension_curve,
            emotional_beats=emotional_beats,
            information_reveal_pattern="gradual"
        )

    async def _integrate_structural_elements(
        self,
        plot_analysis: Any | None,
        timeline_structure: TimelineStructure,
        narrative_flow: NarrativeFlow
    ) -> StructuralElements:
        """構造要素統合"""
        # 基本構造設定
        act_structure = "三幕構成"
        scene_count_estimate = 5  # デフォルト

        # プロット分析から構造推定
        if plot_analysis and hasattr(plot_analysis, "structure"):
            structure_info = plot_analysis.structure
            if structure_info and hasattr(structure_info, "act_structure"):
                act_structure = structure_info.act_structure

        # 時間幅からシーン数推定
        time_span = timeline_structure.time_span
        if time_span == "単一場面":
            scene_count_estimate = 3
        elif time_span == "数時間":
            scene_count_estimate = 5
        elif time_span == "一日":
            scene_count_estimate = 7
        else:
            scene_count_estimate = 10

        # 重要シーン配置
        key_scenes = [
            {"type": "opening", "position": "0-10%", "purpose": "導入・状況設定"},
            {"type": "inciting", "position": "10-25%", "purpose": "きっかけ・問題提起"},
            {"type": "development", "position": "25-75%", "purpose": "展開・対立発展"},
            {"type": "climax", "position": "75-90%", "purpose": "クライマックス"},
            {"type": "resolution", "position": "90-100%", "purpose": "結末・次への準備"}
        ]

        return StructuralElements(
            act_structure=act_structure,
            scene_count_estimate=scene_count_estimate,
            key_scenes=key_scenes,
            transition_points=timeline_structure.temporal_transitions,
            emphasis_moments=narrative_flow.emotional_beats
        )

    def _generate_implementation_guidance(
        self,
        viewpoint_config: ViewpointConfiguration,
        timeline_structure: TimelineStructure,
        narrative_flow: NarrativeFlow
    ) -> tuple[list[str], list[str], list[str]]:
        """実装ガイダンス生成"""
        guidelines = []
        tech_notes = []
        consistency_checks = []

        # 視点ガイドライン
        guidelines.append(f"視点: {viewpoint_config.primary_viewpoint}で一貫して記述")
        guidelines.append(f"視点人物: {viewpoint_config.viewpoint_character}の視点を維持")

        if viewpoint_config.allow_viewpoint_shifts:
            guidelines.append("視点切り替え時は明確な区切りを設ける")
            tech_notes.append("視点切り替えは段落区切り・場面転換で明示")

        # 時系列ガイドライン
        if timeline_structure.narrative_order != "chronological":
            guidelines.append(f"時系列: {timeline_structure.narrative_order}構成を使用")
            tech_notes.append("時系列の切り替えは読者に分かりやすく提示")

        # 叙述流れガイドライン
        guidelines.append(f"開始: {narrative_flow.opening_style}で始める")
        guidelines.append(f"発展: {narrative_flow.development_pattern}パターンで展開")
        guidelines.append(f"結末: {narrative_flow.closing_approach}で締めくくる")

        # 整合性チェック
        consistency_checks.append("視点の一貫性（視点キャラクターの知らない情報を書かない）")
        consistency_checks.append("時系列の整合性（時間の矛盾がないか）")
        consistency_checks.append("情報提示の整合性（読者の理解度に配慮）")

        return guidelines, tech_notes, consistency_checks

    def _calculate_confidence(
        self,
        viewpoint_config: ViewpointConfiguration | None,
        timeline_structure: TimelineStructure | None,
        narrative_flow: NarrativeFlow | None
    ) -> float:
        """構造設計信頼度計算"""
        confidence = 0.0

        if viewpoint_config:
            confidence += 0.3
        if timeline_structure:
            confidence += 0.3
        if narrative_flow:
            confidence += 0.4

        return min(1.0, confidence)
