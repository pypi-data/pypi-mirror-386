#!/usr/bin/env python3

"""Domain.entities.holistic_analysis_result
Where: Domain entity representing holistic analysis outcomes.
What: Aggregates multi-dimensional analysis metrics and insights.
Why: Provides a comprehensive view of manuscript health.
"""

from __future__ import annotations

"""統合分析結果エンティティ

統合コンテキスト分析の結果を包括的に管理するドメインエンティティ。
直接Claude分析レベルの詳細度と豊富な情報量を提供。
"""


from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.holistic_score import HolisticScore

if TYPE_CHECKING:
    from datetime import timedelta


@dataclass
class PhaseAnalysis:
    """段階別分析結果"""

    score: float
    insights_count: int
    passed_items: int = 0
    failed_items: int = 0
    critical_issues: list[str] = field(default_factory=list)
    improvements: list[dict[str, Any]] = field(default_factory=list)

    def get_pass_rate(self) -> float:
        """合格率の計算

        Returns:
            float: 合格率（0.0-1.0）
        """
        total = self.passed_items + self.failed_items
        if total == 0:
            return 0.0
        return self.passed_items / total


@dataclass
class CrossPhaseInsight:
    """段階間洞察"""

    phases: list[str]
    insight: str
    impact_score: float
    evidence: list[str] = field(default_factory=list)
    actionable_recommendations: list[str] = field(default_factory=list)

    def affects_multiple_phases(self) -> bool:
        """複数段階影響判定

        Returns:
            bool: 複数段階にまたがるかどうか
        """
        return len(self.phases) >= 2


@dataclass
class ComprehensiveImprovement:
    """包括的改善提案"""

    improvement_type: str
    affected_phases: list[str]
    original_texts: list[str]
    improved_texts: list[str]
    confidence: str
    reasoning: str
    expected_impact: float
    implementation_priority: int = 1
    technical_enhancement: str | None = None

    def is_high_impact(self) -> bool:
        """高影響判定

        Returns:
            bool: 高影響（7.0以上）かどうか
        """
        return self.expected_impact >= 7.0

    def is_cross_phase(self) -> bool:
        """段階横断判定

        Returns:
            bool: 複数段階にまたがるかどうか
        """
        return len(self.affected_phases) >= 2


@dataclass
class ContextMetrics:
    """コンテキスト保持メトリクス"""

    preservation_rate: float
    cross_reference_count: int
    context_depth: int
    relationship_coverage: float = 0.0
    information_density: float = 0.0

    def is_high_preservation(self) -> bool:
        """高保持率判定

        Returns:
            bool: 高保持率（95%以上）かどうか
        """
        return self.preservation_rate >= 95.0


