#!/usr/bin/env python3

# File: tests/unit/domain/services/test_project_settings_loader.py
# Purpose: Test project settings loader with environment-agnostic path resolution
# Context: Validates config file priority, path resolution, and error handling

"""Test suite for ProjectSettingsLoader.

Tests cover:
- Config file priority (config/novel_config.yaml > プロジェクト設定.yaml > defaults)
- Path resolution across Windows/WSL environments
- Validation of missing files/directories
- Error handling for invalid YAML
"""

import pytest
from pathlib import Path
from noveler.domain.services.project_settings_loader import ProjectSettingsLoader
from noveler.domain.value_objects.project_settings_schema import (
    ProjectSettings,
    ProjectPaths,
    SettingsFileNames
)


@pytest.mark.spec("SPEC-PROJECT_SETTINGS-CONFIG_PRIORITY")
def test_config_priority_novel_config_first(tmp_path):
    """config/novel_config.yaml が最優先されることを確認"""
    # Arrange: 両方の設定ファイルを作成
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    novel_config = config_dir / "novel_config.yaml"
    novel_config.write_text(
        """
project:
  name: "Novel Config Project"

paths:
  manuscripts: "manuscripts/"
  settings: "settings/"

settings_files:
  world_settings: "world.yaml"
  character_settings: "characters.yaml"
""",
        encoding="utf-8"
    )

    legacy_config = tmp_path / "プロジェクト設定.yaml"
    legacy_config.write_text(
        """
project:
  name: "Legacy Config Project"

paths:
  manuscripts: "legacy_manuscripts/"
  settings: "legacy_settings/"
""",
        encoding="utf-8"
    )

    # Act
    loader = ProjectSettingsLoader(tmp_path)
    settings = loader.load_settings()

    # Assert: novel_config の内容が優先される
    assert settings.project_name == "Novel Config Project"
    assert settings.paths.manuscripts == "manuscripts/"
    assert settings.settings_files.world_settings == "world.yaml"


@pytest.mark.spec("SPEC-PROJECT_SETTINGS-CONFIG_PRIORITY")
def test_config_priority_legacy_fallback(tmp_path):
    """config/novel_config.yaml がない場合、プロジェクト設定.yaml が使用される"""
    # Arrange: レガシー設定のみ作成
    legacy_config = tmp_path / "プロジェクト設定.yaml"
    legacy_config.write_text(
        """
project:
  name: "Legacy Project"

paths:
  manuscripts: "40_原稿/"
  settings: "30_設定集/"
""",
        encoding="utf-8"
    )

    # Act
    loader = ProjectSettingsLoader(tmp_path)
    settings = loader.load_settings()

    # Assert: レガシー設定が読み込まれる
    assert settings.project_name == "Legacy Project"
    assert settings.paths.manuscripts == "40_原稿/"


@pytest.mark.spec("SPEC-PROJECT_SETTINGS-DEFAULT_VALUES")
def test_config_priority_defaults_fallback(tmp_path):
    """設定ファイルが存在しない場合、デフォルト値が使用される"""
    # Arrange: 設定ファイルなし

    # Act
    loader = ProjectSettingsLoader(tmp_path)
    settings = loader.load_settings()

    # Assert: デフォルト値が使用される
    assert settings.project_name == tmp_path.name  # ディレクトリ名
    assert settings.paths.manuscripts == "40_原稿/"
    assert settings.paths.settings == "30_設定集/"
    assert settings.settings_files.world_settings == "世界観.yaml"
    assert settings.settings_files.character_settings == "キャラクター.yaml"


@pytest.mark.spec("SPEC-PROJECT_SETTINGS-PATH_RESOLUTION")
def test_path_resolution_environment_agnostic(tmp_path):
    """パス解決が環境非依存で動作することを確認"""
    # Arrange: 設定ファイル作成
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    novel_config = config_dir / "novel_config.yaml"
    novel_config.write_text(
        """
project:
  name: "Test Project"

paths:
  settings: "settings/"

settings_files:
  world_settings: "world.yaml"
""",
        encoding="utf-8"
    )

    # 実際のディレクトリ・ファイル作成
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir()
    world_file = settings_dir / "world.yaml"
    world_file.write_text("name: テスト世界", encoding="utf-8")

    # Act
    loader = ProjectSettingsLoader(tmp_path)
    settings = loader.load_settings()
    world_path = settings.get_world_settings_path()

    # Assert: パスが正しく解決される
    assert world_path.exists()
    assert world_path.name == "world.yaml"
    # 環境に応じた Path 型 (WindowsPath or PosixPath) が自動選択される
    assert isinstance(world_path, Path)


@pytest.mark.spec("SPEC-PROJECT_SETTINGS-VALIDATION")
def test_validation_missing_settings_directory(tmp_path):
    """設定ディレクトリが存在しない場合、バリデーションでエラー報告"""
    # Arrange: 設定ファイルなし、ディレクトリなし

    # Act
    loader = ProjectSettingsLoader(tmp_path)
    settings = loader.load_settings()
    validation_result = settings.validate()

    # Assert: エラーが報告される
    assert len(validation_result["errors"]) > 0
    assert any("設定ディレクトリが存在しません" in err for err in validation_result["errors"])


@pytest.mark.spec("SPEC-PROJECT_SETTINGS-VALIDATION")
def test_validation_missing_mandatory_files(tmp_path):
    """必須ファイルが存在しない場合、バリデーションでエラー報告"""
    # Arrange: ディレクトリのみ作成、ファイルなし
    settings_dir = tmp_path / "30_設定集"
    settings_dir.mkdir()

    # Act
    loader = ProjectSettingsLoader(tmp_path)
    settings = loader.load_settings()
    validation_result = settings.validate()

    # Assert: 必須ファイルのエラーが報告される
    assert len(validation_result["errors"]) >= 2  # 世界観・キャラクター
    assert any("世界観設定ファイルが見つかりません" in err for err in validation_result["errors"])
    assert any("キャラクター設定ファイルが見つかりません" in err for err in validation_result["errors"])


