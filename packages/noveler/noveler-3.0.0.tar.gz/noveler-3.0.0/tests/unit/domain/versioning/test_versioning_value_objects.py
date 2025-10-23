"""自動バージョニングの値オブジェクトのテスト

TDD準拠テスト:
    - ChangeSignificance
- ConsistencyImpact
- ForeshadowingImpact
- ChapterImpact
- MultiChapterImpact
- ChapterForeshadowingImpact
- BidirectionalForeshadowingImpact
- ChangeScope
- VersionCalculator


仕様書: SPEC-UNIT-TEST
"""

import re

import pytest

from noveler.domain.exceptions import DomainException, InvalidVersionError
from noveler.domain.versioning.value_objects import (
    BidirectionalForeshadowingImpact,
    ChangeScope,
    ChangeSignificance,
    ChapterForeshadowingImpact,
    ChapterImpact,
    ConsistencyImpact,
    ForeshadowingImpact,
    MultiChapterImpact,
    VersionCalculator,
)


class TestChangeSignificance:
    """ChangeSignificance値オブジェクトのテストクラス"""

    def test_change_significance_creation_major(self) -> None:
        """メジャー変更重要度作成テスト"""
        change = ChangeSignificance("major", "キャラクターの根本的な設定変更")
        assert change.level == "major"
        assert change.reason == "キャラクターの根本的な設定変更"

    def test_change_significance_creation_minor(self) -> None:
        """マイナー変更重要度作成テスト"""
        change = ChangeSignificance("minor", "台詞の微調整")
        assert change.level == "minor"
        assert change.reason == "台詞の微調整"

    def test_change_significance_creation_patch(self) -> None:
        """パッチ変更重要度作成テスト"""
        change = ChangeSignificance("patch", "誤字の修正")
        assert change.level == "patch"
        assert change.reason == "誤字の修正"

    def test_change_significance_invalid_level_error(self) -> None:
        """無効な変更レベルエラーテスト"""
        with pytest.raises(DomainException, match="変更レベルはmajor, minor, patchのいずれかである必要があります"):
            ChangeSignificance("invalid", "無効なレベル")

    def test_change_significance_empty_reason_error(self) -> None:
        """空の変更理由エラーテスト"""
        with pytest.raises(DomainException, match="変更理由は必須です"):
            ChangeSignificance("major", "")

    def test_change_significance_whitespace_reason_error(self) -> None:
        """空白のみの変更理由エラーテスト"""
        with pytest.raises(DomainException, match="変更理由は必須です"):
            ChangeSignificance("major", "   ")

    def test_change_significance_major_factory(self) -> None:
        """メジャー重要度ファクトリーテスト"""
        change = ChangeSignificance.major("大規模な構造変更")
        assert change.level == "major"
        assert change.reason == "大規模な構造変更"

    def test_change_significance_minor_factory(self) -> None:
        """マイナー重要度ファクトリーテスト"""
        change = ChangeSignificance.minor("小規模な改善")
        assert change.level == "minor"
        assert change.reason == "小規模な改善"

    def test_change_significance_patch_factory(self) -> None:
        """パッチ重要度ファクトリーテスト"""
        change = ChangeSignificance.patch("軽微な修正")
        assert change.level == "patch"
        assert change.reason == "軽微な修正"

    def test_change_significance_requires_versioning_major(self) -> None:
        """メジャー変更のバージョン管理必要性テスト"""
        change = ChangeSignificance.major("重要な変更")
        assert change.requires_versioning() is True

    def test_change_significance_requires_versioning_minor(self) -> None:
        """マイナー変更のバージョン管理必要性テスト"""
        change = ChangeSignificance.minor("軽微な変更")
        assert change.requires_versioning() is False

    def test_change_significance_requires_versioning_patch(self) -> None:
        """パッチ変更のバージョン管理必要性テスト"""
        change = ChangeSignificance.patch("修正")
        assert change.requires_versioning() is False

    def test_change_significance_is_frozen(self) -> None:
        """変更重要度オブジェクトの不変性テスト"""
        change = ChangeSignificance.major("テスト")
        with pytest.raises(AttributeError, match=".*"):
            change.level = "minor"  # type: ignore


