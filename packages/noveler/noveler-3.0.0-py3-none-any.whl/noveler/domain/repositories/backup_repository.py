"""Domain.repositories.backup_repository
Where: Domain repository interface for backup data access.
What: Declares operations required to store and retrieve backup information.
Why: Allows infrastructure implementations to plug into backup workflows.
"""

from __future__ import annotations

"""バックアップリポジトリ

B20準拠実装 - Repository Interface
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from noveler.noveler.domain.value_objects.backup_strategy import BackupStrategy
from noveler.noveler.domain.value_objects.backup_type import BackupType

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class BackupResult:
    """バックアップ実行結果"""

    success: bool
    backup_path: Path | None
    size_mb: float
    errors: list[str]


class BackupRepository(ABC):
    """バックアップリポジトリ - Repository Interface

    B20準拠 Repository Pattern:
    - データ永続化の抽象化
    - ドメインモデルとインフラの分離
    - Pure Domain Interface
    """

    @abstractmethod
    def create_backup(
        self, *, backup_type: BackupType, strategy: BackupStrategy, dry_run: bool = False
    ) -> BackupResult:
        """バックアップ作成"""

    @abstractmethod
    def list_backups(self, backup_type: BackupType | None = None) -> list[Path]:
        """バックアップ一覧取得"""

    @abstractmethod
    def delete_backup(self, backup_path: Path, dry_run: bool = False) -> bool:
        """バックアップ削除"""
