"""Infrastructure.repositories.yaml_episode_management_repository
Where: Infrastructure repository managing episode data via YAML.
What: Handles CRUD operations for episode metadata and statuses stored as YAML.
Why: Provides a file-based implementation for episode management needs.
"""

from noveler.infrastructure.utils.yaml_utils import YAMLHandler

#!/usr/bin/env python3
"""YAMLエピソード管理リポジトリ実装
Infrastructure層:技術的実装の詳細
"""

import os
import shutil
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.episode_management_repository import (
    EpisodeManagementRepository,
    FileBackupRepository,
    FilePermissionRepository,
)


class YamlEpisodeManagementRepository(EpisodeManagementRepository):
    """YAML形式の話数管理リポジトリ実装"""

    def load_episode_management_data(self, project_path: str | Path) -> dict[str, Any]:
        """話数管理データを読み込む"""
        yaml_path = Path(project_path) / "50_管理資料" / "話数管理.yaml"

        if not yaml_path.exists():
            msg = f"話数管理.yamlファイルが見つかりません: {yaml_path}"
            raise FileNotFoundError(msg)

        try:
            with yaml_path.Path(encoding="utf-8").open() as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            msg = f"話数管理ファイルの読み込みに失敗しました: {e}"
            raise OSError(msg) from e

    def save_episode_management_data(self, project_path: str | Path, data: dict[str, Any]) -> None:
        """話数管理データを保存する"""
        yaml_path = Path(project_path) / "50_管理資料" / "話数管理.yaml"
        yaml_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # YAMLHandlerを使用して整形付き保存を試みる
            try:
                YAMLHandler.save_yaml(yaml_path, data, use_formatter=True, create_backup=False)
            except ImportError:
                # フォールバック: 従来の方法で保存
                with yaml_path.Path("w").open(encoding="utf-8") as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            msg = f"話数管理ファイルの保存に失敗しました: {e}"
            raise OSError(msg) from e

    def get_episode_data(self, project_path: str, episode_number: int) -> dict[str, Any]:
        """特定のエピソードデータを取得する"""
        data = self.load_episode_management_data(project_path)
        episode_key = f"第{episode_number:03d}話"

        if "episodes" not in data or episode_key not in data["episodes"]:
            msg = f"エピソード番号{episode_number}が見つかりません"
            raise ValueError(msg)

        return data["episodes"][episode_key]

    def update_episode_data(self, project_path: str | Path, episode_number: int, episode_data: dict[str, Any]) -> None:
        """特定のエピソードデータを更新する"""
        data = self.load_episode_management_data(project_path)
        episode_key = f"第{episode_number:03d}話"

        if "episodes" not in data:
            data["episodes"] = {}

        data["episodes"][episode_key] = episode_data
        self.save_episode_management_data(project_path, data)

    def episode_exists(self, project_path: str, episode_number: int) -> bool:
        """エピソードが存在するかチェックする"""
        try:
            self.get_episode_data(project_path, episode_number)
            return True
        except (FileNotFoundError, ValueError):
            return False


class FileSystemBackupRepository(FileBackupRepository):
    """ファイルシステムベースのバックアップリポジトリ実装"""

    def create_backup(self, file_path: str | Path) -> str:
        """ファイルのバックアップを作成し、バックアップファイルパスを返す"""
        original_path = Path(file_path)
        backup_path = original_path.with_suffix(original_path.suffix + ".bak")

        try:
            shutil.copy2(original_path, backup_path)
            return str(backup_path)
        except Exception as e:
            msg = f"バックアップの作成に失敗しました: {e}"
            raise OSError(msg) from e

    def restore_from_backup(self, original_path: str, backup_path: str | Path) -> None:
        """バックアップからファイルを復元する"""
        try:
            shutil.copy2(backup_path, original_path)
        except Exception as e:
            msg = f"バックアップからの復元に失敗しました: {e}"
            raise OSError(msg) from e

    def delete_backup(self, backup_path: str | Path) -> None:
        """バックアップファイルを削除する"""
        try:
            Path(backup_path).unlink(missing_ok=True)
        except Exception as e:
            msg = f"バックアップファイルの削除に失敗しました: {e}"
            raise OSError(msg) from e


class FileSystemPermissionRepository(FilePermissionRepository):
    """ファイルシステムベースの権限チェックリポジトリ実装"""

    def has_read_permission(self, file_path: str | Path) -> bool:
        """読み取り権限があるかチェック"""
        return os.access(file_path, os.R_OK)

    def has_write_permission(self, file_path: str | Path) -> bool:
        """書き込み権限があるかチェック"""
        return os.access(file_path, os.W_OK)

    def file_exists(self, file_path: str | Path) -> bool:
        """ファイルが存在するかチェック"""
        return Path(file_path).exists()
