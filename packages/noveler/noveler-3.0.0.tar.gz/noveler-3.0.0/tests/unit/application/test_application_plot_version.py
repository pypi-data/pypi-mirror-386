#!/usr/bin/env python3
"""プロットバージョン管理アプリケーション層のテスト
ユースケースのテスト


仕様書: SPEC-UNIT-TEST
"""

import sys

import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.application.use_cases.plot_version_use_cases import (
    CheckManuscriptStatusUseCase,
    CreatePlotVersionUseCase,
)
from noveler.domain.value_objects.project_time import ProjectTimezone

JST = ProjectTimezone.jst().timezone
from noveler.domain.entities.plot_version_entities import ManuscriptPlotLink, PlotVersion

# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()


class TestCreatePlotVersionUseCase(unittest.TestCase):
    """新しいプロットバージョン作成のユースケーステスト"""

    def setUp(self) -> None:
        """テストのセットアップ"""

        self.mock_repo = Mock()
        self.use_case = CreatePlotVersionUseCase(self.mock_repo)

    @pytest.mark.spec("SPEC-APPLICATION_PLOT_VERSION-CREATE_INITIAL_VERSI")
    def test_create_initial_version(self) -> None:
        """初版プロットバージョンを作成できる"""
        # Arrange
        self.mock_repo.get_current.return_value = None

        # Act
        result = self.use_case.execute(
            version_number="v1.0.0",
            author="作者名",
            major_changes=["初版プロット作成"],
            affected_chapters=[],
        )

        # Assert
        assert result.success
        assert result.version.version_number == "v1.0.0"
        self.mock_repo.save.assert_called_once()

    @pytest.mark.spec("SPEC-APPLICATION_PLOT_VERSION-CREATE_NEW_VERSION_W")
    def test_create_new_version_with_git_info(self) -> None:
        """Git情報を含む新バージョンを作成できる"""

        # Arrange
        current = PlotVersion("v1.0.0", datetime.now(JST), "", [], [])
        self.mock_repo.get_current.return_value = current

        # Act
        with patch("noveler.application.use_cases.plot_version_use_cases.GitService") as mock_git:
            mock_git.return_value.create_tag.return_value = True
            mock_git.return_value.get_commit_range.return_value = "abc123..def456"

            result = self.use_case.execute(
                version_number="v1.1.0",
                author="作者名",
                major_changes=["ch03変更"],
                affected_chapters=[3],
            )

        # Assert
        assert result.success
        assert result.version.previous_version == current


class TestLinkManuscriptUseCase(unittest.TestCase):
    """原稿とプロットバージョンの紐付けユースケーステスト"""

    def setUp(self) -> None:
        self.mock_plot_repo = Mock()
        self.mock_link_repo = Mock()
        self.use_case = LinkManuscriptUseCase(self.mock_plot_repo, self.mock_link_repo)

    @pytest.mark.spec("SPEC-APPLICATION_PLOT_VERSION-LINK_MANUSCRIPT_TO_C")
    def test_link_manuscript_to_current_version(self) -> None:
        """原稿を現在のプロットバージョンに紐付けできる"""

        # Arrange
        current = PlotVersion("v1.1.0", datetime.now(JST), "", [], [])
        self.mock_plot_repo.get_current.return_value = current

        # Act
        with patch("noveler.application.use_cases.plot_version_use_cases.GitService") as mock_git:
            mock_git.return_value.get_current_commit.return_value = "abc123"

            result = self.use_case.execute(episode_number="005", plot_version_number=None)  # 現在のバージョンを使用

        # Assert
        assert result.success
        assert result.link.plot_version.version_number == "v1.1.0"
        self.mock_link_repo.save.assert_called_once()


class TestCompareVersionsUseCase(unittest.TestCase):
    """プロットバージョン比較のユースケーステスト"""

    def setUp(self) -> None:
        self.mock_repo = Mock()
        self.use_case = CompareVersionsUseCase(self.mock_repo)

    @pytest.mark.spec("SPEC-APPLICATION_PLOT_VERSION-COMPARE_TWO_VERSIONS")
    def test_compare_two_versions(self) -> None:
        """2つのバージョンを比較できる"""

        # Arrange
        v1 = PlotVersion("v1.0.0", datetime(2024, 1, 15, tzinfo=JST), "", [], [])
        v2 = PlotVersion("v1.1.0", datetime(2024, 2, 20, tzinfo=JST), "", ["ch03変更"], [3])
        self.mock_repo.find_by_version.side_effect = lambda v: v1 if v == "v1.0.0" else v2

        # Act
        git_service_mock = Mock()
        git_service_mock.get_diff.return_value = {
            "files": ["20_プロット/章別プロット/chapter03.yaml"],
            "additions": 50,
            "deletions": 20,
        }
        self.use_case._git_service_cls = Mock(return_value=git_service_mock)

        result = self.use_case.execute("v1.0.0", "v1.1.0")

        # Assert
        assert result.success
        assert len(result.changed_files) == 1
        assert result.changeset.from_version == v1
        assert result.changeset.to_version == v2


class TestCheckManuscriptStatusUseCase(unittest.IsolatedAsyncioTestCase):
    """原稿の更新状況確認ユースケーステスト"""

    def setUp(self) -> None:
        from unittest.mock import AsyncMock
        from noveler.application.use_cases.plot_version_use_cases import ManuscriptStatus
        self.mock_episode_repo = AsyncMock()
        self.mock_plot_repo = AsyncMock()
        self.mock_quality_repo = AsyncMock()
        self.use_case = CheckManuscriptStatusUseCase(
            episode_repository=self.mock_episode_repo,
            plot_repository=self.mock_plot_repo,
            quality_repository=self.mock_quality_repo
        )
        self.use_case._determine_manuscript_status = AsyncMock(return_value=ManuscriptStatus.IN_PROGRESS)
        self.use_case._perform_detailed_analysis = AsyncMock(return_value={})
        self.use_case._get_word_count = AsyncMock(return_value=0)
        self.use_case._get_last_modified = AsyncMock(return_value=datetime.now(JST).isoformat())

    @pytest.mark.spec("SPEC-APPLICATION_PLOT_VERSION-CHECK_OUTDATED_MANUS")
    async def test_check_outdated_manuscript(self) -> None:
        """古いプロットで実装された原稿を検出できる"""

        # Arrange
        from unittest.mock import MagicMock
        mock_episode = MagicMock()
        mock_episode.number = 25
        mock_episode.content = "Test manuscript content"
        mock_episode.last_modified = datetime(2024, 1, 20, tzinfo=JST)

        self.mock_episode_repo.find_by_number.return_value = mock_episode

        mock_plot_data = MagicMock()
        mock_plot_data.version = "v1.1.0"
        self.mock_plot_repo.find_by_episode_number.return_value = mock_plot_data

        # Act
        from noveler.application.use_cases.plot_version_use_cases import CheckManuscriptStatusRequest
        request = CheckManuscriptStatusRequest(
            project_id="test_project",
            episode_number=25,
            check_plot_version=True,
            detailed_analysis=False
        )
        result = await self.use_case.execute(request)

        # Assert
        assert result.success is True
        assert result.plot_version == "v1.1.0"


if __name__ == "__main__":
    unittest.main()
