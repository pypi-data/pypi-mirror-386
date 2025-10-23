#!/usr/bin/env python3
"""強化版執筆時間値オブジェクトのテスト

Design by Contractと不変性を組み合わせたテスト


仕様書: SPEC-UNIT-TEST
"""

from datetime import datetime

import pytest

from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.writing.value_objects.enhanced_writing_duration import EnhancedWritingDuration

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestEnhancedWritingDuration:
    """強化版執筆時間のテストスイート"""

    @pytest.mark.spec("SPEC-ENHANCED_WRITING_DURATION-VALID_DURATION_CREAT")
    def test_valid_duration_creation(self) -> None:
        """正常な執筆時間作成"""
        start = datetime(2024, 1, 1, 10, 0, tzinfo=JST)
        end = datetime(2024, 1, 1, 12, 30, tzinfo=JST)

        duration = EnhancedWritingDuration(start, end)

        assert duration.start_time == start
        assert duration.end_time == end
        assert duration.minutes == 150
        assert duration.hours == 2.5
        assert str(duration) == "2時間30分"

    @pytest.mark.spec("SPEC-ENHANCED_WRITING_DURATION-ZERO_DURATION")
    def test_zero_duration(self) -> None:
        """ゼロ時間の執筆"""
        start = datetime(2024, 1, 1, 10, 0, tzinfo=JST)
        end = start

        duration = EnhancedWritingDuration(start, end)

        assert duration.minutes == 0
        assert duration.hours == 0.0
        assert str(duration) == "0分"

    @pytest.mark.spec("SPEC-ENHANCED_WRITING_DURATION-START_AFTER_END_CONT")
    def test_start_after_end_contract_violation(self) -> None:
        """開始時刻が終了時刻より後の契約違反"""
        start = datetime(2024, 1, 1, 12, 0, tzinfo=JST)
        end = datetime(2024, 1, 1, 10, 0, tzinfo=JST)

        with pytest.raises(DomainException, match=".*"):
            EnhancedWritingDuration(start, end)

    @pytest.mark.spec("SPEC-ENHANCED_WRITING_DURATION-EXCEEDS_MAX_DURATION")
    def test_exceeds_max_duration_contract_violation(self) -> None:
        """24時間制限の契約違反"""
        start = datetime(2024, 1, 1, 0, 0, tzinfo=JST)
        end = datetime(2024, 1, 2, 1, 0, tzinfo=JST)  # 25時間後

        with pytest.raises(DomainException, match=".*"):
            EnhancedWritingDuration(start, end)

    @pytest.mark.spec("SPEC-ENHANCED_WRITING_DURATION-DURATION_ADDITION")
    def test_duration_addition(self) -> None:
        """執筆時間の加算"""
        duration1 = EnhancedWritingDuration(
            datetime(2024, 1, 1, 10, 0, tzinfo=JST), datetime(2024, 1, 1, 12, 0, tzinfo=JST)
        )
        duration2 = EnhancedWritingDuration(
            datetime(2024, 1, 1, 14, 0, tzinfo=JST), datetime(2024, 1, 1, 16, 30, tzinfo=JST)
        )

        total = duration1 + duration2

        # 合計時間は4時間30分
        assert total.minutes == 270
        assert total.hours == 4.5

    @pytest.mark.spec("SPEC-ENHANCED_WRITING_DURATION-ADDITION_EXCEEDS_MAX")
    def test_addition_exceeds_max_duration(self) -> None:
        """加算で24時間制限を超える"""
        duration1 = EnhancedWritingDuration(
            datetime(2024, 1, 1, 0, 0, tzinfo=JST),
            datetime(2024, 1, 1, 15, 0, tzinfo=JST),  # 15時間
        )
        duration2 = EnhancedWritingDuration(
            datetime(2024, 1, 2, 0, 0, tzinfo=JST),
            datetime(2024, 1, 2, 10, 0, tzinfo=JST),  # 10時間
        )

        with pytest.raises(DomainException, match=".*"):
            duration1 + duration2

    @pytest.mark.spec("SPEC-ENHANCED_WRITING_DURATION-IS_PRODUCTIVE")
    def test_is_productive(self) -> None:
        """生産的セッションの判定"""
        # 45分のセッション
        productive = EnhancedWritingDuration(
            datetime(2024, 1, 1, 10, 0, tzinfo=JST), datetime(2024, 1, 1, 10, 45, tzinfo=JST)
        )

        # 15分のセッション
        short = EnhancedWritingDuration(
            datetime(2024, 1, 1, 10, 0, tzinfo=JST), datetime(2024, 1, 1, 10, 15, tzinfo=JST)
        )

        assert productive.is_productive(30) is True
        assert short.is_productive(30) is False
        assert short.is_productive(10) is True

    @pytest.mark.spec("SPEC-ENHANCED_WRITING_DURATION-IS_MARATHON_SESSION")
    def test_is_marathon_session(self) -> None:
        """長時間セッションの判定"""
        # 5時間のセッション
        marathon = EnhancedWritingDuration(
            datetime(2024, 1, 1, 10, 0, tzinfo=JST), datetime(2024, 1, 1, 15, 0, tzinfo=JST)
        )

        # 2時間のセッション
        normal = EnhancedWritingDuration(
            datetime(2024, 1, 1, 10, 0, tzinfo=JST), datetime(2024, 1, 1, 12, 0, tzinfo=JST)
        )

        assert marathon.is_marathon_session(4.0) is True
        assert normal.is_marathon_session(4.0) is False
        assert normal.is_marathon_session(2.0) is True

    @pytest.mark.spec("SPEC-ENHANCED_WRITING_DURATION-IMMUTABILITY")
    def test_immutability(self) -> None:
        """不変性のテスト"""
        duration = EnhancedWritingDuration(
            datetime(2024, 1, 1, 10, 0, tzinfo=JST), datetime(2024, 1, 1, 12, 0, tzinfo=JST)
        )

        # 直接の属性変更は不可
        with pytest.raises(AttributeError, match=".*"):
            duration.start_time = datetime(2024, 1, 1, 11, 0, tzinfo=JST)

        with pytest.raises(AttributeError, match=".*"):
            duration.end_time = datetime(2024, 1, 1, 13, 0, tzinfo=JST)

    @pytest.mark.spec("SPEC-ENHANCED_WRITING_DURATION-TYPE_SAFETY_CONTRACT")
    def test_type_safety_contracts(self) -> None:
        """型安全性の契約"""
        # 文字列は事前条件違反
        with pytest.raises(DomainException, match=".*"):
            EnhancedWritingDuration("2024-01-01", project_now().datetime)  # type: ignore

        with pytest.raises(DomainException, match=".*"):
            EnhancedWritingDuration(project_now().datetime, "2024-01-01")  # type: ignore

    @pytest.mark.spec("SPEC-ENHANCED_WRITING_DURATION-INVARIANT_CONDITIONS")
    def test_invariant_conditions(self) -> None:
        """不変条件のテスト"""
        # 正常なインスタンス作成後、不変条件は常に満たされる
        duration = EnhancedWritingDuration(
            datetime(2024, 1, 1, 10, 0, tzinfo=JST), datetime(2024, 1, 1, 12, 0, tzinfo=JST)
        )

        # どのメソッドを呼んでも不変条件は保持される
        assert duration.duration.total_seconds() >= 0
        assert duration.hours <= 24

        # 加算後も不変条件は保持
        duration2 = EnhancedWritingDuration(
            datetime(2024, 1, 1, 14, 0, tzinfo=JST), datetime(2024, 1, 1, 15, 0, tzinfo=JST)
        )

        result = duration + duration2
        assert result.duration.total_seconds() >= 0
        assert result.hours <= 24
