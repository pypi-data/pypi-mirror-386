"""Infrastructure.di.container
Where: Infrastructure module defining the main dependency injection container.
What: Creates and configures service bindings used across the application.
Why: Ensures dependencies are resolved consistently from a single container implementation.
"""

from __future__ import annotations

from pathlib import Path

from noveler.presentation.shared.shared_utilities import console

"依存性注入コンテナ\n\nDDD準拠: インフラストラクチャ層の依存性注入実装\nサービスの登録と解決を管理する\n"

from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable
T = TypeVar("T")


class DIContainer:
    """依存性注入コンテナ

    シングルトンパターンで実装し、アプリケーション全体で
    一つのコンテナインスタンスを共有する。
    """

    _instance: ClassVar[DIContainer | None] = None
    _services: ClassVar[dict[type | str, Any]] = {}
    _factories: ClassVar[dict[type | str, Callable[[], Any]]] = {}

    def __new__(cls) -> DIContainer:
        """シングルトンインスタンスを取得"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """コンテナを初期化"""
        self._services = {}
        self._factories = {}
        self._configs: dict[str, Any] = {}

    def register(
        self, interface: type[T], implementation: T | None = None, factory: Callable[[], T] | None = None
    ) -> None:
        """サービスを登録

        Args:
            interface: インターフェース型
            implementation: 実装インスタンス
            factory: ファクトリー関数
        """
        if implementation is not None:
            self._services[interface] = implementation
        elif factory is not None:
            self._factories[interface] = factory
        else:
            msg = "実装またはファクトリーのいずれかを指定してください"
            raise ValueError(msg)

    def resolve(self, interface: type[T]) -> T:
        """サービスを解決

        Args:
            interface: インターフェース型

        Returns:
            サービスインスタンス

        Raises:
            ValueError: サービスが登録されていない場合
        """
        if interface in self._services:
            return self._services[interface]
        if interface in self._factories:
            service = self._factories[interface]()
            self._services[interface] = service
            return service
        msg = f"サービスが登録されていません: {interface.__name__}"
        raise ValueError(msg)

    def has(self, interface: type) -> bool:
        """サービスが登録されているか確認

        Args:
            interface: インターフェース型

        Returns:
            登録されている場合True
        """
        return interface in self._services or interface in self._factories

    # ------------------------------------------------------------------
    # 追加ユーティリティ (文字列キー向け・設定向け)
    # ------------------------------------------------------------------

    def register_factory(self, key: str, factory: Callable[[], Any]) -> None:
        """文字列キーでファクトリーを登録"""

        self._factories[key] = factory

    def register_singleton(self, key: str, instance: Any) -> None:
        """文字列キーでシングルトンインスタンスを登録"""

        self._services[key] = instance

    def has_factory(self, key: str) -> bool:
        """ファクトリー登録の有無を確認"""

        return key in self._factories

    def register_config(self, key: str, value: Any) -> None:
        """設定値を登録"""

        self._configs[key] = value

    def has_config(self, key: str) -> bool:
        """設定値の登録有無を確認"""

        return key in self._configs

    def get_config(self, key: str, default: Any | None = None) -> Any:
        """設定値を取得"""

        return self._configs.get(key, default)

    def clear(self) -> None:
        """コンテナをクリア"""
        self._services.clear()
        self._factories.clear()
        self._configs.clear()


_container = DIContainer()


def get_container() -> DIContainer:
    """DIコンテナを取得

    Returns:
        DIコンテナインスタンス
    """
    return _container


def register_service(
    interface: type[T], implementation: T | None = None, factory: Callable[[], T] | None = None
) -> None:
    """サービスを登録（ヘルパー関数）

    Args:
        interface: インターフェース型
        implementation: 実装インスタンス
        factory: ファクトリー関数
    """
    _container.register(interface, implementation, factory)


def resolve_service(interface: type[T] | str) -> T:
    """サービスを解決（ヘルパー関数）

    Args:
        interface: インターフェース型または文字列キー

    Returns:
        サービスインスタンス
    """
    if isinstance(interface, str):
        key = interface
        if key in _container._services:
            return _container._services[key]
        if key in _container._factories:
            service = _container._factories[key]()
            _container._services[key] = service
            return service
        msg = f"サービスが登録されていません: {key}"
        raise ValueError(msg)
    return _container.resolve(interface)


def auto_setup_container() -> None:
    """DIコンテナの自動セットアップ

    基本的なサービスをDIコンテナに登録する。
    アプリケーション起動時に一度だけ呼び出される。
    """
    try:

        def create_logger_service():
            from noveler.infrastructure.adapters.domain_logger_adapter import DomainLoggerAdapter
            return DomainLoggerAdapter()

        def create_path_service():
            from noveler.infrastructure.adapters.path_service_adapter import PathServiceAdapter
            return PathServiceAdapter(Path.cwd())

        def create_console_service():
            from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter
            return ConsoleServiceAdapter()

        def create_configuration_service():
            from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager
            return get_configuration_manager()

        def create_repository_factory():
            from noveler.infrastructure.di.unified_repository_factory import UnifiedRepositoryFactory
            return UnifiedRepositoryFactory()

        _container._factories["ILogger"] = create_logger_service
        _container._factories["IPathService"] = create_path_service
        _container._factories["IConsoleService"] = create_console_service
        _container._factories["IConfigurationService"] = create_configuration_service
        _container._factories["IRepositoryFactory"] = create_repository_factory
    except ImportError as e:
        console.print(f"⚠️ DIコンテナセットアップ警告: {e}")
