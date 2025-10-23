"""コンソール出力サービスProtocol定義

循環依存回避のための純粋なProtocol定義。
プレゼンテーション層への依存を回避する。
"""

from typing import Protocol


class IConsoleServiceProtocol(Protocol):
    """コンソール出力サービスProtocol

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
