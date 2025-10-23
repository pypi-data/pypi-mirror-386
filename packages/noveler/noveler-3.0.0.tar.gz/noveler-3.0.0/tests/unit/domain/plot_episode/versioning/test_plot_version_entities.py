"""プロットバージョン管理ドメインエンティティのテスト

TDD準拠テスト:
    - PlotVersion
    - ManuscriptPlotLink
    - PlotChangeSet


仕様書: SPEC-UNIT-TEST
"""

from datetime import datetime

import pytest

pytestmark = pytest.mark.plot_episode

from noveler.domain.entities.plot_version_entities import (
    ManuscriptPlotLink,
    PlotChangeSet,
    PlotVersion,
)
from noveler.domain.exceptions import InvalidVersionError
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestPlotVersion:
    """PlotVersionのテストクラス"""

    @pytest.fixture
    def base_version(self) -> PlotVersion:
        """基本バージョンv1.0.0"""
        return PlotVersion(
            version_number="v1.0.0",
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=JST),
            author="test_author",
            major_changes=["初版作成"],
            affected_chapters=[1, 2],
        )

    @pytest.fixture
    def minor_version(self, base_version: PlotVersion) -> PlotVersion:
        """マイナーバージョンアップv1.1.0"""
        return PlotVersion(
            version_number="v1.1.0",
            created_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=JST),
            author="test_author",
            major_changes=["新キャラクター追加", "サブプロット追加"],
            affected_chapters=[3, 4],
            previous_version=base_version,
        )

    @pytest.fixture
    def major_version(self, minor_version: PlotVersion) -> PlotVersion:
        """メジャーバージョンアップv2.0.0"""
        return PlotVersion(
            version_number="v2.0.0",
            created_at=datetime(2024, 2, 1, 12, 0, 0, tzinfo=JST),
            author="test_author",
            major_changes=["ストーリー大幅変更", "設定刷新"],
            affected_chapters=[1, 2, 3, 4, 5],
            previous_version=minor_version,
        )

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-VALID_VERSION_NUMBER")
    def test_valid_version_number_creation(self, base_version: PlotVersion) -> None:
        """有効なバージョン番号での作成テスト"""
        assert base_version.version_number == "v1.0.0"
        assert base_version.author == "test_author"
        assert len(base_version.major_changes) == 1

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-INVALID_VERSION_NUMB")
    def test_invalid_version_number_raises_error(self) -> None:
        """無効なバージョン番号でのエラーテスト"""
        invalid_versions = [
            "1.0.0",  # v プレフィックスなし
            "v1.0",  # パッチバージョンなし
            "v1.0.0.0",  # 余分なバージョン
            "va.b.c",  # 非数値
            "",  # 空文字
            "version1.0.0",  # 不正なプレフィックス
        ]

        for invalid_version in invalid_versions:
            with pytest.raises(InvalidVersionError, match="不正なバージョン番号"):
                PlotVersion(
                    version_number=invalid_version,
                    created_at=project_now().datetime,
                    author="test",
                    major_changes=[],
                    affected_chapters=[],
                )

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-IS_VALID_VERSION_NUM")
    def test_is_valid_version_number(self, base_version: PlotVersion) -> None:
        """バージョン番号検証メソッドテスト"""
        valid_versions = ["v1.0.0", "v10.5.23", "v0.0.1"]
        invalid_versions = ["1.0.0", "v1.0", "v1.0.0.0", "invalid"]

        for valid in valid_versions:
            assert base_version._is_valid_version_number(valid) is True

        for invalid in invalid_versions:
            assert base_version._is_valid_version_number(invalid) is False

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-PARSE_VERSION")
    def test_parse_version(self, base_version: PlotVersion) -> None:
        """バージョン番号パーステスト"""
        test_cases = [
            ("v1.0.0", (1, 0, 0)),
            ("v2.5.10", (2, 5, 10)),
            ("v0.1.0", (0, 1, 0)),
            ("v10.20.30", (10, 20, 30)),
        ]

        for version_str, expected_tuple in test_cases:
            assert base_version._parse_version(version_str) == expected_tuple

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-PARSE_VERSION_INVALI")
    def test_parse_version_invalid(self, base_version: PlotVersion) -> None:
        """無効バージョンのパーステスト"""
        invalid_versions = ["invalid", "v1.0", "1.0.0"]

        for invalid in invalid_versions:
            assert base_version._parse_version(invalid) == (0, 0, 0)

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-IS_NEWER_THAN_TRUE")
    def test_is_newer_than_true(self, base_version: PlotVersion, minor_version: PlotVersion) -> None:
        """より新しいバージョンの比較テスト"""
        assert minor_version.is_newer_than(base_version) is True

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-IS_NEWER_THAN_FALSE")
    def test_is_newer_than_false(self, base_version: PlotVersion, minor_version: PlotVersion) -> None:
        """より古いバージョンの比較テスト"""
        assert base_version.is_newer_than(minor_version) is False

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-IS_NEWER_THAN_SAME_V")
    def test_is_newer_than_same_version(self, base_version: PlotVersion) -> None:
        """同じバージョンの比較テスト"""
        same_version = PlotVersion(
            version_number="v1.0.0",
            created_at=project_now().datetime,
            author="another_author",
            major_changes=["different changes"],
            affected_chapters=[],
        )

        assert base_version.is_newer_than(same_version) is False
        assert same_version.is_newer_than(base_version) is False

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-IS_NEWER_THAN_COMPLE")
    def test_is_newer_than_complex_versions(self) -> None:
        """複雑なバージョン比較テスト"""
        v1_0_0 = PlotVersion("v1.0.0", project_now().datetime, "author", [], [])
        v1_0_1 = PlotVersion("v1.0.1", project_now().datetime, "author", [], [])
        v1_1_0 = PlotVersion("v1.1.0", project_now().datetime, "author", [], [])
        v2_0_0 = PlotVersion("v2.0.0", project_now().datetime, "author", [], [])

        # パッチバージョン比較
        assert v1_0_1.is_newer_than(v1_0_0) is True

        # マイナーバージョン比較
        assert v1_1_0.is_newer_than(v1_0_1) is True

        # メジャーバージョン比較
        assert v2_0_0.is_newer_than(v1_1_0) is True

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-IS_INITIAL_VERSION_T")
    def test_is_initial_version_true(self, base_version: PlotVersion) -> None:
        """初版判定(True)テスト"""
        assert base_version.is_initial_version() is True

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-IS_INITIAL_VERSION_F")
    def test_is_initial_version_false(self, minor_version: PlotVersion) -> None:
        """初版判定(False)テスト"""
        assert minor_version.is_initial_version() is False

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-GET_SEMANTIC_VERSION")
    def test_get_semantic_version_type_initial(self, base_version: PlotVersion) -> None:
        """初版のセマンティックバージョンタイプテスト"""
        assert base_version.get_semantic_version_type() == "initial"

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-GET_SEMANTIC_VERSION")
    def test_get_semantic_version_type_patch(self, base_version: PlotVersion) -> None:
        """パッチバージョンアップのタイプテスト"""
        patch_version = PlotVersion(
            version_number="v1.0.1",
            created_at=project_now().datetime,
            author="test_author",
            major_changes=["バグ修正"],
            affected_chapters=[],
            previous_version=base_version,
        )

        assert patch_version.get_semantic_version_type() == "patch"

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-GET_SEMANTIC_VERSION")
    def test_get_semantic_version_type_minor(self, minor_version: PlotVersion) -> None:
        """マイナーバージョンアップのタイプテスト"""
        assert minor_version.get_semantic_version_type() == "minor"

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-GET_SEMANTIC_VERSION")
    def test_get_semantic_version_type_major(self, major_version: PlotVersion) -> None:
        """メジャーバージョンアップのタイプテスト"""
        assert major_version.get_semantic_version_type() == "major"

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-VERSION_WITH_GIT_MET")
    def test_version_with_git_metadata(self) -> None:
        """Git メタデータ付きバージョンテスト"""
        version_with_git = PlotVersion(
            version_number="v1.0.0",
            created_at=project_now().datetime,
            author="test_author",
            major_changes=["Git統合版"],
            affected_chapters=[1],
            git_tag="v1.0.0",
            git_commit_range="abc123..def456",
        )

        assert version_with_git.git_tag == "v1.0.0"
        assert version_with_git.git_commit_range == "abc123..def456"


