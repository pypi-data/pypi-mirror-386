"""Infrastructure.unit_of_work.backup_unit_of_work
Where: Infrastructure unit-of-work managing backup transactions.
What: Coordinates repositories and services involved in backup workflows.
Why: Ensures backup operations run with consistent transactional boundaries.
"""

from __future__ import annotations

"""バックアップUnit of Work

B20準拠実装 - Unit of Work Interface
"""

from abc import ABC, abstractmethod


class BackupUnitOfWork(ABC):
    """バックアップUnit of Work - Interface

    B20準拠 Unit of Work Pattern:
    - トランザクション境界管理
    - 作業単位の統一管理
    - リソース管理の抽象化
    """

    @abstractmethod
    def __enter__(self):
        """トランザクション開始"""

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """リソースクリーンアップ"""

    @abstractmethod
    def add_operation(self, operation_type: str, **kwargs) -> None:
        """操作追加"""

    @abstractmethod
    def commit(self) -> None:
        """コミット - 全操作の永続化"""

    @abstractmethod
    def rollback(self) -> None:
        """ロールバック - 全操作の取り消し"""
