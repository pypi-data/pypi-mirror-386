#!/usr/bin/env python3
"""分析ドメインのエンティティのユニットテスト

TDD原則に従い、ビジネスロジックのテストを実装


仕様書: SPEC-UNIT-TEST
"""

from datetime import date, datetime

import pytest

from noveler.domain.analysis.entities import (
    AccessMetrics,
    AnalysisReport,
    DropoutAnalysis,
    EpisodeAccess,
)
from noveler.domain.analysis.value_objects import (
    AnalysisTimestamp,
    DateRange,
    DropoutRate,
    DropoutSeverity,
    PageView,
    UniqueUser,
)
from noveler.domain.writing.value_objects import EpisodeNumber


class TestEpisodeAccess:
    """EpisodeAccessエンティティのテスト"""

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-INITIAL_STATE")
    def test_initial_state(self) -> None:
        """初期状態の確認"""
        # When
        access = EpisodeAccess()

        # Then
        assert access.id is not None
        assert len(access.id) == 36  # UUID形式
        assert access.episode_number is None
        assert access.date is None
        assert access.page_views is None
        assert access.unique_users is None

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-CREATE_WITH_DATA")
    def test_create_with_data(self) -> None:
        """データ付きで作成"""
        # Given
        episode_num = EpisodeNumber(1)
        access_date = date(2025, 1, 15)
        pv = PageView(1000)
        uu = UniqueUser(500)

        # When
        access = EpisodeAccess(
            episode_number=episode_num,
            date=access_date,
            page_views=pv,
            unique_users=uu,
        )

        # Then
        assert access.episode_number == episode_num
        assert access.date == access_date
        assert access.page_views == pv
        assert access.unique_users == uu

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-CALCULATE_AVERAGE_VI")
    def test_calculate_average_views_per_user_valid(self) -> None:
        """ユーザーあたりの平均閲覧数計算(有効)"""
        # Given
        access = EpisodeAccess(
            page_views=PageView(1500),
            unique_users=UniqueUser(500),
        )

        # When
        avg = access.calculate_average_views_per_user()

        # Then
        assert avg == 3.0  # 1500 / 500

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-CALCULATE_AVERAGE_VI")
    def test_calculate_average_views_per_user_zero_users(self) -> None:
        """ユーザーあたりの平均閲覧数計算(ユーザー0)"""
        # Given
        access = EpisodeAccess(
            page_views=PageView(1000),
            unique_users=UniqueUser(0),
        )

        # When
        avg = access.calculate_average_views_per_user()

        # Then
        assert avg is None

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-CALCULATE_AVERAGE_VI")
    def test_calculate_average_views_per_user_no_data(self) -> None:
        """ユーザーあたりの平均閲覧数計算(データなし)"""
        # Given
        access = EpisodeAccess()

        # When
        avg = access.calculate_average_views_per_user()

        # Then
        assert avg is None

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-IS_DATA_AVAILABLE_TR")
    def test_is_data_available_true(self) -> None:
        """データ利用可能チェック(True)"""
        # Given
        access = EpisodeAccess(
            page_views=PageView(1000),
            unique_users=UniqueUser(500),
        )

        # When & Then
        assert access.is_data_available() is True

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-IS_DATA_AVAILABLE_NO")
    def test_is_data_available_no_views(self) -> None:
        """データ利用可能チェック(ビューなし)"""
        # Given
        access = EpisodeAccess(unique_users=UniqueUser(500))

        # When & Then
        assert access.is_data_available() is False

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-IS_DATA_AVAILABLE_ZE")
    def test_is_data_available_zero_views(self) -> None:
        """データ利用可能チェック(ビュー0)"""
        # Given
        access = EpisodeAccess(
            page_views=PageView(0),
            unique_users=UniqueUser(500),
        )

        # When & Then
        assert access.is_data_available() is False


