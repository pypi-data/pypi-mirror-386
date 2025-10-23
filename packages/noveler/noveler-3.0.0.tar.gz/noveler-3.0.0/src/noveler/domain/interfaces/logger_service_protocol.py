#!/usr/bin/env python3
"""Logger Service Protocol - Domain Interface

SPEC-ARCH-002に基づくDomain層ログサービスインターフェース。
FC/IS（Functional Core / Imperative Shell）アーキテクチャにおいて、
Domain層が外部ログシステムに依存せずにログ出力を行うためのプロトコル定義。
"""

from typing import Any, Protocol


class ILoggerService(Protocol):
    """ログサービスインターフェース - Domain層契約

    FC/ISパターンにおいて、Domain層がログ機能を使用する際の契約。
    実装はInfrastructure層で提供され、Dependency Injectionで注入される。
    """

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """デバッグレベルログ出力

        Args:
            message: ログメッセージ
            *args: フォーマット引数
            **kwargs: 追加パラメータ
        """
        ...

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """情報レベルログ出力

        Args:
            message: ログメッセージ
            *args: フォーマット引数
            **kwargs: 追加パラメータ
        """
        ...

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """警告レベルログ出力

        Args:
            message: ログメッセージ
            *args: フォーマット引数
            **kwargs: 追加パラメータ
        """
        ...

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """エラーレベルログ出力

        Args:
            message: ログメッセージ
            *args: フォーマット引数
            **kwargs: 追加パラメータ
        """
        ...

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """重大エラーレベルログ出力

        Args:
            message: ログメッセージ
            *args: フォーマット引数
            **kwargs: 追加パラメータ
        """
        ...
