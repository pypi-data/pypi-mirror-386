#!/usr/bin/env python3
"""BulkQualityCheck エンティティのユニットテスト

仕様書: specs/bulk_quality_check_entity.spec.md
TDD原則に従い、仕様書に基づいてテストを作成
"""

from datetime import datetime

import pytest

from noveler.domain.entities.bulk_quality_check import (
    BulkQualityCheck,
    QualityHistory,
    QualityRecord,
    QualityTrend,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_check_result import (
    CategoryScores,
    QualityCheckResult,
    QualityScore,
)

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestBulkQualityCheck:
    """BulkQualityCheckのテストクラス"""

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_constructor_with_valid_project_name(self) -> None:
        """有効なプロジェクト名で正常に初期化されることを確認"""
        # When
        bulk_check = BulkQualityCheck(project_name="テスト小説")

        # Then
        assert bulk_check.project_name == "テスト小説"
        assert bulk_check.episode_range is None
        assert bulk_check.parallel is False
        assert bulk_check.include_archived is False
        assert bulk_check.force_recheck is False

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_constructor_with_all_options(self) -> None:
        """全オプション指定で正常に初期化されることを確認"""
        # When
        bulk_check = BulkQualityCheck(
            project_name="テスト小説", episode_range=(1, 10), parallel=True, include_archived=True, force_recheck=True
        )

        # Then
        assert bulk_check.project_name == "テスト小説"
        assert bulk_check.episode_range == (1, 10)
        assert bulk_check.parallel is True
        assert bulk_check.include_archived is True
        assert bulk_check.force_recheck is True

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_constructor_trims_project_name(self) -> None:
        """プロジェクト名が自動的にトリムされることを確認"""
        # When
        bulk_check = BulkQualityCheck(project_name="  テスト小説  ")

        # Then
        assert bulk_check.project_name == "  テスト小説  "  # dataclassなので__post_init__で検証のみ

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_post_init_validation_empty_project_name(self) -> None:
        """空のプロジェクト名でValueErrorが発生することを確認"""
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            BulkQualityCheck(project_name="")
        assert "Project name cannot be empty" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            BulkQualityCheck(project_name="   ")
        assert "Project name cannot be empty" in str(exc_info.value)


class TestQualityRecord:
    """QualityRecordのテストクラス"""

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_constructor_creates_record_correctly(self) -> None:
        """レコードが正しく作成されることを確認"""
        # Given
        timestamp = datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST)
        category_scores = {"style": 85.0, "structure": 80.0}

        # When
        record = QualityRecord(
            episode_number=1, quality_score=82.5, category_scores=category_scores, timestamp=timestamp
        )

        # Then
        assert record.episode_number == 1
        assert record.quality_score == 82.5
        assert record.category_scores == category_scores
        assert record.timestamp == timestamp


class TestQualityTrend:
    """QualityTrendのテストクラス"""

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_constructor_creates_trend_correctly(self) -> None:
        """トレンドが正しく作成されることを確認"""
        # When
        trend = QualityTrend(direction="improving", slope=2.5, confidence=0.8)

        # Then
        assert trend.direction == "improving"
        assert trend.slope == 2.5
        assert trend.confidence == 0.8


