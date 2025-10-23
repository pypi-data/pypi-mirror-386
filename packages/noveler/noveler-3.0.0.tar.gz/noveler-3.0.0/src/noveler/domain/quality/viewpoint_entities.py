"""Domain.quality.viewpoint_entities
Where: Domain entities describing viewpoint-aware quality data.
What: Model viewpoint contexts, adjustments, and scoring modifiers.
Why: Support viewpoint-aware quality analysis across workflows.
"""

from __future__ import annotations

from typing import Any

"""視点情報連動型品質評価のドメインエンティティ

ビジネスルール:
- 視点タイプに基づいて品質評価基準を動的調整
- 内省型は内面描写を重視、交流型は会話比率を重視
- 身体交換時は視点の明確さを最優先
"""


from dataclasses import dataclass
from enum import Enum

from noveler.domain.quality.value_objects import QualityScore


class ViewpointType(Enum):
    """視点タイプ"""

    SINGLE_INTROSPECTIVE = "single_introspective"  # 単一視点・内省型
    SINGLE_INTERACTIVE = "single_interactive"  # 単一視点・交流型
    MULTIPLE_PERSPECTIVE = "multiple_perspective"  # 複数視点
    BODY_SWAP = "body_swap"  # 身体交換


class ComplexityLevel(Enum):
    """視点の複雑度"""

    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"


@dataclass(frozen=True)
class ViewpointInfo:
    """視点情報エンティティ"""

    character: str
    viewpoint_type: ViewpointType
    complexity_level: ComplexityLevel
    special_conditions: list[str]
    narrative_focus: str

    def requires_dialogue_weight_adjustment(self) -> bool:
        """会話比率の重み調整が必要かどうか"""
        return (
            self.viewpoint_type == ViewpointType.SINGLE_INTROSPECTIVE or self.complexity_level == ComplexityLevel.HIGH
        )

    def get_dialogue_weight_multiplier(self) -> float:
        """会話比率の重み倍率を取得"""
        if self.viewpoint_type == ViewpointType.SINGLE_INTROSPECTIVE:
            return 0.5  # 内省型は会話比率の重要度を半分に
        if self.complexity_level == ComplexityLevel.HIGH:
            return 0.7  # 複雑度高は会話比率基準を緩和
        return 1.0  # 通常評価

    def requires_narrative_depth_emphasis(self) -> bool:
        """内面描写深度の重視が必要かどうか"""
        return self.viewpoint_type in (ViewpointType.SINGLE_INTROSPECTIVE, ViewpointType.BODY_SWAP)

    def get_narrative_depth_weight_multiplier(self) -> float:
        """内面描写深度の重み倍率を取得"""
        if self.viewpoint_type == ViewpointType.SINGLE_INTROSPECTIVE:
            return 1.5  # 内省型は内面描写を1.5倍重視
        if self.viewpoint_type == ViewpointType.BODY_SWAP:
            return 1.3  # 身体交換時は内面描写を1.3倍重視
        return 1.0  # 通常評価

    def requires_viewpoint_clarity_check(self) -> bool:
        """視点の明確さチェックが必要かどうか"""
        return (
            self.viewpoint_type in (ViewpointType.BODY_SWAP, ViewpointType.MULTIPLE_PERSPECTIVE)
            or self.complexity_level == ComplexityLevel.HIGH
        )


@dataclass(frozen=True)
class QualityEvaluationCriteria:
    """品質評価基準の値オブジェクト"""

    dialogue_weight: float
    narrative_depth_weight: float
    viewpoint_clarity_weight: float
    basic_style_weight: float
    composition_weight: float

    @classmethod
    def create_standard_criteria(cls) -> QualityEvaluationCriteria:
        """標準的な評価基準を作成"""
        return cls(
            dialogue_weight=1.0,
            narrative_depth_weight=1.0,
            viewpoint_clarity_weight=1.0,
            basic_style_weight=1.0,
            composition_weight=1.0,
        )

    @classmethod
    def create_viewpoint_adjusted_criteria(
        cls,
        viewpoint_info: ViewpointInfo,
    ) -> QualityEvaluationCriteria:
        """視点情報に基づいて調整された評価基準を作成"""
        dialogue_weight = viewpoint_info.get_dialogue_weight_multiplier()
        narrative_depth_weight = viewpoint_info.get_narrative_depth_weight_multiplier()

        # 視点の明確さチェックが必要な場合は重みを増加
        viewpoint_clarity_weight = 1.5 if viewpoint_info.requires_viewpoint_clarity_check() else 1.0

        return cls(
            dialogue_weight=dialogue_weight,
            narrative_depth_weight=narrative_depth_weight,
            viewpoint_clarity_weight=viewpoint_clarity_weight,
            basic_style_weight=1.0,  # 基本スタイルは固定
            composition_weight=1.0,  # 構成も固定
        )


