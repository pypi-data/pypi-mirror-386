"""Infrastructure.di.use_case_factory
Where: Infrastructure module creating use-case instances via DI.
What: Resolves dependencies for application use cases and returns ready-to-use instances.
Why: Simplifies use-case instantiation while honouring dependency contracts.
"""

from __future__ import annotations

"""ユースケースファクトリ - B20準拠依存性注入パターン

B20_Claude_Code開発作業指示書準拠:
- 依存性注入パターンの統一実装
- Unit of Workパターン統合
- Functional Core / Imperative Shell分離
"""


from typing import TYPE_CHECKING, Protocol

from noveler.application.use_cases.create_episode_use_case import CreateEpisodeUseCase

if TYPE_CHECKING:
    from noveler.application.use_cases.a31_auto_fix_use_case import A31AutoFixUseCase
    from noveler.application.use_cases.a31_batch_auto_fix_use_case import A31BatchAutoFixUseCase
    from noveler.application.use_cases.a31_complete_check_use_case import A31CompleteCheckUseCase
    from noveler.domain.interfaces.logger_service import ILoggerService
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.project_repository import ProjectRepository
    from noveler.infrastructure.unit_of_work import UnitOfWork


class IRepositoryFactory(Protocol):
    """リポジトリファクトリインターフェース"""

    def get_episode_repository(self) -> EpisodeRepository:
        """エピソードリポジトリを取得"""
        ...

    def get_project_repository(self) -> ProjectRepository:
        """プロジェクトリポジトリを取得"""
        ...

    def get_logger_service(self) -> ILoggerService:
        """ロガーサービスを取得"""
        ...

    def get_unit_of_work(self) -> UnitOfWork:
        """Unit of Workを取得"""
        ...


class UseCaseFactory:
    """ユースケースファクトリ - B20準拠DI実装

    機能:
    - 依存性注入による疎結合設計
    - 統一的なユースケース生成
    - Unit of Work統合

    参照実装:
    - ___code-master/src/infrastructure/uow.py
    - ___python-ddd-main/src/modules/bidding/
    """

    def __init__(self, repository_factory: IRepositoryFactory) -> None:
        """初期化

        Args:
            repository_factory: リポジトリファクトリ
        """
        self._repository_factory = repository_factory

    def create_episode_use_case(self) -> CreateEpisodeUseCase:
        """エピソード作成ユースケースを生成

        B20準拠:
        - 依存性注入パターン適用
        - コンストラクタ注入による明示的依存関係

        Returns:
            CreateEpisodeUseCase: 設定済みユースケース
        """
        return CreateEpisodeUseCase(
            episode_repository=self._repository_factory.get_episode_repository(),
            project_repository=self._repository_factory.get_project_repository(),
            logger_service=self._repository_factory.get_logger_service(),
        )

    def create_a31_auto_fix_use_case(self) -> A31AutoFixUseCase:
        """A31自動修正ユースケースを生成

        HIGH優先度違反修正:
        - MISSING_DEPENDENCY_INJECTION解消

        Returns:
            A31AutoFixUseCase: 設定済みユースケース
        """
        from noveler.application.use_cases.a31_auto_fix_use_case import A31AutoFixUseCase

        return A31AutoFixUseCase(
            logger_service=self._repository_factory.get_logger_service(),
            unit_of_work=self._repository_factory.get_unit_of_work(),
        )

    def create_a31_batch_auto_fix_use_case(self) -> A31BatchAutoFixUseCase:
        """A31バッチ自動修正ユースケースを生成

        HIGH優先度違反修正:
        - MISSING_DEPENDENCY_INJECTION解消

        Returns:
            A31BatchAutoFixUseCase: 設定済みユースケース
        """
        from noveler.application.use_cases.a31_batch_auto_fix_use_case import A31BatchAutoFixUseCase

        return A31BatchAutoFixUseCase(
            logger_service=self._repository_factory.get_logger_service(),
            unit_of_work=self._repository_factory.get_unit_of_work(),
        )

    def create_a31_complete_check_use_case(self) -> A31CompleteCheckUseCase:
        """A31完全チェックユースケースを生成

        HIGH優先度違反修正:
        - MISSING_DEPENDENCY_INJECTION解消

        Returns:
            A31CompleteCheckUseCase: 設定済みユースケース
        """
        from noveler.application.use_cases.a31_complete_check_use_case import A31CompleteCheckUseCase

        return A31CompleteCheckUseCase(
            logger_service=self._repository_factory.get_logger_service(),
            unit_of_work=self._repository_factory.get_unit_of_work(),
        )

    def create_backup_use_case(self):
        """バックアップユースケースを生成

        B20準拠:
        - logger_service + unit_of_work注入

        Returns:
            BackupUseCase: 設定済みユースケース
        """
        from noveler.application.use_cases.backup_use_case import BackupUseCase

        return BackupUseCase(
            logger_service=self._repository_factory.get_logger_service(),
            unit_of_work=self._repository_factory.get_unit_of_work(),
        )

    def create_plot_generation_use_case(self):
        """プロット生成ユースケースを生成

        Returns:
            PlotGenerationUseCase: 設定済みユースケース
        """
        from noveler.application.use_cases.plot_generation_use_case import PlotGenerationUseCase

        return PlotGenerationUseCase(
            logger_service=self._repository_factory.get_logger_service(),
            unit_of_work=self._repository_factory.get_unit_of_work(),
        )

    def create_system_doctor_use_case(self):
        """システムドクターユースケースを生成

        Returns:
            SystemDoctorUseCase: 設定済みユースケース
        """
        from noveler.application.use_cases.system_doctor_use_case import SystemDoctorUseCase

        return SystemDoctorUseCase(
            logger_service=self._repository_factory.get_logger_service(),
            unit_of_work=self._repository_factory.get_unit_of_work(),
        )

    def create_quality_check_use_case(self):
        """品質チェックユースケースを生成

        Returns:
            QualityCheckUseCase: 設定済みユースケース
        """
        from noveler.application.use_cases.quality_check_use_case import QualityCheckUseCase

        return QualityCheckUseCase(
            logger_service=self._repository_factory.get_logger_service(),
            unit_of_work=self._repository_factory.get_unit_of_work(),
        )


def create_use_case_factory(repository_factory: IRepositoryFactory) -> UseCaseFactory:
    """ユースケースファクトリを作成

    ファクトリ関数によるシンプルな生成パターン

    Args:
        repository_factory: リポジトリファクトリ

    Returns:
        UseCaseFactory: 設定済みファクトリ
    """
    return UseCaseFactory(repository_factory)