class TestConsistencyImpact:
    """ConsistencyImpact値オブジェクトのテストクラス"""

    def test_consistency_impact_creation_major(self) -> None:
        """メジャー整合性影響作成テスト"""
        impact = ConsistencyImpact("major")
        assert impact.version_type == "major"

    def test_consistency_impact_creation_minor(self) -> None:
        """マイナー整合性影響作成テスト"""
        impact = ConsistencyImpact("minor")
        assert impact.version_type == "minor"

    def test_consistency_impact_creation_patch(self) -> None:
        """パッチ整合性影響作成テスト"""
        impact = ConsistencyImpact("patch")
        assert impact.version_type == "patch"

    def test_consistency_impact_invalid_type_error(self) -> None:
        """無効なバージョンタイプエラーテスト"""
        with pytest.raises(
            DomainException, match="バージョンタイプはmajor, minor, patchのいずれかである必要があります"
        ):
            ConsistencyImpact("invalid")

    def test_consistency_impact_requires_episode_status_update(self) -> None:
        """エピソードステータス更新必要性テスト"""
        for version_type in ["major", "minor", "patch"]:
            impact = ConsistencyImpact(version_type)
            assert impact.requires_episode_status_update is True

    def test_consistency_impact_requires_foreshadowing_review_major(self) -> None:
        """メジャー版の伏線レビュー必要性テスト"""
        impact = ConsistencyImpact("major")
        assert impact.requires_foreshadowing_review is True

    def test_consistency_impact_requires_foreshadowing_review_minor_patch(self) -> None:
        """マイナー・パッチ版の伏線レビュー必要性テスト"""
        for version_type in ["minor", "patch"]:
            impact = ConsistencyImpact(version_type)
            assert impact.requires_foreshadowing_review is False

    def test_consistency_impact_requires_character_growth_review_major(self) -> None:
        """メジャー版のキャラクター成長レビュー必要性テスト"""
        impact = ConsistencyImpact("major")
        assert impact.requires_character_growth_review is True

    def test_consistency_impact_requires_character_growth_review_minor_patch(self) -> None:
        """マイナー・パッチ版のキャラクター成長レビュー必要性テスト"""
        for version_type in ["minor", "patch"]:
            impact = ConsistencyImpact(version_type)
            assert impact.requires_character_growth_review is False

    def test_consistency_impact_requires_important_scenes_review_major(self) -> None:
        """メジャー版の重要シーンレビュー必要性テスト"""
        impact = ConsistencyImpact("major")
        assert impact.requires_important_scenes_review is True

    def test_consistency_impact_requires_important_scenes_review_minor_patch(self) -> None:
        """マイナー・パッチ版の重要シーンレビュー必要性テスト"""
        for version_type in ["minor", "patch"]:
            impact = ConsistencyImpact(version_type)
            assert impact.requires_important_scenes_review is False

    def test_consistency_impact_affected_management_files_minor_patch(self) -> None:
        """マイナー・パッチ版の影響ファイル一覧テスト"""
        for version_type in ["minor", "patch"]:
            impact = ConsistencyImpact(version_type)
            files = impact.affected_management_files
            assert files == ["話数管理.yaml"]

    def test_consistency_impact_affected_management_files_major(self) -> None:
        """メジャー版の影響ファイル一覧テスト"""
        impact = ConsistencyImpact("major")
        files = impact.affected_management_files
        expected_files = ["話数管理.yaml", "伏線管理.yaml", "キャラ成長.yaml", "重要シーン.yaml"]
        assert files == expected_files

    def test_consistency_impact_is_frozen(self) -> None:
        """整合性影響オブジェクトの不変性テスト"""
        impact = ConsistencyImpact("major")
        with pytest.raises(AttributeError, match=".*"):
            impact.version_type = "minor"  # type: ignore


