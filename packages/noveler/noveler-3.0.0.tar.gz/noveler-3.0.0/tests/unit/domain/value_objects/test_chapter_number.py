"""章番号値オブジェクトのテスト

SPEC-PLOT-001: Claude Code連携プロット生成システム
"""

import pytest

from noveler.domain.value_objects.chapter_number import ChapterNumber, ChapterNumberError

pytestmark = pytest.mark.vo_smoke



class TestChapterNumber:
    """章番号値オブジェクトのテストクラス"""

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_chapter_number_creation_success(self) -> None:
        """章番号作成成功テスト"""
        # Given & When: 有効な章番号で作成
        chapter_number = ChapterNumber(1)

        # Then: 正しく作成される
        assert chapter_number.value == 1
        assert str(chapter_number) == "chapter01"
        assert repr(chapter_number) == "ChapterNumber(1)"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_chapter_number_creation_with_large_number(self) -> None:
        """大きな章番号作成テスト"""
        # Given & When: 大きな章番号で作成
        chapter_number = ChapterNumber(99)

        # Then: 正しく作成される
        assert chapter_number.value == 99
        assert str(chapter_number) == "chapter99"

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_chapter_number_creation_failure_zero(self) -> None:
        """章番号作成失敗テスト(0)"""
        # Given & When & Then: 0で作成するとエラー
        with pytest.raises(ChapterNumberError, match="章番号は1以上の整数である必要があります"):
            ChapterNumber(0)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_chapter_number_creation_failure_negative(self) -> None:
        """章番号作成失敗テスト(負数)"""
        # Given & When & Then: 負数で作成するとエラー
        with pytest.raises(ChapterNumberError, match="章番号は1以上の整数である必要があります"):
            ChapterNumber(-1)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_chapter_number_equality(self) -> None:
        """章番号等価性テスト"""
        # Given: 同じ値の章番号
        chapter1 = ChapterNumber(1)
        chapter2 = ChapterNumber(1)
        chapter3 = ChapterNumber(2)

        # When & Then: 等価性チェック
        assert chapter1 == chapter2
        assert chapter1 != chapter3
        assert hash(chapter1) == hash(chapter2)
        assert hash(chapter1) != hash(chapter3)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_chapter_number_comparison(self) -> None:
        """章番号比較テスト"""
        # Given: 異なる章番号
        chapter1 = ChapterNumber(1)
        chapter2 = ChapterNumber(2)
        chapter3 = ChapterNumber(3)

        # When & Then: 比較演算子テスト
        assert chapter1 < chapter2
        assert chapter2 < chapter3
        assert chapter1 <= chapter2
        assert chapter2 <= chapter2
        assert chapter3 > chapter2
        assert chapter3 >= chapter2
        assert chapter2 >= chapter2

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_episode_number_to_chapter_number(self) -> None:
        """エピソード番号から章番号変換テスト"""
        # Given & When & Then: エピソード番号から章番号を計算
        # 仮定: 1章あたり10エピソード
        assert ChapterNumber.from_episode_number(1) == ChapterNumber(1)
        assert ChapterNumber.from_episode_number(5) == ChapterNumber(1)
        assert ChapterNumber.from_episode_number(10) == ChapterNumber(1)
        assert ChapterNumber.from_episode_number(11) == ChapterNumber(2)
        assert ChapterNumber.from_episode_number(15) == ChapterNumber(2)
        assert ChapterNumber.from_episode_number(20) == ChapterNumber(2)
        assert ChapterNumber.from_episode_number(21) == ChapterNumber(3)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_episode_number_to_chapter_number_custom_episodes_per_chapter(self) -> None:
        """カスタムエピソード数での章番号変換テスト"""
        # Given & When & Then: カスタムエピソード数での変換
        # 1章あたり5エピソード
        assert ChapterNumber.from_episode_number(1, episodes_per_chapter=5) == ChapterNumber(1)
        assert ChapterNumber.from_episode_number(5, episodes_per_chapter=5) == ChapterNumber(1)
        assert ChapterNumber.from_episode_number(6, episodes_per_chapter=5) == ChapterNumber(2)
        assert ChapterNumber.from_episode_number(10, episodes_per_chapter=5) == ChapterNumber(2)
        assert ChapterNumber.from_episode_number(11, episodes_per_chapter=5) == ChapterNumber(3)

    @pytest.mark.spec("SPEC-PLOT-001")
    def test_episode_number_to_chapter_number_failure(self) -> None:
        """エピソード番号から章番号変換失敗テスト"""
        # Given & When & Then: 無効なエピソード番号でエラー
        with pytest.raises(ChapterNumberError, match="エピソード番号は1以上の整数である必要があります"):
            ChapterNumber.from_episode_number(0)

        with pytest.raises(ChapterNumberError, match="エピソード番号は1以上の整数である必要があります"):
            ChapterNumber.from_episode_number(-1)
