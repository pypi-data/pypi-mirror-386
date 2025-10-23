"""Domain.services.writing_steps.content_optimizer_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""STEP 11: ContentOptimizerService

A38執筆プロンプトガイドのSTEP 11に対応するマイクロサービス。
コンテンツ最適化・構成調整・品質向上を担当。
"""

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService

from noveler.domain.services.writing_steps.base_writing_step import BaseWritingStep, WritingStepResponse


@dataclass
class OptimizationTarget:
    """最適化対象"""

    target_type: str  # "structure", "content", "pacing", "consistency"
    target_area: str  # 具体的な対象領域
    current_score: float  # 現在の評価スコア
    target_score: float   # 目標スコア

    # 最適化方針
    optimization_strategy: str = ""
    specific_actions: list[str] = field(default_factory=list)
    priority_level: int = 5  # 1-10


@dataclass
class ContentAdjustment:
    """コンテンツ調整"""

    adjustment_id: str
    target_section: str  # "opening", "development", "climax", "resolution"
    adjustment_type: str  # "expand", "compress", "rebalance", "enhance"

    # 調整内容
    current_word_count: int
    target_word_count: int
    content_focus: list[str] = field(default_factory=list)

    # 実装指針
    implementation_notes: list[str] = field(default_factory=list)
    quality_criteria: list[str] = field(default_factory=list)


@dataclass
class QualityMetrics:
    """品質メトリクス"""

    # 構造品質
    structure_score: float = 0.0
    pacing_score: float = 0.0
    balance_score: float = 0.0

    # コンテンツ品質
    character_development_score: float = 0.0
    dialogue_quality_score: float = 0.0
    description_quality_score: float = 0.0

    # 技術品質
    consistency_score: float = 0.0
    readability_score: float = 0.0
    engagement_score: float = 0.0

    # 総合評価
    overall_score: float = 0.0


@dataclass
class OptimizationPlan:
    """最適化プラン"""

    episode_number: int
    optimization_confidence: float = 0.0

    # 分析結果
    current_metrics: QualityMetrics | None = None
    improvement_potential: float = 0.0

    # 最適化対象
    optimization_targets: list[OptimizationTarget] = field(default_factory=list)
    content_adjustments: list[ContentAdjustment] = field(default_factory=list)

    # 実装ガイダンス
    optimization_sequence: list[str] = field(default_factory=list)
    quality_checkpoints: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)


@dataclass
class ContentOptimizerResponse(WritingStepResponse):
    """コンテンツ最適化サービス結果"""

    optimization_plan: OptimizationPlan | None = None

    # パフォーマンス情報
    analysis_time_ms: float = 0.0
    optimization_design_time_ms: float = 0.0
    plan_generation_time_ms: float = 0.0

    # 統計情報
    targets_identified: int = 0
    adjustments_planned: int = 0
    potential_improvement: float = 0.0


