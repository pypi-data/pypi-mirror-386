"""Infrastructure.repositories.filesystem_backup_repository
Where: Infrastructure repository handling filesystem-based backups.
What: Manages backup metadata, versions, and file storage operations.
Why: Supports comprehensive backup workflows with persistent storage.
"""

from __future__ import annotations

"""ファイルシステムバックアップリポジトリ

B20準拠実装 - Repository Pattern Implementation
"""

from pathlib import Path

from noveler.noveler.domain.repositories.backup_repository import (
    BackupRepository,
    BackupResult,
)
from noveler.noveler.domain.value_objects.backup_strategy import BackupStrategy
from noveler.noveler.domain.value_objects.backup_type import BackupType
from noveler.noveler.infrastructure.adapters.logger_service_adapter import LoggerServiceProtocol
from noveler.noveler.infrastructure.adapters.path_service_adapter import PathServiceProtocol


class FilesystemBackupRepository(BackupRepository):
    """ファイルシステムバックアップリポジトリ

    B20準拠 Repository Pattern:
    - データ永続化の抽象化
    - ドメインモデルとインフラの分離
    - Functional Core + Imperative Shell
    """

    def __init__(self, *, path_service: PathServiceProtocol, logger_service: LoggerServiceProtocol) -> None:
        """リポジトリ初期化"""
        self._path_service = path_service
        self._logger_service = logger_service

    def create_backup(
        self, *, backup_type: BackupType, strategy: BackupStrategy, dry_run: bool = False
    ) -> BackupResult:
        """バックアップ作成 - Repository Pattern"""
        try:
            self._logger_service.info(f"バックアップ作成開始: {backup_type.value}")

            # バックアップパス生成
            backup_path = self._generate_backup_path(backup_type, strategy)

            if dry_run:
                return self._simulate_backup_creation(backup_path, strategy)

            # 実際のバックアップ作成
            return self._execute_backup_creation(backup_path, strategy)

        except Exception as e:
            self._logger_service.error(f"バックアップ作成失敗: {e}")
            return BackupResult(success=False, backup_path=None, size_mb=0.0, errors=[str(e)])

    def list_backups(self, backup_type: BackupType | None = None) -> list[Path]:
        """バックアップ一覧取得"""
        try:
            backup_base_dir = self._path_service.get_backups_dir()

            if not backup_base_dir.exists():
                return []

            backups = []
            for backup_path in backup_base_dir.iterdir():
                if backup_path.is_dir():
                    if backup_type is None or self._matches_backup_type(backup_path, backup_type):
                        backups.append(backup_path)

            return sorted(backups, key=lambda p: p.stat().st_mtime, reverse=True)

        except Exception as e:
            self._logger_service.error(f"バックアップ一覧取得失敗: {e}")
            return []

    def delete_backup(self, backup_path: Path, dry_run: bool = False) -> bool:
        """バックアップ削除"""
        try:
            if not backup_path.exists():
                return True

            if dry_run:
                self._logger_service.info(f"削除対象(DRY-RUN): {backup_path}")
                return True

            if backup_path.is_file():
                backup_path.unlink()
            else:
                import shutil

                shutil.rmtree(backup_path)

            self._logger_service.info(f"バックアップ削除完了: {backup_path}")
            return True

        except Exception as e:
            self._logger_service.error(f"バックアップ削除失敗: {e}")
            return False

    def _generate_backup_path(self, backup_type: BackupType, strategy: BackupStrategy) -> Path:
        """バックアップパス生成 - Functional Core（純粋関数）"""
        from datetime import datetime, timezone

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_name = f"{backup_type.value}_{timestamp}"

        if strategy.purpose and strategy.purpose != backup_type.value:
            # 目的を含む場合
            safe_purpose = strategy.purpose.replace(" ", "_").replace("　", "_")
            backup_name += f"_{safe_purpose}"

        backup_base_dir = self._path_service.get_backups_dir()

        if strategy.compression_enabled:
            return backup_base_dir / f"{backup_name}.tar.gz"
        return backup_base_dir / backup_name

    def _simulate_backup_creation(self, backup_path: Path, strategy: BackupStrategy) -> BackupResult:
        """バックアップ作成シミュレーション - Functional Core"""
        # 推定サイズ計算
        estimated_size = 0.0
        for target_path in strategy.target_paths:
            if target_path.exists():
                size_mb = self._calculate_directory_size_mb(target_path)
                filtered_size = self._apply_exclusion_filter(size_mb, strategy)
                estimated_size += filtered_size

        final_size = strategy.calculate_estimated_size_mb(estimated_size)

        return BackupResult(success=True, backup_path=backup_path, size_mb=final_size, errors=[])

    def _execute_backup_creation(self, backup_path: Path, strategy: BackupStrategy) -> BackupResult:
        """バックアップ作成実行 - Imperative Shell"""
        # バックアップディレクトリ作成
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        total_size_mb = 0.0
        errors = []

        try:
            if strategy.compression_enabled:
                total_size_mb = self._create_compressed_backup(backup_path, strategy)
            else:
                total_size_mb = self._create_folder_backup(backup_path, strategy)

            return BackupResult(success=len(errors) == 0, backup_path=backup_path, size_mb=total_size_mb, errors=errors)

        except Exception as e:
            errors.append(f"バックアップ作成エラー: {e!s}")
            return BackupResult(success=False, backup_path=None, size_mb=0.0, errors=errors)

    def _create_compressed_backup(self, backup_path: Path, strategy: BackupStrategy) -> float:
        """圧縮バックアップ作成"""
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "backup_staging"
            temp_path.mkdir()

            # ファイルを一時ディレクトリにコピー（除外フィルタ適用）
            for target_path in strategy.target_paths:
                if target_path.exists():
                    self._copy_with_exclusion(target_path, temp_path / target_path.name, strategy)

            # 圧縮実行
            archive_base = str(backup_path.with_suffix(""))
            shutil.make_archive(archive_base, "gztar", temp_dir, "backup_staging")

            # サイズ取得
            return backup_path.stat().st_size / (1024 * 1024)

    def _create_folder_backup(self, backup_path: Path, strategy: BackupStrategy) -> float:
        """フォルダバックアップ作成"""
        total_size = 0

        backup_path.mkdir(parents=True, exist_ok=True)

        for target_path in strategy.target_paths:
            if target_path.exists():
                dest_path = backup_path / target_path.name
                size = self._copy_with_exclusion(target_path, dest_path, strategy)
                total_size += size

        return total_size / (1024 * 1024)

    def _copy_with_exclusion(self, source: Path, dest: Path, strategy: BackupStrategy) -> int:
        """除外フィルタ適用コピー"""
        import shutil

        if strategy.should_exclude(source):
            return 0

        total_size = 0

        if source.is_file():
            shutil.copy2(source, dest)
            total_size = source.stat().st_size
        elif source.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            for item in source.iterdir():
                if not strategy.should_exclude(item):
                    item_dest = dest / item.name
                    size = self._copy_with_exclusion(item, item_dest, strategy)
                    total_size += size

        return total_size

    def _calculate_directory_size_mb(self, directory: Path) -> float:
        """ディレクトリサイズ計算 - Functional Core（純粋関数）"""
        try:
            total_size = sum(f.stat().st_size for f in directory.rglob("*") if f.is_file())
            return total_size / (1024 * 1024)
        except Exception:
            return 0.0

    def _apply_exclusion_filter(self, size_mb: float, strategy: BackupStrategy) -> float:
        """除外フィルタ適用サイズ推定 - Functional Core（純粋関数）"""
        # 除外パターン数に応じて削減率推定
        reduction_rate = len(strategy.exclude_patterns) * 0.15  # 15%ずつ削減
        return size_mb * (1 - min(reduction_rate, 0.8))  # 最大80%削減

    def _matches_backup_type(self, backup_path: Path, backup_type: BackupType) -> bool:
        """バックアップタイプマッチング判定 - Functional Core（純粋関数）"""
        return backup_type.value in backup_path.name.lower()
