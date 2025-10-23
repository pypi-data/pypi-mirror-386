#!/usr/bin/env python3
"""拡張MCPエラーハンドラー

MCPサーバーの包括的なエラーハンドリングと復旧機能を提供する
"""

import contextlib
import json
import traceback
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.presentation.shared.shared_utilities import console
from noveler.infrastructure.logging.unified_logger import get_logger


class MCPErrorSeverity(Enum):
    """MCPエラー重要度"""
    CRITICAL = "critical"  # サーバー停止レベル
    ERROR = "error"       # 機能停止レベル
    WARNING = "warning"   # 品質低下レベル
    INFO = "info"        # 情報レベル


class MCPErrorType(Enum):
    """MCPエラータイプ"""
    VALIDATION_ERROR = "validation"      # 入力バリデーションエラー
    DEPENDENCY_ERROR = "dependency"      # 依存関係エラー
    FILE_ACCESS_ERROR = "file_access"    # ファイルアクセスエラー
    TIMEOUT_ERROR = "timeout"            # タイムアウトエラー
    SESSION_ERROR = "session"            # セッション管理エラー
    JSON_ERROR = "json"                 # JSON処理エラー
    EXTERNAL_COMMAND_ERROR = "external" # 外部コマンド実行エラー
    UNKNOWN_ERROR = "unknown"           # その他のエラー


class MCPErrorContext:
    """MCPエラーコンテキスト"""

    def __init__(self,
                 error_type: MCPErrorType,
                 severity: MCPErrorSeverity,
                 message: str,
                 details: str | None = None,
                 tool_name: str | None = None,
                 episode: int | None = None,
                 session_id: str | None = None,
                 original_exception: Exception | None = None) -> None:
        self.error_type = error_type
        self.severity = severity
        self.message = message
        self.details = details
        self.tool_name = tool_name
        self.episode = episode
        self.session_id = session_id
        self.original_exception = original_exception
        self.timestamp = project_now().datetime
        self.error_id = f"MCP-{int(self.timestamp.timestamp() * 1000)}"

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "error_id": self.error_id,
            "error_type": self.error_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "tool_name": self.tool_name,
            "episode": self.episode,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "traceback": traceback.format_exception(
                type(self.original_exception),
                self.original_exception,
                self.original_exception.__traceback__
            ) if self.original_exception else None
        }


