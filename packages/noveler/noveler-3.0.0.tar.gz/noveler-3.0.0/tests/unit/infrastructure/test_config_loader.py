#!/usr/bin/env python3
"""config_loader.pyのpytestテストケース

仕様書: SPEC-INFRASTRUCTURE
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import yaml

from noveler.infrastructure.adapters.config_loader_adapter import _repository

# 親ディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from noveler.infrastructure.adapters.config_loader_adapter import (
    find_project_config,
    get_author_info,
    get_config,
    get_ncode,
    get_project_info,
    get_project_paths,
    get_quality_threshold,
    load_project_config,
    setup_environment,
)


class TestFindProjectConfig:
    """find_project_config関数のテスト"""

    def test_find_project_config_current_dir(self, tmp_path: object) -> None:
        """現在のディレクトリに設定ファイルがある場合"""
        config_file = tmp_path / "プロジェクト設定.yaml"
        config_file.write_text("project: {}", encoding="utf-8")

        result = find_project_config(tmp_path)
        assert result == config_file

    def test_find_project_config_parent_dir(self, tmp_path: object) -> None:
        """親ディレクトリに設定ファイルがある場合"""
        config_file = tmp_path / "プロジェクト設定.yaml"
        config_file.write_text("project: {}", encoding="utf-8")

        subdir = tmp_path / "subdir"
        subdir.mkdir()

        result = find_project_config(subdir)
        assert result == config_file

    def test_find_project_config_not_found(self, tmp_path: object) -> None:
        """設定ファイルが見つからない場合"""
        result = find_project_config(tmp_path)
        assert result is None

    def test_find_project_config_default_path(self) -> None:
        """デフォルトパス(現在のディレクトリ)での検索"""
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/tmp/test")  # noqa: S108
            with patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = False
                result = find_project_config()
                assert result is None


class TestLoadProjectConfig:
    """load_project_config関数のテスト"""

    def test_load_project_config_success(self, tmp_path: object) -> None:
        """正常な設定ファイルの読み込み"""
        config_file = tmp_path / "プロジェクト設定.yaml"
        config_data = {
            "project": {"title": "テスト小説", "ncode": "n1234567890"},
            "author": {"pen_name": "テスト作者"},
        }
        config_file.write_text(yaml.dump(config_data, allow_unicode=True), encoding="utf-8")

        result = load_project_config(config_file)
        assert result["project"]["title"] == "テスト小説"
        assert result["author"]["pen_name"] == "テスト作者"

    def test_load_project_config_empty_file(self, tmp_path: object) -> None:
        """空のファイルの場合"""
        config_file = tmp_path / "プロジェクト設定.yaml"
        config_file.write_text("", encoding="utf-8")

        result = load_project_config(config_file)
        assert result == {}

    def test_load_project_config_invalid_yaml(self, tmp_path: object) -> None:
        """無効なYAMLファイルの場合"""
        config_file = tmp_path / "プロジェクト設定.yaml"
        config_file.write_text("invalid: yaml: content:", encoding="utf-8")

        result = load_project_config(config_file)
        assert result == {}

    def test_load_project_config_file_not_found(self, tmp_path: object) -> None:
        """ファイルが存在しない場合"""
        config_file = tmp_path / "nonexistent.yaml"

        result = load_project_config(config_file)
        assert result == {}

    @patch("noveler.infrastructure.repositories.configuration_repository.ConfigurationRepository.find_project_config")
    def test_load_project_config_auto_find(self, mock_find: object) -> None:
        """自動検索での設定ファイル読み込み"""
        mock_find.return_value = None

        result = load_project_config()
        assert result == {}
        mock_find.assert_called_once()


class TestGetProjectPaths:
    """get_project_paths関数のテスト"""

    def test_get_project_paths_from_env(self) -> None:
        """環境変数からパスを取得"""
        with patch.dict(
            "os.environ",
            {
                "PROJECT_ROOT": "/test/project",
                "GUIDE_ROOT": "/test/guide",
            },
        ):
            result = get_project_paths()
            assert result["project_root"] == "/test/project"
            assert result["guide_root"] == "/test/guide"

    def test_get_project_paths_from_env_no_guide(self) -> None:
        """環境変数でPROJECT_ROOTのみ設定"""
        with patch.dict("os.environ", {"PROJECT_ROOT": "/test/project"}, clear=True):
            result = get_project_paths()
            assert result["project_root"] == "/test/project"
            assert result["guide_root"] == "/test/00_ガイド"

    @patch("noveler.infrastructure.repositories.configuration_repository.ConfigurationRepository.load_project_config")
    def test_get_project_paths_from_config(self, mock_load: object) -> None:
        """設定ファイルからパスを取得"""
        mock_load.return_value = {
            "paths": {
                "project_root": "/config/project",
                "guide_root": "/config/guide",
            },
        }

        with patch.dict("os.environ", {}, clear=True):
            result = get_project_paths()
            assert result["project_root"] == "/config/project"
            assert result["guide_root"] == "/config/guide"

    @patch("noveler.infrastructure.repositories.configuration_repository.ConfigurationRepository.load_project_config")
    def test_get_project_paths_from_config_no_guide(self, mock_load: object) -> None:
        """設定ファイルでproject_rootのみ設定"""
        mock_load.return_value = {
            "paths": {
                "project_root": "/config/project",
            },
        }

        with patch.dict("os.environ", {}, clear=True):
            result = get_project_paths()
            assert result["project_root"] == "/config/project"
            assert result["guide_root"] == "/config/00_ガイド"

    @patch("noveler.infrastructure.repositories.configuration_repository.ConfigurationRepository.find_project_config")
    @patch("noveler.infrastructure.repositories.configuration_repository.ConfigurationRepository.load_project_config")
    def test_get_project_paths_from_discovery(self, mock_load: object, mock_find: object) -> None:
        """プロジェクト発見からパスを取得"""
        mock_load.return_value = {}
        mock_find.return_value = Path("/discovered/project/プロジェクト設定.yaml")

        with patch.dict("os.environ", {}, clear=True):
            result = get_project_paths()
            assert result["project_root"] == "/discovered/project"
            assert result["guide_root"] == "/discovered/00_ガイド"

    @patch("noveler.infrastructure.repositories.configuration_repository.ConfigurationRepository.find_project_config")
    @patch("noveler.infrastructure.repositories.configuration_repository.ConfigurationRepository.load_project_config")
    def test_get_project_paths_none_found(self, mock_load: object, mock_find: object) -> None:
        """何も見つからない場合"""
        mock_load.return_value = {}
        mock_find.return_value = None

        with patch.dict("os.environ", {}, clear=True):
            result = get_project_paths()
            assert result == {}


class TestSetupEnvironment:
    """setup_environment関数のテスト"""

    @patch("noveler.infrastructure.repositories.configuration_repository.ConfigurationRepository.get_project_paths")
    def test_setup_environment_success(self, mock_get_paths: object) -> None:
        """環境変数設定成功"""
        mock_get_paths.return_value = {
            "project_root": "/test/project",
            "guide_root": "/test/guide",
        }

        with patch.dict("os.environ", {}, clear=True):
            result = setup_environment()
            assert result is True
            assert os.environ["PROJECT_ROOT"] == "/test/project"
            assert os.environ["GUIDE_ROOT"] == "/test/guide"

    @patch("noveler.infrastructure.repositories.configuration_repository.ConfigurationRepository.get_project_paths")
    def test_setup_environment_no_paths(self, mock_get_paths: object) -> None:
        """パスが見つからない場合"""
        mock_get_paths.return_value = {}

        result = setup_environment()
        assert result is False


class TestGetProjectInfo:
    """get_project_info関数のテスト"""

    def test_get_project_info_without_hierarchical(self) -> None:
        """階層的設定なしでプロジェクト情報を取得"""
        # リポジトリインスタンスを直接モック

        # load_project_configメソッドをモックし、階層的設定を無効化
        with (
            patch.object(_repository, "_has_hierarchical", False),
            patch.object(_repository, "load_project_config") as mock_load,
        ):
            mock_load.return_value = {
                "project": {
                    "title": "テスト小説",
                    "ncode": "n1234567890",
                },
            }

            result = get_project_info()
            assert isinstance(result, dict)
            assert result["title"] == "テスト小説"
            assert result["ncode"] == "n1234567890"

    def test_get_project_info_with_hierarchical(self) -> None:
        """階層的設定ありでプロジェクト情報を取得"""

        with (
            patch.object(_repository, "_has_hierarchical", True),
            patch.object(_repository, "_hierarchical_config") as mock_config,
        ):
            mock_config.get.return_value = {"title": "テスト小説"}

            result = get_project_info()
            assert result["title"] == "テスト小説"
        mock_config.get.assert_called_with("project", {})


class TestGetNcode:
    """get_ncode関数のテスト"""

    def test_get_ncode_success(self) -> None:
        """ncode取得成功"""

        with patch.object(_repository, "get_project_info") as mock_get_info:
            mock_get_info.return_value = {"ncode": "n1234567890"}

            result = get_ncode()
            assert result == "n1234567890"

    def test_get_ncode_not_found(self) -> None:
        """ncodeが見つからない場合"""

        with patch.object(_repository, "get_project_info") as mock_get_info:
            mock_get_info.return_value = {}

            result = get_ncode()
            assert result is None


class TestGetConfig:
    """get_config関数のテスト"""

    def test_get_config_without_hierarchical(self) -> None:
        """階層的設定なしで設定値を取得"""

        with (
            patch.object(_repository, "_has_hierarchical", False),
            patch.object(_repository, "load_project_config") as mock_load,
        ):
            mock_load.return_value = {
                "settings": {
                    "quality_threshold": 80,
                },
            }

            result = get_config("settings.quality_threshold")
            assert result == 80

    def test_get_config_default_value(self) -> None:
        """デフォルト値を返す場合"""

        with (
            patch.object(_repository, "_has_hierarchical", False),
            patch.object(_repository, "load_project_config") as mock_load,
        ):
            mock_load.return_value = {}

            result = get_config("nonexistent.key", "default_value")
            assert result == "default_value"

    def test_get_config_no_key(self) -> None:
        """キーを指定しない場合"""

        with (
            patch.object(_repository, "_has_hierarchical", False),
            patch.object(_repository, "load_project_config") as mock_load,
        ):
            config_data = {"test": "value"}
            mock_load.return_value = config_data

            result = get_config()
            assert result == config_data

    def test_get_config_with_hierarchical(self) -> None:
        """階層的設定ありで設定値を取得"""

        with (
            patch.object(_repository, "_has_hierarchical", True),
            patch.object(_repository, "_hierarchical_config") as mock_config,
        ):
            mock_config.get.return_value = "hierarchical_value"

            result = get_config("test.key", "default")
            assert result == "hierarchical_value"
            mock_config.get.assert_called_with("test.key", "default")


class TestGetAuthorInfo:
    """get_author_info関数のテスト"""

    def test_get_author_info_without_hierarchical(self) -> None:
        """階層的設定なしで著者情報を取得"""

        with (
            patch.object(_repository, "_has_hierarchical", False),
            patch.object(_repository, "load_project_config") as mock_load,
        ):
            mock_load.return_value = {
                "author": {
                    "pen_name": "テスト作者",
                    "email": "test@example.com",
                },
            }

            result = get_author_info()
            assert result["pen_name"] == "テスト作者"
            assert result["email"] == "test@example.com"
    def test_get_author_info_with_hierarchical_project(self) -> None:
        """階層的設定ありでプロジェクト固有の著者情報を取得"""

        with (
            patch.object(_repository, "_has_hierarchical", True),
            patch.object(_repository, "_hierarchical_config") as mock_config,
        ):
            mock_config.get.side_effect = lambda key, default=None: {
                "author": {"pen_name": "プロジェクト作者"},
                "default_author": {"pen_name": "デフォルト作者"},
            }.get(key, default)

            result = get_author_info()
            assert result["pen_name"] == "プロジェクト作者"

    def test_get_author_info_with_hierarchical_default(self) -> None:
        """階層的設定ありでデフォルト著者情報を取得"""

        with (
            patch.object(_repository, "_has_hierarchical", True),
            patch.object(_repository, "_hierarchical_config") as mock_config,
        ):
            mock_config.get.side_effect = lambda key, default=None: {
                "author": {},
                "default_author": {"pen_name": "デフォルト作者"},
            }.get(key, default)

            result = get_author_info()
            assert result["pen_name"] == "デフォルト作者"


class TestGetQualityThreshold:
    """get_quality_threshold関数のテスト"""

    def test_get_quality_threshold_without_hierarchical(self) -> None:
        """階層的設定なしで品質閾値を取得"""

        with (
            patch.object(_repository, "_has_hierarchical", False),
            patch.object(_repository, "load_project_config") as mock_load,
        ):
            mock_load.return_value = {
                "settings": {
                    "quality_threshold": 90,
                },
            }

            result = get_quality_threshold()
            assert result == 90

    def test_get_quality_threshold_default(self) -> None:
        """デフォルト品質閾値を取得"""

        with (
            patch.object(_repository, "_has_hierarchical", False),
            patch.object(_repository, "load_project_config") as mock_load,
        ):
            mock_load.return_value = {}

            result = get_quality_threshold()
            assert result == 80

    def test_get_quality_threshold_with_hierarchical(self) -> None:
        """階層的設定ありで品質閾値を取得"""

        with (
            patch.object(_repository, "_has_hierarchical", True),
            patch.object(_repository, "_hierarchical_config") as mock_config,
        ):
            mock_config.get.return_value = 85

            result = get_quality_threshold()
            assert result == 85
            mock_config.get.assert_called_with("quality_management.default_threshold", 80)
