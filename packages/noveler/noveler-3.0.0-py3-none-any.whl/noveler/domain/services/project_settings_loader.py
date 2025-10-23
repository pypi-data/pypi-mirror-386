#!/usr/bin/env python3

# File: src/noveler/domain/services/project_settings_loader.py
# Purpose: Load and parse project configuration files in environment-agnostic manner
# Context: Supports config file priority (config/novel_config.yaml > プロジェクト設定.yaml > defaults)

"""Project settings loader service.

This module provides a service for loading project configuration from YAML files
with prioritized fallback and environment-agnostic path resolution.

Design principle: Load config files in priority order, resolve relative paths at
runtime using the provided project_root, no explicit Windows/WSL detection needed.
"""

from pathlib import Path
from typing import Any, Optional
import yaml

from noveler.domain.value_objects.project_settings_schema import (
    ProjectSettings,
    ProjectPaths,
    SettingsFileNames
)


class ProjectSettingsLoader:
    """プロジェクト設定を統一的に読み込むサービス（環境判定不要）

    Loads project configuration from YAML files with the following priority:
    1. config/novel_config.yaml (recommended for new projects)
    2. プロジェクト設定.yaml (backward compatibility)
    3. Default values (fallback)

    Args:
        project_root: Absolute path to project root (runtime-provided)

    Preconditions:
        - project_root must be a valid Path object pointing to an existing directory
        - If config files exist, they must be valid YAML with UTF-8 encoding

    Side effects:
        - Reads config files from filesystem
        - Caches loaded config in memory
        - Does NOT create any files or directories

    Raises:
        ValueError: If config file has invalid YAML syntax or encoding errors
    """

    # デフォルト値
    DEFAULT_PATHS = {
        "manuscripts": "40_原稿/",
        "management": "50_管理資料/",
        "settings": "30_設定集/",
        "plots": "20_プロット/"
    }

    DEFAULT_FILENAMES = {
        "world_settings": "世界観.yaml",
        "character_settings": "キャラクター.yaml",
        "glossary": "用語集.yaml",
        "style_guide": "文体ガイド.yaml"
    }

    CONFIG_PATHS = [
        "config/novel_config.yaml",  # 優先度1（推奨）
        "プロジェクト設定.yaml"      # 優先度2（後方互換）
    ]

    def __init__(self, project_root: Path):
        """Initialize loader with project root path.

        Args:
            project_root: Absolute path to project root directory

        Side effects:
            - Resolves project_root to absolute path (handles Windows/WSL automatically)
            - Initializes config cache as None
        """
        # 環境に応じた絶対パスに自動変換
        self.project_root = project_root.resolve()
        self._config_cache: dict[str, Any] | None = None

    def load_settings(self) -> ProjectSettings:
        """プロジェクト設定を読み込む（環境判定不要）

        優先順位:
        1. config/novel_config.yaml
        2. プロジェクト設定.yaml
        3. デフォルト値

        Returns:
            ProjectSettings: 統合されたプロジェクト設定

        Side effects:
            - Calls _load_config_file() which reads from filesystem
            - Caches loaded config in self._config_cache

        Raises:
            ValueError: If config file has invalid YAML or encoding errors
        """
        config = self._load_config_file()

        # プロジェクト名
        project_name = self._get_project_name(config)

        # パス設定（相対パスを保持）
        paths = self._load_paths(config)

        # ファイル名設定
        filenames = self._load_filenames(config)

        return ProjectSettings(
            project_name=project_name,
            paths=paths,
            settings_files=filenames
        )

    def _load_config_file(self) -> dict[str, Any] | None:
        """設定ファイルを優先順位に従って読み込む

        Searches for config files in priority order (CONFIG_PATHS) and
        returns the first valid one found.

        Returns:
            Parsed YAML as dict, or None if no config file found

        Side effects:
            - Reads files from filesystem
            - Caches result in self._config_cache
            - Silently continues on file not found

        Raises:
            ValueError: If a config file exists but has invalid YAML syntax
            ValueError: If a config file exists but has encoding errors
        """
        if self._config_cache:
            return self._config_cache

        for config_file in self.CONFIG_PATHS:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, encoding="utf-8") as f:
                        self._config_cache = yaml.safe_load(f)
                        return self._config_cache
                except yaml.YAMLError as e:
                    raise ValueError(f"Invalid YAML syntax in {config_file}: {e}") from e
                except UnicodeDecodeError as e:
                    raise ValueError(f"Encoding error in {config_file}: {e}") from e
                except Exception:
                    # Unexpected errors: continue to next config file
                    continue

        return None

    def _get_project_name(self, config: dict[str, Any] | None) -> str:
        """プロジェクト名を取得

        Args:
            config: Loaded config dict (may be None)

        Returns:
            Project name from config, or directory name as fallback

        Side effects:
            None
        """
        if config and "project" in config and "name" in config["project"]:
            return str(config["project"]["name"])
        return self.project_root.name

    def _load_paths(self, config: dict[str, Any] | None) -> ProjectPaths:
        """パス設定を読み込む（project_rootは実行時の実パスを使用）

        Args:
            config: Loaded config dict (may be None)

        Returns:
            ProjectPaths with relative paths from config or defaults

        Side effects:
            None

        Preconditions:
            - self.project_root must be set
        """
        if config and "paths" in config:
            paths_config = config["paths"]
            return ProjectPaths(
                project_root=self.project_root,  # 実行時の実パスを使用
                manuscripts=paths_config.get("manuscripts", self.DEFAULT_PATHS["manuscripts"]),
                management=paths_config.get("management", self.DEFAULT_PATHS["management"]),
                settings=paths_config.get("settings", self.DEFAULT_PATHS["settings"]),
                plots=paths_config.get("plots", self.DEFAULT_PATHS["plots"])
            )

        # デフォルト値を使用
        return ProjectPaths(
            project_root=self.project_root,
            manuscripts=self.DEFAULT_PATHS["manuscripts"],
            management=self.DEFAULT_PATHS["management"],
            settings=self.DEFAULT_PATHS["settings"],
            plots=self.DEFAULT_PATHS["plots"]
        )

    def _load_filenames(self, config: dict[str, Any] | None) -> SettingsFileNames:
        """ファイル名設定を読み込む

        Args:
            config: Loaded config dict (may be None)

        Returns:
            SettingsFileNames with filenames from config or defaults

        Side effects:
            None
        """
        if config and "settings_files" in config:
            files_config = config["settings_files"]
            return SettingsFileNames(
                world_settings=files_config.get("world_settings", self.DEFAULT_FILENAMES["world_settings"]),
                character_settings=files_config.get("character_settings", self.DEFAULT_FILENAMES["character_settings"]),
                glossary=files_config.get("glossary", self.DEFAULT_FILENAMES["glossary"]),
                style_guide=files_config.get("style_guide", self.DEFAULT_FILENAMES["style_guide"])
            )

        # デフォルト値を使用
        return SettingsFileNames(
            world_settings=self.DEFAULT_FILENAMES["world_settings"],
            character_settings=self.DEFAULT_FILENAMES["character_settings"],
            glossary=self.DEFAULT_FILENAMES["glossary"],
            style_guide=self.DEFAULT_FILENAMES["style_guide"]
        )
