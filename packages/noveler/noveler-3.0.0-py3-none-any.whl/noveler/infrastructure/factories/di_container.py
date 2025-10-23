#!/usr/bin/env python3
"""依存性注入コンテナ

DDD準拠: Infrastructure層のDIコンテナ実装
Clean Architectureの依存性管理を実現

SPEC-DDD-COMPLIANCE-004: DIコンテナ統一実装
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass
class ServiceRegistration:
    """サービス登録情報"""
    factory: Callable[..., Any]
    is_singleton: bool = True
    instance: Any = None


class DIContainer:
    """依存性注入コンテナ

    DDD準拠のサービスライフサイクル管理を提供。
    シングルトン、ファクトリー、スコープ管理に対応。
    """

    def __init__(self) -> None:
        self._services: dict[type[Any], ServiceRegistration] = {}
        self._singletons: dict[type[Any], Any] = {}
        # B30準拠: Console() → self.get_console_service()使用
        self._initialized = False

    def register_singleton(self, interface_type: type[T], factory: Callable[..., T]) -> None:
        """シングルトンサービス登録

        Args:
            interface_type: サービスインターフェース型
            factory: インスタンス生成ファクトリー
        """
        self._services[interface_type] = ServiceRegistration(
            factory=factory,
            is_singleton=True
        )

    def register_transient(self, interface_type: type[T], factory: Callable[..., T]) -> None:
        """トランジェントサービス登録

        Args:
            interface_type: サービスインターフェース型
            factory: インスタンス生成ファクトリー（呼び出し毎に新規作成）
        """
        self._services[interface_type] = ServiceRegistration(
            factory=factory,
            is_singleton=False
        )

    def resolve(self, service_type: type[T]) -> T:
        """サービス解決

        Args:
            service_type: 解決したいサービス型

        Returns:
            T: サービスインスタンス

        Raises:
            DIContainerError: サービス未登録時
        """
        if service_type not in self._services:
            msg = f"サービス未登録: {service_type.__name__}"
            raise DIContainerError(msg)

        registration = self._services[service_type]

        if registration.is_singleton:
            if service_type not in self._singletons:
                self._singletons[service_type] = registration.factory()
            return self._singletons[service_type]
        return registration.factory()

    def resolve_all(self, service_type: type[T]) -> list[T]:
        """指定型の全サービス解決

        Args:
            service_type: 解決したいサービス型

        Returns:
            list[T]: 該当サービス全インスタンス
        """
        services = []
        for registered_type, registration in self._services.items():
            if issubclass(registered_type, service_type):
                if registration.is_singleton:
                    if registered_type not in self._singletons:
                        self._singletons[registered_type] = registration.factory()
                    services.append(self._singletons[registered_type])
                else:
                    services.append(registration.factory())
        return services

    def initialize_core_services(self, project_root: Path | None = None) -> None:
        """コアサービス初期化

        Args:
            project_root: プロジェクトルートパス（自動検出可能）
        """
        if self._initialized:
            return

        try:
            # パスサービス登録
            from noveler.domain.interfaces.path_service_protocol import IPathService
            from noveler.infrastructure.services.path_helper_service import PathHelperService

            self.register_singleton(
                IPathService,
                lambda: PathHelperService(project_root)
            )

            # イベントパブリッシャー登録
            from noveler.domain.interfaces.event_publisher_protocol import IDomainEventPublisher
            from noveler.infrastructure.adapters.console_event_publisher import ConsoleEventPublisher

            self.register_singleton(
                IDomainEventPublisher,
                lambda: ConsoleEventPublisher(self._console)
            )

            # リポジトリファクトリー登録
            from noveler.domain.interfaces.repository_factory import IRepositoryFactory
            from noveler.infrastructure.factories.concrete_repository_factory import ConcreteRepositoryFactory

            path_service = self.resolve(IPathService)
            self.register_singleton(
                IRepositoryFactory,
                lambda: ConcreteRepositoryFactory(path_service)
            )

            self._console.info("🔧 DIコンテナ - コアサービス初期化完了")
            self._initialized = True

        except ImportError as e:
            self._console.error(f"❌ DIコンテナ - サービス初期化エラー: {e}")
            msg = f"コアサービス初期化失敗: {e}"
            raise DIContainerError(msg)

    def clear(self) -> None:
        """コンテナクリア"""
        self._services.clear()
        self._singletons.clear()
        self._initialized = False

    def get_registration_info(self) -> dict[str, dict[str, Any]]:
        """登録情報取得（デバッグ用）

        Returns:
            dict: 登録サービス情報
        """
        info = {}
        for service_type, registration in self._services.items():
            info[service_type.__name__] = {
                "is_singleton": registration.is_singleton,
                "has_instance": service_type in self._singletons
            }
        return info


class DIContainerError(Exception):
    """DIコンテナエラー"""


# グローバル DIコンテナ インスタンス
_global_container: DIContainer | None = None


def get_di_container() -> DIContainer:
    """グローバルDIコンテナ取得

    Returns:
        DIContainer: グローバルDIコンテナ
    """
    global _global_container
    if _global_container is None:
        _global_container = DIContainer()
    return _global_container


def initialize_global_container(project_root: Path | None = None) -> None:
    """グローバルDIコンテナ初期化

    Args:
        project_root: プロジェクトルートパス
    """
    container = get_di_container()
    container.initialize_core_services(project_root)
