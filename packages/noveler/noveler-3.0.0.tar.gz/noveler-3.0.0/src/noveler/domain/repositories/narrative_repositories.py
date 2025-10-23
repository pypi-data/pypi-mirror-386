# domain/narrative_repositories.py
"""リポジトリインターフェース(ドメイン層)"""

from abc import ABC, abstractmethod
from typing import Any


class PlotDataRepository(ABC):
    """プロットデータのリポジトリインターフェース"""

    @abstractmethod
    def get_viewpoint_info(self, episode_number: int) -> dict[str, Any] | None:
        """エピソードの視点情報を取得"""

    @abstractmethod
    def get_complexity_level(self, episode_number: int) -> str:
        """エピソードの複雑度レベルを取得"""


class EpisodeTextRepository(ABC):
    """エピソードテキストのリポジトリインターフェース"""

    @abstractmethod
    def get_episode_text(self, episode_number: int) -> str:
        """エピソードのテキストを取得"""

    @abstractmethod
    def get_episode_metadata(self, episode_number: int) -> dict[str, Any]:
        """エピソードのメタデータを取得"""


class EvaluationResultRepository(ABC):
    """評価結果のリポジトリインターフェース"""

    @abstractmethod
    def save_evaluation_result(self, episode_number: int, result: dict[str, Any]) -> None:
        """評価結果を保存"""

    @abstractmethod
    def get_evaluation_history(self, episode_number: int) -> list[dict[str, Any]]:
        """評価履歴を取得"""
