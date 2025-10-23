#!/usr/bin/env python3
"""設定読み込みユースケースのテスト

REQ-1.1: YAMLファイルからの設定読み込み機能の統合テスト
"""

from pathlib import Path

import pytest

from noveler.application.use_cases.load_configuration_use_case import (
    LoadConfigurationRequest,
    LoadConfigurationUseCase,
)
from noveler.infrastructure.repositories.yaml_configuration_repository import YamlConfigurationRepository


@pytest.mark.spec("SPEC-CONFIG-001")
class TestLoadConfigurationUseCase:
    @pytest.mark.spec("SPEC-LOAD_CONFIGURATION_USE_CASE-EXECUTE_WITH_VALID_C")
    @pytest.mark.asyncio
    async def test_execute_with_valid_config_file_returns_success(self):
        """仕様要件REQ-1.1: 有効な設定ファイルでの正常実行"""
        # Arrange
        repository = YamlConfigurationRepository(path_service=None)
        use_case = LoadConfigurationUseCase(repository)

        # 実際の設定ファイルパスを使用
        config_path = Path("config/novel_config.yaml")
        request = LoadConfigurationRequest(config_file_path=config_path)

        # Act
        response = await use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.configuration is not None
        assert response.error_message is None

    @pytest.mark.spec("SPEC-LOAD_CONFIGURATION_USE_CASE-EXECUTE_WITH_MISSING")
    @pytest.mark.asyncio
    async def test_execute_with_missing_config_file_returns_error(self):
        """仕様要件REQ-1.5: 存在しない設定ファイルでのエラーハンドリング"""
        # Arrange
        repository = YamlConfigurationRepository(path_service=None)
        use_case = LoadConfigurationUseCase(repository)

        missing_path = Path("config/missing_config.yaml")
        request = LoadConfigurationRequest(config_file_path=missing_path)

        # Act
        response = await use_case.execute(request)

        # Assert
        assert response.success is False
        assert response.configuration is None
        assert "見つかりません" in response.error_message

    @pytest.mark.spec("SPEC-LOAD_CONFIGURATION_USE_CASE-EXECUTE_WITH_INVALID")
    @pytest.mark.asyncio
    async def test_execute_with_invalid_yaml_returns_error(self):
        """仕様要件REQ-1.5: 無効なYAMLでのエラーハンドリング"""
        # Arrange
        repository = YamlConfigurationRepository(path_service=None)
        use_case = LoadConfigurationUseCase(repository)

        # テスト用に無効なYAMLファイルを作成（テスト後削除）
        invalid_yaml_path = Path("temp/invalid_config.yaml")
        invalid_yaml_path.parent.mkdir(parents=True, exist_ok=True)

        with open(invalid_yaml_path, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: content: [")

        request = LoadConfigurationRequest(config_file_path=invalid_yaml_path)

        try:
            # Act
            response = await use_case.execute(request)

            # Assert
            assert response.success is False
            assert response.configuration is None
            assert "YAML" in response.error_message
        finally:
            # Cleanup
            if invalid_yaml_path.exists():
                invalid_yaml_path.unlink()

    @pytest.mark.spec("SPEC-LOAD_CONFIGURATION_USE_CASE-EXECUTE_LOADS_ALL_RE")
    @pytest.mark.asyncio
    async def test_execute_loads_all_required_sections(self):
        """仕様要件REQ-1.1: 全必須セクションの正常読み込み"""
        # Arrange
        repository = YamlConfigurationRepository(path_service=None)
        use_case = LoadConfigurationUseCase(repository)

        config_path = Path("config/novel_config.yaml")
        request = LoadConfigurationRequest(config_file_path=config_path)

        # Act
        response = await use_case.execute(request)

        # Assert
        assert response.success is True
        config = response.configuration

        # 主要セクションの存在確認
        assert config.get_system_setting("app_name") == "小説執筆支援システム"
        assert config.get_default_setting("author", "pen_name") == "秋田 武史"
        assert config.get_path_setting("directories", "config") == "config"
