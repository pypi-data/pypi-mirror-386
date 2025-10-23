"""Infrastructure.container.backup_container
Where: Infrastructure module configuring backup-related dependency injection.
What: Registers repositories, services, and unit-of-work bindings for backup workflows.
Why: Provides a central container setup so backup features reuse consistent wiring.
"""

from __future__ import annotations

"""バックアップDIコンテナ

B20準拠実装 - Dependency Injection Container
"""

from noveler.noveler.application.use_cases.unified_backup_management_use_case import (
    UnifiedBackupManagementUseCase,
)
from noveler.noveler.domain.repositories.backup_repository import BackupRepository
from noveler.noveler.domain.services.backup_analysis_service import BackupAnalysisService
from noveler.noveler.domain.services.backup_migration_service import BackupMigrationService
from noveler.noveler.domain.services.backup_strategy_factory import BackupStrategyFactory
from noveler.noveler.infrastructure.adapters.console_service_adapter import get_console_service
from noveler.noveler.infrastructure.adapters.logger_service_adapter import get_logger_service
from noveler.noveler.infrastructure.adapters.path_service_adapter import get_path_service
from noveler.noveler.infrastructure.repositories.filesystem_backup_repository import (
    FilesystemBackupRepository,
)
from noveler.noveler.infrastructure.services.filesystem_backup_analysis_service import (
    FilesystemBackupAnalysisService,
)
from noveler.noveler.infrastructure.services.filesystem_backup_migration_service import (
    FilesystemBackupMigrationService,
)
from noveler.noveler.infrastructure.unit_of_work.backup_unit_of_work import BackupUnitOfWork
from noveler.noveler.infrastructure.unit_of_work.filesystem_backup_unit_of_work import (
    FilesystemBackupUnitOfWork,
)


class BackupContainer:
    """バックアップDIコンテナ

    B20準拠 Dependency Injection Container:
    - Factory Pattern
    - Singleton Pattern（必要時）
    - 依存関係の集約管理
    """

    def __init__(self) -> None:
        """コンテナ初期化 - Lazy initialization"""
        self._backup_uow: BackupUnitOfWork | None = None
        self._backup_repository: BackupRepository | None = None
        self._analysis_service: BackupAnalysisService | None = None
        self._migration_service: BackupMigrationService | None = None
        self._strategy_factory: BackupStrategyFactory | None = None

    def get_backup_management_use_case(self) -> UnifiedBackupManagementUseCase:
        """統一バックアップ管理ユースケース取得 - Factory Method"""
        return UnifiedBackupManagementUseCase(
            backup_uow=self.get_backup_unit_of_work(),
            backup_repository=self.get_backup_repository(),
            analysis_service=self.get_backup_analysis_service(),
            migration_service=self.get_backup_migration_service(),
            console_service=get_console_service(),
            logger_service=get_logger_service(),
            path_service=get_path_service(),
        )

    def get_backup_unit_of_work(self) -> BackupUnitOfWork:
        """バックアップUnit of Work取得 - Singleton Pattern"""
        if self._backup_uow is None:
            self._backup_uow = FilesystemBackupUnitOfWork(path_service=get_path_service())
        return self._backup_uow

    def get_backup_repository(self) -> BackupRepository:
        """バックアップリポジトリ取得 - Singleton Pattern"""
        if self._backup_repository is None:
            self._backup_repository = FilesystemBackupRepository(
                path_service=get_path_service(), logger_service=get_logger_service()
            )
        return self._backup_repository

    def get_backup_analysis_service(self) -> BackupAnalysisService:
        """バックアップ分析サービス取得 - Singleton Pattern"""
        if self._analysis_service is None:
            self._analysis_service = FilesystemBackupAnalysisService(
                path_service=get_path_service(), logger_service=get_logger_service()
            )
        return self._analysis_service

    def get_backup_migration_service(self) -> BackupMigrationService:
        """バックアップ移行サービス取得 - Singleton Pattern"""
        if self._migration_service is None:
            self._migration_service = FilesystemBackupMigrationService(
                path_service=get_path_service(),
                console_service=get_console_service(),
                logger_service=get_logger_service(),
            )
        return self._migration_service

    def get_backup_strategy_factory(self) -> BackupStrategyFactory:
        """バックアップ戦略ファクトリ取得 - Singleton Pattern"""
        if self._strategy_factory is None:
            self._strategy_factory = BackupStrategyFactory(path_service=get_path_service())
        return self._strategy_factory
