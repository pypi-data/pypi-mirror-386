"""統合サービスファクトリー基底クラス

全サービスの統一的な生成管理を提供。
循環依存を回避しつつ、DIパターンを実現する。
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.protocols import (
        IConfigurationServiceProtocol,
        IConsoleServiceProtocol,
        ILoggerProtocol,
        IPathServiceProtocol,
        IRepositoryFactoryProtocol,
        IUnitOfWorkProtocol,
    )


class BaseServiceFactory:
    """統合サービスファクトリー基底クラス

    全サービスの生成ロジックを一元管理。
    Protocol分離により循環依存を回避する。
    """

    def create_logger_service(self) -> "ILoggerProtocol":
        """ロガーサービス生成

        Returns:
            ロガーサービスインスタンス
        """
        # 遅延インポートで循環依存回避
        from noveler.infrastructure.adapters.domain_logger_adapter import DomainLoggerAdapter

        return DomainLoggerAdapter()

    def create_unit_of_work(self) -> "IUnitOfWorkProtocol":
        """Unit of Work生成

        Returns:
            Unit of Workインスタンス
        """
        # 遅延インポートで循環依存回避
        from noveler.infrastructure.di.unified_repository_factory import UnifiedRepositoryFactory

        factory = UnifiedRepositoryFactory()
        return factory.get_unit_of_work()

    def create_console_service(self) -> "IConsoleServiceProtocol":
        """コンソールサービス生成

        Returns:
            コンソールサービスインスタンス
        """
        # 遅延インポートで循環依存回避
        from noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceAdapter
        return ConsoleServiceAdapter()

    def create_path_service(self, project_root: str | None = None) -> "IPathServiceProtocol":
        """パスサービス生成

        Args:
            project_root: プロジェクトルートパス（省略時はデフォルト）

        Returns:
            パスサービスインスタンス
        """
        # 遅延インポートで循環依存回避
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service
        return create_path_service(project_root)

    def create_configuration_service(self) -> "IConfigurationServiceProtocol":
        """設定サービス生成

        Returns:
            設定サービスインスタンス
        """
        # 遅延インポートで循環依存回避
        from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager
        return get_configuration_manager()

    def create_repository_factory(self) -> "IRepositoryFactoryProtocol":
        """リポジトリファクトリー生成

        Returns:
            リポジトリファクトリーインスタンス
        """
        # 遅延インポートで循環依存回避
        from noveler.infrastructure.factories.unified_repository_factory import UnifiedRepositoryFactory
        return UnifiedRepositoryFactory()


class ServiceFactoryManager:
    """サービスファクトリー管理クラス

    ファクトリーインスタンスの管理とアクセス制御を提供。
    """

    _instance: "ServiceFactoryManager | None" = None
    _factory: BaseServiceFactory | None = None

    def __new__(cls) -> "ServiceFactoryManager":
        """シングルトンインスタンス取得"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def factory(self) -> BaseServiceFactory:
        """ファクトリーインスタンス取得

        Returns:
            BaseServiceFactoryインスタンス
        """
        if self._factory is None:
            self._factory = BaseServiceFactory()
        return self._factory

    def set_factory(self, factory: BaseServiceFactory) -> None:
        """ファクトリー設定（テスト用）

        Args:
            factory: 設定するファクトリーインスタンス
        """
        self._factory = factory

    def reset(self) -> None:
        """ファクトリーリセット（テスト用）"""
        self._factory = None


# グローバルアクセス用関数
def get_service_factory() -> BaseServiceFactory:
    """サービスファクトリー取得

    Returns:
        BaseServiceFactoryインスタンス
    """
    manager = ServiceFactoryManager()
    return manager.factory
