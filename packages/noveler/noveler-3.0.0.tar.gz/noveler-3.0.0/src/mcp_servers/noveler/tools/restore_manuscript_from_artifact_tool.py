"""改稿ロールバック/適用ツール

artifact_id で指定された本文を原稿ファイルへ適用する。
オプションで dry_run（差分のみ）・バックアップ作成・出力先変更に対応。
"""
from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolIssue,
    ToolRequest,
    ToolResponse,
)
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.domain.services.artifact_store_service import create_artifact_store


class RestoreManuscriptFromArtifactTool(MCPToolBase):
    def __init__(self) -> None:
        super().__init__(
            tool_name="restore_manuscript_from_artifact",
            tool_description="artifact_idで指定した本文を原稿へ適用（dry_run/backup対応）",
        )

    def get_input_schema(self) -> dict[str, Any]:
        schema = self._get_common_input_schema()
        schema["properties"].update(
            {
                "artifact_id": {
                    "type": "string",
                    "description": "適用する本文のartifact:XXXXXXXX 参照ID",
                },
                "file_path": {
                    "type": "string",
                    "description": "適用先ファイル（省略時はepisodeから推定）",
                },
                "output_path": {
                    "type": "string",
                    "description": "適用先を別ファイルに出力（省略時は上書き）",
                },
                "dry_run": {
                    "type": "boolean",
                    "default": True,
                    "description": "Trueなら差分のみ生成し、ファイルは変更しない",
                },
                "create_backup": {
                    "type": "boolean",
                    "default": True,
                    "description": "上書き時にバックアップを作成",
                },
            }
        )
        schema["required"] = ["episode_number", "artifact_id"]
        return schema

    def execute(self, request: ToolRequest) -> ToolResponse:
        logger = get_logger(__name__)
        import time as _t
        start = _t.time()

        try:
            self._validate_request(request)
            ap = request.additional_params or {}
            artifact_id = str(ap.get("artifact_id", "")).strip()
            if not artifact_id:
                raise ValueError("artifact_id is required")

            dry_run = bool(ap.get("dry_run", True))
            create_backup = bool(ap.get("create_backup", True))

            # 対象パス解決
            fp = self._resolve_target_path(request)
            if isinstance(ap.get("file_path"), str):
                fp = Path(ap["file_path"]).expanduser()
            if fp is None:
                raise FileNotFoundError("target manuscript file not resolved")
            file_path: Path = fp

            # アーティファクト取得
            ps = create_path_service()
            store = create_artifact_store(storage_dir=ps.get_noveler_output_dir() / "artifacts")
            restored = store.fetch(artifact_id)
            if restored is None:
                raise FileNotFoundError(f"artifact not found: {artifact_id}")

            before = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
            after = restored

            # diff
            diff_text = self._make_diff(before, after, file_path)
            diff_ref = store.create_reference(diff_text, alias="rollback_diff", content_type="text", source_file=str(file_path))

            written_to = None
            backup_path = None
            if not dry_run:
                # 出力先
                out_path = Path(ap["output_path"]).expanduser() if isinstance(ap.get("output_path"), str) else file_path
                out_path.parent.mkdir(parents=True, exist_ok=True)
                # バックアップ
                if create_backup and out_path.exists():
                    backup_dir = ps.get_backup_dir()
                    backup_path = backup_dir / f"{out_path.name}.bak"
                    backup_path.write_text(before, encoding="utf-8")
                out_path.write_text(after, encoding="utf-8")
                written_to = str(out_path)

            issue = ToolIssue(
                type="restore_apply_result",
                severity="low",
                message=f"artifact適用{'（dry-run）' if dry_run else ''}",
                file_path=str(file_path),
                details={
                    "artifact_id": artifact_id,
                    "written_to": written_to,
                    "backup_path": str(backup_path) if backup_path else None,
                    "diff_artifact": diff_ref.get("artifact_id"),
                },
            )

            resp = self._create_response(True, 100.0, [issue], start)
            resp.metadata.update(
                {
                    "file_path": str(file_path),
                    "written_to": written_to,
                    "backup_path": str(backup_path) if backup_path else None,
                    "diff_artifact": diff_ref,
                }
            )
            # フォールバックメタ
            self._ps_collect_fallback(ps)
            self._apply_fallback_metadata(resp)
            return resp

        except Exception as e:
            return self._create_response(False, 0.0, [], start, f"restore error: {e!s}")

    # ---- helpers ----
    def _resolve_target_path(self, request: ToolRequest) -> Path | None:
        ap = request.additional_params or {}
        if isinstance(ap.get("file_path"), str):
            return Path(ap["file_path"]).expanduser()
        try:
            from noveler.infrastructure.caching.file_cache_service import get_file_cache_service
            ps = create_path_service()
            cache = get_file_cache_service()
            md = ps.get_manuscript_dir()
            ep = cache.get_episode_file_cached(md, request.episode_number)
            self._ps_collect_fallback(ps)
            return ep
        except Exception:
            return None

    def _make_diff(self, before: str, after: str, path: Path) -> str:
        if before == after:
            return ""
        diff = difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=str(path),
            tofile=str(path),
        )
        return "".join(list(diff))
