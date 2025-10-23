"""check_style ツールの実装

基本スタイル/体裁チェック（安全に自動修正しやすい領域）。
 - 連続空行
 - 行末スペース
 - タブ文字
 - 連続半角スペース
 - 全角スペースの混在（通知のみ）
 - 括弧の対応不一致（全体集計）
"""
from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolIssue,
    ToolRequest,
    ToolResponse,
)
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.caching.file_cache_service import get_file_cache_service
from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class CheckStyleTool(MCPToolBase):
    def __init__(self) -> None:
        super().__init__(
            tool_name="check_style",
            tool_description="体裁・スタイルチェック（空行/スペース/タブ/括弧対応）",
        )

    def get_input_schema(self) -> dict[str, Any]:
        schema = self._get_common_input_schema()
        schema["properties"].update(
            {
                "file_path": {
                    "type": "string",
                    "description": "直接ファイルパス指定（episode_numberより優先）",
                },
            }
        )
        return schema

    def execute(self, request: ToolRequest) -> ToolResponse:
        logger = get_logger(__name__)
        start = time.time()
        try:
            self._validate_request(request)
            ap = request.additional_params or {}

            # ファイル取得
            file_path: Path | None = None
            # content優先（B20: 重複I/O回避）
            if isinstance(ap.get("content"), str):
                content = ap.get("content") or ""
                if isinstance(ap.get("file_path"), str):
                    fp = Path(ap["file_path"]).expanduser()
                    file_path = fp if fp.exists() else fp
            else:
                if isinstance(ap.get("file_path"), str):
                    file_path = Path(ap["file_path"]).expanduser()
                    content = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
                else:
                    content = self._load_episode_content(request.episode_number, request.project_name)
                    try:
                        ps = create_path_service()
                        cache = get_file_cache_service()
                        md = ps.get_manuscript_dir()
                        file_path = cache.get_episode_file_cached(md, request.episode_number)
                        # PathServiceのフォールバックイベントを収集
                        self._ps_collect_fallback(ps)
                    except Exception:
                        file_path = None
            if not content:
                return self._create_response(True, 100.0, [], start)

            fhash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            lines = content.split("\n")

            issues: list[ToolIssue] = []

            # 1) 連続空行
            blank_start = None
            for idx, line in enumerate(lines, 1):
                if line.strip() == "":
                    if blank_start is None:
                        blank_start = idx
                else:
                    if blank_start is not None and idx - blank_start >= 2:
                        sline = blank_start
                        eline = idx - 1
                        block = "\n".join(lines[sline - 1 : eline])
                        blk_hash = hashlib.sha256(block.encode("utf-8")).hexdigest()
                        iid = hashlib.sha256(f"{fhash}:EMPTY_LINE_RUNS:{sline}-{eline}:{blk_hash}".encode("utf-8")).hexdigest()[:12]
                        issues.append(
                            ToolIssue(
                                type="empty_line_runs",
                                severity="low",
                                message=f"空行が連続しています（{sline}–{eline}行）",
                                line_number=sline,
                                end_line_number=eline,
                                file_path=str(file_path) if file_path else None,
                                block_hash=blk_hash,
                                reason_code="EMPTY_LINE_RUNS",
                                issue_id=f"style-{iid}",
                            )
                        )
                    blank_start = None
            if blank_start is not None and len(lines) - blank_start >= 1:
                sline = blank_start
                eline = len(lines)
                block = "\n".join(lines[sline - 1 : eline])
                blk_hash = hashlib.sha256(block.encode("utf-8")).hexdigest()
                iid = hashlib.sha256(f"{fhash}:EMPTY_LINE_RUNS:{sline}-{eline}:{blk_hash}".encode("utf-8")).hexdigest()[:12]
                issues.append(
                    ToolIssue(
                        type="empty_line_runs",
                        severity="low",
                        message=f"空行が連続しています（{sline}–{eline}行）",
                        line_number=sline,
                        end_line_number=eline,
                        file_path=str(file_path) if file_path else None,
                        block_hash=blk_hash,
                        reason_code="EMPTY_LINE_RUNS",
                        issue_id=f"style-{iid}",
                    )
                )

            # 2) 行末スペース/タブ/連続半角スペース/全角スペース
            for idx, line in enumerate(lines, 1):
                stripped = line.rstrip("\n")
                if len(stripped) != len(line):
                    pass
                # 行末スペース
                if re.search(r"\s+$", line):
                    ln_hash = hashlib.sha256(line.strip().encode("utf-8")).hexdigest()
                    iid = hashlib.sha256(f"{fhash}:TRAILING_SPACES:{idx}:{ln_hash}".encode("utf-8")).hexdigest()[:12]
                    issues.append(
                        ToolIssue(
                            type="trailing_spaces",
                            severity="low",
                            message="行末に余分な空白があります",
                            line_number=idx,
                            file_path=str(file_path) if file_path else None,
                            line_hash=ln_hash,
                            reason_code="TRAILING_SPACES",
                            issue_id=f"style-{iid}",
                        )
                    )
                # タブ
                if "\t" in line:
                    ln_hash = hashlib.sha256(line.strip().encode("utf-8")).hexdigest()
                    iid = hashlib.sha256(f"{fhash}:TAB_FOUND:{idx}:{ln_hash}".encode("utf-8")).hexdigest()[:12]
                    issues.append(
                        ToolIssue(
                            type="tab_found",
                            severity="low",
                            message="タブ文字が含まれています",
                            line_number=idx,
                            file_path=str(file_path) if file_path else None,
                            line_hash=ln_hash,
                            reason_code="TAB_FOUND",
                            issue_id=f"style-{iid}",
                        )
                    )
                # 連続半角スペース
                if "  " in line:
                    ln_hash = hashlib.sha256(line.strip().encode("utf-8")).hexdigest()
                    iid = hashlib.sha256(f"{fhash}:DOUBLE_SPACES:{idx}:{ln_hash}".encode("utf-8")).hexdigest()[:12]
                    issues.append(
                        ToolIssue(
                            type="double_spaces",
                            severity="low",
                            message="半角スペースが連続しています",
                            line_number=idx,
                            file_path=str(file_path) if file_path else None,
                            line_hash=ln_hash,
                            reason_code="DOUBLE_SPACES",
                            issue_id=f"style-{iid}",
                        )
                    )
                # 全角スペース
                if "　" in line:
                    ln_hash = hashlib.sha256(line.strip().encode("utf-8")).hexdigest()
                    iid = hashlib.sha256(f"{fhash}:FULLWIDTH_SPACE:{idx}:{ln_hash}".encode("utf-8")).hexdigest()[:12]
                    issues.append(
                        ToolIssue(
                            type="fullwidth_space",
                            severity="low",
                            message="全角スペースが含まれています（要確認）",
                            line_number=idx,
                            file_path=str(file_path) if file_path else None,
                            line_hash=ln_hash,
                            reason_code="FULLWIDTH_SPACE",
                            issue_id=f"style-{iid}",
                        )
                    )

            # 3) 括弧の対応チェック（全体）
            pairs = [
                ("「", "」"),
                ("『", "』"),
                ("（", "）"),
                ("【", "】"),
                ("〈", "〉"),
                ("《", "》"),
                ("〔", "〕"),
            ]
            mismatches = []
            for l, r in pairs:
                lc = content.count(l)
                rc = content.count(r)
                if lc != rc:
                    mismatches.append({"pair": f"{l}{r}", "left": lc, "right": rc})
            if mismatches:
                iid = hashlib.sha256(f"{fhash}:BRACKETS_MISMATCH".encode("utf-8")).hexdigest()[:12]
                issues.append(
                    ToolIssue(
                        type="brackets_mismatch",
                        severity="medium",
                        message="括弧の対応不一致があります（全体集計）",
                        line_number=None,
                        file_path=str(file_path) if file_path else None,
                        reason_code="BRACKETS_MISMATCH",
                        details={"mismatches": mismatches},
                        issue_id=f"style-{iid}",
                    )
                )

            # スコア（軽微なもの主体なので控えめに減点）
            penalty = 0
            for it in issues:
                if it.severity == "medium":
                    penalty += 5
                else:
                    penalty += 2
            score = max(0.0, 100.0 - float(penalty))

            resp = self._create_response(True, score, issues, start)
            if file_path:
                resp.metadata["file_path"] = str(file_path)
                resp.metadata["file_hash"] = fhash
            # PathServiceのフォールバック可視化
            self._apply_fallback_metadata(resp)
            return resp
        except Exception as e:
            return self._create_response(False, 0.0, [], start, f"style check error: {e!s}")
