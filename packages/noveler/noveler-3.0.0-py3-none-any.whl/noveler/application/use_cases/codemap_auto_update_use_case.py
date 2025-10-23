#!/usr/bin/env python3
"""CODEMAP自動更新ユースケース

仕様書: SPEC-CODEMAP-AUTO-UPDATE-001
"""

import time
from dataclasses import dataclass
from typing import Protocol

from noveler.domain.entities.codemap_entity import CodeMapEntity
from noveler.domain.services.codemap_synchronization_service import CodeMapSynchronizationService
from noveler.domain.value_objects.commit_information import CommitInformation


# DDD準拠：インフラ層依存解消のためのプロトコル定義
class CodeMapRepositoryProtocol(Protocol):
    """CODEMAPリポジトリプロトコル"""

    def load_codemap(self) -> CodeMapEntity | None:
        """CODEMAPを読み込み"""
        ...

    def save_codemap(self, codemap: CodeMapEntity) -> bool:
        """CODEMAPを保存"""
        ...

    def create_backup(self) -> str:
        """バックアップ作成"""
        ...

    def restore_from_backup(self, backup_id: str) -> bool:
        """バックアップから復元"""
        ...


class GitInformationAdapterProtocol(Protocol):
    """Git情報取得アダプタープロトコル"""

    def get_latest_commit_info(self) -> CommitInformation | None:
        """最新コミット情報取得"""
        ...

    def is_git_repository(self) -> bool:
        """Gitリポジトリかチェック"""
        ...


@dataclass
class CodeMapAutoUpdateRequest:
    """CODEMAP自動更新リクエスト"""

    force_update: bool = False
    create_backup: bool = True
    validate_result: bool = True


@dataclass
class CodeMapAutoUpdateResponse:
    """CODEMAP自動更新レスポンス"""

    success: bool
    updated: bool = False
    backup_id: str | None = None
    validation_errors: list[str] = None
    commit_hash: str | None = None
    changes_summary: str | None = None
    error_message: str | None = None
    execution_time_ms: float = 0.0

    def __post_init__(self) -> None:
        if self.validation_errors is None:
            self.validation_errors = []


