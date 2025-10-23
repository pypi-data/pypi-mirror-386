#!/usr/bin/env python3
"""統合コンソールマネージャー

console.print() + Logging Framework + ConsoleLogBridge の統合管理
開発者体験を最大化するワンストップインターフェース
"""

from typing import Any

from noveler.infrastructure.logging.console_log_bridge import get_console_log_bridge
from noveler.infrastructure.logging.unified_logger import configure_logging, get_logger
from noveler.presentation.shared.shared_utilities import console


class IntegratedConsole:
    """統合コンソール管理クラス

    責務:
        - console.print()のワンストップアクセス提供
        - ConsoleLogBridge統合ラッパー
        - 開発・プロダクション環境での出力制御統一
        - B30品質ガイドライン完全準拠
    """

    def __init__(self, logger_name: str = __name__) -> None:
        """初期化

        Args:
            logger_name: ロガー名（通常は__name__）
        """
        self.logger = get_logger(logger_name)
        self.bridge = get_console_log_bridge(logger_name)

        # ===========================================
        # プレーン出力（ログなし）
        # ===========================================

    def print(self, *args: Any, **kwargs: Any) -> None:
        """プレーン出力（console.print()のパススルー）

        Args:
            *args: console.print()の引数
            **kwargs: console.print()のキーワード引数
        """
        console.print(*args, **kwargs)

    def rule(self, title: str = "", **kwargs: Any) -> None:
        """区切り線出力

        Args:
            title: 区切り線のタイトル
            **kwargs: console.rule()のキーワード引数
        """
        console.rule(title, **kwargs)

    # ===========================================
    # レベル付き出力（console + log統合）
    # ===========================================

    def info(self, message: str, **kwargs: Any) -> None:
        """INFO レベル出力

        Args:
            message: 出力メッセージ
            **kwargs: 追加データ
        """
        self.bridge.print_info(message, **kwargs)

    def success(self, message: str, **kwargs: Any) -> None:
        """SUCCESS レベル出力

        Args:
            message: 出力メッセージ
            **kwargs: 追加データ
        """
        self.bridge.print_success(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """WARNING レベル出力

        Args:
            message: 出力メッセージ
            **kwargs: 追加データ
        """
        self.bridge.print_warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """ERROR レベル出力

        Args:
            message: 出力メッセージ
            **kwargs: 追加データ
        """
        self.bridge.print_error(message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """DEBUG レベル出力

        Args:
            message: 出力メッセージ
            **kwargs: 追加データ
        """
        self.bridge.print_debug(message, **kwargs)

    # ===========================================
    # 便利メソッド
    # ===========================================

    def header(self, title: str, style: str = "bold blue") -> None:
        """ヘッダー出力

        Args:
            title: ヘッダータイトル
            style: Rich形式のスタイル
        """
        console.rule(title, style=style)
        self.logger.info(f"=== {title} ===")

    def section(self, title: str) -> None:
        """セクション出力

        Args:
            title: セクションタイトル
        """
        console.print(f"\n[bold]{title}[/bold]")
        self.logger.info(f"--- {title} ---")

    def progress_start(self, message: str, **kwargs: Any) -> None:
        """進行状況開始

        Args:
            message: 開始メッセージ
            **kwargs: 追加データ
        """
        console.print(f"[blue]🔄 {message}[/blue]")
        self.logger.info(f"START: {message}", extra=kwargs if kwargs else None)

    def progress_complete(self, message: str, **kwargs: Any) -> None:
        """進行状況完了

        Args:
            message: 完了メッセージ
            **kwargs: 追加データ
        """
        console.print(f"[green]✅ {message}[/green]")
        self.logger.info(f"COMPLETE: {message}", extra=kwargs if kwargs else None)

    def progress_fail(self, message: str, **kwargs: Any) -> None:
        """進行状況失敗

        Args:
            message: 失敗メッセージ
            **kwargs: 追加データ
        """
        console.print(f"[red]❌ {message}[/red]")
        self.logger.error(f"FAIL: {message}", extra=kwargs if kwargs else None)


# ===========================================
# グローバル便利関数
# ===========================================


def get_integrated_console(logger_name: str = __name__) -> IntegratedConsole:
    """統合コンソール取得の便利関数

    Args:
        logger_name: ロガー名（通常は__name__）

    Returns:
        IntegratedConsole: 統合コンソールインスタンス

    Example:
        ```python
        from noveler.infrastructure.logging.integrated_console import get_integrated_console

        ic = get_integrated_console(__name__)
        ic.header("Phase 3: Logging Framework実装")
        ic.info("処理を開始します")
        ic.progress_start("ファイル変換中")
        ic.success("5個のファイルを変換しました")
        ic.progress_complete("全ての変換が完了しました")
        ```
    """
    return IntegratedConsole(logger_name)


def setup_integrated_logging(**kwargs: Any) -> None:
    """統合ログ設定の便利関数

    Args:
        **kwargs: ログ設定オプション

    Example:
        ```python
        # verboseモード設定
        setup_integrated_logging(verbose=2)

        # quietモード設定
        setup_integrated_logging(quiet=True)
        ```
    """
    configure_logging(**kwargs)
