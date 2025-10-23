#!/usr/bin/env python3
"""ロガーインターフェース

DDD準拠: ドメイン層のロガーインターフェース定義
インフラ層への依存を排除し、依存性注入で実装を提供
"""

from typing import Any, Protocol


class ILogger(Protocol):
    """ドメイン層用ロガーインターフェース

    ドメイン層で定義し、インフラ層で実装する。
    これによりドメイン層がインフラ層のロギング実装に依存することを防ぐ。
    """

    def debug(self, message: str, **kwargs: Any) -> None:
        """デバッグレベルのログ出力

        Args:
            message: ログメッセージ
            **kwargs: 追加のコンテキスト情報
        """
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """情報レベルのログ出力

        Args:
            message: ログメッセージ
            **kwargs: 追加のコンテキスト情報
        """
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """警告レベルのログ出力

        Args:
            message: ログメッセージ
            **kwargs: 追加のコンテキスト情報
        """
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """エラーレベルのログ出力

        Args:
            message: ログメッセージ
            **kwargs: 追加のコンテキスト情報
        """
        ...

    def critical(self, message: str, **kwargs: Any) -> None:
        """クリティカルレベルのログ出力

        Args:
            message: ログメッセージ
            **kwargs: 追加のコンテキスト情報
        """
        ...

    def exception(self, message: str, **kwargs: Any) -> None:
        """例外情報を含むログ出力"""
        ...


class NullLogger:
    """ログ出力を行わないダミー実装

    テストやロギング不要な環境用のNullオブジェクトパターン実装
    """

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """何もしない"""
        return None

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """何もしない"""
        return None

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """何もしない"""
        return None

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """何もしない"""
        return None

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """何もしない"""
        return None

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        """何もしない"""
        return None
