#!/usr/bin/env python3
"""WordCount値オブジェクトのユニットテスト

TDD原則に従い、文字数管理のビジネスロジックをテスト
"""

import pytest

from noveler.domain.value_objects.word_count import MAX_WORD_COUNT, MIN_WORD_COUNT_FOR_EPISODE, WordCount

pytestmark = pytest.mark.vo_smoke



class TestWordCount:
    """WordCountのテスト"""

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_create_valid_word_count(self) -> None:
        """有効な文字数の作成"""
        # When
        word_count = WordCount(1000)

        # Then
        assert word_count.value == 1000

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_create_zero_word_count(self) -> None:
        """ゼロ文字数の作成"""
        # When
        word_count = WordCount(0)

        # Then
        assert word_count.value == 0

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_create_max_word_count(self) -> None:
        """最大文字数の作成"""
        # When
        word_count = WordCount(MAX_WORD_COUNT)

        # Then
        assert word_count.value == MAX_WORD_COUNT

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_create_negative_word_count(self) -> None:
        """負の文字数はエラー"""
        # When/Then
        with pytest.raises(ValueError, match="文字数は0以上である必要があります"):
            WordCount(-1)

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_create_over_max_word_count(self) -> None:
        """最大値を超える文字数はエラー"""
        # When/Then
        with pytest.raises(ValueError, match=f"文字数は{MAX_WORD_COUNT}以下である必要があります"):
            WordCount(MAX_WORD_COUNT + 1)

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_create_non_integer_word_count(self) -> None:
        """整数以外の型はエラー"""
        # When/Then
        with pytest.raises(TypeError, match=".*"):
            WordCount("1000")  # 文字列を渡すとエラー

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_calculate_percentage_normal(self) -> None:
        """通常の達成率計算"""
        # Given
        current = WordCount(750)
        target = WordCount(1000)

        # When
        percentage = current.calculate_percentage(target)

        # Then
        assert percentage == 75.0

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_calculate_percentage_over_100(self) -> None:
        """100%を超える達成率"""
        # Given
        current = WordCount(1200)
        target = WordCount(1000)

        # When
        percentage = current.calculate_percentage(target)

        # Then
        assert percentage == 120.0

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_calculate_percentage_zero_target(self) -> None:
        """目標が0の場合の達成率"""
        # Given
        current = WordCount(500)
        target = WordCount(0)

        # When
        percentage = current.calculate_percentage(target)

        # Then
        assert percentage == 100.0

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_is_sufficient_for_episode_true(self) -> None:
        """エピソードとして十分な文字数"""
        # Given
        wc = WordCount(MIN_WORD_COUNT_FOR_EPISODE)

        # When/Then
        assert wc.is_sufficient_for_episode() is True

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_is_sufficient_for_episode_above_minimum(self) -> None:
        """最小値を超える文字数"""
        # Given
        wc = WordCount(MIN_WORD_COUNT_FOR_EPISODE + 500)

        # When/Then
        assert wc.is_sufficient_for_episode() is True

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_is_sufficient_for_episode_false(self) -> None:
        """エピソードとして不十分な文字数"""
        # Given
        wc = WordCount(MIN_WORD_COUNT_FOR_EPISODE - 1)

        # When/Then
        assert wc.is_sufficient_for_episode() is False

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_is_sufficient_for_episode_zero(self) -> None:
        """ゼロ文字の場合"""
        # Given
        wc = WordCount(0)

        # When/Then
        assert wc.is_sufficient_for_episode() is False

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_class_constants(self) -> None:
        """クラス定数の確認"""
        # Then
        assert WordCount.MAX_WORD_COUNT == MAX_WORD_COUNT
        assert WordCount.MIN_WORD_COUNT_FOR_EPISODE == MIN_WORD_COUNT_FOR_EPISODE

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_immutability(self) -> None:
        """不変性の確認"""
        # Given
        wc = WordCount(1000)

        # When/Then
        with pytest.raises(AttributeError, match=".*"):
            wc.value = 2000

    @pytest.mark.spec("SPEC-EPISODE-010")
    def test_edge_case_boundary_values(self) -> None:
        """境界値のテスト"""
        # 最小値
        wc_min = WordCount(0)
        assert wc_min.value == 0

        # 最大値
        wc_max = WordCount(MAX_WORD_COUNT)
        assert wc_max.value == MAX_WORD_COUNT

        # エピソード最小値の境界
        wc_episode_min = WordCount(MIN_WORD_COUNT_FOR_EPISODE)
        assert wc_episode_min.is_sufficient_for_episode() is True

        wc_below_episode = WordCount(MIN_WORD_COUNT_FOR_EPISODE - 1)
        assert wc_below_episode.is_sufficient_for_episode() is False
