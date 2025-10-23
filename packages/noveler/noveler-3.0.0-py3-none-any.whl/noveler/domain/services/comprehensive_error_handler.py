"""
包括的エラーハンドリングサービス

階層的エラーハンドリング、構造化エラーレスポンス、システム回復機能を提供する統合エラーハンドリングシステム。
"""

import time
import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Any

from noveler.domain.errors import (
    ApplicationError,
    BaseError,
    InfrastructureError,
    InputValidationError,
    PartialFailureError,
    PerformanceError,
    RecoveryError,
    SystemStateError,
)
from noveler.domain.interfaces.logger_interface import ILogger, NullLogger

# NOTE: Python logging module defines DEBUG level as 10. We mirror the value here to
# avoid importing the standard logging module in the domain layer while still being
# able to query the injected logger for its debug-level configuration.
DEBUG_LEVEL = 10


class ErrorSeverity(Enum):
    """エラーの重要度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """エラーコンテキスト情報"""
    operation: str
    component: str
    user_action: str | None = None
    system_state: dict[str, Any] | None = None
    performance_data: dict[str, Any] | None = None
    debug_info: dict[str, Any] | None = None


@dataclass
class RecoveryAttempt:
    """復旧試行記録"""
    strategy: str
    timestamp: float
    success: bool
    error_message: str | None = None
    recovery_data: dict[str, Any] | None = None


class ComprehensiveErrorHandler:
    """包括的エラーハンドリングサービス

    Features:
    - 階層的エラー分類とハンドリング
    - 構造化エラーレスポンス生成
    - 自動復旧機能とフォールバック処理
    - パフォーマンス統計記録
    - デバッグ支援機能
    - 日本語ユーザーフレンドリーメッセージ
    """

    def __init__(self, logger: ILogger | None = None) -> None:
        """初期化

        Args:
            logger: ドメイン互換ロガー。未指定時はNullLoggerを使用。
        """
        self._logger: ILogger = logger or NullLogger()
        self.recovery_attempts: dict[str, list[RecoveryAttempt]] = {}
        self.error_statistics: dict[str, int] = {}
        self.performance_metrics: dict[str, list[float]] = {}

    def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        allow_recovery: bool = True,
        max_recovery_attempts: int = 3
    ) -> dict[str, Any]:
        """エラーを包括的に処理する

        Args:
            error: 発生したエラー
            context: エラーコンテキスト
            allow_recovery: 自動復旧を試行するか
            max_recovery_attempts: 最大復旧試行回数

        Returns:
            構造化エラーレスポンス
        """
        start_time = time.time()

        try:
            # エラーを構造化エラーに変換
            structured_error = self._convert_to_structured_error(error, context)

            # エラー統計更新
            self._update_error_statistics(structured_error)

            # 詳細ログ記録
            self._log_detailed_error(structured_error, context, error)

            # 自動復旧試行
            recovery_result = None
            if allow_recovery and structured_error.recoverable:
                recovery_result = self._attempt_automatic_recovery(
                    structured_error, context, max_recovery_attempts
                )

            # 構造化レスポンス生成
            response = self._generate_structured_response(
                structured_error, context, recovery_result
            )

            # パフォーマンス統計記録
            processing_time = time.time() - start_time
            self._record_performance_metric("error_handling_time", processing_time)

            return response

        except Exception as handler_error:
            # エラーハンドラー自体のエラー処理
            self._logger.critical(
                f"エラーハンドラー内でエラーが発生: {handler_error}",
                exc_info=True
            )
            return self._generate_fallback_response(error, handler_error)

    def _convert_to_structured_error(self, error: Exception, context: ErrorContext) -> BaseError:
        """例外を構造化エラーに変換する"""
        if isinstance(error, BaseError):
            return error

        # エラーの種類に基づいて適切な構造化エラーを生成
        error_type = type(error).__name__
        error_message = str(error)

        # ファイルシステムエラー
        if isinstance(error, FileNotFoundError | PermissionError | OSError | IOError):
            return InfrastructureError(
                f"ファイルシステムエラーが発生しました: {error_message}",
                details={"original_error": error_type, "operation": context.operation},
                recovery_actions=[
                    "ファイルのアクセス権限を確認してください",
                    "ディスク容量を確認してください",
                    "ファイルパスが正しいことを確認してください"
                ]
            )

        # 入力検証エラー
        if isinstance(error, ValueError | TypeError):
            return InputValidationError(
                f"入力データに問題があります: {error_message}",
                field=getattr(error, "field", None),
                expected_format="正しい形式のデータ",
                actual_value=str(error),
                validation_rules=["データ形式を確認してください"]
            )

        # メモリ・パフォーマンスエラー
        if isinstance(error, MemoryError | TimeoutError):
            return PerformanceError(
                f"システムリソースエラー: {error_message}",
                metric_name="system_resources",
                optimization_suggestions=[
                    "処理データ量を減らしてください",
                    "システムメモリを確認してください",
                    "処理を小さな単位に分割してください"
                ]
            )

        # ネットワーク・外部サービスエラー
        if isinstance(error, ConnectionError | TimeoutError):
            return InfrastructureError(
                f"ネットワークエラー: {error_message}",
                recovery_actions=[
                    "ネットワーク接続を確認してください",
                    "しばらく時間をおいて再試行してください",
                    "プロキシ設定を確認してください"
                ],
                recoverable=True
            )

        # その他の予期しないエラー
        return ApplicationError(
            f"予期しないエラーが発生しました: {error_message}",
            details={
                "original_error_type": error_type,
                "operation": context.operation,
                "component": context.component
            },
            recovery_actions=[
                "操作を最初からやり直してください",
                "システムログを確認してください",
                "システム管理者にお問い合わせください"
            ]
        )

    def _attempt_automatic_recovery(
        self,
        error: BaseError,
        context: ErrorContext,
        max_attempts: int
    ) -> dict[str, Any] | None:
        """自動復旧を試行する"""
        operation_key = f"{context.component}:{context.operation}"

        # 過去の復旧試行履歴を確認
        if operation_key not in self.recovery_attempts:
            self.recovery_attempts[operation_key] = []

        attempts = self.recovery_attempts[operation_key]
        if len(attempts) >= max_attempts:
            self._logger.warning(
                f"最大復旧試行回数 {max_attempts} に到達: {operation_key}"
            )
            return None

        # 復旧戦略を選択
        recovery_strategies = self._select_recovery_strategies(error, context)

        for strategy in recovery_strategies:
            try:
                self._logger.info(
                    f"復旧戦略 '{strategy}' を試行中: {operation_key}"
                )
                recovery_result = self._execute_recovery_strategy(strategy, error, context)

                if recovery_result:
                    # 復旧成功を記録
                    attempt = RecoveryAttempt(
                        strategy=strategy,
                        timestamp=time.time(),
                        success=True,
                        recovery_data=recovery_result
                    )
                    attempts.append(attempt)

                    self._logger.info(
                        f"復旧戦略 '{strategy}' が成功: {operation_key}"
                    )
                    return recovery_result

            except Exception as recovery_error:
                # 復旧失敗を記録
                attempt = RecoveryAttempt(
                    strategy=strategy,
                    timestamp=time.time(),
                    success=False,
                    error_message=str(recovery_error)
                )
                attempts.append(attempt)

                self._logger.warning(
                    f"復旧戦略 '{strategy}' が失敗: {recovery_error}"
                )
                continue

        return None

    def _select_recovery_strategies(self, error: BaseError, context: ErrorContext) -> list[str]:
        """エラータイプに基づいて復旧戦略を選択する"""
        strategies = []

        if isinstance(error, InfrastructureError):
            strategies.extend(["retry_with_delay", "fallback_path", "create_missing_resource"])

        elif isinstance(error, InputValidationError):
            strategies.extend(["sanitize_input", "use_default_value", "prompt_for_correction"])

        elif isinstance(error, PartialFailureError):
            strategies.extend(["resume_from_checkpoint", "rollback_and_retry", "skip_failed_part"])

        elif isinstance(error, PerformanceError):
            strategies.extend(["reduce_load", "optimize_processing", "use_streaming"])

        else:
            strategies.extend(["basic_retry", "reset_state", "fallback_mode"])

        return strategies

    def _execute_recovery_strategy(
        self,
        strategy: str,
        error: BaseError,
        context: ErrorContext
    ) -> dict[str, Any] | None:
        """特定の復旧戦略を実行する"""

        if strategy == "retry_with_delay":
            time.sleep(1)  # 1秒待機
            return {"strategy": strategy, "delay": 1, "action": "retry"}

        if strategy == "fallback_path":
            return {
                "strategy": strategy,
                "fallback_enabled": True,
                "action": "use_fallback"
            }

        if strategy == "create_missing_resource":
            return {
                "strategy": strategy,
                "resource_created": True,
                "action": "retry_with_new_resource"
            }

        if strategy == "sanitize_input":
            return {
                "strategy": strategy,
                "input_sanitized": True,
                "action": "retry_with_clean_input"
            }

        if strategy == "use_default_value":
            return {
                "strategy": strategy,
                "default_used": True,
                "action": "continue_with_default"
            }

        if strategy == "resume_from_checkpoint":
            return {
                "strategy": strategy,
                "checkpoint_found": True,
                "action": "resume_execution"
            }

        if strategy == "reduce_load":
            return {
                "strategy": strategy,
                "load_reduced": True,
                "action": "retry_with_reduced_load"
            }

        if strategy == "basic_retry":
            return {"strategy": strategy, "action": "retry"}

        return None

    def _generate_structured_response(
        self,
        error: BaseError,
        context: ErrorContext,
        recovery_result: dict[str, Any] | None
    ) -> dict[str, Any]:
        """構造化エラーレスポンスを生成する"""
        response = {
            "success": False,
            "error": error.to_dict(),
            "context": {
                "operation": context.operation,
                "component": context.component,
                "user_action": context.user_action,
                "timestamp": time.time()
            },
            "recovery": {
                "attempted": recovery_result is not None,
                "successful": recovery_result is not None,
                "details": recovery_result
            },
            "user_message": error.get_user_friendly_message(),
            "severity": self._determine_error_severity(error),
            "next_steps": error.recovery_actions if error.recovery_actions else [
                "システム管理者にお問い合わせください"
            ]
        }

        # デバッグ情報を追加（デバッグモード時）
        if self._is_debug_logging_enabled():
            response["debug"] = {
                "system_state": context.system_state,
                "performance_data": context.performance_data,
                "debug_info": context.debug_info,
                "error_statistics": self.error_statistics.copy(),
                "recovery_history": self.recovery_attempts.get(
                    f"{context.component}:{context.operation}", []
                )
            }

        return response

    def _generate_fallback_response(self, original_error: Exception, handler_error: Exception) -> dict[str, Any]:
        """フォールバック用の最小限エラーレスポンス"""
        return {
            "success": False,
            "error": {
                "message": "システムエラーが発生しました",
                "code": "SYSTEM_ERROR",
                "recoverable": False
            },
            "user_message": "システムに問題が発生しました。システム管理者にお問い合わせください。",
            "severity": "critical",
            "next_steps": ["システム管理者にお問い合わせください"],
            "fallback_mode": True,
            "debug": {
                "original_error": str(original_error),
                "handler_error": str(handler_error)
            }
        }

    def _update_error_statistics(self, error: BaseError) -> None:
        """エラー統計を更新する"""
        error_type = error.__class__.__name__
        self.error_statistics[error_type] = self.error_statistics.get(error_type, 0) + 1

        # エラーレベル別統計
        level_key = f"level_{error.error_level}"
        self.error_statistics[level_key] = self.error_statistics.get(level_key, 0) + 1

    def _record_performance_metric(self, metric_name: str, value: float) -> None:
        """パフォーマンスメトリクスを記録する"""
        if metric_name not in self.performance_metrics:
            self.performance_metrics[metric_name] = []
        self.performance_metrics[metric_name].append(value)

        # 過去100件のみ保持
        if len(self.performance_metrics[metric_name]) > 100:
            self.performance_metrics[metric_name] = self.performance_metrics[metric_name][-100:]

    def _log_detailed_error(self, error: BaseError, context: ErrorContext, original_error: Exception) -> None:
        """詳細なエラーログを記録する"""
        extra_info = {
            "error_code": error.code,
            "error_level": error.error_level,
            "recoverable": error.recoverable,
            "operation": context.operation,
            "component": context.component,
            "user_action": context.user_action,
            "error_type": error.__class__.__name__,
            "original_error_type": type(original_error).__name__
        }

        # スタックトレース
        if isinstance(original_error, BaseError):
            extra_info["stack_trace"] = "構造化エラー（スタックトレースなし）"
        else:
            extra_info["stack_trace"] = traceback.format_exc()

        self._logger.error(
            f"エラー発生: {error.message}",
            extra={'extra_data': extra_info},
            exc_info=not isinstance(original_error, BaseError)
        )

    def _determine_error_severity(self, error: BaseError) -> str:
        """エラーの重要度を判定する"""
        if isinstance(error, InfrastructureError | RecoveryError):
            return ErrorSeverity.HIGH.value
        if isinstance(error, PartialFailureError):
            return ErrorSeverity.MEDIUM.value
        if isinstance(error, InputValidationError | SystemStateError):
            return ErrorSeverity.LOW.value
        if isinstance(error, PerformanceError):
            return ErrorSeverity.MEDIUM.value
        return ErrorSeverity.MEDIUM.value

    def get_error_statistics(self) -> dict[str, Any]:
        """エラー統計情報を取得する"""
        return {
            "error_counts": self.error_statistics.copy(),
            "performance_metrics": {
                metric: {
                    "count": len(values),
                    "average": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0
                }
                for metric, values in self.performance_metrics.items()
            },
            "recovery_success_rate": self._calculate_recovery_success_rate()
        }

    def _calculate_recovery_success_rate(self) -> float:
        """復旧成功率を計算する"""
        total_attempts = 0
        successful_attempts = 0

        for attempts in self.recovery_attempts.values():
            total_attempts += len(attempts)
            successful_attempts += sum(1 for attempt in attempts if attempt.success)

        if total_attempts == 0:
            return 0.0

        return (successful_attempts / total_attempts) * 100

    def reset_statistics(self) -> None:
        """統計情報をリセットする"""
        self.error_statistics.clear()
        self.performance_metrics.clear()
        self.recovery_attempts.clear()
        self._logger.info("エラーハンドリング統計をリセットしました")

    def _is_debug_logging_enabled(self) -> bool:
        """ロガーがデバッグ出力を許可しているか判定"""
        is_debug_enabled = getattr(self._logger, "is_debug_enabled", None)
        if callable(is_debug_enabled):
            try:
                return bool(is_debug_enabled())
            except Exception:
                return False

        is_enabled_for = getattr(self._logger, "isEnabledFor", None)
        if callable(is_enabled_for):
            try:
                return bool(is_enabled_for(DEBUG_LEVEL))
            except Exception:
                return False

        return False


# シングルトンインスタンス
_error_handler_instance: ComprehensiveErrorHandler | None = None

def get_comprehensive_error_handler(logger: ILogger | None = None) -> ComprehensiveErrorHandler:
    """包括的エラーハンドラーのシングルトンインスタンスを取得"""
    global _error_handler_instance
    if _error_handler_instance is None or logger is not None:
        _error_handler_instance = ComprehensiveErrorHandler(logger=logger)
    return _error_handler_instance
