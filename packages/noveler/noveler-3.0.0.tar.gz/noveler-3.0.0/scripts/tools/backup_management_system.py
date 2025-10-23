#!/usr/bin/env python3
"""統一バックアップ管理システム

既存のカオス状態を整理し、統一されたバックアップ管理を実現
CLAUDE.md準拠: DDD構造、scripts.プレフィックス、Path Service使用
"""

from typing import Optional
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.configuration.configuration_manager import get_configuration_manager
from noveler.infrastructure.logging.unified_logger import get_logger


class BackupType(Enum):
    """バックアップタイプ定義"""
    AUTOMATED_DAILY = "automated/daily"
    PRE_OPERATION = "automated/pre_operation"
    SYSTEM_RECOVERY = "automated/system_recovery"
    MANUAL = "manual"
    TEMPORARY = "temp"


class BackupStatus(Enum):
    """バックアップ状態"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class BackupResult:
    """バックアップ実行結果"""
    status: BackupStatus
    backup_path: Path | None
    source_path: Path
    backup_size: float  # MB
    file_count: int
    execution_time: float  # seconds
    error_message: str | None = None


@dataclass
class CleanupResult:
    """クリーンアップ実行結果"""
    removed_backups: list[Path]
    freed_space: float  # MB
    errors: list[str]


@dataclass
class MigrationResult:
    """移行実行結果"""
    migrated_backups: list[tuple[Path, Path]]  # (source, destination)
    removed_legacy: list[Path]
    migration_errors: list[str]
    total_freed_space: float  # MB


class UnifiedBackupManager:
    """統一バックアップ管理システム

    既存のBackupUseCaseとの互換性を保ちながら、
    カオス状態のバックアップフォルダを統一管理
    """

    def __init__(self):
        """初期化"""
        self.path_service = create_path_service()
        self.config_manager = get_configuration_manager()
        self.backup_root = self._ensure_backup_root()
        self.logger = self._setup_logger()

    def _ensure_backup_root(self) -> Path:
        """統一バックアップルートディレクトリの確保"""
        # Path Serviceを使用してプロジェクトルート取得
        project_root = self.path_service.get_project_root()
        backup_root = project_root / "backups"

        # 標準ディレクトリ構造作成
        directories = [
            backup_root / "automated" / "daily",
            backup_root / "automated" / "pre_operation",
            backup_root / "automated" / "system_recovery",
            backup_root / "manual",
            backup_root / "archive",
            backup_root / "temp"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        return backup_root

    def _setup_logger(self):
        """ロガー設定（統一ロガー使用）"""
        return get_logger("UnifiedBackupManager")

    def create_backup(self,
                     source_path: Path,
                     backup_type: BackupType,
                     context: str = "",
                     purpose: str = "") -> BackupResult:
        """統一バックアップ作成

        Args:
            source_path: バックアップ対象パス
            backup_type: バックアップタイプ
            context: コンテキスト情報（操作名など）
            purpose: バックアップ目的（手動バックアップ用）

        Returns:
            BackupResult: 実行結果
        """
        start_time = datetime.now()

        try:
            # バックアップ先パス生成
            timestamp = start_time.strftime("%Y%m%d_%H%M%S")
            backup_name = self._generate_backup_name(backup_type, timestamp, context, purpose)
            backup_path = self.backup_root / backup_type.value / backup_name

            # バックアップ実行
            self.logger.info(f"バックアップ開始: {source_path} -> {backup_path}")

            if source_path.is_file():
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, backup_path)
                file_count = 1
            else:
                shutil.copytree(source_path, backup_path, dirs_exist_ok=True)
                file_count = sum(1 for _ in backup_path.rglob("*") if _.is_file())

            # バックアップサイズ計算
            backup_size = self._calculate_size(backup_path)
            execution_time = (datetime.now() - start_time).total_seconds()

            self.logger.info(
                f"バックアップ完了: {backup_size:.2f}MB, "
                f"{file_count}ファイル, {execution_time:.2f}秒"
            )

            return BackupResult(
                status=BackupStatus.SUCCESS,
                backup_path=backup_path,
                source_path=source_path,
                backup_size=backup_size,
                file_count=file_count,
                execution_time=execution_time
            )

        except Exception as e:
            self.logger.error(f"バックアップ失敗: {e}")
            return BackupResult(
                status=BackupStatus.FAILED,
                backup_path=None,
                source_path=source_path,
                backup_size=0.0,
                file_count=0,
                execution_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )

    def _generate_backup_name(self,
                            backup_type: BackupType,
                            timestamp: str,
                            context: str = "",
                            purpose: str = "") -> str:
        """バックアップ名生成"""
        if backup_type == BackupType.AUTOMATED_DAILY:
            return f"daily_{timestamp}"
        if backup_type == BackupType.PRE_OPERATION:
            return f"{context}_{timestamp}" if context else f"operation_{timestamp}"
        if backup_type == BackupType.SYSTEM_RECOVERY:
            return f"recovery_{context}_{timestamp}" if context else f"recovery_{timestamp}"
        if backup_type == BackupType.MANUAL:
            return f"{purpose}_{timestamp}" if purpose else f"manual_{timestamp}"
        if backup_type == BackupType.TEMPORARY:
            return f"temp_{context}_{timestamp}" if context else f"temp_{timestamp}"
        return f"backup_{timestamp}"

    def _calculate_size(self, path: Path) -> float:
        """パスのサイズ計算（MB）"""
        if path.is_file():
            return path.stat().st_size / (1024 * 1024)

        total_size = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)

    def cleanup_old_backups(self, dry_run: bool = False) -> CleanupResult:
        """古いバックアップの自動削除

        Args:
            dry_run: True の場合、削除せずに対象のみ表示

        Returns:
            CleanupResult: クリーンアップ結果
        """
        # 保持ポリシー取得（設定から）
        retention_days = {
            BackupType.AUTOMATED_DAILY: 7,
            BackupType.PRE_OPERATION: 30,
            BackupType.SYSTEM_RECOVERY: 90,
            BackupType.MANUAL: 365,
            BackupType.TEMPORARY: 1
        }

        removed_backups = []
        freed_space = 0.0
        errors = []

        for backup_type, days in retention_days.items():
            type_dir = self.backup_root / backup_type.value
            if not type_dir.exists():
                continue

            cutoff_date = datetime.now() - timedelta(days=days)

            for backup_dir in type_dir.iterdir():
                if not backup_dir.is_dir():
                    continue

                # タイムスタンプ抽出と比較
                try:
                    # フォルダ名からタイムスタンプ抽出（最後の YYYYMMDD_HHMMSS パターン）
                    timestamp_str = self._extract_timestamp(backup_dir.name)
                    if not timestamp_str:
                        continue

                    backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                    if backup_date < cutoff_date:
                        size = self._calculate_size(backup_dir)

                        if not dry_run:
                            shutil.rmtree(backup_dir)
                            self.logger.info(f"古いバックアップ削除: {backup_dir}")

                        removed_backups.append(backup_dir)
                        freed_space += size

                except Exception as e:
                    errors.append(f"削除エラー {backup_dir}: {e}")
                    self.logger.error(f"削除エラー {backup_dir}: {e}")

        return CleanupResult(
            removed_backups=removed_backups,
            freed_space=freed_space,
            errors=errors
        )

    def _extract_timestamp(self, folder_name: str) -> str | None:
        """フォルダ名からタイムスタンプ抽出"""
        import re

        # YYYYMMDD_HHMMSS パターンを検索
        pattern = r"(\d{8}_\d{6})"
        match = re.search(pattern, folder_name)
        return match.group(1) if match else None

    def migrate_legacy_backups(self, dry_run: bool = False) -> MigrationResult:
        """既存のカオス状態バックアップの移行

        Args:
            dry_run: True の場合、移行せずに計画のみ表示

        Returns:
            MigrationResult: 移行結果
        """
        project_root = self.path_service.get_project_root()

        # 移行対象の既存バックアップパターン
        legacy_patterns = [
            "tests_backup_*",
            "specs_backup_*",
            "temp/ddd_fix_backups",
            "backup",
            "archive/backup_files",
            ".codemap_backups"
        ]

        migrated_backups = []
        removed_legacy = []
        migration_errors = []
        total_freed_space = 0.0

        for pattern in legacy_patterns:
            try:
                matches = list(project_root.glob(pattern))

                for legacy_path in matches:
                    if not legacy_path.exists():
                        continue

                    # 移行先決定
                    destination = self._determine_migration_destination(legacy_path)

                    if not dry_run:
                        # 移行実行
                        destination.parent.mkdir(parents=True, exist_ok=True)

                        if legacy_path.is_file():
                            shutil.copy2(legacy_path, destination)
                        else:
                            shutil.copytree(legacy_path, destination, dirs_exist_ok=True)

                        # 元の削除
                        size = self._calculate_size(legacy_path)
                        if legacy_path.is_file():
                            legacy_path.unlink()
                        else:
                            shutil.rmtree(legacy_path)

                        total_freed_space += size
                        removed_legacy.append(legacy_path)

                    migrated_backups.append((legacy_path, destination))

            except Exception as e:
                migration_errors.append(f"移行エラー {pattern}: {e}")
                self.logger.error(f"移行エラー {pattern}: {e}")

        return MigrationResult(
            migrated_backups=migrated_backups,
            removed_legacy=removed_legacy,
            migration_errors=migration_errors,
            total_freed_space=total_freed_space
        )

    def _determine_migration_destination(self, legacy_path: Path) -> Path:
        """レガシーパスの移行先決定"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = legacy_path.name

        # パターン別の移行先決定
        if "tests_backup" in name:
            return self.backup_root / "archive" / f"legacy_tests_{timestamp}"
        if "specs_backup" in name:
            return self.backup_root / "archive" / f"legacy_specs_{timestamp}"
        if "ddd_fix_backups" in str(legacy_path):
            return self.backup_root / "archive" / f"legacy_ddd_fix_{timestamp}"
        if name == "backup":
            return self.backup_root / "archive" / f"legacy_root_backup_{timestamp}"
        if "backup_files" in str(legacy_path):
            return self.backup_root / "archive" / f"legacy_archive_{timestamp}"
        if "codemap_backups" in name:
            return self.backup_root / "archive" / f"legacy_codemap_{timestamp}"
        return self.backup_root / "archive" / f"legacy_unknown_{timestamp}"

    def get_backup_status(self) -> dict[str, any]:
        """バックアップシステム状態取得"""
        status = {
            "backup_root": str(self.backup_root),
            "total_backups": 0,
            "total_size": 0.0,
            "by_type": {}
        }

        for backup_type in BackupType:
            type_dir = self.backup_root / backup_type.value
            if type_dir.exists():
                backups = [d for d in type_dir.iterdir() if d.is_dir()]
                type_size = sum(self._calculate_size(d) for d in backups)

                status["by_type"][backup_type.name] = {
                    "count": len(backups),
                    "size_mb": round(type_size, 2)
                }

                status["total_backups"] += len(backups)
                status["total_size"] += type_size

        status["total_size"] = round(status["total_size"], 2)
        return status


