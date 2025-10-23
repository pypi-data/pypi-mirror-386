#!/usr/bin/env python3
"""品質記録拡張エンティティのユニットテスト

TDD原則に従い、仕様書に基づいたテストケースを実装
"""

import time
from datetime import datetime

import pytest

from noveler.domain.entities.quality_record_enhancement import QualityRecordEnhancement
from noveler.domain.exceptions import BusinessRuleViolationError
from noveler.domain.value_objects.learning_metrics import LearningMetrics


class TestQualityRecordEnhancement:
    """QualityRecordEnhancementエンティティのテスト"""

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_initial_state(self) -> None:
        """初期状態の確認"""
        # When
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # Then
        assert record.project_name == "テストプロジェクト"
        assert record.version == "1.0"
        assert isinstance(record.last_updated, datetime)
        assert record.entry_count == 0
        assert record.quality_checks == []

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_project_name_validation_empty(self) -> None:
        """プロジェクト名の検証(空文字列)"""
        # When & Then
        with pytest.raises(BusinessRuleViolationError) as exc:
            QualityRecordEnhancement(project_name="")
        assert "プロジェクト名は必須です" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_project_name_validation_whitespace(self) -> None:
        """プロジェクト名の検証(空白のみ)"""
        # When & Then
        with pytest.raises(BusinessRuleViolationError) as exc:
            QualityRecordEnhancement(project_name="   ")
        assert "プロジェクト名は必須です" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_version_validation_empty(self) -> None:
        """バージョンの検証(空文字列)"""
        # When & Then
        with pytest.raises(BusinessRuleViolationError) as exc:
            QualityRecordEnhancement(project_name="テスト", version="")
        assert "バージョンは必須です" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_add_quality_check_result_valid(self) -> None:
        """品質チェック結果の追加(正常)"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")
        learning_metrics = LearningMetrics(
            improvement_from_previous=5.2,
            time_spent_writing=30,
            revision_count=2,
            user_feedback="良い改善が見られました",
            writing_context="ch01の冒頭部分",
        )

        category_scores = {"basic_writing_style": 85.0, "story_structure": 78.5, "readability": 90.0}
        errors = ["誤字: 「です」が重複しています"]
        warnings = ["文が長すぎます(50文字以上)"]
        auto_fixes = ["誤字の修正を適用しました"]

        # When
        record.add_quality_check_result(
            episode_number=1,
            category_scores=category_scores,
            errors=errors,
            warnings=warnings,
            auto_fixes=auto_fixes,
            learning_metrics=learning_metrics,
            writing_environment="VS Code",
            target_audience="ライトノベル読者",
            writing_goal="読みやすさ重視",
        )

        # Then
        assert record.entry_count == 1
        assert len(record.quality_checks) == 1

        check = record.quality_checks[0]
        assert check["episode_number"] == 1
        assert check["results"]["category_scores"] == category_scores
        assert check["results"]["errors"] == errors
        assert check["results"]["warnings"] == warnings
        assert check["results"]["auto_fixes"] == auto_fixes
        assert check["learning_metrics"]["improvement_from_previous"] == 5.2
        assert check["learning_metrics"]["time_spent_writing"] == 30
        assert check["learning_metrics"]["revision_count"] == 2
        assert check["learning_metrics"]["user_feedback"] == "良い改善が見られました"
        assert check["learning_metrics"]["writing_context"] == "ch01の冒頭部分"
        assert check["context"]["writing_environment"] == "VS Code"
        assert check["context"]["target_audience"] == "ライトノベル読者"
        assert check["context"]["writing_goal"] == "読みやすさ重視"

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_add_quality_check_result_invalid_episode_number(self) -> None:
        """品質チェック結果の追加(無効なエピソード番号)"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")
        learning_metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=10, revision_count=0)

        # When & Then
        with pytest.raises(BusinessRuleViolationError) as exc:
            record.add_quality_check_result(
                episode_number=0,
                category_scores={},
                errors=[],
                warnings=[],
                auto_fixes=[],
                learning_metrics=learning_metrics,
            )

        assert "エピソード番号は1以上の正の整数である必要があります" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_get_improvement_trend_single_category(self) -> None:
        """改善トレンド取得(単一カテゴリ)"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # 複数のチェック結果を追加
        for i in range(3):
            learning_metrics = LearningMetrics(
                improvement_from_previous=i * 2.5, time_spent_writing=30, revision_count=1
            )

            record.add_quality_check_result(
                episode_number=i + 1,
                category_scores={"basic_writing_style": 80.0 + i * 5},
                errors=[],
                warnings=[],
                auto_fixes=[],
                learning_metrics=learning_metrics,
            )

        # When
        trend = record.get_improvement_trend("basic_writing_style")

        # Then
        assert len(trend) == 3
        assert trend[0]["episode_number"] == 1
        assert trend[0]["score"] == 80.0
        assert trend[0]["improvement"] == 0.0
        assert trend[1]["episode_number"] == 2
        assert trend[1]["score"] == 85.0
        assert trend[1]["improvement"] == 2.5
        assert trend[2]["episode_number"] == 3
        assert trend[2]["score"] == 90.0
        assert trend[2]["improvement"] == 5.0

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_get_improvement_trend_nonexistent_category(self) -> None:
        """改善トレンド取得(存在しないカテゴリ)"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")
        learning_metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=30, revision_count=1)
        record.add_quality_check_result(
            episode_number=1,
            category_scores={"basic_writing_style": 80.0},
            errors=[],
            warnings=[],
            auto_fixes=[],
            learning_metrics=learning_metrics,
        )

        # When
        trend = record.get_improvement_trend("nonexistent_category")

        # Then
        assert trend == []

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_calculate_average_improvement_rate(self) -> None:
        """平均改善率の計算"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # 複数のチェック結果を追加
        improvements = [5.0, 3.0, 7.0, -2.0]
        for i, improvement in enumerate(improvements):
            learning_metrics = LearningMetrics(
                improvement_from_previous=improvement, time_spent_writing=30, revision_count=1
            )

            record.add_quality_check_result(
                episode_number=i + 1,
                category_scores={"score": 80.0},
                errors=[],
                warnings=[],
                auto_fixes=[],
                learning_metrics=learning_metrics,
            )

        # When
        avg_improvement = record.calculate_average_improvement_rate()

        # Then
        assert avg_improvement == 3.25  # (5.0 + 3.0 + 7.0 + (-2.0)) / 4

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_calculate_average_improvement_rate_no_data(self) -> None:
        """平均改善率の計算(データなし)"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # When
        avg_improvement = record.calculate_average_improvement_rate()

        # Then
        assert avg_improvement == 0.0

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_get_latest_scores(self) -> None:
        """最新スコアの取得"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # 複数のチェック結果を追加
        for i in range(3):
            learning_metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=30, revision_count=1)
            category_scores = {"basic_writing_style": 80.0 + i * 5, "story_structure": 75.0 + i * 3}
            record.add_quality_check_result(
                episode_number=i + 1,
                category_scores=category_scores,
                errors=[],
                warnings=[],
                auto_fixes=[],
                learning_metrics=learning_metrics,
            )

        # When
        latest_scores = record.get_latest_scores()

        # Then
        assert latest_scores["basic_writing_style"] == 90.0  # 80 + 2 * 5
        assert latest_scores["story_structure"] == 81.0  # 75 + 2 * 3

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_get_latest_scores_no_data(self) -> None:
        """最新スコアの取得(データなし)"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # When
        latest_scores = record.get_latest_scores()

        # Then
        assert latest_scores == {}

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_get_weakest_categories(self) -> None:
        """最も弱いカテゴリの取得"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")
        learning_metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=30, revision_count=1)
        category_scores = {
            "basic_writing_style": 90.0,
            "story_structure": 65.0,
            "readability": 85.0,
            "character_consistency": 70.0,
            "pacing": 60.0,
        }
        record.add_quality_check_result(
            episode_number=1,
            category_scores=category_scores,
            errors=[],
            warnings=[],
            auto_fixes=[],
            learning_metrics=learning_metrics,
        )

        # When
        weakest = record.get_weakest_categories(limit=3)

        # Then
        assert weakest == ["pacing", "story_structure", "character_consistency"]

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_get_weakest_categories_no_data(self) -> None:
        """最も弱いカテゴリの取得(データなし)"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # When
        weakest = record.get_weakest_categories()

        # Then
        assert weakest == []

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_get_strongest_categories(self) -> None:
        """最も強いカテゴリの取得"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")
        learning_metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=30, revision_count=1)
        category_scores = {
            "basic_writing_style": 90.0,
            "story_structure": 65.0,
            "readability": 85.0,
            "character_consistency": 70.0,
            "pacing": 60.0,
        }
        record.add_quality_check_result(
            episode_number=1,
            category_scores=category_scores,
            errors=[],
            warnings=[],
            auto_fixes=[],
            learning_metrics=learning_metrics,
        )

        # When
        strongest = record.get_strongest_categories(limit=3)

        # Then
        assert strongest == ["basic_writing_style", "readability", "character_consistency"]

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_has_sufficient_data_for_analysis(self) -> None:
        """分析に十分なデータがあるか(True)"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # 3つのチェック結果を追加
        for i in range(3):
            learning_metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=30, revision_count=1)
            record.add_quality_check_result(
                episode_number=i + 1,
                category_scores={"score": 80.0},
                errors=[],
                warnings=[],
                auto_fixes=[],
                learning_metrics=learning_metrics,
            )

        # When & Then
        assert record.has_sufficient_data_for_analysis() is True
        assert record.has_sufficient_data_for_analysis(minimum_entries=2) is True
        assert record.has_sufficient_data_for_analysis(minimum_entries=4) is False

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_get_total_writing_time(self) -> None:
        """総執筆時間の取得"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # 複数のチェック結果を追加
        writing_times = [30, 45, 60, 25]
        for i, writing_time in enumerate(writing_times):
            learning_metrics = LearningMetrics(
                improvement_from_previous=0.0, time_spent_writing=writing_time, revision_count=1
            )

            record.add_quality_check_result(
                episode_number=i + 1,
                category_scores={"score": 80.0},
                errors=[],
                warnings=[],
                auto_fixes=[],
                learning_metrics=learning_metrics,
            )

        # When
        total_time = record.get_total_writing_time()

        # Then
        assert total_time == 160  # 30 + 45 + 60 + 25

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_get_total_revision_count(self) -> None:
        """総リビジョン数の取得"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # 複数のチェック結果を追加
        revision_counts = [1, 3, 2, 4]
        for i, count in enumerate(revision_counts):
            learning_metrics = LearningMetrics(
                improvement_from_previous=0.0, time_spent_writing=30, revision_count=count
            )

            record.add_quality_check_result(
                episode_number=i + 1,
                category_scores={"score": 80.0},
                errors=[],
                warnings=[],
                auto_fixes=[],
                learning_metrics=learning_metrics,
            )

        # When
        total_revisions = record.get_total_revision_count()

        # Then
        assert total_revisions == 10  # 1 + 3 + 2 + 4

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_get_learning_summary_with_data(self) -> None:
        """学習サマリーの取得(データあり)"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # 複数のチェック結果を追加
        for i in range(3):
            learning_metrics = LearningMetrics(
                improvement_from_previous=i * 2.0, time_spent_writing=30 + i * 10, revision_count=i + 1
            )

            category_scores = {
                "basic_writing_style": 90.0 - i * 5,
                "story_structure": 70.0 + i * 5,
                "readability": 80.0,
            }
            record.add_quality_check_result(
                episode_number=i + 1,
                category_scores=category_scores,
                errors=[],
                warnings=[],
                auto_fixes=[],
                learning_metrics=learning_metrics,
            )

        # When
        summary = record.get_learning_summary()

        # Then
        assert summary["total_entries"] == 3
        assert summary["total_writing_time"] == 120  # 30 + 40 + 50
        assert summary["total_revisions"] == 6  # 1 + 2 + 3
        assert summary["average_improvement_rate"] == 2.0  # (0 + 2 + 4) / 3
        assert summary["has_sufficient_data"] is True
        assert "strongest_categories" in summary
        assert "weakest_categories" in summary
        assert "latest_scores" in summary

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_get_learning_summary_no_data(self) -> None:
        """学習サマリーの取得(データなし)"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # When
        summary = record.get_learning_summary()

        # Then
        assert summary["total_entries"] == 0
        assert summary["total_writing_time"] == 0
        assert summary["total_revisions"] == 0
        assert summary["average_improvement_rate"] == 0.0
        assert summary["has_sufficient_data"] is False
        assert summary["strongest_categories"] == []
        assert summary["weakest_categories"] == []

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_can_generate_trend_analysis(self) -> None:
        """トレンド分析可能チェック"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # 3つのチェック結果を追加
        for i in range(3):
            learning_metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=30, revision_count=1)
            record.add_quality_check_result(
                episode_number=i + 1,
                category_scores={"score": 80.0},
                errors=[],
                warnings=[],
                auto_fixes=[],
                learning_metrics=learning_metrics,
            )

        # When & Then
        assert record.can_generate_trend_analysis() is True

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_can_generate_improvement_suggestions(self) -> None:
        """改善提案生成可能チェック"""
        # Given
        record_with_data = QualityRecordEnhancement(project_name="テストプロジェクト")
        record_without_data = QualityRecordEnhancement(project_name="テストプロジェクト2")

        # 3つのチェック結果を追加
        for i in range(3):
            learning_metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=30, revision_count=1)
            record_with_data.add_quality_check_result(
                episode_number=i + 1,
                category_scores={"score": 80.0},
                errors=[],
                warnings=[],
                auto_fixes=[],
                learning_metrics=learning_metrics,
            )

        # When & Then
        assert record_with_data.can_generate_improvement_suggestions() is True
        assert record_without_data.can_generate_improvement_suggestions() is False

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_generate_improvement_suggestions_precondition_check(self) -> None:
        """改善提案生成の前提条件チェック"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # データ不足の状態(2つのみ)
        for i in range(2):
            learning_metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=30, revision_count=1)
            record.add_quality_check_result(
                episode_number=i + 1,
                category_scores={"score": 80.0},
                errors=[],
                warnings=[],
                auto_fixes=[],
                learning_metrics=learning_metrics,
            )

        # When & Then
        with pytest.raises(BusinessRuleViolationError) as exc:
            record.generate_improvement_suggestions_precondition_check()
        assert "改善提案の生成には最低3回の品質チェックデータが必要です" in str(exc.value)
        assert "現在のデータ数: 2" in str(exc.value)

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_multiple_quality_checks_ordering(self) -> None:
        """複数の品質チェック結果の順序性"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")

        # 順序を入れ替えて追加
        episodes = [3, 1, 4, 2]
        for ep in episodes:
            learning_metrics = LearningMetrics(
                improvement_from_previous=ep * 1.0, time_spent_writing=30, revision_count=1
            )

            record.add_quality_check_result(
                episode_number=ep,
                category_scores={"basic_writing_style": 70.0 + ep * 5},
                errors=[],
                warnings=[],
                auto_fixes=[],
                learning_metrics=learning_metrics,
            )

        # When
        trend = record.get_improvement_trend("basic_writing_style")

        # Then
        # エピソード番号順にソートされていることを確認
        assert len(trend) == 4
        assert trend[0]["episode_number"] == 1
        assert trend[1]["episode_number"] == 2
        assert trend[2]["episode_number"] == 3
        assert trend[3]["episode_number"] == 4

    @pytest.mark.spec("SPEC-QUALITY-006")
    def test_id_generation_uniqueness(self) -> None:
        """ID生成の一意性確認"""
        # Given
        record = QualityRecordEnhancement(project_name="テストプロジェクト")
        learning_metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=30, revision_count=1)

        # When
        # 同じエピソード番号で2回追加
        record.add_quality_check_result(
            episode_number=1,
            category_scores={"score": 80.0},
            errors=[],
            warnings=[],
            auto_fixes=[],
            learning_metrics=learning_metrics,
        )

        time.sleep(0.001)  # タイムスタンプを変更するための小さな待機

        record.add_quality_check_result(
            episode_number=1,
            category_scores={"score": 85.0},
            errors=[],
            warnings=[],
            auto_fixes=[],
            learning_metrics=learning_metrics,
        )

        # Then
        assert len(record.quality_checks) == 2
        # IDが異なることを確認
        assert record.quality_checks[0]["id"] != record.quality_checks[1]["id"]
        # 両方のIDがプロジェクト名とエピソード番号を含むことを確認
        assert "テストプロジェクト_1_" in record.quality_checks[0]["id"]
        assert "テストプロジェクト_1_" in record.quality_checks[1]["id"]
