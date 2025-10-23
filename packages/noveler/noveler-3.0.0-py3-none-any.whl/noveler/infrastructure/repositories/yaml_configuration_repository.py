#!/usr/bin/env python3
"""YAML設定リポジトリ実装
Infrastructure層:技術的実装の詳細
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.interfaces.i_path_service import IPathService
from noveler.domain.repositories.configuration_repository import (
    ConfigurationRepository,
    EpisodeManagementDataRepository,
    ManuscriptRepository,
)
from noveler.infrastructure.repositories.base_yaml_repository import BaseYamlRepository


class YamlConfigurationRepository(BaseYamlRepository, ConfigurationRepository):
    """YAML形式の設定リポジトリ実装

    IPathServiceインターフェースを使用してパス操作を統一化。
    """

    def __init__(self, path_service: IPathService | None = None) -> None:
        """初期化

        Args:
            path_service: パスサービス（Noneの場合は自動検出）
        """
        self._path_service = path_service

    def load_config(self, config_path: Path) -> dict[str, Any]:
        """統合設定ファイル（novel_config.yaml）を読み込む

        Args:
            config_path: 設定ファイルパス

        Returns:
            設定データ辞書

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            yaml.YAMLError: YAML解析エラーの場合
            OSError: その他のファイル読み込みエラー
        """
        return self._load_yaml_file(config_path)

    def load_project_config(self, project_path: str | Path) -> dict[str, Any]:
        """プロジェクト設定を読み込む"""
        config_file = Path(project_path) / "プロジェクト設定.yaml"
        return self._load_yaml_file(config_file)

    def save_project_config(self, project_path: str | Path, config_data: dict[str, Any]) -> None:
        """プロジェクト設定を保存する"""
        config_file = Path(project_path) / "プロジェクト設定.yaml"

        try:
            with config_file.open("w", encoding="utf-8") as f:
                yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            msg = f"設定ファイルの保存に失敗しました: {e}"
            raise OSError(msg) from e

    def load_quality_config(self, project_path: str | Path) -> dict[str, Any]:
        """品質チェック設定を読み込む"""
        path_service = self._get_path_service(project_path)
        config_file = path_service.get_quality_config_file()

        if not config_file.exists():
            # デフォルト設定を返す
            return {"max_length": 3000, "check_spelling": True, "check_grammar": True}

        return self._load_yaml_file(config_file)

    def save_quality_config(self, project_path: str | Path, config_data: dict[str, Any]) -> None:
        """品質チェック設定を保存する"""
        path_service = self._get_path_service(project_path)
        config_file = path_service.get_quality_config_file()
        config_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with config_file.open("w", encoding="utf-8") as f:
                yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            msg = f"品質設定ファイルの保存に失敗しました: {e}"
            raise OSError(msg) from e

    def project_exists(self, project_path: str | Path) -> bool:
        """プロジェクトディレクトリが存在するか確認"""
        return Path(project_path).exists()

    def _get_path_service(self, project_path: str | Path) -> IPathService:
        """パスサービスを取得（遅延初期化）

        Args:
            project_path: プロジェクトパス

        Returns:
            IPathService: パスサービスインスタンス
        """
        if self._path_service is None:
            from noveler.infrastructure.adapters.path_service_adapter import create_path_service

            self._path_service = create_path_service(Path(project_path))
        return self._path_service


class MarkdownManuscriptRepository(ManuscriptRepository):
    """Markdown原稿リポジトリ実装

    IPathServiceインターフェースを使用してパス操作を統一化。
    """

    def __init__(self, path_service: IPathService | None = None) -> None:
        """初期化

        Args:
            path_service: パスサービス（Noneの場合は自動検出）
        """
        self._path_service = path_service

    def load_episode_content(self, project_path: str, episode_number: int) -> str:
        """エピソードの原稿内容を読み込む"""
        path_service = self._get_path_service(project_path)
        manuscript_file = path_service.get_manuscript_path(episode_number)
        if not manuscript_file.exists():
            msg = f"第{episode_number:03d}話の原稿ファイルが見つかりません: {manuscript_file}"
            raise FileNotFoundError(msg)
        try:
            return manuscript_file.read_text(encoding="utf-8")
        except Exception as e:
            msg = f"原稿ファイルの読み込みに失敗しました: {e}"
            raise OSError(msg) from e

    def save_episode_content(self, project_path: str, episode_number: int, content: str) -> None:
        """エピソードの原稿内容を保存する"""
        path_service = self._get_path_service(project_path)
        manuscript_file = path_service.get_manuscript_path(episode_number)
        manuscript_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            # バッチ書き込みを使用
            manuscript_file.write_text(content, encoding="utf-8")
        except Exception as e:
            msg = f"原稿ファイルの保存に失敗しました: {e}"
            raise OSError(msg) from e

    def list_episodes(self, project_path: str) -> list[int]:
        """プロジェクトの全エピソード番号を取得"""
        path_service = self._get_path_service(project_path)
        manuscript_dir = path_service.get_manuscript_dir()

        if not manuscript_dir.exists():
            return []

        episode_numbers = []
        for file_path in manuscript_dir.glob("第*話_*.md"):
            try:
                # ファイル名から番号を抽出
                number_part = file_path.stem.split("_")[0][1:4]  # "第001話" -> "001"
                episode_numbers.append(int(number_part))
            except (ValueError, IndexError):
                continue

        return sorted(episode_numbers)

    def _get_path_service(self, project_path: str | Path) -> IPathService:
        """パスサービスを取得（遅延初期化）

        Args:
            project_path: プロジェクトパス

        Returns:
            IPathService: パスサービスインスタンス
        """
        if self._path_service is None:
            from noveler.infrastructure.adapters.path_service_adapter import create_path_service

            self._path_service = create_path_service(Path(project_path))
        return self._path_service


class YamlEpisodeManagementDataRepository(EpisodeManagementDataRepository, BaseYamlRepository):
    """YAML話数管理データリポジトリ実装

    IPathServiceインターフェースを使用してパス操作を統一化。
    """

    def __init__(self, path_service: IPathService | None = None) -> None:
        """初期化

        Args:
            path_service: パスサービス（Noneの場合は自動検出）
        """
        self._path_service = path_service

    def load_episode_management(self, project_path: str | Path) -> dict[str, Any]:
        """話数管理データを読み込む"""
        path_service = self._get_path_service(project_path)
        management_file = path_service.get_episode_management_file()

        if not management_file.exists():
            return {"episodes": {}}

        config_data = self._load_yaml_file(management_file)
        return config_data or {"episodes": {}}

    def save_episode_management(self, project_path: str | Path, data: dict[str, Any]) -> None:
        """話数管理データを保存する"""
        path_service = self._get_path_service(project_path)
        management_file = path_service.get_episode_management_file()
        management_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with management_file.open("w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            msg = f"話数管理ファイルの保存に失敗しました: {e}"
            raise OSError(msg) from e

    def get_episode_metadata(self, project_path: str, episode_number: int) -> dict[str, Any]:
        """特定エピソードのメタデータを取得"""
        data = self.load_episode_management(project_path)
        episodes = data.get("episodes", {})

        episode_key = f"第{episode_number:03d}話"
        return episodes.get(episode_key, {})

    def update_episode_metadata(self, project_path: str, episode_number: int, metadata: dict[str, Any]) -> None:
        """特定エピソードのメタデータを更新"""
        data = self.load_episode_management(project_path)
        episodes = data.setdefault("episodes", {})

        episode_key = f"第{episode_number:03d}話"
        episodes[episode_key] = metadata

        self.save_episode_management(project_path, data)

    def _get_path_service(self, project_path: str | Path) -> IPathService:
        """パスサービスを取得（遅延初期化）

        Args:
            project_path: プロジェクトパス

        Returns:
            IPathService: パスサービスインスタンス
        """
        if self._path_service is None:
            from noveler.infrastructure.adapters.path_service_adapter import create_path_service

            self._path_service = create_path_service(Path(project_path))
        return self._path_service
