"""インフラストラクチャ設定の永続化インターフェース"""

from abc import ABC, abstractmethod
from typing import Any


class InfrastructureConfigurationRepository(ABC):
    """インフラストラクチャ設定の永続化を行うリポジトリインターフェース

    設定ファイルの読み書きを抽象化し、具体的な実装(YAML、JSON等)から
    ドメイン層を独立させる。
    """

    @abstractmethod
    def load(self, file_path: str) -> dict[str, Any]:
        """設定ファイルを読み込み、辞書として返す

        Args:
            file_path: 読み込む設定ファイルのパス

        Returns:
            設定内容の辞書

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: ファイル形式が不正な場合
        """

    @abstractmethod
    def save(self, file_path: str, config: dict[str, Any]) -> None:
        """設定を指定したファイルに保存する

        Args:
            file_path: 保存先のファイルパス
            config: 保存する設定内容

        Raises:
            ValueError: 設定内容が不正な場合
            OSError: ファイルの書き込みに失敗した場合
        """
