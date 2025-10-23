#!/usr/bin/env python3

"""Application.use_cases.quality_check_functional_core
Where: Application module exposing the functional core of quality checking steps.
What: Provides reusable routines to score, filter, and aggregate quality metrics.
Why: Keeps quality-check logic centralised for use by multiple application workflows.
"""

from __future__ import annotations


from dataclasses import dataclass
from typing import Any

from noveler.domain.entities.quality_check_aggregate import QualityRule, QualityViolation


@dataclass(frozen=True)
class QualityCheckInput:
    """Immutable input data for quality checks."""
    episode_id: str
    project_id: str
    episode_content: str
    quality_rules: list[QualityRule]
    check_options: dict[str, Any]
    quality_threshold: float


@dataclass(frozen=True)
class QualityCheckOutput:
    """Immutable output data returned by quality checks."""
    violations: list[QualityViolation]
    overall_score: float
    rule_scores: dict[str, float]
    check_summary: dict[str, Any]
    auto_fix_suggestions: list[str]


class QualityCheckCore:
    """Functional core responsible for evaluating quality rules."""

    @staticmethod
    def execute_quality_check(input_data: QualityCheckInput) -> QualityCheckOutput:
        """Evaluate quality rules using pure functions.

        Args:
            input_data: Immutable quality check input payload.

        Returns:
            QualityCheckOutput: Results including scores, violations, and summary data.
        """
        violations = []
        rule_scores = {}
        auto_fix_suggestions = []

        # 各ルールに対して品質チェック実行
        for rule in input_data.quality_rules:
            rule_result = QualityCheckCore._check_rule(
                rule, input_data.episode_content, input_data.check_options
            )

            violations.extend(rule_result["violations"])
            rule_scores[rule.rule_id] = rule_result["score"]
            auto_fix_suggestions.extend(rule_result["suggestions"])

        # 総合スコア計算
        overall_score = QualityCheckCore._calculate_overall_score(rule_scores)

        # チェックサマリー作成
        check_summary = QualityCheckCore._create_check_summary(
            input_data, violations, overall_score
        )

        return QualityCheckOutput(
            violations=violations,
            overall_score=overall_score,
            rule_scores=rule_scores,
            check_summary=check_summary,
            auto_fix_suggestions=auto_fix_suggestions
        )

    @staticmethod
    def _check_rule(
        rule: QualityRule,
        content: str,
        options: dict[str, Any]
    ) -> dict[str, Any]:
        """Evaluate a single quality rule using pure functions."""
        violations = []
        suggestions = []
        score = 1.0  # デフォルトスコア

        # ルール種別に応じた処理
        if rule.rule_id == "length_check":
            result = QualityCheckCore._check_length(content, rule.threshold)
            violations.extend(result["violations"])
            suggestions.extend(result["suggestions"])
            score = result["score"]

        elif rule.rule_id == "sentence_structure":
            result = QualityCheckCore._check_sentence_structure(content)
            violations.extend(result["violations"])
            suggestions.extend(result["suggestions"])
            score = result["score"]

        elif rule.rule_id == "character_consistency":
            result = QualityCheckCore._check_character_consistency(content)
            violations.extend(result["violations"])
            suggestions.extend(result["suggestions"])
            score = result["score"]

        return {
            "violations": violations,
            "score": score,
            "suggestions": suggestions
        }

    @staticmethod
    def _check_length(content: str, threshold: float) -> dict[str, Any]:
        """Perform length-based quality checks."""
        violations = []
        suggestions = []

        char_count = len(content.strip())
        target_length = int(threshold)

        score = min(1.0, char_count / target_length) if target_length > 0 else 1.0

        if char_count < target_length * 0.8:
            violations.append(QualityViolation(
                rule_id="length_check",
                severity="warning",
                message=f"文字数不足: {char_count}/{target_length}",
                location=None
            ))
            suggestions.append(f"目標文字数{target_length}まで内容を拡充してください")

        return {
            "violations": violations,
            "score": score,
            "suggestions": suggestions
        }

    @staticmethod
    def _check_sentence_structure(content: str) -> dict[str, Any]:
        """Assess sentence structure heuristics."""
        violations = []
        suggestions = []
        score = 1.0

        lines = content.split("\n")

        # 空行が多すぎる場合
        empty_line_ratio = sum(1 for line in lines if not line.strip()) / len(lines)
        if empty_line_ratio > 0.3:
            violations.append(QualityViolation(
                rule_id="sentence_structure",
                severity="info",
                message="空行が多すぎます",
                location=None
            ))
            suggestions.append("不要な空行を削除してください")
            score = 0.8

        return {
            "violations": violations,
            "score": score,
            "suggestions": suggestions
        }

    @staticmethod
    def _check_character_consistency(content: str) -> dict[str, Any]:
        """Perform simple character consistency checks."""
        violations = []
        suggestions = []
        score = 1.0

        # 簡単な一貫性チェック（実際の実装では詳細な分析が必要）
        if "「" in content and "」" not in content:
            violations.append(QualityViolation(
                rule_id="character_consistency",
                severity="error",
                message="開始鍵括弧に対応する終了鍵括弧がありません",
                location=None
            ))
            suggestions.append("鍵括弧の対応を確認してください")
            score = 0.5

        return {
            "violations": violations,
            "score": score,
            "suggestions": suggestions
        }

    @staticmethod
    def _calculate_overall_score(rule_scores: dict[str, float]) -> float:
        """総合スコア計算（純粋関数）

        Args:
            rule_scores: ルール別スコア

        Returns:
            総合スコア
        """
        if not rule_scores:
            return 0.0

        return sum(rule_scores.values()) / len(rule_scores)

    @staticmethod
    def _create_check_summary(
        input_data: QualityCheckInput,
        violations: list[QualityViolation],
        overall_score: float
    ) -> dict[str, Any]:
        """チェックサマリー作成（純粋関数）

        Args:
            input_data: 入力データ
            violations: 検出された違反
            overall_score: 総合スコア

        Returns:
            チェックサマリー
        """
        return {
            "total_violations": len(violations),
            "error_count": sum(1 for v in violations if v.severity == "error"),
            "warning_count": sum(1 for v in violations if v.severity == "warning"),
            "info_count": sum(1 for v in violations if v.severity == "info"),
            "overall_score": overall_score,
            "passed_threshold": overall_score >= input_data.quality_threshold,
            "content_length": len(input_data.episode_content),
            "rules_applied": len(input_data.quality_rules)
        }
