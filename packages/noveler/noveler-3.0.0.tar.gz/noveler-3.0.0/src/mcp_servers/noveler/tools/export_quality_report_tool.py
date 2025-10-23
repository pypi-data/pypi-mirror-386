"""export_quality_report ツールの実装

run_quality_checks の結果を JSON/CSV/Markdown/NDJSON で保存する。
"""
from __future__ import annotations

import csv
import json
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
from .run_quality_checks_tool import RunQualityChecksTool
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from collections import Counter, defaultdict


class ExportQualityReportTool(MCPToolBase):
    """品質レポートエクスポート"""

    def __init__(self) -> None:
        super().__init__(
            tool_name="export_quality_report",
            tool_description="品質チェック結果をJSON/CSV/MD/NDJSONで保存",
        )

    def get_input_schema(self) -> dict[str, Any]:
        schema = self._get_common_input_schema()
        schema["properties"].update(
            {
                "file_path": {"type": "string", "description": "直接ファイル指定"},
                "aspects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["rhythm", "readability", "grammar"],
                },
                "preset": {"type": "string", "enum": ["narou", "custom"], "default": "narou"},
                "thresholds": {"type": "object"},
                "severity_threshold": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "default": "low",
                },
                "format": {
                    "type": "string",
                    "enum": ["json", "csv", "md", "ndjson"],
                    "default": "json",
                },
                "destination": {
                    "type": "string",
                    "description": "出力ファイルパス（省略時はプロジェクトreports内に保存）",
                },
                "template": {
                    "type": "string",
                    "enum": ["compact", "detailed", "grouped_by_reason", "grouped_by_severity"],
                    "default": "compact",
                    "description": "Markdown出力テンプレート",
                },
                "max_per_group": {
                    "type": "integer",
                    "default": 10,
                    "description": "各グループで表示する最大件数（Markdownのみ）",
                },
                "max_issues": {
                    "type": "integer",
                    "default": 200,
                    "description": "全体で表示する最大件数（Markdownのみ）",
                },
                "include_details": {
                    "type": "boolean",
                    "default": False,
                    "description": "詳細フィールド（hashやdetails）をMarkdownに含める",
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
            fmt = str(ap.get("format", "json"))

            # 実行
            checks_req = ToolRequest(
                episode_number=request.episode_number,
                project_name=request.project_name,
                additional_params=ap,
            )
            result = RunQualityChecksTool().execute(checks_req)

            # 保存先
            out_path = self._resolve_output_path(request, fmt, ap.get("destination"))
            out_path.parent.mkdir(parents=True, exist_ok=True)

            # 出力
            if fmt == "json":
                payload = self._to_json_payload(result)
                out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            elif fmt == "ndjson":
                lines = [json.dumps(self._issue_to_dict(i), ensure_ascii=False) for i in result.issues]
                out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            elif fmt == "csv":
                self._write_csv(out_path, result)
            elif fmt == "md":
                tpl = str(ap.get("template", "compact"))
                max_per_group = int(ap.get("max_per_group", 10))
                max_issues = int(ap.get("max_issues", 200))
                include_details = bool(ap.get("include_details", False))
                out_path.write_text(
                    self._to_markdown(
                        result,
                        template=tpl,
                        max_per_group=max_per_group,
                        max_issues=max_issues,
                        include_details=include_details,
                    ),
                    encoding="utf-8",
                )
            else:
                raise ValueError(f"Unsupported format: {fmt}")

            aspect_scores = result.metadata.get("aspect_scores")
            score_method = result.metadata.get("score_method")

            issues = [
                ToolIssue(
                    type="export_quality_report",
                    severity="low",
                    message=f"レポートを保存しました: {out_path}",
                    suggestion="必要に応じて共有・差分管理してください",
                    details={
                        "format": fmt,
                        "aspect_scores": aspect_scores,
                        "score_method": score_method,
                        "file_path": result.metadata.get("file_path"),
                    },
                )
            ]

            resp = self._create_response(True, result.score, issues, start)
            resp.metadata.update(
                {
                    "output_path": str(out_path),
                    "format": fmt,
                    "file_path": result.metadata.get("file_path"),
                    "file_hash": result.metadata.get("file_hash"),
                    "aspect_scores": aspect_scores,
                    "score_method": score_method,
                }
            )
            # PathServiceのフォールバック情報を継承
            if result.metadata.get("path_fallback_used"):
                resp.metadata["path_fallback_used"] = True
                resp.metadata["path_fallback_events"] = result.metadata.get("path_fallback_events", [])
            return resp

        except Exception as e:
            return self._create_response(False, 0.0, [], start, f"export error: {e!s}")

    # ---- helpers ----

    def _resolve_output_path(self, request: ToolRequest, fmt: str, destination: Any) -> Path:
        if isinstance(destination, str) and destination:
            return Path(destination)
        # プロジェクト標準のreports配下
        ps = create_path_service()
        reports_dir = ps.get_reports_dir() / "quality"
        ts = time.strftime("%Y%m%d_%H%M%S")
        out = reports_dir / f"quality_ep{request.episode_number:03d}_{ts}.{fmt}"
        # ここでもフォールバックがあれば可視化できるよう、RunQualityChecks側に委譲（上で継承）
        try:
            if hasattr(ps, "get_and_clear_fallback_events"):
                ev = ps.get_and_clear_fallback_events() or []
                # この関数単独では返却できないため、ファイル名ヘッダー等のメタ付与に留める運用も可
                # 実際の応答はexecuteでRunQualityChecksのメタから継承される
                if ev:
                    # no-op placeholder for future enrichment
                    _ = ev
        except Exception:
            pass
        return out

    def _to_json_payload(self, result: ToolResponse) -> dict[str, Any]:
        return {
            "success": result.success,
            "score": result.score,
            "metadata": result.metadata,
            "issues": [self._issue_to_dict(i) for i in result.issues],
        }

    def _issue_to_dict(self, i: ToolIssue) -> dict[str, Any]:
        return {
            "type": i.type,
            "severity": i.severity,
            "message": i.message,
            "line_number": i.line_number,
            "end_line_number": getattr(i, "end_line_number", None),
            "file_path": getattr(i, "file_path", None),
            "line_hash": getattr(i, "line_hash", None),
            "block_hash": getattr(i, "block_hash", None),
            "reason_code": getattr(i, "reason_code", None),
            "details": getattr(i, "details", None),
            "issue_id": getattr(i, "issue_id", None),
        }

    def _write_csv(self, out_path: Path, result: ToolResponse) -> None:
        headers = [
            "type",
            "severity",
            "line_number",
            "end_line_number",
            "reason_code",
            "issue_id",
            "message",
        ]
        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for i in result.issues:
                writer.writerow(
                    [
                        i.type,
                        i.severity,
                        i.line_number,
                        getattr(i, "end_line_number", None),
                        getattr(i, "reason_code", None),
                        getattr(i, "issue_id", None),
                        i.message,
                    ]
                )

    def _to_markdown(
        self,
        result: ToolResponse,
        *,
        template: str = "compact",
        max_per_group: int = 10,
        max_issues: int = 200,
        include_details: bool = False,
    ) -> str:
        meta = result.metadata
        header = [
            "# Quality Report\n",
            f"- File: {meta.get('file_path')}\n",
            f"- Score: {result.score}\n",
        ]
        if "aspect_scores" in meta:
            header.append(f"- Aspect Scores: {json.dumps(meta['aspect_scores'], ensure_ascii=False)}\n")
        header.append("\n")

        # 集計
        issues = list(result.issues)
        summary = None
        rest = []
        for i in issues:
            if i.type == "summary_metrics" and summary is None:
                summary = i.message
            else:
                rest.append(i)

        # 上限で切る
        rest = rest[:max_issues]

        if template == "compact":
            body = self._md_compact(summary, rest, include_details)
        elif template == "grouped_by_reason":
            body = self._md_grouped(rest, key=lambda i: getattr(i, "reason_code", i.type), title="Issues by Reason", max_per_group=max_per_group, include_details=include_details)
        elif template == "grouped_by_severity":
            order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            body = self._md_grouped(rest, key=lambda i: getattr(i, "severity", "low"), title="Issues by Severity", key_order=order, max_per_group=max_per_group, include_details=include_details)
        elif template == "detailed":
            body = self._md_detailed(rest)
        else:
            body = self._md_compact(summary, rest, include_details)

        return "".join(header) + body

    def _md_compact(self, summary_msg: str | None, issues: list[ToolIssue], include_details: bool) -> str:
        lines: list[str] = []
        if summary_msg:
            lines.append("## Summary\n")
            lines.append(f"- {summary_msg}\n\n")

        # カウント
        by_reason = Counter(getattr(i, "reason_code", i.type) for i in issues)
        by_sev = Counter(getattr(i, "severity", "low") for i in issues)
        lines.append("## Overview\n")
        lines.append("### Counts by Reason\n")
        lines.append("| Reason | Count |\n|---|---:|\n")
        for k, v in by_reason.most_common():
            lines.append(f"| {k} | {v} |\n")
        lines.append("\n### Counts by Severity\n")
        lines.append("| Severity | Count |\n|---|---:|\n")
        for k, v in by_sev.most_common():
            lines.append(f"| {k} | {v} |\n")

        # 例示
        lines.append("\n## Sample Issues\n")
        top = issues[: min(20, len(issues))]
        for i in top:
            span = (
                f"L{(i.line_number or '-')}-{getattr(i,'end_line_number')}"
                if getattr(i, "end_line_number", None)
                else f"L{(i.line_number or '-')}"
            )
            lines.append(
                f"- [{getattr(i,'severity','')}] {getattr(i,'reason_code', i.type)} {span}: {i.message} (id: {getattr(i,'issue_id','')})\n"
            )
            if include_details and getattr(i, "details", None):
                details_json = json.dumps(getattr(i, "details"), ensure_ascii=False)
                lines.append(f"  - details: `{details_json}`\n")
        return "".join(lines)

    def _md_grouped(
        self,
        issues: list[ToolIssue],
        *,
        key,
        title: str,
        key_order: dict[str, int] | None = None,
        max_per_group: int = 10,
        include_details: bool = False,
    ) -> str:
        groups: dict[str, list[ToolIssue]] = defaultdict(list)
        for i in issues:
            groups[str(key(i))].append(i)
        # 並び順
        keys = list(groups.keys())
        if key_order:
            keys.sort(key=lambda k: (key_order.get(k, 999), k))
        else:
            keys.sort()
        lines = [f"## {title}\n"]
        for k in keys:
            lines.append(f"\n### {k} ({len(groups[k])})\n")
            for i in groups[k][:max_per_group]:
                span = (
                    f"L{(i.line_number or '-')}-{getattr(i,'end_line_number')}"
                    if getattr(i, "end_line_number", None)
                    else f"L{(i.line_number or '-')}"
                )
                lines.append(
                    f"- [{getattr(i,'severity','')}] {i.type} {span}: {i.message} (id: {getattr(i,'issue_id','')})\n"
                )
                if include_details and getattr(i, "details", None):
                    details_json = json.dumps(getattr(i, "details"), ensure_ascii=False)
                    lines.append(f"  - details: `{details_json}`\n")
        return "".join(lines)

    def _md_detailed(self, issues: list[ToolIssue]) -> str:
        lines = ["## Issues (Detailed)\n"]
        for i in issues:
            lines.append(
                "\n".join(
                    [
                        f"### {getattr(i,'reason_code', i.type)}",
                        f"- Type: {i.type}",
                        f"- Severity: {i.severity}",
                        f"- Lines: {i.line_number}" + (f"-{getattr(i,'end_line_number')}" if getattr(i,'end_line_number',None) else ""),
                        f"- Message: {i.message}",
                        f"- Issue ID: {getattr(i,'issue_id','')}",
                        f"- Line Hash: {getattr(i,'line_hash','')}",
                        f"- Block Hash: {getattr(i,'block_hash','')}",
                        f"- Details: {json.dumps(getattr(i,'details',{}), ensure_ascii=False)}",
                        "",
                    ]
                )
            )
        return "".join(lines)