class TestForeshadowingImpact:
    """ForeshadowingImpact値オブジェクトのテストクラス"""

    def test_foreshadowing_impact_creation(self) -> None:
        """伏線影響分析作成テスト"""
        impact = ForeshadowingImpact()
        assert impact.potentially_invalidated == []
        assert impact.review_recommendations == []

    def test_foreshadowing_impact_add_invalidated_single(self) -> None:
        """無効化伏線追加(単一)テスト"""
        impact = ForeshadowingImpact()
        impact.add_invalidated_foreshadowing("foreshadow_01", "キャラクター設定変更により矛盾")

        assert impact.potentially_invalidated == ["foreshadow_01"]
        assert impact.review_recommendations == ["キャラクター設定変更により矛盾"]

    def test_foreshadowing_impact_add_invalidated_multiple(self) -> None:
        """無効化伏線追加(複数)テスト"""
        impact = ForeshadowingImpact()
        impact.add_invalidated_foreshadowing("foreshadow_01", "理由1")
        impact.add_invalidated_foreshadowing("foreshadow_02", "理由2")
        impact.add_invalidated_foreshadowing("foreshadow_03", "理由3")

        assert impact.potentially_invalidated == ["foreshadow_01", "foreshadow_02", "foreshadow_03"]
        assert impact.review_recommendations == ["理由1", "理由2", "理由3"]

    def test_foreshadowing_impact_add_invalidated_empty_reason(self) -> None:
        """空の理由での無効化伏線追加テスト"""
        impact = ForeshadowingImpact()
        impact.add_invalidated_foreshadowing("foreshadow_01", "")

        assert impact.potentially_invalidated == ["foreshadow_01"]
        assert impact.review_recommendations == ["foreshadow_01: "]


class TestChapterImpact:
    """ChapterImpact値オブジェクトのテストクラス"""

    def test_chapter_impact_creation_valid(self) -> None:
        """有効な章別影響作成テスト"""
        impact = ChapterImpact(3)
        assert impact.affected_chapter == 3

    def test_chapter_impact_creation_zero_error(self) -> None:
        """章番号0エラーテスト"""
        with pytest.raises(DomainException, match="章番号は1以上である必要があります"):
            ChapterImpact(0)

    def test_chapter_impact_creation_negative_error(self) -> None:
        """負の章番号エラーテスト"""
        with pytest.raises(DomainException, match="章番号は1以上である必要があります"):
            ChapterImpact(-1)

    def test_chapter_impact_chapter_name(self) -> None:
        """章名取得テスト"""
        impact = ChapterImpact(5)
        assert impact.chapter_name == "ch05"

    def test_chapter_impact_requires_episode_review(self) -> None:
        """エピソードレビュー必要性テスト"""
        impact = ChapterImpact(1)
        assert impact.requires_episode_review is True

    def test_chapter_impact_requires_foreshadowing_review(self) -> None:
        """伏線レビュー必要性テスト"""
        impact = ChapterImpact(1)
        assert impact.requires_foreshadowing_review is True

    def test_chapter_impact_impact_scope(self) -> None:
        """影響スコープテスト"""
        impact = ChapterImpact(1)
        assert impact.impact_scope == "chapter_specific"

    def test_chapter_impact_is_frozen(self) -> None:
        """章別影響オブジェクトの不変性テスト"""
        impact = ChapterImpact(1)
        with pytest.raises(AttributeError, match=".*"):
            impact.affected_chapter = 2  # type: ignore


