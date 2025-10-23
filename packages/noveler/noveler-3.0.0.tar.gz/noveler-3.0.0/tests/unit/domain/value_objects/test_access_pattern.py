#!/usr/bin/env python3
"""AccessPattern値オブジェクトのユニットテスト

SPEC-ANALYSIS-001に基づくTDD実装
"""

from datetime import date, datetime, timezone

import pytest

from noveler.domain.value_objects.access_pattern import AccessPattern

pytestmark = pytest.mark.vo_smoke



class TestAccessPattern:
    """AccessPattern値オブジェクトのテストクラス"""

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_create_valid_access_pattern(self) -> None:
        """正常なAccessPatternの作成テスト"""
        # Given: 正常なアクセスデータ
        pv = 1000
        ua = 800
        episode_number = 1
        measurement_date = datetime.now(timezone.utc).date()

        # When: AccessPatternを作成
        pattern = AccessPattern(pv=pv, ua=ua, episode_number=episode_number, measurement_date=measurement_date)

        # Then: 正しく作成される
        assert pattern.pv == pv
        assert pattern.ua == ua
        assert pattern.episode_number == episode_number
        assert pattern.measurement_date == measurement_date

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_calculate_pv_per_ua_normal_case(self) -> None:
        """正常なPV/UA計算テスト"""
        # Given: UAが0でないAccessPattern
        pattern = AccessPattern(pv=1000, ua=800, episode_number=1, measurement_date=datetime.now(timezone.utc).date())

        # When: PV/UAを計算
        result = pattern.calculate_pv_per_ua()

        # Then: 正しい比率が返される
        assert result == 1.25  # 1000 / 800

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_calculate_pv_per_ua_zero_ua(self) -> None:
        """UA=0の場合のPV/UA計算テスト"""
        # Given: UA=0のAccessPattern
        pattern = AccessPattern(pv=1000, ua=0, episode_number=1, measurement_date=datetime.now(timezone.utc).date())

        # When: PV/UAを計算
        result = pattern.calculate_pv_per_ua()

        # Then: 0.0が返される(ゼロ除算回避)
        assert result == 0.0

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_is_valid_data_with_valid_pattern(self) -> None:
        """有効データの判定テスト"""
        # Given: 有効なAccessPattern
        pattern = AccessPattern(pv=1000, ua=800, episode_number=1, measurement_date=datetime.now(timezone.utc).date())

        # When: データ有効性を確認
        result = pattern.is_valid_data()

        # Then: Trueが返される
        assert result is True

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_is_valid_data_with_zero_pv(self) -> None:
        """PV=0の場合の無効データ判定テスト"""
        # Given: PV=0のAccessPattern
        pattern = AccessPattern(pv=0, ua=800, episode_number=1, measurement_date=datetime.now(timezone.utc).date())

        # When: データ有効性を確認
        result = pattern.is_valid_data()

        # Then: Falseが返される
        assert result is False

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_is_valid_data_with_negative_values(self) -> None:
        """負の値の場合の無効データ判定テスト"""
        # Given: 負の値を含むAccessPattern
        pattern = AccessPattern(pv=-100, ua=800, episode_number=1, measurement_date=datetime.now(timezone.utc).date())

        # When: データ有効性を確認
        result = pattern.is_valid_data()

        # Then: Falseが返される
        assert result is False

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_is_valid_data_with_invalid_episode_number(self) -> None:
        """無効なエピソード番号の場合の判定テスト"""
        # Given: 無効なエピソード番号のAccessPattern
        pattern = AccessPattern(pv=1000, ua=800, episode_number=0, measurement_date=datetime.now(timezone.utc).date())

        # When: データ有効性を確認
        result = pattern.is_valid_data()

        # Then: Falseが返される
        assert result is False

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_access_pattern_immutability(self) -> None:
        """AccessPatternの不変性テスト"""
        # Given: AccessPattern
        pattern = AccessPattern(pv=1000, ua=800, episode_number=1, measurement_date=datetime.now(timezone.utc).date())

        # When/Then: 属性変更を試行するとエラーが発生
        with pytest.raises(AttributeError, match=".*"):
            pattern.pv = 2000

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_access_pattern_equality(self) -> None:
        """AccessPatternの等価性テスト"""
        # Given: 同じ値を持つ2つのAccessPattern
        pattern1 = AccessPattern(pv=1000, ua=800, episode_number=1, measurement_date=date(2025, 7, 24))
        pattern2 = AccessPattern(pv=1000, ua=800, episode_number=1, measurement_date=date(2025, 7, 24))

        # When/Then: 等価である
        assert pattern1 == pattern2
        assert hash(pattern1) == hash(pattern2)

    @pytest.mark.spec("SPEC-ANALYSIS-001")
    def test_access_pattern_inequality(self) -> None:
        """AccessPatternの非等価性テスト"""
        # Given: 異なる値を持つ2つのAccessPattern
        pattern1 = AccessPattern(pv=1000, ua=800, episode_number=1, measurement_date=datetime.now(timezone.utc).date())
        pattern2 = AccessPattern(pv=2000, ua=800, episode_number=1, measurement_date=datetime.now(timezone.utc).date())

        # When/Then: 等価でない
        assert pattern1 != pattern2
        assert hash(pattern1) != hash(pattern2)
