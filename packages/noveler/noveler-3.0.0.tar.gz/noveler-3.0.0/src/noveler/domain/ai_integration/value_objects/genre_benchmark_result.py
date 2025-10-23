#!/usr/bin/env python3

"""Domain.ai_integration.value_objects.genre_benchmark_result
Where: Domain value object summarising genre benchmark comparisons.
What: Holds per-genre scoring details and benchmark interpretations.
Why: Supports reporting on how closely works align with target genres.
"""

from __future__ import annotations

"""ジャンル比較結果値オブジェクト

書籍化作品との比較分析結果を表現
"""


from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.ai_integration.value_objects.genre_configuration import GenreConfiguration


class ComparisonStatus(Enum):
    """比較ステータス"""

    EXCELLENT = "✅"  # 優秀
    GOOD = "🟢"  # 良好
    WARNING = "⚠️"  # 警告
    CRITICAL = "❌"  # 致命的


@dataclass(frozen=True)
class StructuralComparison:
    """構造的比較"""

    aspect: str  # 比較要素
    user_value: str  # ユーザー作品の値
    benchmark_value: str  # ベンチマーク値
    conformity_rate: float  # 適合率(0.0-1.0)
    status: ComparisonStatus

    def __post_init__(self) -> None:
        """比較の妥当性検証"""
        if not self.aspect:
            msg = "比較要素は必須です"
            raise ValueError(msg)

        if not 0.0 <= self.conformity_rate <= 1.0:
            msg = f"適合率は0.0以上1.0以下である必要があります: {self.conformity_rate}"
            raise ValueError(msg)

    def is_problematic(self) -> bool:
        """問題があるか"""
        return self.status in [ComparisonStatus.WARNING, ComparisonStatus.CRITICAL]

    def get_severity_score(self) -> int:
        """重要度スコア(高いほど重要)"""
        severity_map = {
            ComparisonStatus.CRITICAL: 4,
            ComparisonStatus.WARNING: 3,
            ComparisonStatus.GOOD: 2,
            ComparisonStatus.EXCELLENT: 1,
        }
        return severity_map[self.status]


@dataclass(frozen=True)
class ImprovementSuggestion:
    """改善提案"""

    priority: str  # 優先度
    description: str  # 説明
    reference_work: str | None  # 参考作品
    expected_impact: str  # 期待される効果

    def __post_init__(self) -> None:
        """提案の妥当性検証"""
        if not self.description:
            msg = "説明は必須です"
            raise ValueError(msg)

        valid_priorities = ["高", "中", "低"]
        if self.priority not in valid_priorities:
            msg = f"優先度は{valid_priorities}のいずれかである必要があります: {self.priority}"
            raise ValueError(msg)

    def is_high_priority(self) -> bool:
        """高優先度か"""
        return self.priority == "高"


@dataclass(frozen=True)
class PublicationReadiness:
    """書籍化準備度"""

    readiness_score: float  # 準備度スコア(0.0-1.0)
    success_probability: float  # 成功確率(0.0-1.0)
    critical_gaps: list[str]  # 致命的なギャップ
    competitive_advantages: list[str]  # 競合優位性

    def __post_init__(self) -> None:
        """準備度の妥当性検証"""
        if not 0.0 <= self.readiness_score <= 1.0:
            msg = f"準備度スコアは0.0以上1.0以下である必要があります: {self.readiness_score}"
            raise ValueError(msg)

        if not 0.0 <= self.success_probability <= 1.0:
            msg = f"成功確率は0.0以上1.0以下である必要があります: {self.success_probability}"
            raise ValueError(msg)

        # リストをタプルに変換して不変性を保証
        object.__setattr__(self, "critical_gaps", tuple(self.critical_gaps))
        object.__setattr__(self, "competitive_advantages", tuple(self.competitive_advantages))

    def get_readiness_grade(self) -> str:
        """準備度グレード"""
        if self.readiness_score >= 0.8:
            return "A"
        if self.readiness_score >= 0.6:
            return "B"
        if self.readiness_score >= 0.4:
            return "C"
        return "D"

    def is_publication_ready(self) -> bool:
        """書籍化準備完了か"""
        return self.readiness_score >= 0.7 and len(self.critical_gaps) == 0

    def get_next_milestone(self) -> str | None:
        """次のマイルストーン"""
        if self.critical_gaps:
            return f"致命的ギャップの解消: {self.critical_gaps[0]}"
        if self.readiness_score < 0.8:
            return "準備度80%達成に向けた改善"
        return None


