"""EpisodeTitle値オブジェクトの不変条件テスト
TDD: RED Phase - 失敗するテストから開始


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

pytestmark = pytest.mark.plot_episode


from noveler.domain.exceptions import DomainException
from noveler.domain.writing.value_objects.episode_title import EpisodeTitle


class TestEpisodeTitleInvariants:
    """EpisodeTitle値オブジェクトの不変条件テスト"""

    @pytest.mark.spec("SPEC-EPISODE_TITLE_INVARIANTS-VALID_EPISODE_TITLE_")
    def test_valid_episode_title_creation(self) -> None:
        """有効なタイトルでEpisodeTitleを作成できる"""
        title = EpisodeTitle("接続過多な朝")
        assert title.value == "接続過多な朝"
        assert str(title) == "接続過多な朝"

    @pytest.mark.spec("SPEC-EPISODE_TITLE_INVARIANTS-EMPTY_TITLE_RAISES_E")
    def test_empty_title_raises_error(self) -> None:
        """空のタイトルはエラーになる"""
        with pytest.raises(DomainException, match="タイトルは空にできません"):
            EpisodeTitle("")

    @pytest.mark.spec("SPEC-EPISODE_TITLE_INVARIANTS-WHITESPACE_ONLY_TITL")
    def test_whitespace_only_title_raises_error(self) -> None:
        """空白のみのタイトルはエラーになる"""
        with pytest.raises(DomainException, match="タイトルは空にできません"):
            EpisodeTitle("   ")

    @pytest.mark.spec("SPEC-EPISODE_TITLE_INVARIANTS-TITLE_MAX_LENGTH_LIM")
    def test_title_max_length_limit(self) -> None:
        """タイトルの最大長(100文字)を超えるとエラーになる"""
        long_title = "あ" * 101
        with pytest.raises(DomainException, match="タイトルは100文字以内である必要があります"):
            EpisodeTitle(long_title)

    @pytest.mark.spec("SPEC-EPISODE_TITLE_INVARIANTS-TITLE_EXACTLY_AT_MAX")
    def test_title_exactly_at_max_length(self) -> None:
        """ちょうど100文字のタイトルは有効"""
        max_title = "あ" * 100
        title = EpisodeTitle(max_title)
        assert len(title.value) == 100

    @pytest.mark.spec("SPEC-EPISODE_TITLE_INVARIANTS-TITLE_MINIMUM_LENGTH")
    def test_title_minimum_length(self) -> None:
        """1文字のタイトルも有効"""
        title = EpisodeTitle("夢")
        assert title.value == "夢"

    @pytest.mark.spec("SPEC-EPISODE_TITLE_INVARIANTS-EPISODE_TITLE_IMMUTA")
    def test_episode_title_immutability(self) -> None:
        """EpisodeTitleは不変である"""
        title = EpisodeTitle("不変のタイトル")
        with pytest.raises(AttributeError, match=".*"):
            title.value = "変更されたタイトル"

    @pytest.mark.spec("SPEC-EPISODE_TITLE_INVARIANTS-CONTAINS_EPISODE_NUM")
    def test_contains_episode_number_detection(self) -> None:
        """話数が含まれているか正しく検出する"""
        # 話数を含むタイトル
        title_with_number = EpisodeTitle("第1話 始まりの朝")
        assert title_with_number.contains_episode_number()

        # 話数を含まないタイトル
        title_without_number = EpisodeTitle("始まりの朝")
        assert not title_without_number.contains_episode_number()

        # 「第」のみ含む場合
        title_with_dai_only = EpisodeTitle("第一章の始まり")
        assert not title_with_dai_only.contains_episode_number()

        # 「話」のみ含む場合
        title_with_wa_only = EpisodeTitle("昔話の続き")
        assert not title_with_wa_only.contains_episode_number()

    @pytest.mark.spec("SPEC-EPISODE_TITLE_INVARIANTS-TITLE_WITH_SPECIAL_C")
    def test_title_with_special_characters(self) -> None:
        """特殊文字を含むタイトルも有効"""
        special_titles = [
            "記憶の欠片【前編】",
            "出会い~運命の交差点~",
            "終焉/始まり",
            "???の正体",
            "!!緊急事態!!",
        ]
        for title_str in special_titles:
            title = EpisodeTitle(title_str)
            assert title.value == title_str

    @pytest.mark.spec("SPEC-EPISODE_TITLE_INVARIANTS-TITLE_NORMALIZATION")
    def test_title_normalization(self) -> None:
        """タイトルの正規化(前後の空白除去)"""
        title = EpisodeTitle("  前後に空白があるタイトル  ")
        # 不変条件として、前後の空白は自動的に除去されるべき
        assert title.value == "前後に空白があるタイトル"

    @pytest.mark.spec("SPEC-EPISODE_TITLE_INVARIANTS-TITLE_FORMAT_METHOD")
    def test_title_format_method(self) -> None:
        """フォーマットメソッドのテスト"""
        title = EpisodeTitle("テストタイトル")
        # format()メソッドを追加予定
        assert title.format() == "テストタイトル"

    @pytest.mark.spec("SPEC-EPISODE_TITLE_INVARIANTS-TITLE_EQUALITY")
    def test_title_equality(self) -> None:
        """タイトルの等価性"""
        title1 = EpisodeTitle("同じタイトル")
        title2 = EpisodeTitle("同じタイトル")
        title3 = EpisodeTitle("違うタイトル")

        assert title1 == title2
        assert title1 != title3

    @pytest.mark.spec("SPEC-EPISODE_TITLE_INVARIANTS-TITLE_HASHABLE")
    def test_title_hashable(self) -> None:
        """EpisodeTitleはハッシュ可能"""
        title1 = EpisodeTitle("タイトルA")
        title2 = EpisodeTitle("タイトルB")
        title1_copy = EpisodeTitle("タイトルA")

        title_set = {title1, title2, title1_copy}
        assert len(title_set) == 2  # title1とtitle1_copyは同じ
