"""Tests.tests.unit.domain.analysis.test_analysis_value_objects
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from datetime import date, datetime, timezone

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

#!/usr/bin/env python3
"""分析ドメインの値オブジェクトのユニットテスト

TDD原則に従い、値オブジェクトの不変性とビジネスルールをテスト


仕様書: SPEC-UNIT-TEST
"""

from datetime import timedelta
from unittest.mock import Mock

import pytest

from noveler.domain.analysis.value_objects import (
    AnalysisPeriod,
    AnalysisTimestamp,
    DateRange,
    DropoutRate,
    DropoutSeverity,
    NarouCode,
    PageView,
    UniqueUser,
)

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestAnalysisPeriod:
    """AnalysisPeriod列挙型のテスト"""

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-ALL_PERIODS_DEFINED")
    def test_all_periods_defined(self) -> None:
        """全ての分析期間が定義されていることを確認"""
        expected_periods = ["daily", "weekly", "monthly", "all_time"]
        actual_periods = [period.value for period in AnalysisPeriod]
        assert set(expected_periods) == set(actual_periods)


class TestDropoutSeverity:
    """DropoutSeverity列挙型のテスト"""

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-ALL_SEVERITIES_DEFIN")
    def test_all_severities_defined(self) -> None:
        """全ての深刻度が定義されていることを確認"""
        expected_severities = ["low", "moderate", "high", "critical"]
        actual_severities = [severity.value for severity in DropoutSeverity]
        assert set(expected_severities) == set(actual_severities)


class TestDropoutRate:
    """DropoutRate値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-CREATE_VALID_DROPOUT")
    def test_create_valid_dropout_rate(self) -> None:
        """有効な離脱率の作成"""
        # When
        rate = DropoutRate(0.25)

        # Then
        assert rate.value == 0.25

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-IMMUTABILITY")
    def test_immutability(self) -> None:
        """不変性の確認"""
        # Given
        rate = DropoutRate(0.25)

        # When & Then
        with pytest.raises(AttributeError, match=".*"):
            rate.value = 0.5

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-INVALID_RATE_BELOW_Z")
    def test_invalid_rate_below_zero(self) -> None:
        """0未満の離脱率でエラー"""
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            DropoutRate(-0.1)
        assert "離脱率は0.0から1.0の範囲である必要があります" in str(exc_info.value)

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-INVALID_RATE_ABOVE_O")
    def test_invalid_rate_above_one(self) -> None:
        """1を超える離脱率でエラー"""
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            DropoutRate(1.1)
        assert "離脱率は0.0から1.0の範囲である必要があります" in str(exc_info.value)

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-BOUNDARY_VALUES")
    def test_boundary_values(self) -> None:
        """境界値の確認"""
        # When & Then (例外が発生しない)
        DropoutRate(0.0)
        DropoutRate(1.0)

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-TO_PERCENTAGE")
    def test_to_percentage(self) -> None:
        """パーセンテージ変換"""
        # Given
        rate = DropoutRate(0.25)

        # When
        percentage = rate.to_percentage()

        # Then
        assert percentage == 25.0

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-GET_SEVERITY_LOW")
    def test_get_severity_low(self) -> None:
        """深刻度判定(低)"""
        # Given
        rate = DropoutRate(0.05)  # 5%

        # When
        severity = rate.get_severity()

        # Then
        assert severity == DropoutSeverity.LOW

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-GET_SEVERITY_MODERAT")
    def test_get_severity_moderate(self) -> None:
        """深刻度判定(中)"""
        # Given
        rate = DropoutRate(0.15)  # 15%

        # When
        severity = rate.get_severity()

        # Then
        assert severity == DropoutSeverity.MODERATE

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-GET_SEVERITY_HIGH")
    def test_get_severity_high(self) -> None:
        """深刻度判定(高)"""
        # Given
        rate = DropoutRate(0.25)  # 25%

        # When
        severity = rate.get_severity()

        # Then
        assert severity == DropoutSeverity.HIGH

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-GET_SEVERITY_CRITICA")
    def test_get_severity_critical(self) -> None:
        """深刻度判定(危険)"""
        # Given
        rate = DropoutRate(0.35)  # 35%

        # When
        severity = rate.get_severity()

        # Then
        assert severity == DropoutSeverity.CRITICAL

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-GET_SEVERITY_BOUNDAR")
    def test_get_severity_boundaries(self) -> None:
        """深刻度判定の境界値"""
        assert DropoutRate(0.099).get_severity() == DropoutSeverity.LOW
        assert DropoutRate(0.1).get_severity() == DropoutSeverity.MODERATE
        assert DropoutRate(0.199).get_severity() == DropoutSeverity.MODERATE
        assert DropoutRate(0.2).get_severity() == DropoutSeverity.HIGH
        assert DropoutRate(0.299).get_severity() == DropoutSeverity.HIGH
        assert DropoutRate(0.3).get_severity() == DropoutSeverity.CRITICAL

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-IS_ACCEPTABLE_DEFAUL")
    def test_is_acceptable_default_threshold(self) -> None:
        """許容可能チェック(デフォルト閾値)"""
        # Given
        acceptable = DropoutRate(0.15)
        unacceptable = DropoutRate(0.25)

        # When & Then
        assert acceptable.is_acceptable() is True
        assert unacceptable.is_acceptable() is False

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-IS_ACCEPTABLE_CUSTOM")
    def test_is_acceptable_custom_threshold(self) -> None:
        """許容可能チェック(カスタム閾値)"""
        # Given
        rate = DropoutRate(0.15)

        # When & Then
        assert rate.is_acceptable(0.1) is False
        assert rate.is_acceptable(0.2) is True

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-STR_REPRESENTATION")
    def test_str_representation(self) -> None:
        """文字列表現"""
        # Given
        rate = DropoutRate(0.254)

        # When
        str_rep = str(rate)

        # Then
        assert str_rep == "25.4%"


