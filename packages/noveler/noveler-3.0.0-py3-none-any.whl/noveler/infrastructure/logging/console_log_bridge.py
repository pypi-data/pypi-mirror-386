#!/usr/bin/env python3
"""Console・ログ統合ブリッジ

console.print()とLogging Frameworkを統合したハイブリッドシステム
B30品質ガイドライン準拠・console統一の拡張機能
"""

from enum import Enum
from typing import Any

from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.presentation.shared.shared_utilities import console


class ConsoleLogLevel(Enum):
    """コンソール・ログレベル統合定義"""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class ConsoleLogBridge:
    """Console出力とログ出力を統合するブリッジクラス

    責務:
        - console.print()とlogger出力の統一インターフェース
        - レベル別の色分け・フォーマット統一
        - 開発時とプロダクション時の出力制御統一
    """

    def __init__(self, logger_name: str) -> None:
        """初期化

        Args:
            logger_name: ロガー名（通常は__name__）
        """
        self.logger = get_logger(logger_name)

    def print_info(self, message: str, **kwargs: Any) -> None:
        """INFO レベル出力（console + log）

        Args:
            message: 出力メッセージ
            **kwargs: 追加データ
        """
        console.print(f"[blue]ℹ️  {message}[/blue]")
        self.logger.info(message, extra=kwargs if kwargs else None)

    def print_success(self, message: str, **kwargs: Any) -> None:
        """SUCCESS レベル出力（console + log）

        Args:
            message: 出力メッセージ
            **kwargs: 追加データ
        """
        console.print(f"[green]✅ {message}[/green]")
        self.logger.info(f"SUCCESS: {message}", extra=kwargs if kwargs else None)

    def print_warning(self, message: str, **kwargs: Any) -> None:
        """WARNING レベル出力（console + log）

        Args:
            message: 出力メッセージ
            **kwargs: 追加データ
        """
        console.print(f"[yellow]⚠️  {message}[/yellow]")
        self.logger.warning(message, extra=kwargs if kwargs else None)

    def print_error(self, message: str, **kwargs: Any) -> None:
        """ERROR レベル出力（console + log）

        Args:
            message: 出力メッセージ
            **kwargs: 追加データ
        """
        console.print(f"[red]❌ {message}[/red]")
        self.logger.error(message, extra=kwargs if kwargs else None)

    def print_debug(self, message: str, **kwargs: Any) -> None:
        """DEBUG レベル出力（console + log）

        Args:
            message: 出力メッセージ
            **kwargs: 追加データ
        """
        console.print(f"[dim]🔍 {message}[/dim]")
        self.logger.debug(message, extra=kwargs if kwargs else None)

    def print_plain(self, message: str) -> None:
        """プレーン出力（consoleのみ・ログなし）

        Args:
            message: 出力メッセージ
        """
        console.print(message)


def get_console_log_bridge(logger_name: str) -> ConsoleLogBridge:
    """ConsoleLogBridge取得の便利関数

    Args:
        logger_name: ロガー名（通常は__name__）

    Returns:
        ConsoleLogBridge: 統合出力インスタンス

    Example:
        ```python
        from noveler.infrastructure.logging.console_log_bridge import get_console_log_bridge

        bridge = get_console_log_bridge(__name__)
        bridge.print_info("処理開始")
        bridge.print_success("変換完了")
        bridge.print_warning("未テストファイルがあります")
        bridge.print_error("処理に失敗しました")
        ```
    """
    return ConsoleLogBridge(logger_name)
