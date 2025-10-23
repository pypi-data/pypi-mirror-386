"""リポジトリファクトリーProtocol定義

循環依存回避のための純粋なProtocol定義。
リポジトリへの参照はtypingで型ヒントのみ提供。
"""

from typing import TYPE_CHECKING, Any, Protocol, TypeVar

if TYPE_CHECKING:
    from noveler.domain.repositories.a31_checklist_repository import A31ChecklistRepository
    from noveler.domain.repositories.base_repository import IRepository
    from noveler.domain.repositories.character_repository import CharacterRepository
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.foreshadowing_repository import ForeshadowingRepository
    from noveler.domain.repositories.plot_repository import PlotRepository
    from noveler.domain.repositories.project_repository import ProjectRepository
    from noveler.domain.repositories.quality_check_repository import QualityCheckRepository
    from noveler.domain.repositories.scene_repository import SceneRepository

TEntity = TypeVar("TEntity")


class IRepositoryFactoryProtocol(Protocol):
    """リポジトリファクトリーProtocol

    DDDに準拠したリポジトリインスタンス生成抽象化。
    Application層からの依存注入契約を定義。
    循環依存を避けるためTYPE_CHECKINGで型ヒントを分離。
    """

    def create_episode_repository(self) -> "EpisodeRepository":
        """エピソードリポジトリ生成

        Returns:
            EpisodeRepository: エピソードリポジトリインスタンス
        """
        ...

    def create_plot_repository(self) -> "PlotRepository":
        """プロットリポジトリ生成

        Returns:
            PlotRepository: プロットリポジトリインスタンス
        """
        ...

    def create_project_repository(self) -> "ProjectRepository":
        """プロジェクトリポジトリ生成

        Returns:
            ProjectRepository: プロジェクトリポジトリインスタンス
        """
        ...

    def create_character_repository(self) -> "CharacterRepository":
        """キャラクターリポジトリ生成

        Returns:
            CharacterRepository: キャラクターリポジトリインスタンス
        """
        ...

    def create_foreshadowing_repository(self) -> "ForeshadowingRepository":
        """伏線リポジトリ生成

        Returns:
            ForeshadowingRepository: 伏線リポジトリインスタンス
        """
        ...

    def create_scene_repository(self) -> "SceneRepository":
        """シーンリポジトリ生成

        Returns:
            SceneRepository: シーンリポジトリインスタンス
        """
        ...

    def create_a31_checklist_repository(self) -> "A31ChecklistRepository":
        """A31チェックリストリポジトリ生成

        Returns:
            A31ChecklistRepository: A31チェックリストリポジトリインスタンス
        """
        ...

    def create_quality_check_repository(self) -> "QualityCheckRepository":
        """品質チェックリポジトリ生成

        Returns:
            QualityCheckRepository: 品質チェックリポジトリインスタンス
        """
        ...

    def create_repository(self, repository_type: type[TEntity]) -> "IRepository[TEntity, Any]":
        """指定型のリポジトリ生成（汎用メソッド）

        Args:
            repository_type: リポジトリが扱うエンティティ型

        Returns:
            IRepository: リポジトリ実装
        """
        ...
