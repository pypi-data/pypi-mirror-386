"""Domain Repository Interfaces for Writing Context
執筆コンテキストのドメインリポジトリインターフェース

DDD原則でのリポジトリパターン実装
- ドメイン層でインターフェース定義
- インフラ層で実装
- 依存性逆転の原則を適用
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from noveler.domain.writing.entities import Episode, WritingRecord, WritingSession


class EpisodeRepository(ABC):
    """エピソードリポジトリインターフェース"""

    @abstractmethod
    def find_by_id(self, episode_id: str) -> Episode | None:
        """IDでエピソードを取得"""

    @abstractmethod
    def find_by_number(self, project_id: str, episode_number: int) -> Episode | None:
        """プロジェクトと話数でエピソードを取得"""

    @abstractmethod
    def find_by_status(self, project_id: str, status: str) -> list[Episode]:
        """ステータス別にエピソードを取得"""

    @abstractmethod
    def find_next_unwritten(self, project_id: str) -> Episode | None:
        """次の未執筆エピソードを取得"""

    @abstractmethod
    def find_all_by_project(self, project_id: str) -> list[Episode]:
        """プロジェクトの全エピソードを取得"""

    @abstractmethod
    def find_by_phase(self, project_id: str, phase: str) -> list[Episode]:
        """フェーズ別にエピソードを取得"""

    @abstractmethod
    def find_by_publication_status(self, project_id: str, status: str) -> list[Episode]:
        """公開ステータス別にエピソードを取得"""

    @abstractmethod
    def find_latest_episode(self, project_id: str) -> Episode | None:
        """最新のエピソードを取得"""

    @abstractmethod
    def save(self, episode: Episode) -> Episode:
        """エピソードを保存し、保存後のエンティティを返却"""

    @abstractmethod
    def create_from_plot(self, project_id: str, plot_info: dict[str, Any]) -> Episode:
        """プロット情報からエピソードを作成"""

    @abstractmethod
    def update_plot_status(self, project_id: str, episode_number: int) -> bool:
        """プロットファイルのステータスを更新"""

    @abstractmethod
    def delete(self, episode_id: str) -> None:
        """エピソードを削除"""


class WritingRecordRepository(ABC):
    """執筆記録リポジトリインターフェース"""

    @abstractmethod
    def find_by_id(self, record_id: str) -> WritingRecord | None:
        """IDで執筆記録を取得"""

    @abstractmethod
    def find_by_episode(self, episode_id: str) -> list[WritingRecord]:
        """エピソードの全執筆記録を取得"""

    @abstractmethod
    def find_by_date_range(self, project_id: str, start_date: date) -> list[WritingRecord]:
        """期間内の執筆記録を取得"""

    @abstractmethod
    def save(self, record: WritingRecord) -> WritingRecord:
        """執筆記録を保存し、保存後のエンティティを返却"""

    @abstractmethod
    def delete(self, record_id: str) -> None:
        """執筆記録を削除"""


class WritingSessionRepository(ABC):
    """執筆セッションリポジトリインターフェース"""

    @abstractmethod
    def find_by_id(self, session_id: str) -> WritingSession | None:
        """IDで執筆セッションを取得"""

    @abstractmethod
    def find_by_date(self, project_id: str, date: date) -> WritingSession | None:
        """日付で執筆セッションを取得"""

    @abstractmethod
    def find_by_episode(self, episode_id: str) -> list[WritingSession]:
        """エピソードの全執筆セッションを取得"""

    @abstractmethod
    def find_recent_sessions(self, project_id: str, days: int) -> list[WritingSession]:
        """最近の執筆セッションを取得"""

    @abstractmethod
    def save(self, session: WritingSession) -> WritingSession:
        """執筆セッションを保存し、保存後のエンティティを返却"""

    @abstractmethod
    def delete(self, session_id: str) -> None:
        """執筆セッションを削除"""
