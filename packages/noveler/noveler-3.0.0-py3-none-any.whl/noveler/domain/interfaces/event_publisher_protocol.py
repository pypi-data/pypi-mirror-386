"""
ドメインイベントパブリッシャープロトコル

DDD原則に従い、ドメイン層がプレゼンテーション層（Console出力等）に
直接依存することを防ぐ抽象化インターフェース。

SPEC-DDD-COMPLIANCE-002: ドメインイベント抽象化
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class EventLevel(Enum):
    """イベントレベル"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class DomainEvent:
    """ドメインイベント基底クラス"""

    message: str
    level: EventLevel = EventLevel.INFO
    context: dict[str, Any] | None = None


@dataclass
class ProgressEvent:
    """進捗表示イベント"""

    message: str
    current: int
    total: int
    level: EventLevel = EventLevel.INFO
    context: dict[str, Any] | None = None


@dataclass
class ValidationEvent:
    """検証結果イベント"""

    message: str
    is_valid: bool
    details: dict[str, Any] | None = None
    level: EventLevel = EventLevel.INFO
    context: dict[str, Any] | None = None


class IDomainEventPublisher(Protocol):
    """ドメインイベントパブリッシャーインターフェース

    ドメイン層から外部への出力を抽象化し、
    Clean Architecture の原則を維持。
    """

    def publish(self, event: DomainEvent) -> None:
        """イベントを発行

        Args:
            event: 発行するドメインイベント
        """
        ...

    def publish_info(self, message: str, context: dict[str, Any] | None = None) -> None:
        """情報レベルのメッセージ発行

        Args:
            message: メッセージ
            context: 追加コンテキスト
        """
        ...

    def publish_warning(self, message: str, context: dict[str, Any] | None = None) -> None:
        """警告レベルのメッセージ発行

        Args:
            message: メッセージ
            context: 追加コンテキスト
        """
        ...

    def publish_error(self, message: str, context: dict[str, Any] | None = None) -> None:
        """エラーレベルのメッセージ発行

        Args:
            message: メッセージ
            context: 追加コンテキスト
        """
        ...

    def publish_progress(self, message: str, current: int, total: int) -> None:
        """進捗情報発行

        Args:
            message: 進捗メッセージ
            current: 現在位置
            total: 総数
        """
        ...
