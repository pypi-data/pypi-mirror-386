#!/usr/bin/env python3
"""エピソード番号値オブジェクトのユニットテスト

TDD+DDD原則に基づく高速ユニットテスト
実行時間目標: < 0.01秒/テスト
"""

import pytest

from noveler.domain.value_objects.episode_number import EpisodeNumber


class TestEpisodeNumber:
    """エピソード番号値オブジェクトのユニットテスト"""

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_valid_episode_number_creation(self) -> None:
        """正常なエピソード番号の作成"""
        episode_num = EpisodeNumber(1)
        assert episode_num.value == 1

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_episode_number_string_representation(self) -> None:
        """文字列表現のテスト"""
        episode_num = EpisodeNumber(5)
        assert str(episode_num) == "第005話"

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_episode_number_comparison(self) -> None:
        """比較演算子のテスト"""
        ep1 = EpisodeNumber(1)
        ep2 = EpisodeNumber(2)
        ep3 = EpisodeNumber(1)

        assert ep1 < ep2
        assert ep2 > ep1
        assert ep1 == ep3

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_next_episode_number(self) -> None:
        """次のエピソード番号取得"""
        episode_num = EpisodeNumber(5)
        next_num = episode_num.next()
        assert next_num.value == 6

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_previous_episode_number(self) -> None:
        """前のエピソード番号取得"""
        episode_num = EpisodeNumber(5)
        prev_num = episode_num.previous()
        assert prev_num.value == 4

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_invalid_episode_number_zero(self) -> None:
        """不正なエピソード番号(0)でエラー"""
        with pytest.raises(ValueError, match="エピソード番号は1以上である必要があります"):
            EpisodeNumber(0)

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_invalid_episode_number_negative(self) -> None:
        """不正なエピソード番号(負数)でエラー"""
        with pytest.raises(ValueError, match="エピソード番号は1以上である必要があります"):
            EpisodeNumber(-1)

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_invalid_episode_number_too_large(self) -> None:
        """不正なエピソード番号(上限超過)でエラー"""
        with pytest.raises(ValueError, match="エピソード番号は9999以下である必要があります"):
            EpisodeNumber(10000)

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_first_episode_previous_error(self) -> None:
        """第1話の前のエピソードでエラー"""
        episode_num = EpisodeNumber(1)
        with pytest.raises(ValueError, match="最初のエピソードに前のエピソードはありません"):
            episode_num.previous()

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_episode_number_not_implemented_comparison(self) -> None:
        """異なる型との比較でTypeError"""
        episode_num = EpisodeNumber(1)
        with pytest.raises(TypeError, match=".*"):
            assert episode_num < "invalid"
        with pytest.raises(TypeError, match=".*"):
            assert episode_num <= "invalid"
        with pytest.raises(TypeError, match=".*"):
            assert episode_num > "invalid"
        with pytest.raises(TypeError, match=".*"):
            assert episode_num >= "invalid"

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_invalid_episode_number_string(self) -> None:
        """文字列でエラー"""
        with pytest.raises(ValueError, match="エピソード番号は整数である必要があります"):
            EpisodeNumber("1")

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_invalid_episode_number_float(self) -> None:
        """小数でエラー"""
        with pytest.raises(ValueError, match="エピソード番号は整数である必要があります"):
            EpisodeNumber(1.5)

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_last_episode_next_error(self) -> None:
        """最終話(9999)の次のエピソードでエラー"""
        episode_num = EpisodeNumber(9999)
        with pytest.raises(ValueError, match="エピソード番号は9999以下である必要があります"):
            episode_num.next()

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_episode_number_not_equal(self) -> None:
        """不等価演算子のテスト"""
        ep1 = EpisodeNumber(1)
        ep2 = EpisodeNumber(2)
        assert ep1 != ep2

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_episode_number_hashable(self) -> None:
        """ハッシュ可能性のテスト"""
        ep1 = EpisodeNumber(1)
        ep2 = EpisodeNumber(1)
        ep3 = EpisodeNumber(2)

        # ハッシュ値の確認
        assert hash(ep1) == hash(ep2)
        assert hash(ep1) != hash(ep3)

        # セットで使用可能
        episode_set = {ep1, ep2, ep3}
        assert len(episode_set) == 2  # ep1とep2は同一

        # 辞書のキーとして使用可能
        episode_dict = {ep1: "第1話", ep3: "第2話"}
        assert episode_dict[EpisodeNumber(1)] == "第1話"

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_episode_number_string_format_boundaries(self) -> None:
        """文字列表現の境界値テスト"""
        # 1桁
        assert str(EpisodeNumber(1)) == "第001話"
        assert str(EpisodeNumber(9)) == "第009話"

        # 2桁
        assert str(EpisodeNumber(10)) == "第010話"
        assert str(EpisodeNumber(99)) == "第099話"

        # 3桁
        assert str(EpisodeNumber(100)) == "第100話"
        assert str(EpisodeNumber(999)) == "第999話"

        # 4桁(最大値)
        assert str(EpisodeNumber(1000)) == "第1000話"
        assert str(EpisodeNumber(9999)) == "第9999話"

    @pytest.mark.spec("SPEC-EPISODE-008")
    @pytest.mark.spec("SPEC-EPISODE-005")
    def test_comparison_operators_complete(self) -> None:
        """比較演算子の完全テスト(<=, >=含む)"""
        ep1 = EpisodeNumber(1)
        ep2 = EpisodeNumber(2)
        ep3 = EpisodeNumber(1)

        # less than or equal
        assert ep1 <= ep2
        assert ep1 <= ep3
        assert not ep2 <= ep1

        # greater than or equal
        assert ep2 >= ep1
        assert ep3 >= ep1
        assert not ep1 >= ep2
