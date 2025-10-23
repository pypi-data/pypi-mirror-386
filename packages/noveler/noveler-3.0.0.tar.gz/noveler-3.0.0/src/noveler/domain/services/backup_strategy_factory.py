"""Domain.services.backup_strategy_factory
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""バックアップ戦略ファクトリ

B20準拠実装 - Factory Pattern
"""

from noveler.noveler.domain.value_objects.backup_strategy import BackupStrategy
from noveler.noveler.domain.value_objects.backup_type import BackupType
from noveler.noveler.infrastructure.adapters.path_service_adapter import PathServiceProtocol


class BackupStrategyFactory:
    """バックアップ戦略ファクトリ

    B20準拠 Factory Pattern:
    - 戦略オブジェクト生成
    - タイプ別戦略の統一インターフェース
    - Functional Core（純粋関数的）
    """

    def __init__(self, *, path_service: PathServiceProtocol) -> None:
        """ファクトリ初期化"""
        self._path_service = path_service

    def create_strategy(self, *, backup_type: BackupType, purpose: str | None = None) -> BackupStrategy:
        """戦略作成 - Factory Method Pattern

        Args:
            backup_type: バックアップタイプ
            purpose: バックアップ目的・説明

        Returns:
            BackupStrategy: 戦略オブジェクト
        """
        if backup_type == BackupType.MANUAL:
            return self._create_manual_strategy(purpose)
        if backup_type == BackupType.DAILY:
            return self._create_daily_strategy()
        if backup_type == BackupType.PRE_OPERATION:
            return self._create_pre_operation_strategy(purpose)
        if backup_type == BackupType.SYSTEM_RECOVERY:
            return self._create_system_recovery_strategy()
        msg = f"未対応バックアップタイプ: {backup_type}"
        raise ValueError(msg)

    def _create_manual_strategy(self, purpose: str | None) -> BackupStrategy:
        """手動バックアップ戦略作成"""
        return BackupStrategy(
            backup_type=BackupType.MANUAL,
            target_paths=[
                self._path_service.get_project_root(),
            ],
            exclude_patterns=["__pycache__", "*.pyc", ".git", "node_modules", ".pytest_cache"],
            compression_enabled=True,
            purpose=purpose or "手動バックアップ",
            retention_days=30,
        )

    def _create_daily_strategy(self) -> BackupStrategy:
        """日次バックアップ戦略作成"""
        return BackupStrategy(
            backup_type=BackupType.DAILY,
            target_paths=[
                self._path_service.get_manuscripts_dir(),
                self._path_service.get_project_config_dir(),
            ],
            exclude_patterns=["__pycache__", "*.pyc", ".pytest_cache"],
            compression_enabled=True,
            purpose="日次自動バックアップ",
            retention_days=7,
        )

    def _create_pre_operation_strategy(self, purpose: str | None) -> BackupStrategy:
        """操作前バックアップ戦略作成"""
        return BackupStrategy(
            backup_type=BackupType.PRE_OPERATION,
            target_paths=[
                self._path_service.get_project_root(),
            ],
            exclude_patterns=[
                "__pycache__",
                "*.pyc",
                ".git",
                "node_modules",
                ".pytest_cache",
                "backups",  # 既存バックアップは除外
            ],
            compression_enabled=True,
            purpose=purpose or "操作前安全バックアップ",
            retention_days=14,
        )

    def _create_system_recovery_strategy(self) -> BackupStrategy:
        """システム復旧バックアップ戦略作成"""
        return BackupStrategy(
            backup_type=BackupType.SYSTEM_RECOVERY,
            target_paths=[
                self._path_service.get_project_root(),
            ],
            exclude_patterns=["__pycache__", "*.pyc", ".pytest_cache"],
            compression_enabled=True,
            purpose="システム復旧用完全バックアップ",
            retention_days=60,
        )
