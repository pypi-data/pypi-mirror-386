"""Unit of Work Protocol定義

循環依存回避のための純粋なProtocol定義。
インフラ層型への依存を避け、必要最小限の契約のみを提示する。
"""

from typing import Any, Protocol


class IUnitOfWorkProtocol(Protocol):
    """Unit of Work Protocol

    トランザクション管理とリポジトリアクセスの統一インターフェース。
    循環依存を避けるためTYPE_CHECKINGで型ヒントを分離。
    """

    episode_repository: Any
    project_repository: Any
    character_repository: Any | None
    configuration_repository: Any | None
    plot_repository: Any | None
    backup_repository: Any | None

    def __enter__(self) -> "IUnitOfWorkProtocol":
        """コンテキストマネージャー開始

        Returns:
            自身のインスタンス
        """
        ...

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """コンテキストマネージャー終了

        Args:
            exc_type: 例外の型
            exc_val: 例外の値
            exc_tb: 例外のトレースバック
        """
        ...

    def commit(self) -> None:
        """変更をコミット"""
        ...

    def rollback(self) -> None:
        """変更をロールバック"""
        ...
