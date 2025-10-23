"""執筆記録リポジトリインターフェース

執筆の履歴や完成記録を管理するための抽象インターフェース。
DDD原則に基づき、ドメイン層に配置。
"""

from abc import ABC, abstractmethod
from typing import Any


class WritingRecordRepository(ABC):
    """執筆記録リポジトリの抽象インターフェース"""

    @abstractmethod
    def save_completion_record(self, record: dict[str, Any]) -> None:
        """完成記録を保存

        Args:
            record: 完成記録データ
                - project_name: プロジェクト名
                - episode_number: エピソード番号
                - old_phase: 元のフェーズ
                - new_phase: 新しいフェーズ
                - quality_score: 品質スコア(オプション)
                - completed_at: 完成日時

        Raises:
            RepositoryError: 保存エラー
        """

    @abstractmethod
    def get_completion_history(self, project_name: str, episode_number: int) -> list[dict[str, Any]]:
        """完成履歴を取得

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号(指定しない場合は全エピソード)

        Returns:
            完成履歴のリスト

        Raises:
            RepositoryError: 取得エラー
        """

    @abstractmethod
    def get_latest_completion(self, project_name: str, episode_number: int) -> dict[str, Any] | None:
        """最新の完成記録を取得

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            最新の完成記録(見つからない場合はNone)

        Raises:
            RepositoryError: 取得エラー
        """

    @abstractmethod
    def get_phase_duration(self, project_name: str, episode_number: int) -> float | None:
        """特定フェーズの所要時間を取得

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            phase: 執筆フェーズ

        Returns:
            所要時間(時間単位)、データがない場合はNone

        Raises:
            RepositoryError: 取得エラー
        """
