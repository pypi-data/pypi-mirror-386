#!/usr/bin/env python3
"""YamlProjectInfoRepository のテスト
インフラ層のリポジトリ実装テスト


仕様書: SPEC-INFRASTRUCTURE
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from noveler.infrastructure.repositories.yaml_project_info_repository import YamlProjectInfoRepository
from noveler.presentation.shared.shared_utilities import get_common_path_service


class TestYamlProjectInfoRepository:
    """YamlProjectInfoRepository のテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        get_common_path_service()
        self.repository = YamlProjectInfoRepository()

    def test_get_supported_file_types(self) -> None:
        """サポートされているファイルタイプの取得"""
        # Act
        file_types = self.repository.get_supported_file_types()

        # Assert
        assert "project_settings" in file_types
        assert "character_settings" in file_types
        assert "plot_settings" in file_types
        assert "episode_management" in file_types

    def test_get_file_type_description(self) -> None:
        """ファイルタイプ説明の取得"""
        # Act
        description = self.repository.get_file_type_description("project_settings")

        # Assert
        assert "プロジェクトの基本設定" in description

    def test_get_file_path(self) -> None:
        """ファイルパス取得"""
        # Act
        file_path = self.repository.get_file_path("/test/project", "project_settings")

        # Assert
        assert file_path == "/test/project/プロジェクト設定.yaml"

    def test_get_file_path_invalid_type(self) -> None:
        """無効なファイルタイプでエラー"""
        # Act & Assert
        with pytest.raises(ValueError, match="未知のファイルタイプ"):
            self.repository.get_file_path("/test", "invalid_type")

    def test_file_exists_true(self) -> None:
        """ファイル存在確認:存在する場合"""
        with tempfile.NamedTemporaryFile() as temp_file:
            # Act
            result = self.repository.file_exists(temp_file.name)

            # Assert
            assert result is True

    def test_file_exists_false(self) -> None:
        """ファイル存在確認:存在しない場合"""
        # Act
        result = self.repository.file_exists("/non/existent/file.yaml")

        # Assert
        assert result is False


