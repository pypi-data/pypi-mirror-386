#!/usr/bin/env python3
"""CategoryAnalysisResult エンティティ単体テスト

TDD Red フェーズ: カテゴリ別分析結果エンティティの失敗テスト
"""

from datetime import datetime, timezone

import pytest

from noveler.domain.entities.category_analysis_result import AnalysisResultId, CategoryAnalysisResult
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory
from noveler.domain.value_objects.improvement_suggestion import ImprovementSuggestion


@pytest.mark.spec("SPEC-A31-DET-001")
class TestCategoryAnalysisResult:
    """CategoryAnalysisResult エンティティテスト"""

    @pytest.mark.spec("SPEC-CATEGORY_ANALYSIS_RESULT-CREATE_CATEGORY_ANAL")
    def test_create_category_analysis_with_valid_parameters(self) -> None:
        """有効なパラメータでカテゴリ分析結果を作成できる"""
        # Given
        category = A31EvaluationCategory.FORMAT_CHECK
        score = 85.0
        issues = ["問題1", "問題2"]
        suggestions = ["提案1", "提案2"]

        # When
        result = CategoryAnalysisResult.create(
            category=category, score=score, issues_found=issues, suggestions=suggestions
        )

        # Then
        assert result.category == category
        assert result.score == score
        assert result.issues_found == issues
        assert result.suggestions == suggestions
        assert isinstance(result.result_id, AnalysisResultId)
        assert result.analyzed_at <= datetime.now(timezone.utc)

    @pytest.mark.spec("SPEC-CATEGORY_ANALYSIS_RESULT-RESULT_ID_IS_UNIQUE_")
    def test_result_id_is_unique_for_each_analysis(self) -> None:
        """各分析結果のIDが一意である"""
        # Given
        category = A31EvaluationCategory.CONTENT_BALANCE

        # When
        result1 = CategoryAnalysisResult.create(
            category=category, score=80.0, issues_found=["問題A"], suggestions=["提案A"]
        )

        result2 = CategoryAnalysisResult.create(
            category=category, score=85.0, issues_found=["問題B"], suggestions=["提案B"]
        )

        # Then
        assert result1.result_id != result2.result_id

    @pytest.mark.spec("SPEC-CATEGORY_ANALYSIS_RESULT-SCORE_MUST_BE_WITHIN")
    def test_score_must_be_within_valid_range(self) -> None:
        """スコアは有効範囲（0-100）内である必要がある"""
        # When & Then - 負のスコア
        with pytest.raises(ValueError, match="スコアは0.0から100.0の範囲である必要があります"):
            CategoryAnalysisResult.create(
                category=A31EvaluationCategory.FORMAT_CHECK, score=-1.0, issues_found=[], suggestions=[]
            )

        # When & Then - 100を超えるスコア
        with pytest.raises(ValueError, match="スコアは0.0から100.0の範囲である必要があります"):
            CategoryAnalysisResult.create(
                category=A31EvaluationCategory.FORMAT_CHECK, score=101.0, issues_found=[], suggestions=[]
            )

    @pytest.mark.spec("SPEC-CATEGORY_ANALYSIS_RESULT-ADD_DETAILED_SUGGEST")
    def test_add_detailed_suggestion_with_improvement_object(self) -> None:
        """詳細な改善提案オブジェクトを追加できる"""
        # Given
        result = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.STYLE_CONSISTENCY, score=75.0, issues_found=["文末単調"], suggestions=[]
        )

        suggestion = ImprovementSuggestion.create(
            content="文末バリエーションを増やす",
            suggestion_type="style",
            confidence=0.9,
            fix_example="だった。→である。～した。",
            expected_impact="読みやすさ向上",
        )

        # When
        result.add_detailed_suggestion(suggestion)

        # Then
        assert len(result.detailed_suggestions) == 1
        assert result.detailed_suggestions[0] == suggestion

    @pytest.mark.spec("SPEC-CATEGORY_ANALYSIS_RESULT-CALCULATE_CONFIDENCE")
    def test_calculate_confidence_score_based_on_factors(self) -> None:
        """各種要因に基づいて信頼度スコアを計算"""
        # Given
        result = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.READABILITY_CHECK,
            score=88.0,
            issues_found=["問題1", "問題2"],  # 2件の問題
            suggestions=["提案1", "提案2", "提案3"],  # 3件の提案
        )

        # 詳細提案を追加（高信頼度）
        high_confidence_suggestion = ImprovementSuggestion.create(
            content="具体的改善案", suggestion_type="enhancement", confidence=0.95
        )

        result.add_detailed_suggestion(high_confidence_suggestion)

        # When
        confidence = result.calculate_confidence_score()

        # Then
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.8  # 高品質な分析結果のため高信頼度

    @pytest.mark.spec("SPEC-CATEGORY_ANALYSIS_RESULT-IS_PASSING_GRADE_EVA")
    def test_is_passing_grade_evaluation(self) -> None:
        """合格基準の評価を正しく判定"""
        # Given - 合格スコア
        passing_result = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.CHARACTER_CONSISTENCY, score=85.0, issues_found=[], suggestions=[]
        )

        # Given - 不合格スコア
        failing_result = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.CHARACTER_CONSISTENCY,
            score=65.0,
            issues_found=["一貫性問題"],
            suggestions=["修正提案"],
        )

        # When & Then
        assert passing_result.is_passing_grade(threshold=80.0) is True
        assert failing_result.is_passing_grade(threshold=80.0) is False

    @pytest.mark.spec("SPEC-CATEGORY_ANALYSIS_RESULT-GET_PRIORITY_ISSUES_")
    def test_get_priority_issues_returns_critical_first(self) -> None:
        """優先度順に問題を取得（重要度高いものが先）"""
        # Given
        result = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.QUALITY_THRESHOLD,
            score=70.0,
            issues_found=["軽微問題", "重要問題", "致命的問題"],
            suggestions=[],
        )

        # 問題の重要度を設定（実際の実装では問題オブジェクトで管理）
        result._set_issue_priorities({"致命的問題": "critical", "重要問題": "major", "軽微問題": "minor"})

        # When
        priority_issues = result.get_priority_issues()

        # Then
        assert priority_issues[0] == "致命的問題"
        assert priority_issues[1] == "重要問題"
        assert priority_issues[2] == "軽微問題"

    @pytest.mark.spec("SPEC-CATEGORY_ANALYSIS_RESULT-HAS_ACTIONABLE_SUGGE")
    def test_has_actionable_suggestions_check(self) -> None:
        """実行可能な提案があるかチェック"""
        # Given - 実行可能提案あり
        result_with_suggestions = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.CONTENT_BALANCE,
            score=78.0,
            issues_found=["バランス問題"],
            suggestions=["具体的修正案"],
        )

        # Given - 提案なし
        result_without_suggestions = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.CONTENT_BALANCE, score=95.0, issues_found=[], suggestions=[]
        )

        # When & Then
        assert result_with_suggestions.has_actionable_suggestions() is True
        assert result_without_suggestions.has_actionable_suggestions() is False

    @pytest.mark.spec("SPEC-CATEGORY_ANALYSIS_RESULT-TO_SUMMARY_DICT_CONT")
    def test_to_summary_dict_contains_essential_info(self) -> None:
        """サマリー辞書に必須情報が含まれる"""
        # Given
        result = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.CLAUDE_CODE_EVALUATION,
            score=82.5,
            issues_found=["問題A", "問題B"],
            suggestions=["提案1", "提案2", "提案3"],
        )

        # When
        summary = result.to_summary_dict()

        # Then
        assert summary["category"] == "claude_code_evaluation"
        assert summary["score"] == 82.5
        assert summary["issues_count"] == 2
        assert summary["suggestions_count"] == 3
        assert summary["passing_grade"] is True  # デフォルト閾値80.0で合格
        assert "analyzed_at" in summary

    @pytest.mark.spec("SPEC-CATEGORY_ANALYSIS_RESULT-MERGE_WITH_COMPATIBL")
    def test_merge_with_compatible_analysis_result(self) -> None:
        """互換性のある分析結果とマージできる"""
        # Given
        result1 = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.SYSTEM_FUNCTION, score=80.0, issues_found=["問題1"], suggestions=["提案1"]
        )

        result2 = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.SYSTEM_FUNCTION, score=85.0, issues_found=["問題2"], suggestions=["提案2"]
        )

        # When
        merged_result = result1.merge_with(result2)

        # Then
        assert merged_result.category == A31EvaluationCategory.SYSTEM_FUNCTION
        assert merged_result.score == 82.5  # 平均スコア
        assert len(merged_result.issues_found) == 2
        assert len(merged_result.suggestions) == 2

    @pytest.mark.spec("SPEC-CATEGORY_ANALYSIS_RESULT-CANNOT_MERGE_DIFFERE")
    def test_cannot_merge_different_categories(self) -> None:
        """異なるカテゴリの結果はマージできない"""
        # Given
        result1 = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.FORMAT_CHECK, score=80.0, issues_found=[], suggestions=[]
        )

        result2 = CategoryAnalysisResult.create(
            category=A31EvaluationCategory.CONTENT_BALANCE, score=85.0, issues_found=[], suggestions=[]
        )

        # When & Then
        with pytest.raises(ValueError, match="異なるカテゴリの分析結果はマージできません"):
            result1.merge_with(result2)