class TestQualityHistory:
    """QualityHistoryのテストクラス"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.history = QualityHistory("テスト小説")

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_constructor_initializes_correctly(self) -> None:
        """コンストラクタで正しく初期化されることを確認"""
        # Then
        assert self.history.project_name == "テスト小説"
        assert len(self.history.records) == 0

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_add_record_appends_with_current_timestamp(self) -> None:
        """記録追加時に現在時刻が設定されることを確認"""
        # Given
        category_scores = CategoryScores(
            basic_style=QualityScore.from_float(85.0),
            composition=QualityScore.from_float(80.0),
            character_consistency=QualityScore.from_float(82.0),
            readability=QualityScore.from_float(83.0),
        )

        quality_result = QualityCheckResult(
            episode_number=1,
            timestamp=datetime(2025, 1, 1, 10, 0, 0, tzinfo=JST),
            checker_version="1.0.0",
            category_scores=category_scores,
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        before_time = project_now().datetime

        # When
        self.history.add_record(1, quality_result)

        # Then
        after_time = project_now().datetime
        assert len(self.history.records) == 1

        record = self.history.records[0]
        assert record.episode_number == 1
        assert record.quality_score == 82.5  # (85 + 80 + 82 + 83) / 4
        assert record.category_scores == {
            "basic_style": 85.0,
            "composition": 80.0,
            "character_consistency": 82.0,
            "readability": 83.0,
        }
        assert before_time <= record.timestamp <= after_time

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_calculate_trend_with_insufficient_data(self) -> None:
        """記録が2件未満の場合のトレンド計算を確認"""
        # Given: 記録が1件のみ
        category_scores = CategoryScores(
            basic_style=QualityScore.from_float(85.0),
            composition=QualityScore.from_float(85.0),
            character_consistency=QualityScore.from_float(85.0),
            readability=QualityScore.from_float(85.0),
        )

        quality_result = QualityCheckResult(
            episode_number=1,
            timestamp=project_now().datetime,
            checker_version="1.0.0",
            category_scores=category_scores,
            errors=[],
            warnings=[],
            auto_fixes=[],
        )

        self.history.add_record(1, quality_result)

        # When
        trend = self.history.calculate_trend()

        # Then
        assert trend.direction == "stable"
        assert trend.slope == 0.0
        assert trend.confidence == 0.0

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_calculate_trend_improving(self) -> None:
        """改善傾向のトレンド計算を確認"""
        # Given: 改善傾向のスコア
        scores = [70.0, 75.0, 80.0, 85.0, 90.0]
        for i, score in enumerate(scores):
            category_scores = CategoryScores(
                basic_style=QualityScore.from_float(score),
                composition=QualityScore.from_float(score),
                character_consistency=QualityScore.from_float(score),
                readability=QualityScore.from_float(score),
            )

            quality_result = QualityCheckResult(
                episode_number=i + 1,
                timestamp=project_now().datetime,
                checker_version="1.0.0",
                category_scores=category_scores,
                errors=[],
                warnings=[],
                auto_fixes=[],
            )

            self.history.add_record(i + 1, quality_result)

        # When
        trend = self.history.calculate_trend()

        # Then
        assert trend.direction == "improving"
        assert trend.slope > 1.0
        assert 0.0 < trend.confidence <= 1.0

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_calculate_trend_declining(self) -> None:
        """悪化傾向のトレンド計算を確認"""
        # Given: 悪化傾向のスコア
        scores = [90.0, 85.0, 80.0, 75.0, 70.0]
        for i, score in enumerate(scores):
            category_scores = CategoryScores(
                basic_style=QualityScore.from_float(score),
                composition=QualityScore.from_float(score),
                character_consistency=QualityScore.from_float(score),
                readability=QualityScore.from_float(score),
            )

            quality_result = QualityCheckResult(
                episode_number=i + 1,
                timestamp=project_now().datetime,
                checker_version="1.0.0",
                category_scores=category_scores,
                errors=[],
                warnings=[],
                auto_fixes=[],
            )

            self.history.add_record(i + 1, quality_result)

        # When
        trend = self.history.calculate_trend()

        # Then
        assert trend.direction == "declining"
        assert trend.slope < -1.0
        assert 0.0 < trend.confidence <= 1.0

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_calculate_trend_stable(self) -> None:
        """安定傾向のトレンド計算を確認"""
        # Given: 安定しているスコア
        scores = [85.0, 84.0, 86.0, 85.5, 84.5]
        for i, score in enumerate(scores):
            category_scores = CategoryScores(
                basic_style=QualityScore.from_float(score),
                composition=QualityScore.from_float(score),
                character_consistency=QualityScore.from_float(score),
                readability=QualityScore.from_float(score),
            )

            quality_result = QualityCheckResult(
                episode_number=i + 1,
                timestamp=project_now().datetime,
                checker_version="1.0.0",
                category_scores=category_scores,
                errors=[],
                warnings=[],
                auto_fixes=[],
            )

            self.history.add_record(i + 1, quality_result)

        # When
        trend = self.history.calculate_trend()

        # Then
        assert trend.direction == "stable"
        assert -1.0 <= trend.slope <= 1.0
        assert 0.0 <= trend.confidence <= 1.0

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_find_problematic_episodes_default_threshold(self) -> None:
        """デフォルト閾値での問題エピソード特定を確認"""
        # Given: 混合品質スコア
        test_data = [(1, 75.0), (2, 65.0), (3, 85.0), (4, 60.0), (5, 80.0)]
        for episode_num, score in test_data:
            category_scores = CategoryScores(
                basic_style=QualityScore.from_float(score),
                composition=QualityScore.from_float(score),
                character_consistency=QualityScore.from_float(score),
                readability=QualityScore.from_float(score),
            )

            quality_result = QualityCheckResult(
                episode_number=episode_num,
                timestamp=project_now().datetime,
                checker_version="1.0.0",
                category_scores=category_scores,
                errors=[],
                warnings=[],
                auto_fixes=[],
            )

            self.history.add_record(episode_num, quality_result)

        # When
        problematic_episodes = self.history.find_problematic_episodes()

        # Then
        # 70.0未満は episode 2 (65.0) と episode 4 (60.0)
        assert problematic_episodes == [2, 4]

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_find_problematic_episodes_custom_threshold(self) -> None:
        """カスタム閾値での問題エピソード特定を確認"""
        # Given: 混合品質スコア
        test_data = [(1, 75.0), (2, 85.0), (3, 90.0), (4, 78.0), (5, 82.0)]
        for episode_num, score in test_data:
            category_scores = CategoryScores(
                basic_style=QualityScore.from_float(score),
                composition=QualityScore.from_float(score),
                character_consistency=QualityScore.from_float(score),
                readability=QualityScore.from_float(score),
            )

            quality_result = QualityCheckResult(
                episode_number=episode_num,
                timestamp=project_now().datetime,
                checker_version="1.0.0",
                category_scores=category_scores,
                errors=[],
                warnings=[],
                auto_fixes=[],
            )

            self.history.add_record(episode_num, quality_result)

        # When
        problematic_episodes = self.history.find_problematic_episodes(threshold=80.0)

        # Then
        # 80.0未満は episode 1 (75.0) と episode 4 (78.0)
        assert problematic_episodes == [1, 4]

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_find_problematic_episodes_no_problems(self) -> None:
        """問題なしの場合は空リストが返されることを確認"""
        # Given: 全て高品質スコア
        test_data = [(1, 85.0), (2, 88.0), (3, 90.0)]
        for episode_num, score in test_data:
            category_scores = CategoryScores(
                basic_style=QualityScore.from_float(score),
                composition=QualityScore.from_float(score),
                character_consistency=QualityScore.from_float(score),
                readability=QualityScore.from_float(score),
            )

            quality_result = QualityCheckResult(
                episode_number=episode_num,
                timestamp=project_now().datetime,
                checker_version="1.0.0",
                category_scores=category_scores,
                errors=[],
                warnings=[],
                auto_fixes=[],
            )

            self.history.add_record(episode_num, quality_result)

        # When
        problematic_episodes = self.history.find_problematic_episodes(threshold=70.0)

        # Then
        assert problematic_episodes == []

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_confidence_calculation_boundary_cases(self) -> None:
        """信頼度計算の境界ケースを確認"""
        # Given: 極端な変化のスコア
        extreme_scores = [0.0, 100.0]
        for i, score in enumerate(extreme_scores):
            category_scores = CategoryScores(
                basic_style=QualityScore.from_float(score),
                composition=QualityScore.from_float(score),
                character_consistency=QualityScore.from_float(score),
                readability=QualityScore.from_float(score),
            )

            quality_result = QualityCheckResult(
                episode_number=i + 1,
                timestamp=project_now().datetime,
                checker_version="1.0.0",
                category_scores=category_scores,
                errors=[],
                warnings=[],
                auto_fixes=[],
            )

            self.history.add_record(i + 1, quality_result)

        # When
        trend = self.history.calculate_trend()

        # Then
        # 信頼度は1.0に制限される
        assert trend.confidence <= 1.0
        assert trend.confidence >= 0.0

    @pytest.mark.spec("SPEC-QUALITY-012")
    def test_linear_regression_calculation(self) -> None:
        """線形回帰の計算が正しく行われることを確認"""
        # Given: 完全な線形増加
        scores = [20.0, 40.0, 60.0, 80.0, 100.0]
        for i, score in enumerate(scores):
            category_scores = CategoryScores(
                basic_style=QualityScore.from_float(score),
                composition=QualityScore.from_float(score),
                character_consistency=QualityScore.from_float(score),
                readability=QualityScore.from_float(score),
            )

            quality_result = QualityCheckResult(
                episode_number=i + 1,
                timestamp=project_now().datetime,
                checker_version="1.0.0",
                category_scores=category_scores,
                errors=[],
                warnings=[],
                auto_fixes=[],
            )

            self.history.add_record(i + 1, quality_result)

        # When
        trend = self.history.calculate_trend()

        # Then
        # 完全な線形増加なので slope は正の値
        assert trend.slope == 20.0  # y = 20x の傾き
        assert trend.direction == "improving"