class TestDropoutAnalysis:
    """DropoutAnalysisエンティティのテスト"""

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-INITIAL_STATE")
    def test_initial_state(self) -> None:
        """初期状態の確認"""
        # When
        analysis = DropoutAnalysis()

        # Then
        assert analysis.id is not None
        assert analysis.project_id == ""
        assert analysis.ncode is None
        assert analysis.episode_number is None
        assert analysis.previous_users is None
        assert analysis.current_users is None
        assert analysis.dropout_rate is None
        assert analysis.severity is None
        assert isinstance(analysis.analyzed_at, AnalysisTimestamp)

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-CALCULATE_DROPOUT_RA")
    def test_calculate_dropout_rate_normal(self) -> None:
        """離脱率計算(通常)"""
        # Given
        analysis = DropoutAnalysis(
            previous_users=UniqueUser(1000),
            current_users=UniqueUser(750),
        )

        # When
        analysis.calculate_dropout_rate()

        # Then
        assert analysis.dropout_rate is not None
        assert analysis.dropout_rate.value == 0.25  # 25%離脱
        assert analysis.severity == DropoutSeverity.HIGH

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-CALCULATE_DROPOUT_RA")
    def test_calculate_dropout_rate_no_previous(self) -> None:
        """離脱率計算(前回データなし)"""
        # Given
        analysis = DropoutAnalysis(current_users=UniqueUser(750))

        # When
        analysis.calculate_dropout_rate()

        # Then
        assert analysis.dropout_rate is None
        assert analysis.severity is None

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-CALCULATE_DROPOUT_RA")
    def test_calculate_dropout_rate_zero_previous(self) -> None:
        """離脱率計算(前回ユーザー0)"""
        # Given
        analysis = DropoutAnalysis(
            previous_users=UniqueUser(0),
            current_users=UniqueUser(100),
        )

        # When
        analysis.calculate_dropout_rate()

        # Then
        assert analysis.dropout_rate is None
        assert analysis.severity is None

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-IS_CRITICAL_TRUE")
    def test_is_critical_true(self) -> None:
        """危険な離脱率チェック(True)"""
        # Given
        analysis = DropoutAnalysis(
            dropout_rate=DropoutRate(0.35),
            severity=DropoutSeverity.CRITICAL,
        )

        # When & Then
        assert analysis.is_critical() is True

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-IS_CRITICAL_FALSE")
    def test_is_critical_false(self) -> None:
        """危険な離脱率チェック(False)"""
        # Given
        analysis = DropoutAnalysis(
            dropout_rate=DropoutRate(0.15),
            severity=DropoutSeverity.MODERATE,
        )

        # When & Then
        assert analysis.is_critical() is False

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-IS_SIGNIFICANT_TRUE")
    def test_is_significant_true(self) -> None:
        """有意な離脱率チェック(True)"""
        # Given
        analysis = DropoutAnalysis(dropout_rate=DropoutRate(0.25))

        # When & Then
        assert analysis.is_significant() is True  # 20%以上

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-IS_SIGNIFICANT_FALSE")
    def test_is_significant_false(self) -> None:
        """有意な離脱率チェック(False)"""
        # Given
        analysis = DropoutAnalysis(dropout_rate=DropoutRate(0.15))

        # When & Then
        assert analysis.is_significant() is False  # 20%未満

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-IS_SIGNIFICANT_NO_RA")
    def test_is_significant_no_rate(self) -> None:
        """有意な離脱率チェック(率なし)"""
        # Given
        analysis = DropoutAnalysis()

        # When & Then
        assert analysis.is_significant() is not True  # None or False

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GET_IMPROVEMENT_PRIO")
    def test_get_improvement_priority(self) -> None:
        """改善優先度取得"""
        # Given
        critical = DropoutAnalysis(severity=DropoutSeverity.CRITICAL)
        high = DropoutAnalysis(severity=DropoutSeverity.HIGH)
        moderate = DropoutAnalysis(severity=DropoutSeverity.MODERATE)
        low = DropoutAnalysis(severity=DropoutSeverity.LOW)
        none_severity = DropoutAnalysis()

        # When & Then
        assert critical.get_improvement_priority() == 1
        assert high.get_improvement_priority() == 2
        assert moderate.get_improvement_priority() == 3
        assert low.get_improvement_priority() == 4
        assert none_severity.get_improvement_priority() == 4


