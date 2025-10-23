#!/usr/bin/env python3

"""Domain.interfaces.logger_service
Where: Domain interface defining logging service expectations.
What: Declares operations for structured logging within the domain.
Why: Enables logging abstractions decoupled from infrastructure choices.
"""

from __future__ import annotations

"""ロガーサービスインターフェース

DDD準拠: ドメイン層のインターフェース定義
アプリケーション層はこのインターフェース経由でログ出力を行う
"""


from typing import Any, Protocol


class ILoggerService(Protocol):
    """ロガーサービスインターフェース

    ドメイン層で定義し、インフラ層で実装する。
    これによりドメイン層がインフラ層のロギング実装に依存することを防ぐ。
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


class NullLoggerService:
    """ログ出力を行わないNullObjectパターンのロガー

    テストや初期化時に使用する
    """

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """何もしない"""

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """何もしない"""

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """何もしない"""

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """何もしない"""

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """何もしない"""

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """何もしない"""

    def set_level(self, level: str) -> None:
        """何もしない"""

    def get_level(self) -> str:
        """常にINFOを返す"""
        return "INFO"

    def add_context(self, **context: Any) -> None:
        """何もしない"""

    def clear_context(self) -> None:
        """何もしない"""
