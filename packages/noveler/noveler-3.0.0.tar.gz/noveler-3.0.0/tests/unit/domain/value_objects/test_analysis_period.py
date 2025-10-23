#!/usr/bin/env python3
"""AnalysisPeriod値オブジェクトのユニットテスト

SPEC-ANALYSIS-001に基づくTDD実装
"""

from datetime import date, datetime, timedelta, timezone

import pytest

from noveler.domain.value_objects.analysis_period import AnalysisPeriod

pytestmark = pytest.mark.vo_smoke



class TestAnalysisPeriod:
    """AnalysisPeriod値オブジェクトのテストクラス"""

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_create_valid_analysis_period(self) -> None:
        """正常なAnalysisPeriodの作成テスト"""
        # Given: 正常な期間データ
        start_date = date(2025, 7, 1)
        end_date = date(2025, 7, 14)
        days = 14

        # When: AnalysisPeriodを作成
        period = AnalysisPeriod(start_date=start_date, end_date=end_date, days=days)

        # Then: 正しく作成される
        assert period.start_date == start_date
        assert period.end_date == end_date
        assert period.days == days

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_invalid_period_start_after_end(self) -> None:
        """開始日が終了日より後の場合のエラーテスト"""
        # Given: 開始日が終了日より後
        start_date = date(2025, 7, 15)
        end_date = date(2025, 7, 1)
        days = 14

        # When/Then: エラーが発生
        with pytest.raises(ValueError, match="start_date must be before or equal to end_date"):
            AnalysisPeriod(start_date=start_date, end_date=end_date, days=days)

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_invalid_period_negative_days(self) -> None:
        """負の日数の場合のエラーテスト"""
        # Given: 負の日数
        start_date = date(2025, 7, 1)
        end_date = date(2025, 7, 14)
        days = -5

        # When/Then: エラーが発生
        with pytest.raises(ValueError, match="days must be positive"):
            AnalysisPeriod(start_date=start_date, end_date=end_date, days=days)

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_invalid_period_inconsistent_days(self) -> None:
        """実際の日数と指定日数が一致しない場合のエラーテスト"""
        # Given: 実際は14日間だが10日と指定
        start_date = date(2025, 7, 1)
        end_date = date(2025, 7, 14)
        days = 10  # 実際は14日間

        # When/Then: エラーが発生
        with pytest.raises(ValueError, match="days.*doesn't match actual period"):
            AnalysisPeriod(start_date=start_date, end_date=end_date, days=days)

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_contains_date_within_period(self) -> None:
        """期間内の日付判定テスト(True)"""
        # Given: 分析期間
        period = AnalysisPeriod(start_date=date(2025, 7, 1), end_date=date(2025, 7, 14), days=14)

        # When: 期間内の日付をチェック
        result = period.contains(date(2025, 7, 7))

        # Then: Trueが返される
        assert result is True

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_contains_date_outside_period(self) -> None:
        """期間外の日付判定テスト(False)"""
        # Given: 分析期間
        period = AnalysisPeriod(start_date=date(2025, 7, 1), end_date=date(2025, 7, 14), days=14)

        # When: 期間外の日付をチェック
        result = period.contains(date(2025, 7, 20))

        # Then: Falseが返される
        assert result is False

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_contains_boundary_dates(self) -> None:
        """境界日付の判定テスト"""
        # Given: 分析期間
        period = AnalysisPeriod(start_date=date(2025, 7, 1), end_date=date(2025, 7, 14), days=14)

        # When/Then: 境界日付は含まれる
        assert period.contains(date(2025, 7, 1)) is True
        assert period.contains(date(2025, 7, 14)) is True

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_is_recent_data_within_2_days(self) -> None:
        """直近2日間内のデータ判定テスト(True)"""
        # Given: 分析期間
        period = AnalysisPeriod(start_date=date(2025, 7, 1), end_date=date(2025, 7, 14), days=14)

        # When: 直近の日付をチェック
        yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
        result = period.is_recent_data(yesterday)

        # Then: Trueが返される
        assert result is True

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_is_recent_data_older_than_2_days(self) -> None:
        """直近2日間より古いデータ判定テスト(False)"""
        # Given: 分析期間
        period = AnalysisPeriod(start_date=date(2025, 7, 1), end_date=date(2025, 7, 14), days=14)

        # When: 古い日付をチェック
        old_date = datetime.now(timezone.utc).date() - timedelta(days=5)
        result = period.is_recent_data(old_date)

        # Then: Falseが返される
        assert result is False

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_last_14_days_factory(self) -> None:
        """直近14日間ファクトリメソッドテスト"""
        # When: 直近14日間を作成
        period = AnalysisPeriod.last_14_days()

        # Then: 正しい期間が作成される
        today = datetime.now(timezone.utc).date()
        expected_start = today - timedelta(days=13)

        assert period.start_date == expected_start
        assert period.end_date == today
        assert period.days == 14

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_last_30_days_factory(self) -> None:
        """直近30日間ファクトリメソッドテスト"""
        # When: 直近30日間を作成
        period = AnalysisPeriod.last_30_days()

        # Then: 正しい期間が作成される
        today = datetime.now(timezone.utc).date()
        expected_start = today - timedelta(days=29)

        assert period.start_date == expected_start
        assert period.end_date == today
        assert period.days == 30

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_custom_period_factory(self) -> None:
        """カスタム期間ファクトリメソッドテスト"""
        # Given: カスタム期間の日付
        start_date = date(2025, 7, 1)
        end_date = date(2025, 7, 10)

        # When: カスタム期間を作成
        period = AnalysisPeriod.custom_period(start_date, end_date)

        # Then: 正しい期間が作成される
        assert period.start_date == start_date
        assert period.end_date == end_date
        assert period.days == 10

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_analysis_period_immutability(self) -> None:
        """AnalysisPeriodの不変性テスト"""
        # Given: AnalysisPeriod
        period = AnalysisPeriod(start_date=date(2025, 7, 1), end_date=date(2025, 7, 14), days=14)

        # When/Then: 属性変更を試行するとエラーが発生
        with pytest.raises(AttributeError, match=".*"):
            period.days = 30
