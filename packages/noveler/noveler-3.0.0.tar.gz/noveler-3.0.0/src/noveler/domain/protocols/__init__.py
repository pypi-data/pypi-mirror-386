"""ドメインProtocol統合モジュール

循環依存回避のための純粋なProtocol定義集約。
関数レベルインポートを避け、型安全性を確保する。

使用方法:
```python
from noveler.domain.protocols import (
    ILoggerProtocol,
    IUnitOfWorkProtocol,
    IConsoleServiceProtocol,
    IPathServiceProtocol,
    IConfigurationServiceProtocol,
    IRepositoryFactoryProtocol
)
```
"""

from noveler.domain.protocols.configuration_service_protocol import IConfigurationServiceProtocol
from noveler.domain.protocols.console_service_protocol import IConsoleServiceProtocol
from noveler.domain.protocols.logger_protocol import ILoggerProtocol
from noveler.domain.protocols.path_service_protocol import IPathServiceProtocol
from noveler.domain.protocols.repository_factory_protocol import IRepositoryFactoryProtocol
from noveler.domain.protocols.unit_of_work_protocol import IUnitOfWorkProtocol

__all__ = [
    "IConfigurationServiceProtocol",
    "IConsoleServiceProtocol",
    "ILoggerProtocol",
    "IPathServiceProtocol",
    "IRepositoryFactoryProtocol",
    "IUnitOfWorkProtocol",
]
