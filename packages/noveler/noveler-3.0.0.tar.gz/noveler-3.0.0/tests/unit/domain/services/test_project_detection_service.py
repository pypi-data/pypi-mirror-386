"""プロジェクト検出サービスのテスト

仕様書: SPEC-DOMAIN-SERVICES
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from noveler.domain.exceptions import ProjectNotFoundError
from noveler.domain.services.project_detection_service import ProjectDetectionService
from noveler.domain.value_objects.project_info import ProjectInfo


class TestProjectDetectionService:
    """プロジェクト検出サービスのテスト

    仕様書: SPEC-DOMAIN-SERVICES
    """

    @patch("pathlib.Path.open")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    @patch("yaml.safe_load")
    def test_detect_project_in_current_directory(
        self, mock_yaml_load: object, mock_is_file: object, mock_exists: object, mock_path_open: object
    ) -> None:
        """現在のディレクトリでプロジェクトを検出"""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_yaml_load.return_value = {"title": "テスト小説", "author": "テスト作者"}

        service = ProjectDetectionService()
        project_info = service.detect()

        assert project_info.name == "テスト小説"
        assert project_info.root_path == Path.cwd()
        assert project_info.config_path == Path.cwd() / "プロジェクト設定.yaml"

    @patch("pathlib.Path.open")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    @patch("yaml.safe_load")
    def test_detect_project_in_parent_directory(
        self, mock_yaml_load: object, mock_is_file: object, mock_exists: object, mock_path_open: object
    ) -> None:
        """親ディレクトリでプロジェクトを検出"""
        # 現在のディレクトリには設定ファイルがない、親ディレクトリにある
        mock_exists.side_effect = [False, True]
        mock_is_file.return_value = True
        mock_yaml_load.return_value = {"title": "親ディレクトリ小説"}

        service = ProjectDetectionService()
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/test/child")

            project_info = service.detect()

            assert project_info.name == "親ディレクトリ小説"
            assert project_info.root_path == Path("/test")

    @patch("pathlib.Path.exists")
    def test_no_project_found_raises_error(self, mock_exists: object) -> None:
        """プロジェクトが見つからない場合エラー"""
        mock_exists.return_value = False

        service = ProjectDetectionService()
        with pytest.raises(ProjectNotFoundError) as exc_info:
            service.detect()

        assert "プロジェクト設定.yaml" in str(exc_info.value)

    @patch("pathlib.Path.open")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    @patch("yaml.safe_load")
    def test_detect_with_manuscript_folder(
        self, mock_yaml_load: object, mock_is_file: object, mock_exists: object, mock_path_open: object
    ) -> None:
        """40_原稿フォルダからの検出"""
        # current_pathをモック
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/project/40_原稿")
            # exists()の動作を設定(現在:False、親:True)
            mock_exists.side_effect = [False, True]
            mock_is_file.return_value = True
            mock_yaml_load.return_value = {"title": "原稿フォルダ内小説"}

            service = ProjectDetectionService()
            project_info = service.detect()

            assert project_info.name == "原稿フォルダ内小説"
            assert project_info.root_path == Path("/project")

    @pytest.mark.spec("SPEC-PROJECT_DETECTION_SERVICE-PROJECT_INFO_PROPERT")
    def test_project_info_properties(self) -> None:
        """ProjectInfo値オブジェクトのプロパティ"""

        info = ProjectInfo(
            name="テスト小説", root_path=Path("/test/project"), config_path=Path("/test/project/プロジェクト設定.yaml")
        )

        assert info.name == "テスト小説"
        assert info.root_path == Path("/test/project")
        assert info.config_path == Path("/test/project/プロジェクト設定.yaml")
        assert info.manuscript_path == Path("/test/project/40_原稿")
        assert info.management_path == Path("/test/project/50_管理資料")
