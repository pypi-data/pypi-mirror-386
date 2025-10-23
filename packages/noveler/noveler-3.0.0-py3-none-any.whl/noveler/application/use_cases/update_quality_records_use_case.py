#!/usr/bin/env python3
"""Update quality records use case.

Coordinate business flows at the application layer for quality record updates."""

from dataclasses import dataclass
from pathlib import Path

from noveler.domain.entities.quality_record import QualityRecord
from noveler.domain.exceptions import QualityRecordError
from noveler.domain.repositories.episode_management_repository import EpisodeManagementRepository
from noveler.domain.repositories.quality_record_repository import QualityRecordRepository
from noveler.domain.value_objects.quality_check_result import QualityCheckResult


@dataclass(frozen=True)
class UpdateQualityRecordsRequest:
    """Input payload for updating quality records."""

    project_name: str
    project_path: Path
    quality_result: QualityCheckResult

    def __post_init__(self) -> None:
        if not self.project_name or not self.project_name.strip():
            msg = "Project name cannot be empty"
            raise ValueError(msg)
        if not isinstance(self.project_path, Path):
            msg = "Project path must be a Path object"
            raise TypeError(msg)


@dataclass
class UpdateQualityRecordsResponse:
    """Response returned after updating quality records."""

    success: bool
    error_message: str | None = None
    updated_files: list[str] = None

    def __post_init__(self) -> None:
        if self.updated_files is None:
            object.__setattr__(self, "updated_files", [])

    @classmethod
    def success(cls, updated_files: list[str]) -> "UpdateQualityRecordsResponse":
        """成功レスポンス作成"""
        return cls(success=True, error_message=None, updated_files=updated_files)

    @classmethod
    def failure(cls, error_message: str) -> "UpdateQualityRecordsResponse":
        """失敗レスポンス作成"""
        return cls(success=False, error_message=error_message, updated_files=[])


class UpdateQualityRecordsUseCase:
    """Manage quality record updates and domain events."""

    def __init__(
        self,
        quality_record_repository: QualityRecordRepository,
        episode_management_repository: EpisodeManagementRepository,
    ) -> None:
        """依存性注入によるコンストラクタ"""
        self._quality_record_repository = quality_record_repository
        self._episode_management_repository = episode_management_repository

    def execute(self, request: UpdateQualityRecordsRequest) -> UpdateQualityRecordsResponse:
        """Execute the quality record update workflow.

        Follows DDD principles by delegating business rules to domain entities and abstracting infrastructure concerns.
        """
        try:
            # 1. 既存記録の取得または新規作成
            quality_record = self._get_or_create_quality_record(request.project_name)

            # 2. ドメインエンティティにビジネスルール適用
            try:
                quality_record.add_quality_check_result(request.quality_result, metadata={"source": "quality_check"})
            except QualityRecordError as e:
                return UpdateQualityRecordsResponse.failure(str(e))

            try:
                updated_files = self._update_quality_records(quality_record, request)
            except QualityRecordError as e:
                return UpdateQualityRecordsResponse.failure(str(e))

            # 4. ドメインイベント処理
            self._process_domain_events(quality_record)

            return UpdateQualityRecordsResponse.success(updated_files)

        except Exception as e:
            return UpdateQualityRecordsResponse.failure(f"Unexpected error: {e}")

    def _get_or_create_quality_record(self, project_name: str) -> QualityRecord:
        """Retrieve an existing quality record or create a new one."""
        try:
            existing_record = self._quality_record_repository.find_by_project(project_name)
            if existing_record:
                return existing_record
        except (FileNotFoundError, ValueError):
            # 既存レコードが見つからない、または破損している場合は新しいレコードを作成
            pass
        return QualityRecord(project_name, entries=[])

    def _update_quality_records(
        self, quality_record: QualityRecord, request: UpdateQualityRecordsRequest
    ) -> list[str]:
        """Persist quality records and return updated file names."""
        updated_files = []

        try:
            # 品質記録の永続化
            self._quality_record_repository.save(quality_record)
            updated_files.append("品質記録.yaml")
        except Exception as e:
            msg = f"Record update failed: {e!s}"
            raise QualityRecordError(request.project_name, msg) from e

        try:
            self._episode_management_repository.update(
                project_name=request.project_name,
                episode_number=request.quality_result.episode_number,
                metadata={
                    "overall_score": request.quality_result.overall_score.value,
                    "error_count": request.quality_result.error_count,
                    "warning_count": request.quality_result.warning_count,
                },
            )
            updated_files.append("話数管理.yaml")
        except Exception as exc:
            raise QualityRecordError(request.project_name, str(exc)) from exc

        updated_files.append("改訂履歴.yaml")

        return updated_files

    def _process_domain_events(self, quality_record: QualityRecord) -> None:
        """Process domain events emitted by the quality record."""
        domain_events = quality_record.get_domain_events()

        # 今後の拡張:イベントハンドラーでの通知、ログ出力、分析等
        for event in domain_events:
            if event["type"] == "QualityCheckAdded":
                # 統計更新、通知送信、レポート生成等の副作用
                pass

        # イベントクリア
        quality_record.clear_domain_events()
