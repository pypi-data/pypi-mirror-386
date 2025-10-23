"""サービスロケータープロトコル

循環依存解決のための統一的なサービスアクセスインターフェース
"""

from typing import TYPE_CHECKING, Protocol

from noveler.domain.protocols.unit_of_work_protocol import IUnitOfWorkProtocol

if TYPE_CHECKING:
    from noveler.domain.interfaces.configuration_service import IConfigurationService
    from noveler.domain.interfaces.console_service_protocol import IConsoleService
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.domain.interfaces.path_service_protocol import IPathService
    from noveler.domain.interfaces.repository_factory_protocol import IRepositoryFactory


class IServiceLocator(Protocol):
    """サービスロケータープロトコル

    循環依存を避けるための統一的なサービスアクセス点。
    各サービスは遅延取得され、必要な時のみインスタンス化される。
    """

    def get_logger_service(self) -> "ILoggerService | None":
        """ロガーサービス取得"""
        ...

    def get_console_service(self) -> "IConsoleService | None":
        """コンソールサービス取得"""
        ...

    def get_path_service(self, project_root: str | None = None) -> "IPathService | None":
        """パスサービス取得

        Args:
            project_root: プロジェクトルートパス（指定時は専用インスタンス作成）
        """
        ...

    def get_configuration_service(self) -> "IConfigurationService":
        """設定サービス取得"""
        ...

    def get_repository_factory(self) -> "IRepositoryFactory":
        """リポジトリファクトリー取得"""
        ...

    def get_unit_of_work(self) -> "IUnitOfWorkProtocol | None":
        """Unit of Work取得"""
        ...
