"""統合サービスロケーター実装

Protocol分離とLazy Proxyを組み合わせた高性能なサービス管理。
循環依存を完全に回避しつつ、透過的なサービス提供を実現。
"""

from typing import TYPE_CHECKING, Any, TypeVar, cast

from noveler.domain.interfaces.service_locator_protocol import IServiceLocator
from noveler.infrastructure.factories.base_service_factory import get_service_factory
from noveler.infrastructure.patterns.lazy_proxy import LazyProxy

if TYPE_CHECKING:
    from noveler.domain.protocols import (
        IConfigurationServiceProtocol,
        IConsoleServiceProtocol,
        ILoggerProtocol,
        IPathServiceProtocol,
        IRepositoryFactoryProtocol,
        IUnitOfWorkProtocol,
    )

T = TypeVar("T")


class ServiceLocator(IServiceLocator):
    """統合サービスロケーター

    Protocol分離により循環依存を回避し、Lazy Proxyで遅延初期化を実現。
    AbstractUseCaseの関数レベルインポートを完全に置き換える。
    """

    def __init__(self) -> None:
        """初期化"""
        self._factory = get_service_factory()
        self._cache: dict[type, Any] = {}

    def get_logger_service(self) -> "ILoggerProtocol":
        """ロガーサービス取得（Lazy Proxy）

        Returns:
            ロガーサービスのLazy Proxy
        """
        service_type = "ILoggerProtocol"
        if service_type not in self._cache:
            self._cache[service_type] = LazyProxy(self._factory.create_logger_service)
        return cast("ILoggerProtocol", self._cache[service_type])

    def get_unit_of_work(self) -> "IUnitOfWorkProtocol":
        """Unit of Work取得（Lazy Proxy）

        Returns:
            Unit of WorkのLazy Proxy
        """
        service_type = "IUnitOfWorkProtocol"
        if service_type not in self._cache:
            self._cache[service_type] = LazyProxy(self._factory.create_unit_of_work)
        return cast("IUnitOfWorkProtocol", self._cache[service_type])

    def get_console_service(self) -> "IConsoleServiceProtocol":
        """コンソールサービス取得（Lazy Proxy）

        Returns:
            コンソールサービスのLazy Proxy
        """
        service_type = "IConsoleServiceProtocol"
        if service_type not in self._cache:
            self._cache[service_type] = LazyProxy(self._factory.create_console_service)
        return cast("IConsoleServiceProtocol", self._cache[service_type])

    def get_path_service(self, project_root: str | None = None) -> "IPathServiceProtocol":
        """パスサービス取得（Lazy Proxy）

        Args:
            project_root: プロジェクトルートパス

        Returns:
            パスサービスのLazy Proxy
        """
        # プロジェクトルート指定がある場合は新しいインスタンスを作成
        if project_root is not None:
            return LazyProxy(lambda: self._factory.create_path_service(project_root))

        service_type = "IPathServiceProtocol"
        if service_type not in self._cache:
            self._cache[service_type] = LazyProxy(self._factory.create_path_service)
        return cast("IPathServiceProtocol", self._cache[service_type])

    def get_configuration_service(self) -> "IConfigurationServiceProtocol":
        """設定サービス取得（Lazy Proxy）

        Returns:
            設定サービスのLazy Proxy
        """
        service_type = "IConfigurationServiceProtocol"
        if service_type not in self._cache:
            self._cache[service_type] = LazyProxy(self._factory.create_configuration_service)
        return cast("IConfigurationServiceProtocol", self._cache[service_type])

    def get_repository_factory(self) -> "IRepositoryFactoryProtocol":
        """リポジトリファクトリー取得（Lazy Proxy）

        Returns:
            リポジトリファクトリーのLazy Proxy
        """
        service_type = "IRepositoryFactoryProtocol"
        if service_type not in self._cache:
            self._cache[service_type] = LazyProxy(self._factory.create_repository_factory)
        return cast("IRepositoryFactoryProtocol", self._cache[service_type])

    def clear_cache(self) -> None:
        """キャッシュクリア（テスト用）"""
        self._cache.clear()

    def is_cached(self, service_type: str) -> bool:
        """サービスがキャッシュされているか確認

        Args:
            service_type: サービス型名

        Returns:
            キャッシュされている場合True
        """
        return service_type in self._cache

    def is_initialized(self, service_type: str) -> bool:
        """サービスが初期化されているか確認

        Args:
            service_type: サービス型名

        Returns:
            初期化済みの場合True
        """
        if service_type not in self._cache:
            return False
        proxy = self._cache[service_type]
        if isinstance(proxy, LazyProxy):
            return proxy.is_initialized
        return True


class ServiceLocatorManager:
    """サービスロケーター管理クラス

    グローバルなServiceLocatorインスタンスを管理。
    """

    _instance: "ServiceLocatorManager | None" = None
    _locator: ServiceLocator | None = None

    def __new__(cls) -> "ServiceLocatorManager":
        """シングルトンインスタンス取得"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def locator(self) -> ServiceLocator:
        """サービスロケーター取得

        Returns:
            ServiceLocatorインスタンス
        """
        if self._locator is None:
            self._locator = ServiceLocator()
        return self._locator

    def set_locator(self, locator: ServiceLocator) -> None:
        """サービスロケーター設定（テスト用）

        Args:
            locator: 設定するサービスロケーター
        """
        self._locator = locator

    def reset(self) -> None:
        """サービスロケーターリセット（テスト用）"""
        self._locator = None


# グローバルアクセス用関数
def get_service_locator() -> ServiceLocator:
    """サービスロケーター取得

    Returns:
        ServiceLocatorインスタンス
    """
    manager = ServiceLocatorManager()
    return manager.locator