class TestPageView:
    """PageView値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-CREATE_VALID_PAGE_VI")
    def test_create_valid_page_view(self) -> None:
        """有効なページビューの作成"""
        # When
        pv = PageView(1000)

        # Then
        assert pv.value == 1000

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-IMMUTABILITY")
    def test_immutability(self) -> None:
        """不変性の確認"""
        # Given
        pv = PageView(1000)

        # When & Then
        with pytest.raises(AttributeError, match=".*"):
            pv.value = 2000

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-INVALID_NEGATIVE_VAL")
    def test_invalid_negative_value(self) -> None:
        """負の値でエラー"""
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            PageView(-1)
        assert "ページビューは0以上である必要があります" in str(exc_info.value)

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-ZERO_VALUE")
    def test_zero_value(self) -> None:
        """0値の確認"""
        # When & Then (例外が発生しない)
        pv = PageView(0)
        assert pv.value == 0

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-ADDITION")
    def test_addition(self) -> None:
        """ページビューの加算"""
        # Given
        pv1 = PageView(1000)
        pv2 = PageView(500)

        # When
        result = pv1 + pv2

        # Then
        assert isinstance(result, PageView)
        assert result.value == 1500

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-SUBTRACTION")
    def test_subtraction(self) -> None:
        """ページビューの差分"""
        # Given
        pv1 = PageView(1000)
        pv2 = PageView(300)

        # When
        diff = pv1 - pv2

        # Then
        assert isinstance(diff, int)
        assert diff == 700


class TestUniqueUser:
    """UniqueUser値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-CREATE_VALID_UNIQUE_")
    def test_create_valid_unique_user(self) -> None:
        """有効なユニークユーザーの作成"""
        # When
        uu = UniqueUser(500)

        # Then
        assert uu.value == 500

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-IMMUTABILITY")
    def test_immutability(self) -> None:
        """不変性の確認"""
        # Given
        uu = UniqueUser(500)

        # When & Then
        with pytest.raises(AttributeError, match=".*"):
            uu.value = 600

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-INVALID_NEGATIVE_VAL")
    def test_invalid_negative_value(self) -> None:
        """負の値でエラー"""
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            UniqueUser(-1)
        assert "ユニークユーザー数は0以上である必要があります" in str(exc_info.value)

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-CALCULATE_DROPOUT_RA")
    def test_calculate_dropout_rate_normal(self) -> None:
        """通常の離脱率計算"""
        # Given
        current = UniqueUser(300)
        previous = UniqueUser(400)

        # When
        dropout_rate = current.calculate_dropout_rate(previous)

        # Then
        assert dropout_rate is not None
        assert dropout_rate.value == 0.25  # (400 - 300) / 400

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-CALCULATE_DROPOUT_RA")
    def test_calculate_dropout_rate_no_change(self) -> None:
        """変化なしの離脱率計算"""
        # Given
        current = UniqueUser(400)
        previous = UniqueUser(400)

        # When
        dropout_rate = current.calculate_dropout_rate(previous)

        # Then
        assert dropout_rate is not None
        assert dropout_rate.value == 0.0

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-CALCULATE_DROPOUT_RA")
    def test_calculate_dropout_rate_increase(self) -> None:
        """ユーザー数増加時の離脱率計算"""
        # Given
        current = UniqueUser(500)
        previous = UniqueUser(400)

        # When
        dropout_rate = current.calculate_dropout_rate(previous)

        # Then
        assert dropout_rate is not None
        assert dropout_rate.value == 0.0  # 増加時は離脱率0

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-CALCULATE_DROPOUT_RA")
    def test_calculate_dropout_rate_zero_previous(self) -> None:
        """前回ユーザー数0の場合"""
        # Given
        current = UniqueUser(100)
        previous = UniqueUser(0)

        # When
        dropout_rate = current.calculate_dropout_rate(previous)

        # Then
        assert dropout_rate is None