@dataclass(frozen=True)
class GenreBenchmarkResult:
    """ジャンル比較結果

    書籍化作品との比較分析結果の全体
    """

    genre_config: GenreConfiguration
    comparison_target_count: int  # 比較対象作品数
    structural_comparisons: list[StructuralComparison]
    improvement_suggestions: list[ImprovementSuggestion]
    publication_readiness: PublicationReadiness
    reference_works: list[str]  # 参考作品リスト

    def __post_init__(self) -> None:
        """結果の妥当性検証"""
        if self.comparison_target_count < 1:
            msg = f"比較対象作品数は1以上である必要があります: {self.comparison_target_count}"
            raise ValueError(msg)

        if not self.structural_comparisons:
            msg = "構造的比較は1つ以上必要です"
            raise ValueError(msg)

        # リストをタプルに変換して不変性を保証
        object.__setattr__(self, "structural_comparisons", tuple(self.structural_comparisons))
        object.__setattr__(self, "improvement_suggestions", tuple(self.improvement_suggestions))
        object.__setattr__(self, "reference_works", tuple(self.reference_works))

    def get_critical_issues(self) -> list[StructuralComparison]:
        """致命的な問題を取得"""
        return [comp for comp in self.structural_comparisons if comp.status == ComparisonStatus.CRITICAL]

    def get_warning_issues(self) -> list[StructuralComparison]:
        """警告レベルの問題を取得"""
        return [comp for comp in self.structural_comparisons if comp.status == ComparisonStatus.WARNING]

    def get_high_priority_suggestions(self) -> list[ImprovementSuggestion]:
        """高優先度の改善提案を取得"""
        return [suggestion for suggestion in self.improvement_suggestions if suggestion.is_high_priority()]

    def get_overall_conformity(self) -> float:
        """全体適合率"""
        if not self.structural_comparisons:
            return 0.0

        total_conformity = sum(comp.conformity_rate for comp in self.structural_comparisons)
        return total_conformity / len(self.structural_comparisons)

    def get_market_position(self) -> str:
        """市場ポジション"""
        conformity = self.get_overall_conformity()
        critical_count = len(self.get_critical_issues())

        if conformity >= 0.8 and critical_count == 0:
            return "市場適合度が高く、書籍化の可能性が高い"
        if conformity >= 0.6 and critical_count <= 1:
            return "市場適合度は良好だが、改善の余地がある"
        if conformity >= 0.4:
            return "市場適合度は標準的、重要な改善が必要"
        return "市場適合度が低く、大幅な見直しが必要"

    def get_summary_report(self) -> str:
        """サマリーレポート"""
        lines = [
            f"🎯 ジャンル: {self.genre_config.get_genre_combination()}",
            f"📊 比較対象: {self.comparison_target_count}作品",
            f"📈 全体適合率: {self.get_overall_conformity():.1%}",
            f"🎓 書籍化準備度: {self.publication_readiness.get_readiness_grade()}級",
            f"💡 市場ポジション: {self.get_market_position()}",
        ]

        critical_issues = self.get_critical_issues()
        if critical_issues:
            lines.append(f"⚠️ 致命的問題: {len(critical_issues)}件")

        high_priority = self.get_high_priority_suggestions()
        if high_priority:
            lines.append(f"🚨 高優先度改善: {len(high_priority)}項目")

        return "\n".join(lines)
