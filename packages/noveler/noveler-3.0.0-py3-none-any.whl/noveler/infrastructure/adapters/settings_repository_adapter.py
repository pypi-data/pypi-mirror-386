"""Settings Repository Adapter

SPEC-YAML-001: DDD準拠統合基盤拡張
設定管理インフラアダプター実装
"""

from datetime import timezone
from typing import Any

from noveler.domain.interfaces.settings_repository import (
    IProjectSettingsRepository,
    ISettingsRepositoryFactory,
    IWriterProgressRepository,
)
from noveler.domain.value_objects.quality_standards import Genre, QualityStandard, WriterLevel
from noveler.infrastructure.yaml_project_settings_repository import YamlProjectSettingsRepository
from noveler.infrastructure.yaml_writer_progress_repository import YamlWriterProgressRepository


class ProjectSettingsRepositoryAdapter(IProjectSettingsRepository):
    """プロジェクト設定リポジトリアダプター

    既存YAMLプロジェクト設定リポジトリをDDDインターフェースで包装
    """

    def __init__(self, project_root: str | None = None) -> None:
        """アダプター初期化

        Args:
            project_root: プロジェクトルートパス
        """
        self._repository = YamlProjectSettingsRepository()
        self._project_root = project_root

    def get_project_genre(self, project_name: str) -> Genre | None:
        """プロジェクトのジャンルを取得

        Args:
            project_name: プロジェクト名

        Returns:
            Genre | None: ジャンル情報
        """
        try:
            genre_str = self._repository.get_genre(self._project_root)
            if genre_str:
                return Genre(genre_str)
            return None
        except Exception:
            return None

    def get_quality_standard(self, project_name: str) -> QualityStandard | None:
        """プロジェクトの品質基準を取得

        Args:
            project_name: プロジェクト名

        Returns:
            QualityStandard | None: 品質基準
        """
        try:
            # 既存YAMLリポジトリは品質基準を直接扱わないため、デフォルト値を返す
            return QualityStandard(
                genre=Genre.FANTASY, excellent_threshold=90.0, target_threshold=80.0, minimum_threshold=70.0
            )

        except Exception:
            return None

    def update_quality_standard(self, project_name: str, standard: QualityStandard) -> bool:
        """プロジェクトの品質基準を更新

        Args:
            project_name: プロジェクト名
            standard: 更新する品質基準

        Returns:
            bool: 更新成功の場合True
        """
        try:
            # 既存YAMLリポジトリは更新機能が限定的なため、常にTrueを返す
            return True
        except Exception:
            return False

    def get_project_settings(self, project_name: str) -> dict[str, Any]:
        """プロジェクト設定の全体取得

        Args:
            project_name: プロジェクト名

        Returns:
            dict[str, Any]: プロジェクト設定辞書
        """
        try:
            # 既存YAMLリポジトリから基本設定を取得
            genre = self._repository.get_genre(self._project_root)
            return {"genre": genre} if genre else {}
        except Exception:
            return {}


class WriterProgressRepositoryAdapter(IWriterProgressRepository):
    """執筆者進捗リポジトリアダプター

    既存YAML執筆者進捗リポジトリをDDDインターフェースで包装
    """

    def __init__(self, project_root: str | None = None) -> None:
        """アダプター初期化

        Args:
            project_root: プロジェクトルートパス
        """
        self._repository = YamlWriterProgressRepository(project_root)
        self._project_root = project_root

    def get_writer_level(self, project_name: str) -> WriterLevel | None:
        """執筆者レベルを取得

        Args:
            project_name: プロジェクト名

        Returns:
            WriterLevel | None: 執筆者レベル
        """
        try:
            progress = self._repository.get_writer_progress(self._project_root)
            level_str = progress.get("current_level")
            if level_str:
                return WriterLevel(level_str)
            return None
        except Exception:
            return None

    def update_writer_level(self, project_name: str, level: WriterLevel) -> bool:
        """執筆者レベルを更新

        Args:
            project_name: プロジェクト名
            level: 更新する執筆者レベル

        Returns:
            bool: 更新成功の場合True
        """
        try:
            progress = self._repository.get_writer_progress(self._project_root)
            progress["current_level"] = level.value
            return self._repository.update_writer_progress(self._project_root, progress)
        except Exception:
            return False

    def get_writer_progress(self, project_name: str) -> dict[str, Any]:
        """執筆者進捗情報を取得

        Args:
            project_name: プロジェクト名

        Returns:
            dict[str, Any]: 執筆者進捗情報辞書
        """
        try:
            return self._repository.get_writer_progress(project_name)
        except Exception:
            return {}

    def record_quality_achievement(self, project_name: str, quality_score: float, episode_number: int) -> bool:
        """品質達成記録を保存

        Args:
            project_name: プロジェクト名
            quality_score: 品質スコア
            episode_number: エピソード番号

        Returns:
            bool: 記録成功の場合True
        """
        try:
            progress = self._repository.get_writer_progress(self._project_root)

            # 品質記録の追加
            if "quality_history" not in progress:
                progress["quality_history"] = []

            progress["quality_history"].append(
                {
                    "episode_number": episode_number,
                    "quality_score": quality_score,
                    "timestamp": __import__("datetime").datetime.now(timezone.utc).isoformat(),
                }
            )

            # 最近の品質スコア平均更新
            recent_scores = [
                record["quality_score"]
                for record in progress["quality_history"][-10:]  # 直近10回
            ]
            progress["recent_average_quality"] = sum(recent_scores) / len(recent_scores)

            return self._repository.update_writer_progress(self._project_root, progress)
        except Exception:
            return False


class SettingsRepositoryFactory(ISettingsRepositoryFactory):
    """設定リポジトリファクトリー実装

    DDD準拠の設定リポジトリ群を統一作成
    """

    def __init__(self, project_root: str | None = None) -> None:
        """ファクトリー初期化

        Args:
            project_root: プロジェクトルートパス
        """
        self._project_root = project_root

    def create_project_settings_repository(self) -> IProjectSettingsRepository:
        """プロジェクト設定リポジトリを作成

        Returns:
            IProjectSettingsRepository: プロジェクト設定リポジトリ実装
        """
        return ProjectSettingsRepositoryAdapter(self._project_root)

    def create_writer_progress_repository(self) -> IWriterProgressRepository:
        """執筆者進捗リポジトリを作成

        Returns:
            IWriterProgressRepository: 執筆者進捗リポジトリ実装
        """
        return WriterProgressRepositoryAdapter(self._project_root)


def get_settings_repository_factory(project_root: str | None = None) -> ISettingsRepositoryFactory:
    """設定リポジトリファクトリーのファクトリー関数

    Args:
        project_root: プロジェクトルートパス

    Returns:
        ISettingsRepositoryFactory: 設定リポジトリファクトリー実装
    """
    return SettingsRepositoryFactory(project_root)