class TestDateRange:
    """DateRange値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-CREATE_VALID_DATE_RA")
    def test_create_valid_date_range(self) -> None:
        """有効な日付範囲の作成"""
        # Given
        start = date(2025, 1, 1)
        end = date(2025, 1, 31)

        # When
        date_range = DateRange(start, end)

        # Then
        assert date_range.start_date == start
        assert date_range.end_date == end

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-IMMUTABILITY")
    def test_immutability(self) -> None:
        """不変性の確認"""
        # Given
        date_range = DateRange(date(2025, 1, 1), date(2025, 1, 31))

        # When & Then
        with pytest.raises(AttributeError, match=".*"):
            date_range.start_date = date(2025, 2, 1)

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-INVALID_DATE_ORDER")
    def test_invalid_date_order(self) -> None:
        """開始日が終了日より後の場合のエラー"""
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            DateRange(date(2025, 2, 1), date(2025, 1, 1))
        assert "開始日は終了日以前である必要があります" in str(exc_info.value)

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-SAME_DATE_RANGE")
    def test_same_date_range(self) -> None:
        """同日の範囲"""
        # When & Then (例外が発生しない)
        date_range = DateRange(date(2025, 1, 1), date(2025, 1, 1))
        assert date_range.days() == 1

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-CONTAINS")
    def test_contains(self) -> None:
        """日付が範囲内かチェック"""
        # Given
        date_range = DateRange(date(2025, 1, 10), date(2025, 1, 20))

        # When & Then
        assert date_range.contains(date(2025, 1, 15)) is True
        assert date_range.contains(date(2025, 1, 10)) is True  # 開始日
        assert date_range.contains(date(2025, 1, 20)) is True  # 終了日
        assert date_range.contains(date(2025, 1, 9)) is False
        assert date_range.contains(date(2025, 1, 21)) is False

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-DAYS")
    def test_days(self) -> None:
        """期間の日数計算"""
        # Given
        date_range = DateRange(date(2025, 1, 1), date(2025, 1, 10))

        # When
        days = date_range.days()

        # Then
        assert days == 10  # 両端を含む

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-WEEKS")
    def test_weeks(self) -> None:
        """期間の週数計算"""
        # Given
        date_range = DateRange(date(2025, 1, 1), date(2025, 1, 14))

        # When
        weeks = date_range.weeks()

        # Then
        assert weeks == 2  # 14日 = 2週間

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-LAST_N_DAYS")
    def test_last_n_days(self) -> None:
        """過去n日間の範囲作成"""
        # Given - project_now()をmockして安定したテストにする
        from unittest.mock import patch

        with patch("noveler.domain.analysis.value_objects.project_now") as mock_project_now:
            # 固定日付を設定
            mock_time = Mock()
            mock_time.datetime.date.return_value = date(2025, 8, 3)
            mock_project_now.return_value = mock_time

            # When
            date_range = DateRange.last_n_days(7)

            # Then
            expected_end = date(2025, 8, 3)
            expected_start = expected_end - timedelta(days=6)
            assert date_range.end_date == expected_end
            assert date_range.start_date == expected_start
            assert date_range.days() == 7

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-LAST_WEEK")
    def test_last_week(self) -> None:
        """先週の範囲作成"""
        # Given - project_now()をmockして安定したテストにする
        from unittest.mock import patch

        with patch("noveler.domain.analysis.value_objects.project_now") as mock_project_now:
            # 固定日付を設定(2025年8月3日は日曜日)
            mock_time = Mock()
            mock_time.datetime.date.return_value = date(2025, 8, 3)
            mock_project_now.return_value = mock_time

            # When
            date_range = DateRange.last_week()

            # Then
            # 先週月曜日から日曜日まで(7月21日-7月27日)
            expected_start = date(2025, 7, 21)  # 月曜日
            expected_end = date(2025, 7, 27)  # 日曜日

            assert date_range.start_date == expected_start
            assert date_range.end_date == expected_end
            assert date_range.days() == 7
            assert date_range.start_date.weekday() == 0  # 月曜日
            assert date_range.end_date.weekday() == 6  # 日曜日  # 日曜日

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-LAST_MONTH")
    def test_last_month(self) -> None:
        """先月の範囲作成"""
        # Given - project_now()をmockして安定したテストにする
        from unittest.mock import patch

        with patch("noveler.domain.analysis.value_objects.project_now") as mock_project_now:
            # 固定日付を設定(2025年8月3日)
            mock_time = Mock()
            mock_time.datetime.date.return_value = date(2025, 8, 3)
            mock_project_now.return_value = mock_time

            # When
            date_range = DateRange.last_month()

            # Then
            # 先月(7月)の範囲
            expected_start = date(2025, 7, 1)  # 7月1日
            expected_end = date(2025, 7, 31)  # 7月31日

            assert date_range.start_date == expected_start
            assert date_range.end_date == expected_end
            assert date_range.start_date.day == 1
            assert (date_range.end_date + timedelta(days=1)).day == 1


class TestNarouCode:
    """NarouCode値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-CREATE_VALID_NAROU_C")
    def test_create_valid_narou_code(self) -> None:
        """有効ななろうコードの作成"""
        # When
        code = NarouCode("n1234567890")

        # Then
        assert code.value == "n1234567890"

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-CREATE_VALID_NAROU_C")
    def test_create_valid_narou_code_with_suffix(self) -> None:
        """サフィックス付きの有効ななろうコードの作成"""
        # When
        code = NarouCode("n1234567890a")

        # Then
        assert code.value == "n1234567890a"

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-IMMUTABILITY")
    def test_immutability(self) -> None:
        """不変性の確認"""
        # Given
        code = NarouCode("n1234567890")

        # When & Then
        with pytest.raises(AttributeError, match=".*"):
            code.value = "n0987654321"

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-EMPTY_CODE")
    def test_empty_code(self) -> None:
        """空のコードでエラー"""
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            NarouCode("")
        assert "なろうコードは必須です" in str(exc_info.value)

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-INVALID_FORMAT_NO_PR")
    def test_invalid_format_no_prefix(self) -> None:
        """プレフィックスなしの無効な形式"""
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            NarouCode("1234567890")
        assert "無効ななろうコード形式です" in str(exc_info.value)

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-INVALID_FORMAT_WRONG")
    def test_invalid_format_wrong_length(self) -> None:
        """長さが違う無効な形式"""
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            NarouCode("n123456789")  # 9桁(10桁必要)
        assert "無効ななろうコード形式です" in str(exc_info.value)

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-INVALID_FORMAT_WRONG")
    def test_invalid_format_wrong_suffix(self) -> None:
        """無効なサフィックス"""
        # When & Then
        with pytest.raises(ValueError) as exc_info:
            NarouCode("n1234567890A")  # 大文字
        assert "無効ななろうコード形式です" in str(exc_info.value)

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-GET_KASASAGI_URL")
    def test_get_kasasagi_url(self) -> None:
        """KASASAGI APIのURL生成"""
        # Given
        code = NarouCode("n1234567890")

        # When
        url = code.get_kasasagi_url()

        # Then
        assert url == "https://kasasagi.hinaproject.com/access/top/ncode/n1234567890/"

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-STR_REPRESENTATION")
    def test_str_representation(self) -> None:
        """文字列表現"""
        # Given
        code = NarouCode("n1234567890")

        # When
        str_rep = str(code)

        # Then
        assert str_rep == "n1234567890"


