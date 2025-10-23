"""ファイル名テンプレート管理サービスのテスト

B20指示書準拠のTDD実装 - GREEN状態への移行
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

import noveler.infrastructure.ai_integration.repositories.yaml_project_config_repository as config_repo_module
from noveler.infrastructure.ai_integration.repositories.yaml_project_config_repository import YamlProjectConfigRepository

from noveler.domain.services.file_template_service import FileTemplateService, FileTemplateRepository

@pytest.mark.spec("SPEC-CONFIG-002")
class TestFileTemplateService:
    """ファイル名テンプレートサービスのテスト"""

    def test_get_project_config_filename_default(self):
        """デフォルト設定でプロジェクト設定ファイル名を取得"""
        # Arrange
        service = FileTemplateService(None)

        # Act
        filename = service.get_project_config_filename()

        # Assert
        assert filename == "プロジェクト設定.yaml"

    def test_get_project_config_filename_custom(self):
        """カスタム設定でプロジェクト設定ファイル名を取得"""
        # Arrange
        mock_repo = Mock(spec=FileTemplateRepository)
        mock_repo.get_template.return_value = "custom_project.yaml"
        service = FileTemplateService(mock_repo)

        # Act
        filename = service.get_project_config_filename()

        # Assert
        assert filename == "custom_project.yaml"
        mock_repo.get_template.assert_called_once_with("project_config")

    def test_get_episode_management_filename_default(self):
        """デフォルト設定で話数管理ファイル名を取得"""
        # Arrange
        service = FileTemplateService(None)

        # Act
        filename = service.get_episode_management_filename()

        # Assert
        assert filename == "話数管理.yaml"

    def test_get_filename_with_invalid_key(self):
        """無効なキー指定時のフォールバック動作"""
        # Arrange
        service = FileTemplateService(None)

        # Act
        filename = service.get_filename("invalid_key")

        # Assert
        assert filename == "invalid_key.yaml"

    def test_configuration_file_read_error_fallback(self):
        """.novelerrc.yaml読み込みエラー時のフォールバック"""
        # Arrange
        mock_repo = Mock(spec=FileTemplateRepository)
        mock_repo.get_template.side_effect = Exception("Configuration error")
        service = FileTemplateService(mock_repo)

        # Act
        filename = service.get_project_config_filename()

        # Assert
        assert filename == "プロジェクト設定.yaml"  # デフォルト値にフォールバック

@pytest.mark.spec("SPEC-CONFIG-002")
class TestConfigurationManagerFileTemplate:
    """ConfigurationManagerのファイル名テンプレート機能テスト"""

    def test_get_file_template_method_exists(self):
        """get_file_templateメソッドが存在する"""
        # Arrange
        from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager
        manager = get_configuration_manager()

        # Act
        result = manager.get_file_template("project_config")

        # Assert
        assert hasattr(manager, "get_file_template")
        assert result == "プロジェクト設定.yaml"

    def test_get_project_config_filename_method_exists(self):
        """get_project_config_filenameメソッドが存在する"""
        # Arrange
        from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager
        manager = get_configuration_manager()

        # Act
        result = manager.get_project_config_filename()

        # Assert
        assert hasattr(manager, "get_project_config_filename")
        assert result == "プロジェクト設定.yaml"

@pytest.mark.spec("SPEC-CONFIG-002")
class TestYamlProjectConfigRepositoryFileTemplate:
    """YamlProjectConfigRepositoryの設定ベースファイル名テスト"""

    def test_config_filename_uses_template_service(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """設定ファイル名がテンプレートサービス経由で取得される"""
        template_name = "custom_project.yaml"
        rc_path = tmp_path / ".novelerrc.yaml"
        rc_path.write_text(
            "file_templates:\n  project_config: {name}\n".format(name=template_name),
            encoding="utf-8",
        )

        from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager

        manager = get_configuration_manager()
        manager.clear_project_cache(tmp_path)
        monkeypatch.chdir(tmp_path)

        repository = YamlProjectConfigRepository(tmp_path)

        assert repository.config_filename == template_name
        manager.clear_project_cache(tmp_path)

    def test_config_filename_defaults_when_manager_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """コンフィグ取得に失敗した場合はデフォルト名を返す"""
        import noveler.infrastructure.factories.configuration_service_factory as config_factory

        def _raise_error():
            raise RuntimeError("manager unavailable")

        monkeypatch.setattr(config_factory, "get_configuration_manager", _raise_error)

        repository = YamlProjectConfigRepository(tmp_path)

        assert repository.config_filename == "プロジェクト設定.yaml"
