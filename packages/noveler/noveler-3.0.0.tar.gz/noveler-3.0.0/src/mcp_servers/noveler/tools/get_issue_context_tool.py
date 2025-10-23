"""get_issue_context ツールの実装

issue_idや行番号をもとに前後コンテキストを返す。
run_quality_checks と同等のissue_id付与ロジックを再現して検索。
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolIssue,
    ToolRequest,
    ToolResponse,
)
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.caching.file_cache_service import get_file_cache_service
from noveler.infrastructure.adapters.path_service_adapter import create_path_service

from .check_rhythm_tool import CheckRhythmTool
from .check_readability_tool import CheckReadabilityTool
from .check_grammar_tool import CheckGrammarTool


class GetIssueContextTool(MCPToolBase):
    """Issue周辺文脈取得ツール"""

    def __init__(self) -> None:
        super().__init__(
            tool_name="get_issue_context",
            tool_description="Issue周辺の前後行スニペット取得",
        )
        # フォールバックイベントは基底クラスの共通バッファを使用

    def get_input_schema(self) -> dict[str, Any]:
        schema = self._get_common_input_schema()
        schema["properties"].update(
            {
                "file_path": {
                    "type": "string",
                    "description": "直接ファイルパス指定（episode_numberより優先）",
                },
                "issue_id": {
                    "type": "string",
                    "description": "対象Issueの安定ID（推奨）",
                },
                "line_number": {
                    "type": "integer",
                    "description": "行番号で特定（issue_idが無い場合）",
                },
                "window": {
                    "type": "integer",
                    "default": 2,
                    "description": "前後に含める行数",
                },
            }
        )
        return schema

    def execute(self, request: ToolRequest) -> ToolResponse:
        logger = get_logger(__name__)
        import time

        start = time.time()
        try:
            self._validate_request(request)
            ap = request.additional_params or {}
            window = int(ap.get("window", 2))

            path = self._resolve_target_path(request)
            if not path or not path.exists():
                return self._create_response(False, 0.0, [], start, "Target file not found")

            text = path.read_text(encoding="utf-8")
            lines = text.split("\n")
            file_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

            # 検出（rhythm/readability/grammar）
            issues = self._collect_issues(request, str(path), lines, file_hash)

            hit = None
            target_issue_id = ap.get("issue_id")
            target_line = ap.get("line_number")
            if target_issue_id:
                for it in issues:
                    if it.issue_id == target_issue_id:
                        hit = it
                        break
            if hit is None and target_line:
                target_line = int(target_line)
                # 最も近いissueを選ぶ
                hit = min(
                    issues,
                    key=lambda i: abs((i.line_number or 0) - target_line),
                    default=None,
                )
            if hit is None:
                return self._create_response(False, 0.0, [], start, "Issue not found")

            sline = max(1, (hit.line_number or 1) - window)
            eline = min(len(lines), (hit.end_line_number or (hit.line_number or 1)) + window)
            snippet_lines = [
                f"{idx:>5}: {lines[idx-1]}" for idx in range(sline, eline + 1)
            ]

            issues_out = [
                ToolIssue(
                    type="issue_context",
                    severity="low",
                    message="\n".join(snippet_lines),
                    line_number=sline,
                    suggestion="周辺文脈を確認し、修正案を検討",
                    end_line_number=eline,
                    file_path=str(path),
                    reason_code=hit.reason_code,
                    details={
                        "issue_id": hit.issue_id,
                        "hit_line": hit.line_number,
                        "hit_end_line": hit.end_line_number,
                    },
                )
            ]

            resp = self._create_response(True, 100.0, issues_out, start)
            resp.metadata.update(
                {
                    "file_path": str(path),
                    "file_hash": file_hash,
                }
            )
            # PathServiceのフォールバック可視化（共通ヘルパ）
            self._apply_fallback_metadata(resp)
            return resp

        except Exception as e:
            return self._create_response(False, 0.0, [], start, f"get_issue_context error: {e!s}")

    # ---- helpers ----

    def _resolve_target_path(self, request: ToolRequest) -> Path | None:
        ap = request.additional_params or {}
        if isinstance(ap.get("file_path"), str):
            return Path(ap["file_path"]).expanduser()
        try:
            ps = create_path_service()
            cache = get_file_cache_service()
            md = ps.get_manuscript_dir()
            ep = cache.get_episode_file_cached(md, request.episode_number)
            # PathServiceのフォールバックイベントを収集（共通ヘルパ）
            self._ps_collect_fallback(ps)
            return ep
        except Exception:
            return None

    def _collect_issues(
        self, request: ToolRequest, file_path: str, lines: list[str], file_hash: str
    ) -> list[ToolIssue]:
        issues: list[ToolIssue] = []

        # rhythm（すでにissue_idあり）
        rreq = ToolRequest(
            episode_number=request.episode_number,
            project_name=request.project_name,
            additional_params={"file_path": file_path},
        )
        rres = CheckRhythmTool().execute(rreq)
        issues.extend(rres.issues)

        # readability/grammar（issue_id補完）
        def norm(its: Iterable[ToolIssue]) -> list[ToolIssue]:
            out: list[ToolIssue] = []
            for it in its:
                if it.type == "summary_metrics":
                    continue
                line_hash = it.line_hash
                if line_hash is None and it.line_number and 1 <= it.line_number <= len(lines):
                    line_text = lines[it.line_number - 1].strip()
                    line_hash = hashlib.sha256(line_text.encode("utf-8")).hexdigest()
                block_hash = it.block_hash
                issue_id = it.issue_id
                if issue_id is None:
                    base = f"{file_hash}:{it.type}:{it.line_number}:{line_hash or ''}:{block_hash or ''}"
                    issue_id = hashlib.sha256(base.encode("utf-8")).hexdigest()[:12]
                    issue_id = f"quality-{issue_id}"
                out.append(
                    ToolIssue(
                        type=it.type,
                        severity=it.severity,
                        message=it.message,
                        line_number=it.line_number,
                        suggestion=it.suggestion,
                        end_line_number=getattr(it, "end_line_number", None),
                        file_path=file_path,
                        line_hash=line_hash,
                        block_hash=block_hash,
                        reason_code=getattr(it, "reason_code", None),
                        details=getattr(it, "details", None),
                        issue_id=issue_id,
                    )
                )
            return out

        read = CheckReadabilityTool().execute(rreq)
        issues.extend(norm(read.issues))
        gram = CheckGrammarTool().execute(rreq)
        issues.extend(norm(gram.issues))
        return issues
