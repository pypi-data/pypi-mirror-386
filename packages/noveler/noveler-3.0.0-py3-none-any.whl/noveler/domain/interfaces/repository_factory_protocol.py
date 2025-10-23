#!/usr/bin/env python3
"""リポジトリファクトリプロトコル

RepositoryFactory系の循環依存解決
Protocol基盤によるリポジトリ生成の抽象化インターフェース
"""

import importlib
from abc import abstractmethod
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from noveler.domain.repositories.a31_checklist_repository import A31ChecklistRepository
    from noveler.domain.repositories.character_repository import CharacterRepository
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.foreshadowing_repository import ForeshadowingRepository
    from noveler.domain.repositories.plot_repository import PlotRepository
    from noveler.domain.repositories.project_repository import ProjectRepository
    from noveler.domain.repositories.quality_check_repository import QualityCheckRepository
    from noveler.domain.repositories.scene_repository import SceneRepository


@runtime_checkable
class RepositoryFactoryProtocol(Protocol):
    """リポジトリファクトリの抽象インターフェース"""

    @abstractmethod
    def create_episode_repository(self) -> "EpisodeRepository":
        """エピソードリポジトリ生成

        Returns:
            EpisodeRepository作成インスタンス
        """
        ...

    @abstractmethod
    def create_plot_repository(self) -> "PlotRepository":
        """プロットリポジトリ生成

        Returns:
            PlotRepository作成インスタンス
        """
        ...

    @abstractmethod
    def create_project_repository(self) -> "ProjectRepository":
        """プロジェクトリポジトリ生成

        Returns:
            ProjectRepository作成インスタンス
        """
        ...

    @abstractmethod
    def create_character_repository(self) -> "CharacterRepository":
        """キャラクターリポジトリ生成

        Returns:
            CharacterRepository作成インスタンス
        """
        ...

    @abstractmethod
    def create_foreshadowing_repository(self) -> "ForeshadowingRepository":
        """伏線リポジトリ生成

        Returns:
            ForeshadowingRepository作成インスタンス
        """
        ...

    @abstractmethod
    def create_scene_repository(self) -> "SceneRepository":
        """シーンリポジトリ生成

        Returns:
            SceneRepository作成インスタンス
        """
        ...

    @abstractmethod
    def create_a31_checklist_repository(self) -> "A31ChecklistRepository":
        """A31チェックリストリポジトリ生成

        Returns:
            A31ChecklistRepository作成インスタンス
        """
        ...

    @abstractmethod
    def create_quality_check_repository(self) -> "QualityCheckRepository":
        """品質チェックリポジトリ生成

        Returns:
            QualityCheckRepository作成インスタンス
        """
        ...


class LazyRepositoryFactoryProxy:
    """遅延ロード対応のリポジトリファクトリプロキシ

    循環依存を回避しつつ、実際のRepositoryFactoryの生成を遅延実行
    """

    def __init__(self) -> None:
        self._cached_factory: RepositoryFactoryProtocol | None = None

    @property
    def factory(self) -> RepositoryFactoryProtocol:
        """遅延ロードされるリポジトリファクトリ"""
        if self._cached_factory is None:
            # 初回アクセス時のみインポート・インスタンス化
            # B20準拠修正: Infrastructure依存をInterface経由に変更
            mod = importlib.import_module("noveler.infrastructure.di.repository_factory_impl")
            self._cached_factory = mod.RepositoryFactoryImpl()
        return self._cached_factory

    def create_episode_repository(self) -> "EpisodeRepository":
        """エピソードリポジトリ生成（遅延ロード）

        Returns:
            EpisodeRepository作成インスタンス
        """
        return self.factory.create_episode_repository()

    def create_plot_repository(self) -> "PlotRepository":
        """プロットリポジトリ生成（遅延ロード）

        Returns:
            PlotRepository作成インスタンス
        """
        return self.factory.create_plot_repository()

    def create_project_repository(self) -> "ProjectRepository":
        """プロジェクトリポジトリ生成（遅延ロード）

        Returns:
            ProjectRepository作成インスタンス
        """
        return self.factory.create_project_repository()

    def create_character_repository(self) -> "CharacterRepository":
        """キャラクターリポジトリ生成（遅延ロード）

        Returns:
            CharacterRepository作成インスタンス
        """
        return self.factory.create_character_repository()

    def create_foreshadowing_repository(self) -> "ForeshadowingRepository":
        """伏線リポジトリ生成（遅延ロード）

        Returns:
            ForeshadowingRepository作成インスタンス
        """
        return self.factory.create_foreshadowing_repository()

    def create_scene_repository(self) -> "SceneRepository":
        """シーンリポジトリ生成（遅延ロード）

        Returns:
            SceneRepository作成インスタンス
        """
        return self.factory.create_scene_repository()

    def create_a31_checklist_repository(self) -> "A31ChecklistRepository":
        """A31チェックリストリポジトリ生成（遅延ロード）

        Returns:
            A31ChecklistRepository作成インスタンス
        """
        return self.factory.create_a31_checklist_repository()

    def create_quality_check_repository(self) -> "QualityCheckRepository":
        """品質チェックリポジトリ生成（遅延ロード）

        Returns:
            QualityCheckRepository作成インスタンス
        """
        return self.factory.create_quality_check_repository()


# グローバル遅延プロキシインスタンス（シングルトン）
_repository_factory_proxy = LazyRepositoryFactoryProxy()


def get_repository_factory_manager() -> LazyRepositoryFactoryProxy:
    """リポジトリファクトリプロキシ取得（DI対応）"""
    return _repository_factory_proxy
