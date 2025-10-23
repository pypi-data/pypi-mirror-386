"""Infrastructure.di.service_provider
Where: Infrastructure module registering service providers in the DI container.
What: Binds service interfaces to concrete infrastructure implementations.
Why: Supports modular service registration for infrastructure components.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""サービスプロバイダー

DDD準拠: サービスの登録と初期化を管理
"""

from pathlib import Path
from typing import Any

from noveler.domain.interfaces.configuration_service import IConfigurationService
from noveler.domain.interfaces.logger_service import ILoggerService
from noveler.domain.interfaces.path_service import IPathService
from noveler.infrastructure.di.container import get_container, register_service


class ServiceProvider:
    """サービスプロバイダー

    アプリケーション起動時にサービスを登録する。
    """

    @staticmethod
    def register_all_services(project_root: Path | None = None) -> None:
        """すべてのサービスを登録

        Args:
            project_root: プロジェクトルートパス
        """
        # PathServiceの登録
        ServiceProvider.register_path_service(project_root)

        # ConfigurationServiceの登録
        ServiceProvider.register_configuration_service()

        # LoggerServiceの登録
        ServiceProvider.register_logger_service()

    @staticmethod
    def register_path_service(project_root: Path | None = None) -> None:
        """PathServiceを登録

        Args:
            project_root: プロジェクトルートパス
        """
        # 既存のインフラ実装をアダプター経由で登録
        from noveler.infrastructure.adapters.path_service_adapter import PathServiceAdapter

        if project_root is None:
            project_root = Path.cwd()

        path_service = PathServiceAdapter(project_root)
        register_service(IPathService, implementation=path_service)

    @staticmethod
    def register_configuration_service() -> None:
        """ConfigurationServiceを登録"""
        from noveler.infrastructure.adapters.configuration_service_adapter import ConfigurationServiceAdapter

        config_service = ConfigurationServiceAdapter()
        register_service(IConfigurationService, implementation=config_service)

    @staticmethod
    def register_logger_service() -> None:
        """LoggerServiceを登録"""
        from noveler.infrastructure.adapters.logger_service_adapter import LoggerServiceAdapter

        # ファクトリー関数で登録（遅延初期化）
        def create_logger_service() -> Any:
            return LoggerServiceAdapter(__name__)

        register_service(ILoggerService, factory=create_logger_service)

    @staticmethod
    def clear_all() -> None:
        """すべてのサービスをクリア"""
        container = get_container()
        container.clear()