class TestManuscriptPlotLink:
    """ManuscriptPlotLinkのテストクラス"""

    @pytest.fixture
    def old_version(self) -> PlotVersion:
        """古いバージョン"""
        return PlotVersion(
            version_number="v1.0.0",
            created_at=datetime(2024, 1, 1, tzinfo=JST),
            author="author",
            major_changes=["初版"],
            affected_chapters=[1, 2],
        )

    @pytest.fixture
    def new_version(self, old_version: PlotVersion) -> PlotVersion:
        """新しいバージョン"""
        return PlotVersion(
            version_number="v1.1.0",
            created_at=datetime(2024, 1, 15, tzinfo=JST),
            author="author",
            major_changes=["改訂版"],
            affected_chapters=[2, 3],
            previous_version=old_version,
        )

    @pytest.fixture
    def manuscript_link(self, old_version: PlotVersion) -> ManuscriptPlotLink:
        """原稿プロットリンク"""
        return ManuscriptPlotLink(
            episode_number="005",
            plot_version=old_version,
            implementation_date=datetime(2024, 1, 10, tzinfo=JST),
            git_commit="abc123",
        )

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-MANUSCRIPT_LINK_CREA")
    def test_manuscript_link_creation(self, manuscript_link: ManuscriptPlotLink) -> None:
        """原稿プロットリンク作成テスト"""
        assert manuscript_link.episode_number == "005"
        assert manuscript_link.git_commit == "abc123"
        assert manuscript_link.plot_snapshot is None

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-MANUSCRIPT_LINK_WITH")
    def test_manuscript_link_with_snapshot(self, old_version: PlotVersion) -> None:
        """スナップショット付きリンクテスト"""
        snapshot = {"chapter": 1, "scene": "opening"}
        link_with_snapshot = ManuscriptPlotLink(
            episode_number="001",
            plot_version=old_version,
            implementation_date=project_now().datetime,
            git_commit="def456",
            plot_snapshot=snapshot,
        )

        assert link_with_snapshot.plot_snapshot == snapshot

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-IS_OUTDATED_FOR_TRUE")
    def test_is_outdated_for_true(self, manuscript_link: ManuscriptPlotLink, new_version: PlotVersion) -> None:
        """古くなったリンクの判定(True)テスト"""
        assert manuscript_link.is_outdated_for(new_version) is True

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-IS_OUTDATED_FOR_FALS")
    def test_is_outdated_for_false(self, manuscript_link: ManuscriptPlotLink, old_version: PlotVersion) -> None:
        """古くなったリンクの判定(False)テスト"""
        assert manuscript_link.is_outdated_for(old_version) is False

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-GET_CHAPTER_NUMBER_V")
    def test_get_chapter_number_valid_episode(self, manuscript_link: ManuscriptPlotLink) -> None:
        """有効エピソード番号からの章番号計算テスト"""
        test_cases = [
            ("001", 1),  # 1-10話はch01
            ("005", 1),
            ("010", 1),
            ("011", 2),  # 11-20話はch02
            ("015", 2),
            ("020", 2),
            ("021", 3),  # 21-30話はch03
            ("100", 10),  # 91-100話はch10
        ]

        for episode_num, expected_chapter in test_cases:
            link = ManuscriptPlotLink(
                episode_number=episode_num,
                plot_version=manuscript_link.plot_version,
                implementation_date=project_now().datetime,
                git_commit="test",
            )

            assert link.get_chapter_number() == expected_chapter

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-GET_CHAPTER_NUMBER_I")
    def test_get_chapter_number_invalid_episode(self, old_version: PlotVersion) -> None:
        """無効エピソード番号での章番号計算テスト"""
        invalid_link = ManuscriptPlotLink(
            episode_number="invalid",
            plot_version=old_version,
            implementation_date=project_now().datetime,
            git_commit="test",
        )

        assert invalid_link.get_chapter_number() == 0

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-IS_AFFECTED_BY_VERSI")
    def test_is_affected_by_version_true(self, manuscript_link: ManuscriptPlotLink) -> None:
        """バージョン変更の影響を受ける判定(True)テスト"""
        # エピソード005はch01、affected_chapters=[1,2]に含まれる
        affecting_version = PlotVersion(
            version_number="v1.1.0",
            created_at=project_now().datetime,
            author="author",
            major_changes=["ch01変更"],
            affected_chapters=[1, 3],  # ch01が含まれている
        )

        assert manuscript_link.is_affected_by_version(affecting_version) is True

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-IS_AFFECTED_BY_VERSI")
    def test_is_affected_by_version_false(self, manuscript_link: ManuscriptPlotLink) -> None:
        """バージョン変更の影響を受けない判定(False)テスト"""
        # エピソード005はch01、affected_chapters=[2,3]に含まれない
        non_affecting_version = PlotVersion(
            version_number="v1.1.0",
            created_at=project_now().datetime,
            author="author",
            major_changes=["第2,3章変更"],
            affected_chapters=[2, 3],  # ch01が含まれていない
        )

        assert manuscript_link.is_affected_by_version(non_affecting_version) is False