class TestYamlProjectInfoRepositoryWithTempDir:
    """一時ディレクトリを使用したテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.repository = YamlProjectInfoRepository()
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)

    def teardown_method(self) -> None:
        """テストクリーンアップ"""

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_project_structure(self) -> None:
        """プロジェクト構造作成"""
        # Act
        self.repository.create_project_structure(str(self.project_path), "テストプロジェクト")

        # Assert
        # ディレクトリが作成されている
        path_service = get_common_path_service()
        assert (self.project_path / str(path_service.get_plots_dir())).exists()
        assert (self.project_path / str(path_service.get_plots_dir())).exists()
        assert (self.project_path / str(path_service.get_management_dir())).exists()
        assert (self.project_path / str(path_service.get_manuscript_dir())).exists()
        assert (self.project_path / str(path_service.get_management_dir())).exists()

        # プロジェクト設定ファイルが作成されている
        settings_file = self.project_path / "プロジェクト設定.yaml"
        assert settings_file.exists()

        # ファイル内容の確認
        with Path(settings_file).open(encoding="utf-8") as f:
            content = yaml.safe_load(f)
        assert content["title"] == "テストプロジェクト"

    def test_validate_project_structure_valid(self) -> None:
        """有効なプロジェクト構造の検証"""
        # Arrange
        self.repository.create_project_structure(str(self.project_path), "有効プロジェクト")

        # Act
        result = self.repository.validate_project_structure(str(self.project_path))

        # Assert
        assert result["is_valid"] is True
        assert len(result["missing_directories"]) == 0
        assert len(result["missing_files"]) == 0

    def test_validate_project_structure_missing_directories(self) -> None:
        """ディレクトリ不足のプロジェクト構造検証"""
        # Arrange
        # プロジェクト設定ファイルのみ作成
        settings_file = self.project_path / "プロジェクト設定.yaml"
        with Path(settings_file).open("w", encoding="utf-8") as f:
            yaml.dump({"title": "不完全プロジェクト"}, f, allow_unicode=True)

        # Act
        result = self.repository.validate_project_structure(str(self.project_path))

        # Assert
        assert result["is_valid"] is False
        assert len(result["missing_directories"]) > 0
        path_service = get_common_path_service()
        assert str(path_service.get_plots_dir()) in result["missing_directories"]

    def test_validate_project_structure_missing_settings_file(self) -> None:
        """プロジェクト設定ファイル不足の検証"""
        # Arrange
        # ディレクトリのみ作成
        path_service = get_common_path_service()
        (self.project_path / str(path_service.get_plots_dir())).mkdir()
        (self.project_path / str(path_service.get_plots_dir())).mkdir()
        (self.project_path / str(path_service.get_management_dir())).mkdir()
        (self.project_path / str(path_service.get_manuscript_dir())).mkdir()
        (self.project_path / str(path_service.get_management_dir())).mkdir()

        # Act
        result = self.repository.validate_project_structure(str(self.project_path))

        # Assert
        assert result["is_valid"] is False
        assert "プロジェクト設定.yaml" in result["missing_files"]

    def test_load_project_files_complete_project(self) -> None:
        """完全なプロジェクトファイルの読み込み"""
        # Arrange
        self.repository.create_project_structure(str(self.project_path), "完全プロジェクト")

        # キャラクター設定ファイルを作成
        path_service = get_common_path_service()
        char_dir = self.project_path / str(path_service.get_management_dir())
        char_file = char_dir / "キャラクター.yaml"
        with Path(char_file).open("w", encoding="utf-8") as f:
            yaml.dump({"main_characters": [{"name": "主人公", "role": "主人公"}]}, f, allow_unicode=True)

        # プロット設定ファイルを作成
        plot_dir = self.project_path / str(path_service.get_plots_dir())
        plot_file = plot_dir / "全体構成.yaml"
        with Path(plot_file).open("w", encoding="utf-8") as f:
            yaml.dump({"total_episodes": 50, "act_structure": {"act1": "起"}}, f, allow_unicode=True)

        # Act
        result = self.repository.load_project_files(str(self.project_path))

        # Assert
        assert "project_settings" in result
        assert "character_settings" in result
        assert "plot_settings" in result
        assert result["project_settings"]["title"] == "完全プロジェクト"
        assert len(result["character_settings"]["main_characters"]) == 1
        assert result["plot_settings"]["total_episodes"] == 50

    def test_load_project_files_minimal_project(self) -> None:
        """最小限のプロジェクトファイル読み込み"""
        # Arrange
        # プロジェクト設定ファイルのみ作成
        settings_file = self.project_path / "プロジェクト設定.yaml"
        with Path(settings_file).open("w", encoding="utf-8") as f:
            yaml.dump({"title": "最小限プロジェクト", "genre": "テスト"}, f, allow_unicode=True)

        # Act
        result = self.repository.load_project_files(str(self.project_path))

        # Assert
        assert "project_settings" in result
        assert result["project_settings"]["title"] == "最小限プロジェクト"
        # 他のファイルは存在しないので含まれない
        assert "character_settings" not in result
        assert "plot_settings" not in result

    def test_load_project_files_nonexistent_directory(self) -> None:
        """存在しないディレクトリでエラー"""
        # Act & Assert
        with pytest.raises(FileNotFoundError, match="プロジェクトルートが見つかりません"):
            self.repository.load_project_files("/non/existent/directory")

    def test_get_project_root_with_settings_file(self) -> None:
        """プロジェクト設定ファイルによるルート検出"""
        # Arrange
        settings_file = self.project_path / "プロジェクト設定.yaml"
        with Path(settings_file).open("w") as f:
            f.write("title: test")

        # Act
        # start_pathを明示的に指定してテスト
        result = self.repository.get_project_root(start_path=str(self.project_path))

        # Assert
        assert result == str(self.project_path)

    def test_get_project_root_with_claude_md(self) -> None:
        """CLAUDE.mdによるルート検出"""
        # Arrange
        claude_file = self.project_path / "CLAUDE.md"
        with Path(claude_file).open("w") as f:
            f.write("# CLAUDE.md")
        # Act
        # start_pathを明示的に指定してテスト
        result = self.repository.get_project_root(start_path=str(self.project_path))

        # Assert
        assert result == str(self.project_path)

    def test_get_project_root_not_found_returns_current(self) -> None:
        """プロジェクトルート見つからない場合は現在ディレクトリ"""
        # Act
        # マーカーファイルがない場合のテスト
        result = self.repository.get_project_root(start_path=str(self.project_path))

        # Assert
        assert result == str(self.project_path)


class TestYamlProjectInfoRepositoryErrorHandling:
    """エラーハンドリングのテスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.repository = YamlProjectInfoRepository()

    def test_load_yaml_file_invalid_yaml(self) -> None:
        """無効なYAMLファイルでエラー"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="YAML形式が不正です"):
                self.repository._load_yaml_file(Path(temp_path))
        finally:
            os.unlink(temp_path)

    def test_load_yaml_file_non_dict_content(self) -> None:
        """辞書でないYAMLコンテンツでエラー"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("- list\n- content")
            temp_path = f.name

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="辞書形式である必要があります"):
                self.repository._load_yaml_file(Path(temp_path))
        finally:
            os.unlink(temp_path)

    def test_load_yaml_file_empty_file(self) -> None:
        """空ファイルの処理"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            # Act
            result = self.repository._load_yaml_file(Path(temp_path))

            # Assert
            assert result is None
        finally:
            os.unlink(temp_path)

    @patch("pathlib.Path.open", side_effect=PermissionError("Permission denied"))
    def test_load_yaml_file_permission_error(self) -> None:
        """ファイル読み込み権限エラー"""
        # Act & Assert
        with pytest.raises(PermissionError, match="ファイル読み込み権限がありません"):
            self.repository._load_yaml_file(Path("/test/file.yaml"))

    def test_load_project_files_with_file_errors(self) -> None:
        """一部ファイルエラーがあっても継続処理"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # 有効なプロジェクト設定ファイル
            settings_file = project_path / "プロジェクト設定.yaml"
            with Path(settings_file).open("w", encoding="utf-8") as f:
                yaml.dump({"title": "エラーテスト"}, f, allow_unicode=True)

            # 無効なキャラクターファイル(権限エラーをシミュレート)
            path_service = get_common_path_service()
            char_dir = project_path / str(path_service.get_management_dir())
            char_dir.mkdir()
            char_file = char_dir / "キャラクター.yaml"
            with Path(char_file).open("w") as f:
                f.write("invalid: yaml: [")

            # Act
            # 警告出力をキャプチャするため、標準出力をモック
            with patch("builtins.print") as mock_print:
                result = self.repository.load_project_files(str(project_path))

            # Assert
            # 有効なファイルは読み込まれる
            assert "project_settings" in result
            assert result["project_settings"]["title"] == "エラーテスト"

            # 無効なファイルは除外される
            assert "character_settings" not in result

            # 警告が出力される
            mock_print.assert_called()


