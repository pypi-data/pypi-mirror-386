"""Domain.services.backup_migration_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""バックアップ移行サービス

B20準拠実装 - Domain Service Interface
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class MigrationPhase:
    """移行フェーズ"""

    phase_number: int
    description: str
    operations: list[str]
    estimated_duration_minutes: int


@dataclass
class MigrationPlan:
    """移行プラン"""

    phases: list[MigrationPhase]
    total_estimated_minutes: int
    dry_run: bool


@dataclass
class PhaseResult:
    """フェーズ実行結果"""

    success: bool
    operations: list[str]
    errors: list[str]


@dataclass
class CleanupResult:
    """クリーンアップ実行結果"""

    success: bool
    operations: list[str]
    errors: list[str]
    cleaned_count: int
    reclaimed_space_mb: float


class BackupMigrationService(ABC):
    """バックアップ移行サービス - Domain Service Interface

    B20準拠 Domain Service:
    - 移行ビジネスロジックの抽象化
    - 段階的移行プロセス管理
    - Pure Domain Logic
    """

    @abstractmethod
    def create_migration_plan(self, source_paths: list[Path], dry_run: bool = True) -> MigrationPlan:
        """移行プラン作成"""

    @abstractmethod
    def execute_phase(self, phase: MigrationPhase, dry_run: bool = True) -> PhaseResult:
        """フェーズ実行"""

    @abstractmethod
    def execute_cleanup(self, dry_run: bool = True) -> CleanupResult:
        """クリーンアップ実行"""
