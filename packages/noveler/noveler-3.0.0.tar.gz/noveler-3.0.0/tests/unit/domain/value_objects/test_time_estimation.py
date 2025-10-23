#!/usr/bin/env python3
"""時間見積もり値オブジェクトのテスト

TDD原則に基づく単体テスト


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.time_estimation import TimeEstimation

pytestmark = pytest.mark.vo_smoke



class TestTimeEstimation:
    """TimeEstimation値オブジェクトのテスト"""

    def test_from_minutes_valid_values(self) -> None:
        """分単位での作成 - 有効な値"""
        # 境界値テスト
        time_0 = TimeEstimation.from_minutes(0)
        assert time_0.minutes == 0

        time_60 = TimeEstimation.from_minutes(60)
        assert time_60.minutes == 60

        time_1440 = TimeEstimation.from_minutes(1440)  # 24時間
        assert time_1440.minutes == 1440

    def test_from_minutes_invalid_values(self) -> None:
        """分単位での作成 - 無効な値"""
        # 負の値
        with pytest.raises(DomainException, match="時間見積もりは0分以上である必要があります"):
            TimeEstimation.from_minutes(-1)

        # 24時間超過
        with pytest.raises(DomainException, match="時間見積もりは24時間以下である必要があります"):
            TimeEstimation.from_minutes(1441)

    def test_from_hours_valid_values(self) -> None:
        """時間単位での作成 - 有効な値"""
        # 整数時間
        time_1h = TimeEstimation.from_hours(1)
        assert time_1h.minutes == 60

        time_2h = TimeEstimation.from_hours(2)
        assert time_2h.minutes == 120

        # 小数時間
        time_half = TimeEstimation.from_hours(0.5)
        assert time_half.minutes == 30

        time_quarter = TimeEstimation.from_hours(0.25)
        assert time_quarter.minutes == 15

    def test_from_hours_boundary_values(self) -> None:
        """時間単位での作成 - 境界値"""
        # 0時間
        time_0 = TimeEstimation.from_hours(0)
        assert time_0.minutes == 0

        # 24時間
        time_24 = TimeEstimation.from_hours(24)
        assert time_24.minutes == 1440

    def test_from_hours_invalid_values(self) -> None:
        """時間単位での作成 - 無効な値"""
        # 負の値
        with pytest.raises(DomainException, match=".*"):
            TimeEstimation.from_hours(-1)

        # 24時間超過
        with pytest.raises(DomainException, match=".*"):
            TimeEstimation.from_hours(25)

    def test_in_minutes(self) -> None:
        """分単位での取得"""
        time = TimeEstimation.from_minutes(90)
        assert time.in_minutes() == 90

    def test_in_hours(self) -> None:
        """時間単位での取得"""
        # 整数時間
        time_60 = TimeEstimation.from_minutes(60)
        assert time_60.in_hours() == 1.0

        # 小数時間
        time_90 = TimeEstimation.from_minutes(90)
        assert time_90.in_hours() == 1.5

        # 30分
        time_30 = TimeEstimation.from_minutes(30)
        assert time_30.in_hours() == 0.5

    def test_display_text_minutes_only(self) -> None:
        """表示テキスト - 分のみ"""
        time_30 = TimeEstimation.from_minutes(30)
        assert time_30.display_text() == "30分"

        time_59 = TimeEstimation.from_minutes(59)
        assert time_59.display_text() == "59分"

    def test_display_text_hours_only(self) -> None:
        """表示テキスト - 時間のみ"""
        time_60 = TimeEstimation.from_minutes(60)
        assert time_60.display_text() == "1時間"

        time_120 = TimeEstimation.from_minutes(120)
        assert time_120.display_text() == "2時間"

    def test_display_text_hours_and_minutes(self) -> None:
        """表示テキスト - 時間と分"""
        time_90 = TimeEstimation.from_minutes(90)
        assert time_90.display_text() == "1時間30分"

        time_125 = TimeEstimation.from_minutes(125)
        assert time_125.display_text() == "2時間5分"

    def test_display_text_zero_minutes(self) -> None:
        """表示テキスト - 0分"""
        time_0 = TimeEstimation.from_minutes(0)
        assert time_0.display_text() == "0分"

    def test_addition(self) -> None:
        """時間見積もりの加算"""
        time_30 = TimeEstimation.from_minutes(30)
        time_45 = TimeEstimation.from_minutes(45)

        result = time_30 + time_45
        assert result.minutes == 75
        assert result.display_text() == "1時間15分"

    def test_addition_boundary_check(self) -> None:
        """加算での境界値チェック"""
        time_720 = TimeEstimation.from_minutes(720)  # 12時間
        time_719 = TimeEstimation.from_minutes(719)  # 11時間59分

        # 境界値内での加算
        result = time_720 + time_719
        assert result.minutes == 1439  # 23時間59分

        # 境界値を超える加算
        time_1 = TimeEstimation.from_minutes(1)
        with pytest.raises(DomainException, match=".*"):
            time_720 + time_720 + time_1

    def test_multiplication(self) -> None:
        """時間見積もりの倍数"""
        time_30 = TimeEstimation.from_minutes(30)

        # 2倍
        result_2 = time_30 * 2
        assert result_2.minutes == 60
        assert result_2.display_text() == "1時間"

        # 3倍
        result_3 = time_30 * 3
        assert result_3.minutes == 90
        assert result_3.display_text() == "1時間30分"

    def test_multiplication_boundary_check(self) -> None:
        """倍数での境界値チェック"""
        time_720 = TimeEstimation.from_minutes(720)  # 12時間

        # 境界値内での倍数
        result = time_720 * 2
        assert result.minutes == 1440  # 24時間

        # 境界値を超える倍数
        with pytest.raises(DomainException, match=".*"):
            time_720 * 3

    def test_immutability(self) -> None:
        """不変性のテスト"""
        original = TimeEstimation.from_minutes(60)

        # 加算は新しいオブジェクトを返す
        time_30 = TimeEstimation.from_minutes(30)
        result = original + time_30

        assert original.minutes == 60  # 元のオブジェクトは変更されない
        assert result.minutes == 90  # 新しいオブジェクトが返される
        assert original is not result  # 異なるオブジェクト

    def test_equality(self) -> None:
        """等価性のテスト"""
        time_60_a = TimeEstimation.from_minutes(60)
        time_60_b = TimeEstimation.from_minutes(60)
        time_90 = TimeEstimation.from_minutes(90)

        # 同じ値は等価
        assert time_60_a == time_60_b

        # 異なる値は非等価
        assert time_60_a != time_90

    def test_complex_operations(self) -> None:
        """複合操作のテスト"""
        # 現実的なシナリオ: タスクの時間見積もり
        task_a = TimeEstimation.from_minutes(45)  # 45分
        task_b = TimeEstimation.from_hours(1.5)  # 1時間30分
        task_c = TimeEstimation.from_minutes(30)  # 30分

        # 総見積もり時間
        total = task_a + task_b + task_c
        assert total.minutes == 45 + 90 + 30
        assert total.display_text() == "2時間45分"

        # タスクAを3回実行する見積もり
        task_a_triple = task_a * 3
        assert task_a_triple.minutes == 135
        assert task_a_triple.display_text() == "2時間15分"
