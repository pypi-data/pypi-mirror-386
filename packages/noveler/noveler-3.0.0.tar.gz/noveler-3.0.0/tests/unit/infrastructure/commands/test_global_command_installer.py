#!/usr/bin/env python3
"""
グローバルコマンドインストーラーのテスト

SPEC-MCP-001準拠: グローバル /noveler コマンド機能のテスト実装
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.infrastructure.commands.global_command_installer import (
    GlobalCommandInstaller,
    GlobalCommandInstallerError,
)


class TestGlobalCommandInstaller:
    """グローバルコマンドインストーラーのテスト"""

    def setup_method(self):
        """各テストの前処理"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mock_home = self.temp_dir / "home"
        self.mock_home.mkdir(parents=True)
        self.claude_dir = self.mock_home / ".claude" / "commands"
        self.claude_dir.mkdir(parents=True)

    def teardown_method(self):
        """各テストの後処理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('pathlib.Path.home')
    def test_install_global_command_creates_noveler_md(self, mock_home):
        """グローバルコマンドファイルが正しく作成されることを確認"""
        # Arrange
        mock_home.return_value = self.mock_home
        installer = GlobalCommandInstaller()
        expected_file = self.claude_dir / "noveler.md"

        # Act
        result = installer.install_global_command()

        # Assert
        assert result is True, "インストールが成功するはず"
        assert expected_file.exists(), "noveler.mdファイルが作成されるはず"

        content = expected_file.read_text(encoding='utf-8')
        assert 'allowed-tools: ["mcp__noveler__*"]' in content, "MCPツール指定が含まれるはず"
        assert 'description: "小説執筆支援（グローバル）"' in content, "正しい説明が含まれるはず"

    @patch('pathlib.Path.home')
    def test_backup_existing_file_when_noveler_md_exists(self, mock_home):
        """既存のnoveler.mdファイルがある場合、バックアップが作成されることを確認"""
        # Arrange
        mock_home.return_value = self.mock_home
        installer = GlobalCommandInstaller()
        existing_file = self.claude_dir / "noveler.md"
        existing_content = "既存のコンテンツ"
        existing_file.write_text(existing_content, encoding='utf-8')

        # Act
        result = installer.install_global_command()

        # Assert
        assert result is True, "インストールが成功するはず"

        # バックアップファイルが作成されているはず
        backup_files = list(self.claude_dir.glob("noveler.md.backup.*"))
        assert len(backup_files) == 1, "バックアップファイルが1つ作成されるはず"

        backup_content = backup_files[0].read_text(encoding='utf-8')
        assert backup_content == existing_content, "バックアップの内容が正しいはず"

    @patch('pathlib.Path.home')
    def test_cross_platform_path_resolution(self, mock_home):
        """クロスプラットフォーム対応のパス解決を確認"""
        # Arrange
        mock_home.return_value = self.mock_home
        installer = GlobalCommandInstaller()

        # Act
        claude_commands_path = installer.get_claude_commands_path()

        # Assert
        expected_path = self.mock_home / ".claude" / "commands"
        assert claude_commands_path == expected_path, "正しいパスが解決されるはず"
        assert isinstance(claude_commands_path, Path), "Pathオブジェクトが返されるはず"

    @patch('pathlib.Path.home')
    def test_permission_handling_when_directory_creation_fails(self, mock_home):
        """ディレクトリ作成に失敗した場合の権限エラー処理を確認"""
        # Arrange
        mock_home.return_value = self.mock_home
        installer = GlobalCommandInstaller()

        with patch.object(Path, 'mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("権限がありません")

            # Act & Assert
            with pytest.raises(GlobalCommandInstallerError) as exc_info:
                installer.install_global_command()

            assert "権限エラー" in str(exc_info.value), "権限エラーメッセージが含まれるはず"

    @patch('pathlib.Path.home')
    def test_template_content_validation(self, mock_home):
        """作成されるテンプレートの内容が仕様に準拠していることを確認"""
        # Arrange
        mock_home.return_value = self.mock_home
        installer = GlobalCommandInstaller()

        # Act
        installer.install_global_command()

        # Assert
        noveler_file = self.claude_dir / "noveler.md"
        content = noveler_file.read_text(encoding='utf-8')

        # YAMLフロントマターの確認
        assert content.startswith('---'), "YAMLフロントマターで始まるはず"
        assert 'allowed-tools: ["mcp__noveler__*"]' in content, "MCPツール許可設定があるはず"
        assert 'argument-hint: "<command> [options]"' in content, "引数ヒントがあるはず"
        assert 'model: "claude-3-5-sonnet-20241022"' in content, "モデル指定があるはず"

        # コマンド使用例の確認
        assert '/noveler write 1' in content, "執筆コマンド例があるはず"
        assert '/noveler check 1' in content, "品質チェックコマンド例があるはず"
        assert '/noveler status' in content, "ステータス確認コマンド例があるはず"

    @patch('pathlib.Path.home')
    def test_installation_status_check(self, mock_home):
        """インストール状況の確認機能をテスト"""
        # Arrange
        mock_home.return_value = self.mock_home
        installer = GlobalCommandInstaller()

        # Act & Assert - インストール前
        assert installer.is_installed() is False, "インストール前はFalseを返すはず"

        # インストール実行
        installer.install_global_command()

        # Act & Assert - インストール後
        assert installer.is_installed() is True, "インストール後はTrueを返すはず"

    @patch('pathlib.Path.home')
    def test_uninstall_global_command(self, mock_home):
        """グローバルコマンドのアンインストール機能をテスト"""
        # Arrange
        mock_home.return_value = self.mock_home
        installer = GlobalCommandInstaller()

        # インストール実行
        installer.install_global_command()
        assert installer.is_installed() is True, "インストールが成功しているはず"

        # Act
        result = installer.uninstall_global_command()

        # Assert
        assert result is True, "アンインストールが成功するはず"
        assert installer.is_installed() is False, "アンインストール後は存在しないはず"

    def test_global_command_installer_error_inheritance(self):
        """GlobalCommandInstallerErrorが適切に継承されていることを確認"""
        # Act & Assert
        error = GlobalCommandInstallerError("テストエラー")
        assert isinstance(error, Exception), "Exceptionを継承しているはず"
        assert str(error) == "テストエラー", "エラーメッセージが正しいはず"

    @patch('pathlib.Path.home')
    def test_get_noveler_template_path(self, mock_home):
        """テンプレートファイルのパス取得をテスト"""
        # Arrange
        mock_home.return_value = self.mock_home
        installer = GlobalCommandInstaller()

        # Act
        template_path = installer.get_noveler_template_path()

        # Assert
        assert template_path.name == "global_noveler.md", "テンプレートファイル名が正しいはず"
        assert "templates" in str(template_path), "templatesディレクトリが含まれるはず"
