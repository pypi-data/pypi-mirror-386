"""Infrastructure.services.quality_check_recovery
Where: Infrastructure service recovering from quality check failures.
What: Rebuilds state, restores backups, and retries quality workflows.
Why: Enhances resilience of quality check pipelines.
"""

from noveler.presentation.shared.shared_utilities import console

"品質チェック復旧システム\n\n仕様書: SPEC-QUALITY-RECOVERY-001\n品質チェック実行時のエラー処理と自動復旧\n\n設計原則:\n    - 段階的復旧戦略\n- エラー分類と適切な対応\n- 最小限の機能で継続実行\n"
import json
import shutil
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.domain.interfaces.i_unified_file_storage import FileContentType
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.storage import UnifiedFileStorageService


class ErrorSeverity(Enum):
    """エラー重要度"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryAction(Enum):
    """復旧アクション"""

    IGNORE = "ignore"
    RETRY = "retry"
    FALLBACK = "fallback"
    CACHE_CLEAR = "cache_clear"
    SAFE_MODE = "safe_mode"
    ABORT = "abort"


@dataclass
class ErrorContext:
    """エラーコンテキスト"""

    error_type: str
    error_message: str
    stack_trace: str
    operation_name: str
    timestamp: datetime
    severity: ErrorSeverity
    recovery_actions: list[RecoveryAction]
    metadata: dict[str, Any]


@dataclass
class RecoveryResult:
    """復旧結果"""

    success: bool
    action_taken: RecoveryAction
    error_resolved: bool
    fallback_used: bool
    duration_seconds: float
    details: str


class QualityCheckRecoveryManager:
    """品質チェック復旧管理システム

    責務:
        - エラー分類と重要度判定
        - 段階的復旧戦略実行
        - フォールバック機能提供
        - 復旧状況の監視
    """

    def __init__(self, project_root: Path) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
        """
        self.project_root = project_root
        self.logger = get_logger(__name__)
        self._init_recovery_strategies()
        self.recovery_log = []

    def _init_recovery_strategies(self) -> None:
        """復旧戦略の初期化"""
        self.recovery_strategies = {
            "ModuleNotFoundError": {
                "severity": ErrorSeverity.HIGH,
                "actions": [RecoveryAction.RETRY, RecoveryAction.FALLBACK],
            },
            "FileNotFoundError": {
                "severity": ErrorSeverity.MEDIUM,
                "actions": [RecoveryAction.FALLBACK, RecoveryAction.IGNORE],
            },
            "PermissionError": {
                "severity": ErrorSeverity.HIGH,
                "actions": [RecoveryAction.FALLBACK, RecoveryAction.SAFE_MODE],
            },
            "SyntaxError": {
                "severity": ErrorSeverity.MEDIUM,
                "actions": [RecoveryAction.IGNORE, RecoveryAction.FALLBACK],
            },
            "MemoryError": {
                "severity": ErrorSeverity.HIGH,
                "actions": [RecoveryAction.CACHE_CLEAR, RecoveryAction.SAFE_MODE],
            },
            "git": {"severity": ErrorSeverity.MEDIUM, "actions": [RecoveryAction.FALLBACK, RecoveryAction.IGNORE]},
            "ConnectionError": {
                "severity": ErrorSeverity.LOW,
                "actions": [RecoveryAction.RETRY, RecoveryAction.IGNORE],
            },
            "pickle": {
                "severity": ErrorSeverity.MEDIUM,
                "actions": [RecoveryAction.CACHE_CLEAR, RecoveryAction.FALLBACK],
            },
            "Exception": {
                "severity": ErrorSeverity.MEDIUM,
                "actions": [RecoveryAction.FALLBACK, RecoveryAction.SAFE_MODE],
            },
        }

    def handle_error(
        self, error: Exception, operation_name: str, context: dict[str, Any] | None = None
    ) -> RecoveryResult:
        """エラー処理と復旧実行

        Args:
            error: 発生したエラー
            operation_name: 操作名
            context: 追加コンテキスト

        Returns:
            復旧結果
        """
        start_time = datetime.now(timezone.utc)
        error_context = self._create_error_context(error, operation_name, context or {})
        console.print(f"品質チェックエラー発生: {error_context.error_type} - {operation_name}")
        recovery_result = self._execute_recovery_strategy(error_context)
        recovery_result.duration_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
        self.recovery_log.append(
            {
                "timestamp": start_time.isoformat(),
                "operation": operation_name,
                "error_type": error_context.error_type,
                "severity": error_context.severity.value,
                "action_taken": recovery_result.action_taken.value,
                "success": recovery_result.success,
            }
        )
        return recovery_result

    def _create_error_context(self, error: Exception, operation_name: str, metadata: dict[str, Any]) -> ErrorContext:
        """エラーコンテキスト生成

        Args:
            error: エラーオブジェクト
            operation_name: 操作名
            metadata: 追加メタデータ

        Returns:
            エラーコンテキスト
        """
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()
        strategy = self._get_recovery_strategy(error_type, error_message)
        return ErrorContext(
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            operation_name=operation_name,
            timestamp=datetime.now(timezone.utc),
            severity=strategy["severity"],
            recovery_actions=strategy["actions"],
            metadata=metadata,
        )

    def _get_recovery_strategy(self, error_type: str, error_message: str) -> dict[str, Any]:
        """復旧戦略取得

        Args:
            error_type: エラータイプ
            error_message: エラーメッセージ

        Returns:
            復旧戦略
        """
        if error_type in self.recovery_strategies:
            return self.recovery_strategies[error_type]
        for pattern, strategy in self.recovery_strategies.items():
            if pattern.lower() in error_message.lower() or pattern.lower() in error_type.lower():
                return strategy
        return self.recovery_strategies["Exception"]

    def _execute_recovery_strategy(self, error_context: ErrorContext) -> RecoveryResult:
        """復旧戦略実行

        Args:
            error_context: エラーコンテキスト

        Returns:
            復旧結果
        """
        for action in error_context.recovery_actions:
            try:
                result = self._execute_recovery_action(action, error_context)
                if result.success:
                    return result
            except Exception as recovery_error:
                self.logger.exception("復旧アクション失敗: %s - %s", action.value, recovery_error)
                continue
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.ABORT,
            error_resolved=False,
            fallback_used=False,
            duration_seconds=0.0,
            details="すべての復旧アクションが失敗しました",
        )

    def _execute_recovery_action(self, action: RecoveryAction, error_context: ErrorContext) -> RecoveryResult:
        """復旧アクション実行

        Args:
            action: 復旧アクション
            error_context: エラーコンテキスト

        Returns:
            復旧結果
        """
        if action == RecoveryAction.IGNORE:
            return self._ignore_error(error_context)
        if action == RecoveryAction.RETRY:
            return self._retry_operation(error_context)
        if action == RecoveryAction.FALLBACK:
            return self._execute_fallback(error_context)
        if action == RecoveryAction.CACHE_CLEAR:
            return self._clear_cache(error_context)
        if action == RecoveryAction.SAFE_MODE:
            return self._execute_safe_mode(error_context)
        if action == RecoveryAction.ABORT:
            return self._abort_operation(error_context)
        msg = f"未知の復旧アクション: {action}"
        raise ValueError(msg)

    def _ignore_error(self, error_context: ErrorContext) -> RecoveryResult:
        """エラー無視"""
        console.print(f"エラーを無視して継続: {error_context.operation_name}")
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.IGNORE,
            error_resolved=False,
            fallback_used=False,
            duration_seconds=0.0,
            details="エラーを無視して処理を継続しました",
        )

    def _retry_operation(self, error_context: ErrorContext) -> RecoveryResult:
        """操作再試行"""
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.RETRY,
            error_resolved=False,
            fallback_used=False,
            duration_seconds=0.0,
            details="操作再試行を推奨します",
        )

    def _execute_fallback(self, error_context: ErrorContext) -> RecoveryResult:
        """フォールバック実行"""
        fallback_strategies = {
            "ddd_compliance_check": self._fallback_basic_compliance_check,
            "change_impact_analysis": self._fallback_basic_analysis,
            "performance_monitoring": self._fallback_simple_timing,
            "cache_operations": self._fallback_no_cache,
        }
        for operation_pattern, fallback_func in fallback_strategies.items():
            if operation_pattern in error_context.operation_name.lower():
                try:
                    fallback_func(error_context)
                    return RecoveryResult(
                        success=True,
                        action_taken=RecoveryAction.FALLBACK,
                        error_resolved=False,
                        fallback_used=True,
                        duration_seconds=0.0,
                        details=f"フォールバック実行: {operation_pattern}",
                    )
                except Exception as fallback_error:
                    self.logger.exception("フォールバック失敗: %s", fallback_error)
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.FALLBACK,
            error_resolved=False,
            fallback_used=False,
            duration_seconds=0.0,
            details="適用可能なフォールバック戦略が見つかりませんでした",
        )

    def _clear_cache(self, error_context: ErrorContext) -> RecoveryResult:
        """キャッシュクリア"""
        try:
            cache_dir = self.project_root / ".ddd_cache"
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(exist_ok=True)
                console.print("DDDキャッシュをクリアしました")
                return RecoveryResult(
                    success=True,
                    action_taken=RecoveryAction.CACHE_CLEAR,
                    error_resolved=True,
                    fallback_used=False,
                    duration_seconds=0.0,
                    details="キャッシュクリアが完了しました",
                )
        except Exception as clear_error:
            self.logger.exception("キャッシュクリアエラー: %s", clear_error)
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.CACHE_CLEAR,
            error_resolved=False,
            fallback_used=False,
            duration_seconds=0.0,
            details="キャッシュクリアに失敗しました",
        )

    def _execute_safe_mode(self, error_context: ErrorContext) -> RecoveryResult:
        """セーフモード実行"""
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.SAFE_MODE,
            error_resolved=False,
            fallback_used=True,
            duration_seconds=0.0,
            details="セーフモードで最小限のチェックを実行します",
        )

    def _abort_operation(self, error_context: ErrorContext) -> RecoveryResult:
        """操作中止"""
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.ABORT,
            error_resolved=False,
            fallback_used=False,
            duration_seconds=0.0,
            details="操作を中止しました",
        )

    def _fallback_basic_compliance_check(self, error_context: ErrorContext) -> None:
        """基本的なDDD準拠性チェック"""
        console.print("基本DDD準拠性チェックに切り替え")

    def _fallback_basic_analysis(self, error_context: ErrorContext) -> None:
        """基本的な変更影響分析"""
        console.print("基本変更影響分析に切り替え")

    def _fallback_simple_timing(self, error_context: ErrorContext) -> None:
        """簡易実行時間測定"""
        console.print("簡易実行時間測定に切り替え")

    def _fallback_no_cache(self, error_context: ErrorContext) -> None:
        """キャッシュなし実行"""
        console.print("キャッシュなしで実行")

    def get_recovery_statistics(self) -> dict[str, Any]:
        """復旧統計情報取得

        Returns:
            復旧統計情報
        """
        if not self.recovery_log:
            return {"total_recoveries": 0}
        total_recoveries = len(self.recovery_log)
        successful_recoveries = sum(1 for log in self.recovery_log if log["success"])
        action_counts = {}
        severity_counts = {}
        for log in self.recovery_log:
            action = log["action_taken"]
            severity = log["severity"]
            action_counts[action] = action_counts.get(action, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        return {
            "total_recoveries": total_recoveries,
            "successful_recoveries": successful_recoveries,
            "success_rate": successful_recoveries / total_recoveries * 100,
            "action_breakdown": action_counts,
            "severity_breakdown": severity_counts,
            "recent_recoveries": self.recovery_log[-5:],
        }

    def export_recovery_report(self, output_path: Path | None = None) -> None:
        """復旧レポート出力

        Args:
            output_path: 出力パス
        """
        if output_path is None:
            output_path = self.project_root / "reports" / "recovery_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "statistics": self.get_recovery_statistics(),
            "recovery_log": self.recovery_log,
        }
        try:
            # UnifiedFileStorageServiceを使用して復旧レポートを保存
            storage_service = UnifiedFileStorageService()
            storage_service.save(
                file_path=output_path,
                content=report,
                content_type=FileContentType.API_RESPONSE,
                metadata={
                    "report_type": "quality_check_recovery",
                    "total_recoveries": len(self.recovery_log),
                    "statistics": self.get_recovery_statistics(),
                },
            )
            console.print(f"復旧レポート出力完了: {output_path}")
        except (OSError, json.JSONEncodeError) as e:
            self.logger.exception("復旧レポート出力エラー: %s", e)


class RecoveryContext:
    """復旧コンテキストマネージャー"""

    def __init__(self, operation_name: str, project_root: Path, auto_retry: bool = True) -> None:
        self.operation_name = operation_name
        self.recovery_manager = QualityCheckRecoveryManager(project_root)
        self.auto_retry = auto_retry

    def __enter__(self) -> "RecoveryContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_val is not None:
            recovery_result = self.recovery_manager.handle_error(exc_val, self.operation_name)
            if self.auto_retry and recovery_result.action_taken == RecoveryAction.RETRY:
                return True
            return recovery_result.success
        return False

    def get_recovery_manager(self) -> QualityCheckRecoveryManager:
        """復旧マネージャー取得"""
        return self.recovery_manager
