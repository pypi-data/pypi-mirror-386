"""WordCount値オブジェクトの不変条件テスト
TDD: RED Phase - 失敗するテストから開始


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.exceptions import DomainException
from noveler.domain.writing.value_objects.word_count import WordCount

pytestmark = pytest.mark.vo_smoke



class TestWordCountInvariants:
    """WordCount値オブジェクトの不変条件テスト"""

    def test_valid_word_count_creation(self) -> None:
        """有効な文字数でWordCountを作成できる"""
        count = WordCount(1000)
        assert count.value == 1000

    def test_zero_word_count_is_valid(self) -> None:
        """文字数0は有効(空の原稿)"""
        count = WordCount(0)
        assert count.value == 0

    def test_negative_word_count_raises_error(self) -> None:
        """負の文字数はエラーになる"""
        with pytest.raises(DomainException, match="文字数は0以上である必要があります"):
            WordCount(-1)

    def test_word_count_max_limit(self) -> None:
        """文字数の上限(100万文字)を超えるとエラーになる"""
        # 小説プラットフォームでの現実的な上限
        with pytest.raises(DomainException, match="文字数は1000000以下である必要があります"):
            WordCount(1000001)

    def test_word_count_immutability(self) -> None:
        """WordCountは不変である"""
        count = WordCount(1000)
        with pytest.raises(AttributeError, match=".*"):
            count.value = 2000

    def test_word_count_addition(self) -> None:
        """文字数の加算が正しく動作する"""
        count1 = WordCount(1000)
        count2 = WordCount(2000)
        result = count1 + count2
        assert result.value == 3000
        assert isinstance(result, WordCount)

    def test_word_count_addition_respects_limit(self) -> None:
        """加算結果も上限を守る"""
        count1 = WordCount(600000)
        count2 = WordCount(500000)
        with pytest.raises(DomainException, match="文字数は1000000以下である必要があります"):
            count1 + count2

    def test_word_count_subtraction(self) -> None:
        """文字数の減算が正しく動作する"""
        count1 = WordCount(3000)
        count2 = WordCount(1000)
        result = count1 - count2
        assert result.value == 2000

    def test_word_count_subtraction_prevents_negative(self) -> None:
        """減算で負にならない"""
        count1 = WordCount(1000)
        count2 = WordCount(2000)
        with pytest.raises(DomainException, match="文字数は0以上である必要があります"):
            count1 - count2

    def test_word_count_comparison(self) -> None:
        """文字数の比較が正しく動作する"""
        count1 = WordCount(1000)
        count2 = WordCount(2000)
        count3 = WordCount(1000)

        assert count1 < count2
        assert count2 > count1
        assert count1 == count3
        assert count1 <= count3
        assert count2 >= count1

    def test_word_count_episode_categorization(self) -> None:
        """話のカテゴリ分けが正しく動作する"""
        short_story = WordCount(500)  # ショートショート
        normal_story = WordCount(3000)  # 通常話
        long_story = WordCount(10000)  # 長編話

        assert short_story.is_short_story()
        assert normal_story.is_normal_story()
        assert long_story.is_long_story()

    def test_word_count_format(self) -> None:
        """文字数の表示フォーマット"""
        test_cases = [
            (0, "0文字"),
            (100, "100文字"),
            (1000, "1,000文字"),
            (10000, "10,000文字"),
            (100000, "100,000文字"),
        ]
        for value, expected in test_cases:
            count = WordCount(value)
            assert str(count) == expected
            assert count.format() == expected