class CodeMapAutoUpdateUseCase:
    """CODEMAP自動更新ユースケース

    REQ-1: Git コミット発生時のCODEMAP自動更新機能
    REQ-2: バックアップ・ロールバック機能
    REQ-3: 検証・整合性チェック機能
    """

    def __init__(
        self,
        codemap_repository: CodeMapRepositoryProtocol,
        git_adapter: GitInformationAdapterProtocol,
        sync_service: CodeMapSynchronizationService,
    ) -> None:
        """初期化

        Args:
            codemap_repository: CODEMAPリポジトリ
            git_adapter: Git情報取得アダプター
            sync_service: CODEMAP同期サービス
        """
        self._codemap_repository = codemap_repository
        self._git_adapter = git_adapter
        self._sync_service = sync_service

    def execute(self, request: CodeMapAutoUpdateRequest) -> CodeMapAutoUpdateResponse:
        """CODEMAP自動更新実行

        Args:
            request: 更新リクエスト

        Returns:
            CodeMapAutoUpdateResponse: 更新結果
        """

        start_time = time.time()

        def _elapsed_ms() -> float:
            return max((time.time() - start_time) * 1000, 0.0)

        try:
            # 1. 前提条件チェック
            if not self._git_adapter.is_git_repository():
                return CodeMapAutoUpdateResponse(
                    success=False,
                    error_message="Not a Git repository",
                    execution_time_ms=_elapsed_ms(),
                )

            # 2. 現在のCODEMAP読み込み
            current_codemap = self._codemap_repository.load_codemap()
            if not current_codemap:
                return CodeMapAutoUpdateResponse(
                    success=False,
                    error_message="Failed to load current CODEMAP",
                    execution_time_ms=_elapsed_ms(),
                )

            # 3. 最新コミット情報取得
            commit_info = self._git_adapter.get_latest_commit_info()
            if not commit_info:
                return CodeMapAutoUpdateResponse(
                    success=False,
                    error_message="Failed to get commit information",
                    execution_time_ms=_elapsed_ms(),
                )

            # 4. 更新が必要かチェック
            if not request.force_update and not self._needs_update(current_codemap, commit_info):
                return CodeMapAutoUpdateResponse(
                    success=True,
                    updated=False,
                    commit_hash=commit_info.short_hash,
                    changes_summary="No update needed",
                    execution_time_ms=_elapsed_ms(),
                )

            # 5. バックアップ作成
            backup_id = None
            if request.create_backup:
                backup_id = self._codemap_repository.create_backup()
                if not backup_id:
                    return CodeMapAutoUpdateResponse(
                        success=False,
                        error_message="Failed to create backup",
                        execution_time_ms=_elapsed_ms(),
                    )

            # 6. CODEMAP同期実行
            try:
                updated_codemap = self._sync_service.synchronize_with_commit(current_codemap, commit_info)

            except Exception as e:
                return CodeMapAutoUpdateResponse(
                    success=False,
                    error_message=f"Synchronization failed: {e!s}",
                    backup_id=backup_id,
                    execution_time_ms=_elapsed_ms(),
                )

            # 7. 結果検証
            validation_errors = []
            if request.validate_result:
                validation_errors = self._sync_service.validate_synchronization_result(updated_codemap)
                if validation_errors:
                    # バックアップから復元
                    if backup_id:
                        self._codemap_repository.restore_from_backup(backup_id)
                    return CodeMapAutoUpdateResponse(
                        success=False,
                        validation_errors=validation_errors,
                        error_message="Validation failed, restored from backup",
                        backup_id=backup_id,
                        execution_time_ms=_elapsed_ms(),
                    )

            # 8. CODEMAP保存
            if not self._codemap_repository.save_codemap(updated_codemap):
                # バックアップから復元
                if backup_id:
                    self._codemap_repository.restore_from_backup(backup_id)
                return CodeMapAutoUpdateResponse(
                    success=False,
                    error_message="Failed to save updated CODEMAP, restored from backup",
                    backup_id=backup_id,
                    execution_time_ms=_elapsed_ms(),
                )

            # 9. 変更影響の分析
            impact = self._sync_service.calculate_synchronization_impact(current_codemap, updated_codemap)

            changes_summary = self._create_changes_summary(impact, commit_info)

            return CodeMapAutoUpdateResponse(
                success=True,
                updated=True,
                backup_id=backup_id,
                validation_errors=[],
                commit_hash=commit_info.short_hash,
                changes_summary=changes_summary,
                execution_time_ms=_elapsed_ms(),
            )

        except Exception as e:
            return CodeMapAutoUpdateResponse(
                success=False,
                error_message=f"Unexpected error: {e!s}",
                execution_time_ms=_elapsed_ms(),
            )

    def _needs_update(self, codemap: CodeMapEntity, commit_info: CommitInformation) -> bool:
        """更新が必要かを判定

        Args:
            codemap: 現在のCODEMAP
            commit_info: 最新コミット情報

        Returns:
            bool: 更新が必要な場合True
        """
        # 既に同じコミットで更新済みかチェック
        if codemap.metadata.commit == commit_info.short_hash:
            return False

        # 実装に関連する変更があるかチェック
        if commit_info.is_implementation_commit():
            return True

        # ドキュメント更新でもCODEMAPに関連する場合は更新
        if commit_info.is_documentation_update():
            codemap_related_files = ["CODEMAP", "README", "docs/"]
            if any(
                pattern in file_path for pattern in codemap_related_files for file_path in commit_info.changed_files
            ):
                return True

        # アーキテクチャに影響する変更があるかチェック
        affected_layers = commit_info.get_affected_architecture_layers()
        return bool(affected_layers)

    def _create_changes_summary(self, impact: dict, commit_info: CommitInformation) -> str:
        """変更サマリの作成

        Args:
            impact: 変更影響分析結果
            commit_info: コミット情報

        Returns:
            str: 変更サマリ
        """
        summary_parts = [f"Updated from commit {commit_info.short_hash}"]

        if impact["issues_resolved"] > 0:
            summary_parts.append(f"{impact['issues_resolved']} issues resolved")

        if impact["completion_rate_change"] > 0:
            summary_parts.append(f"completion rate improved by {impact['completion_rate_change']:.1f}%")

        script_paths = [self._map_to_scripts_path(path) for path in commit_info.changed_files]
        if script_paths:
            summary_parts.append(f"affected files: {', '.join(script_paths)}")

        return "; ".join(summary_parts)

    @staticmethod
    def _map_to_scripts_path(file_path: str) -> str:
        """Convert repository paths to script resource paths for reporting."""
        if file_path.startswith("noveler/"):
            return file_path.replace("noveler", "scripts", 1)
        return file_path

    def get_update_status(self) -> dict:
        """更新システムの状態取得

        Returns:
            dict: システム状態情報
        """
        try:
            codemap = self._codemap_repository.load_codemap()
            latest_commit = self._git_adapter.get_latest_commit_info()

            return {
                "codemap_available": codemap is not None,
                "git_repository": self._git_adapter.is_git_repository(),
                "current_commit": codemap.metadata.commit if codemap else None,
                "latest_commit": latest_commit.short_hash if latest_commit else None,
                "needs_update": self._needs_update(codemap, latest_commit) if codemap and latest_commit else False,
                "completion_rate": codemap.get_completion_rate() if codemap else 0.0,
            }
        except Exception as e:
            return {"error": str(e), "codemap_available": False, "git_repository": False}
