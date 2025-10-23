#!/usr/bin/env python3
"""Common error handling service used across application workflows."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar

from noveler.domain.errors import BaseError

# DDD準拠: Application層はInfrastructure層に直接依存しない
# ロガーは依存性注入により提供
from noveler.domain.services.error_classifier import ErrorClassifier, ErrorLevel

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService

T = TypeVar("T")


@dataclass
class ErrorResult:
    """Value object returned after processing an exception."""
    handled: bool
    user_message: str
    log_level: ErrorLevel
    requires_restart: bool = False
    recovery_suggestions: list[str] = None

    def __post_init__(self):
        if self.recovery_suggestions is None:
            self.recovery_suggestions = []


class ErrorHandlingService:
    """Coordinate logging, user messaging, and recovery suggestions for errors."""

    def __init__(self, logger_service: "ILoggerService", console_service=None) -> None:
        """Initialize the service with injected logger and optional console providers."""
        # DDD準拠: Application層はInfrastructure層に直接依存しない
        # 依存性注入パターンで対応
        self.logger = logger_service
        self.console_service = console_service  # テスト互換性のため追加

        # DDD準拠: ロガーはコンストラクタ注入により提供される

    def safe_execute(
        self, operation: Callable[[], T], error_response_factory: Callable[[str], T], operation_name: str = "操作"
    ) -> T:
        """Execute an operation and return a fallback response on failure."""
        try:
            return operation()
        except Exception as e:
            error_message = f"{operation_name}エラー: {e}"
            self.logger.error(error_message, exc_info=True)
            return error_response_factory(error_message)

    @staticmethod
    def create_error_response(response_class: type, **kwargs: Any) -> Any:
        """Build a standardized error response using the provided class."""
        return response_class(success=False, **kwargs)

    def handle_error(self, error: Exception, context: dict | None = None) -> ErrorResult:
        """Handle an exception and return an ``ErrorResult``."""
        # Pure function: エラー分類
        level = ErrorClassifier.classify(error)
        error_context = ErrorClassifier.extract_context(error)
        user_message = ErrorClassifier.get_user_friendly_message(error, level)
        _should_notify = ErrorClassifier.should_notify_user(level)  # 将来の拡張用

        # Side effects: ログ記録
        self._log_error(error, level, error_context, context)

        # 結果生成
        return ErrorResult(
            handled=True,
            user_message=user_message,
            log_level=level,
            requires_restart=(level == ErrorLevel.CRITICAL),
            recovery_suggestions=self._get_recovery_suggestions(error, level)
        )

    def _log_error(self, error: Exception, level: ErrorLevel,
                   error_context: dict, additional_context: dict | None = None) -> None:
        """Write the error to the injected logger using severity-aware logging."""
        log_message = f"{error_context['error_type']}: {error_context['message']}"

        if additional_context:
            log_message += f" | Context: {additional_context}"

        # レベルに応じたログ出力
        if level == ErrorLevel.CRITICAL:
            self.logger.critical(log_message)
        elif level == ErrorLevel.ERROR:
            self.logger.error(log_message)
        elif level == ErrorLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def _get_recovery_suggestions(self, error: Exception, level: ErrorLevel) -> list[str]:
        """Return recovery suggestions tailored to the error level."""
        suggestions = []

        if isinstance(error, BaseError):
            if hasattr(error, "details") and "suggestions" in error.details:
                suggestions.extend(error.details["suggestions"])

        if level == ErrorLevel.CRITICAL:
            suggestions.append("システム管理者に連絡してください")
            suggestions.append("アプリケーションの再起動を検討してください")
        elif level == ErrorLevel.ERROR:
            suggestions.append("入力内容を確認してください")
            suggestions.append("しばらく待ってから再試行してください")

        return suggestions

    @staticmethod
    def create_success_response(response_class: type, **kwargs: Any) -> Any:
        """Build a standardized success response using the provided class."""
        return response_class(success=True, **kwargs)
