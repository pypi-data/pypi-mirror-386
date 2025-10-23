"""離脱率メトリクス値オブジェクトのユニットテスト

TDD原則に基づき、実装前にテストを作成。
"""

from datetime import date, datetime, timezone

import pytest

from noveler.domain.value_objects.dropout_metrics import AccessData, DropoutMetrics, DropoutRate, EpisodeAccess

pytestmark = pytest.mark.vo_smoke



@pytest.mark.spec("SPEC-QUALITY-014")
class TestDropoutRate:
    """離脱率値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-CREATE")
    def test_create(self) -> None:
        """正常な範囲の離脱率を作成できることを確認"""
        # Given/When
        rate = DropoutRate(25.5)

        # Then
        assert rate.value == 25.5
        assert str(rate) == "25.5%"

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-UNNAMED")
    def test_unnamed(self) -> None:
        """0%の離脱率を作成できることを確認"""
        # Given/When
        rate = DropoutRate(0.0)

        # Then
        assert rate.value == 0.0
        assert str(rate) == "0.0%"

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-100")
    def test_100(self) -> None:
        """100%の離脱率を作成できることを確認"""
        # Given/When
        rate = DropoutRate(100.0)

        # Then
        assert rate.value == 100.0
        assert str(rate) == "100.0%"

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-UNNAMED")
    def test_basic_functionality(self) -> None:
        """離脱率の比較ができることを確認"""
        # Given
        rate1 = DropoutRate(20.0)
        rate2 = DropoutRate(30.0)
        rate3 = DropoutRate(20.0)

        # Then
        assert rate1 < rate2
        assert rate2 > rate1
        assert rate1 == rate3
        assert rate1 != rate2

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-DETERMINE")
    def test_determine(self) -> None:
        """高い離脱率かどうか判定できることを確認"""
        # Given
        high_rate = DropoutRate(30.0)
        normal_rate = DropoutRate(10.0)

        # Then
        assert high_rate.is_critical(threshold=20.0)
        assert not normal_rate.is_critical(threshold=20.0)


@pytest.mark.spec("SPEC-QUALITY-014")
class TestEpisodeAccess:
    """エピソードアクセス情報のテスト"""

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-UNNAMED")
    def test_edge_cases(self) -> None:
        """エピソードアクセス情報を作成できることを確認"""
        # Given/When
        access = EpisodeAccess(episode_number=5, page_views=1500, date=date(2024, 1, 15))

        # Then
        assert access.episode_number == 5
        assert access.page_views == 1500
        assert access.date == date(2024, 1, 15)

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-ERROR")
    def test_error(self) -> None:
        """無効なエピソード番号でエラーになることを確認"""
        # Given/When/Then
        with pytest.raises(ValueError) as exc_info:
            EpisodeAccess(episode_number=0, page_views=100, date=datetime.now(timezone.utc).date())
        assert "エピソード番号は1以上" in str(exc_info.value)

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-ERROR")
    def test_error_1(self) -> None:
        """負のページビュー数でエラーになることを確認"""
        # Given/When/Then
        with pytest.raises(ValueError) as exc_info:
            EpisodeAccess(episode_number=1, page_views=-1, date=datetime.now(timezone.utc).date())
        assert "ページビュー数は0以上" in str(exc_info.value)


@pytest.mark.spec("SPEC-QUALITY-014")
class TestAccessData:
    """アクセスデータコレクションのテスト"""

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-DATA_CREATE")
    def test_data_create(self) -> None:
        """アクセスデータコレクションを作成できることを確認"""
        # Given
        accesses = [
            EpisodeAccess(1, 1000, datetime.now(timezone.utc).date()),
            EpisodeAccess(2, 800, datetime.now(timezone.utc).date()),
            EpisodeAccess(3, 600, datetime.now(timezone.utc).date()),
        ]

        # When
        data = AccessData(accesses)

        # Then
        assert len(data) == 3
        assert data.get_episode_access(2).page_views == 800

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-UNNAMED")
    def test_error_handling(self) -> None:
        """特定エピソードのアクセス情報を取得できることを確認"""
        # Given
        data = AccessData(
            [
                EpisodeAccess(1, 1000, datetime.now(timezone.utc).date()),
                EpisodeAccess(2, 800, datetime.now(timezone.utc).date()),
            ]
        )

        # When
        access = data.get_episode_access(1)

        # Then
        assert access is not None
        assert access.page_views == 1000

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-GET")
    def test_get(self) -> None:
        """存在しないエピソードの情報取得時はNoneを返すことを確認"""
        # Given
        data = AccessData([EpisodeAccess(1, 1000, datetime.now(timezone.utc).date())])

        # When
        access = data.get_episode_access(999)

        # Then
        assert access is None

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-FILTER")
    def test_filter(self) -> None:
        """特定の日付のデータのみ取得できることを確認"""
        # Given
        data = AccessData(
            [
                EpisodeAccess(1, 1000, date(2024, 1, 1)),
                EpisodeAccess(1, 1100, date(2024, 1, 2)),
                EpisodeAccess(2, 800, date(2024, 1, 1)),
                EpisodeAccess(2, 850, date(2024, 1, 2)),
            ]
        )

        # When
        filtered = data.filter_by_date(date(2024, 1, 2))

        # Then
        assert len(filtered) == 2
        assert all(access.date == date(2024, 1, 2) for access in filtered.accesses)

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-UNNAMED")
    def test_validation(self) -> None:
        """エピソード番号順にソートされることを確認"""
        # Given
        data = AccessData(
            [
                EpisodeAccess(3, 600, datetime.now(timezone.utc).date()),
                EpisodeAccess(1, 1000, datetime.now(timezone.utc).date()),
                EpisodeAccess(2, 800, datetime.now(timezone.utc).date()),
            ]
        )

        # When
        sorted_data = data.sorted_by_episode()

        # Then
        episodes = [access.episode_number for access in sorted_data.accesses]
        assert episodes == [1, 2, 3]


@pytest.mark.spec("SPEC-QUALITY-014")
class TestDropoutMetrics:
    """離脱率メトリクスのテスト"""

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-UNNAMED")
    def test_integration(self) -> None:
        """離脱率メトリクスを作成できることを確認"""
        # Given/When
        metrics = DropoutMetrics()

        # Then
        assert metrics.average_dropout_rate == 0.0
        assert len(metrics.episode_rates) == 0

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-UNNAMED")
    def test_performance(self) -> None:
        """エピソード別の離脱率を追加できることを確認"""
        # Given
        metrics = DropoutMetrics()

        # When
        metrics.add_episode_rate(2, DropoutRate(20.0))
        metrics.add_episode_rate(3, DropoutRate(15.0))

        # Then
        assert len(metrics.episode_rates) == 2
        assert metrics.get_rate_for_episode(2).value == 20.0
        assert metrics.get_rate_for_episode(3).value == 15.0

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-UNNAMED")
    def test_configuration(self) -> None:
        """平均離脱率が正しく計算されることを確認"""
        # Given
        metrics = DropoutMetrics()
        metrics.add_episode_rate(2, DropoutRate(20.0))
        metrics.add_episode_rate(3, DropoutRate(30.0))
        metrics.add_episode_rate(4, DropoutRate(10.0))

        # When
        metrics.calculate_average()

        # Then
        assert metrics.average_dropout_rate == 20.0  # (20+30+10)/3

    @pytest.mark.spec("SPEC-DROPOUT_METRICS-GET")
    def test_get(self) -> None:
        """高い離脱率のエピソードを取得できることを確認"""
        # Given
        metrics = DropoutMetrics()
        metrics.add_episode_rate(1, DropoutRate(10.0))
        metrics.add_episode_rate(2, DropoutRate(25.0))
        metrics.add_episode_rate(3, DropoutRate(30.0))
        metrics.add_episode_rate(4, DropoutRate(15.0))

        # When
        critical = metrics.get_critical_episodes(threshold=20.0)

        # Then
        assert len(critical) == 2
        assert 2 in critical
        assert 3 in critical
