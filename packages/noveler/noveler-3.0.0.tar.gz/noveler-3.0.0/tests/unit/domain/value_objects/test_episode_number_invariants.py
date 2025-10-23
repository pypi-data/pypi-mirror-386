"""EpisodeNumber値オブジェクトの不変条件テスト
TDD: RED Phase - 失敗するテストから開始


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.exceptions import DomainException
from noveler.domain.writing.value_objects.episode_number import EpisodeNumber


class TestEpisodeNumberInvariants:
    """EpisodeNumber値オブジェクトの不変条件テスト"""

    @pytest.mark.spec("SPEC-EPISODE_NUMBER_INVARIANTS-VALID_EPISODE_NUMBER")
    def test_valid_episode_number_creation(self) -> None:
        """有効な話数でEpisodeNumberを作成できる"""
        episode = EpisodeNumber(1)
        assert episode.value == 1
        assert str(episode) == "第001話"

    @pytest.mark.spec("SPEC-EPISODE_NUMBER_INVARIANTS-ZERO_EPISODE_NUMBER_")
    def test_zero_episode_number_raises_error(self) -> None:
        """話数0はエラーになる"""
        with pytest.raises(DomainException, match=".*"):
            EpisodeNumber(0)

    @pytest.mark.spec("SPEC-EPISODE_NUMBER_INVARIANTS-NEGATIVE_EPISODE_NUM")
    def test_negative_episode_number_raises_error(self) -> None:
        """負の話数はエラーになる"""
        with pytest.raises(DomainException, match=".*"):
            EpisodeNumber(-1)

    @pytest.mark.spec("SPEC-EPISODE_NUMBER_INVARIANTS-EPISODE_NUMBER_MAX_L")
    def test_episode_number_max_limit(self) -> None:
        """話数の上限(9999話)を超えるとエラーになる"""
        # 多くの小説プラットフォームでは9999話が上限
        with pytest.raises(DomainException, match="話数は9999以下である必要があります"):
            EpisodeNumber(10000)

    @pytest.mark.spec("SPEC-EPISODE_NUMBER_INVARIANTS-EPISODE_NUMBER_IMMUT")
    def test_episode_number_immutability(self) -> None:
        """EpisodeNumberは不変である"""
        episode = EpisodeNumber(1)
        with pytest.raises(AttributeError, match=".*"):
            episode.value = 2

    @pytest.mark.spec("SPEC-EPISODE_NUMBER_INVARIANTS-NEXT_EPISODE_RESPECT")
    def test_next_episode_respects_limit(self) -> None:
        """next()メソッドも上限を守る"""
        episode = EpisodeNumber(9999)
        with pytest.raises(DomainException, match="話数は9999以下である必要があります"):
            episode.next()

    @pytest.mark.spec("SPEC-EPISODE_NUMBER_INVARIANTS-EPISODE_NUMBER_COMPA")
    def test_episode_number_comparison(self) -> None:
        """話数の比較が正しく動作する"""
        ep1 = EpisodeNumber(1)
        ep2 = EpisodeNumber(2)
        ep3 = EpisodeNumber(2)

        assert ep1 < ep2
        assert ep2 > ep1
        assert ep2 == ep3
        assert ep1 != ep2

    @pytest.mark.spec("SPEC-EPISODE_NUMBER_INVARIANTS-EPISODE_NUMBER_FORMA")
    def test_episode_number_format_consistency(self) -> None:
        """フォーマットの一貫性を保つ"""
        test_cases = [
            (1, "第001話"),
            (10, "第010話"),
            (100, "第100話"),
            (1000, "第1000話"),
            (9999, "第9999話"),
        ]
        for value, expected in test_cases:
            episode = EpisodeNumber(value)
            assert str(episode) == expected
            assert episode.format() == expected  # formatメソッドも追加予定

    @pytest.mark.spec("SPEC-EPISODE_NUMBER_INVARIANTS-EPISODE_NUMBER_HASHA")
    def test_episode_number_hashable(self) -> None:
        """EpisodeNumberはハッシュ可能でセットや辞書のキーに使える"""
        ep1 = EpisodeNumber(1)
        ep2 = EpisodeNumber(2)
        ep1_copy = EpisodeNumber(1)

        episode_set = {ep1, ep2, ep1_copy}
        assert len(episode_set) == 2  # ep1とep1_copyは同じ

        episode_dict = {ep1: "第1話の内容"}
        assert episode_dict[ep1_copy] == "第1話の内容"
