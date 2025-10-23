"""Infrastructure.shared.unified_error_handler
Where: Infrastructure module providing a unified error handler.
What: Normalises exceptions and maps them to consistent error responses.
Why: Ensures infrastructure components report errors in a unified format.
"""

from noveler.presentation.shared.shared_utilities import console

"統一エラーハンドリングシステム\n\n中優先度問題解決:エラーハンドリングの不整合修正\n- 統一されたエラー処理パターン\n- 構造化されたエラーメッセージ\n- 適切なログレベル管理\n"
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from noveler.infrastructure.logging.unified_logger import get_logger


class ErrorSeverity(Enum):
    """エラー重要度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorResult:
    """エラー結果構造体"""

    success: bool
    message: str
    error_code: str | None = None
    details: dict[str, Any] | None = None
    severity: ErrorSeverity = ErrorSeverity.MEDIUM


T = TypeVar("T")


class UnifiedErrorHandler:
    """統一エラーハンドリングクラス"""

    def __init__(self, component_name: str) -> None:
        """Args:
        component_name: コンポーネント名(ログ用)
        """
        self.component_name = component_name
        self.logger = get_logger("novel.%s", component_name)

    def handle_with_result(
        self,
        operation: callable,
        operation_name: str,
        default_result: object = None,
        error_severity: str = "ERROR",
        user_message: str | None = None,
    ) -> tuple[object, ErrorResult]:
        """結果とエラー情報を両方返すハンドリング

        Args:
            operation: 実行する処理
            operation_name: 処理名(ログ・エラーメッセージ用)
            default_result: エラー時のデフォルト値
            error_severity: エラー重要度
            user_message: ユーザー向けメッセージ(指定されない場合は自動生成)

        Returns:
            (結果, エラー情報) のタプル
        """
        try:
            result = operation()
            return (result, ErrorResult(success=True, message=""))
        except Exception as e:
            error_code = f"{self.component_name}.{operation_name}.{type(e).__name__}"
            self._log_error(error_severity, operation_name, str(e), error_code)
            if user_message is None:
                user_message = self._generate_user_message(operation_name, error_severity)
            error_result = ErrorResult(
                success=False,
                message=user_message,
                error_code=error_code,
                details={"original_error": str(e), "operation": operation_name},
                severity=error_severity,
            )
            return (default_result, error_result)

    def handle_boolean_operation(
        self, operation: callable, operation_name: str, error_severity: str = "ERROR", user_message: str | None = None
    ) -> tuple[bool, ErrorResult]:
        """真偽値を返す処理用のハンドリング"""
        return self.handle_with_result(operation, operation_name, False, error_severity, user_message)

    def handle_optional_operation(
        self, operation: callable, operation_name: str, error_severity: str = "ERROR", user_message: str | None = None
    ) -> tuple[object | None, ErrorResult]:
        """オプショナル値を返す処理用のハンドリング"""
        return self.handle_with_result(operation, operation_name, None, error_severity, user_message)

    def handle_list_operation(
        self, operation: callable, operation_name: str, error_severity: str = "ERROR", user_message: str | None = None
    ) -> tuple[list[object], ErrorResult]:
        """リストを返す処理用のハンドリング"""
        return self.handle_with_result(operation, operation_name, [], error_severity, user_message)

    def _log_error(self, severity: ErrorSeverity, operation_name: str, error_message: str, error_code: str) -> None:
        """エラーレベルに応じたログ出力"""
        log_message = f"{operation_name}でエラー発生: {error_message} (コード: {error_code})"
        if severity in (ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH):
            console.print(log_message)
        elif severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)

    def _generate_user_message(self, operation_name: str, severity: ErrorSeverity) -> str:
        """ユーザー向けメッセージを生成"""
        base_messages = {
            ErrorSeverity.LOW: f"{operation_name}を実行しました(軽微な問題あり)",
            ErrorSeverity.MEDIUM: f"{operation_name}中に問題が発生しましたが、処理を続行します",
            ErrorSeverity.HIGH: f"{operation_name}でエラーが発生しました",
            ErrorSeverity.CRITICAL: f"{operation_name}で致命的なエラーが発生しました",
        }
        return base_messages.get(severity, f"{operation_name}でエラーが発生しました")


class ErrorHandlerFactory:
    """エラーハンドラーファクトリー"""

    _handlers: dict[str, UnifiedErrorHandler] = {}

    @classmethod
    def get_handler(cls, component_name: str) -> UnifiedErrorHandler:
        """コンポーネント用エラーハンドラーを取得"""
        if component_name not in cls._handlers:
            cls._handlers[component_name] = UnifiedErrorHandler(component_name)
        return cls._handlers[component_name]

    @classmethod
    def reset_handlers(cls) -> None:
        """テスト用:ハンドラーをリセット"""
        cls._handlers.clear()


def get_error_handler(component_name: str) -> UnifiedErrorHandler:
    """エラーハンドラーを取得する便利関数"""
    return ErrorHandlerFactory.get_handler(component_name)
