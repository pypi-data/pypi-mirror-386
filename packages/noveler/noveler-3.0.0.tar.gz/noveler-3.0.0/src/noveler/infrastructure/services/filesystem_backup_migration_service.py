"""Infrastructure.services.filesystem_backup_migration_service
Where: Infrastructure service migrating filesystem backups.
What: Handles backup format updates and migration routines.
Why: Keeps backup data aligned with evolving storage formats.
"""

from __future__ import annotations

"""ファイルシステムバックアップ移行サービス

B20準拠実装 - Domain Service Implementation
"""

from typing import TYPE_CHECKING

from noveler.domain.value_objects.project_time import project_now
from noveler.noveler.domain.services.backup_migration_service import (
    BackupMigrationService,
    CleanupResult,
    MigrationPhase,
    MigrationPlan,
    PhaseResult,
)
from noveler.noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceProtocol
from noveler.noveler.infrastructure.adapters.logger_service_adapter import LoggerServiceProtocol
from noveler.noveler.infrastructure.adapters.path_service_adapter import PathServiceProtocol

if TYPE_CHECKING:
    from pathlib import Path
    import shutil


class FilesystemBackupMigrationService(BackupMigrationService):
    """ファイルシステムバックアップ移行サービス

    B20準拠 Domain Service:
    - カオス状態のバックアップフォルダを統一構造に移行
    - 段階的移行プロセス
    - Functional Core + Imperative Shell
    """

    def __init__(
        self,
        *,
        path_service: PathServiceProtocol,
        console_service: ConsoleServiceProtocol,
        logger_service: LoggerServiceProtocol,
    ) -> None:
        """移行サービス初期化"""
        self._path_service = path_service
        self._console_service = console_service
        self._logger_service = logger_service

    def create_migration_plan(self, source_paths: list[Path], dry_run: bool = True) -> MigrationPlan:
        """移行プラン作成 - Functional Core（純粋関数的）"""
        if not source_paths:
            # デフォルト: プロジェクト全体から検出
            source_paths = [self._path_service.get_project_root()]

        phases = []

        # Phase 1: 調査・分析
        phases.append(
            MigrationPhase(
                phase_number=1,
                description="バックアップフォルダ調査・分析",
                operations=["既存バックアップフォルダ検出", "サイズ・日付分析", "重複判定"],
                estimated_duration_minutes=5,
            )
        )

        # Phase 2: 統一構造準備
        phases.append(
            MigrationPhase(
                phase_number=2,
                description="統一構造ディレクトリ準備",
                operations=["統一バックアップディレクトリ作成", "日付ベース構造構築"],
                estimated_duration_minutes=2,
            )
        )

        # Phase 3: 段階的移行
        phases.append(
            MigrationPhase(
                phase_number=3,
                description="レガシーバックアップ移行",
                operations=["古いフォルダ名前変更", "日付ベース再配置", "メタデータ付与"],
                estimated_duration_minutes=10,
            )
        )

        # Phase 4: 検証・クリーンアップ
        phases.append(
            MigrationPhase(
                phase_number=4,
                description="移行検証・クリーンアップ",
                operations=["移行結果検証", "重複フォルダ削除", "構造整合性チェック"],
                estimated_duration_minutes=3,
            )
        )

        return MigrationPlan(
            phases=phases, total_estimated_minutes=sum(p.estimated_duration_minutes for p in phases), dry_run=dry_run
        )

    def execute_phase(self, phase: MigrationPhase, dry_run: bool = True) -> PhaseResult:
        """フェーズ実行"""
        try:
            self._logger_service.info(f"Phase {phase.phase_number}実行開始: {phase.description}")

            if phase.phase_number == 1:
                return self._execute_analysis_phase(phase, dry_run)
            if phase.phase_number == 2:
                return self._execute_preparation_phase(phase, dry_run)
            if phase.phase_number == 3:
                return self._execute_migration_phase(phase, dry_run)
            if phase.phase_number == 4:
                return self._execute_verification_phase(phase, dry_run)
            return PhaseResult(success=False, operations=[], errors=[f"未対応フェーズ: {phase.phase_number}"])

        except Exception as e:
            self._logger_service.error(f"Phase {phase.phase_number}実行失敗: {e}")
            return PhaseResult(success=False, operations=[], errors=[str(e)])

    def execute_cleanup(self, dry_run: bool = True) -> CleanupResult:
        """クリーンアップ実行"""
        try:
            self._logger_service.info("バックアップクリーンアップ開始")

            operations = []
            errors = []
            cleaned_count = 0
            reclaimed_space_mb = 0.0

            # 古いバックアップフォルダ検出
            old_backups = self._find_old_backup_folders()

            for backup_path in old_backups:
                try:
                    # サイズ取得
                    size_mb = self._calculate_folder_size_mb(backup_path)

                    if dry_run:
                        operations.append(f"削除対象(DRY-RUN): {backup_path.name} ({size_mb:.1f}MB)")
                    else:
                        # 実際に削除
                        shutil.rmtree(backup_path)
                        operations.append(f"削除完了: {backup_path.name} ({size_mb:.1f}MB)")
                        cleaned_count += 1
                        reclaimed_space_mb += size_mb

                except Exception as e:
                    errors.append(f"削除失敗 {backup_path.name}: {e!s}")

            return CleanupResult(
                success=len(errors) == 0,
                operations=operations,
                errors=errors,
                cleaned_count=cleaned_count,
                reclaimed_space_mb=reclaimed_space_mb,
            )

        except Exception as e:
            self._logger_service.error(f"クリーンアップ失敗: {e}")
            return CleanupResult(success=False, operations=[], errors=[str(e)], cleaned_count=0, reclaimed_space_mb=0.0)

    def _execute_analysis_phase(self, phase: MigrationPhase, dry_run: bool) -> PhaseResult:
        """分析フェーズ実行"""
        operations = []
        errors = []

        try:
            project_root = self._path_service.get_project_root()

            # バックアップフォルダ検出
            backup_folders = self._discover_backup_folders(project_root)
            operations.append(f"バックアップフォルダ {len(backup_folders)}箇所検出")

            # サイズ分析
            total_size_mb = sum(self._calculate_folder_size_mb(folder) for folder in backup_folders)
            operations.append(f"総サイズ: {total_size_mb:.1f}MB")

            # 重複分析
            duplicates = self._find_duplicate_folders(backup_folders)
            if duplicates:
                operations.append(f"重複候補: {len(duplicates)}組検出")

        except Exception as e:
            errors.append(f"分析エラー: {e!s}")

        return PhaseResult(success=len(errors) == 0, operations=operations, errors=errors)

    def _execute_preparation_phase(self, phase: MigrationPhase, dry_run: bool) -> PhaseResult:
        """準備フェーズ実行"""
        operations = []
        errors = []

        try:
            # 統一バックアップディレクトリ作成
            backup_dir = self._path_service.get_backups_dir()

            if not dry_run:
                backup_dir.mkdir(parents=True, exist_ok=True)
                operations.append(f"統一バックアップディレクトリ作成: {backup_dir}")
            else:
                operations.append(f"統一バックアップディレクトリ作成予定: {backup_dir}")

            # サブディレクトリ構造準備
            subdirs = ["manual", "daily", "pre_operation", "system_recovery"]
            for subdir in subdirs:
                subdir_path = backup_dir / subdir
                if not dry_run:
                    subdir_path.mkdir(exist_ok=True)
                operations.append(f"サブディレクトリ: {subdir}")

        except Exception as e:
            errors.append(f"準備エラー: {e!s}")

        return PhaseResult(success=len(errors) == 0, operations=operations, errors=errors)

    def _execute_migration_phase(self, phase: MigrationPhase, dry_run: bool) -> PhaseResult:
        """移行フェーズ実行"""
        operations = []
        errors = []

        try:
            project_root = self._path_service.get_project_root()
            backup_folders = self._discover_backup_folders(project_root)

            for folder in backup_folders:
                try:
                    new_path = self._determine_new_path(folder)

                    if dry_run:
                        operations.append(f"移行予定: {folder.name} → {new_path.name}")
                    else:
                        # 実際の移行
                        folder.rename(new_path)
                        operations.append(f"移行完了: {folder.name} → {new_path.name}")

                except Exception as e:
                    errors.append(f"移行失敗 {folder.name}: {e!s}")

        except Exception as e:
            errors.append(f"移行フェーズエラー: {e!s}")

        return PhaseResult(success=len(errors) == 0, operations=operations, errors=errors)

    def _execute_verification_phase(self, phase: MigrationPhase, dry_run: bool) -> PhaseResult:
        """検証フェーズ実行"""
        operations = []
        errors = []

        try:
            backup_dir = self._path_service.get_backups_dir()

            if backup_dir.exists():
                # 移行後フォルダ確認
                migrated_folders = list(backup_dir.rglob("*"))
                folder_count = len([f for f in migrated_folders if f.is_dir()])
                operations.append(f"移行後フォルダ数: {folder_count}")

                # 構造整合性チェック
                expected_subdirs = ["manual", "daily", "pre_operation", "system_recovery"]
                for subdir in expected_subdirs:
                    subdir_path = backup_dir / subdir
                    if subdir_path.exists():
                        operations.append(f"構造確認OK: {subdir}")
                    else:
                        errors.append(f"構造不整合: {subdir}が存在しません")
            else:
                errors.append("バックアップディレクトリが存在しません")

        except Exception as e:
            errors.append(f"検証エラー: {e!s}")

        return PhaseResult(success=len(errors) == 0, operations=operations, errors=errors)

    def _discover_backup_folders(self, project_root: Path) -> list[Path]:
        """バックアップフォルダ検出"""
        backup_folders = []

        patterns = ["*backup*", "tests_backup*"]

        for pattern in patterns:
            for folder in project_root.rglob(pattern):
                if folder.is_dir() and self._is_legacy_backup_folder(folder):
                    backup_folders.append(folder)

        return backup_folders

    def _is_legacy_backup_folder(self, folder: Path) -> bool:
        """レガシーバックアップフォルダ判定"""
        name = folder.name.lower()

        # 統一構造に含まれていないもの
        if folder.parent.name == "backups":
            return False  # 既に移行済み

        # レガシー判定
        legacy_patterns = ["backup", "tests_backup", "old", "archive"]
        return any(pattern in name for pattern in legacy_patterns)

    def _determine_new_path(self, old_folder: Path) -> Path:
        """新しいパス決定"""
        backup_dir = self._path_service.get_backups_dir()

        # フォルダタイプ判定
        if "tests_backup" in old_folder.name.lower():
            category = "daily"
        elif "backup_" in old_folder.name:
            category = "manual"
        else:
            category = "manual"

        # タイムスタンプ付き名前生成

        timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
        new_name = f"legacy_{old_folder.name}_{timestamp}"

        return backup_dir / category / new_name

    def _find_old_backup_folders(self) -> list[Path]:
        """古いバックアップフォルダ検出"""
        from datetime import datetime, timedelta

        from noveler.domain.value_objects.project_time import project_now

        cutoff_date = project_now().datetime - timedelta(days=30)
        old_folders = []

        project_root = self._path_service.get_project_root()

        for folder in self._discover_backup_folders(project_root):
            try:
                folder_time = datetime.fromtimestamp(folder.stat().st_ctime)
                if folder_time < cutoff_date:
                    old_folders.append(folder)
            except Exception:
                continue

        return old_folders

    def _find_duplicate_folders(self, folders: list[Path]) -> list[tuple]:
        """重複フォルダ検出"""
        duplicates = []

        # サイズベース重複検出
        size_map = {}
        for folder in folders:
            size = self._calculate_folder_size_mb(folder)
            if size not in size_map:
                size_map[size] = []
            size_map[size].append(folder)

        for size, folder_list in size_map.items():
            if len(folder_list) > 1 and size > 0:
                duplicates.append(tuple(folder_list))

        return duplicates

    def _calculate_folder_size_mb(self, folder: Path) -> float:
        """フォルダサイズ計算"""
        try:
            total_size = sum(f.stat().st_size for f in folder.rglob("*") if f.is_file())
            return total_size / (1024 * 1024)
        except Exception:
            return 0.0
