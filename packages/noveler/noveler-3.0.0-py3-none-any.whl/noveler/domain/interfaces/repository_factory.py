#!/usr/bin/env python3
"""リポジトリファクトリインターフェース

DDD準拠: Domain層の抽象インターフェース
リポジトリインスタンス生成の抽象化
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

# 循環参照回避のための型チェック時のみのインポート
if TYPE_CHECKING:
    from noveler.domain.repositories.a31_checklist_repository import A31ChecklistRepository
    from noveler.domain.repositories.character_repository import CharacterRepository
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.foreshadowing_repository import ForeshadowingRepository
    from noveler.domain.repositories.plot_repository import PlotRepository
    from noveler.domain.repositories.project_repository import ProjectRepository
    from noveler.domain.repositories.quality_check_repository import QualityCheckRepository
    from noveler.domain.repositories.scene_repository import SceneRepository


class IRepositoryFactory(ABC):
    """リポジトリファクトリインターフェース

    DDD準拠のリポジトリインスタンス生成抽象化
    Application層からの依存注入契約を定義
    """

    @abstractmethod
    def create_episode_repository(self) -> "EpisodeRepository":
        """エピソードリポジトリ生成

        Returns:
            EpisodeRepository: エピソードリポジトリインスタンス
        """

    @abstractmethod
    def create_plot_repository(self) -> "PlotRepository":
        """プロットリポジトリ生成

        Returns:
            PlotRepository: プロットリポジトリインスタンス
        """

    @abstractmethod
    def create_project_repository(self) -> "ProjectRepository":
        """プロジェクトリポジトリ生成

        Returns:
            ProjectRepository: プロジェクトリポジトリインスタンス
        """

    @abstractmethod
    def create_character_repository(self) -> "CharacterRepository":
        """キャラクターリポジトリ生成

        Returns:
            CharacterRepository: キャラクターリポジトリインスタンス
        """

    @abstractmethod
    def create_foreshadowing_repository(self) -> "ForeshadowingRepository":
        """伏線リポジトリ生成

        Returns:
            ForeshadowingRepository: 伏線リポジトリインスタンス
        """

    @abstractmethod
    def create_scene_repository(self) -> "SceneRepository":
        """シーンリポジトリ生成

        Returns:
            SceneRepository: シーンリポジトリインスタンス
        """

    @abstractmethod
    def create_a31_checklist_repository(self) -> "A31ChecklistRepository":
        """A31チェックリストリポジトリ生成

        Returns:
            A31ChecklistRepository: A31チェックリストリポジトリインスタンス
        """

    @abstractmethod
    def create_quality_check_repository(self) -> "QualityCheckRepository":
        """品質チェックリポジトリ生成

        Returns:
            QualityCheckRepository: 品質チェックリポジトリインスタンス
        """
