"""ドメインコマンド基底クラス

SPEC-901-DDD-REFACTORING対応:
- CQRS（Command Query Responsibility Segregation）実装
- Message Busでのコマンド処理基盤
- MCPサーバー統合準備

参照: goldensamples/ddd_patterns_golden_sample.py
"""

import uuid
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class DomainCommand(ABC):
    """ドメインコマンド基底クラス

    特徴:
    - CQRS（Command Query Responsibility Segregation）対応
    - 不変コマンドオブジェクト
    - Message Busでの処理に対応
    - メタデータとトレーサビリティサポート

    SPEC-901要件:
    - コマンドとイベントの統一処理システム
    - MCPサーバーからのコマンド受信処理
    """

    # 自動設定されるフィールド
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    # 実行制御フィールド
    user_id: str | None = None
    correlation_id: str | None = None
    expected_version: int | None = None

    def __post_init__(self):
        """初期化後処理 - サブクラスでカスタマイズ可能"""
        if not self.correlation_id:
            self.correlation_id = f"cmd-{self.command_id[:8]}"

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
        """コマンドを辞書形式に変換

        Returns:
            コマンドデータ辞書
        """
        return {
            "command_type": self.__class__.__name__,
            "command_id": self.command_id,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id,
            "correlation_id": self.correlation_id,
            "expected_version": self.expected_version,
            "metadata": self.metadata,
            "data": {
                k: v for k, v in self.__dict__.items()
                if k not in ["command_id", "created_at", "metadata", "user_id", "correlation_id", "expected_version"]
            }
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainCommand":
        """辞書からコマンドを復元

        Args:
            data: コマンドデータ辞書

        Returns:
            ドメインコマンドインスタンス
        """
        # この基底クラスでは基本的な復元のみ実装
        # サブクラスで具体的な復元ロジックをオーバーライド
        instance = cls()
        instance.command_id = data.get("command_id", instance.command_id)
        instance.created_at = datetime.fromisoformat(data.get("created_at", instance.created_at.isoformat()))
        instance.user_id = data.get("user_id")
        instance.correlation_id = data.get("correlation_id", instance.correlation_id)
        instance.expected_version = data.get("expected_version")
        instance.metadata = data.get("metadata", {})
        return instance

    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.__class__.__name__}(id={self.command_id[:8]}, correlation={self.correlation_id})"

    def __repr__(self) -> str:
        """詳細表現"""
        return (f"{self.__class__.__name__}("
                f"command_id='{self.command_id}', "
                f"created_at='{self.created_at.isoformat()}', "
                f"correlation_id='{self.correlation_id}'"
                f")")


@dataclass
class MCPCommand(DomainCommand):
    """MCPサーバー統合コマンド基底クラス

    MCPサーバーから受信するコマンド用の基底クラス
    非同期処理やパフォーマンス最適化に対応
    """

    # MCP固有フィールド
    mcp_tool_name: str | None = None
    execution_mode: str = "async"  # "sync" | "async" | "concurrent"
    timeout_seconds: int = 300

    def __post_init__(self):
        """MCP コマンド特有の初期化処理"""
        super().__post_init__()
        if not self.correlation_id:
            self.correlation_id = f"mcp-{self.command_id[:8]}"


@dataclass
class SystemCommand(DomainCommand):
    """システムレベルコマンド基底クラス

    アプリケーション全体に関わるシステム操作用
    """

    # システム操作権限レベル
    privilege_level: str = "user"  # "user" | "admin" | "system"

    def __post_init__(self):
        """システムコマンド特有の初期化処理"""
        super().__post_init__()
        if not self.correlation_id:
            self.correlation_id = f"sys-{self.command_id[:8]}"
