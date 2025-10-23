"""Domain.quality.entities
Where: Domain entities representing quality metrics and contexts.
What: Encapsulate quality scores, violations, and related metadata.
Why: Provide a reusable model for quality evaluation workflows.
"""

from __future__ import annotations

"""品質管理ドメインのエンティティ"""


import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from noveler.domain.quality.value_objects import (
    AdaptationStrength,
    ErrorSeverity,
    QualityScore,
    RuleCategory,
)

if TYPE_CHECKING:
    from noveler.domain.quality.value_objects import (
        ErrorContext,
        LineNumber,
    )


@dataclass
class QualityViolation:
    """品質違反エンティティ"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_name: str = ""
    category: RuleCategory = RuleCategory.BASIC_STYLE
    severity: ErrorSeverity = ErrorSeverity.WARNING
    line_number: LineNumber | None = None
    message: str = ""
    context: ErrorContext | None = None
    suggestion: str | None = None

    def is_critical(self) -> bool:
        """重大な違反かどうか"""
        return self.severity == ErrorSeverity.ERROR

    def is_auto_fixable(self) -> bool:
        """自動修正可能かどうか"""
        return self.suggestion is not None

    def get_display_message(self) -> str:
        """表示用メッセージを生成"""
        msg = f"[{self.severity.value}] {self.message}"
        if self.line_number:
            msg = f"{self.line_number}: {msg}"
        if self.context:
            msg += f"\n  問題箇所: {self.context.get_highlighted_text()}"
        if self.suggestion:
            msg += f"\n  修正案: {self.suggestion}"
        return msg


@dataclass
class AdaptiveQualityEvaluator:
    """適応的品質評価エンティティ(学習モデル統合)"""

    evaluator_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    learning_model_path: str | None = None
    current_policy: QualityAdaptationPolicy | None = None
    is_trained: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def has_learning_model(self) -> bool:
        """学習モデルが利用可能かどうか"""
        return self.learning_model_path is not None and self.is_trained

    def is_ready_for_adaptive_evaluation(self) -> bool:
        """適応的評価の準備ができているかどうか"""
        return self.has_learning_model()

    def evaluate_adaptively(
        self, standard_scores: dict[str, QualityScore], context: dict[str, Any]
    ) -> dict[str, QualityScore]:
        """適応的評価を実行"""
        if not self.is_ready_for_adaptive_evaluation():
            return standard_scores

        adapted_scores = {}
        for metric, score in standard_scores.items():
            adaptation_strength = self.get_adaptation_strength(metric)
            adapted_value = self._apply_adaptation(score.value, adaptation_strength, context)
            adapted_scores[metric] = QualityScore(adapted_value)

        # 適応的評価固有の情報を追加
        adapted_scores["adaptation_confidence"] = QualityScore(0.8)  # デフォルト信頼度
        adapted_scores["learning_source"] = "project_specific_model"

        return adapted_scores

    def apply_adaptation_policy(self, policy: dict[str, Any]) -> None:
        """適応ポリシーを適用"""
        self.current_policy = policy

    def has_adaptation_policy(self) -> bool:
        """適応ポリシーが設定されているかどうか"""
        return self.current_policy is not None

    def get_adaptation_strength(self, metric: str) -> AdaptationStrength:
        """メトリックの適応強度を取得"""
        if not self.current_policy:
            return AdaptationStrength.WEAK
        return self.current_policy.adaptations.get(metric, AdaptationStrength.WEAK)

    def _apply_adaptation(
        self, score: float, strength: AdaptationStrength, context: dict[str, Any] | None = None
    ) -> float:
        """適応強度に基づいてスコアを調整"""
        if strength == AdaptationStrength.WEAK:
            multiplier = 1.05
        elif strength == AdaptationStrength.MODERATE:
            multiplier = 1.15
        elif strength == AdaptationStrength.STRONG:
            multiplier = 1.25
        else:
            multiplier = 1.0

        # ジャンル特化調整
        if context and hasattr(context, "genre") and hasattr(context, "viewpoint_type"):
            if context.genre == "body_swap_fantasy" and "character_consistency" in context.viewpoint_type:
                multiplier *= 1.1

        return min(100.0, score * multiplier)


@dataclass
class QualityAdaptationPolicy:
    """品質適応ポリシーエンティティ"""

    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    adaptations: dict[str, AdaptationStrength] = field(default_factory=dict)
    confidence_threshold: float = 0.7
    created_at: datetime = field(default_factory=datetime.now)

    def add_adaptation(self, metric: str, strength: AdaptationStrength) -> None:
        """適応設定を追加"""
        self.adaptations[metric] = strength

    def get_adaptation_strength(self, metric: str) -> AdaptationStrength:
        """メトリックの適応強度を取得"""
        return self.adaptations.get(metric, AdaptationStrength.WEAK)

    def is_applicable(self, confidence: float) -> bool:
        """信頼度に基づいて適用可能かどうか判定"""
        return confidence >= self.confidence_threshold

    def get_coverage_metrics(self) -> list[str]:
        """カバーされているメトリックの一覧"""
        return list(self.adaptations.keys())


@dataclass
class QualityReport:
    """品質レポートエンティティ"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    episode_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    violations: list[QualityViolation] = field(default_factory=list)
    auto_fixed_count: int = 0

    def add_violation(self, violation: QualityViolation) -> None:
        """違反を追加"""
        self.violations.append(violation)

    def get_violations_by_severity(self, severity: str) -> list[QualityViolation]:
        """重要度別に違反を取得"""
        return [v for v in self.violations if v.severity == severity]

    def get_violations_by_category(self, category: str) -> list[QualityViolation]:
        """カテゴリー別に違反を取得"""
        return [v for v in self.violations if v.category == category]

    def get_critical_violations(self) -> list[QualityViolation]:
        """重大な違反のみ取得"""
        return [v for v in self.violations if v.is_critical()]

    def get_auto_fixable_violations(self) -> list[QualityViolation]:
        """自動修正可能な違反のみ取得"""
        return [v for v in self.violations if v.is_auto_fixable()]

    def calculate_score(self) -> QualityScore:
        """品質スコアを計算"""
        if not self.violations:
            return QualityScore(100.0)

        base_score = 100.0
        for violation in self.violations:
            if violation.severity == ErrorSeverity.ERROR:
                base_score -= 10.0
            elif violation.severity == ErrorSeverity.WARNING:
                base_score -= 3.0
            elif violation.severity == ErrorSeverity.INFO:
                base_score -= 1.0

        # スコアは0以上に制限
        return QualityScore(max(0.0, base_score))

    def get_summary(self) -> dict[str, int]:
        """サマリー情報を取得"""
        return {
            "total_violations": len(self.violations),
            "errors": len(self.get_violations_by_severity(ErrorSeverity.ERROR)),
            "warnings": len(self.get_violations_by_severity(ErrorSeverity.WARNING)),
            "info": len(self.get_violations_by_severity(ErrorSeverity.INFO)),
            "auto_fixable": len(self.get_auto_fixable_violations()),
            "auto_fixed": self.auto_fixed_count,
        }
