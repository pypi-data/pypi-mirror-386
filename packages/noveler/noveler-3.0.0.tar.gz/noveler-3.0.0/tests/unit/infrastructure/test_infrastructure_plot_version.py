#!/usr/bin/env python3
"""プロットバージョン管理インフラ層のテスト
Git連携と永続化のテスト


仕様書: SPEC-INFRASTRUCTURE
"""

import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from noveler.domain.entities.plot_version_entities import ManuscriptPlotLink, PlotVersion
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.infrastructure.adapters.git_service import GitService
from noveler.infrastructure.persistence.yaml_manuscript_link_repository import YamlManuscriptLinkRepository
from noveler.infrastructure.persistence.yaml_plot_version_repository import YamlPlotVersionRepository

# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports
from noveler.presentation.shared.shared_utilities import get_common_path_service

ensure_imports()


# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class TestYamlPlotVersionRepository(unittest.TestCase):
    """YAMLベースのリポジトリ実装テスト"""

    def setUp(self) -> None:
        """テスト用の一時ディレクトリを作成"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        shutil.rmtree(self.test_dir)

    def test_save_and_find_plot_version(self) -> None:
        """プロットバージョンを保存して検索できる"""

        # Arrange
        get_common_path_service()
        repo = YamlPlotVersionRepository(self.test_path)
        version = PlotVersion(
            version_number="v1.0.0",
            created_at=datetime(2024, 1, 15, tzinfo=ProjectTimezone.jst().timezone),
            author="テスト作者",
            major_changes=["初版作成"],
            affected_chapters=[],
            git_tag="plot-v1.0.0",
        )

        # Act
        repo.save(version)
        found = repo.find_by_version("v1.0.0")

        # Assert
        assert found is not None
        assert found.version_number == "v1.0.0"
        assert found.author == "テスト作者"

    def test_get_current_version(self) -> None:
        """現在のバージョンを取得できる"""

        # Arrange
        repo = YamlPlotVersionRepository(self.test_path)
        v1 = PlotVersion("v1.0.0", datetime(2024, 1, 15, tzinfo=ProjectTimezone.jst().timezone), "", [], [])
        v2 = PlotVersion("v1.1.0", datetime(2024, 2, 20, tzinfo=ProjectTimezone.jst().timezone), "", [], [])

        # Act
        repo.save(v1)
        repo.save(v2)
        current = repo.get_current()

        # Assert
        assert current.version_number == "v1.1.0"


class TestGitService(unittest.TestCase):
    """Git連携サービスのテスト"""

    @patch("subprocess.run")
    def test_create_git_tag(self, mock_run: object) -> None:
        """Gitタグを作成できる"""

        # Arrange
        mock_run.return_value = MagicMock(returncode=0)
        service = GitService(Path("/test/project"))

        # Act
        result = service.create_tag("plot-v1.0.0", "Version 1.0.0")

        # Assert
        assert result
        mock_run.assert_called()

    @patch("subprocess.run")
    def test_get_diff_between_versions(self, mock_run: object) -> None:
        """バージョン間の差分を取得できる"""

        # Arrange
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="20_プロット/章別プロット/chapter03.yaml\n30_設定集/キャラクター.yaml",
        )

        service = GitService(Path("/test/project"))

        # Act
        path_service = get_common_path_service()
        diff = service.get_diff("plot-v1.0.0", "plot-v1.1.0", str(path_service.get_plots_dir()))

        # Assert
        assert len(diff["files"]) == 2
        assert "20_プロット/章別プロット/chapter03.yaml" in diff["files"]

    @patch("subprocess.run")
    def test_get_commit_hash(self, mock_run: object) -> None:
        """現在のコミットハッシュを取得できる"""

        # Arrange
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="abc123def456",
        )

        service = GitService(Path("/test/project"))

        # Act
        commit = service.get_current_commit()

        # Assert
        assert commit == "abc123def456"


class TestManuscriptPlotLinkRepository(unittest.TestCase):
    """原稿紐付けリポジトリのテスト"""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)

    def test_save_and_find_link(self) -> None:
        """紐付け情報を保存して検索できる"""

        # Arrange
        repo = YamlManuscriptLinkRepository(self.test_path)
        version = PlotVersion("v1.0.0", project_now().datetime, "", [], [])
        link = ManuscriptPlotLink(
            episode_number="005",
            plot_version=version,
            implementation_date=datetime(2024, 1, 20, tzinfo=ProjectTimezone.jst().timezone),
            git_commit="abc123",
        )

        # Act
        repo.save(link)
        found = repo.find_by_episode("005")

        # Assert
        assert found is not None
        assert found.episode_number == "005"
        assert found.plot_version.version_number == "v1.0.0"

    def test_find_outdated_manuscripts(self) -> None:
        """古いバージョンの原稿を検索できる"""

        # Arrange
        repo = YamlManuscriptLinkRepository(self.test_path)
        v1 = PlotVersion("v1.0.0", datetime(2024, 1, 15, tzinfo=ProjectTimezone.jst().timezone), "", [], [])
        v2 = PlotVersion("v1.1.0", datetime(2024, 2, 20, tzinfo=ProjectTimezone.jst().timezone), "", [], [])

        link1 = ManuscriptPlotLink("001", v1, datetime(2024, 1, 20, tzinfo=ProjectTimezone.jst().timezone), "abc")
        link2 = ManuscriptPlotLink("002", v2, datetime(2024, 2, 25, tzinfo=ProjectTimezone.jst().timezone), "def")

        repo.save(link1)
        repo.save(link2)

        # Act
        outdated = repo.find_outdated(v2)

        # Assert
        assert len(outdated) == 1
        assert outdated[0].episode_number == "001"


if __name__ == "__main__":
    unittest.main()
