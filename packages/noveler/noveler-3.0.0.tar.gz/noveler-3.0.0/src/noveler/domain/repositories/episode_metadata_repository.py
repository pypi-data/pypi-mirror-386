"""
SPEC-EPISODE-004: エピソードメタデータリポジトリインターフェース

エピソードメタデータの永続化を抽象化するリポジトリインターフェース。
DDD設計に基づくドメイン層のインターフェース定義。
"""

from abc import ABC, abstractmethod

from noveler.domain.services.metadata_value_objects import EpisodeMetadata, MetadataStatistics


class EpisodeMetadataRepository(ABC):
    """エピソードメタデータリポジトリインターフェース"""

    @abstractmethod
    def find_by_episode_number(self, episode_number: int) -> EpisodeMetadata | None:
        """エピソード番号でメタデータを検索

        Args:
            episode_number: 検索対象のエピソード番号

        Returns:
            見つかったメタデータ、存在しない場合はNone
        """

    @abstractmethod
    def search_by_criteria(self, criteria: dict) -> list[EpisodeMetadata]:
        """検索条件でメタデータを検索

        Args:
            criteria: 検索条件

        Returns:
            条件に一致するメタデータのリスト
        """

    @abstractmethod
    def save(self, metadata: EpisodeMetadata) -> None:
        """メタデータを保存

        Args:
            metadata: 保存するメタデータ
        """

    @abstractmethod
    def delete(self, episode_number: int) -> bool:
        """メタデータを削除

        Args:
            episode_number: 削除対象のエピソード番号

        Returns:
            削除成功の場合True、対象が存在しない場合False
        """

    @abstractmethod
    def get_statistics(self, period: str) -> MetadataStatistics:
        """指定期間の統計情報を取得

        Args:
            period: 統計期間

        Returns:
            統計情報
        """

    @abstractmethod
    def get_all(self) -> list[EpisodeMetadata]:
        """全てのメタデータを取得

        Returns:
            全メタデータのリスト
        """

    @abstractmethod
    def exists(self, episode_number: int) -> bool:
        """メタデータの存在確認

        Args:
            episode_number: 確認対象のエピソード番号

        Returns:
            存在する場合True
        """
