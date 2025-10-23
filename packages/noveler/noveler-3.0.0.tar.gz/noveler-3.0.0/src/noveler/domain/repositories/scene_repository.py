#!/usr/bin/env python3
"""シーンリポジトリインターフェース

DDD原則に基づくリポジトリインターフェース
重要シーン情報の永続化を抽象化
"""

from abc import ABC, abstractmethod
from typing import Any


class SceneRepository(ABC):
    """シーンリポジトリインターフェース"""

    @abstractmethod
    def find_by_episode(self, project_name: str, episode_number: int) -> list[dict[str, Any]]:
        """エピソードに関連するシーン情報を取得

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            シーン情報のリスト
        """

    @abstractmethod
    def find_by_id(self, project_name: str, scene_id: str) -> dict[str, Any] | None:
        """シーンIDでシーン情報を取得

        Args:
            project_name: プロジェクト名
            scene_id: シーンID

        Returns:
            シーン情報の辞書、見つからない場合はNone
        """

    @abstractmethod
    def save_scene(self, project_name: str, scene_data: dict[str, Any]) -> None:
        """シーン情報を保存

        Args:
            project_name: プロジェクト名
            scene_data: シーン情報
        """

    @abstractmethod
    def find_by_category(self, project_name: str, category: str) -> list[dict[str, Any]]:
        """カテゴリ別にシーンを取得

        Args:
            project_name: プロジェクト名
            category: シーンカテゴリ(climax_scenes, emotional_scenes等)

        Returns:
            シーン情報のリスト
        """

    @abstractmethod
    def find_by_importance(self, project_name: str, importance_level: str) -> list[dict[str, Any]]:
        """重要度別にシーンを取得

        Args:
            project_name: プロジェクト名
            importance_level: 重要度(S, A, B, C)

        Returns:
            シーン情報のリスト
        """

    @abstractmethod
    def exists(self, project_name: str, scene_id: str) -> bool:
        """シーンが存在するか確認

        Args:
            project_name: プロジェクト名
            scene_id: シーンID

        Returns:
            存在する場合True
        """
