"""Settings Repository Interface

SPEC-YAML-001: DDD準拠統合基盤拡張
設定管理のドメインインターフェース定義
"""

from abc import ABC, abstractmethod
from typing import Any

from noveler.domain.value_objects.quality_standards import Genre, QualityStandard, WriterLevel


class IProjectSettingsRepository(ABC):
    """プロジェクト設定リポジトリインターフェース

    DDD原則に基づき、インフラ層への直接依存を排除し
    抽象インターフェースを通じた依存性逆転を実現
    """

    @abstractmethod
    def get_project_genre(self, project_name: str) -> Genre | None:
        """プロジェクトのジャンルを取得

        Args:
            project_name: プロジェクト名

        Returns:
            Genre | None: ジャンル情報（見つからない場合はNone）
        """

    @abstractmethod
    def get_quality_standard(self, project_name: str) -> QualityStandard | None:
        """プロジェクトの品質基準を取得

        Args:
            project_name: プロジェクト名

        Returns:
            QualityStandard | None: 品質基準（見つからない場合はNone）
        """

    @abstractmethod
    def update_quality_standard(self, project_name: str, standard: QualityStandard) -> bool:
        """プロジェクトの品質基準を更新

        Args:
            project_name: プロジェクト名
            standard: 更新する品質基準

        Returns:
            bool: 更新成功の場合True
        """

    @abstractmethod
    def get_project_settings(self, project_name: str) -> dict[str, Any]:
        """プロジェクト設定の全体取得

        Args:
            project_name: プロジェクト名

        Returns:
            dict[str, Any]: プロジェクト設定辞書
        """


class IWriterProgressRepository(ABC):
    """執筆者進捗リポジトリインターフェース

    執筆者のレベルと進捗情報管理のための
    ドメイン層インターフェース
    """

    @abstractmethod
    def get_writer_level(self, project_name: str) -> WriterLevel | None:
        """執筆者レベルを取得

        Args:
            project_name: プロジェクト名

        Returns:
            WriterLevel | None: 執筆者レベル（見つからない場合はNone）
        """

    @abstractmethod
    def update_writer_level(self, project_name: str, level: WriterLevel) -> bool:
        """執筆者レベルを更新

        Args:
            project_name: プロジェクト名
            level: 更新する執筆者レベル

        Returns:
            bool: 更新成功の場合True
        """

    @abstractmethod
    def get_writer_progress(self, project_name: str) -> dict[str, Any]:
        """執筆者進捗情報を取得

        Args:
            project_name: プロジェクト名

        Returns:
            dict[str, Any]: 執筆者進捗情報辞書
        """

    @abstractmethod
    def record_quality_achievement(self, project_name: str, quality_score: float, episode_number: int) -> bool:
        """品質達成記録を保存

        Args:
            project_name: プロジェクト名
            quality_score: 品質スコア
            episode_number: エピソード番号

        Returns:
            bool: 記録成功の場合True
        """


class ISettingsRepositoryFactory(ABC):
    """設定リポジトリファクトリーインターフェース

    各種設定リポジトリの統一的な作成インターフェース
    """

    @abstractmethod
    def create_project_settings_repository(self) -> IProjectSettingsRepository:
        """プロジェクト設定リポジトリを作成

        Returns:
            IProjectSettingsRepository: プロジェクト設定リポジトリ実装
        """

    @abstractmethod
    def create_writer_progress_repository(self) -> IWriterProgressRepository:
        """執筆者進捗リポジトリを作成

        Returns:
            IWriterProgressRepository: 執筆者進捗リポジトリ実装
        """
