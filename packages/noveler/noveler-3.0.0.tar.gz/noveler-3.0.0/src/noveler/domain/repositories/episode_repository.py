"""Domain.repositories.episode_repository
Where: Domain repository interface for episodes.
What: Specifies CRUD operations for episode aggregates and metadata.
Why: Provides a contract for infrastructure to manage episode data.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""エピソードリポジトリインターフェース

DDD原則に基づくドメイン層のリポジトリ抽象化
"""


from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from noveler.domain.entities.episode import Episode


class EpisodeStatistics(TypedDict):
    """エピソード統計情報の型定義"""

    total_episodes: int
    total_word_count: int
    published_episodes: int
    draft_episodes: int
    average_word_count: float
    last_updated: str


class EpisodeInfo(TypedDict):
    """エピソード情報の型定義"""

    id: str
    number: int
    title: str
    status: str
    word_count: int
    published_date: str | None
    phase: str


class EpisodeRepository(ABC):
    """エピソードリポジトリインターフェース"""

    @abstractmethod
    def save(self, episode: Episode, project_id: str) -> None:
        """エピソードを保存

        Args:
            episode: 保存するエピソード
            project_id: プロジェクトID
        """

    @abstractmethod
    def find_by_id(self, episode_id: str, project_id: str) -> Episode | None:
        """IDでエピソードを検索

        Args:
            episode_id: エピソードID
            project_id: プロジェクトID

        Returns:
            Episode: 見つかったエピソード、なければNone
        """

    @abstractmethod
    def find_by_project_and_number(self, project_id: str, episode_number: int) -> Episode | None:
        """プロジェクトIDとエピソード番号でエピソードを検索

        Args:
            project_id: プロジェクトID
            episode_number: エピソード番号

        Returns:
            Episode: 見つかったエピソード、なければNone
        """

    @abstractmethod
    def find_all_by_project(self, project_id: str) -> list[Episode]:
        """プロジェクトの全エピソードを取得

        Args:
            project_id: プロジェクトID

        Returns:
            list[Episode]: エピソードリスト
        """

    @abstractmethod
    def find_by_status(self, project_id: str, status: str) -> list[Episode]:
        """ステータスでエピソードを検索

        Args:
            project_id: プロジェクトID
            status: エピソードステータス

        Returns:
            list[Episode]: 該当するエピソードリスト
        """

    @abstractmethod
    def find_by_date_range(self, project_id: str, start_date: datetime, end_date: datetime) -> list[Episode]:
        """日付範囲でエピソードを検索

        Args:
            project_id: プロジェクトID
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            list[Episode]: 該当するエピソードリスト
        """

    @abstractmethod
    def delete(self, episode_id: str, project_id: str) -> bool:
        """エピソードを削除

        Args:
            episode_id: エピソードID
            project_id: プロジェクトID

        Returns:
            bool: 削除成功時True
        """

    @abstractmethod
    def get_next_episode_number(self, project_id: str) -> int:
        """次のエピソード番号を取得

        Args:
            project_id: プロジェクトID

        Returns:
            int: 次のエピソード番号
        """

    @abstractmethod
    def get_episode_count(self, project_id: str) -> int:
        """エピソード数を取得

        Args:
            project_id: プロジェクトID

        Returns:
            int: エピソード数
        """

    @abstractmethod
    def get_total_word_count(self, project_id: str) -> int:
        """総文字数を取得

        Args:
            project_id: プロジェクトID

        Returns:
            int: 総文字数
        """

    @abstractmethod
    def find_by_tags(self, project_id: str, tags: list[str]) -> list[Episode]:
        """タグでエピソードを検索

        Args:
            project_id: プロジェクトID
            tags: 検索タグリスト

        Returns:
            list[Episode]: 該当するエピソードリスト
        """

    @abstractmethod
    def find_by_quality_score_range(self, project_id: str, min_score: float, max_score: float) -> list[Episode]:
        """品質スコア範囲でエピソードを検索

        Args:
            project_id: プロジェクトID
            min_score: 最小スコア
            max_score: 最大スコア

        Returns:
            list[Episode]: 該当するエピソードリスト
        """

    @abstractmethod
    def find_ready_for_publication(self, project_id: str) -> list[Episode]:
        """公開準備完了のエピソードを取得

        Args:
            project_id: プロジェクトID

        Returns:
            list[Episode]: 公開可能なエピソードリスト
        """

    @abstractmethod
    def get_statistics(self, project_id: str) -> EpisodeStatistics:
        """エピソード統計情報を取得

        Args:
            project_id: プロジェクトID

        Returns:
            EpisodeStatistics: 統計情報
        """

    def bulk_update_status(self, project_id: str, episode_ids: list[str], new_status: str) -> int:
        """複数エピソードのステータスを一括更新

        Args:
            project_id: プロジェクトID
            episode_ids: エピソードIDリスト
            new_status: 新しいステータス

        Returns:
            int: 更新されたエピソード数
        """
        raise NotImplementedError('bulk_update_status is not implemented')

    def backup_episode(self, episode_id: str, project_id: str) -> bool:
        """エピソードをバックアップ

        Args:
            episode_id: エピソードID
            project_id: プロジェクトID

        Returns:
            bool: バックアップ成功時True
        """
        raise NotImplementedError('backup_episode is not implemented')

    def restore_episode(self, episode_id: str, project_id: str, backup_version: str) -> bool:
        """エピソードをバックアップから復元

        Args:
            episode_id: エピソードID
            project_id: プロジェクトID
            backup_version: バックアップバージョン

        Returns:
            bool: 復元成功時True
        """
        raise NotImplementedError('restore_episode is not implemented')

    def get_episode_info(self, project_name: str, episode_number: int) -> EpisodeInfo | None:
        """エピソード情報を取得

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            エピソード情報(見つからない場合はNone)
        """
        raise NotImplementedError('get_episode_info is not implemented')

    def update_phase(self, project_name: str, episode_number: int, new_phase: str) -> None:
        """エピソードのフェーズを更新

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            new_phase: 新しいフェーズ
        """
        raise NotImplementedError('update_phase is not implemented')

    def get_all_episodes(self, project_name: str) -> list[EpisodeInfo]:
        """プロジェクトの全エピソード情報を取得

        Args:
            project_name: プロジェクト名

        Returns:
            エピソード情報のリスト
        """
        raise NotImplementedError('get_all_episodes is not implemented')

    def get_episodes_in_range(self, project_name: str, start_episode: int, end_episode: int) -> list[EpisodeInfo]:
        """範囲指定でエピソード情報を取得

        Args:
            project_name: プロジェクト名
            start_episode: 開始エピソード番号
            end_episode: 終了エピソード番号

        Returns:
            範囲内のエピソード情報リスト
        """
        raise NotImplementedError('get_episodes_in_range is not implemented')

    def get_latest_episode(self, project_name: str) -> EpisodeInfo | None:
        """最新のエピソード情報を取得

        Args:
            project_name: プロジェクト名

        Returns:
            最新エピソード情報(見つからない場合はNone)
        """
        raise NotImplementedError('get_latest_episode is not implemented')

    def update_content(self, project_name: str, episode_number: int, new_content: str) -> None:
        """エピソードの内容を更新

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            new_content: 新しい内容
        """
        raise NotImplementedError('update_content is not implemented')

    def get_episode_content(self, project_name: str, episode_number: int) -> str:
        """エピソードの内容を取得

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            str: エピソード内容

        Raises:
            FileNotFoundError: エピソードが見つからない場合
        """
        raise NotImplementedError('get_episode_content is not implemented')

    def save_episode_content(self, target_file: Path, content: str) -> None:
        """エピソード内容をファイルに保存

        Args:
            target_file: 保存先ファイルパス
            content: 保存する内容
        """
        raise NotImplementedError('save_episode_content is not implemented')


