#!/usr/bin/env python3
"""プロットバージョン管理ドメインのテストスイート
TDDアプローチ: 失敗するテストを先に作成


仕様書: SPEC-UNIT-TEST
"""

import pytest
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
pytestmark = pytest.mark.plot_episode



from noveler.domain.entities.plot_version_entities import ManuscriptPlotLink, PlotChangeSet, PlotVersion
from noveler.domain.exceptions import InvalidVersionError
from noveler.domain.repositories import PlotVersionRepository
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# テスト対象のモジュールはまだ存在しない(RED段階)
# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestPlotVersionEntity(unittest.TestCase):
    """PlotVersionエンティティのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_VERSION-CREATE_PLOT_VERSION")
    def test_create_plot_version(self) -> None:
        """プロットバージョンを作成できる"""
        # Arrange & Act

        version = PlotVersion(
            version_number="v1.0.0",
            created_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
            author="作者名",
            major_changes=["初版プロット作成"],
            affected_chapters=[],
            git_tag="plot-v1.0.0",
        )

        # Assert
        assert version.version_number == "v1.0.0"
        assert version.author == "作者名"
        assert len(version.major_changes) == 1
        assert version.is_initial_version()

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_VERSION-VERSION_COMPARISON")
    def test_version_comparison(self) -> None:
        """バージョン番号を比較できる"""

        v1 = PlotVersion("v1.0.0", project_now().datetime, "", [], [])
        v2 = PlotVersion("v1.1.0", project_now().datetime, "", [], [])

        assert v2.is_newer_than(v1)
        assert not v1.is_newer_than(v2)

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_VERSION-INVALID_VERSION_NUMB")
    def test_invalid_version_number(self) -> None:
        """不正なバージョン番号は拒否される"""

        with pytest.raises(InvalidVersionError, match=".*"):
            PlotVersion("invalid", project_now().datetime, "", [], [])

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_VERSION-VERSION_WITH_PREVIOU")
    def test_version_with_previous(self) -> None:
        """前バージョンとの関連を持てる"""

        v1 = PlotVersion("v1.0.0", datetime(2024, 1, 15, tzinfo=timezone.utc), "", [], [])
        v2 = PlotVersion(
            "v1.1.0",
            datetime(2024, 2, 20, tzinfo=timezone.utc),
            "",
            ["ch03変更"],
            [3],
            previous_version=v1,
        )

        assert v2.previous_version == v1
        assert v2.affected_chapters == [3]


class TestManuscriptPlotLink(unittest.TestCase):
    """原稿とプロットの紐付けテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_VERSION-CREATE_MANUSCRIPT_LI")
    def test_create_manuscript_link(self) -> None:
        """原稿をプロットバージョンに紐付けできる"""

        version = PlotVersion("v1.0.0", project_now().datetime, "", [], [])
        link = ManuscriptPlotLink(
            episode_number="001",
            plot_version=version,
            implementation_date=datetime(2024, 1, 20, tzinfo=timezone.utc),
            git_commit="abc123",
        )

        assert link.episode_number == "001"
        assert link.plot_version.version_number == "v1.0.0"
        assert link.git_commit == "abc123"

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_VERSION-IS_OUTDATED")
    def test_is_outdated(self) -> None:
        """原稿が最新プロットに対して古いか判定できる"""

        v1 = PlotVersion("v1.0.0", datetime(2024, 1, 15, tzinfo=timezone.utc), "", [], [])
        v2 = PlotVersion("v1.1.0", datetime(2024, 2, 20, tzinfo=timezone.utc), "", ["変更"], [1])

        link = ManuscriptPlotLink("001", v1, datetime(2024, 1, 20, tzinfo=timezone.utc), "abc123")

        assert link.is_outdated_for(v2)
        assert not link.is_outdated_for(v1)


class TestPlotChangeSet(unittest.TestCase):
    """プロット変更セットのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_VERSION-CREATE_CHANGESET")
    def test_create_changeset(self) -> None:
        """バージョン間の変更セットを作成できる"""

        v1 = PlotVersion("v1.0.0", datetime(2024, 1, 15, tzinfo=timezone.utc), "", [], [])
        v2 = PlotVersion("v1.1.0", datetime(2024, 2, 20, tzinfo=timezone.utc), "", ["ch03変更"], [3])

        changeset = PlotChangeSet(from_version=v1, to_version=v2)

        assert changeset.from_version == v1
        assert changeset.to_version == v2
        assert changeset.has_changes()

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_VERSION-AFFECTED_EPISODES")
    def test_affected_episodes(self) -> None:
        """変更セットから影響を受けるエピソードを特定できる"""

        v1 = PlotVersion("v1.0.0", datetime(2024, 1, 15, tzinfo=timezone.utc), "", [], [])
        v2 = PlotVersion("v1.1.0", datetime(2024, 2, 20, tzinfo=timezone.utc), "", ["ch03変更"], [3])

        changeset = PlotChangeSet(v1, v2)

        # ch03は第21-30話に相当
        affected = changeset.get_affected_episode_numbers()
        normalized = {ep.lstrip("0") or "0" for ep in affected}
        assert "21" in normalized
        assert "30" in normalized
        assert "001" not in affected


class TestPlotVersionRepository(unittest.TestCase):
    """リポジトリインターフェースのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_PLOT_VERSION-REPOSITORY_INTERFACE")
    def test_repository_interface(self) -> None:
        """リポジトリインターフェースが定義されている"""

        # インターフェースの存在確認
        assert hasattr(PlotVersionRepository, "save")
        assert hasattr(PlotVersionRepository, "find_by_version")
        assert hasattr(PlotVersionRepository, "find_all")
        assert hasattr(PlotVersionRepository, "get_current")


if __name__ == "__main__":
    unittest.main()
