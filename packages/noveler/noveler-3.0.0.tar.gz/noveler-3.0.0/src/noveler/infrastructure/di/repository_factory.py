"""Infrastructure.di.repository_factory
Where: Infrastructure module providing repository factory helpers.
What: Instantiates repository implementations based on configuration and context.
Why: Keeps repository creation logic encapsulated and adaptable.
"""

from __future__ import annotations

"""リポジトリファクトリ - B20準拠依存性注入実装

B20_Claude_Code開発作業指示書準拠:
- Repository パターン統一実装
- Imperative Shell層での副作用局所化
- 外部依存関係の抽象化
"""


import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

from noveler.infrastructure.unit_of_work import UnitOfWork

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service import ILoggerService
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.project_repository import ProjectRepository


from noveler.domain.interfaces.i_path_service import IPathService


class RepositoryFactory:
    """リポジトリファクトリ - B20準拠実装

    機能:
    - Infrastructure層での具象実装提供
    - Imperative Shell パターン適用
    - 外部システムとの境界管理

    参照実装:
    - ___code-master/src/domain/repositories.py
    - Repository パターンによる疎結合設計
    """

    def __init__(self, project_root: Path | None = None, path_service: IPathService | None = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス
            path_service: パスサービス（Noneの場合は自動生成）
        """
        self._project_root = project_root or Path.cwd()

        # IPathServiceインターフェースを使用
        if path_service is None:
            from noveler.infrastructure.adapters.path_service_adapter import create_path_service

            path_service = create_path_service(self._project_root)

        self._path_service = path_service
        self._repositories = {}  # キャッシュ用  # キャッシュ用

    def get_episode_repository(self) -> EpisodeRepository:
        """エピソードリポジトリを取得

        Imperative Shell実装:
        - ファイルI/O副作用をShell層に局所化
        - Domain層は純粋なインターフェースのみ依存

        Returns:
            EpisodeRepository: エピソードリポジトリ
        """
        if "episode" not in self._repositories:
            from noveler.infrastructure.repositories.yaml_episode_repository import YamlEpisodeRepository

            self._repositories["episode"] = YamlEpisodeRepository(self._project_root, self._path_service)

        return self._repositories["episode"]

    def get_project_repository(self) -> ProjectRepository:
        """プロジェクトリポジトリを取得

        Returns:
            ProjectRepository: プロジェクトリポジトリ
        """
        if "project" not in self._repositories:
            from noveler.infrastructure.repositories.yaml_project_repository import YamlProjectRepository

            self._repositories["project"] = YamlProjectRepository(base_path=self._project_root)

        return self._repositories["project"]

    def get_logger_service(self) -> ILoggerService:
        """ロガーサービスを取得

        Functional Core対応:
        - ログ出力はShell層で実行
        - Core層は構造化データのみ返却

        Returns:
            ILoggerService: ロガーサービス
        """
        if "logger" not in self._repositories:
            from noveler.infrastructure.adapters.domain_logger_adapter import DomainLoggerAdapter

            self._repositories["logger"] = DomainLoggerAdapter()

        return self._repositories["logger"]

    def get_unit_of_work(self) -> UnitOfWork:
        """Unit of Workを取得 - B20準拠拡張版

        B20準拠トランザクション管理:
        - ___code-master/src/infrastructure/uow.py パターン適用
        - 複数集約の整合性保証
        - 拡張リポジトリ対応

        Returns:
            UnitOfWork: Unit of Work
        """
        if "uow" not in self._repositories:
            # オプショナルリポジトリの取得（エラーを無視）
            character_repo = None
            config_repo = None
            plot_repo = None

            with contextlib.suppress(KeyError, ImportError, AttributeError):
                character_repo = self._get_character_repository()

            with contextlib.suppress(KeyError, ImportError, AttributeError):
                config_repo = self._get_configuration_repository()

            with contextlib.suppress(KeyError, ImportError, AttributeError):
                plot_repo = self._get_plot_repository()

            backup_repo = None
            with contextlib.suppress(KeyError, ImportError, AttributeError):
                backup_repo = self._get_backup_repository()

            self._repositories["uow"] = UnitOfWork(
                episode_repository=self.get_episode_repository(),
                project_repository=self.get_project_repository(),
                character_repository=character_repo,
                configuration_repository=config_repo,
                plot_repository=plot_repo,
                backup_repository=backup_repo,
            )

        return self._repositories["uow"]

    def _get_character_repository(self) -> object:
        """キャラクターリポジトリを取得（内部用）"""
        if "character" not in self._repositories:
            from noveler.infrastructure.repositories.yaml_character_repository import YamlCharacterRepository

            self._repositories["character"] = YamlCharacterRepository(base_path=self._project_root)
        return self._repositories["character"]

    def _get_configuration_repository(self) -> object:
        """設定リポジトリを取得（内部用）"""
        if "configuration" not in self._repositories:
            from noveler.infrastructure.repositories.yaml_configuration_repository import YamlConfigurationRepository

            self._repositories["configuration"] = YamlConfigurationRepository(self._path_service)
        return self._repositories["configuration"]

    def _get_plot_repository(self) -> object:
        """プロットリポジトリを取得（内部用）"""
        if "plot" not in self._repositories:
            from noveler.infrastructure.repositories.yaml_plot_repository import YamlPlotRepository

            self._repositories["plot"] = YamlPlotRepository(base_path=self._project_root)
        return self._repositories["plot"]

    def _get_backup_repository(self) -> object:
        """バックアップリポジトリを取得（内部用）"""
        if "backup" not in self._repositories:
            from noveler.infrastructure.repositories.file_system_backup_repository import FileSystemBackupRepository

            backup_root = self._project_root / "backups"
            self._repositories["backup"] = FileSystemBackupRepository(backup_root=backup_root)
        return self._repositories["backup"]


def create_repository_factory(
    project_root: Path | None = None, path_service: IPathService | None = None
) -> RepositoryFactory:
    """リポジトリファクトリを作成

    ファクトリ関数によるシンプルな生成パターン
    テスト互換性のためpath_serviceパラメータを追加

    Args:
        project_root: プロジェクトルートパス
        path_service: パスサービス（テスト用、Noneの場合は自動生成）

    Returns:
        RepositoryFactory: 設定済みファクトリ
    """
    return RepositoryFactory(project_root, path_service)