class TestAccessMetrics:
    """AccessMetricsエンティティのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.sample_accesses = [
            EpisodeAccess(
                episode_number=EpisodeNumber(1),
                page_views=PageView(1000),
                unique_users=UniqueUser(500),
            ),
            EpisodeAccess(
                episode_number=EpisodeNumber(2),
                page_views=PageView(800),
                unique_users=UniqueUser(400),
            ),
            EpisodeAccess(
                episode_number=EpisodeNumber(3),
                page_views=PageView(600),
                unique_users=UniqueUser(300),
            ),
        ]

        self.sample_analyses = [
            DropoutAnalysis(
                episode_number=EpisodeNumber(2),
                dropout_rate=DropoutRate(0.2),
                severity=DropoutSeverity.HIGH,
            ),
            DropoutAnalysis(
                episode_number=EpisodeNumber(3),
                dropout_rate=DropoutRate(0.25),
                severity=DropoutSeverity.HIGH,
            ),
        ]

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-INITIAL_STATE")
    def test_initial_state(self) -> None:
        """初期状態の確認"""
        # When
        metrics = AccessMetrics()

        # Then
        assert metrics.id is not None
        assert metrics.project_id == ""
        assert metrics.ncode is None
        assert isinstance(metrics.period, DateRange)
        assert metrics.episode_accesses == []
        assert metrics.dropout_analyses == []
        assert isinstance(metrics.created_at, datetime)

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-ADD_EPISODE_ACCESS")
    def test_add_episode_access(self) -> None:
        """エピソードアクセス情報追加"""
        # Given
        metrics = AccessMetrics()
        access = self.sample_accesses[0]

        # When
        metrics.add_episode_access(access)

        # Then
        assert len(metrics.episode_accesses) == 1
        assert metrics.episode_accesses[0] == access

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-ADD_DROPOUT_ANALYSIS")
    def test_add_dropout_analysis(self) -> None:
        """離脱率分析追加"""
        # Given
        metrics = AccessMetrics()
        analysis = self.sample_analyses[0]

        # When
        metrics.add_dropout_analysis(analysis)

        # Then
        assert len(metrics.dropout_analyses) == 1
        assert metrics.dropout_analyses[0] == analysis

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GET_TOTAL_PAGE_VIEWS")
    def test_get_total_page_views(self) -> None:
        """総ページビュー数取得"""
        # Given
        metrics = AccessMetrics(episode_accesses=self.sample_accesses)

        # When
        total = metrics.get_total_page_views()

        # Then
        assert total == 2400  # 1000 + 800 + 600

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GET_TOTAL_PAGE_VIEWS")
    def test_get_total_page_views_empty(self) -> None:
        """総ページビュー数取得(空)"""
        # Given
        metrics = AccessMetrics()

        # When
        total = metrics.get_total_page_views()

        # Then
        assert total == 0

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GET_TOTAL_UNIQUE_USE")
    def test_get_total_unique_users(self) -> None:
        """総ユニークユーザー数取得"""
        # Given
        metrics = AccessMetrics(episode_accesses=self.sample_accesses)

        # When
        total = metrics.get_total_unique_users()

        # Then
        assert total == 500  # 最初のエピソードのユーザー数

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GET_TOTAL_UNIQUE_USE")
    def test_get_total_unique_users_no_episodes(self) -> None:
        """総ユニークユーザー数取得(エピソードなし)"""
        # Given
        metrics = AccessMetrics()

        # When
        total = metrics.get_total_unique_users()

        # Then
        assert total == 0

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GET_AVERAGE_DROPOUT_")
    def test_get_average_dropout_rate(self) -> None:
        """平均離脱率取得"""
        # Given
        metrics = AccessMetrics(dropout_analyses=self.sample_analyses)

        # When
        avg_rate = metrics.get_average_dropout_rate()

        # Then
        assert avg_rate is not None
        assert avg_rate.value == 0.225  # (0.2 + 0.25) / 2

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GET_AVERAGE_DROPOUT_")
    def test_get_average_dropout_rate_no_data(self) -> None:
        """平均離脱率取得(データなし)"""
        # Given
        metrics = AccessMetrics()

        # When
        avg_rate = metrics.get_average_dropout_rate()

        # Then
        assert avg_rate is None

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GET_CRITICAL_EPISODE")
    def test_get_critical_episodes(self) -> None:
        """危険な離脱率のエピソード取得"""
        # Given
        critical = DropoutAnalysis(
            episode_number=EpisodeNumber(4),
            dropout_rate=DropoutRate(0.35),
            severity=DropoutSeverity.CRITICAL,
        )

        analyses = [*self.sample_analyses, critical]
        metrics = AccessMetrics(dropout_analyses=analyses)

        # When
        critical_episodes = metrics.get_critical_episodes()

        # Then
        assert len(critical_episodes) == 1
        assert critical_episodes[0] == critical

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GET_EPISODES_BY_SEVE")
    def test_get_episodes_by_severity(self) -> None:
        """深刻度別エピソード取得"""
        # Given
        critical = DropoutAnalysis(
            episode_number=EpisodeNumber(4),
            dropout_rate=DropoutRate(0.35),
            severity=DropoutSeverity.CRITICAL,
        )

        analyses = [*self.sample_analyses, critical]
        metrics = AccessMetrics(dropout_analyses=analyses)

        # When
        high_episodes = metrics.get_episodes_by_severity(DropoutSeverity.HIGH)
        critical_episodes = metrics.get_episodes_by_severity(DropoutSeverity.CRITICAL)

        # Then
        assert len(high_episodes) == 2
        assert len(critical_episodes) == 1

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GENERATE_SUMMARY")
    def test_generate_summary(self) -> None:
        """サマリー情報生成"""
        # Given
        metrics = AccessMetrics(
            period=DateRange(date(2025, 1, 1), date(2025, 1, 7)),
            episode_accesses=self.sample_accesses,
            dropout_analyses=self.sample_analyses,
        )

        # When
        summary = metrics.generate_summary()

        # Then
        assert summary["period"]["days"] == 7
        assert summary["total_episodes"] == 3
        assert summary["total_page_views"] == 2400
        assert summary["total_unique_users"] == 500
        assert summary["average_dropout_rate"] == 22.5  # 22.5%
        assert summary["critical_episodes"] == 0
        assert "severity_breakdown" in summary
        assert summary["severity_breakdown"][DropoutSeverity.HIGH.value] == 2


class TestAnalysisReport:
    """AnalysisReportエンティティのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.sample_metrics = AccessMetrics(
            episode_accesses=[
                EpisodeAccess(
                    episode_number=EpisodeNumber(1),
                    page_views=PageView(1000),
                    unique_users=UniqueUser(500),
                )
            ],
            dropout_analyses=[
                DropoutAnalysis(
                    episode_number=EpisodeNumber(2),
                    dropout_rate=DropoutRate(0.35),
                    severity=DropoutSeverity.CRITICAL,
                )
            ],
        )

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-INITIAL_STATE")
    def test_initial_state(self) -> None:
        """初期状態の確認"""
        # When
        report = AnalysisReport()

        # Then
        assert report.id is not None
        assert report.project_id == ""
        assert report.title == ""
        assert report.metrics is None
        assert report.recommendations == []
        assert isinstance(report.generated_at, datetime)

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-ADD_RECOMMENDATION")
    def test_add_recommendation(self) -> None:
        """推奨事項追加"""
        # Given
        report = AnalysisReport()
        recommendation = "第2話の離脱率が高いため、内容の見直しを推奨します。"

        # When
        report.add_recommendation(recommendation)

        # Then
        assert len(report.recommendations) == 1
        assert report.recommendations[0] == recommendation

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GENERATE_RECOMMENDAT")
    def test_generate_recommendations_with_critical_episodes(self) -> None:
        """推奨事項自動生成(危険なエピソードあり)"""
        # Given
        report = AnalysisReport(metrics=self.sample_metrics)

        # When
        report.generate_recommendations()

        # Then
        assert len(report.recommendations) > 0
        # 危険なエピソードについての推奨事項が含まれる
        assert any("離脱率が" in rec and "非常に高い" in rec for rec in report.recommendations)

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GENERATE_RECOMMENDAT")
    def test_generate_recommendations_high_average_dropout(self) -> None:
        """推奨事項自動生成(高い平均離脱率)"""
        # Given
        metrics = AccessMetrics(
            dropout_analyses=[
                DropoutAnalysis(dropout_rate=DropoutRate(0.2)),
                DropoutAnalysis(dropout_rate=DropoutRate(0.25)),
            ]
        )

        report = AnalysisReport(metrics=metrics)

        # When
        report.generate_recommendations()

        # Then
        assert any("全体の平均離脱率が" in rec for rec in report.recommendations)

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GENERATE_RECOMMENDAT")
    def test_generate_recommendations_improving_episodes(self) -> None:
        """推奨事項自動生成(改善エピソードあり)"""
        # Given
        metrics = AccessMetrics(
            dropout_analyses=[
                DropoutAnalysis(dropout_rate=DropoutRate(0.05)),
                DropoutAnalysis(dropout_rate=DropoutRate(0.08)),
            ]
        )

        report = AnalysisReport(metrics=metrics)

        # When
        report.generate_recommendations()

        # Then
        assert any("離脱率が10%未満と良好" in rec for rec in report.recommendations)

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GENERATE_RECOMMENDAT")
    def test_generate_recommendations_no_metrics(self) -> None:
        """推奨事項自動生成(メトリクスなし)"""
        # Given
        report = AnalysisReport()

        # When
        report.generate_recommendations()

        # Then
        assert len(report.recommendations) == 0

    @pytest.mark.spec("SPEC-ANALYSIS_ENTITIES-GENERATE_RECOMMENDAT")
    def test_generate_recommendations_limits_critical_episodes(self) -> None:
        """推奨事項自動生成(危険なエピソード数制限)"""
        # Given
        analyses = []
        for i in range(5):
            analyses.append(
                DropoutAnalysis(
                    episode_number=EpisodeNumber(i + 1),
                    dropout_rate=DropoutRate(0.35),
                    severity=DropoutSeverity.CRITICAL,
                )
            )

        metrics = AccessMetrics(dropout_analyses=analyses)
        report = AnalysisReport(metrics=metrics)

        # When
        report.generate_recommendations()

        # Then
        # 上位3つのみに関する推奨事項
        critical_recommendations = [rec for rec in report.recommendations if "離脱率が" in rec and "非常に高い" in rec]
        assert len(critical_recommendations) == 3