class ViewpointBasedQualityEvaluator:
    """視点ベース品質評価ドメインサービス"""

    def evaluate_quality_with_viewpoint(
        self, _text: str, viewpoint: ViewpointInfo, base_quality_scores: dict[str, QualityScore] | None = None
    ) -> dict[str, QualityScore]:
        """視点情報を考慮した品質評価"""

        # 視点情報に基づいて評価基準を調整
        criteria = QualityEvaluationCriteria.create_viewpoint_adjusted_criteria(viewpoint)

        # 各評価項目のスコアを調整
        adjusted_scores = {}
        base_quality_scores = base_quality_scores or {}

        # 会話比率の調整
        if "dialogue_ratio" in base_quality_scores:
            original_score = base_quality_scores["dialogue_ratio"]
            adjusted_score = self._adjust_score_with_weight(
                original_score,
                criteria.dialogue_weight,
            )

            adjusted_scores["dialogue_ratio"] = adjusted_score

        # 内面描写深度の調整
        if "narrative_depth" in base_quality_scores:
            original_score = base_quality_scores["narrative_depth"]
            adjusted_score = self._adjust_score_with_weight(
                original_score,
                criteria.narrative_depth_weight,
            )

            adjusted_scores["narrative_depth"] = adjusted_score

        # その他のスコアはそのまま
        for key, score in base_quality_scores.items():
            if key not in adjusted_scores:
                adjusted_scores[key] = score

        return adjusted_scores

    def _adjust_score_with_weight(self, original_score: QualityScore, weight: float) -> QualityScore:
        """重み付けでスコアを調整"""
        if weight < 1.0:
            # 重要度を下げる場合:スコアを緩和(底上げ)
            adjusted_value = min(100.0, original_score.value + (100 - original_score.value) * (1.0 - weight))
        elif weight > 1.0:
            # 重要度を上げる場合:スコアをより厳格に
            adjusted_value = max(0.0, original_score.value * (2.0 - weight))
        else:
            adjusted_value = original_score.value

        return QualityScore(adjusted_value)

    def generate_viewpoint_context_message(self, viewpoint_info: ViewpointInfo) -> str:
        """視点コンテキストメッセージを生成"""
        messages: list[Any] = []

        # 視点タイプ情報
        type_names = {
            ViewpointType.SINGLE_INTROSPECTIVE: "単一視点・内省型",
            ViewpointType.SINGLE_INTERACTIVE: "単一視点・交流型",
            ViewpointType.MULTIPLE_PERSPECTIVE: "複数視点",
            ViewpointType.BODY_SWAP: "身体交換",
        }
        messages.append(f"📌 視点タイプ: {type_names.get(viewpoint_info.viewpoint_type, '不明')}")

        # 複雑度情報
        messages.append(f"📌 複雑度: {viewpoint_info.complexity_level.value}")

        # 調整された評価項目
        if viewpoint_info.requires_dialogue_weight_adjustment():
            weight = viewpoint_info.get_dialogue_weight_multiplier()
            if weight < 1.0:
                messages.append(f"⚠️ 内省型エピソードのため会話比率は参考値(重み:{weight})")

        if viewpoint_info.requires_narrative_depth_emphasis():
            weight = viewpoint_info.get_narrative_depth_weight_multiplier()
            messages.append(f"✨ 内面描写深度を重視して評価(重み:{weight})")

        if viewpoint_info.requires_viewpoint_clarity_check():
            messages.append("🔍 視点の明確さを特に重視して評価")

        return "\n".join(messages)