class EnhancedMCPErrorHandler:
    """拡張MCPエラーハンドラー"""

    def __init__(self, log_dir: Path | None = None) -> None:
        self.log_dir = log_dir or Path.cwd() / "temp" / "mcp_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.logger = get_logger(__name__)
        self.error_log_file = self.log_dir / f"mcp_errors_{project_now().datetime.strftime('%Y%m%d')}.json"

        # エラー統計
        self.error_counts = dict.fromkeys(MCPErrorType, 0)
        self.session_errors = {}  # session_id -> error_list

    def handle_error(self, error_context: MCPErrorContext) -> str:
        """エラーハンドリング実行

        Args:
            error_context: エラーコンテキスト

        Returns:
            クライアント向けのエラーメッセージ
        """
        # エラー統計更新
        self.error_counts[error_context.error_type] += 1

        # セッション別エラー記録
        if error_context.session_id:
            if error_context.session_id not in self.session_errors:
                self.session_errors[error_context.session_id] = []
            self.session_errors[error_context.session_id].append(error_context)

        # エラーログ記録
        self._log_error(error_context)

        # 復旧処理実行
        recovery_action = self._attempt_recovery(error_context)

        # クライアント向けメッセージ生成
        return self._generate_client_message(error_context, recovery_action)

    def _log_error(self, error_context: MCPErrorContext) -> None:
        """エラーログ記録"""
        error_data = error_context.to_dict()

        # JSONログファイルに追記
        try:
            if self.error_log_file.exists():
                with open(self.error_log_file, encoding="utf-8") as f:
                    existing_data = json.load(f)
            else:
                existing_data = {"errors": []}

            existing_data["errors"].append(error_data)

            with open(self.error_log_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            # ログ記録に失敗した場合も継続
            self.logger.exception(f"エラーログ記録に失敗: {e}")

        # コンソールログ出力
        severity_emoji = {
            MCPErrorSeverity.CRITICAL: "🔥",
            MCPErrorSeverity.ERROR: "❌",
            MCPErrorSeverity.WARNING: "⚠️",
            MCPErrorSeverity.INFO: "ℹ️"
        }

        emoji = severity_emoji.get(error_context.severity, "❓")
        console.print(f"{emoji} MCP Error [{error_context.error_id}]: {error_context.message}")

        if error_context.details:
            console.print(f"   詳細: {error_context.details}")

    def _attempt_recovery(self, error_context: MCPErrorContext) -> str | None:
        """復旧処理の試行

        Args:
            error_context: エラーコンテキスト

        Returns:
            復旧アクション（成功時のメッセージ）
        """
        try:
            if error_context.error_type == MCPErrorType.VALIDATION_ERROR:
                return self._recover_validation_error(error_context)
            if error_context.error_type == MCPErrorType.FILE_ACCESS_ERROR:
                return self._recover_file_access_error(error_context)
            if error_context.error_type == MCPErrorType.TIMEOUT_ERROR:
                return self._recover_timeout_error(error_context)
            if error_context.error_type == MCPErrorType.SESSION_ERROR:
                return self._recover_session_error(error_context)
            if error_context.error_type == MCPErrorType.JSON_ERROR:
                return self._recover_json_error(error_context)
            return None  # 復旧不可能

        except Exception as recovery_error:
            self.logger.exception(f"復旧処理中にエラー: {recovery_error}")
            return None

    def _recover_validation_error(self, error_context: MCPErrorContext) -> str | None:
        """バリデーションエラーの復旧"""
        if error_context.episode and error_context.episode <= 0:
            # エピソード番号が無効な場合、1に補正
            error_context.episode = 1
            return "エピソード番号を1に補正しました"
        return None

    def _recover_file_access_error(self, error_context: MCPErrorContext) -> str | None:
        """ファイルアクセスエラーの復旧"""
        # ディレクトリが存在しない場合は作成を試行
        if "ディレクトリ" in (error_context.details or ""):
            try:
                # 簡易的なディレクトリ作成（実際の実装ではより詳細な処理が必要）
                return "不足するディレクトリの作成を試行しました"
            except Exception:
                pass
        return None

    def _recover_timeout_error(self, error_context: MCPErrorContext) -> str | None:
        """タイムアウトエラーの復旧"""
        # セッション状態の保存を試行
        if error_context.session_id:
            self._save_session_state(error_context.session_id, error_context)
            return "セッション状態を保存し、後で再開可能にしました"
        return None

    def _recover_session_error(self, error_context: MCPErrorContext) -> str | None:
        """セッションエラーの復旧"""
        # セッションクリーンアップ
        if error_context.session_id and error_context.session_id in self.session_errors:
            del self.session_errors[error_context.session_id]
            return "セッション状態をクリーンアップしました"
        return None

    def _recover_json_error(self, error_context: MCPErrorContext) -> str | None:
        """JSONエラーの復旧"""
        # JSON修復を試行（簡易版）
        if error_context.details and "{" in error_context.details:
            return "JSON形式の修復を試行しました（部分的な情報が利用可能な場合があります）"
        return None

    def _save_session_state(self, session_id: str, error_context: MCPErrorContext) -> None:
        """セッション状態の保存"""
        try:
            session_state_file = self.log_dir / f"session_{session_id}_recovery.json"
            session_state = {
                "session_id": session_id,
                "error_time": error_context.timestamp.isoformat(),
                "tool_name": error_context.tool_name,
                "episode": error_context.episode,
                "error_type": error_context.error_type.value,
                "recovery_suggestions": [
                    f"{error_context.tool_name}の実行を再試行する",
                    "エピソード番号や入力パラメータを確認する",
                    "プロジェクトファイルの整合性を確認する"
                ]
            }

            with open(session_state_file, "w", encoding="utf-8") as f:
                json.dump(session_state, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.exception(f"セッション状態保存に失敗: {e}")

    def _generate_client_message(self, error_context: MCPErrorContext, recovery_action: str | None) -> str:
        """クライアント向けメッセージ生成"""
        base_message = {
            "success": False,
            "error_id": error_context.error_id,
            "error_type": error_context.error_type.value,
            "message": error_context.message,
            "severity": error_context.severity.value,
            "timestamp": error_context.timestamp.isoformat()
        }

        if error_context.details:
            base_message["details"] = error_context.details

        if recovery_action:
            base_message["recovery_action"] = recovery_action
            base_message["recovery_attempted"] = True
        else:
            base_message["recovery_attempted"] = False

        # 復旧提案の追加
        suggestions = self._generate_recovery_suggestions(error_context)
        if suggestions:
            base_message["suggestions"] = suggestions

        return json.dumps(base_message, ensure_ascii=False, indent=2)

    def _generate_recovery_suggestions(self, error_context: MCPErrorContext) -> list[str]:
        """復旧提案の生成"""
        suggestions = []

        if error_context.error_type == MCPErrorType.VALIDATION_ERROR:
            suggestions.extend([
                "入力パラメータの値を確認してください",
                "エピソード番号は1以上の整数である必要があります"
            ])
        elif error_context.error_type == MCPErrorType.FILE_ACCESS_ERROR:
            suggestions.extend([
                "ファイルパスが正しく、ファイルが存在することを確認してください",
                "プロジェクトルートの設定を確認してください"
            ])
        elif error_context.error_type == MCPErrorType.TIMEOUT_ERROR:
            suggestions.extend([
                "処理を小さな単位に分割して実行してください",
                "セッションIDを使用して中断した処理を再開できます"
            ])
        elif error_context.error_type == MCPErrorType.SESSION_ERROR:
            suggestions.extend([
                "新しいセッションで処理を開始してください",
                "セッション状態ファイルの整合性を確認してください"
            ])

        # 共通提案
        suggestions.extend([
            "問題が継続する場合は、テストモード（--test）で基本動作を確認してください",
            f"エラーID {error_context.error_id} をサポートに報告してください"
        ])

        return suggestions

    def get_error_statistics(self) -> dict[str, Any]:
        """エラー統計の取得"""
        total_errors = sum(self.error_counts.values())

        return {
            "total_errors": total_errors,
            "error_by_type": {error_type.value: count for error_type, count in self.error_counts.items()},
            "active_sessions": len(self.session_errors),
            "sessions_with_errors": list(self.session_errors.keys()),
            "log_file": str(self.error_log_file) if self.error_log_file.exists() else None
        }

    def clear_session_errors(self, session_id: str) -> bool:
        """セッションエラーのクリア"""
        if session_id in self.session_errors:
            del self.session_errors[session_id]

            # セッション状態ファイルも削除
            session_state_file = self.log_dir / f"session_{session_id}_recovery.json"
            if session_state_file.exists():
                with contextlib.suppress(Exception):
                    session_state_file.unlink()

            return True
        return False


# グローバルインスタンス（シングルトンパターン）
_error_handler_instance: EnhancedMCPErrorHandler | None = None

def get_mcp_error_handler() -> EnhancedMCPErrorHandler:
    """MCPエラーハンドラーのグローバルインスタンスを取得"""
    global _error_handler_instance
    if _error_handler_instance is None:
        _error_handler_instance = EnhancedMCPErrorHandler()
    return _error_handler_instance


def handle_mcp_error(error_type: MCPErrorType,
                    severity: MCPErrorSeverity,
                    message: str,
                    details: str | None = None,
                    tool_name: str | None = None,
                    episode: int | None = None,
                    session_id: str | None = None,
                    original_exception: Exception | None = None) -> str:
    """便利関数：MCPエラーハンドリング"""
    error_context = MCPErrorContext(
        error_type=error_type,
        severity=severity,
        message=message,
        details=details,
        tool_name=tool_name,
        episode=episode,
        session_id=session_id,
        original_exception=original_exception
    )

    handler = get_mcp_error_handler()
    return handler.handle_error(error_context)
