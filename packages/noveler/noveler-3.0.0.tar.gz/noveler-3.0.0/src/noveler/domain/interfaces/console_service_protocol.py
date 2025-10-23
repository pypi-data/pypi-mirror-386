#!/usr/bin/env python3
"""Console Service Protocol - Domain Interface

SPEC-ARCH-002に基づくDomain層コンソール出力サービスインターフェース。
FC/IS（Functional Core / Imperative Shell）アーキテクチャにおいて、
Domain層が外部コンソールシステムに依存せずに出力を行うためのプロトコル定義。
"""

from typing import Protocol


class IConsoleService(Protocol):
    """コンソール出力サービスの抽象インターフェース

    Application層がPresentation層のconsoleに直接依存しないよう
    依存性逆転の原則を適用するためのプロトコル。
    FC/ISパターンにおけるImperative Shell側で実装。
    """

    def print(self, message: str, style: str = "") -> None:
        """メッセージ出力

        Args:
            message: 出力メッセージ
            style: スタイル指定（例：'[blue]', '[green]'など）
        """
        ...

    def print_info(self, message: str) -> None:
        """情報メッセージ出力

        Args:
            message: 出力メッセージ
        """
        ...

    def print_success(self, message: str) -> None:
        """成功メッセージ出力

        Args:
            message: 出力メッセージ
        """
        ...

    def print_warning(self, message: str) -> None:
        """警告メッセージ出力

        Args:
            message: 出力メッセージ
        """
        ...

    def print_error(self, message: str) -> None:
        """エラーメッセージ出力

        Args:
            message: 出力メッセージ
        """
        ...

    def print_debug(self, message: str) -> None:
        """デバッグメッセージ出力

        Args:
            message: 出力メッセージ
        """
        ...
