"""Domain.value_objects.execution_result
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""実行結果バリューオブジェクト

DDD準拠: Domainレイヤーのvalue object
実行結果データの不変性と値の等価性を保証
"""


from dataclasses import dataclass

from noveler.domain.value_objects.improvement_suggestion import ImprovementSuggestion
from noveler.domain.value_objects.quality_issue import QualityIssue


@dataclass(frozen=True)
class ExecutionResult:
    """実行結果バリューオブジェクト"""

    success: bool  # 実行成功フラグ
    output_content: str  # 出力内容
    confidence_score: float  # 分析信頼度
    processing_time: float  # 処理時間（秒）
    issues_found: tuple[QualityIssue, ...]  # 発見された問題（不変タプル）
    suggestions: tuple[ImprovementSuggestion, ...]  # 改善提案（不変タプル）
    error_message: str | None = None  # エラーメッセージ

    def __post_init__(self) -> None:
        """後初期化バリデーション"""
        if self.confidence_score < 0.0 or self.confidence_score > 1.0:
            msg = "confidence_score must be between 0.0 and 1.0"
            raise ValueError(msg)

        if self.processing_time < 0.0:
            msg = "processing_time must be non-negative"
            raise ValueError(msg)

    def calculate_effectiveness_score(self) -> float:
        """実行効果性スコア計算

        Returns:
            float: 効果性スコア（0-100）
        """
        if not self.success:
            return 0.0

        effectiveness_factors = []

        # 問題検出数による効果性
        issue_effectiveness = min(100.0, len(self.issues_found) * 15)
        effectiveness_factors.append(issue_effectiveness)

        # 提案品質による効果性
        actionable_suggestions = sum(1 for suggestion in self.suggestions if suggestion.is_actionable())
        suggestion_effectiveness = min(100.0, actionable_suggestions * 20)
        effectiveness_factors.append(suggestion_effectiveness)

        # 信頼度による効果性
        confidence_effectiveness = self.confidence_score * 100
        effectiveness_factors.append(confidence_effectiveness)

        # 処理時間効率性（短いほど良い、最大10秒として正規化）
        time_efficiency = max(0.0, (10.0 - min(self.processing_time, 10.0)) / 10.0 * 100)
        effectiveness_factors.append(time_efficiency)

        # 加重平均計算
        weights = [0.3, 0.3, 0.3, 0.1]  # 問題検出、提案、信頼度、時間効率
        weighted_score = sum(factor * weight for factor, weight in zip(effectiveness_factors, weights, strict=False))

        return min(100.0, weighted_score)

    def get_critical_issues(self) -> tuple[QualityIssue, ...]:
        """クリティカル問題を取得

        Returns:
            tuple[QualityIssue, ...]: クリティカル問題一覧
        """
        return tuple(issue for issue in self.issues_found if issue.severity == "critical")

    def has_critical_issues(self) -> bool:
        """クリティカル問題の有無確認

        Returns:
            bool: クリティカル問題がある場合True
        """
        return len(self.get_critical_issues()) > 0

    def get_summary_metrics(self) -> dict[str, float | int]:
        """サマリーメトリクス取得

        Returns:
            dict[str, float | int]: メトリクス辞書
        """
        return {
            "effectiveness_score": self.calculate_effectiveness_score(),
            "issues_count": len(self.issues_found),
            "critical_issues_count": len(self.get_critical_issues()),
            "suggestions_count": len(self.suggestions),
            "processing_time": self.processing_time,
            "confidence_score": self.confidence_score,
            "success": self.success,
        }

    @classmethod
    def create_success(
        cls,
        output_content: str,
        confidence_score: float,
        processing_time: float,
        issues_found: list[QualityIssue] | None = None,
        suggestions: list[ImprovementSuggestion] | None = None,
    ) -> ExecutionResult:
        """成功結果作成ファクトリ

        Args:
            output_content: 出力内容
            confidence_score: 信頼度
            processing_time: 処理時間
            issues_found: 発見された問題
            suggestions: 改善提案

        Returns:
            ExecutionResult: 成功実行結果
        """
        return cls(
            success=True,
            output_content=output_content,
            confidence_score=confidence_score,
            processing_time=processing_time,
            issues_found=tuple(issues_found or []),
            suggestions=tuple(suggestions or []),
        )

    @classmethod
    def create_failure(cls, error_message: str, processing_time: float = 0.0) -> ExecutionResult:
        """失敗結果作成ファクトリ

        Args:
            error_message: エラーメッセージ
            processing_time: 処理時間

        Returns:
            ExecutionResult: 失敗実行結果
        """
        return cls(
            success=False,
            output_content="",
            confidence_score=0.0,
            processing_time=processing_time,
            issues_found=(),
            suggestions=(),
            error_message=error_message,
        )
