#!/usr/bin/env python3
"""Domain用DIコンテナファクトリー実装

Infrastructure層でDomain抽象化を実装
Phase 4: Domain純粋性完全確保
"""

from typing import TypeVar

from noveler.domain.interfaces.di_container_factory import DIResolutionError, IDIContainerFactory
from noveler.infrastructure.di.simple_di_container import get_container

T = TypeVar("T")


class DomainDIContainerFactory(IDIContainerFactory):
    """Domain層用DIコンテナファクトリー実装

    simple_di_containerのDomain抽象化ラッパー
    Domain層からのInfrastructure直接依存を除去
    """

    def __init__(self) -> None:
        """初期化"""
        self._container = get_container()

    def resolve(self, interface_type: type[T]) -> T:
        """インターフェース型から実装を解決

        Args:
            interface_type: 解決したいインターフェース型

        Returns:
            interface_typeの実装インスタンス

        Raises:
            DIResolutionError: 解決できない場合
        """
        try:
            return self._container.get(interface_type)
        except (ValueError, KeyError) as e:
            raise DIResolutionError(interface_type, f"DI container resolution failed: {e}") from e

    def is_registered(self, interface_type: type) -> bool:
        """指定したインターフェースが登録されているか確認

        Args:
            interface_type: 確認したいインターフェース型

        Returns:
            bool: 登録されている場合True
        """
        try:
            self._container.get(interface_type)
            return True
        except (ValueError, KeyError):
            return False


# グローバルインスタンス（Domain層からアクセス可能）
_domain_di_factory: IDIContainerFactory | None = None


def get_domain_di_factory() -> IDIContainerFactory:
    """Domain用DIファクトリーの取得

    Domain層のエンティティ・サービスからアクセス可能な
    Infrastructure非依存のDI抽象化層

    Returns:
        IDIContainerFactory: Domain用DIファクトリー
    """
    global _domain_di_factory

    if _domain_di_factory is None:
        try:
            _domain_di_factory = DomainDIContainerFactory()
        except ImportError:
            # Infrastructure層が利用できない場合のフォールバック
            from noveler.domain.interfaces.di_container_factory import NullDIContainerFactory

            _domain_di_factory = NullDIContainerFactory()

    return _domain_di_factory


def set_domain_di_factory(factory: IDIContainerFactory) -> None:
    """Domain用DIファクトリーの設定

    テスト時やカスタム実装を使用する場合に使用

    Args:
        factory: 設定するDIファクトリー
    """
    global _domain_di_factory
    _domain_di_factory = factory