class TestYamlProjectInfoRepositoryIntegration:
    """統合テスト"""

    def test_full_project_workflow(self) -> None:
        """完全なプロジェクトワークフロー"""
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = YamlProjectInfoRepository()
            project_path = temp_dir

            # 1. プロジェクト構造作成
            repository.create_project_structure(project_path, "統合テストプロジェクト")

            # 2. 構造検証
            validation = repository.validate_project_structure(project_path)
            assert validation["is_valid"] is True

            # 3. 追加ファイル作成
            # キャラクター設定
            path_service = get_common_path_service()
            char_file = Path(project_path) / str(path_service.get_management_dir()) / "キャラクター.yaml"
            with Path(char_file).open("w", encoding="utf-8") as f:
                yaml.dump(
                    {
                        "main_characters": [
                            {"name": "統合テスト主人公", "role": "主人公"},
                            {"name": "統合テスト敵", "role": "アンタゴニスト"},
                        ]
                    },
                    f,
                    allow_unicode=True,
                )

            # 4. ファイル読み込み
            project_files = repository.load_project_files(project_path)

            # 5. 結果検証
            assert "project_settings" in project_files
            assert "character_settings" in project_files
            assert project_files["project_settings"]["title"] == "統合テストプロジェクト"
            assert len(project_files["character_settings"]["main_characters"]) == 2

            # 6. ファイル操作の確認
            settings_path = repository.get_file_path(project_path, "project_settings")
            assert repository.file_exists(settings_path)

            char_path = repository.get_file_path(project_path, "character_settings")
            assert repository.file_exists(char_path)
