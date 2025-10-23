"""Domain.value_objects.error_response
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""エラーレスポンスバリューオブジェクト

DDD準拠: Domain層のvalue object
エラー情報の不変性と構造化を保証
"""


from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ErrorSeverity(Enum):
    """エラー重要度"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorCategory(Enum):
    """エラーカテゴリ"""

    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    INFRASTRUCTURE = "infrastructure"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"
    USER_INPUT = "user_input"


@dataclass(frozen=True)
class ErrorResponse:
    """エラーレスポンスバリューオブジェクト"""

    error_code: str  # エラーコード
    message: str  # エラーメッセージ
    severity: ErrorSeverity  # 重要度
    category: ErrorCategory  # カテゴリ
    details: dict[str, Any] | None = None  # 詳細情報
    timestamp: datetime | None = None  # 発生時刻
    context: dict[str, Any] | None = None  # コンテキスト情報
    recovery_suggestions: tuple[str, ...] = ()  # 復旧提案

    def __post_init__(self) -> None:
        """後初期化バリデーション"""
        if not self.error_code.strip():
            msg = "error_code cannot be empty"
            raise ValueError(msg)

        if not self.message.strip():
            msg = "message cannot be empty"
            raise ValueError(msg)

        # timestampがNoneの場合は現在時刻を設定
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc))

    def is_critical(self) -> bool:
        """クリティカルエラー判定

        Returns:
            bool: クリティカルエラーの場合True
        """
        return self.severity == ErrorSeverity.CRITICAL

    def is_recoverable(self) -> bool:
        """回復可能エラー判定

        Returns:
            bool: 回復可能な場合True
        """
        return len(self.recovery_suggestions) > 0

    def get_formatted_message(self) -> str:
        """フォーマット済みメッセージ取得

        Returns:
            str: 重要度付きのフォーマット済みメッセージ
        """
        severity_prefix = {
            ErrorSeverity.CRITICAL: "🔴",
            ErrorSeverity.HIGH: "🟠",
            ErrorSeverity.MEDIUM: "🟡",
            ErrorSeverity.LOW: "🔵",
            ErrorSeverity.INFO: "ℹ️",
        }

        prefix = severity_prefix.get(self.severity, "")
        return f"{prefix} [{self.error_code}] {self.message}"

    def get_debug_info(self) -> dict[str, Any]:
        """デバッグ情報取得

        Returns:
            dict[str, Any]: デバッグ用の詳細情報
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "details": self.details,
            "context": self.context,
            "recovery_suggestions": list(self.recovery_suggestions),
            "is_critical": self.is_critical(),
            "is_recoverable": self.is_recoverable(),
        }

    @classmethod
    def create_validation_error(
        cls, error_code: str, message: str, details: dict[str, Any] | None = None
    ) -> ErrorResponse:
        """バリデーションエラー作成ファクトリ

        Args:
            error_code: エラーコード
            message: エラーメッセージ
            details: 詳細情報

        Returns:
            ErrorResponse: バリデーションエラー
        """
        return cls(
            error_code=error_code,
            message=message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
            details=details,
            recovery_suggestions=("入力内容を確認してください", "正しい形式で再入力してください"),
        )

    @classmethod
    def create_business_error(
        cls,
        error_code: str,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        details: dict[str, Any] | None = None,
    ) -> ErrorResponse:
        """ビジネスロジックエラー作成ファクトリ

        Args:
            error_code: エラーコード
            message: エラーメッセージ
            severity: 重要度
            details: 詳細情報

        Returns:
            ErrorResponse: ビジネスロジックエラー
        """
        return cls(
            error_code=error_code,
            message=message,
            severity=severity,
            category=ErrorCategory.BUSINESS_LOGIC,
            details=details,
        )

    @classmethod
    def create_system_error(
        cls, error_code: str, message: str, details: dict[str, Any] | None = None, context: dict[str, Any] | None = None
    ) -> ErrorResponse:
        """システムエラー作成ファクトリ

        Args:
            error_code: エラーコード
            message: エラーメッセージ
            details: 詳細情報
            context: コンテキスト情報

        Returns:
            ErrorResponse: システムエラー
        """
        return cls(
            error_code=error_code,
            message=message,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
            details=details,
            context=context,
            recovery_suggestions=("システム管理者に連絡してください", "しばらく時間をおいて再試行してください"),
        )
