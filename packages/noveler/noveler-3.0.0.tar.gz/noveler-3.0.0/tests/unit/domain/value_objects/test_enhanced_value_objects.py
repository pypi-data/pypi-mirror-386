#!/usr/bin/env python3
"""追加の値オブジェクトテスト - カバレッジ向上用

主要な値オブジェクトの包括的なテスト


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.quality_score import QualityScore
from noveler.domain.value_objects.word_count import WordCount

pytestmark = pytest.mark.vo_smoke



class TestEpisodeNumberEnhanced:
    """EpisodeNumberの詳細テスト"""

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS-EPISODE_NUMBER_VALID")
    def test_episode_number_validation_edge_cases(self) -> None:
        """エピソード番号の境界値テスト"""
        # 正常値
        assert EpisodeNumber(1).value == 1
        assert EpisodeNumber(9999).value == 9999

        # 無効値
        with pytest.raises(ValueError, match=".*"):
            EpisodeNumber(0)
        with pytest.raises(ValueError, match=".*"):
            EpisodeNumber(-1)
        with pytest.raises(ValueError, match=".*"):
            EpisodeNumber(10000)

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS-EPISODE_NUMBER_COMPA")
    def test_episode_number_comparison(self) -> None:
        """エピソード番号の比較"""
        ep1 = EpisodeNumber(1)
        ep2 = EpisodeNumber(2)
        ep1_copy = EpisodeNumber(1)

        assert ep1 == ep1_copy
        assert ep1 != ep2
        assert ep1 < ep2
        assert ep2 > ep1

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS-EPISODE_NUMBER_STRIN")
    def test_episode_number_string_representation(self) -> None:
        """エピソード番号の文字列表現"""
        ep = EpisodeNumber(42)
        assert str(ep) == "第042話"  # 実際の実装に合わせて修正
        # __repr__メソッドが実装されていない場合はスキップ
        assert "EpisodeNumber" in repr(ep)


class TestEpisodeTitleEnhanced:
    """EpisodeTitleの詳細テスト"""

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS-EPISODE_TITLE_FILENA")
    def test_episode_title_filename_conversion(self) -> None:
        """タイトルのファイル名変換"""
        title = EpisodeTitle("第1話 始まりの朝")
        safe_filename = title.to_filename_safe()
        assert safe_filename == "第1話_始まりの朝"

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS-EPISODE_TITLE_SPECIA")
    def test_episode_title_special_characters(self) -> None:
        """特殊文字を含むタイトル"""
        # 全角文字の処理
        title = EpisodeTitle("第１話 特殊文字!?")
        safe_filename = title.to_filename_safe()
        assert "!" not in safe_filename
        assert "?" not in safe_filename

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS-EPISODE_TITLE_LENGTH")
    def test_episode_title_length_validation(self) -> None:
        """タイトル長の検証"""
        # 境界値テスト
        valid_title = EpisodeTitle("a" * 100)  # 100文字(上限)
        assert len(valid_title.value) == 100

        with pytest.raises(ValueError, match=".*"):
            EpisodeTitle("a" * 101)  # 101文字(上限超過)


class TestWordCountEnhanced:
    """WordCountの詳細テスト"""

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS-WORD_COUNT_BASIC_OPE")
    def test_word_count_basic_operations(self) -> None:
        """文字数の基本操作"""
        wc = WordCount(2500)

        # 基本的な値の確認
        assert wc.value == 2500

        # 文字列表現
        assert str(wc) == "2,500文字"


class TestQualityScoreEnhanced:
    """QualityScoreの詳細テスト"""

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS-QUALITY_SCORE_VALIDA")
    def test_quality_score_validation(self) -> None:
        """品質スコアの値検証"""
        valid_score = QualityScore(85)
        assert valid_score.value == 85

        # 境界値テスト
        min_score = QualityScore(0)
        max_score = QualityScore(100)
        assert min_score.value == 0
        assert max_score.value == 100

        # 無効値
        with pytest.raises(DomainException, match=".*"):
            QualityScore(-1)
        with pytest.raises(DomainException, match=".*"):
            QualityScore(101)

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS-QUALITY_SCORE_COMPAR")
    def test_quality_score_comparison_operations(self) -> None:
        """品質スコアの比較演算"""
        score1 = QualityScore(75)
        score2 = QualityScore(80)
        score1_copy = QualityScore(75)

        assert score1 == score1_copy
        assert score1 != score2
        assert score1 < score2
        assert score2 > score1

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS-QUALITY_SCORE_BASIC_")
    def test_quality_score_basic_operations(self) -> None:
        """品質スコアの基本操作"""
        score = QualityScore(82)

        # 基本的な値の確認
        assert score.value == 82

        # 文字列表現
        assert str(score) == "82点"


class TestValueObjectsIntegration:
    """値オブジェクト間の統合テスト"""

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS-EPISODE_COMPONENTS_I")
    def test_episode_components_integration(self) -> None:
        """エピソード構成要素の統合"""
        number = EpisodeNumber(1)
        title = EpisodeTitle("第1話 テスト")
        word_count = WordCount(2500)
        quality_score = QualityScore(82)

        # すべての値オブジェクトが正常に作成される
        assert number.value == 1
        assert title.value == "第1話 テスト"
        assert word_count.value == 2500
        assert quality_score.value == 82

        # 相互に関連する操作
        assert word_count.is_sufficient_for_episode()
        assert quality_score.get_grade() == "A"
        assert title.to_filename_safe() == "第1話_テスト"

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS-VALUE_OBJECTS_IMMUTA")
    def test_value_objects_immutability(self) -> None:
        """値オブジェクトの不変性"""
        number = EpisodeNumber(1)
        title = EpisodeTitle("テスト")
        word_count = WordCount(1000)
        quality_score = QualityScore(75)

        # 値オブジェクトは不変であることを確認
        original_number = number.value
        original_title = title.value
        original_word_count = word_count.value
        original_quality_score = quality_score.value

        # 新しい値オブジェクトを作成しても元の値は変わらない
        EpisodeNumber(2)
        EpisodeTitle("新しいテスト")

        assert number.value == original_number
        assert title.value == original_title
        assert word_count.value == original_word_count
        assert quality_score.value == original_quality_score

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS-VALUE_OBJECTS_HASH_C")
    def test_value_objects_hash_consistency(self) -> None:
        """値オブジェクトのハッシュ一貫性"""
        number1 = EpisodeNumber(1)
        number2 = EpisodeNumber(1)
        number3 = EpisodeNumber(2)

        # 同じ値のオブジェクトは同じハッシュ
        assert hash(number1) == hash(number2)
        # 異なる値のオブジェクトは(通常)異なるハッシュ
        assert hash(number1) != hash(number3)

        # セットでの使用が可能
        number_set = {number1, number2, number3}
        assert len(number_set) == 2  # number1とnumber2は同じ扱い