class ContentOptimizerService(BaseWritingStep):
    """STEP 11: コンテンツ最適化マイクロサービス

    生成された原稿コンテンツを分析し、
    品質向上のための最適化プランを策定。
    """

    def __init__(
        self,
        logger_service: ILoggerService = None,
        **kwargs: Any
    ) -> None:
        """コンテンツ最適化サービス初期化"""
        super().__init__(step_number=11, step_name="content_optimizer", **kwargs)

        self._logger_service = logger_service

    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None = None
    ) -> ContentOptimizerResponse:
        """コンテンツ最適化実行"""
        start_time = time.time()

        try:
            if self._logger_service:
                self._logger_service.info(f"STEP 11 コンテンツ最適化開始: エピソード={episode_number}")

            # 1. 前ステップからコンテンツ情報取得
            manuscript_result, design_info = self._extract_content_info(previous_results)

            # 2. 現在品質分析
            analysis_start = time.time()
            current_metrics = await self._analyze_content_quality(
                manuscript_result, design_info, previous_results
            )
            analysis_time = (time.time() - analysis_start) * 1000

            # 3. 最適化対象特定
            optimization_start = time.time()
            optimization_targets = await self._identify_optimization_targets(
                current_metrics, design_info
            )

            # 4. コンテンツ調整計画
            content_adjustments = await self._plan_content_adjustments(
                optimization_targets, manuscript_result, design_info
            )
            optimization_time = (time.time() - optimization_start) * 1000

            # 5. 最適化プラン生成
            plan_start = time.time()
            optimization_plan = await self._generate_optimization_plan(
                episode_number, current_metrics, optimization_targets,
                content_adjustments
            )
            plan_time = (time.time() - plan_start) * 1000

            # 6. 成功応答作成
            execution_time = (time.time() - start_time) * 1000

            return ContentOptimizerResponse(
                success=True,
                step_number=11,
                step_name="content_optimizer",
                execution_time_ms=execution_time,
                optimization_plan=optimization_plan,

                # パフォーマンス情報
                analysis_time_ms=analysis_time,
                optimization_design_time_ms=optimization_time,
                plan_generation_time_ms=plan_time,

                # 統計情報
                targets_identified=len(optimization_targets),
                adjustments_planned=len(content_adjustments),
                potential_improvement=optimization_plan.improvement_potential
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_message = f"STEP 11 コンテンツ最適化エラー: {e}"

            if self._logger_service:
                self._logger_service.error(error_message)

            return ContentOptimizerResponse(
                success=False,
                step_number=11,
                step_name="content_optimizer",
                execution_time_ms=execution_time,
                error_message=error_message
            )

    def _extract_content_info(
        self,
        previous_results: dict[int, Any] | None
    ) -> tuple[Any | None, dict[str, Any] | None]:
        """コンテンツ情報抽出"""
        manuscript_result = None
        design_info = {}

        if previous_results:
            # STEP 10から原稿生成結果
            if 10 in previous_results:
                step10_result = previous_results[10]
                manuscript_result = step10_result

            # STEP 4からシーン設計情報
            if 4 in previous_results:
                step4_result = previous_results[4]
                if hasattr(step4_result, "design_plan"):
                    design_info["scene_plan"] = step4_result.design_plan

            # STEP 5から対話設計情報
            if 5 in previous_results:
                step5_result = previous_results[5]
                if hasattr(step5_result, "dialogue_result"):
                    design_info["dialogue_design"] = step5_result.dialogue_result

            # STEP 3から叙述構造情報
            if 3 in previous_results:
                step3_result = previous_results[3]
                if hasattr(step3_result, "structure_result"):
                    design_info["narrative_structure"] = step3_result.structure_result

        return manuscript_result, design_info

    async def _analyze_content_quality(
        self,
        manuscript_result: Any | None,
        design_info: dict[str, Any],
        previous_results: dict[int, Any] | None
    ) -> QualityMetrics:
        """コンテンツ品質分析"""
        # 基本メトリクス初期化
        metrics = QualityMetrics()

        # 構造品質評価
        metrics.structure_score = self._evaluate_structure_quality(design_info)

        # ペーシング評価
        metrics.pacing_score = self._evaluate_pacing_quality(design_info)

        # バランス評価
        metrics.balance_score = self._evaluate_content_balance(design_info)

        # キャラクター開発評価
        metrics.character_development_score = self._evaluate_character_development(
            design_info, previous_results
        )

        # 対話品質評価
        metrics.dialogue_quality_score = self._evaluate_dialogue_quality(design_info)

        # 描写品質評価
        metrics.description_quality_score = self._evaluate_description_quality(design_info)

        # 一貫性評価
        metrics.consistency_score = self._evaluate_consistency(design_info)

        # 読みやすさ評価
        metrics.readability_score = self._evaluate_readability(design_info)

        # エンゲージメント評価
        metrics.engagement_score = self._evaluate_engagement(design_info)

        # 総合評価計算
        metrics.overall_score = self._calculate_overall_score(metrics)

        return metrics

    def _evaluate_structure_quality(self, design_info: dict[str, Any]) -> float:
        """構造品質評価"""
        score = 5.0  # 基本スコア

        # シーン設計の品質
        if "scene_plan" in design_info:
            scene_plan = design_info["scene_plan"]
            if hasattr(scene_plan, "scene_blocks"):
                scene_count = len(scene_plan.scene_blocks)
                # 適切なシーン数 (3-7)
                if 3 <= scene_count <= 7:
                    score += 2.0
                elif scene_count > 0:
                    score += 1.0

                # シーン遷移の品質
                if hasattr(scene_plan, "transitions") and scene_plan.transitions:
                    score += 1.5

        # 叙述構造の品質
        if "narrative_structure" in design_info:
            structure = design_info["narrative_structure"]
            if (hasattr(structure, "structure_confidence") and
                structure.structure_confidence > 0.7):
                score += 1.5

        return min(10.0, score)

    def _evaluate_pacing_quality(self, design_info: dict[str, Any]) -> float:
        """ペーシング品質評価"""
        score = 6.0

        # シーン設計からペーシング評価
        if "scene_plan" in design_info:
            scene_plan = design_info["scene_plan"]
            if hasattr(scene_plan, "scene_blocks"):
                # 緊張レベルの変化
                tension_levels = []
                for block in scene_plan.scene_blocks:
                    if hasattr(block, "tension_level"):
                        tension_levels.append(block.tension_level)

                if tension_levels:
                    # 変化の適切さ
                    tension_range = max(tension_levels) - min(tension_levels)
                    if tension_range >= 4:  # 十分な変化
                        score += 2.0
                    elif tension_range >= 2:
                        score += 1.0

        return min(10.0, score)

    def _evaluate_content_balance(self, design_info: dict[str, Any]) -> float:
        """コンテンツバランス評価"""
        score = 6.0

        # 対話・描写・アクションのバランス
        if "scene_plan" in design_info:
            scene_plan = design_info["scene_plan"]
            if hasattr(scene_plan, "scene_blocks"):
                dialogue_ratios = []
                action_ratios = []
                description_ratios = []

                for block in scene_plan.scene_blocks:
                    dialogue_ratios.append(getattr(block, "dialogue_ratio", 0.3))
                    action_ratios.append(getattr(block, "action_ratio", 0.2))
                    description_ratios.append(getattr(block, "description_ratio", 0.5))

                if dialogue_ratios:
                    avg_dialogue = sum(dialogue_ratios) / len(dialogue_ratios)
                    avg_action = sum(action_ratios) / len(action_ratios)
                    avg_description = sum(description_ratios) / len(description_ratios)

                    # 適切なバランス判定 (対話30-50%, アクション10-30%, 描写30-60%)
                    balance_score = 0.0
                    if 0.3 <= avg_dialogue <= 0.5:
                        balance_score += 1.0
                    if 0.1 <= avg_action <= 0.3:
                        balance_score += 1.0
                    if 0.3 <= avg_description <= 0.6:
                        balance_score += 1.0

                    score += balance_score

        return min(10.0, score)

    def _evaluate_character_development(
        self,
        design_info: dict[str, Any],
        previous_results: dict[int, Any] | None
    ) -> float:
        """キャラクター開発評価"""
        score = 5.0

        # キャラクター数と関与度
        character_count = 0
        if "dialogue_design" in design_info:
            dialogue_design = design_info["dialogue_design"]
            if hasattr(dialogue_design, "character_voices"):
                character_count = len(dialogue_design.character_voices)

                # 適切なキャラクター数
                if 2 <= character_count <= 5:
                    score += 2.0
                elif character_count > 0:
                    score += 1.0

                # 音声設計の詳細度
                detailed_voices = sum(1 for voice in dialogue_design.character_voices
                                    if voice.speech_patterns or voice.catchphrases)
                if detailed_voices > 0:
                    score += 2.0 * (detailed_voices / character_count)

        return min(10.0, score)

    def _evaluate_dialogue_quality(self, design_info: dict[str, Any]) -> float:
        """対話品質評価"""
        score = 5.0

        if "dialogue_design" in design_info:
            dialogue_design = design_info["dialogue_design"]

            # 対話シーンの存在
            if hasattr(dialogue_design, "dialogue_scenes"):
                scene_count = len(dialogue_design.dialogue_scenes)
                if scene_count > 0:
                    score += 2.0

                    # 対話交換の詳細度
                    total_exchanges = sum(len(scene.dialogue_exchanges)
                                        for scene in dialogue_design.dialogue_scenes)
                    if total_exchanges > 0:
                        score += 2.0

                        # 目的の多様性
                        purposes = set()
                        for scene in dialogue_design.dialogue_scenes:
                            for exchange in scene.dialogue_exchanges:
                                purposes.add(exchange.primary_purpose)

                        if len(purposes) >= 2:
                            score += 1.0

        return min(10.0, score)

    def _evaluate_description_quality(self, design_info: dict[str, Any]) -> float:
        """描写品質評価"""
        score = 6.0

        # シーン設定の詳細度
        if "scene_plan" in design_info:
            scene_plan = design_info["scene_plan"]
            if hasattr(scene_plan, "scene_blocks"):
                location_set = sum(1 for block in scene_plan.scene_blocks
                                 if hasattr(block, "location") and block.location)
                time_set = sum(1 for block in scene_plan.scene_blocks
                             if hasattr(block, "time_context") and block.time_context)

                total_blocks = len(scene_plan.scene_blocks)
                if total_blocks > 0:
                    location_ratio = location_set / total_blocks
                    time_ratio = time_set / total_blocks

                    score += 2.0 * location_ratio + 1.0 * time_ratio

        return min(10.0, score)

    def _evaluate_consistency(self, design_info: dict[str, Any]) -> float:
        """一貫性評価"""
        score = 7.0

        # キャラクター音声の一貫性
        if "dialogue_design" in design_info:
            dialogue_design = design_info["dialogue_design"]
            if (hasattr(dialogue_design, "character_voices") and
                dialogue_design.character_voices):
                # 音声特性が設定されているキャラクター
                voiced_characters = sum(1 for voice in dialogue_design.character_voices
                                      if voice.speaking_style != "casual")
                total_characters = len(dialogue_design.character_voices)

                if total_characters > 0:
                    consistency_ratio = voiced_characters / total_characters
                    score += 2.0 * consistency_ratio

        return min(10.0, score)

    def _evaluate_readability(self, design_info: dict[str, Any]) -> float:
        """読みやすさ評価"""
        score = 7.0

        # 構造の明確性
        if "narrative_structure" in design_info:
            structure = design_info["narrative_structure"]
            if hasattr(structure, "writing_guidelines") and structure.writing_guidelines:
                score += 1.5

            if hasattr(structure, "consistency_checks") and structure.consistency_checks:
                score += 1.0

        return min(10.0, score)

    def _evaluate_engagement(self, design_info: dict[str, Any]) -> float:
        """エンゲージメント評価"""
        score = 6.0

        # 緊張・感情の変化
        if "scene_plan" in design_info:
            scene_plan = design_info["scene_plan"]
            if hasattr(scene_plan, "scene_blocks"):
                emotional_variety = set()
                for block in scene_plan.scene_blocks:
                    if hasattr(block, "emotional_tone"):
                        emotional_variety.add(block.emotional_tone)

                # 感情の多様性
                if len(emotional_variety) >= 3:
                    score += 2.0
                elif len(emotional_variety) >= 2:
                    score += 1.0

        return min(10.0, score)

    def _calculate_overall_score(self, metrics: QualityMetrics) -> float:
        """総合評価計算"""
        weights = {
            "structure": 0.15,
            "pacing": 0.15,
            "balance": 0.1,
            "character_development": 0.15,
            "dialogue_quality": 0.15,
            "description_quality": 0.1,
            "consistency": 0.1,
            "readability": 0.05,
            "engagement": 0.05
        }

        return (
            metrics.structure_score * weights["structure"] +
            metrics.pacing_score * weights["pacing"] +
            metrics.balance_score * weights["balance"] +
            metrics.character_development_score * weights["character_development"] +
            metrics.dialogue_quality_score * weights["dialogue_quality"] +
            metrics.description_quality_score * weights["description_quality"] +
            metrics.consistency_score * weights["consistency"] +
            metrics.readability_score * weights["readability"] +
            metrics.engagement_score * weights["engagement"]
        )


    async def _identify_optimization_targets(
        self,
        metrics: QualityMetrics,
        design_info: dict[str, Any]
    ) -> list[OptimizationTarget]:
        """最適化対象特定"""
        targets = []

        # 低スコア項目を最適化対象として特定
        threshold = 7.0

        if metrics.structure_score < threshold:
            targets.append(OptimizationTarget(
                target_type="structure",
                target_area="シーン構成・遷移",
                current_score=metrics.structure_score,
                target_score=8.0,
                optimization_strategy="シーン構成の見直しと遷移改善",
                specific_actions=["シーン配置調整", "遷移の自然化", "構成バランス改善"],
                priority_level=9
            ))

        if metrics.dialogue_quality_score < threshold:
            targets.append(OptimizationTarget(
                target_type="content",
                target_area="対話品質",
                current_score=metrics.dialogue_quality_score,
                target_score=8.5,
                optimization_strategy="対話の自然性向上とキャラクター性強化",
                specific_actions=["キャラクター音声の明確化", "対話目的の強化", "会話リズム改善"],
                priority_level=8
            ))

        if metrics.pacing_score < threshold:
            targets.append(OptimizationTarget(
                target_type="pacing",
                target_area="テンポ・リズム",
                current_score=metrics.pacing_score,
                target_score=8.0,
                optimization_strategy="緊張と緩和のリズム調整",
                specific_actions=["緊張レベル調整", "場面転換の最適化", "情報提示ペース改善"],
                priority_level=7
            ))

        if metrics.character_development_score < threshold:
            targets.append(OptimizationTarget(
                target_type="content",
                target_area="キャラクター描写",
                current_score=metrics.character_development_score,
                target_score=8.0,
                optimization_strategy="キャラクター個性の強化と関係性深化",
                specific_actions=["個性的特徴の強化", "内面描写の充実", "関係性発展"],
                priority_level=8
            ))

        return targets

    async def _plan_content_adjustments(
        self,
        optimization_targets: list[OptimizationTarget],
        manuscript_result: Any | None,
        design_info: dict[str, Any]
    ) -> list[ContentAdjustment]:
        """コンテンツ調整計画"""
        adjustments = []

        # シーン構成調整
        if any(target.target_type == "structure" for target in optimization_targets):
            if "scene_plan" in design_info:
                scene_plan = design_info["scene_plan"]
                adjustments.extend(self._plan_structure_adjustments(scene_plan))

        # 対話品質調整
        if any(target.target_area == "対話品質" for target in optimization_targets):
            adjustments.append(ContentAdjustment(
                adjustment_id="dialogue_enhancement",
                target_section="development",
                adjustment_type="enhance",
                current_word_count=0,
                target_word_count=0,
                content_focus=["対話の自然性", "キャラクター音声", "会話目的明確化"],
                implementation_notes=["キャラクター固有表現の追加", "対話の目的明確化", "サブテキストの活用"],
                quality_criteria=["自然な会話流れ", "キャラクター識別可能", "目的達成"]
            ))

        # ペーシング調整
        if any(target.target_type == "pacing" for target in optimization_targets):
            adjustments.append(ContentAdjustment(
                adjustment_id="pacing_adjustment",
                target_section="development",
                adjustment_type="rebalance",
                current_word_count=0,
                target_word_count=0,
                content_focus=["緊張と緩和のバランス", "情報提示ペース", "場面転換"],
                implementation_notes=["緊張カーブの調整", "情報の段階的開示", "適切な間の設置"],
                quality_criteria=["読者の関心維持", "自然な情報流れ", "適切な緊張感"]
            ))

        return adjustments

    def _plan_structure_adjustments(self, scene_plan: Any) -> list[ContentAdjustment]:
        """構造調整計画"""
        adjustments = []

        if hasattr(scene_plan, "scene_blocks"):
            total_words = getattr(scene_plan, "total_estimated_words", 4000)
            len(scene_plan.scene_blocks)

            # 各シーンの最適化
            for i, block in enumerate(scene_plan.scene_blocks):
                section = block.position if hasattr(block, "position") else "development"
                current_words = getattr(block, "estimated_word_count", 0)

                # 重要シーンの拡張
                if (hasattr(block, "tension_level") and
                    block.tension_level >= 8 and
                    current_words < total_words * 0.25):

                    adjustments.append(ContentAdjustment(
                        adjustment_id=f"expand_scene_{i+1}",
                        target_section=section,
                        adjustment_type="expand",
                        current_word_count=current_words,
                        target_word_count=int(current_words * 1.3),
                        content_focus=["詳細描写", "感情表現", "緊張演出"],
                        implementation_notes=["重要場面の詳細化", "感情描写の充実", "臨場感の向上"]
                    ))

        return adjustments

    async def _generate_optimization_plan(
        self,
        episode_number: int,
        current_metrics: QualityMetrics,
        optimization_targets: list[OptimizationTarget],
        content_adjustments: list[ContentAdjustment]
    ) -> OptimizationPlan:
        """最適化プラン生成"""
        # 改善ポテンシャル計算
        improvement_potential = 0.0
        if optimization_targets:
            total_gap = sum(target.target_score - target.current_score
                          for target in optimization_targets)
            improvement_potential = min(total_gap / len(optimization_targets), 3.0)

        # 最適化シーケンス
        optimization_sequence = self._create_optimization_sequence(optimization_targets)

        # 品質チェックポイント
        quality_checkpoints = [
            "構造の明確性確認",
            "キャラクター一貫性チェック",
            "対話の自然性確認",
            "ペーシングバランス確認",
            "全体品質最終確認"
        ]

        # 成功基準
        success_criteria = [
            "総合品質スコア 8.0以上",
            "重要項目スコア 7.5以上",
            "読者エンゲージメント向上",
            "技術的一貫性維持"
        ]

        # 信頼度計算
        confidence = self._calculate_optimization_confidence(
            current_metrics, optimization_targets
        )

        return OptimizationPlan(
            episode_number=episode_number,
            optimization_confidence=confidence,
            current_metrics=current_metrics,
            improvement_potential=improvement_potential,
            optimization_targets=optimization_targets,
            content_adjustments=content_adjustments,
            optimization_sequence=optimization_sequence,
            quality_checkpoints=quality_checkpoints,
            success_criteria=success_criteria
        )

    def _create_optimization_sequence(
        self,
        optimization_targets: list[OptimizationTarget]
    ) -> list[str]:
        """最適化シーケンス作成"""
        # 優先度順にソート
        sorted_targets = sorted(optimization_targets,
                               key=lambda x: x.priority_level, reverse=True)

        sequence = []
        for target in sorted_targets:
            sequence.append(f"{target.target_area}の最適化: {target.optimization_strategy}")

        return sequence

    def _calculate_optimization_confidence(
        self,
        current_metrics: QualityMetrics,
        optimization_targets: list[OptimizationTarget]
    ) -> float:
        """最適化信頼度計算"""
        base_confidence = 0.7

        # 現在品質による調整
        if current_metrics.overall_score >= 7.0:
            base_confidence += 0.2
        elif current_metrics.overall_score < 5.0:
            base_confidence -= 0.2

        # 最適化対象数による調整
        if len(optimization_targets) <= 3:
            base_confidence += 0.1
        elif len(optimization_targets) > 5:
            base_confidence -= 0.1

        return max(0.0, min(1.0, base_confidence))
