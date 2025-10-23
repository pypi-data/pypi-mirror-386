"""Infrastructure.unit_of_work.filesystem_backup_unit_of_work
Where: Infrastructure unit-of-work tailored for filesystem backups.
What: Manages filesystem backup repositories and ensures cleanup on failure.
Why: Provides reliable transaction handling for filesystem backup operations.
"""

from __future__ import annotations

"""ファイルシステムバックアップUnit of Work

B20準拠実装 - Unit of Work Pattern
"""

import shutil
from pathlib import Path

from noveler.domain.interfaces.path_service import IPathService
from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.unit_of_work.backup_unit_of_work import BackupUnitOfWork


class FilesystemBackupUnitOfWork(BackupUnitOfWork):
    """ファイルシステムバックアップUnit of Work

    B20準拠 Unit of Work Pattern:
    - トランザクション境界管理
    - 作業単位の統一コミット・ロールバック
    - リソース管理
    """

    def __init__(self, *, path_service: IPathService) -> None:
        """Unit of Work初期化"""
        self._path_service = path_service
        self._pending_operations: list[dict] = []
        self._backup_temp_dir: Path | None = None
        self._is_committed = False

    def __enter__(self):
        """コンテキスト開始 - トランザクション開始"""
        self._backup_temp_dir = self._path_service.get_temp_dir() / "backup_transaction"
        self._backup_temp_dir.mkdir(exist_ok=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキスト終了 - リソースクリーンアップ"""
        if not self._is_committed and exc_type is None:
            # 正常終了時で未コミットの場合は自動ロールバック
            self.rollback()

        # 一時ディレクトリクリーンアップ
        if self._backup_temp_dir and self._backup_temp_dir.exists():
            shutil.rmtree(self._backup_temp_dir)

    def add_operation(self, operation_type: str, **kwargs) -> None:
        """操作追加 - Functional Core（純粋関数的）"""
        if self._is_committed:
            msg = "コミット済みのトランザクションに操作を追加できません"
            raise ValueError(msg)

        operation = {"type": operation_type, "timestamp": self._get_current_timestamp(), **kwargs}

        self._pending_operations.append(operation)

    def commit(self) -> None:
        """コミット - 全操作の永続化"""
        if self._is_committed:
            msg = "既にコミット済みです"
            raise ValueError(msg)

        try:
            for operation in self._pending_operations:
                self._execute_operation(operation)

            self._is_committed = True

        except Exception as e:
            self.rollback()
            msg = f"コミット失敗: {e}"
            raise RuntimeError(msg)

    def rollback(self) -> None:
        """ロールバック - 全操作の取り消し"""
        # 一時的な変更を元に戻す
        self._pending_operations.clear()

        # 一時ファイルの削除は __exit__ で処理される

    def _execute_operation(self, operation: dict) -> None:
        """操作実行 - Imperative Shell"""
        operation_type = operation["type"]

        if operation_type == "create_backup":
            self._execute_create_backup(operation)
        elif operation_type == "migrate_folder":
            self._execute_migrate_folder(operation)
        elif operation_type == "cleanup_old":
            self._execute_cleanup_old(operation)
        else:
            msg = f"未対応操作タイプ: {operation_type}"
            raise ValueError(msg)

    def _execute_create_backup(self, operation: dict) -> None:
        """バックアップ作成実行"""
        source_path = Path(operation["source_path"])
        target_path = Path(operation["target_path"])

        if operation.get("compression", False):
            self._create_compressed_backup(source_path, target_path)
        else:
            self._create_folder_backup(source_path, target_path)

    def _execute_migrate_folder(self, operation: dict) -> None:
        """フォルダ移行実行"""
        source_path = Path(operation["source_path"])
        target_path = Path(operation["target_path"])

        shutil.move(str(source_path), str(target_path))

    def _execute_cleanup_old(self, operation: dict) -> None:
        """古いバックアップクリーンアップ実行"""
        target_path = Path(operation["target_path"])

        if target_path.exists():
            if target_path.is_file():
                target_path.unlink()
            else:
                shutil.rmtree(target_path)

    def _create_compressed_backup(self, source: Path, target: Path) -> None:
        """圧縮バックアップ作成"""
        # .tar.gz形式で圧縮
        shutil.make_archive(str(target.with_suffix("")), "gztar", str(source.parent), str(source.name))

    def _create_folder_backup(self, source: Path, target: Path) -> None:
        """フォルダバックアップ作成"""
        shutil.copytree(str(source), str(target), dirs_exist_ok=True)

    def _get_current_timestamp(self) -> str:
        """現在タイムスタンプ取得 - Functional Core（純粋関数）"""

        return project_now().datetime.strftime("%Y%m%d_%H%M%S")
