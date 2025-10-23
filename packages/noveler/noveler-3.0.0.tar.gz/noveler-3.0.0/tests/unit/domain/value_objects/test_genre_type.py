"""GenreType値オブジェクトのテスト

仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.value_objects.genre_type import GenreType

pytestmark = pytest.mark.vo_smoke



class TestGenreType:
    """GenreType値オブジェクトのテスト

    仕様書: SPEC-DOMAIN-VALUE-OBJECTS
    """

    def test_creation(self) -> None:
        """ファンタジージャンルが正しく作成できることを確認"""
        # テストは失敗する(実装前)
        genre = GenreType("ファンタジー")
        assert genre.value == "ファンタジー"
        assert genre.name == "ファンタジー"

    def test_creation_1(self) -> None:
        """ミステリージャンルが正しく作成できることを確認"""
        genre = GenreType("ミステリー")
        assert genre.value == "ミステリー"
        assert genre.name == "ミステリー"

    def test_sf_creation(self) -> None:
        """SFジャンルが正しく作成できることを確認"""
        genre = GenreType("SF")
        assert genre.value == "SF"
        assert genre.name == "SF"

    def test_creation_2(self) -> None:
        """その他のジャンルも作成できることを確認"""
        genre = GenreType("ホラー")
        assert genre.value == "ホラー"
        assert genre.name == "ホラー"

    def test_unnamed(self) -> None:
        """空文字列のジャンルは作成できないことを確認"""
        with pytest.raises(ValueError, match="ジャンル名は空にできません"):
            GenreType("")

    def test_nonevalue(self) -> None:
        """None値のジャンルは作成できないことを確認"""
        with pytest.raises(ValueError, match="ジャンル名は空にできません"):
            GenreType(None)

    def test_quality_configurationget(self) -> None:
        """ジャンルに応じた品質設定が取得できることを確認"""
        fantasy = GenreType("ファンタジー")
        config = fantasy.get_default_quality_config()

        assert config["basic_style"]["max_hiragana_ratio"] == 0.45
        assert config["basic_style"]["min_sentence_variety"] == 0.25
        assert config["composition"]["dialog_ratio_range"] == [0.25, 0.55]
        assert config["composition"]["short_sentence_ratio"] == 0.4

    def test_quality_configuration(self) -> None:
        """恋愛ジャンルの品質設定が正しいことを確認"""
        romance = GenreType("恋愛")
        config = romance.get_default_quality_config()

        assert config["basic_style"]["max_hiragana_ratio"] == 0.40
        assert config["basic_style"]["min_sentence_variety"] == 0.30
        assert config["composition"]["dialog_ratio_range"] == [0.35, 0.65]
        assert config["composition"]["short_sentence_ratio"] == 0.3

    def test_quality_configuration_1(self) -> None:
        """ミステリージャンルの品質設定が正しいことを確認"""
        mystery = GenreType("ミステリー")
        config = mystery.get_default_quality_config()

        assert config["basic_style"]["max_hiragana_ratio"] == 0.35
        assert config["basic_style"]["min_sentence_variety"] == 0.35
        assert config["composition"]["dialog_ratio_range"] == [0.30, 0.55]
        assert config["composition"]["short_sentence_ratio"] == 0.25

    def test_quality_configuration_2(self) -> None:
        """未定義ジャンルではデフォルト設定が返ることを確認"""
        other = GenreType("ホラー")
        config = other.get_default_quality_config()

        # デフォルト設定(ファンタジーと同じ)
        assert config["basic_style"]["max_hiragana_ratio"] == 0.40
        assert config["basic_style"]["min_sentence_variety"] == 0.30

    def test_verification(self) -> None:
        """同じジャンル名の値オブジェクトは等価であることを確認"""
        genre1 = GenreType("ファンタジー")
        genre2 = GenreType("ファンタジー")
        genre3 = GenreType("恋愛")

        assert genre1 == genre2
        assert genre1 != genre3
        assert genre2 != genre3

    def test_value_verification(self) -> None:
        """値オブジェクトがハッシュ可能であることを確認"""
        genre1 = GenreType("ファンタジー")
        genre2 = GenreType("ファンタジー")

        assert hash(genre1) == hash(genre2)

        # セットに追加できることを確認
        genre_set = {genre1, genre2}
        assert len(genre_set) == 1