def main():
    """統一バックアップ管理システムのメイン処理"""
    manager = UnifiedBackupManager()

    print("=== 統一バックアップ管理システム ===\n")

    # 現在のステータス表示
    print("現在のバックアップ状況:")
    status = manager.get_backup_status()
    print(f"バックアップルート: {status['backup_root']}")
    print(f"総バックアップ数: {status['total_backups']}")
    print(f"総サイズ: {status['total_size']:.2f}MB\n")

    for type_name, info in status["by_type"].items():
        print(f"  {type_name}: {info['count']}個, {info['size_mb']:.2f}MB")

    print("\n" + "="*50)

    # レガシー移行プレビュー
    print("\nレガシーバックアップ移行計画（dry-run）:")
    migration_result = manager.migrate_legacy_backups(dry_run=True)

    print(f"移行対象: {len(migration_result.migrated_backups)}項目")
    for source, dest in migration_result.migrated_backups:
        print(f"  {source} -> {dest}")

    if migration_result.migration_errors:
        print(f"\n移行エラー: {len(migration_result.migration_errors)}件")
        for error in migration_result.migration_errors:
            print(f"  {error}")

    print("\n" + "="*50)

    # クリーンアップ計画
    print("\n古いバックアップクリーンアップ計画（dry-run）:")
    cleanup_result = manager.cleanup_old_backups(dry_run=True)

    print(f"削除対象: {len(cleanup_result.removed_backups)}項目")
    print(f"解放予定容量: {cleanup_result.freed_space:.2f}MB")

    for backup in cleanup_result.removed_backups:
        print(f"  {backup}")


if __name__ == "__main__":
    main()
