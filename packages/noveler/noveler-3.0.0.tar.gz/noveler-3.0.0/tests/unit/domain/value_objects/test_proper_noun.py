#!/usr/bin/env python3
"""固有名詞値オブジェクトのユニットテスト

TDD+DDD原則に基づく高速ユニットテスト
実行時間目標: < 0.01秒/テスト


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.value_objects.proper_noun import ProperNoun, ProperNounType

pytestmark = pytest.mark.vo_smoke



class TestProperNoun:
    """固有名詞値オブジェクトのユニットテスト"""

    def test_valid_person_name_creation(self) -> None:
        """正常な人名の作成"""
        noun = ProperNoun("綾瀬カノン", ProperNounType.PERSON)
        assert noun.value == "綾瀬カノン"
        assert noun.noun_type == ProperNounType.PERSON

    def test_person_name_detection(self) -> None:
        """人名判定のテスト"""
        person = ProperNoun("綾瀬カノン", ProperNounType.PERSON)
        place = ProperNoun("東京", ProperNounType.PLACE)

        assert person.is_person_name()
        assert not place.is_person_name()

    def test_place_name_detection(self) -> None:
        """地名判定のテスト"""
        place = ProperNoun("東京", ProperNounType.PLACE)
        person = ProperNoun("綾瀬カノン", ProperNounType.PERSON)

        assert place.is_place_name()
        assert not person.is_place_name()

    def test_organization_name_detection(self) -> None:
        """組織名判定のテスト"""
        org = ProperNoun("BUG.CHURCH", ProperNounType.ORGANIZATION)
        person = ProperNoun("綾瀬カノン", ProperNounType.PERSON)

        assert org.is_organization_name()
        assert not person.is_organization_name()

    def test_special_characters_detection(self) -> None:
        """特殊文字検出のテスト"""
        special = ProperNoun("A-137", ProperNounType.TECHNOLOGY)
        normal = ProperNoun("あいうえお", ProperNounType.OTHER)

        assert special.contains_special_chars()
        assert not normal.contains_special_chars()

    def test_string_methods(self) -> None:
        """文字列メソッドのテスト"""
        noun = ProperNoun("テストデータ", ProperNounType.OTHER)

        assert noun.get_length() == 6
        assert noun.starts_with("テスト")
        assert noun.ends_with("データ")
        assert noun.contains("スト")

    def test_comparison_operators(self) -> None:
        """比較演算子のテスト"""
        noun1 = ProperNoun("あいうえお", ProperNounType.OTHER)
        noun2 = ProperNoun("かきくけこ", ProperNounType.OTHER)
        noun3 = ProperNoun("あいうえお", ProperNounType.PERSON)

        assert noun1 < noun2
        assert noun2 > noun1
        assert noun1 <= noun3
        assert noun2 >= noun1

    def test_display_string(self) -> None:
        """表示用文字列のテスト"""
        person = ProperNoun("綾瀬カノン", ProperNounType.PERSON)
        display = person.to_display_string()
        assert "綾瀬カノン" in display
        assert "人名" in display

    def test_string_representation(self) -> None:
        """文字列表現のテスト"""
        noun = ProperNoun("テスト", ProperNounType.OTHER)
        assert str(noun) == "テスト"

    def test_empty_value_error(self) -> None:
        """空の値でエラー"""
        with pytest.raises(ValueError, match="固有名詞は空にできません"):
            ProperNoun("", ProperNounType.OTHER)

    def test_whitespace_only_error(self) -> None:
        """空白のみでエラー"""
        with pytest.raises(ValueError, match="固有名詞は空にできません"):
            ProperNoun("   ", ProperNounType.OTHER)

    def test_too_long_value_error(self) -> None:
        """長すぎる値でエラー"""
        long_value = "あ" * 101
        with pytest.raises(ValueError, match="固有名詞は100文字以内である必要があります"):
            ProperNoun(long_value, ProperNounType.OTHER)

    def test_invalid_type_error(self) -> None:
        """無効な型でエラー"""
        with pytest.raises(ValueError, match="固有名詞は文字列である必要があります"):
            ProperNoun(123, ProperNounType.OTHER)

    def test_invalid_noun_type_error(self) -> None:
        """無効な固有名詞タイプでエラー"""
        with pytest.raises(ValueError, match="無効な固有名詞タイプ"):
            ProperNoun("テスト", "invalid_type")
