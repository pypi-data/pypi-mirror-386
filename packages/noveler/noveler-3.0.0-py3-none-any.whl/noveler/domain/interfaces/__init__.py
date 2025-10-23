"""ドメインインターフェース

DDDアーキテクチャのドメイン層インターフェース
"""

from noveler.domain.interfaces.configuration_service import IConfigurationService
from noveler.domain.interfaces.console_service_protocol import IConsoleService

# イベント処理
from noveler.domain.interfaces.event_publisher_protocol import (
    DomainEvent,
    EventLevel,
    IDomainEventPublisher,
    ProgressEvent,
    ValidationEvent,
)

# 主要インターフェース
from noveler.domain.interfaces.logger import ILogger
from noveler.domain.interfaces.path_service import IPathService
from noveler.domain.interfaces.repository_factory import IRepositoryFactory
from noveler.domain.interfaces.path_service_protocol import (
    PathServiceFactoryProtocol as IPathServiceFactory,
)

# 設定・リポジトリ
from noveler.domain.interfaces.settings_repository import (
    IProjectSettingsRepository,
    ISettingsRepositoryFactory,
    IWriterProgressRepository,
)

__all__ = [
    # イベント処理
    "DomainEvent",
    "EventLevel",
    "IConfigurationService",
    "IConsoleService",
    "IDomainEventPublisher",
    # 主要インターフェース
    "ILogger",
    "IPathService",
    "IPathServiceFactory",
    "IProjectSettingsRepository",
    "IRepositoryFactory",
    # 設定・リポジトリ
    "ISettingsRepositoryFactory",
    "IWriterProgressRepository",
    "ProgressEvent",
    "ValidationEvent",
]