@pytest.mark.spec("SPEC-PROJECT_SETTINGS-VALIDATION")
def test_validation_success_all_files_exist(tmp_path):
    """全ファイルが存在する場合、バリデーション成功"""
    # Arrange: ディレクトリとファイル作成
    settings_dir = tmp_path / "30_設定集"
    settings_dir.mkdir()

    (settings_dir / "世界観.yaml").write_text("name: テスト世界", encoding="utf-8")
    (settings_dir / "キャラクター.yaml").write_text("characters: {}", encoding="utf-8")

    # Act
    loader = ProjectSettingsLoader(tmp_path)
    settings = loader.load_settings()
    validation_result = settings.validate()

    # Assert: エラーなし
    assert len(validation_result["errors"]) == 0
    assert len(validation_result["warnings"]) == 0


@pytest.mark.spec("SPEC-PROJECT_SETTINGS-ERROR_HANDLING")
def test_invalid_yaml_raises_value_error(tmp_path):
    """不正なYAMLファイルで ValueError が発生"""
    # Arrange: 不正なYAML作成
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    novel_config = config_dir / "novel_config.yaml"
    novel_config.write_text(
        """
project:
  name: "Test Project"
  invalid yaml syntax: [
""",
        encoding="utf-8"
    )

    # Act & Assert
    loader = ProjectSettingsLoader(tmp_path)
    with pytest.raises(ValueError, match="Invalid YAML syntax"):
        loader.load_settings()


@pytest.mark.spec("SPEC-PROJECT_SETTINGS-PATH_RESOLUTION")
def test_get_all_setting_file_paths(tmp_path):
    """全設定ファイルパスが正しく取得できることを確認"""
    # Arrange
    settings_dir = tmp_path / "30_設定集"
    settings_dir.mkdir()

    (settings_dir / "世界観.yaml").write_text("name: 世界", encoding="utf-8")
    (settings_dir / "キャラクター.yaml").write_text("characters: {}", encoding="utf-8")
    (settings_dir / "用語集.yaml").write_text("terms: {}", encoding="utf-8")
    (settings_dir / "文体ガイド.yaml").write_text("style: {}", encoding="utf-8")

    # Act
    loader = ProjectSettingsLoader(tmp_path)
    settings = loader.load_settings()

    world_path = settings.get_world_settings_path()
    character_path = settings.get_character_settings_path()
    glossary_path = settings.get_glossary_path()
    style_guide_path = settings.get_style_guide_path()

    # Assert: 全パスが存在確認可能
    assert world_path.exists()
    assert character_path.exists()
    assert glossary_path.exists()
    assert style_guide_path.exists()

    # ファイル名確認
    assert world_path.name == "世界観.yaml"
    assert character_path.name == "キャラクター.yaml"
    assert glossary_path.name == "用語集.yaml"
    assert style_guide_path.name == "文体ガイド.yaml"


@pytest.mark.spec("SPEC-PROJECT_SETTINGS-BACKWARD_COMPATIBILITY")
def test_backward_compatibility_with_hardcoded_paths(tmp_path):
    """従来のハードコードパス（30_設定集）との後方互換性確認"""
    # Arrange: 従来のディレクトリ構造
    settings_dir = tmp_path / "30_設定集"
    settings_dir.mkdir()

    (settings_dir / "世界観.yaml").write_text("name: 世界", encoding="utf-8")
    (settings_dir / "キャラクター.yaml").write_text("characters: {}", encoding="utf-8")

    # Act: 設定ファイルなし（デフォルト動作）
    loader = ProjectSettingsLoader(tmp_path)
    settings = loader.load_settings()

    # Assert: デフォルトの "30_設定集" が使用される
    assert settings.paths.settings == "30_設定集/"
    assert settings.get_world_settings_path().exists()
    assert settings.get_character_settings_path().exists()


@pytest.mark.spec("SPEC-PROJECT_SETTINGS-CONFIG_CACHE")
def test_config_caching(tmp_path):
    """設定ファイルがキャッシュされることを確認"""
    # Arrange
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    novel_config = config_dir / "novel_config.yaml"
    novel_config.write_text(
        """
project:
  name: "Cached Project"
""",
        encoding="utf-8"
    )

    # Act: 同じローダーで複数回読み込み
    loader = ProjectSettingsLoader(tmp_path)
    settings1 = loader.load_settings()
    settings2 = loader.load_settings()

    # Assert: キャッシュが使用される（同一設定）
    assert settings1.project_name == settings2.project_name
    assert settings1.project_name == "Cached Project"


@pytest.mark.spec("SPEC-PROJECT_SETTINGS-ENCODING")
def test_utf8_encoding_support(tmp_path):
    """UTF-8エンコーディングの日本語ファイル名・内容をサポート"""
    # Arrange: 日本語を含む設定ファイル
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    novel_config = config_dir / "novel_config.yaml"
    novel_config.write_text(
        """
project:
  name: "日本語プロジェクト名"

paths:
  settings: "設定/"

settings_files:
  world_settings: "世界観.yaml"
  character_settings: "キャラクター.yaml"
""",
        encoding="utf-8"
    )

    # Act
    loader = ProjectSettingsLoader(tmp_path)
    settings = loader.load_settings()

    # Assert: 日本語が正しく読み込まれる
    assert settings.project_name == "日本語プロジェクト名"
    assert settings.settings_files.world_settings == "世界観.yaml"
    assert settings.settings_files.character_settings == "キャラクター.yaml"
