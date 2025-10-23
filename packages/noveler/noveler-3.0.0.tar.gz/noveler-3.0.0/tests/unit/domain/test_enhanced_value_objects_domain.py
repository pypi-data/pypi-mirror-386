#!/usr/bin/env python3
"""強化版値オブジェクトのテスト

Design by Contractと不変性を組み合わせたテスト


仕様書: SPEC-UNIT-TEST
"""

import pytest

from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.enhanced_episode_title import EnhancedEpisodeTitle


class TestEnhancedEpisodeTitle:
    """強化版エピソードタイトルのテストスイート"""

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS_DOMAIN-VALID_TITLE_CREATION")
    def test_valid_title_creation(self) -> None:
        """正常なタイトル作成"""
        title = EnhancedEpisodeTitle("第1話 始まりの物語")
        assert title.value == "第1話 始まりの物語"
        assert str(title) == "第1話 始まりの物語"

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS_DOMAIN-WHITESPACE_NORMALIZA")
    def test_whitespace_normalization(self) -> None:
        """空白の正規化"""
        # 前後の空白は自動的に除去される
        title = EnhancedEpisodeTitle("  タイトル  ")
        assert title.value == "タイトル"

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS_DOMAIN-EMPTY_TITLE_CONTRACT")
    def test_empty_title_contract_violation(self) -> None:
        """空タイトルの契約違反"""
        # 空文字列は事前条件違反
        with pytest.raises(DomainException, match=".*"):
            EnhancedEpisodeTitle("")

        # 空白のみも事前条件違反
        with pytest.raises(DomainException, match=".*"):
            EnhancedEpisodeTitle("   ")

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS_DOMAIN-LENGTH_LIMIT_CONTRAC")
    def test_length_limit_contract(self) -> None:
        """文字数制限の契約"""
        # 100文字ちょうどはOK
        long_title = "あ" * 100
        title = EnhancedEpisodeTitle(long_title)
        assert len(title.value) == 100

        # 101文字は事前条件違反
        with pytest.raises(DomainException, match=".*"):
            EnhancedEpisodeTitle("あ" * 101)

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS_DOMAIN-FILENAME_SAFE_CONVER")
    def test_filename_safe_conversion(self) -> None:
        """ファイル名安全変換の契約"""
        title = EnhancedEpisodeTitle("第1話: 始まり/終わり")
        safe_name = title.to_filename_safe()

        # 事後条件: 無効な文字が含まれていない
        assert ":" not in safe_name
        assert "/" not in safe_name
        assert safe_name == "第1話_ 始まり_終わり"

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS_DOMAIN-TRUNCATE_CONTRACT")
    def test_truncate_contract(self) -> None:
        """切り詰めの契約"""
        title = EnhancedEpisodeTitle("とても長いタイトルです")

        # 正常な切り詰め
        truncated = title.truncate(10)
        assert truncated.value == "とても長いタイ..."  # 7文字 + "..." = 10文字
        assert len(truncated.value) == 10

        # 無効な引数はValueError
        with pytest.raises(ValueError, match=".*"):
            title.truncate(0)

        with pytest.raises(ValueError, match=".*"):
            title.truncate(-1)

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS_DOMAIN-IMMUTABILITY")
    def test_immutability(self) -> None:
        """不変性のテスト"""
        title = EnhancedEpisodeTitle("不変のタイトル")

        # 直接の属性変更は不可
        with pytest.raises(AttributeError, match=".*"):
            title.value = "変更後"

        # 元のインスタンスは変更されない
        original = title.value
        title.truncate(5)
        assert title.value == original

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS_DOMAIN-CONTAINS_KEYWORD")
    def test_contains_keyword(self) -> None:
        """キーワード検索の契約"""
        title = EnhancedEpisodeTitle("魔法使いの冒険")

        # 事後条件: boolを返す
        assert title.contains_keyword("魔法") is True
        assert title.contains_keyword("剣士") is False

        # 大文字小文字を区別しない
        assert title.contains_keyword("魔法") is True
        assert title.contains_keyword("魔法") is True

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS_DOMAIN-INVARIANT_CONDITIONS")
    def test_invariant_conditions(self) -> None:
        """不変条件のテスト"""
        # 正常なインスタンス作成後、不変条件は常に満たされる
        title = EnhancedEpisodeTitle("テストタイトル")

        # どのメソッドを呼んでも不変条件は保持される
        title.to_filename_safe()
        assert title.value  # 空でない
        assert len(title.value) <= 100  # 長さ制限内

        title.truncate(5)
        assert title.value
        assert len(title.value) <= 100

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS_DOMAIN-TYPE_SAFETY_CONTRACT")
    def test_type_safety_contracts(self) -> None:
        """型安全性の契約"""
        # 文字列以外はDomainException
        with pytest.raises(DomainException, match=".*"):
            EnhancedEpisodeTitle(123)  # type: ignore

        with pytest.raises(DomainException, match=".*"):
            EnhancedEpisodeTitle(None)  # type: ignore

    @pytest.mark.spec("SPEC-ENHANCED_VALUE_OBJECTS_DOMAIN-CONTRACT_COMPOSITION")
    def test_contract_composition(self) -> None:
        """複合的な契約の動作"""
        # 複数の契約が組み合わさった場合
        title = EnhancedEpisodeTitle("第1話: 新たな<冒険>の始まり")

        # ファイル名変換は複数の事後条件を満たす
        safe = title.to_filename_safe()
        assert safe  # 空でない
        assert "<" not in safe  # 無効文字除去
        assert ">" not in safe
        assert ":" not in safe

        # 切り詰めも複数の条件を満たす
        truncated = title.truncate(15)
        assert len(truncated.value) <= 15
        assert truncated.value.endswith("...")
        assert isinstance(truncated, EnhancedEpisodeTitle)