@dataclass
class HolisticAnalysisResult:
    """統合分析結果エンティティ

    統合コンテキスト分析による包括的品質評価結果。
    直接Claude分析レベルの詳細度と情報量を提供。
    """

    project_name: str
    episode_number: int
    overall_score: HolisticScore
    phase_analyses: dict[str, PhaseAnalysis]
    cross_phase_insights: list[CrossPhaseInsight]
    comprehensive_improvements: list[ComprehensiveImprovement]
    context_preservation_metrics: ContextMetrics
    execution_time: timedelta

    # 統計情報
    total_items_analyzed: int = 0
    high_confidence_improvements: int = 0
    critical_issues_count: int = 0

    # メタデータ
    analysis_timestamp: str | None = None
    analysis_version: str = "1.0"

    def get_quality_summary(self) -> dict[str, Any]:
        """品質サマリーの生成

        Returns:
            dict: 品質サマリー情報
        """
        return {
            "overall_score": self.overall_score.value,
            "grade": self.overall_score.get_grade(),
            "grade_description": self.overall_score.get_grade_description(),
            "total_phases_analyzed": len(self.phase_analyses),
            "cross_phase_insights_count": len(self.cross_phase_insights),
            "comprehensive_improvements_count": len(self.comprehensive_improvements),
            "context_preservation_rate": self.context_preservation_metrics.preservation_rate,
            "execution_time_seconds": self.execution_time.total_seconds(),
            "high_quality_achieved": self.overall_score.is_high_quality(),
        }

    def get_improvement_statistics(self) -> dict[str, Any]:
        """改善統計の生成

        Returns:
            dict: 改善提案統計
        """
        total_improvements = len(self.comprehensive_improvements)
        high_impact_count = sum(1 for imp in self.comprehensive_improvements if imp.is_high_impact())
        cross_phase_count = sum(1 for imp in self.comprehensive_improvements if imp.is_cross_phase())

        confidence_distribution = {}
        for improvement in self.comprehensive_improvements:
            conf = improvement.confidence
            confidence_distribution[conf] = confidence_distribution.get(conf, 0) + 1

        return {
            "total_improvements": total_improvements,
            "high_impact_improvements": high_impact_count,
            "cross_phase_improvements": cross_phase_count,
            "confidence_distribution": confidence_distribution,
            "average_expected_impact": self._calculate_average_impact(),
            "improvement_coverage": self._calculate_improvement_coverage(),
        }

    def get_phase_performance(self) -> dict[str, dict[str, Any]]:
        """段階別パフォーマンス取得

        Returns:
            dict: 段階別詳細パフォーマンス
        """
        performance = {}

        for phase_name, analysis in self.phase_analyses.items():
            performance[phase_name] = {
                "score": analysis.score,
                "pass_rate": analysis.get_pass_rate(),
                "insights_count": analysis.insights_count,
                "critical_issues": len(analysis.critical_issues),
                "improvements_count": len(analysis.improvements),
                "grade": self._score_to_grade(analysis.score),
            }

        return performance

    def get_cross_phase_effectiveness(self) -> dict[str, Any]:
        """段階間効果性の評価

        Returns:
            dict: 段階間分析効果性
        """
        multi_phase_insights = [insight for insight in self.cross_phase_insights if insight.affects_multiple_phases()]

        return {
            "cross_phase_insights_count": len(self.cross_phase_insights),
            "multi_phase_insights_count": len(multi_phase_insights),
            "average_impact_score": self._calculate_average_insight_impact(),
            "phase_coverage": self._calculate_phase_coverage(),
            "integration_effectiveness": self._calculate_integration_effectiveness(),
        }

    def is_production_ready(self) -> bool:
        """製品品質判定

        Returns:
            bool: 製品レベル品質かどうか
        """
        return (
            self.overall_score.value >= 90.0
            and self.context_preservation_metrics.is_high_preservation()
            and self.critical_issues_count == 0
            and len(self.comprehensive_improvements) >= 5
        )

    def _calculate_average_impact(self) -> float:
        """平均期待影響度の計算"""
        if not self.comprehensive_improvements:
            return 0.0

        total_impact = sum(imp.expected_impact for imp in self.comprehensive_improvements)
        return total_impact / len(self.comprehensive_improvements)

    def _calculate_improvement_coverage(self) -> float:
        """改善カバレッジの計算"""
        if not self.phase_analyses:
            return 0.0

        phases_with_improvements = set()
        for improvement in self.comprehensive_improvements:
            phases_with_improvements.update(improvement.affected_phases)

        return len(phases_with_improvements) / len(self.phase_analyses)

    def _calculate_average_insight_impact(self) -> float:
        """平均洞察影響度の計算"""
        if not self.cross_phase_insights:
            return 0.0

        total_impact = sum(insight.impact_score for insight in self.cross_phase_insights)
        return total_impact / len(self.cross_phase_insights)

    def _calculate_phase_coverage(self) -> float:
        """段階カバレッジの計算"""
        if not self.phase_analyses:
            return 0.0

        phases_with_insights = set()
        for insight in self.cross_phase_insights:
            phases_with_insights.update(insight.phases)

        return len(phases_with_insights) / len(self.phase_analyses)

    def _calculate_integration_effectiveness(self) -> float:
        """統合効果性の計算"""
        context_score = self.context_preservation_metrics.preservation_rate / 100.0
        insight_score = min(len(self.cross_phase_insights) / 10.0, 1.0)  # 10個で満点
        improvement_score = min(len(self.comprehensive_improvements) / 20.0, 1.0)  # 20個で満点

        return (context_score + insight_score + improvement_score) / 3.0

    def _score_to_grade(self, score: float) -> str:
        """スコアをグレードに変換"""
        return HolisticScore(score).get_grade()
