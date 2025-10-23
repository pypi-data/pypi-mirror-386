#!/usr/bin/env python3
"""リポジトリ基底プロトコル

DDD準拠: Domain層の基底リポジトリインターフェース
全リポジトリが実装すべき共通契約を定義

SPEC-DDD-COMPLIANCE-003: リポジトリ抽象化統一
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, Protocol, TypeVar

# リポジトリで扱うエンティティの型パラメータ
TEntity = TypeVar("TEntity")
TId = TypeVar("TId")


class IRepository(Protocol, Generic[TEntity, TId]):
    """リポジトリ基底インターフェース

    全てのリポジトリが実装すべき共通契約。
    DDD原則に従い、ドメインオブジェクトの永続化を抽象化。
    """

    @abstractmethod
    async def save(self, entity: TEntity) -> None:
        """エンティティ保存

        Args:
            entity: 保存対象エンティティ

        Raises:
            RepositoryError: 保存失敗時
        """
        ...

    @abstractmethod
    async def find_by_id(self, entity_id: TId) -> TEntity | None:
        """ID による単一エンティティ検索

        Args:
            entity_id: 検索対象ID

        Returns:
            TEntity | None: エンティティ（存在しない場合はNone）
        """
        ...

    @abstractmethod
    async def find_all(self) -> list[TEntity]:
        """全エンティティ取得

        Returns:
            list[TEntity]: 全エンティティリスト
        """
        ...

    @abstractmethod
    async def delete(self, entity_id: TId) -> bool:
        """エンティティ削除

        Args:
            entity_id: 削除対象ID

        Returns:
            bool: 削除成功/失敗
        """
        ...

    @abstractmethod
    async def exists(self, entity_id: TId) -> bool:
        """エンティティ存在確認

        Args:
            entity_id: 確認対象ID

        Returns:
            bool: 存在/非存在
        """
        ...


class IRepositoryFactory(ABC):
    """リポジトリファクトリー基底インターフェース

    DDD準拠のリポジトリインスタンス生成抽象化。
    Application層からの依存注入契約を定義。
    """

    @abstractmethod
    def create_repository(self, repository_type: type[TEntity]) -> IRepository[TEntity, Any]:
        """指定型のリポジトリ生成

        Args:
            repository_type: リポジトリが扱うエンティティ型

        Returns:
            IRepository: リポジトリ実装
        """


class RepositoryError(Exception):
    """リポジトリ操作エラー基底クラス"""

    def __init__(self, message: str, entity_type: type[Any] | None = None, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.entity_type = entity_type
        self.context = context or {}


class EntityNotFoundError(RepositoryError):
    """エンティティ未発見エラー"""


class PersistenceError(RepositoryError):
    """永続化エラー"""
