#!/usr/bin/env python3
"""エピソードタイトル値オブジェクトのユニットテスト

TDD+DDD原則に基づく高速ユニットテスト
実行時間目標: < 0.01秒/テスト
"""

import pytest

pytestmark = pytest.mark.plot_episode


from noveler.domain.value_objects.episode_title import EpisodeTitle


class TestEpisodeTitle:
    """エピソードタイトル値オブジェクトのユニットテスト"""

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_valid_title_creation(self) -> None:
        """正常なタイトルの作成"""
        title = EpisodeTitle("テストタイトル")
        assert title.value == "テストタイトル"

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_title_string_representation(self) -> None:
        """文字列表現のテスト"""
        title = EpisodeTitle("テストタイトル")
        assert str(title) == "テストタイトル"

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_filename_safe_conversion(self) -> None:
        """ファイル名安全変換のテスト"""
        title = EpisodeTitle("テスト:タイトル!?")
        safe_name = title.to_filename_safe()
        assert safe_name == "テスト_タイトル"

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_filename_safe_consecutive_underscores(self) -> None:
        """連続アンダースコアの処理"""
        title = EpisodeTitle("テスト  タイトル")
        safe_name = title.to_filename_safe()
        assert safe_name == "テスト_タイトル"

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_filename_safe_leading_trailing_cleanup(self) -> None:
        """先頭・末尾のアンダースコア削除"""
        title = EpisodeTitle(":テストタイトル:")
        safe_name = title.to_filename_safe()
        assert safe_name == "テストタイトル"

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_empty_title_error(self) -> None:
        """空のタイトルでエラー"""
        with pytest.raises(ValueError, match="タイトルは空にできません"):
            EpisodeTitle("")

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_whitespace_only_title_error(self) -> None:
        """空白のみのタイトルでエラー"""
        with pytest.raises(ValueError, match="タイトルは空にできません"):
            EpisodeTitle("   ")

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_too_long_title_error(self) -> None:
        """長すぎるタイトルでエラー"""
        long_title = "あ" * 101
        with pytest.raises(ValueError, match="タイトルは100文字以内である必要があります"):
            EpisodeTitle(long_title)

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_invalid_characters_error(self) -> None:
        """使用禁止文字でエラー"""
        with pytest.raises(ValueError, match="タイトルに使用できない文字が含まれています"):
            EpisodeTitle("テスト\\タイトル")

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_invalid_type_error(self) -> None:
        """文字列以外の型でエラー"""
        with pytest.raises(ValueError, match="タイトルは文字列である必要があります"):
            EpisodeTitle(123)

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_forbidden_characters_complete(self) -> None:
        """全ての禁止文字でエラー"""
        forbidden_chars = ["\\", "/", "*", '"', "<", ">", "|"]
        for char in forbidden_chars:
            with pytest.raises(ValueError, match="タイトルに使用できない文字が含まれています"):
                EpisodeTitle(f"テスト{char}タイトル")

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_filename_safe_conversion_complete(self) -> None:
        """ファイル名変換の完全なルールテスト"""
        # 読点 → アンダースコア
        title1 = EpisodeTitle("テスト、タイトル")
        assert title1.to_filename_safe() == "テスト_タイトル"

        # 句点 → 削除
        title2 = EpisodeTitle("テスト。タイトル")
        assert title2.to_filename_safe() == "テストタイトル"

        # 半角スペース → アンダースコア
        title3 = EpisodeTitle("テスト タイトル")
        assert title3.to_filename_safe() == "テスト_タイトル"

        # 複合パターン
        title4 = EpisodeTitle("第1話 特別な一日!?。、")
        assert title4.to_filename_safe() == "第1話_特別な一日"

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_newline_character_forbidden(self) -> None:
        """改行文字は禁止"""
        with pytest.raises(ValueError, match="タイトルに改行文字を含めることはできません"):
            EpisodeTitle("テスト\nタイトル")

        with pytest.raises(ValueError, match="タイトルに改行文字を含めることはできません"):
            EpisodeTitle("テスト\r\nタイトル")

    @pytest.mark.spec("SPEC-EPISODE-009")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_title_length_boundaries(self) -> None:
        """タイトル長の境界値テスト"""
        # 1文字(最小)
        title1 = EpisodeTitle("あ")
        assert len(title1.value) == 1

        # 100文字(最大)
        title100 = EpisodeTitle("あ" * 100)
        assert len(title100.value) == 100
