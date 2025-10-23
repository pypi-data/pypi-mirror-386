#!/usr/bin/env python3
"""話数管理リポジトリインターフェース"""

from abc import ABC, abstractmethod
from typing import Any


class EpisodeManagementRepository(ABC):
    """話数管理リポジトリのインターフェース"""

    @abstractmethod
    def load_episode_management_data(self, project_path: str) -> dict[str, Any]:
        """話数管理データを読み込む"""

    @abstractmethod
    def save_episode_management_data(self, project_path: str, data: dict[str, Any]) -> None:
        """話数管理データを保存する"""

    @abstractmethod
    def get_episode_data(self, project_path: str, episode_number: int) -> dict[str, Any]:
        """特定のエピソードデータを取得する"""

    @abstractmethod
    def update_episode_data(self, project_path: str, episode_number: int) -> None:
        """特定のエピソードデータを更新する"""

    @abstractmethod
    def episode_exists(self, project_path: str, episode_number: int) -> bool:
        """エピソードが存在するかチェックする"""


class FileBackupRepository(ABC):
    """ファイルバックアップリポジトリのインターフェース"""

    @abstractmethod
    def create_backup(self, file_path: str) -> str:
        """ファイルのバックアップを作成し、バックアップファイルパスを返す"""

    @abstractmethod
    def restore_from_backup(self, original_path: str, backup_path: str) -> None:
        """バックアップからファイルを復元する"""

    @abstractmethod
    def delete_backup(self, backup_path: str) -> None:
        """バックアップファイルを削除する"""


class FilePermissionRepository(ABC):
    """ファイル権限チェックリポジトリのインターフェース"""

    @abstractmethod
    def has_read_permission(self, file_path: str) -> bool:
        """読み取り権限があるかチェック"""

    @abstractmethod
    def has_write_permission(self, file_path: str) -> bool:
        """書き込み権限があるかチェック"""

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """ファイルが存在するかチェック"""