class TestMultiChapterImpact:
    """MultiChapterImpact値オブジェクトのテストクラス"""

    def test_multi_chapter_impact_creation_single(self) -> None:
        """単一章での複数章影響作成テスト"""
        impact = MultiChapterImpact([3])
        assert impact.chapter_numbers == [3]

    def test_multi_chapter_impact_creation_multiple(self) -> None:
        """複数章での複数章影響作成テスト"""
        impact = MultiChapterImpact([3, 1, 5, 2])
        assert impact.chapter_numbers == [1, 2, 3, 5]  # ソート済み

    def test_multi_chapter_impact_creation_empty_error(self) -> None:
        """空の章番号リストエラーテスト"""
        with pytest.raises(DomainException, match="少なくとも1つの章番号が必要です"):
            MultiChapterImpact([])

    def test_multi_chapter_impact_creation_zero_chapter_error(self) -> None:
        """章番号0を含むエラーテスト"""
        with pytest.raises(DomainException, match="章番号は1以上である必要があります"):
            MultiChapterImpact([1, 0, 3])

    def test_multi_chapter_impact_creation_negative_chapter_error(self) -> None:
        """負の章番号を含むエラーテスト"""
        with pytest.raises(DomainException, match="章番号は1以上である必要があります"):
            MultiChapterImpact([1, -1, 3])

    def test_multi_chapter_impact_affected_chapters(self) -> None:
        """影響章番号取得テスト"""
        impact = MultiChapterImpact([5, 2, 8, 1])
        assert impact.affected_chapters == [1, 2, 5, 8]

    def test_multi_chapter_impact_chapter_impacts(self) -> None:
        """章別影響リスト取得テスト"""
        impact = MultiChapterImpact([3, 1])
        chapter_impacts = impact.chapter_impacts

        assert len(chapter_impacts) == 2
        assert chapter_impacts[0].affected_chapter == 1
        assert chapter_impacts[1].affected_chapter == 3
        assert all(isinstance(ci, ChapterImpact) for ci in chapter_impacts)

    def test_multi_chapter_impact_impact_scope(self) -> None:
        """影響スコープテスト"""
        impact = MultiChapterImpact([1, 2, 3])
        assert impact.impact_scope == "multi_chapter"

    def test_multi_chapter_impact_duplicate_chapters(self) -> None:
        """重複章番号処理テスト"""
        impact = MultiChapterImpact([3, 1, 3, 2, 1])
        assert impact.chapter_numbers == [1, 1, 2, 3, 3]  # 重複もソート

    def test_multi_chapter_impact_is_frozen(self) -> None:
        """複数章影響オブジェクトの不変性テスト"""
        impact = MultiChapterImpact([1, 2])
        with pytest.raises(AttributeError, match=".*"):
            impact.chapter_numbers = [3, 4]  # type: ignore


class TestChapterForeshadowingImpact:
    """ChapterForeshadowingImpact値オブジェクトのテストクラス"""

    def test_chapter_foreshadowing_impact_creation(self) -> None:
        """章別伏線影響作成テスト"""
        impact = ChapterForeshadowingImpact(5)
        assert impact.chapter == 5
        assert impact.affected_foreshadowing == []
        assert impact.review_recommendation == ""

    def test_chapter_foreshadowing_impact_add_affected_single(self) -> None:
        """影響伏線追加(単一)テスト"""
        impact = ChapterForeshadowingImpact(3)
        impact.add_affected_foreshadowing("foreshadow_01")

        assert impact.affected_foreshadowing == ["foreshadow_01"]
        assert impact.review_recommendation == "ch03の変更により伏線レビューが必要"

    def test_chapter_foreshadowing_impact_add_affected_multiple(self) -> None:
        """影響伏線追加(複数)テスト"""
        impact = ChapterForeshadowingImpact(7)
        impact.add_affected_foreshadowing("foreshadow_01")
        impact.add_affected_foreshadowing("foreshadow_02")
        impact.add_affected_foreshadowing("foreshadow_03")

        assert impact.affected_foreshadowing == ["foreshadow_01", "foreshadow_02", "foreshadow_03"]
        assert impact.review_recommendation == "ch07の変更により伏線レビューが必要"

    def test_chapter_foreshadowing_impact_recommendation_update(self) -> None:
        """推奨事項更新テスト"""
        impact = ChapterForeshadowingImpact(2)
        impact.add_affected_foreshadowing("foreshadow_01")
        original_recommendation = impact.review_recommendation

        impact.add_affected_foreshadowing("foreshadow_02")
        # 推奨事項は最後に追加された時に更新される
        assert impact.review_recommendation == original_recommendation


