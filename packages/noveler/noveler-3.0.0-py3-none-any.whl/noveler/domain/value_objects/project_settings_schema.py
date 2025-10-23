#!/usr/bin/env python3

# File: src/noveler/domain/value_objects/project_settings_schema.py
# Purpose: Define environment-agnostic project configuration schema
# Context: Standardizes settings file management across Windows/WSL without explicit environment detection

"""Project settings schema for environment-agnostic configuration.

This module provides value objects for project configuration that work
seamlessly across Windows and WSL environments by using relative paths
and letting pathlib handle OS-specific path resolution automatically.

Design principle: Store only relative paths in config files, resolve to
absolute paths at runtime using the provided project_root.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ProjectPaths:
    """プロジェクトのフォルダパス設定（環境非依存）

    project_root: 実行時に自動決定される絶対パス
    その他: 相対パスのみを保持

    Args:
        project_root: Runtime-provided absolute path (auto-resolved by pathlib)
        manuscripts: Relative path to manuscripts directory
        management: Relative path to management documents directory
        settings: Relative path to settings directory
        plots: Relative path to plot documents directory

    Preconditions:
        - project_root must be a valid Path object
        - All relative paths should use forward slashes for cross-platform compatibility

    Side effects:
        - resolve_*() methods create absolute paths based on execution environment
        - Path() automatically detects Windows vs POSIX environment
    """
    project_root: Path  # 実行時に渡される実パス
    manuscripts: str = "40_原稿/"
    management: str = "50_管理資料/"
    settings: str = "30_設定集/"
    plots: str = "20_プロット/"

    def resolve_manuscripts_dir(self) -> Path:
        """原稿ディレクトリの絶対パスを取得（環境自動判定）

        Returns:
            Absolute path to manuscripts directory (WindowsPath on Windows, PosixPath on WSL/Linux)
        """
        return self.project_root / self.manuscripts

    def resolve_management_dir(self) -> Path:
        """管理資料ディレクトリの絶対パスを取得（環境自動判定）

        Returns:
            Absolute path to management directory (WindowsPath on Windows, PosixPath on WSL/Linux)
        """
        return self.project_root / self.management

    def resolve_settings_dir(self) -> Path:
        """設定ディレクトリの絶対パスを取得（環境自動判定）

        Returns:
            Absolute path to settings directory (WindowsPath on Windows, PosixPath on WSL/Linux)
        """
        return self.project_root / self.settings

    def resolve_plots_dir(self) -> Path:
        """プロットディレクトリの絶対パスを取得（環境自動判定）

        Returns:
            Absolute path to plot documents directory (WindowsPath on Windows, PosixPath on WSL/Linux)
        """
        return self.project_root / self.plots


@dataclass
class SettingsFileNames:
    """設定ファイル名の標準定義

    ファイル名のみを保持。実際のパスはProjectPathsと組み合わせて解決。

    Args:
        world_settings: Filename for world-building settings
        character_settings: Filename for character definitions
        glossary: Filename for term glossary
        style_guide: Filename for writing style guide

    Preconditions:
        - All filenames must include .yaml extension
        - Filenames should not contain path separators

    Side effects:
        - resolve_*() methods combine with settings_dir to create absolute paths
    """
    world_settings: str = "世界観.yaml"
    character_settings: str = "キャラクター.yaml"
    glossary: str = "用語集.yaml"
    style_guide: str = "文体ガイド.yaml"

    def resolve_world_path(self, settings_dir: Path) -> Path:
        """世界観設定ファイルの絶対パス

        Args:
            settings_dir: Absolute path to settings directory

        Returns:
            Full absolute path to world settings file
        """
        return settings_dir / self.world_settings

    def resolve_character_path(self, settings_dir: Path) -> Path:
        """キャラクター設定ファイルの絶対パス

        Args:
            settings_dir: Absolute path to settings directory

        Returns:
            Full absolute path to character settings file
        """
        return settings_dir / self.character_settings

    def resolve_glossary_path(self, settings_dir: Path) -> Path:
        """用語集ファイルの絶対パス

        Args:
            settings_dir: Absolute path to settings directory

        Returns:
            Full absolute path to glossary file
        """
        return settings_dir / self.glossary

    def resolve_style_guide_path(self, settings_dir: Path) -> Path:
        """文体ガイドファイルの絶対パス

        Args:
            settings_dir: Absolute path to settings directory

        Returns:
            Full absolute path to style guide file
        """
        return settings_dir / self.style_guide


@dataclass
class ProjectSettings:
    """プロジェクト設定の統合構造

    Combines project paths and settings file names into a unified configuration.
    Provides high-level methods for accessing setting file paths and validating
    the project structure.

    Args:
        project_name: Name of the novel project
        paths: Project directory paths configuration
        settings_files: Settings file names configuration

    Preconditions:
        - project_name must be non-empty
        - paths.project_root must point to a valid directory
        - settings_files must contain valid YAML filenames

    Side effects:
        - validate() checks filesystem for directory and file existence
        - get_*_path() methods resolve absolute paths based on current environment

    Raises:
        No exceptions raised directly, but validate() returns error lists
    """
    project_name: str
    paths: ProjectPaths
    settings_files: SettingsFileNames

    def get_world_settings_path(self) -> Path:
        """世界観設定ファイルの完全パス

        Returns:
            Full absolute path to world settings YAML file
        """
        return self.settings_files.resolve_world_path(
            self.paths.resolve_settings_dir()
        )

    def get_character_settings_path(self) -> Path:
        """キャラクター設定ファイルの完全パス

        Returns:
            Full absolute path to character settings YAML file
        """
        return self.settings_files.resolve_character_path(
            self.paths.resolve_settings_dir()
        )

    def get_glossary_path(self) -> Path:
        """用語集ファイルの完全パス

        Returns:
            Full absolute path to glossary YAML file
        """
        return self.settings_files.resolve_glossary_path(
            self.paths.resolve_settings_dir()
        )

    def get_style_guide_path(self) -> Path:
        """文体ガイドファイルの完全パス

        Returns:
            Full absolute path to style guide YAML file
        """
        return self.settings_files.resolve_style_guide_path(
            self.paths.resolve_settings_dir()
        )

    def validate(self) -> dict[str, list[str]]:
        """設定の妥当性チェック

        Validates project structure by checking:
        - Existence of settings directory
        - Existence of mandatory settings files (world, character)

        Returns:
            Dictionary with "errors" and "warnings" keys, each containing
            a list of validation messages. Empty lists indicate no issues.

        Side effects:
            - Performs filesystem reads to check path existence
            - Does NOT create directories or files

        Example:
            >>> settings = ProjectSettings(...)
            >>> result = settings.validate()
            >>> if result["errors"]:
            ...     print("Configuration errors found:", result["errors"])
        """
        errors: list[str] = []
        warnings: list[str] = []

        # 必須ディレクトリの存在確認
        settings_dir = self.paths.resolve_settings_dir()
        if not settings_dir.exists():
            errors.append(f"設定ディレクトリが存在しません: {settings_dir}")

        # 必須ファイルの存在確認
        world_path = self.get_world_settings_path()
        if not world_path.exists():
            errors.append(f"世界観設定ファイルが見つかりません: {world_path}")

        character_path = self.get_character_settings_path()
        if not character_path.exists():
            errors.append(f"キャラクター設定ファイルが見つかりません: {character_path}")

        return {"errors": errors, "warnings": warnings}