class TestPlotChangeSet:
    """PlotChangeSetのテストクラス"""

    @pytest.fixture
    def from_version(self) -> PlotVersion:
        """変更前バージョン"""
        return PlotVersion(
            version_number="v1.0.0",
            created_at=datetime(2024, 1, 1, tzinfo=JST),
            author="author",
            major_changes=["初版"],
            affected_chapters=[1, 2],
        )

    @pytest.fixture
    def to_version(self, from_version: PlotVersion) -> PlotVersion:
        """変更後バージョン"""
        return PlotVersion(
            version_number="v1.1.0",
            created_at=datetime(2024, 1, 15, tzinfo=JST),
            author="author",
            major_changes=["マイナー更新"],
            affected_chapters=[2, 3],
            previous_version=from_version,
        )

    @pytest.fixture
    def changeset(self, from_version: PlotVersion, to_version: PlotVersion) -> PlotChangeSet:
        """プロット変更セット"""
        return PlotChangeSet(
            from_version=from_version, to_version=to_version, git_diff_files=["plot/chapter2.md", "plot/chapter3.md"]
        )

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-CHANGESET_CREATION")
    def test_changeset_creation(self, changeset: PlotChangeSet) -> None:
        """変更セット作成テスト"""
        assert changeset.from_version.version_number == "v1.0.0"
        assert changeset.to_version.version_number == "v1.1.0"
        assert len(changeset.git_diff_files) == 2

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-CHANGESET_CREATION_W")
    def test_changeset_creation_without_git_files(self, from_version: PlotVersion, to_version: PlotVersion) -> None:
        """Git ファイルなしでの変更セット作成テスト"""
        changeset_no_git = PlotChangeSet(from_version=from_version, to_version=to_version)

        assert changeset_no_git.git_diff_files == []

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-HAS_CHANGES_TRUE")
    def test_has_changes_true(self, changeset: PlotChangeSet) -> None:
        """変更があることの判定(True)テスト"""
        assert changeset.has_changes() is True

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-HAS_CHANGES_FALSE")
    def test_has_changes_false(self, from_version: PlotVersion) -> None:
        """変更がないことの判定(False)テスト"""
        same_version_changeset = PlotChangeSet(
            from_version=from_version,
            to_version=from_version,  # 同じバージョン
        )

        assert same_version_changeset.has_changes() is False

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-GET_AFFECTED_EPISODE")
    def test_get_affected_episode_numbers(self, changeset: PlotChangeSet) -> None:
        """影響を受けるエピソード番号取得テスト"""
        affected_episodes = changeset.get_affected_episode_numbers()

        # affected_chapters=[2, 3] → エピソード11-20, 21-30
        expected_episode_numbers = set(range(11, 31))
        assert {int(ep) for ep in affected_episodes} == expected_episode_numbers

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-GET_AFFECTED_EPISODE")
    def test_get_affected_episode_numbers_no_affected_chapters(self, from_version: PlotVersion) -> None:
        """影響章なしでのエピソード番号取得テスト"""
        no_affected_version = PlotVersion(
            version_number="v1.0.1",
            created_at=project_now().datetime,
            author="author",
            major_changes=["パッチ更新"],
            affected_chapters=[],  # 影響章なし
        )

        changeset_no_affected = PlotChangeSet(from_version=from_version, to_version=no_affected_version)

        affected_episodes = changeset_no_affected.get_affected_episode_numbers()
        assert affected_episodes == []

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-GET_AFFECTED_EPISODE")
    def test_get_affected_episode_numbers_multiple_chapters(self) -> None:
        """複数章での影響エピソード取得テスト"""
        from_ver = PlotVersion("v1.0.0", project_now().datetime, "author", [], [])
        to_ver = PlotVersion("v2.0.0", project_now().datetime, "author", ["大幅変更"], [1, 5, 10])

        changeset_multi = PlotChangeSet(from_version=from_ver, to_version=to_ver)
        affected_episodes = changeset_multi.get_affected_episode_numbers()

        # ch01: 1-10, ch05: 41-50, ch10: 91-100
        expected_count = 10 + 10 + 10  # 30エピソード
        assert len(affected_episodes) == expected_count
        affected_numbers = {int(ep) for ep in affected_episodes}
        assert len(affected_numbers) == expected_count

        # 代表的なエピソードが含まれているかチェック
        assert {1, 5, 41, 50, 91, 100}.issubset(affected_numbers)

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-GET_VERSION_PATH_SIM")
    def test_get_version_path_simple(self, changeset: PlotChangeSet) -> None:
        """単純なバージョン経路取得テスト"""
        path = changeset.get_version_path()

        assert len(path) == 2
        assert path[0] == changeset.from_version
        assert path[1] == changeset.to_version

    @pytest.mark.spec("SPEC-PLOT_VERSION_ENTITIES-GET_VERSION_PATH_SAM")
    def test_get_version_path_same_versions(self, from_version: PlotVersion) -> None:
        """同一バージョン間の経路取得テスト"""
        same_changeset = PlotChangeSet(from_version=from_version, to_version=from_version)

        path = same_changeset.get_version_path()

        assert len(path) == 2
        assert path[0] == from_version
        assert path[1] == from_version
