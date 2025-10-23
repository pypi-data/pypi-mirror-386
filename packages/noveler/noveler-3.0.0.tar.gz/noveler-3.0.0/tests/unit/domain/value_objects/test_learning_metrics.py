#!/usr/bin/env python3
"""学習メトリクス値オブジェクトのユニットテスト

TDD原則に従い、値オブジェクトの不変条件とビジネスロジックをテスト


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.exceptions import ValidationError
from noveler.domain.value_objects.learning_metrics import LearningMetrics


class TestLearningMetrics:
    """LearningMetrics値オブジェクトのテスト"""

    def test_create_valid_minimal(self) -> None:
        """有効な最小限のデータで作成"""
        # When
        metrics = LearningMetrics(improvement_from_previous=5.0, time_spent_writing=30, revision_count=2)

        # Then
        assert metrics.improvement_from_previous == 5.0
        assert metrics.time_spent_writing == 30
        assert metrics.revision_count == 2
        assert metrics.user_feedback is None
        assert metrics.writing_context is None

    def test_create_valid_full(self) -> None:
        """有効な全データで作成"""
        # When
        metrics = LearningMetrics(
            improvement_from_previous=10.5,
            time_spent_writing=45,
            revision_count=3,
            user_feedback="構成が改善されました",
            writing_context="ch02のクライマックスシーン",
        )

        # Then
        assert metrics.improvement_from_previous == 10.5
        assert metrics.time_spent_writing == 45
        assert metrics.revision_count == 3
        assert metrics.user_feedback == "構成が改善されました"
        assert metrics.writing_context == "ch02のクライマックスシーン"

    def test_improvement_rate_validation_too_low(self) -> None:
        """改善率の検証(低すぎる値)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            LearningMetrics(improvement_from_previous=-101.0, time_spent_writing=30, revision_count=1)
        assert "改善率は-100%から100%の範囲で指定してください" in str(exc.value)

    def test_improvement_rate_validation_too_high(self) -> None:
        """改善率の検証(高すぎる値)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            LearningMetrics(improvement_from_previous=101.0, time_spent_writing=30, revision_count=1)
        assert "改善率は-100%から100%の範囲で指定してください" in str(exc.value)

    def test_improvement_rate_validation_boundary(self) -> None:
        """改善率の検証(境界値)"""
        # When & Then
        # -100%はOK
        metrics1 = LearningMetrics(improvement_from_previous=-100.0, time_spent_writing=30, revision_count=1)
        assert metrics1.improvement_from_previous == -100.0

        # 100%はOK
        metrics2 = LearningMetrics(improvement_from_previous=100.0, time_spent_writing=30, revision_count=1)
        assert metrics2.improvement_from_previous == 100.0

    def test_time_spent_validation_negative(self) -> None:
        """執筆時間の検証(負の値)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            LearningMetrics(improvement_from_previous=5.0, time_spent_writing=-1, revision_count=1)
        assert "執筆時間は0分以上で指定してください" in str(exc.value)

    def test_time_spent_validation_zero(self) -> None:
        """執筆時間の検証(0分)"""
        # When
        metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=0, revision_count=0)

        # Then
        assert metrics.time_spent_writing == 0

    def test_revision_count_validation_negative(self) -> None:
        """リビジョン数の検証(負の値)"""
        # When & Then
        with pytest.raises(ValidationError) as exc:
            LearningMetrics(improvement_from_previous=5.0, time_spent_writing=30, revision_count=-1)
        assert "リビジョン数は0以上で指定してください" in str(exc.value)

    def test_revision_count_validation_zero(self) -> None:
        """リビジョン数の検証(0回)"""
        # When
        metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=30, revision_count=0)

        # Then
        assert metrics.revision_count == 0

    def test_is_improvement_positive(self) -> None:
        """改善判定(正の改善)"""
        # Given
        metrics = LearningMetrics(improvement_from_previous=5.0, time_spent_writing=30, revision_count=1)

        # When & Then
        assert metrics.is_improvement() is True

    def test_is_improvement_zero(self) -> None:
        """改善判定(改善なし)"""
        # Given
        metrics = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=30, revision_count=1)

        # When & Then
        assert metrics.is_improvement() is False

    def test_is_improvement_negative(self) -> None:
        """改善判定(悪化)"""
        # Given
        metrics = LearningMetrics(improvement_from_previous=-5.0, time_spent_writing=30, revision_count=1)

        # When & Then
        assert metrics.is_improvement() is False

    def test_is_significant_improvement_default_threshold(self) -> None:
        """有意な改善判定(デフォルト閾値)"""
        # Given
        metrics1 = LearningMetrics(improvement_from_previous=5.0, time_spent_writing=30, revision_count=1)
        metrics2 = LearningMetrics(improvement_from_previous=4.9, time_spent_writing=30, revision_count=1)

        # When & Then
        default_threshold = 5.0
        assert metrics1.is_significant_improvement(default_threshold) is True  # 5.0 >= 5.0
        assert metrics2.is_significant_improvement(default_threshold) is False  # 4.9 < 5.0

    def test_is_significant_improvement_custom_threshold(self) -> None:
        """有意な改善判定(カスタム閾値)"""
        # Given
        metrics = LearningMetrics(improvement_from_previous=7.5, time_spent_writing=30, revision_count=1)

        # When & Then
        assert metrics.is_significant_improvement(threshold=10.0) is False  # 7.5 < 10.0
        assert metrics.is_significant_improvement(threshold=7.5) is True  # 7.5 >= 7.5
        assert metrics.is_significant_improvement(threshold=7.0) is True  # 7.5 >= 7.0

    def test_get_learning_efficiency_normal(self) -> None:
        """学習効率の計算(通常)"""
        # Given
        metrics = LearningMetrics(improvement_from_previous=10.0, time_spent_writing=20, revision_count=1)

        # When
        efficiency = metrics.get_learning_efficiency()

        # Then
        assert efficiency == 0.5  # 10.0 / 20

    def test_get_learning_efficiency_zero_time(self) -> None:
        """学習効率の計算(時間0)"""
        # Given
        metrics = LearningMetrics(improvement_from_previous=10.0, time_spent_writing=0, revision_count=1)

        # When
        efficiency = metrics.get_learning_efficiency()

        # Then
        assert efficiency == 0.0

    def test_get_learning_efficiency_negative_improvement(self) -> None:
        """学習効率の計算(負の改善)"""
        # Given
        metrics = LearningMetrics(improvement_from_previous=-5.0, time_spent_writing=10, revision_count=1)

        # When
        efficiency = metrics.get_learning_efficiency()

        # Then
        assert efficiency == -0.5  # -5.0 / 10

    def test_get_quality_description_major_improvement(self) -> None:
        """品質説明の取得(大幅な改善)"""
        # Given
        metrics = LearningMetrics(improvement_from_previous=15.0, time_spent_writing=30, revision_count=1)

        # When
        description = metrics.get_quality_description()

        # Then
        assert description == "大幅な改善"

    def test_get_quality_description_improvement(self) -> None:
        """品質説明の取得(改善)"""
        # Given
        metrics = LearningMetrics(improvement_from_previous=7.5, time_spent_writing=30, revision_count=1)

        # When
        description = metrics.get_quality_description()

        # Then
        assert description == "改善"

    def test_get_quality_description_stable(self) -> None:
        """品質説明の取得(現状維持)"""
        # Given
        metrics1 = LearningMetrics(improvement_from_previous=0.0, time_spent_writing=30, revision_count=1)
        metrics2 = LearningMetrics(improvement_from_previous=-4.9, time_spent_writing=30, revision_count=1)

        # When & Then
        assert metrics1.get_quality_description() == "現状維持"
        assert metrics2.get_quality_description() == "現状維持"

    def test_get_quality_description_needs_improvement(self) -> None:
        """品質説明の取得(要改善)"""
        # Given
        metrics = LearningMetrics(improvement_from_previous=-10.0, time_spent_writing=30, revision_count=1)

        # When
        description = metrics.get_quality_description()

        # Then
        assert description == "要改善"

    def test_get_quality_description_boundary_values(self) -> None:
        """品質説明の取得(境界値)"""
        # Given
        metrics1 = LearningMetrics(improvement_from_previous=10.0, time_spent_writing=30, revision_count=1)
        metrics2 = LearningMetrics(improvement_from_previous=10.1, time_spent_writing=30, revision_count=1)
        metrics3 = LearningMetrics(improvement_from_previous=5.0, time_spent_writing=30, revision_count=1)
        metrics4 = LearningMetrics(improvement_from_previous=5.1, time_spent_writing=30, revision_count=1)
        metrics5 = LearningMetrics(improvement_from_previous=-5.0, time_spent_writing=30, revision_count=1)
        metrics6 = LearningMetrics(improvement_from_previous=-5.1, time_spent_writing=30, revision_count=1)

        # When & Then
        assert metrics1.get_quality_description() == "改善"  # 10.0は改善
        assert metrics2.get_quality_description() == "大幅な改善"  # 10.1は大幅な改善
        assert metrics3.get_quality_description() == "現状維持"  # 5.0は現状維持
        assert metrics4.get_quality_description() == "改善"  # 5.1は改善
        assert metrics5.get_quality_description() == "要改善"  # -5.0は要改善
        assert metrics6.get_quality_description() == "要改善"  # -5.1は要改善

    def test_immutability(self) -> None:
        """値オブジェクトの不変性"""
        # Given
        metrics = LearningMetrics(
            improvement_from_previous=5.0,
            time_spent_writing=30,
            revision_count=2,
            user_feedback="良い改善",
            writing_context="ch01",
        )

        # When & Then
        # frozen=Trueのため、属性の変更はできない
        with pytest.raises(AttributeError, match=".*"):
            metrics.improvement_from_previous = 10.0

        with pytest.raises(AttributeError, match=".*"):
            metrics.time_spent_writing = 60

        with pytest.raises(AttributeError, match=".*"):
            metrics.revision_count = 5

        with pytest.raises(AttributeError, match=".*"):
            metrics.user_feedback = "新しいフィードバック"

    def test_equality(self) -> None:
        """値オブジェクトの等価性"""
        # Given
        metrics1 = LearningMetrics(
            improvement_from_previous=5.0,
            time_spent_writing=30,
            revision_count=2,
            user_feedback="良い改善",
            writing_context="ch01",
        )

        metrics2 = LearningMetrics(
            improvement_from_previous=5.0,
            time_spent_writing=30,
            revision_count=2,
            user_feedback="良い改善",
            writing_context="ch01",
        )

        metrics3 = LearningMetrics(
            improvement_from_previous=5.0,
            time_spent_writing=30,
            revision_count=2,
            user_feedback="良い改善",
            writing_context="ch02",  # 異なるコンテキスト
        )

        # When & Then
        assert metrics1 == metrics2
        assert metrics1 != metrics3
        assert hash(metrics1) == hash(metrics2)
        assert hash(metrics1) != hash(metrics3)
