#!/usr/bin/env python3
"""話数管理同期ユースケース
話数管理.yaml自動同期機能のアプリケーション層
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from noveler.domain.interfaces.console_service_protocol import IConsoleService
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService
    from noveler.domain.interfaces.path_service_protocol import IPathService
    from noveler.infrastructure.unit_of_work import IUnitOfWork

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.value_objects.episode_completion_data import EpisodeCompletionData
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.sync_result import SyncResult
from noveler.infrastructure.di.container import container

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass
class EpisodeManagementSyncCommand:
    """話数管理同期コマンド"""

    project_name: str
    episode_number: int
    completion_status: str
    quality_score: float
    quality_grade: str
    word_count: int
    revision_count: int
    completion_date: datetime | None = None
    quality_check_results: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """デフォルト値の設定"""
        if self.completion_date is None:
            self.completion_date = project_now().datetime
        if self.quality_check_results is None:
            self.quality_check_results = {}


@dataclass
class EpisodeManagementSyncResult:
    """話数管理同期結果"""

    success: bool
    updated_fields: list[str]
    error_message: str | None = None
    backup_created: bool = False
    statistics: dict[str, Any] | None = None

    @classmethod
    def from_sync_result(cls, sync_result: SyncResult, statistics: dict[str, Any]) -> "EpisodeManagementSyncResult":
        """SyncResultから変換"""
        return cls(
            success=sync_result.success,
            updated_fields=sync_result.updated_fields,
            error_message=sync_result.error_message,
            backup_created=sync_result.backup_created,
            statistics=statistics,
        )


class EpisodeManagementSyncUseCase(AbstractUseCase[EpisodeManagementSyncCommand, EpisodeManagementSyncResult]):
    """話数管理同期ユースケース"""

    def __init__(self,
        logger_service: "ILoggerService" = None,
        unit_of_work: "IUnitOfWork" = None,
        console_service: Optional["IConsoleService"] = None,
        path_service: Optional["IPathService"] = None,
        sync_service = None,
        **kwargs) -> None:
        """初期化"""
        # 基底クラス初期化（共通サービス）
        super().__init__(console_service=console_service, path_service=path_service, **kwargs)
        # B20準拠: 標準DIサービス
        self._logger_service = logger_service
        self._unit_of_work = unit_of_work


        self.sync_service = sync_service

    def execute(self, command: EpisodeManagementSyncCommand) -> EpisodeManagementSyncResult:
        """話数管理同期を実行"""
        try:
            # コマンドをドメインオブジェクトに変換
            completion_data: dict[str, Any] = EpisodeCompletionData(
                project_name=command.project_name,
                episode_number=command.episode_number,
                completion_status=command.completion_status,
                quality_score=command.quality_score,
                quality_grade=command.quality_grade,
                word_count=command.word_count,
                revision_count=command.revision_count,
                completion_date=command.completion_date,
                quality_check_results=command.quality_check_results,
            )

            # 同期を実行
            sync_result = self.sync_service.sync_episode_completion(completion_data)

            # 統計情報を取得(同期が成功した場合)
            statistics = None
            if sync_result.success:
                statistics = self._get_updated_statistics(command.project_name)

            return EpisodeManagementSyncResult.from_sync_result(sync_result, statistics)

        except Exception as e:
            return EpisodeManagementSyncResult(
                success=False,
                updated_fields=[],
                error_message=f"ユースケース実行中にエラーが発生しました: {e!s}",
                backup_created=False,
            )

    def _get_updated_statistics(self, project_name: str) -> dict[str, Any]:
        """更新された統計情報を取得"""
        try:
            # 話数管理.yamlを読み込んで統計情報を取得
            yaml_handler = container.get("yaml_handler")
            yaml_path = self.sync_service._get_episode_management_yaml_path(project_name)

            if yaml_path.exists():
                yaml_data: dict[str, Any] = yaml_handler.load_yaml(str(yaml_path))
                return self.sync_service.calculate_statistics(yaml_data)

        except Exception as e:
            self.logger.warning("話数管理ファイルの統計計算でエラー: %s", e)

        return {}