class TestAnalysisTimestamp:
    """AnalysisTimestamp値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-CREATE_ANALYSIS_TIME")
    def test_create_analysis_timestamp(self) -> None:
        """分析タイムスタンプの作成"""
        # Given
        now = project_now().datetime

        # When
        timestamp = AnalysisTimestamp(now)

        # Then
        assert timestamp.value == now

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-IMMUTABILITY")
    def test_immutability(self) -> None:
        """不変性の確認"""
        # Given
        timestamp = AnalysisTimestamp(project_now().datetime)

        # When & Then
        with pytest.raises(AttributeError, match=".*"):
            timestamp.value = project_now().datetime

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-IS_RECENT_TRUE")
    def test_is_recent_true(self) -> None:
        """最近の分析かチェック(True)"""
        # Given
        recent = project_now().datetime - timedelta(hours=12)
        timestamp = AnalysisTimestamp(recent)

        # When & Then
        assert timestamp.is_recent(hours=24) is True

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-IS_RECENT_FALSE")
    def test_is_recent_false(self) -> None:
        """最近の分析かチェック(False)"""
        # Given
        old = project_now().datetime - timedelta(hours=25)
        timestamp = AnalysisTimestamp(old)

        # When & Then
        assert timestamp.is_recent(hours=24) is False

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-IS_RECENT_BOUNDARY")
    def test_is_recent_boundary(self) -> None:
        """最近の分析かチェック(境界値)"""
        # Given
        exactly_24h = project_now().datetime - timedelta(hours=24, seconds=1)
        timestamp = AnalysisTimestamp(exactly_24h)

        # When & Then
        assert timestamp.is_recent(hours=24) is False

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-TIME_SINCE")
    def test_time_since(self) -> None:
        """分析からの経過時間"""
        # Given
        past = project_now().datetime - timedelta(hours=3, minutes=30)
        timestamp = AnalysisTimestamp(past)

        # When
        elapsed = timestamp.time_since()

        # Then
        assert isinstance(elapsed, timedelta)
        # 約3時間30分(誤差を考慮)
        assert 3.4 < elapsed.total_seconds() / 3600 < 3.6

    @pytest.mark.spec("SPEC-ANALYSIS_VALUE_OBJECTS-STR_REPRESENTATION")
    def test_str_representation(self) -> None:
        """文字列表現"""
        # Given
        dt = datetime(2025, 1, 15, 14, 30, 45, tzinfo=timezone.utc)
        timestamp = AnalysisTimestamp(dt)

        # When
        str_rep = str(timestamp)

        # Then
        assert str_rep == "2025-01-15 14:30:45"
