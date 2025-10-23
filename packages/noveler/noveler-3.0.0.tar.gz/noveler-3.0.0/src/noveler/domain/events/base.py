"""ドメインイベント基底クラス

SPEC-901-DDD-REFACTORING対応:
- Domain Events管理システムの基盤
- 集約ルート内でのイベント収集・発行機能
- Message Bus統合準備

参照: goldensamples/ddd_patterns_golden_sample.py
"""

import uuid
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class DomainEvent(ABC):
    """ドメインイベント基底クラス

    特徴:
    - 不変オブジェクト（frozen=True設定可能）
    - 自動的にID・タイムスタンプ付与
    - メタデータサポート
    - Message Busでの処理に対応

    SPEC-901要件:
    - Domain Events の収集・発行機能
    - イベント駆動処理の基盤
    """

    # 自動設定されるフィールド
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)

    # 追跡用フィールド
    aggregate_id: str | None = None
    aggregate_type: str | None = None
    version: int = 1

    def __post_init__(self):
        """初期化後処理 - サブクラスでカスタマイズ可能"""

    def add_metadata(self, key: str, value: Any) -> None:
        """メタデータ追加

        Args:
            key: メタデータキー
            value: メタデータ値
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """メタデータ取得

        Args:
            key: メタデータキー
            default: デフォルト値

        Returns:
            メタデータ値
        """
        return self.metadata.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        """イベントを辞書形式に変換

        Returns:
            イベントデータ辞書
        """
        return {
            "event_type": self.__class__.__name__,
            "event_id": self.event_id,
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "version": self.version,
            "metadata": self.metadata,
            "data": {
                k: v for k, v in self.__dict__.items()
                if k not in ["event_id", "occurred_at", "metadata", "aggregate_id", "aggregate_type", "version"]
            }
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainEvent":
        """辞書からイベントを復元

        Args:
            data: イベントデータ辞書

        Returns:
            ドメインイベントインスタンス
        """
        # この基底クラスでは基本的な復元のみ実装
        # サブクラスで具体的な復元ロジックをオーバーライド
        instance = cls()
        instance.event_id = data.get("event_id", instance.event_id)
        instance.occurred_at = datetime.fromisoformat(data.get("occurred_at", instance.occurred_at.isoformat()))
        instance.aggregate_id = data.get("aggregate_id")
        instance.aggregate_type = data.get("aggregate_type")
        instance.version = data.get("version", 1)
        instance.metadata = data.get("metadata", {})
        return instance

    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.__class__.__name__}(id={self.event_id[:8]}, aggregate={self.aggregate_id})"

    def __repr__(self) -> str:
        """詳細表現"""
        return (f"{self.__class__.__name__}("
                f"event_id='{self.event_id}', "
                f"occurred_at='{self.occurred_at.isoformat()}', "
                f"aggregate_id='{self.aggregate_id}'"
                f")")


@dataclass
class SystemEvent(DomainEvent):
    """システムレベルイベント基底クラス

    アプリケーション全体に関わるシステムイベント用
    """


@dataclass
class IntegrationEvent(DomainEvent):
    """統合イベント基底クラス

    外部システムとの統合に関わるイベント用
    MCPサーバーとの連携等で使用
    """

    # 統合先情報
    target_system: str | None = None
    correlation_id: str | None = None

    def __post_init__(self):
        """統合イベント特有の初期化処理"""
        super().__post_init__()
        if not self.correlation_id:
            self.correlation_id = f"integ-{self.event_id[:8]}"
