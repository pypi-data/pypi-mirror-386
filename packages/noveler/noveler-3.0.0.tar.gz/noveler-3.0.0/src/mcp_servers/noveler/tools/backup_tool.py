"""BackupTool実装

SPEC-MCP-BACKUP: MCPバックアップツール統合
"""
import time
from pathlib import Path
from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolIssue,
    ToolRequest,
    ToolResponse,
)
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.repositories.file_system_backup_repository import FileSystemBackupRepository


class BackupTool(MCPToolBase):
    """MCPバックアップツール

    既存のBackupUseCaseを活用してバックアップ操作を提供する。
    4つの基本操作（create/restore/list/delete）をMCP経由で実行可能。
    """

    def __init__(self) -> None:
        """初期化"""
        super().__init__(
            tool_name="backup_management",
            tool_description="ファイル・ディレクトリのバックアップ管理"
        )
        self.logger = get_logger(__name__)

    def get_input_schema(self) -> dict[str, Any]:
        """入力スキーマ定義

        Returns:
            バックアップ操作用の入力スキーマ
        """
        schema = self._get_common_input_schema()

        # バックアップ特有のパラメータを追加
        schema["properties"].update({
            "action": {
                "type": "string",
                "enum": ["create", "restore", "list", "delete"],
                "description": "実行するバックアップ操作"
            },
            "backup_id": {
                "type": "string",
                "description": "バックアップID（restore、delete時）"
            },
            "backup_name": {
                "type": "string",
                "description": "バックアップ名（create時、オプション）"
            },
            "file_path": {
                "type": "string",
                "description": "ファイルパス（create時）"
            },
            "restore_path": {
                "type": "string",
                "description": "復元先パス（restore時、オプション）"
            },
            "filter_pattern": {
                "type": "string",
                "description": "フィルターパターン（list時、オプション）"
            }
        })

        # actionを必須フィールドに追加
        schema["required"].append("action")

        return schema

    def execute(self, request: ToolRequest) -> ToolResponse:
        """バックアップ操作の実行

        Args:
            request: ツールリクエスト

        Returns:
            バックアップ操作結果
        """
        start_time = time.time()

        try:
            # リクエスト検証
            self._validate_request(request)
            action = request.additional_params.get("action")

            # プロジェクトルートの自動検出
            path_service = create_path_service()
            # PathServiceのフォールバックイベントを収集
            self._ps_collect_fallback(path_service)

            # バックアップディレクトリを設定
            backup_dir = path_service.get_backup_dir()
            backup_repository = FileSystemBackupRepository(backup_dir)

            # アクションに応じた処理を実行
            if action == "create":
                return self._execute_create_backup(request, path_service, backup_repository, start_time)
            if action == "restore":
                return self._execute_restore_backup(request, backup_repository, start_time)
            if action == "list":
                return self._execute_list_backups(request, backup_repository, start_time)
            if action == "delete":
                return self._execute_delete_backup(request, backup_repository, start_time)
            # 無効なアクション
            issues = [ToolIssue(
                type="invalid_action",
                severity="critical",
                message=f"無効なアクション: {action}",
                suggestion="create, restore, list, delete のいずれかを指定してください"
            )]
            return self._create_response(False, 0.0, issues, start_time)

        except Exception as e:
            self.logger.exception("BackupTool実行エラー")
            issues = [ToolIssue(
                type="execution_error",
                severity="critical",
                message=f"実行エラー: {e!s}"
            )]
            return self._create_response(False, 0.0, issues, start_time)

    def _execute_create_backup(
        self,
        request: ToolRequest,
        path_service: object,  # IPathService
        backup_repository: FileSystemBackupRepository,
        start_time: float
    ) -> ToolResponse:
        """バックアップ作成実行

        Args:
            request: ツールリクエスト
            path_service: パスサービス
            backup_repository: バックアップリポジトリ
            start_time: 開始時間

        Returns:
            バックアップ作成結果
        """
        try:
            episode_number = request.episode_number
            backup_name = request.additional_params.get("backup_name")

            # 対象原稿ファイル（PathServiceで一元解決）
            manuscript_path = path_service.get_manuscript_path(episode_number)
            if not manuscript_path.exists():
                # フォールバック: 既存の命名ゆらぎに備えてパターン探索
                manuscript_dir = path_service.get_manuscript_dir()
                episode_files = list(manuscript_dir.glob(f"第{episode_number:03d}話_*.md"))
                if episode_files:
                    manuscript_path = episode_files[0]

            if not manuscript_path.exists():
                issues = [ToolIssue(
                    type="file_not_found",
                    severity="critical",
                    message=f"第{episode_number:03d}話の原稿ファイルが見つかりません",
                    suggestion=f"{path_service.get_manuscript_dir()} にファイルが存在することを確認してください"
                )]
                return self._create_response(False, 0.0, issues, start_time)

            # バックアップ実行
            file_to_backup = manuscript_path
            backup_id = backup_repository.create_backup(file_to_backup, backup_name)

            # バックアップサイズとファイル数を取得
            backup_path = backup_repository.backup_root / f"{backup_id}.bak"
            backup_size = backup_path.stat().st_size if backup_path.exists() else 0

            metadata = {
                "action_performed": "create",
                "backup_id": backup_id,
                "backup_size": backup_size,
                "file_count": 1,
                "tool_name": self.tool_name,
                "tool_version": self.version
            }
            resp = self._create_response(True, 100.0, [], start_time, metadata)
            self._apply_fallback_metadata(resp)
            return resp

        except FileNotFoundError as e:
            issues = [ToolIssue(
                type="file_not_found",
                severity="critical",
                message=str(e)
            )]
            resp = self._create_response(False, 0.0, issues, start_time)
            self._apply_fallback_metadata(resp)
            return resp
        except Exception as e:
            issues = [ToolIssue(
                type="backup_error",
                severity="critical",
                message=f"バックアップ作成エラー: {e!s}"
            )]
            resp = self._create_response(False, 0.0, issues, start_time)
            self._apply_fallback_metadata(resp)
            return resp

    def _execute_restore_backup(
        self,
        request: ToolRequest,
        backup_repository: FileSystemBackupRepository,
        start_time: float
    ) -> ToolResponse:
        """バックアップ復元実行

        Args:
            request: ツールリクエスト
            backup_repository: バックアップリポジトリ
            start_time: 開始時間

        Returns:
            バックアップ復元結果
        """
        backup_id = request.additional_params.get("backup_id")
        if not backup_id:
            issues = [ToolIssue(
                type="missing_backup_id",
                severity="critical",
                message="復元にはbackup_idが必要です"
            )]
            return self._create_response(False, 0.0, issues, start_time)

        try:
            restore_path = request.additional_params.get("restore_path")
            backup_repository.restore_backup(backup_id, Path(restore_path) if restore_path else None)

            metadata = {
                "action_performed": "restore",
                "backup_id": backup_id,
                "file_count": 1,  # 単一ファイルの復元
                "tool_name": self.tool_name,
                "tool_version": self.version
            }
            return self._create_response(True, 100.0, [], start_time, metadata)

        except FileNotFoundError:
            issues = [ToolIssue(
                type="backup_not_found",
                severity="critical",
                message=f"バックアップが見つかりません: {backup_id}"
            )]
            return self._create_response(False, 0.0, issues, start_time)
        except Exception as e:
            issues = [ToolIssue(
                type="restore_error",
                severity="critical",
                message=f"復元エラー: {e!s}"
            )]
            return self._create_response(False, 0.0, issues, start_time)

    def _execute_list_backups(
        self,
        request: ToolRequest,
        backup_repository: FileSystemBackupRepository,
        start_time: float
    ) -> ToolResponse:
        """バックアップ一覧取得実行

        Args:
            request: ツールリクエスト
            backup_repository: バックアップリポジトリ
            start_time: 開始時間

        Returns:
            バックアップ一覧結果
        """
        try:
            filter_pattern = request.additional_params.get("filter_pattern")
            backup_list = backup_repository.list_backups(filter_pattern)

            metadata = {
                "action_performed": "list",
                "backup_count": len(backup_list),
                "backups": backup_list,
                "tool_name": self.tool_name,
                "tool_version": self.version
            }
            return self._create_response(True, 100.0, [], start_time, metadata)

        except Exception as e:
            issues = [ToolIssue(
                type="list_error",
                severity="high",
                message=f"一覧取得エラー: {e!s}"
            )]
            return self._create_response(False, 0.0, issues, start_time)

    def _execute_delete_backup(
        self,
        request: ToolRequest,
        backup_repository: FileSystemBackupRepository,
        start_time: float
    ) -> ToolResponse:
        """バックアップ削除実行

        Args:
            request: ツールリクエスト
            backup_repository: バックアップリポジトリ
            start_time: 開始時間

        Returns:
            バックアップ削除結果
        """
        backup_id = request.additional_params.get("backup_id")
        if not backup_id:
            issues = [ToolIssue(
                type="missing_backup_id",
                severity="critical",
                message="削除にはbackup_idが必要です"
            )]
            return self._create_response(False, 0.0, issues, start_time)

        try:
            # バックアップサイズを事前に取得
            backup_path = backup_repository.backup_root / f"{backup_id}.bak"
            deleted_size = backup_path.stat().st_size if backup_path.exists() else 0

            backup_repository.delete_backup(backup_id)

            metadata = {
                "action_performed": "delete",
                "backup_id": backup_id,
                "deleted_size": deleted_size,
                "tool_name": self.tool_name,
                "tool_version": self.version
            }
            return self._create_response(True, 100.0, [], start_time, metadata)

        except FileNotFoundError:
            issues = [ToolIssue(
                type="backup_not_found",
                severity="critical",
                message=f"バックアップが見つかりません: {backup_id}"
            )]
            return self._create_response(False, 0.0, issues, start_time)
        except Exception as e:
            issues = [ToolIssue(
                type="delete_error",
                severity="critical",
                message=f"削除エラー: {e!s}"
            )]
            return self._create_response(False, 0.0, issues, start_time)

    def _create_response(
        self,
        success: bool,
        score: float,
        issues: list[ToolIssue],
        start_time: float,
        additional_metadata: dict[str, Any] | None = None
    ) -> ToolResponse:
        """レスポンス作成（メタデータ拡張版）

        Args:
            success: 成功フラグ
            score: 品質スコア
            issues: 問題リスト
            start_time: 開始時間
            additional_metadata: 追加メタデータ

        Returns:
            ツールレスポンス
        """
        execution_time = (time.time() - start_time) * 1000  # ms

        metadata = {
            "tool_name": self.tool_name,
            "tool_version": self.version,
            "check_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        resp = ToolResponse(
            success=success,
            score=score,
            issues=issues,
            execution_time_ms=execution_time,
            metadata=metadata
        )
        # 基底のヘルパーでフォールバックメタを付与
        self._apply_fallback_metadata(resp)
        return resp
