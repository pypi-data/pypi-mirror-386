"""Infrastructure.ports.repositories.episode_repository
Where: Infrastructure port helpers for episode repositories.
What: Provides stub implementations and testing helpers for episode ports.
Why: Simplifies testing and modular reuse of repository ports.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""エピソードリポジトリポートインターフェース

SPEC-901-DDD-REFACTORING: Port & Adapter分離実装
Golden Sampleに基づくヘキサゴナルアーキテクチャパターン適用

このポートはDDD原則に基づくリポジトリ抽象化を定義し、
アダプターの具象実装への依存を排除します。
"""

import abc
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from datetime import datetime

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


class EpisodeRepositoryPort(abc.ABC):
    """エピソードリポジトリポートインターフェース

    Golden Sampleのパターンに従い、明確にPortとして定義。
    すべての永続化操作をアダプターに委譲し、ドメイン知識を保持しない。
    """

    @abc.abstractmethod
    async def save(self, episode: Episode, project_id: str) -> None:
        """エピソードを非同期で保存

        Args:
            episode: 保存するエピソード
            project_id: プロジェクトID

        Raises:
            RepositoryError: 保存に失敗した場合
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_id(self, episode_id: str, project_id: str) -> Episode | None:
        """IDでエピソードを非同期検索

        Args:
            episode_id: エピソードID
            project_id: プロジェクトID

        Returns:
            Episode: 見つかったエピソード、なければNone

        Raises:
            RepositoryError: 検索に失敗した場合
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_project_and_number(self, project_id: str, episode_number: int) -> Episode | None:
        """プロジェクトIDとエピソード番号でエピソードを非同期検索

        Args:
            project_id: プロジェクトID
            episode_number: エピソード番号

        Returns:
            Episode: 見つかったエピソード、なければNone

        Raises:
            RepositoryError: 検索に失敗した場合
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def find_all_by_project(self, project_id: str) -> list[Episode]:
        """プロジェクトの全エピソードを非同期取得

        Args:
            project_id: プロジェクトID

        Returns:
            list[Episode]: エピソードリスト

        Raises:
            RepositoryError: 検索に失敗した場合
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_status(self, project_id: str, status: str) -> list[Episode]:
        """ステータスでエピソードを非同期検索

        Args:
            project_id: プロジェクトID
            status: エピソードステータス

        Returns:
            list[Episode]: 該当するエピソードリスト

        Raises:
            RepositoryError: 検索に失敗した場合
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def find_by_date_range(self, project_id: str, start_date: datetime, end_date: datetime) -> list[Episode]:
        """日付範囲でエピソードを非同期検索

        Args:
            project_id: プロジェクトID
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            list[Episode]: 該当するエピソードリスト

        Raises:
            RepositoryError: 検索に失敗した場合
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, episode_id: str, project_id: str) -> bool:
        """エピソードを非同期削除

        Args:
            episode_id: エピソードID
            project_id: プロジェクトID

        Returns:
            bool: 削除成功時True

        Raises:
            RepositoryError: 削除に失敗した場合
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def get_next_episode_number(self, project_id: str) -> int:
        """次のエピソード番号を非同期取得

        Args:
            project_id: プロジェクトID

        Returns:
            int: 次のエピソード番号

        Raises:
            RepositoryError: 取得に失敗した場合
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def get_statistics(self, project_id: str) -> EpisodeStatistics:
        """エピソード統計情報を非同期取得

        Args:
            project_id: プロジェクトID

        Returns:
            EpisodeStatistics: 統計情報

        Raises:
            RepositoryError: 取得に失敗した場合
        """
        raise NotImplementedError


class EpisodeQuery:
    """エピソード検索クエリオブジェクト

    複雑な検索条件を表現するためのクエリビルダーパターン実装
    """

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

    def order_by_field(self, field: str, desc: bool = False) -> EpisodeQuery:
        """ソート設定"""
        self.order_by = field
        self.order_desc = desc
        return self

    def with_pagination(self, limit: int, offset: int = 0) -> EpisodeQuery:
        """ページネーション設定"""
        self.limit = limit
        self.offset = offset
        return self


class AdvancedEpisodeRepositoryPort(EpisodeRepositoryPort):
    """高度なエピソードリポジトリポートインターフェース

    複雑なクエリと分析機能をサポート
    """

    @abc.abstractmethod
    async def find_by_query(self, query: EpisodeQuery) -> list[Episode]:
        """クエリでエピソードを非同期検索

        Args:
            query: 検索クエリ

        Returns:
            list[Episode]: 検索結果

        Raises:
            RepositoryError: 検索に失敗した場合
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def count_by_query(self, query: EpisodeQuery) -> int:
        """クエリに該当するエピソード数を非同期取得

        Args:
            query: 検索クエリ

        Returns:
            int: 該当エピソード数

        Raises:
            RepositoryError: 取得に失敗した場合
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def bulk_update_status(self, project_id: str, episode_ids: list[str], new_status: str) -> int:
        """複数エピソードのステータスを一括更新

        Args:
            project_id: プロジェクトID
            episode_ids: エピソードIDリスト
            new_status: 新しいステータス

        Returns:
            int: 更新されたエピソード数

        Raises:
            RepositoryError: 更新に失敗した場合
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def backup_episode(self, episode_id: str, project_id: str) -> bool:
        """エピソードを非同期バックアップ

        Args:
            episode_id: エピソードID
            project_id: プロジェクトID

        Returns:
            bool: バックアップ成功時True

        Raises:
            RepositoryError: バックアップに失敗した場合
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def restore_episode(self, episode_id: str, project_id: str, backup_version: str) -> bool:
        """エピソードをバックアップから非同期復元

        Args:
            episode_id: エピソードID
            project_id: プロジェクトID
            backup_version: バックアップバージョン

        Returns:
            bool: 復元成功時True

        Raises:
            RepositoryError: 復元に失敗した場合
        """
        raise NotImplementedError


# 後方互換性のためのエイリアス（段階的移行用）
EpisodeRepository = EpisodeRepositoryPort
AdvancedEpisodeRepository = AdvancedEpisodeRepositoryPort
