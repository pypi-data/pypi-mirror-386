"""Application.use_cases.unified_backup_management_use_case
Where: Application use case coordinating unified backup operations.
What: Manages backup creation, verification, and restoration through domain services.
Why: Centralises backup workflows so teams maintain data safety consistently.
"""

from __future__ import annotations


from dataclasses import dataclass
from typing import TYPE_CHECKING

from noveler.domain.value_objects.project_time import project_now
from noveler.noveler.domain.entities.backup_session import BackupSession
from noveler.noveler.domain.repositories.backup_repository import BackupRepository
from noveler.noveler.domain.services.backup_analysis_service import BackupAnalysisService
from noveler.noveler.domain.services.backup_migration_service import BackupMigrationService
from noveler.noveler.domain.value_objects.backup_strategy import BackupStrategy
from noveler.noveler.domain.value_objects.backup_type import BackupType
from noveler.noveler.infrastructure.adapters.console_service_adapter import ConsoleServiceProtocol
from noveler.noveler.infrastructure.adapters.logger_service_adapter import LoggerServiceProtocol
from noveler.noveler.infrastructure.adapters.path_service_adapter import PathServiceProtocol
from noveler.noveler.infrastructure.unit_of_work.backup_unit_of_work import BackupUnitOfWork

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class UnifiedBackupRequest:
    """統一バックアップリクエスト - B20準拠Value Object"""

    operation_type: str  # 'analyze' | 'migrate' | 'cleanup' | 'create'
    dry_run: bool = True
    backup_type: BackupType | None = None
    source_paths: list[Path] = None
    target_strategy: BackupStrategy | None = None

    def __post_init__(self) -> None:
        if self.source_paths is None:
            self.source_paths = []


@dataclass
class UnifiedBackupResponse:
    """統一バックアップレスポンス - B20準拠Value Object"""

    session_id: str
    operation_completed: bool
    analysis_summary: dict[str, any]
    migration_results: list[str]
    errors: list[str]
    recommendations: list[str]

    def __post_init__(self) -> None:
        if not self.analysis_summary:
            self.analysis_summary = {}
        if not self.migration_results:
            self.migration_results = []
        if not self.errors:
            self.errors = []
        if not self.recommendations:
            self.recommendations = []


