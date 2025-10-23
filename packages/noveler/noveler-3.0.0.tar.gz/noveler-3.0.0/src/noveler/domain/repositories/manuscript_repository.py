"""原稿管理用リポジトリインターフェース."""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path


class ManuscriptRepository(ABC):
    """原稿の永続化を担当するリポジトリインターフェース."""

    @abstractmethod
    def get_manuscript(self, episode_number: int) -> str | None:
        """指定されたエピソードの原稿を取得.

        Args:
            episode_number: エピソード番号

        Returns:
            原稿内容、存在しない場合はNone
        """

    @abstractmethod
    def save_manuscript(self, episode_number: int, content: str) -> bool:
        """原稿を保存.

        Args:
            episode_number: エピソード番号
            content: 原稿内容
            title: エピソードタイトル

        Returns:
            保存成功時True
        """

    @abstractmethod
    def get_manuscript_metadata(self, episode_number: int) -> dict | None:
        """原稿のメタデータを取得.

        Args:
            episode_number: エピソード番号

        Returns:
            メタデータ、存在しない場合はNone
        """

    @abstractmethod
    def list_manuscripts(self) -> list[int]:
        """存在する原稿のエピソード番号一覧を取得.

        Returns:
            エピソード番号のリスト
        """

    @abstractmethod
    def get_manuscript_path(self, episode_number: int) -> Path | None:
        """原稿ファイルのパスを取得.

        Args:
            episode_number: エピソード番号

        Returns:
            ファイルパス、存在しない場合はNone
        """

    @abstractmethod
    def delete_manuscript(self, episode_number: int) -> bool:
        """原稿を削除.

        Args:
            episode_number: エピソード番号

        Returns:
            削除成功時True
        """

    @abstractmethod
    def get_word_count(self, episode_number: int) -> int:
        """原稿の文字数を取得.

        Args:
            episode_number: エピソード番号

        Returns:
            文字数、存在しない場合は0
        """

    @abstractmethod
    def get_last_modified(self, episode_number: int) -> datetime | None:
        """原稿の最終更新日時を取得.

        Args:
            episode_number: エピソード番号

        Returns:
            最終更新日時、存在しない場合はNone
        """
