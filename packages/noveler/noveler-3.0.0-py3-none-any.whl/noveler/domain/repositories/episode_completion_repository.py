#!/usr/bin/env python3
"""執筆完了関連のリポジトリインターフェース
DDD原則:ドメイン層でインターフェースを定義
"""

from abc import ABC, abstractmethod
from typing import Any


class EpisodeManagementRepository(ABC):
    """話数管理リポジトリ"""

    @abstractmethod
    def update_episode_status(self, project_path: str, episode_number: int) -> None:
        """エピソードステータスを更新"""

    @abstractmethod
    def get_episode_info(self, project_path: str, episode_number: int) -> dict[str, Any] | None:
        """エピソード情報を取得"""


class ForeshadowingRepository(ABC):
    """伏線管理リポジトリ"""

    @abstractmethod
    def update_foreshadowing_status(self, project_path: str, foreshadowing_id: str) -> None:
        """伏線ステータスを更新"""

    @abstractmethod
    def get_foreshadowing_info(self, project_path: str, foreshadowing_id: str) -> dict[str, Any] | None:
        """伏線情報を取得"""

    @abstractmethod
    def list_foreshadowing_by_episode(self, project_path: str, episode_number: int) -> list[dict[str, Any]]:
        """エピソード別伏線リスト取得"""


class CharacterGrowthRepository(ABC):
    """キャラクター成長記録リポジトリ"""

    @abstractmethod
    def add_growth_event(self, project_path: str, character_name: str) -> None:
        """成長イベントを追加"""

    @abstractmethod
    def get_character_growth_history(self, project_path: str, character_name: str) -> list[dict[str, Any]]:
        """キャラクター成長履歴を取得"""


class ImportantSceneRepository(ABC):
    """重要シーン記録リポジトリ"""

    @abstractmethod
    def add_important_scene(self, project_path: str, episode_number: int) -> None:
        """重要シーンを追加"""

    @abstractmethod
    def get_scenes_by_episode(self, project_path: str, episode_number: int) -> list[dict[str, Any]]:
        """エピソード別シーンリスト取得"""


class RevisionHistoryRepository(ABC):
    """改訂履歴リポジトリ"""

    @abstractmethod
    def add_completion_record(self, project_path: str, episode_number: int) -> None:
        """執筆完了記録を追加"""


class ChapterPlotRepository(ABC):
    """章別プロットリポジトリ"""

    @abstractmethod
    def update_plot_status(self, project_path: str, chapter: int) -> None:
        """プロットステータスを更新"""

    @abstractmethod
    def get_plot_data(self, project_path: str, chapter: int) -> dict[str, Any] | None:
        """プロットデータを取得"""


class CompletionTransactionManager(ABC):
    """執筆完了トランザクション管理"""

    @abstractmethod
    def begin_transaction(self) -> "CompletionTransaction":
        """トランザクション開始"""


class CompletionTransaction(ABC):
    """執筆完了トランザクション"""

    @abstractmethod
    def update_episode_status(self, episode_number: int, status: str) -> None:
        """エピソードステータス更新"""

    @abstractmethod
    def plant_foreshadowing(self, foreshadowing_id: str, episode_number: int) -> None:
        """伏線を仕込む"""

    @abstractmethod
    def resolve_foreshadowing(self, foreshadowing_id: str, episode_number: int) -> None:
        """伏線を回収"""

    @abstractmethod
    def add_character_growth(self, character_name: str, episode_number: int) -> None:
        """キャラクター成長を追加"""

    @abstractmethod
    def add_important_scene(self, episode_number: int, scene: dict[str, Any]) -> None:
        """重要シーンを追加"""

    @abstractmethod
    def add_revision_history(self, episode_number: int, data: dict[str, Any]) -> None:
        """改訂履歴を追加"""

    @abstractmethod
    def update_chapter_plot(self, chapter: int, episode_number: int) -> None:
        """章別プロットを更新"""

    @abstractmethod
    def commit(self) -> None:
        """トランザクションコミット"""

    @abstractmethod
    def rollback(self) -> None:
        """トランザクションロールバック"""
