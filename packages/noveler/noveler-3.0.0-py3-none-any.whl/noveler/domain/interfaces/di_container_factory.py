#!/usr/bin/env python3
"""DIコンテナファクトリーインターフェース

Domain層でのDI抽象化 - Infrastructure依存除去
Phase 4: 契約違反緊急修正 - Domain純粋性完全確保
"""

from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar("T")


class IDIContainerFactory(ABC):
    """DIコンテナファクトリーインターフェース

    Domain層がDIコンテナに依存せずに依存性注入を実現
    Infrastructure層で具象実装を提供
    """

    @abstractmethod
    def resolve(self, interface_type: type[T]) -> T:
        """インターフェース型から実装を解決

        Args:
            interface_type: 解決したいインターフェース型

        Returns:
            interface_typeの実装インスタンス

        Raises:
            DIResolutionError: 解決できない場合
        """

    @abstractmethod
    def is_registered(self, interface_type: type) -> bool:
        """指定したインターフェースが登録されているか確認

        Args:
            interface_type: 確認したいインターフェース型

        Returns:
            bool: 登録されている場合True
        """


class DIResolutionError(Exception):
    """DI解決エラー

    指定されたインターフェース型の実装が見つからない、
    または解決に失敗した場合に発生する例外
    """

    def __init__(self, interface_type: type, details: str = "") -> None:
        self.interface_type = interface_type
        self.details = details
        super().__init__(f"Cannot resolve {interface_type.__name__}: {details}")


class NullDIContainerFactory(IDIContainerFactory):
    """NullオブジェクトパターンDIファクトリー

    テスト時やDIコンテナが利用できない場合のフォールバック実装
    """

    def resolve(self, interface_type: type[T]) -> T:
        """常にDIResolutionErrorを発生"""
        raise DIResolutionError(interface_type, "No DI container available - using NullDIContainerFactory")

    def is_registered(self, interface_type: type) -> bool:
        """常にFalseを返す"""
        return False
