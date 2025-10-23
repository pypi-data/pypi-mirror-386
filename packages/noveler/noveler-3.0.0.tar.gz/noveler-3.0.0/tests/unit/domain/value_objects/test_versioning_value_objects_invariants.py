"""バージョニングドメインの値オブジェクトの不変条件テスト
TDD: RED Phase - 失敗するテストから開始


仕様書: SPEC-DOMAIN-VALUE-OBJECTS
"""

import pytest

from noveler.domain.exceptions import DomainException
from noveler.domain.versioning.value_objects import (
    ChangeSignificance,
    ChapterImpact,
    ConsistencyImpact,
    MultiChapterImpact,
)

pytestmark = pytest.mark.vo_smoke


class TestChangeSignificanceInvariants:
    """ChangeSignificance値オブジェクトの不変条件テスト"""

    def test_valid_change_significance_creation(self) -> None:
        """有効な変更重要度を作成できる"""
        sig = ChangeSignificance.major("大規模な構造変更")
        assert sig.level == "major"
        assert sig.reason == "大規模な構造変更"
        assert sig.requires_versioning()

    def test_change_significance_factory_methods(self) -> None:
        """ファクトリメソッドが正しく動作する"""
        major = ChangeSignificance.major("メジャー変更")
        minor = ChangeSignificance.minor("マイナー変更")
        patch = ChangeSignificance.patch("パッチ変更")

        assert major.level == "major"
        assert minor.level == "minor"
        assert patch.level == "patch"

    def test_invalid_level_raises_error(self) -> None:
        """無効なレベルはエラーになる"""
        with pytest.raises(DomainException, match="変更レベルはmajor, minor, patchのいずれかである必要があります"):
            ChangeSignificance("invalid", "理由")

    def test_empty_reason_raises_error(self) -> None:
        """空の理由はエラーになる"""
        with pytest.raises(DomainException, match="変更理由は必須です"):
            ChangeSignificance.major("")

    def test_change_significance_immutability(self) -> None:
        """ChangeSignificanceは不変である"""
        sig = ChangeSignificance.major("テスト")
        with pytest.raises(AttributeError, match=".*"):
            sig.level = "minor"
        with pytest.raises(AttributeError, match=".*"):
            sig.reason = "変更"

    def test_requires_versioning_logic(self) -> None:
        """バージョニング必要性の判定が正しい"""
        assert ChangeSignificance.major("理由").requires_versioning()
        assert not ChangeSignificance.minor("理由").requires_versioning()
        assert not ChangeSignificance.patch("理由").requires_versioning()

    def test_change_significance_equality(self) -> None:
        """等価性のテスト"""
        sig1 = ChangeSignificance.major("同じ理由")
        sig2 = ChangeSignificance.major("同じ理由")
        sig3 = ChangeSignificance.minor("同じ理由")

        assert sig1 == sig2
        assert sig1 != sig3


class TestConsistencyImpactInvariants:
    """ConsistencyImpact値オブジェクトの不変条件テスト"""

    def test_valid_consistency_impact_creation(self) -> None:
        """有効な整合性影響を作成できる"""
        impact = ConsistencyImpact("major")
        assert impact.version_type == "major"
        assert impact.requires_episode_status_update
        assert impact.requires_foreshadowing_review
        assert impact.requires_character_growth_review
        assert impact.requires_important_scenes_review

    def test_minor_impact_settings(self) -> None:
        """マイナー影響の設定が正しい"""
        impact = ConsistencyImpact("minor")
        assert impact.version_type == "minor"
        assert impact.requires_episode_status_update  # 常にTrue
        assert not impact.requires_foreshadowing_review
        assert not impact.requires_character_growth_review
        assert not impact.requires_important_scenes_review

    def test_invalid_version_type_raises_error(self) -> None:
        """無効なバージョンタイプはエラーになる"""
        with pytest.raises(
            DomainException,
            match="バージョンタイプはmajor, minor, patchのいずれかである必要があります",
        ):
            ConsistencyImpact("invalid")

    def test_affected_files_list(self) -> None:
        """影響ファイルリストが正しい"""
        major_impact = ConsistencyImpact("major")
        assert "話数管理.yaml" in major_impact.affected_management_files
        assert "伏線管理.yaml" in major_impact.affected_management_files
        assert "キャラ成長.yaml" in major_impact.affected_management_files
        assert "重要シーン.yaml" in major_impact.affected_management_files

        minor_impact = ConsistencyImpact("minor")
        assert "話数管理.yaml" in minor_impact.affected_management_files
        assert len(minor_impact.affected_management_files) == 1

    def test_consistency_impact_immutability(self) -> None:
        """ConsistencyImpactは不変である"""
        impact = ConsistencyImpact("major")
        with pytest.raises(AttributeError, match=".*"):
            impact.version_type = "minor"


class TestChapterImpactInvariants:
    """ChapterImpact値オブジェクトの不変条件テスト"""

    def test_valid_chapter_impact_creation(self) -> None:
        """有効な章別影響を作成できる"""
        impact = ChapterImpact(3)
        assert impact.affected_chapter == 3
        assert impact.chapter_name == "chapter03"
        assert impact.requires_episode_review
        assert impact.requires_foreshadowing_review
        assert impact.impact_scope == "chapter_specific"

    def test_invalid_chapter_number_raises_error(self) -> None:
        """無効な章番号はエラーになる"""
        with pytest.raises(DomainException, match="章番号は1以上である必要があります"):
            ChapterImpact(0)
        with pytest.raises(DomainException, match="章番号は1以上である必要があります"):
            ChapterImpact(-1)

    def test_chapter_impact_immutability(self) -> None:
        """ChapterImpactは不変である"""
        impact = ChapterImpact(5)
        with pytest.raises(AttributeError, match=".*"):
            impact.affected_chapter = 6
        with pytest.raises(AttributeError, match=".*"):
            impact.requires_episode_review = False


class TestMultiChapterImpactInvariants:
    """MultiChapterImpact値オブジェクトの不変条件テスト"""

    def test_valid_multi_chapter_impact_creation(self) -> None:
        """有効な複数章影響を作成できる"""
        impact = MultiChapterImpact([3, 1, 5])
        assert impact.affected_chapters == [1, 3, 5]  # ソートされている
        assert len(impact.chapter_impacts) == 3
        assert impact.impact_scope == "multi_chapter"

    def test_empty_chapters_raises_error(self) -> None:
        """空の章リストはエラーになる"""
        with pytest.raises(DomainException, match="少なくとも1つの章番号が必要です"):
            MultiChapterImpact([])

    def test_invalid_chapter_in_list_raises_error(self) -> None:
        """リスト内の無効な章番号はエラーになる"""
        with pytest.raises(DomainException, match="章番号は1以上である必要があります"):
            MultiChapterImpact([1, 0, 3])

    def test_multi_chapter_impact_immutability(self) -> None:
        """MultiChapterImpactは不変である"""
        impact = MultiChapterImpact([1, 2, 3])
        with pytest.raises(AttributeError, match=".*"):
            impact.chapter_numbers = [4, 5, 6]
        # affected_chaptersプロパティ経由では変更不可
        original_chapters = impact.affected_chapters
        assert original_chapters == [1, 2, 3]