class TestBidirectionalForeshadowingImpact:
    """BidirectionalForeshadowingImpact値オブジェクトのテストクラス"""

    def test_bidirectional_foreshadowing_impact_creation(self) -> None:
        """双方向伏線影響作成テスト"""
        impact = BidirectionalForeshadowingImpact(5)
        assert impact.affected_chapter == 5
        assert impact.setup_modified == []
        assert impact.resolution_modified == []

    def test_bidirectional_foreshadowing_impact_add_setup_modified(self) -> None:
        """仕込み変更追加テスト"""
        impact = BidirectionalForeshadowingImpact(3)
        impact.add_setup_modified("foreshadow_01", 7)

        assert impact.setup_modified == [("foreshadow_01", 7)]
        assert impact.resolution_modified == []

    def test_bidirectional_foreshadowing_impact_add_resolution_modified(self) -> None:
        """回収変更追加テスト"""
        impact = BidirectionalForeshadowingImpact(8)
        impact.add_resolution_modified("foreshadow_02", 4)

        assert impact.setup_modified == []
        assert impact.resolution_modified == [("foreshadow_02", 4)]

    def test_bidirectional_foreshadowing_impact_add_both_types(self) -> None:
        """両タイプ変更追加テスト"""
        impact = BidirectionalForeshadowingImpact(5)
        impact.add_setup_modified("foreshadow_01", 9)
        impact.add_resolution_modified("foreshadow_02", 2)
        impact.add_setup_modified("foreshadow_03", 11)

        assert impact.setup_modified == [("foreshadow_01", 9), ("foreshadow_03", 11)]
        assert impact.resolution_modified == [("foreshadow_02", 2)]

    def test_bidirectional_foreshadowing_impact_has_bidirectional_impact_none(self) -> None:
        """双方向影響なしテスト"""
        impact = BidirectionalForeshadowingImpact(1)
        assert impact.has_bidirectional_impact is False

    def test_bidirectional_foreshadowing_impact_has_bidirectional_impact_setup_only(self) -> None:
        """仕込み変更のみ双方向影響テスト"""
        impact = BidirectionalForeshadowingImpact(1)
        impact.add_setup_modified("foreshadow_01", 5)
        assert impact.has_bidirectional_impact is True

    def test_bidirectional_foreshadowing_impact_has_bidirectional_impact_resolution_only(self) -> None:
        """回収変更のみ双方向影響テスト"""
        impact = BidirectionalForeshadowingImpact(1)
        impact.add_resolution_modified("foreshadow_01", 3)
        assert impact.has_bidirectional_impact is True

    def test_bidirectional_foreshadowing_impact_has_bidirectional_impact_both(self) -> None:
        """両方の双方向影響テスト"""
        impact = BidirectionalForeshadowingImpact(1)
        impact.add_setup_modified("foreshadow_01", 5)
        impact.add_resolution_modified("foreshadow_02", 3)
        assert impact.has_bidirectional_impact is True

    def test_bidirectional_foreshadowing_impact_impact_summary_none(self) -> None:
        """影響なしサマリーテスト"""
        impact = BidirectionalForeshadowingImpact(4)
        assert impact.impact_summary == "ch04 - "

    def test_bidirectional_foreshadowing_impact_impact_summary_setup_only(self) -> None:
        """仕込み変更のみサマリーテスト"""
        impact = BidirectionalForeshadowingImpact(2)
        impact.add_setup_modified("foreshadow_01", 6)
        impact.add_setup_modified("foreshadow_02", 8)

        assert impact.impact_summary == "ch02 - 仕込み変更: 2件"

    def test_bidirectional_foreshadowing_impact_impact_summary_resolution_only(self) -> None:
        """回収変更のみサマリーテスト"""
        impact = BidirectionalForeshadowingImpact(7)
        impact.add_resolution_modified("foreshadow_01", 3)

        assert impact.impact_summary == "ch07 - 回収変更: 1件"

    def test_bidirectional_foreshadowing_impact_impact_summary_both(self) -> None:
        """両方の変更サマリーテスト"""
        impact = BidirectionalForeshadowingImpact(3)
        impact.add_setup_modified("foreshadow_01", 7)
        impact.add_setup_modified("foreshadow_02", 9)
        impact.add_resolution_modified("foreshadow_03", 1)

        assert impact.impact_summary == "ch03 - 仕込み変更: 2件, 回収変更: 1件"


