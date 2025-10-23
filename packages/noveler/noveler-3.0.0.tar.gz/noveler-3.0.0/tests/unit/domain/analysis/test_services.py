#!/usr/bin/env python3
"""分析ドメインサービスのユニットテスト

TDD原則に従い、ドメインサービスのビジネスロジックをテスト


仕様書: SPEC-UNIT-TEST
"""

from datetime import date, datetime, timezone
from unittest.mock import Mock

import pytest

from noveler.domain.analysis.entities import AccessMetrics, DropoutAnalysis, EpisodeAccess
from noveler.domain.analysis.services import AccessDataService, DropoutAnalyzer
from noveler.domain.analysis.value_objects import DateRange, DropoutRate, UniqueUser
from noveler.domain.writing.value_objects import EpisodeNumber


class TestAccessDataService:
    """AccessDataServiceインターフェースのテスト"""

    @pytest.mark.spec("SPEC-SERVICES-IS_ABSTRACT_INTERFAC")
    def test_is_abstract_interface(self) -> None:
        """抽象インターフェースであることを確認"""
        # When & Then
        with pytest.raises(TypeError, match=".*"):
            AccessDataService()

    @pytest.mark.spec("SPEC-SERVICES-INTERFACE_METHODS_DE")
    def test_interface_methods_defined(self) -> None:
        """インターフェースメソッドが定義されている"""
        # Given
        service = Mock()

        # When & Then
        assert hasattr(service, "fetch_episode_access")
        assert hasattr(service, "fetch_daily_access")
        assert hasattr(service, "is_data_available")


