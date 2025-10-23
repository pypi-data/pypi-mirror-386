"""ロガーサービスProtocol定義

循環依存回避のための純粋なProtocol定義。
importは最小限とし、型定義のみに集中する。
"""

from typing import Any, Protocol


class ILoggerProtocol(Protocol):
    """ロガーサービスProtocol

    循環依存を回避するための純粋なProtocol定義。
    実装の詳細に依存しない構造的サブタイピングを提供する。
    """

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """デバッグレベルのログを出力

        Args:
            message: ログメッセージ
            *args: フォーマット引数
            **kwargs: 追加パラメータ
        """
        ...

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """情報レベルのログを出力

        Args:
            message: ログメッセージ
            *args: フォーマット引数
            **kwargs: 追加パラメータ
        """
        ...

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """警告レベルのログを出力

        Args:
            message: ログメッセージ
            *args: フォーマット引数
            **kwargs: 追加パラメータ
        """
        ...

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """エラーレベルのログを出力

        Args:
            message: ログメッセージ
            *args: フォーマット引数
            **kwargs: 追加パラメータ
        """
        ...

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """致命的エラーレベルのログを出力

        Args:
            message: ログメッセージ
            *args: フォーマット引数
            **kwargs: 追加パラメータ
        """
        ...

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """例外情報付きのエラーログを出力

        Args:
            message: ログメッセージ
            *args: フォーマット引数
            **kwargs: 追加パラメータ
        """
        ...

    def set_level(self, level: str) -> None:
        """ログレベルを設定

        Args:
            level: ログレベル（DEBUG/INFO/WARNING/ERROR/CRITICAL）
        """
        ...

    def get_level(self) -> str:
        """現在のログレベルを取得

        Returns:
            現在のログレベル
        """
        ...

    def add_context(self, **context: Any) -> None:
        """ログコンテキストを追加

        Args:
            **context: コンテキスト情報
        """
        ...

    def clear_context(self) -> None:
        """ログコンテキストをクリア"""
        ...
