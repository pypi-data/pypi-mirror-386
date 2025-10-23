"""ファイルバックアップ用リポジトリインターフェース."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class FileBackupRepository(ABC):
    """ファイルバックアップの永続化を担当するリポジトリインターフェース."""

    @abstractmethod
    def create_backup(self, file_path: Path, backup_name: str | None = None) -> str:
        """ファイルのバックアップを作成.

        Args:
            file_path: バックアップ対象のファイルパス
            backup_name: バックアップ名(省略時は自動生成)

        Returns:
            作成されたバックアップID
        """

    @abstractmethod
    def restore_backup(self, backup_id: str, target_path: Path) -> bool:
        """バックアップを復元.

        Args:
            backup_id: バックアップID
            target_path: 復元先のパス

        Returns:
            復元成功時True
        """

    @abstractmethod
    def list_backups(self, file_path: Path | None = None) -> list[dict[str, Any]]:
        """バックアップリストを取得.

        Args:
            file_path: 特定ファイルのバックアップのみを取得(省略時は全て)

        Returns:
            バックアップ情報のリスト
        """

    @abstractmethod
    def delete_backup(self, backup_id: str) -> bool:
        """バックアップを削除.

        Args:
            backup_id: バックアップID

        Returns:
            削除成功時True
        """

    @abstractmethod
    def get_backup_info(self, backup_id: str) -> dict[str, Any] | None:
        """バックアップ情報を取得.

        Args:
            backup_id: バックアップID

        Returns:
            バックアップ情報、存在しない場合はNone
        """

    @abstractmethod
    def cleanup_old_backups(self, days: int) -> int:
        """古いバックアップを削除.

        Args:
            days: 保持期間(日数)

        Returns:
            削除されたバックアップの数
        """
