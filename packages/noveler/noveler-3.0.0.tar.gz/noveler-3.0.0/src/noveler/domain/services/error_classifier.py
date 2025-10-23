"""
エラー分類サービス（Functional Core）
SPEC-ERR-001: 統一エラーハンドリングシステム

純粋関数として実装し、副作用を持たない
"""

from enum import Enum
from typing import Any


class ErrorLevel(Enum):
    """エラーレベル定義"""
    CRITICAL = "critical"  # システム停止が必要
    ERROR = "error"        # 処理失敗
    WARNING = "warning"    # 警告
    INFO = "info"         # 情報


class ErrorClassifier:
    """
    エラー分類純粋関数クラス

    Functional Core原則:
    - 副作用なし
    - 決定論的（同じ入力→同じ出力）
    - 外部依存なし
    """

    @staticmethod
    def classify(error: Exception) -> ErrorLevel:
        """
        エラーを分類する純粋関数

        Args:
            error: 分類対象のエラー

        Returns:
            ErrorLevel: エラーレベル
        """
        # エラータイプによる分類マッピング（決定論的）
        error_type = type(error).__name__

        # Critical errors
        if isinstance(error, SystemError | MemoryError | RecursionError):
            return ErrorLevel.CRITICAL

        # Domain/Application errors
        if error_type in ("DomainError", "ApplicationError", "ValueError", "RuntimeError"):
            return ErrorLevel.ERROR

        # Warnings
        if isinstance(error, UserWarning | DeprecationWarning | Warning):
            return ErrorLevel.WARNING

        # Info level
        if error_type in ("InfoException", "NotificationError"):
            return ErrorLevel.INFO

        # Default
        return ErrorLevel.ERROR

    @staticmethod
    def extract_context(error: Exception) -> dict[str, Any]:
        """
        エラーからコンテキスト情報を抽出する純粋関数

        Args:
            error: コンテキスト抽出対象のエラー

        Returns:
            Dict[str, Any]: エラーコンテキスト（副作用なし）
        """
        return {
            "error_type": type(error).__name__,
            "message": str(error),
            "attributes": {
                attr: getattr(error, attr)
                for attr in dir(error)
                if not attr.startswith("_") and not callable(getattr(error, attr))
            }
        }

    @staticmethod
    def is_pure_function() -> bool:
        """
        このクラスが純粋関数であることを示すマーカー

        Returns:
            bool: 常にTrue（Functional Core契約）
        """
        return True

    @staticmethod
    def get_user_friendly_message(error: Exception, level: ErrorLevel) -> str:
        """
        ユーザー向けメッセージを生成する純粋関数

        Args:
            error: エラーオブジェクト
            level: エラーレベル

        Returns:
            str: ユーザー向けメッセージ
        """
        if level == ErrorLevel.CRITICAL:
            return "システムエラーが発生しました。管理者に連絡してください。"
        if level == ErrorLevel.ERROR:
            return "処理中にエラーが発生しました。"
        if level == ErrorLevel.WARNING:
            return "警告: 処理は続行されますが、確認が必要です。"
        return "情報: 処理に関する通知があります。"

    @staticmethod
    def should_notify_user(level: ErrorLevel) -> bool:
        """
        ユーザー通知が必要かを判定する純粋関数

        Args:
            level: エラーレベル

        Returns:
            bool: 通知が必要な場合True
        """
        return level in (ErrorLevel.CRITICAL, ErrorLevel.ERROR, ErrorLevel.WARNING)
