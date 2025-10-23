#!/usr/bin/env python3
"""NovelConfiguration エンティティのテスト

REQ-1.1: YAMLファイルからの設定読み込み機能のテスト
"""

import pytest

from noveler.domain.entities.novel_configuration import NovelConfiguration
from noveler.presentation.shared.shared_utilities import get_common_path_service


@pytest.mark.spec("SPEC-CONFIG-001")
class TestNovelConfiguration:
    """NovelConfiguration エンティティのテストクラス"""

    @pytest.mark.spec("SPEC-NOVEL_CONFIGURATION-CREATE_FROM_DICT_RET")
    def test_create_from_dict_returns_valid_configuration(self):
        """仕様要件REQ-1.1: 辞書からの設定オブジェクト作成"""
        # Arrange
        config_data = {
            "system": {"app_name": "小説執筆支援システム", "version": "1.0.0", "debug": False},
            "defaults": {"author": {"pen_name": "テスト太郎"}, "episode": {"default_word_count": 3500}},
        }

        # Act
        config = NovelConfiguration.from_dict(config_data)

        # Assert
        assert config is not None
        assert config.get_system_setting("app_name") == "小説執筆支援システム"
        assert config.get_default_setting("episode", "default_word_count") == 3500

    @pytest.mark.spec("SPEC-NOVEL_CONFIGURATION-GET_SYSTEM_SETTING_R")
    def test_get_system_setting_returns_correct_value(self):
        """仕様要件REQ-1.2: システム設定の正常取得"""
        # Arrange
        config_data = {"system": {"app_name": "小説執筆支援システム", "version": "1.0.0"}}
        config = NovelConfiguration.from_dict(config_data)

        # Act
        app_name = config.get_system_setting("app_name")
        version = config.get_system_setting("version")

        # Assert
        assert app_name == "小説執筆支援システム"
        assert version == "1.0.0"

    @pytest.mark.spec("SPEC-NOVEL_CONFIGURATION-GET_PATH_SETTING_RET")
    def test_get_path_setting_returns_correct_path(self):
        """仕様要件REQ-1.3: パス設定の正常取得"""
        # Arrange
        path_service = get_common_path_service()
        config_data = {
            "paths": {
                "directories": {"config": "config", "cache": "cache"},
                "project_paths": {"manuscript_dir": str(path_service.get_manuscript_dir())},
            }
        }
        config = NovelConfiguration.from_dict(config_data)

        # Act
        config_dir = config.get_path_setting("directories", "config")
        manuscript_dir = config.get_path_setting("project_paths", "manuscript_dir")

        # Assert
        assert config_dir == "config"
        assert manuscript_dir == str(path_service.get_manuscript_dir())

    @pytest.mark.spec("SPEC-NOVEL_CONFIGURATION-GET_PLATFORM_PATH_RE")
    def test_get_platform_path_returns_current_platform_path(self):
        """仕様要件REQ-1.3: プラットフォーム固有パスの自動選択"""
        # Arrange
        config_data = {
            "platform_paths": {
                "linux": {"default_project_root": "/mnt/c/Users/test"},
                "windows": {"default_project_root": "C:\\Users\\test"},
                "darwin": {"default_project_root": "~/test"},
            }
        }
        config = NovelConfiguration.from_dict(config_data)

        # Act
        project_root = config.get_platform_path("default_project_root")

        # Assert
        # プラットフォームに応じた値が返されることを確認
        assert project_root is not None
        assert len(project_root) > 0

    @pytest.mark.spec("SPEC-NOVEL_CONFIGURATION-GET_MISSING_SETTING_")
    def test_get_missing_setting_returns_default(self):
        """仕様要件REQ-1.4: 存在しない設定キーでのデフォルト値返却"""
        # Arrange
        config = NovelConfiguration.from_dict({})

        # Act
        missing_value = config.get_system_setting("missing_key", "default")

        # Assert
        assert missing_value == "default"

    @pytest.mark.spec("SPEC-NOVEL_CONFIGURATION-IS_FEATURE_ENABLED_R")
    def test_is_feature_enabled_returns_correct_value(self):
        """仕様要件REQ-1.2: 機能フラグの正常判定"""
        # Arrange
        config_data = {
            "features": {"experimental": {"smart_auto_enhancement": True}, "legacy": {"old_quality_checker": False}}
        }
        config = NovelConfiguration.from_dict(config_data)

        # Act
        smart_enabled = config.is_feature_enabled("experimental", "smart_auto_enhancement")
        legacy_enabled = config.is_feature_enabled("legacy", "old_quality_checker")

        # Assert
        assert smart_enabled is True
        assert legacy_enabled is False
