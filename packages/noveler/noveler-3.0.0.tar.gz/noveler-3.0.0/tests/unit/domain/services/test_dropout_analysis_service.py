#!/usr/bin/env python3
"""離脱率分析サービスのテスト(TDD - RED段階)

離脱率計算とデータ検証のビジネスロジックをテスト。


仕様書: SPEC-DOMAIN-SERVICES
"""

from datetime import datetime, timezone

import pytest

from noveler.domain.entities.dropout_analysis_session import (
    DropoutRate,
    EpisodeDropout,
    EpisodeMetrics,
)
from noveler.domain.services.dropout_analysis_service import (
    DataValidationService,
    DropoutAnalysisService,
)


class TestDropoutAnalysisService:
    """離脱率分析サービスのテスト"""

    @pytest.mark.spec("SPEC-DROPOUT_ANALYSIS_SERVICE-CALCULATE_DROPOUT_RA")
    def test_calculate_dropout_rate(self) -> None:
        """離脱率を計算できる"""
        # Given
        service = DropoutAnalysisService()
        previous_pv = 1000
        current_pv = 800

        # When
        rate = service.calculate_dropout_rate(previous_pv, current_pv)

        # Then
        assert isinstance(rate, DropoutRate)
        assert rate.value == 20.0  # (1000-800)/1000 * 100

    @pytest.mark.spec("SPEC-DROPOUT_ANALYSIS_SERVICE-CALCULATE_DROPOUT_RA")
    def test_calculate_dropout_rate_with_zero_previous(self) -> None:
        """前のPVが0の場合は0%を返す"""
        # Given
        service = DropoutAnalysisService()

        # When
        rate = service.calculate_dropout_rate(0, 100)

        # Then
        assert rate.value == 0.0

    @pytest.mark.spec("SPEC-DROPOUT_ANALYSIS_SERVICE-ANALYZE_EPISODE_SEQU")
    def test_analyze_episode_sequence(self) -> None:
        """エピソードシーケンスから離脱率を分析できる"""
        # Given
        service = DropoutAnalysisService()
        metrics_list = [
            EpisodeMetrics(1, "第001話", 1000, 800, datetime.now(timezone.utc).date()),
            EpisodeMetrics(2, "第002話", 800, 700, datetime.now(timezone.utc).date()),
            EpisodeMetrics(3, "第003話", 600, 500, datetime.now(timezone.utc).date()),
        ]

        # When
        dropouts = service.analyze_episode_sequence(metrics_list)

        # Then
        assert len(dropouts) == 2
        assert dropouts[0].episode_number == 2
        assert dropouts[0].dropout_rate.value == 20.0
        assert dropouts[1].episode_number == 3
        assert dropouts[1].dropout_rate.value == 25.0

    @pytest.mark.spec("SPEC-DROPOUT_ANALYSIS_SERVICE-CALCULATE_AVERAGE_DR")
    def test_calculate_average_dropout(self) -> None:
        """平均離脱率を計算できる"""
        # Given
        service = DropoutAnalysisService()
        dropouts = [
            EpisodeDropout(2, "第002話", DropoutRate(20.0), 800, 1000),
            EpisodeDropout(3, "第003話", DropoutRate(30.0), 700, 1000),
            EpisodeDropout(4, "第004話", DropoutRate(25.0), 525, 700),
        ]

        # When
        avg_rate = service.calculate_average_dropout(dropouts)

        # Then
        assert avg_rate.value == 25.0  # (20+30+25)/3

    @pytest.mark.spec("SPEC-DROPOUT_ANALYSIS_SERVICE-IDENTIFY_CRITICAL_TH")
    def test_identify_critical_threshold(self) -> None:
        """重要な閾値を特定できる"""
        # Given
        service = DropoutAnalysisService()
        dropouts = [
            EpisodeDropout(2, "第002話", DropoutRate(15.0), 850, 1000),
            EpisodeDropout(3, "第003話", DropoutRate(35.0), 552, 850),  # Critical
            EpisodeDropout(4, "第004話", DropoutRate(40.0), 331, 552),  # Critical
            EpisodeDropout(5, "第005話", DropoutRate(10.0), 298, 331),
        ]

        # When
        critical = service.identify_critical_episodes(dropouts, threshold=30.0)

        # Then
        assert len(critical) == 2
        assert critical[0].episode_number == 3
        assert critical[1].episode_number == 4


class TestDataValidationService:
    """データ検証サービスのテスト"""

    @pytest.mark.spec("SPEC-DROPOUT_ANALYSIS_SERVICE-VALIDATE_EPISODE_MET")
    def test_validate_episode_metrics(self) -> None:
        """エピソードメトリクスを検証できる"""
        # Given
        service = DataValidationService()
        valid = EpisodeMetrics(1, "第001話", 1000, 800, datetime.now(timezone.utc).date())
        invalid = EpisodeMetrics(2, "第002話", 0, 0, datetime.now(timezone.utc).date())

        # When/Then
        assert service.is_valid_metrics(valid) is True
        assert service.is_valid_metrics(invalid) is False

    @pytest.mark.spec("SPEC-DROPOUT_ANALYSIS_SERVICE-FILTER_INCOMPLETE_DA")
    def test_filter_incomplete_data(self) -> None:
        """不完全なデータをフィルタできる"""
        # Given
        service = DataValidationService()
        metrics_list = [
            EpisodeMetrics(1, "第001話", 1000, 800, datetime.now(timezone.utc).date()),
            EpisodeMetrics(2, "第002話", 0, 0, datetime.now(timezone.utc).date()),  # 集計中
            EpisodeMetrics(3, "第003話", 800, 700, datetime.now(timezone.utc).date()),
            EpisodeMetrics(4, "第004話", 50, 40, datetime.now(timezone.utc).date()),  # 極端に低い
        ]

        # When
        filtered = service.filter_incomplete_data(metrics_list)

        # Then
        assert len(filtered) == 2
        assert filtered[0].episode_number == 1
        assert filtered[1].episode_number == 3

    @pytest.mark.spec("SPEC-DROPOUT_ANALYSIS_SERVICE-DETECT_EXTREME_DROPO")
    def test_detect_extreme_dropout(self) -> None:
        """極端な離脱率を検出できる"""
        # Given
        service = DataValidationService()
        metrics_list = [
            EpisodeMetrics(1, "第001話", 1000, 800, datetime.now(timezone.utc).date()),
            EpisodeMetrics(2, "第002話", 100, 90, datetime.now(timezone.utc).date()),  # 90%離脱
            EpisodeMetrics(3, "第003話", 95, 85, datetime.now(timezone.utc).date()),
        ]

        # When
        has_extreme, extreme_episodes = service.detect_extreme_dropout(metrics_list)

        # Then
        assert has_extreme is True
        assert len(extreme_episodes) == 1
        assert extreme_episodes[0].episode_number == 2

    @pytest.mark.spec("SPEC-DROPOUT_ANALYSIS_SERVICE-VALIDATE_DATA_FRESHN")
    def test_validate_data_freshness(self) -> None:
        """データの鮮度を検証できる"""
        # Given
        service = DataValidationService()

        # When
        message = service.get_data_freshness_warning()

        # Then
        assert "直近2日間" in message
        assert "集計中" in message
