"""エピソード管理データ用リポジトリインターフェース."""

from abc import ABC, abstractmethod

from noveler.domain.value_objects.episode_number import EpisodeNumber


class EpisodeManagementDataRepository(ABC):
    """エピソード管理データの永続化を担当するリポジトリインターフェース."""

    @abstractmethod
    def get_episode_data(self, episode_number: EpisodeNumber) -> dict | None:
        """指定されたエピソード番号の管理データを取得.

        Args:
            episode_number: エピソード番号

        Returns:
            エピソード管理データ、存在しない場合はNone
        """

    @abstractmethod
    def save_episode_data(self, episode_number: EpisodeNumber, data: dict) -> None:
        """エピソード管理データを保存.

        Args:
            episode_number: エピソード番号
            data: 管理データ
        """

    @abstractmethod
    def get_all_episode_data(self) -> dict[int, dict]:
        """全エピソードの管理データを取得.

        Returns:
            エピソード番号をキーとした管理データの辞書
        """

    @abstractmethod
    def delete_episode_data(self, episode_number: EpisodeNumber) -> bool:
        """指定されたエピソードの管理データを削除.

        Args:
            episode_number: エピソード番号

        Returns:
            削除成功時True、対象が存在しない場合False
        """

    @abstractmethod
    def get_episode_list(self) -> list[EpisodeNumber]:
        """管理データが存在するエピソード番号のリストを取得.

        Returns:
            エピソード番号のリスト
        """