# クエリオブジェクト(より複雑な検索用)
class EpisodeQuery:
    """エピソード検索クエリ"""

    def __init__(self) -> None:
        self.project_id: str | None = None
        self.episode_numbers: list[int] | None = None
        self.statuses: list[str] | None = None
        self.tags: list[str] | None = None
        self.min_word_count: int | None = None
        self.max_word_count: int | None = None
        self.min_quality_score: float | None = None
        self.max_quality_score: float | None = None
        self.created_after: datetime | None = None
        self.created_before: datetime | None = None
        self.updated_after: datetime | None = None
        self.updated_before: datetime | None = None
        self.order_by: str = "episode_number"
        self.order_desc: bool = False
        self.limit: int | None = None
        self.offset: int = 0

    def with_project(self, project_id: str) -> EpisodeQuery:
        """プロジェクトIDを設定"""
        self.project_id = project_id
        return self

    def with_episode_numbers(self, numbers: list[int]) -> EpisodeQuery:
        """エピソード番号を設定"""
        self.episode_numbers = numbers
        return self

    def with_statuses(self, statuses: list[str]) -> EpisodeQuery:
        """ステータスを設定"""
        self.statuses = statuses
        return self

    def with_tags(self, tags: list[str]) -> EpisodeQuery:
        """タグを設定"""
        self.tags = tags
        return self

    def with_word_count_range(self, min_count: int, max_count: int) -> EpisodeQuery:
        """文字数範囲を設定"""
        self.min_word_count = min_count
        self.max_word_count = max_count
        return self

    def with_quality_score_range(self, min_score: float, max_score: float) -> EpisodeQuery:
        """品質スコア範囲を設定"""
        self.min_quality_score = min_score
        self.max_quality_score = max_score
        return self

    def with_created_date_range(self, after: datetime, before: datetime) -> EpisodeQuery:
        """作成日時範囲を設定"""
        self.created_after = after
        self.created_before = before
        return self

    def with_updated_date_range(self, after: datetime, before: datetime) -> EpisodeQuery:
        """更新日時範囲を設定"""
        self.updated_after = after
        self.updated_before = before
        return self

    def order_by_field(self, field: str, desc: bool) -> EpisodeQuery:
        """ソート設定"""
        self.order_by = field
        self.order_desc = desc
        return self

    def with_pagination(self, limit: int, offset: int) -> EpisodeQuery:
        """ページネーション設定"""
        self.limit = limit
        self.offset = offset
        return self


# 拡張リポジトリインターフェース(高度な検索用)
class AdvancedEpisodeRepository(EpisodeRepository):
    """高度なエピソードリポジトリインターフェース"""

    @abstractmethod
    def find_by_query(self, query: EpisodeQuery) -> list[Episode]:
        """クエリでエピソードを検索

        Args:
            query: 検索クエリ

        Returns:
            list[Episode]: 検索結果
        """

    @abstractmethod
    def count_by_query(self, query: EpisodeQuery) -> int:
        """クエリに該当するエピソード数を取得

        Args:
            query: 検索クエリ

        Returns:
            int: 該当エピソード数
        """
