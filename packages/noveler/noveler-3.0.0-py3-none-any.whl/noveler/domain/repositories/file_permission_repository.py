"""ファイル権限管理用リポジトリインターフェース."""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path


class PermissionLevel(Enum):
    """権限レベル."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class FilePermissionRepository(ABC):
    """ファイル権限の永続化を担当するリポジトリインターフェース."""

    @abstractmethod
    def get_file_permissions(self, file_path: str) -> dict[str, list[PermissionLevel]]:
        """ファイルの権限設定を取得.

        Args:
            file_path: 対象ファイルパス

        Returns:
            ユーザー/グループごとの権限設定
        """

    @abstractmethod
    def set_file_permissions(self, file_path: str, permissions: dict[str, list[PermissionLevel]]) -> bool:
        """ファイルの権限設定を更新.

        Args:
            file_path: 対象ファイルパス
            permissions: 設定する権限

        Returns:
            設定成功時True
        """

    @abstractmethod
    def check_permission(self, file_path: str, user: str) -> bool:
        """特定ユーザーの権限を確認.

        Args:
            file_path: 対象ファイルパス
            user: ユーザー名
            permission: 確認する権限

        Returns:
            権限がある場合True
        """

    @abstractmethod
    def list_accessible_files(self, user: str, permission: PermissionLevel) -> list[Path]:
        """ユーザーがアクセス可能なファイル一覧を取得.

        Args:
            user: ユーザー名
            permission: 必要な権限レベル

        Returns:
            アクセス可能なファイルパスのリスト
        """

    @abstractmethod
    def backup_permissions(self, directory: str) -> str | None:
        """ディレクトリの権限設定をバックアップ.

        Args:
            directory: バックアップ対象ディレクトリ

        Returns:
            バックアップID、失敗時はNone
        """

    @abstractmethod
    def restore_permissions(self, backup_id: str) -> bool:
        """権限設定を復元.

        Args:
            backup_id: バックアップID

        Returns:
            復元成功時True
        """
