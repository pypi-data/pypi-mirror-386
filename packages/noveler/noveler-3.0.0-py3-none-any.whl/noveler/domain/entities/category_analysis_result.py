#!/usr/bin/env python3
"""カテゴリ分析結果 エンティティ

A31評価カテゴリ別の詳細分析結果を管理するエンティティ。
各カテゴリの問題点、改善提案、信頼度を統合管理する。
"""

import uuid
from datetime import datetime, timezone
from statistics import mean
from typing import Any

from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory
from noveler.domain.value_objects.improvement_suggestion import ImprovementSuggestion


class AnalysisResultId:
    """分析結果識別子バリューオブジェクト"""

    def __init__(self, value: str) -> None:
        """分析結果ID初期化

        Args:
            value: UUID文字列
        """
        if not value or not isinstance(value, str):
            msg = "分析結果IDは空でない文字列である必要があります"
            raise ValueError(msg)
        self._value = value

    @classmethod
    def generate(cls) -> "AnalysisResultId":
        """新しい分析結果IDを生成

        Returns:
            AnalysisResultId: 新しい分析結果ID
        """
        return cls(str(uuid.uuid4()))

    @property
    def value(self) -> str:
        """分析結果ID値を取得

        Returns:
            str: 分析結果ID文字列
        """
        return self._value

    def __eq__(self, other: Any) -> bool:
        """等価性比較"""
        if not isinstance(other, AnalysisResultId):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        """ハッシュ値計算"""
        return hash(self._value)

    def __str__(self) -> str:
        """文字列表現"""
        return self._value