class TestChangeScope:
    """ChangeScope(Enum)のテストクラス"""

    def test_change_scope_values(self) -> None:
        """変更スコープ値テスト"""
        assert ChangeScope.MAJOR.value == "major"
        assert ChangeScope.MINOR.value == "minor"
        assert ChangeScope.PATCH.value == "patch"

    def test_change_scope_enum_count(self) -> None:
        """変更スコープ数テスト"""
        assert len(ChangeScope) == 3

    def test_change_scope_membership(self) -> None:
        """変更スコープメンバーシップテスト"""
        assert ChangeScope.MAJOR in ChangeScope
        assert ChangeScope.MINOR in ChangeScope
        assert ChangeScope.PATCH in ChangeScope


class TestVersionCalculator:
    """VersionCalculator値オブジェクトのテストクラス"""

    @pytest.fixture
    def calculator(self) -> VersionCalculator:
        """バージョン計算器"""
        return VersionCalculator()

    def test_version_calculator_calculate_next_version_major(self, calculator: VersionCalculator) -> None:
        """メジャーバージョン計算テスト"""
        assert calculator.calculate_next_version("v1.2.3", "major") == "v2.0.0"
        assert calculator.calculate_next_version("v0.5.10", "major") == "v1.0.0"
        assert calculator.calculate_next_version("v10.0.0", "major") == "v11.0.0"

    def test_version_calculator_calculate_next_version_minor(self, calculator: VersionCalculator) -> None:
        """マイナーバージョン計算テスト"""
        assert calculator.calculate_next_version("v1.2.3", "minor") == "v1.3.0"
        assert calculator.calculate_next_version("v2.0.5", "minor") == "v2.1.0"
        assert calculator.calculate_next_version("v0.99.0", "minor") == "v0.100.0"

    def test_version_calculator_calculate_next_version_patch(self, calculator: VersionCalculator) -> None:
        """パッチバージョン計算テスト"""
        assert calculator.calculate_next_version("v1.2.3", "patch") == "v1.2.4"
        assert calculator.calculate_next_version("v1.0.0", "patch") == "v1.0.1"
        assert calculator.calculate_next_version("v5.10.99", "patch") == "v5.10.100"

    def test_version_calculator_calculate_next_version_invalid_type_error(self, calculator: VersionCalculator) -> None:
        """無効なバージョンタイプエラーテスト"""
        with pytest.raises(InvalidVersionError, match="Unknown version type: invalid"):
            calculator.calculate_next_version("v1.0.0", "invalid")

    def test_version_calculator_parse_version_valid(self, calculator: VersionCalculator) -> None:
        """有効なバージョン解析テスト"""
        assert calculator._parse_version("v1.2.3") == (1, 2, 3)
        assert calculator._parse_version("v0.0.1") == (0, 0, 1)
        assert calculator._parse_version("v10.20.30") == (10, 20, 30)

    def test_version_calculator_parse_version_invalid_format_error(self, calculator: VersionCalculator) -> None:
        """無効なバージョン形式エラーテスト"""
        invalid_versions = [
            "1.2.3",  # vプレフィックスなし
            "v1.2",  # パッチ番号なし
            "v1.2.3.4",  # 追加番号
            "va.b.c",  # 非数値
            "v1.2.3-dev",  # サフィックス
            "v-1.0.0",  # 負の数値
            "",  # 空文字列
            "invalid",  # 完全に無効
        ]

        for invalid_version in invalid_versions:
            with pytest.raises(InvalidVersionError, match=f"Invalid version format: {re.escape(invalid_version)}"):
                calculator._parse_version(invalid_version)

    def test_version_calculator_edge_cases(self, calculator: VersionCalculator) -> None:
        """バージョン計算器エッジケーステスト"""
        # 大きな数値
        assert calculator.calculate_next_version("v999.999.999", "major") == "v1000.0.0"
        assert calculator.calculate_next_version("v999.999.999", "minor") == "v999.1000.0"
        assert calculator.calculate_next_version("v999.999.999", "patch") == "v999.999.1000"

        # 0からの開始
        assert calculator.calculate_next_version("v0.0.0", "major") == "v1.0.0"
        assert calculator.calculate_next_version("v0.0.0", "minor") == "v0.1.0"
        assert calculator.calculate_next_version("v0.0.0", "patch") == "v0.0.1"