class UnifiedBackupManagementUseCase:
    """統一バックアップ管理ユースケース

    B20準拠実装:
    - FC/IS: Functional Core（純粋なロジック）+ Imperative Shell（I/O）
    - DDD: ドメインサービス調整 + Repository パターン
    - Unit of Work: トランザクション境界管理
    """

    def __init__(
        self,
        *,  # B20準拠: keyword-only引数
        backup_uow: BackupUnitOfWork,
        backup_repository: BackupRepository,
        analysis_service: BackupAnalysisService,
        migration_service: BackupMigrationService,
        console_service: ConsoleServiceProtocol,
        logger_service: LoggerServiceProtocol,
        path_service: PathServiceProtocol,
    ) -> None:
        """DI構築 - B20準拠インジェクション"""
        self._backup_uow = backup_uow
        self._backup_repository = backup_repository
        self._analysis_service = analysis_service
        self._migration_service = migration_service
        self._console_service = console_service
        self._logger_service = logger_service
        self._path_service = path_service

    def execute(self, request: UnifiedBackupRequest) -> UnifiedBackupResponse:
        """メインエクゼキューター - B20準拠Unit of Workパターン"""
        session_id = self._generate_session_id()

        try:
            with self._backup_uow:
                # Session開始
                session = self._create_backup_session(session_id, request)

                # Operation実行（FC/ISパターン）
                response = self._execute_operation(session, request)

                # 成功時コミット
                if not request.dry_run and response.operation_completed:
                    self._backup_uow.commit()
                    self._logger_service.info(f"バックアップ操作完了: {session_id}")
                else:
                    self._backup_uow.rollback()
                    self._logger_service.info(f"ドライラン完了: {session_id}")

                return response

        except Exception as e:
            self._backup_uow.rollback()
            self._logger_service.error(f"バックアップ操作失敗: {e}")
            return UnifiedBackupResponse(
                session_id=session_id,
                operation_completed=False,
                analysis_summary={},
                migration_results=[],
                errors=[str(e)],
                recommendations=["エラーログを確認し、システム状態をチェックしてください"],
            )

    def _execute_operation(self, session: BackupSession, request: UnifiedBackupRequest) -> UnifiedBackupResponse:
        """操作実行 - Functional Core（純粋関数パターン）"""

        if request.operation_type == "analyze":
            return self._execute_analysis(session, request)
        if request.operation_type == "migrate":
            return self._execute_migration(session, request)
        if request.operation_type == "cleanup":
            return self._execute_cleanup(session, request)
        if request.operation_type == "create":
            return self._execute_creation(session, request)
        msg = f"未対応オペレーション: {request.operation_type}"
        raise ValueError(msg)

    def _execute_analysis(self, session: BackupSession, request: UnifiedBackupRequest) -> UnifiedBackupResponse:
        """分析実行 - Functional Core"""
        self._console_service.print("🔍 バックアップ状況分析開始...")

        # カオス状態の分析
        chaos_analysis = self._analysis_service.analyze_chaos_state(self._path_service.get_project_root())

        # 統計情報生成
        statistics = self._analysis_service.generate_statistics(chaos_analysis)

        # 推奨事項生成
        recommendations = self._analysis_service.generate_recommendations(statistics)

        self._console_service.print(f"✅ 分析完了: {len(chaos_analysis.backup_folders)}箇所検出")

        return UnifiedBackupResponse(
            session_id=session.session_id,
            operation_completed=True,
            analysis_summary={
                "total_backup_folders": len(chaos_analysis.backup_folders),
                "total_size_mb": statistics.total_size_mb,
                "oldest_backup": statistics.oldest_backup_date.isoformat() if statistics.oldest_backup_date else None,
                "newest_backup": statistics.newest_backup_date.isoformat() if statistics.newest_backup_date else None,
                "duplicate_candidates": len(statistics.duplicate_candidates),
            },
            migration_results=[],
            errors=[],
            recommendations=recommendations,
        )

    def _execute_migration(self, session: BackupSession, request: UnifiedBackupRequest) -> UnifiedBackupResponse:
        """移行実行 - Unit of Work管理"""
        self._console_service.print("🔄 バックアップ移行開始...")

        migration_results = []
        errors = []

        try:
            # 移行プランの作成
            migration_plan = self._migration_service.create_migration_plan(
                source_paths=request.source_paths, dry_run=request.dry_run
            )

            # 段階的実行
            for phase in migration_plan.phases:
                self._console_service.print(f"Phase {phase.phase_number}: {phase.description}")

                phase_result = self._migration_service.execute_phase(phase, dry_run=request.dry_run)

                if phase_result.success:
                    migration_results.extend(phase_result.operations)
                else:
                    errors.extend(phase_result.errors)
                    break

            self._console_service.print("✅ 移行完了")

        except Exception as e:
            errors.append(f"移行エラー: {e!s}")
            self._logger_service.error(f"移行失敗: {e}")

        return UnifiedBackupResponse(
            session_id=session.session_id,
            operation_completed=len(errors) == 0,
            analysis_summary={},
            migration_results=migration_results,
            errors=errors,
            recommendations=["移行後は動作確認を実施してください"],
        )

    def _execute_cleanup(self, session: BackupSession, request: UnifiedBackupRequest) -> UnifiedBackupResponse:
        """クリーンアップ実行"""
        self._console_service.print("🧹 バックアップクリーンアップ開始...")

        cleanup_results = self._migration_service.execute_cleanup(dry_run=request.dry_run)

        return UnifiedBackupResponse(
            session_id=session.session_id,
            operation_completed=cleanup_results.success,
            analysis_summary={
                "cleaned_folders": cleanup_results.cleaned_count,
                "reclaimed_space_mb": cleanup_results.reclaimed_space_mb,
            },
            migration_results=cleanup_results.operations,
            errors=cleanup_results.errors,
            recommendations=["定期的なクリーンアップを推奨します"],
        )

    def _execute_creation(self, session: BackupSession, request: UnifiedBackupRequest) -> UnifiedBackupResponse:
        """新規バックアップ作成"""
        if not request.backup_type or not request.target_strategy:
            msg = "バックアップ作成にはtypeとstrategyが必要です"
            raise ValueError(msg)

        self._console_service.print(f"💾 {request.backup_type.value}バックアップ作成中...")

        backup_result = self._backup_repository.create_backup(
            backup_type=request.backup_type, strategy=request.target_strategy, dry_run=request.dry_run
        )

        return UnifiedBackupResponse(
            session_id=session.session_id,
            operation_completed=backup_result.success,
            analysis_summary={
                "backup_path": str(backup_result.backup_path) if backup_result.backup_path else None,
                "backup_size_mb": backup_result.size_mb,
            },
            migration_results=[f"バックアップ作成: {backup_result.backup_path}"],
            errors=backup_result.errors,
            recommendations=["バックアップの整合性を確認してください"],
        )

    def _create_backup_session(self, session_id: str, request: UnifiedBackupRequest) -> BackupSession:
        """バックアップセッション作成 - Domain Entity"""
        return BackupSession(
            session_id=session_id,
            operation_type=request.operation_type,
            started_at=project_now().datetime,
            dry_run=request.dry_run,
        )

    def _generate_session_id(self) -> str:
        """セッションID生成 - Functional Core（純粋関数）"""
        timestamp = project_now().datetime.strftime("%Y%m%d_%H%M%S")
        return f"backup_session_{timestamp}"