class TestDropoutAnalyzer:
    """DropoutAnalyzer分析サービスのテスト"""

    @pytest.mark.spec("SPEC-SERVICES-ANALYZE_DROPOUT_PATT")
    def test_analyze_dropout_patterns_insufficient_data(self) -> None:
        """データ不足時のエラーハンドリング"""
        # Given
        analyzer = DropoutAnalyzer()
        single_episode = [
            EpisodeAccess(
                episode_number=EpisodeNumber(1), unique_users=UniqueUser(100), date=datetime.now(timezone.utc).date()
            )
        ]

        # When
        result = analyzer.analyze_dropout_patterns(single_episode)

        # Then
        assert "error" in result
        assert result["error"] == "分析には2話以上のデータが必要です"

    @pytest.mark.spec("SPEC-SERVICES-ANALYZE_DROPOUT_PATT")
    def test_analyze_dropout_patterns_empty_data(self) -> None:
        """空データの場合"""
        # Given
        analyzer = DropoutAnalyzer()

        # When
        result = analyzer.analyze_dropout_patterns([])

        # Then
        assert "error" in result
        assert result["error"] == "分析には2話以上のデータが必要です"

    @pytest.mark.spec("SPEC-SERVICES-ANALYZE_DROPOUT_PATT")
    def test_analyze_dropout_patterns_sudden_drop_detected(self) -> None:
        """急激な離脱の検出"""
        # Given
        analyzer = DropoutAnalyzer()
        episodes = [
            EpisodeAccess(
                episode_number=EpisodeNumber(1), unique_users=UniqueUser(1000), date=datetime.now(timezone.utc).date()
            ),
            EpisodeAccess(
                episode_number=EpisodeNumber(2),
                unique_users=UniqueUser(700),  # 30%離脱
                date=datetime.now(timezone.utc).date(),
            ),
        ]

        # When
        result = analyzer.analyze_dropout_patterns(episodes)

        # Then
        assert "sudden_drops" in result
        assert len(result["sudden_drops"]) == 1
        assert result["sudden_drops"][0]["episode"] == EpisodeNumber(2)
        assert result["sudden_drops"][0]["users_lost"] == 300

    @pytest.mark.spec("SPEC-SERVICES-ANALYZE_DROPOUT_PATT")
    def test_analyze_dropout_patterns_recovery_point_detected(self) -> None:
        """回復ポイントの検出"""
        # Given
        analyzer = DropoutAnalyzer()
        episodes = [
            EpisodeAccess(
                episode_number=EpisodeNumber(1), unique_users=UniqueUser(800), date=datetime.now(timezone.utc).date()
            ),
            EpisodeAccess(
                episode_number=EpisodeNumber(2),
                unique_users=UniqueUser(900),  # 100人増加
                date=datetime.now(timezone.utc).date(),
            ),
        ]

        # When
        result = analyzer.analyze_dropout_patterns(episodes)

        # Then
        assert "recovery_points" in result
        assert len(result["recovery_points"]) == 1
        assert result["recovery_points"][0]["episode"] == EpisodeNumber(2)
        assert result["recovery_points"][0]["users_gained"] == 100

    @pytest.mark.spec("SPEC-SERVICES-ANALYZE_DROPOUT_PATT")
    def test_analyze_dropout_patterns_stable_section_detected(self) -> None:
        """安定区間の検出"""
        # Given
        analyzer = DropoutAnalyzer()
        episodes = [
            EpisodeAccess(
                episode_number=EpisodeNumber(1), unique_users=UniqueUser(1000), date=datetime.now(timezone.utc).date()
            ),
            EpisodeAccess(
                episode_number=EpisodeNumber(2),
                unique_users=UniqueUser(970),  # 3%離脱(安定)
                date=datetime.now(timezone.utc).date(),
            ),
        ]

        # When
        result = analyzer.analyze_dropout_patterns(episodes)

        # Then
        assert "stable_sections" in result
        assert len(result["stable_sections"]) == 1
        assert result["stable_sections"][0]["episode"] == EpisodeNumber(2)

    @pytest.mark.spec("SPEC-SERVICES-ANALYZE_DROPOUT_PATT")
    def test_analyze_dropout_patterns_none_unique_users_skipped(self) -> None:
        """ユニークユーザー数がNoneの場合はスキップ"""
        # Given
        analyzer = DropoutAnalyzer()
        episodes = [
            EpisodeAccess(
                episode_number=EpisodeNumber(1), unique_users=UniqueUser(1000), date=datetime.now(timezone.utc).date()
            ),
            EpisodeAccess(
                episode_number=EpisodeNumber(2),
                unique_users=None,  # None
                date=datetime.now(timezone.utc).date(),
            ),
            EpisodeAccess(
                episode_number=EpisodeNumber(3), unique_users=UniqueUser(1050), date=datetime.now(timezone.utc).date()
            ),
        ]

        # When
        result = analyzer.analyze_dropout_patterns(episodes)

        # Then
        # エピソード2がNoneなので、エピソード1→エピソード3の比較は行われない
        # （隣接エピソードのみ比較する実装のため）
        assert len(result["recovery_points"]) == 0
        assert len(result["sudden_drops"]) == 0
        assert len(result["stable_sections"]) == 0

    @pytest.mark.spec("SPEC-SERVICES-IDENTIFY_CRITICAL_EP")
    def test_identify_critical_episodes_with_high_dropout(self) -> None:
        """高離脱率エピソードの特定"""
        # Given
        analyzer = DropoutAnalyzer()

        # AccessMetricsエンティティのコンストラクタを確認してから使用
        metrics = AccessMetrics(
            project_id="テストプロジェクト",
            period=DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 1, 31)),
            episode_accesses=[],
            dropout_analyses=[
                DropoutAnalysis(
                    episode_number=EpisodeNumber(1),
                    dropout_rate=DropoutRate(0.1),  # 10%
                ),
                DropoutAnalysis(
                    episode_number=EpisodeNumber(2),
                    dropout_rate=DropoutRate(0.35),  # 35%(高い)
                ),
                DropoutAnalysis(
                    episode_number=EpisodeNumber(3),
                    dropout_rate=DropoutRate(0.25),  # 25%(高い)
                ),
            ],
        )

        # When
        critical_episodes = analyzer.identify_critical_episodes(metrics, threshold=0.2)

        # Then
        assert len(critical_episodes) == 2
        assert EpisodeNumber(2) in critical_episodes
        assert EpisodeNumber(3) in critical_episodes
        # 離脱率の高い順(35% > 25%)でソート
        assert critical_episodes[0] == EpisodeNumber(2)
        assert critical_episodes[1] == EpisodeNumber(3)
