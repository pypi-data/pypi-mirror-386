#!/usr/bin/env python3

"""Tests.tests.e2e.test_repositories
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

"""E2Eテスト用の簡易リポジトリ実装

DDD原則に基づくが、E2Eテストのための最小限の実装


仕様書: SPEC-E2E-WORKFLOW
"""


from typing import TYPE_CHECKING

from noveler.domain.entities.episode import Episode, EpisodeStatus
from noveler.domain.repositories.episode_repository import EpisodeRepository
from noveler.domain.repositories.project_repository import ProjectRepository

if TYPE_CHECKING:
    from datetime import datetime


class InMemoryEpisodeRepository(EpisodeRepository):
    """メモリ内エピソードリポジトリ(E2Eテスト用)"""

    def __init__(self) -> None:
        self._episodes: dict[str, dict[int, Episode]] = {}

    def save(self, episode: Episode, project_id: str) -> None:
        """エピソードを保存"""
        if project_id not in self._episodes:
            self._episodes[project_id] = {}
        self._episodes[project_id][episode.number.value] = episode

    def find_by_id(self, _episode_id: str, _project_id: str) -> Episode | None:
        """IDでエピソードを検索(E2E用簡易実装)"""
        # E2Eテストでは使用しないのでNoneを返す
        return None

    def find_by_project_and_number(self, project_id: str, episode_number: int) -> Episode | None:
        """プロジェクトIDとエピソード番号で検索"""
        if project_id not in self._episodes:
            return None
        return self._episodes[project_id].get(episode_number)

    def find_all_by_project(self, project_id: str) -> list[Episode]:
        """プロジェクトの全エピソードを取得"""
        if project_id not in self._episodes:
            return []
        return list(self._episodes[project_id].values())

    def find_by_status(self, status: EpisodeStatus, project_id: str) -> list[Episode]:
        """ステータスでエピソードを検索"""
        if project_id not in self._episodes:
            return []
        return [ep for ep in self._episodes[project_id].values() if ep.status == status]

    def find_by_quality_score_range(
        self,
        min_score: int,
        max_score: int,
        project_id: str,
    ) -> list[Episode]:
        """品質スコア範囲でエピソードを検索"""
        if project_id not in self._episodes:
            return []
        return [
            ep
            for ep in self._episodes[project_id].values()
            if ep.quality_score and min_score <= ep.quality_score.value <= max_score
        ]

    def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        project_id: str,
    ) -> list[Episode]:
        """日付範囲でエピソードを検索"""
        if project_id not in self._episodes:
            return []
        return [
            ep
            for ep in self._episodes[project_id].values()
            if ep.created_at and start_date <= ep.created_at <= end_date
        ]

    def find_by_tags(self, tags: list[str], project_id: str) -> list[Episode]:
        """タグでエピソードを検索"""
        if project_id not in self._episodes:
            return []
        return [ep for ep in self._episodes[project_id].values() if any(tag in ep.tags for tag in tags)]

    def find_ready_for_publication(self, project_id: str) -> list[Episode]:
        """公開準備完了のエピソードを検索"""
        if project_id not in self._episodes:
            return []
        return [ep for ep in self._episodes[project_id].values() if ep.status == EpisodeStatus.REVIEWED]

    def get_episode_count(self, project_id: str) -> int:
        """プロジェクトのエピソード数を取得"""
        if project_id not in self._episodes:
            return 0
        return len(self._episodes[project_id])

    def get_total_word_count(self, project_id: str) -> int:
        """プロジェクトの総文字数を取得"""
        if project_id not in self._episodes:
            return 0
        return sum(ep.calculate_word_count() for ep in self._episodes[project_id].values())

    def bulk_update_status(
        self,
        _episode_ids: list[str],
        status: EpisodeStatus,
        project_id: str,
    ) -> None:
        """複数エピソードのステータスを一括更新"""
        # E2Eテストでは使用しないのでパス

    def backup_episode(self, _episode_id: str, project_id: str) -> None:
        """エピソードをバックアップ"""
        # E2Eテストでは使用しないのでパス

    def restore_episode(self, _episode_id: str, _backup_version: int, project_id: str) -> None:
        """エピソードを復元"""
        # E2Eテストでは使用しないのでパス

    def delete(self, project_id: str, episode_number: int) -> None:
        """エピソードを削除"""
        if project_id in self._episodes and episode_number in self._episodes[project_id]:
            del self._episodes[project_id][episode_number]

    def get_next_episode_number(self, project_id: str) -> int:
        """次のエピソード番号を取得"""
        if project_id not in self._episodes or not self._episodes[project_id]:
            return 1
        return max(self._episodes[project_id].keys()) + 1

    def get_statistics(self, project_id: str) -> dict[str, object]:
        """統計情報を取得"""
        if project_id not in self._episodes:
            return {
                "total_episodes": 0,
                "total_words": 0,
                "average_words": 0,
                "status_distribution": {},
            }

        episodes = self._episodes[project_id].values()
        total_episodes = len(episodes)
        total_words = sum(ep.calculate_word_count() for ep in episodes)

        status_distribution = {}
        for status in EpisodeStatus:
            count = len([ep for ep in episodes if ep.status == status])
            status_distribution[status.name] = count

        return {
            "total_episodes": total_episodes,
            "total_words": total_words,
            "average_words": total_words // total_episodes if total_episodes > 0 else 0,
            "status_distribution": status_distribution,
        }


class InMemoryProjectRepository(ProjectRepository):
    """メモリ内プロジェクトリポジトリ(E2Eテスト用)"""

    def __init__(self) -> None:
        self._projects: dict[str, dict[str, object]] = {}

    def exists(self, project_id: str) -> bool:
        """プロジェクトの存在確認"""
        return project_id in self._projects

    def get_config(self, project_id: str) -> dict[str, object]:
        """プロジェクト設定を取得"""
        if project_id not in self._projects:
            return {}
        return self._projects[project_id].copy()

    def save_config(self, project_id: str, config: dict[str, object]) -> None:
        """プロジェクト設定を保存"""
        self._projects[project_id] = config.copy()

    def get_quality_threshold(self, project_id: str) -> int:
        """品質基準スコアを取得"""
        if project_id not in self._projects:
            return 70
        return self._projects[project_id].get("quality_threshold", 70)

    def get_project_info(self, project_id: str) -> dict[str, object]:
        """プロジェクト情報を取得"""
        if project_id not in self._projects:
            return {
                "id": project_id,
                "title": project_id,
                "author": "Unknown",
                "genre": "Unknown",
                "quality_threshold": 70,
            }
        return self._projects[project_id].copy()

    def update_project_info(self, project_id: str, info: dict[str, object]) -> None:
        """プロジェクト情報を更新"""
        if project_id not in self._projects:
            self._projects[project_id] = {}
        self._projects[project_id].update(info)

    def create(self, project_id: str, project_info: dict[str, object]) -> None:
        """プロジェクトを作成"""
        self._projects[project_id] = project_info.copy()

    def delete(self, project_id: str) -> None:
        """プロジェクトを削除"""
        if project_id in self._projects:
            del self._projects[project_id]

    def get_all_projects(self) -> list[str]:
        """すべてのプロジェクトIDを取得"""
        return list(self._projects.keys())

    def get_project_directory(self, project_id: str) -> str:
        """プロジェクトディレクトリパスを取得"""
        return f"/test/{project_id}"

    def get_project_metadata(self, project_id: str) -> dict[str, object]:
        """プロジェクトメタデータを取得"""
        if project_id not in self._projects:
            return {}
        return self._projects[project_id].get("metadata", {})

    def set_project_metadata(self, project_id: str, metadata: dict[str, object]) -> None:
        """プロジェクトメタデータを設定"""
        if project_id not in self._projects:
            self._projects[project_id] = {}
        self._projects[project_id]["metadata"] = metadata

    def get_project_settings(self, project_id: str) -> dict[str, object]:
        """プロジェクト設定を取得"""
        return self.get_config(project_id)

    def update_project_settings(self, project_id: str, settings: dict[str, object]) -> None:
        """プロジェクト設定を更新"""
        self.save_config(project_id, settings)

    def get_project_statistics(self, _project_id: str) -> dict[str, object]:
        """プロジェクト統計を取得"""
        return {
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "episode_count": 0,
            "total_words": 0,
        }

    def initialize_project_structure(self, project_id: str) -> None:
        """プロジェクト構造を初期化"""
        # E2Eテストではメモリ内なので何もしない

    def validate_project_structure(self, project_id: str) -> bool:
        """プロジェクト構造を検証"""
        return project_id in self._projects

    def backup_project(self, project_id: str) -> None:
        """プロジェクトをバックアップ"""
        # E2Eテストでは使用しない

    def restore_project(self, project_id: str, _backup_date: str) -> None:
        """プロジェクトを復元"""
        # E2Eテストでは使用しない

    def archive_project(self, project_id: str) -> None:
        """プロジェクトをアーカイブ"""
        # E2Eテストでは使用しない