class CategoryAnalysisResult:
    """カテゴリ分析結果 エンティティ

    A31評価の特定カテゴリに対する詳細分析結果を管理。
    問題点、改善提案、信頼度評価を統合したエンティティ。
    """

    def __init__(
        self,
        result_id: AnalysisResultId,
        category: A31EvaluationCategory,
        score: float,
        issues_found: list[str],
        suggestions: list[str],
        analyzed_at: datetime,
        detailed_suggestions: list[ImprovementSuggestion] | None = None,
        confidence_score: float | None = None,
        issue_priorities: dict[str, str] | None = None,
        evaluated_items: list[str] | None = None,
    ) -> None:
        """カテゴリ分析結果初期化

        Args:
            result_id: 分析結果識別子
            category: 評価カテゴリ
            score: 分析スコア（0.0-100.0）
            issues_found: 発見された問題リスト
            suggestions: 改善提案リスト
            analyzed_at: 分析実行日時
            detailed_suggestions: 詳細改善提案リスト
            confidence_score: 信頼度スコア
            issue_priorities: 問題優先度マップ
        """
        self._result_id = result_id
        self._category = category
        self._score = score
        self._issues_found = issues_found.copy()
        self._suggestions = suggestions.copy()
        self._analyzed_at = analyzed_at
        self._detailed_suggestions = detailed_suggestions or []
        self._confidence_score = confidence_score
        self._issue_priorities = issue_priorities or {}
        self._evaluated_items = evaluated_items or []

    @classmethod
    def create(
        cls,
        category: A31EvaluationCategory,
        score: float,
        issues_found: list[str],
        suggestions: list[str],
        evaluated_items: list[str] | None = None,
    ) -> "CategoryAnalysisResult":
        """新しいカテゴリ分析結果を作成

        Args:
            category: 評価カテゴリ
            score: 分析スコア
            issues_found: 発見された問題リスト
            suggestions: 改善提案リスト

        Returns:
            CategoryAnalysisResult: 新しい分析結果

        Raises:
            ValueError: スコアが有効範囲外の場合
        """
        if not 0.0 <= score <= 100.0:
            msg = "スコアは0.0から100.0の範囲である必要があります"
            raise ValueError(msg)

        return cls(
            result_id=AnalysisResultId.generate(),
            category=category,
            score=score,
            issues_found=issues_found,
            suggestions=suggestions,
            analyzed_at=datetime.now(timezone.utc),
            evaluated_items=evaluated_items,
        )

    def add_detailed_suggestion(self, suggestion: ImprovementSuggestion) -> None:
        """詳細改善提案を追加

        Args:
            suggestion: 改善提案オブジェクト
        """
        self._detailed_suggestions.append(suggestion)

    def calculate_confidence_score(self) -> float:
        """信頼度スコアを計算

        各種要因（詳細提案数、問題特定精度等）に基づいて信頼度を算出。

        Returns:
            float: 信頼度スコア（0.0-1.0）
        """
        factors = []

        # 要因1: 詳細提案の信頼度平均
        if self._detailed_suggestions:
            suggestion_confidences = [s.confidence for s in self._detailed_suggestions]
            factors.append(mean(suggestion_confidences))

        # 要因2: 問題特定の明確性（問題数に基づく）
        if self._issues_found:
            # 問題が多すぎず少なすぎない場合に高信頼度
            issue_count = len(self._issues_found)
            if 1 <= issue_count <= 3:
                factors.append(0.9)
            elif 4 <= issue_count <= 6:
                factors.append(0.7)
            else:
                factors.append(0.5)
        else:
            # 問題なしの場合、スコアが高ければ高信頼度
            factors.append(0.9 if self._score >= 90.0 else 0.6)

        # 要因3: スコア一貫性（極端でない適度なスコア）
        if 70.0 <= self._score <= 95.0:
            factors.append(0.8)
        elif 50.0 <= self._score < 70.0 or 95.0 < self._score <= 100.0:
            factors.append(0.6)
        else:
            factors.append(0.4)

        # 各要因の平均を計算
        self._confidence_score = mean(factors) if factors else 0.5
        return self._confidence_score

    def is_passing_grade(self, threshold: float = 80.0) -> bool:
        """合格基準を満たしているかチェック

        Args:
            threshold: 合格基準スコア

        Returns:
            bool: 合格基準を満たす場合True
        """
        return self._score >= threshold

    def get_priority_issues(self) -> list[str]:
        """優先度順に問題を取得

        Returns:
            list[str]: 優先度順問題リスト（critical → major → minor）
        """
        if not self._issue_priorities:
            return self._issues_found.copy()

        # 優先度別にグループ化
        critical_issues = []
        major_issues = []
        minor_issues = []
        unclassified_issues = []

        for issue in self._issues_found:
            priority = self._issue_priorities.get(issue, "unclassified")
            if priority == "critical":
                critical_issues.append(issue)
            elif priority == "major":
                major_issues.append(issue)
            elif priority == "minor":
                minor_issues.append(issue)
            else:
                unclassified_issues.append(issue)

        # 優先度順に結合
        return critical_issues + major_issues + minor_issues + unclassified_issues

    def set_evaluated_items(self, item_ids: list[str]) -> None:
        """評価対象となったA31項目IDを設定"""

        self._evaluated_items = item_ids.copy()

    @property
    def evaluated_items(self) -> list[str]:
        """評価対象項目ID一覧を取得"""

        return self._evaluated_items.copy()

    def has_actionable_suggestions(self) -> bool:
        """実行可能な提案があるかチェック

        Returns:
            bool: 実行可能な提案がある場合True
        """
        return len(self._suggestions) > 0 or len(self._detailed_suggestions) > 0

    def to_summary_dict(self) -> dict[str, Any]:
        """サマリー辞書を生成

        Returns:
            dict[str, Any]: 分析結果サマリー
        """
        return {
            "result_id": self._result_id.value,
            "category": self._category.value,
            "score": self._score,
            "issues_count": len(self._issues_found),
            "suggestions_count": len(self._suggestions),
            "detailed_suggestions_count": len(self._detailed_suggestions),
            "passing_grade": self.is_passing_grade(),
            "confidence_score": self._confidence_score or self.calculate_confidence_score(),
            "analyzed_at": self._analyzed_at.isoformat(),
        }

    def merge_with(self, other: "CategoryAnalysisResult") -> "CategoryAnalysisResult":
        """他の分析結果とマージ

        同一カテゴリの分析結果を統合する。

        Args:
            other: マージ対象の分析結果

        Returns:
            CategoryAnalysisResult: マージされた分析結果

        Raises:
            ValueError: 異なるカテゴリの場合
        """
        if self._category != other._category:
            msg = "異なるカテゴリの分析結果はマージできません"
            raise ValueError(msg)

        # スコアの平均を計算
        merged_score = (self._score + other._score) / 2

        # 問題と提案をマージ（重複除去）
        merged_issues = list(set(self._issues_found + other._issues_found))
        merged_suggestions = list(set(self._suggestions + other._suggestions))

        # 詳細提案をマージ
        merged_detailed_suggestions = self._detailed_suggestions + other._detailed_suggestions

        # 問題優先度をマージ
        merged_priorities = {**self._issue_priorities, **other._issue_priorities}

        return CategoryAnalysisResult(
            result_id=AnalysisResultId.generate(),
            category=self._category,
            score=merged_score,
            issues_found=merged_issues,
            suggestions=merged_suggestions,
            analyzed_at=datetime.now(timezone.utc),
            detailed_suggestions=merged_detailed_suggestions,
            issue_priorities=merged_priorities,
        )

    def _set_issue_priorities(self, priorities: dict[str, str]) -> None:
        """問題優先度を設定（テスト用メソッド）

        Args:
            priorities: 問題優先度マップ
        """
        self._issue_priorities = priorities.copy()

    # プロパティ
    @property
    def result_id(self) -> AnalysisResultId:
        """分析結果ID"""
        return self._result_id

    @property
    def category(self) -> A31EvaluationCategory:
        """評価カテゴリ"""
        return self._category

    @property
    def score(self) -> float:
        """分析スコア"""
        return self._score

    @property
    def issues_found(self) -> list[str]:
        """発見された問題リスト"""
        return self._issues_found.copy()

    @property
    def suggestions(self) -> list[str]:
        """改善提案リスト"""
        return self._suggestions.copy()

    @property
    def analyzed_at(self) -> datetime:
        """分析実行日時"""
        return self._analyzed_at

    @property
    def detailed_suggestions(self) -> list[ImprovementSuggestion]:
        """詳細改善提案リスト"""
        return self._detailed_suggestions.copy()

    @property
    def confidence_score(self) -> float | None:
        """信頼度スコア"""
        return self._confidence_score

    def __eq__(self, other: Any) -> bool:
        """等価性比較"""
        if not isinstance(other, CategoryAnalysisResult):
            return False
        return self._result_id == other._result_id

    def __hash__(self) -> int:
        """ハッシュ値計算"""
        return hash(self._result_id)

    def __str__(self) -> str:
        """文字列表現"""
        return f"CategoryAnalysisResult({self._category.value}, score={self._score:.1f})"

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return (
            f"CategoryAnalysisResult("
            f"category={self._category.value}, "
            f"score={self._score:.1f}, "
            f"issues={len(self._issues_found)}, "
            f"suggestions={len(self._suggestions)})"
        )
