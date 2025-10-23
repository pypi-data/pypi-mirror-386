#!/usr/bin/env python3

"""Domain.ai_integration.value_objects.analysis_result
Where: Domain value object representing results from AI integration analyses.
What: Stores metric scores, observations, and metadata produced by analysis services.
Why: Enables downstream consumers to access structured analysis outcomes.
"""

from __future__ import annotations

"""分析結果値オブジェクト

プロット分析の結果を表現する
"""


from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from noveler.domain.ai_integration.value_objects.plot_score import PlotScore


@dataclass(frozen=True)
class StrengthPoint:
    """強みポイント"""

    description: str
    score: int  # 個別スコア(0-100)

    def __post_init__(self) -> None:
        max_score = 100
        if not 0 <= self.score <= max_score:
            msg = f"スコアは0以上100以下でなければなりません: {self.score}"
            raise ValueError(msg)


@dataclass(frozen=True)
class ImprovementPoint:
    """改善ポイント"""

    description: str
    score: int  # 個別スコア(0-100)
    suggestion: str  # 改善提案

    def __post_init__(self) -> None:
        max_score = 100
        if not 0 <= self.score <= max_score:
            msg = f"スコアは0以上100以下でなければなりません: {self.score}"
            raise ValueError(msg)

    def is_critical(self) -> bool:
        """致命的な問題かどうか(40点未満)"""
        critical_threshold = 40
        return self.score < critical_threshold

    @property
    def priority(self) -> Literal["high", "medium", "low"]:
        """改善の優先度"""
        high_priority_threshold = 40
        medium_priority_threshold = 70
        if self.score < high_priority_threshold:
            return "high"
        if self.score < medium_priority_threshold:
            return "medium"
        return "low"


@dataclass(frozen=True)
class AnalysisResult:
    """プロット分析結果

    総合スコア、強み、改善点、総合アドバイスを含む
    """

    total_score: PlotScore
    strengths: list[StrengthPoint]
    improvements: list[ImprovementPoint]
    overall_advice: str

    def __post_init__(self) -> None:
        """リストをタプルに変換して不変性を保証"""
        object.__setattr__(self, "strengths", tuple(self.strengths))
        object.__setattr__(self, "improvements", tuple(self.improvements))

    def has_high_quality_structure(self) -> bool:
        """高品質な構造を持つかどうか"""
        high_quality_threshold = 70
        return self.total_score.value >= high_quality_threshold

    def get_critical_improvements(self) -> list[ImprovementPoint]:
        """致命的な改善点を取得"""
        return [imp for imp in self.improvements if imp.is_critical()]

    def get_summary(self) -> str:
        """結果のサマリーを生成"""
        summary_lines = [
            f"総合評価: {self.total_score.value}/100点",
            f"強み: {len(self.strengths)}項目",
            f"改善点: {len(self.improvements)}項目",
        ]

        critical_count = len(self.get_critical_improvements())
        if critical_count > 0:
            summary_lines.append(f"致命的な問題: {critical_count}件")

        return "\n".join(summary_lines)
