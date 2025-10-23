"""Base class for Noveler application-layer use cases."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

# モジュールレベルでimport（循環依存回避版）
from noveler.infrastructure.di.service_locator import get_service_locator

if TYPE_CHECKING:
    from pathlib import Path

    from noveler.domain.interfaces import (
        IConfigurationService,
        IConsoleService,
        ILoggerService,
        IPathService,
        IRepositoryFactory,
    )
    from noveler.domain.interfaces.service_locator_protocol import IServiceLocator
    from noveler.infrastructure.unit_of_work import IUnitOfWork

RequestType = TypeVar("RequestType")
ResponseType = TypeVar("ResponseType")


class AbstractUseCase(ABC, Generic[RequestType, ResponseType]):
    """Base class that coordinates dependency lookup for use cases."""

    def __init__(
        self,
        service_locator: "IServiceLocator | None" = None,
        # 後方互換性のため既存パラメータを維持
        logger_service: "ILoggerService | None" = None,
        unit_of_work: "IUnitOfWork | None" = None,
        console_service: "IConsoleService | None" = None,
        path_service: "IPathService | None" = None,
        config_service: "IConfigurationService | None" = None,
        repository_factory: "IRepositoryFactory | None" = None,
        **kwargs: object,  # 既存コードとの互換性
    ) -> None:
        """Initialise the use case with optional explicit dependencies.

        Args:
            service_locator (IServiceLocator | None): Service locator instance.
            logger_service (ILoggerService | None): Optional logger override.
            unit_of_work (IUnitOfWork | None): Optional Unit of Work override.
            console_service (IConsoleService | None): Optional console service
                override.
            path_service (IPathService | None): Optional path service override.
            config_service (IConfigurationService | None): Optional config
                service override.
            repository_factory (IRepositoryFactory | None): Optional repository
                factory override.
            **kwargs: Additional keyword arguments kept for backwards
                compatibility.
        """
        # ServiceLocator優先、フォールバックで個別注入
        if service_locator is not None:
            self._service_locator = service_locator
        else:
            self._service_locator = get_service_locator()

        # 後方互換性：既存の個別サービス注入もサポート
        self._injected_logger_service = logger_service
        self._injected_unit_of_work = unit_of_work
        self._injected_console_service = console_service
        self._injected_path_service = path_service
        self._injected_config_service = config_service
        self._injected_repository_factory = repository_factory

        # レガシー対応
        self._legacy_logger = kwargs.get("logger")

    @property
    def logger_service(self) -> "ILoggerService | None":
        """Return the logger service, preferring explicitly injected values."""
        # 個別注入が優先、次にServiceLocator
        if self._injected_logger_service is not None:
            return self._injected_logger_service
        return self._service_locator.get_logger_service()

    @property
    def unit_of_work(self) -> "IUnitOfWork | None":
        """Return the Unit of Work, preferring explicitly injected values."""
        if self._injected_unit_of_work is not None:
            return self._injected_unit_of_work
        return self._service_locator.get_unit_of_work()

    @property
    def logger(self) -> "ILoggerService | None":
        """Backward-compatible alias that returns :attr:`logger_service`."""
        return self.logger_service

    @property
    def console_service(self) -> "IConsoleService | None":
        """Return the console service, preferring explicitly injected values."""
        if self._injected_console_service is not None:
            return self._injected_console_service
        return self._service_locator.get_console_service()

    @property
    def path_service(self) -> "IPathService | None":
        """Return the path service, preferring explicitly injected values."""
        if self._injected_path_service is not None:
            return self._injected_path_service
        return self._service_locator.get_path_service()

    def get_path_service(self, project_root: "Path | str | None" = None) -> "IPathService":
        """Return a path service instance for the given project root.

        Args:
            project_root (Path | str | None): Optional project root override.

        Returns:
            IPathService: Path service instance.
        """
        if project_root is None:
            return self.path_service

        # プロジェクトルート指定時は新しいインスタンスを取得
        return self._service_locator.get_path_service(str(project_root) if project_root else None)

    @property
    def config_service(self) -> "IConfigurationService":
        """Return the configuration service, preferring injected values."""
        if self._injected_config_service is not None:
            return self._injected_config_service
        return self._service_locator.get_configuration_service()

    @property
    def repository_factory(self) -> "IRepositoryFactory":
        """Return the repository factory, preferring injected values."""
        if self._injected_repository_factory is not None:
            return self._injected_repository_factory
        return self._service_locator.get_repository_factory()

    @abstractmethod
    def execute(self, request: RequestType) -> ResponseType:
        """Invoke the use case logic. Subclasses must implement this method."""
