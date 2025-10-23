# File: src/noveler/presentation/mcp/adapters/handlers.py
# Purpose: Thin presentation-layer helpers for MCP tool execution and wrapping.
# Context: Provide small, reusable helpers to keep server entrypoints minimal
#          while avoiding any domain/business logic in this layer.
"""MCP presentation-layer handler helpers.

This module exposes tiny helpers to execute a given async tool runner with
optional logging and to wrap arbitrary payloads into MCP `TextContent` lists.
It deliberately knows nothing about domain rules.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import time
from typing import Any, Awaitable, Callable

from mcp.types import TextContent
from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest

# Tools used by quality metadata adapters
from mcp_servers.noveler.tools.quality_metadata_tools import (
    GetQualitySchemaTool,
    ListQualityPresetsTool,
)
from mcp_servers.noveler.tools.check_readability_tool import CheckReadabilityTool
from mcp_servers.noveler.tools.check_grammar_tool import CheckGrammarTool
from mcp_servers.noveler.tools.check_style_tool import CheckStyleTool
from mcp_servers.noveler.tools.check_rhythm_tool import CheckRhythmTool
from mcp_servers.noveler.tools.improve_quality_until_tool import ImproveQualityUntilTool
from mcp_servers.noveler.tools.run_quality_checks_tool import RunQualityChecksTool
from mcp_servers.noveler.tools.test_result_analysis_tool import ResultAnalysisTool
from mcp_servers.noveler.tools.backup_tool import BackupTool
from mcp_servers.noveler.tools.fix_quality_issues_tool import FixQualityIssuesTool
from mcp_servers.noveler.tools.get_issue_context_tool import GetIssueContextTool
from mcp_servers.noveler.tools.export_quality_report_tool import ExportQualityReportTool
from mcp_servers.noveler.tools.polish_manuscript_tool import PolishManuscriptTool
from mcp_servers.noveler.tools.polish_manuscript_apply_tool import PolishManuscriptApplyTool
from mcp_servers.noveler.tools.restore_manuscript_from_artifact_tool import (
    RestoreManuscriptFromArtifactTool,
)
from mcp_servers.noveler.tools.polish_tool import PolishTool
from noveler.presentation.mcp.adapters.io import resolve_path_service
from noveler.domain.utils.domain_logging import capture_domain_logs

try:
    # Optional import guard to avoid breaking tests when not available
    from noveler.domain.services.artifact_store_service import create_artifact_store  # type: ignore
    _ARTIFACT_AVAILABLE = True
except Exception:  # pragma: no cover
    create_artifact_store = None  # type: ignore
    _ARTIFACT_AVAILABLE = False
from mcp_servers.noveler.json_conversion_adapter import (
    convert_cli_to_json as _legacy_convert_cli_to_json,
    validate_json_response as _legacy_validate_json_response,
)


ConsoleLike = Any  # duck-typed: expects print_info/print_error methods when provided


async def execute_with_logging(
    name: str,
    arguments: dict[str, Any],
    runner: Callable[[], Awaitable[Any]],
    *,
    debug: bool = False,
    console: ConsoleLike | None = None,
) -> Any:
    """Execute the async runner with minimal timing/logging.

    Args:
        name: Tool name for logs.
        arguments: Raw arguments (logged only when debug and console provided).
        runner: Async function that performs the actual tool work and returns a payload.
        debug: When True, logs start/end events to the provided console.
        console: Console-like object supporting print_info/print_error (optional).

    Returns:
        Any: Whatever the runner returns (typically a dict payload).
    """
    t0 = time.time()
    if debug and console is not None:
        try:
            console.print_info(f"🛠️ CallTool start: {name} args_keys={list((arguments or {}).keys())}")
        except Exception:
            pass

    with capture_domain_logs() as domain_logs:
        result = await runner()

    if debug and console is not None:
        try:
            elapsed_ms = int((time.time() - t0) * 1000)
            score = result.get("score") if isinstance(result, dict) else None
            issues = result.get("issues") if isinstance(result, dict) else None
            issue_count = len(issues) if isinstance(issues, list) else None
            console.print_info(
                f"✅ CallTool done: {name} elapsed={elapsed_ms}ms score={score} issues={issue_count}"
            )
        except Exception:
            pass
    if isinstance(result, dict) and domain_logs:
        metadata = result.setdefault("metadata", {})
        metadata.setdefault("domain_logs", list(domain_logs))
    return result


def wrap_json_text(result: Any) -> list[TextContent]:
    """Wrap a payload into MCP `TextContent` with pretty JSON.

    Args:
        result: Arbitrary JSON-serializable payload.

    Returns:
        list[TextContent]: Single-item list with JSON string payload.
    """
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


# --- Specific thin adapters (phase 1 extract) ---

async def list_quality_presets(arguments: dict[str, Any]) -> dict[str, Any]:
    """Run ListQualityPresetsTool and normalise its response to dict.

    Args:
        arguments: Raw MCP arguments (episode_number optional).

    Returns:
        dict: Normalised payload with success/score/issues/metadata.
    """
    request = ToolRequest(episode_number=arguments.get("episode_number", 1), additional_params=arguments)
    tool = ListQualityPresetsTool()
    response = tool.execute(request)
    return {
        "success": response.success,
        "score": response.score,
        "issues": [
            {"type": i.type, "severity": i.severity, "message": i.message, "details": getattr(i, "details", None)}
            for i in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }


async def get_quality_schema(arguments: dict[str, Any]) -> dict[str, Any]:
    """Run GetQualitySchemaTool and normalise its response to dict.

    Args:
        arguments: Raw MCP arguments (episode_number optional).

    Returns:
        dict: Normalised payload with success/score/issues/metadata.
    """
    request = ToolRequest(episode_number=arguments.get("episode_number", 1), additional_params=arguments)
    tool = GetQualitySchemaTool()
    response = tool.execute(request)
    return {
        "success": response.success,
        "score": response.score,
        "issues": [
            {"type": i.type, "severity": i.severity, "message": i.message, "details": getattr(i, "details", None)}
        for i in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }


# JSON utilities (sync wrappers)

def convert_cli_to_json_adapter(cli_result: dict) -> dict:
    """Thin wrapper for legacy convert_cli_to_json (kept sync by design)."""
    return _legacy_convert_cli_to_json(cli_result)


def validate_json_response_adapter(json_data: dict) -> dict:
    """Thin wrapper for legacy validate_json_response (kept sync by design)."""
    return _legacy_validate_json_response(json_data)


# Readability / Grammar adapters

async def check_readability(arguments: dict[str, Any]) -> dict[str, Any]:
    request = ToolRequest(
        episode_number=arguments["episode_number"],
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = CheckReadabilityTool()
    response = tool.execute(request)
    result = {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": issue.type,
                "severity": issue.severity,
                "message": issue.message,
                "line_number": issue.line_number,
                "suggestion": issue.suggestion,
            }
            for issue in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }
    return _apply_lightweight_output(result, arguments)


async def check_grammar(arguments: dict[str, Any]) -> dict[str, Any]:
    request = ToolRequest(
        episode_number=arguments["episode_number"],
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = CheckGrammarTool()
    response = tool.execute(request)
    result = {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": issue.type,
                "severity": issue.severity,
                "message": issue.message,
                "line_number": issue.line_number,
                "suggestion": issue.suggestion,
            }
            for issue in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }
    return _apply_lightweight_output(result, arguments)


async def check_style(arguments: dict[str, Any]) -> dict[str, Any]:
    request = ToolRequest(
        episode_number=arguments.get("episode_number", 1),
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = CheckStyleTool()
    response = tool.execute(request)
    result = {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": issue.type,
                "severity": issue.severity,
                "message": issue.message,
                "line_number": issue.line_number,
                "suggestion": issue.suggestion,
            }
            for issue in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }
    return _apply_lightweight_output(result, arguments)


async def run_quality_checks(arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute the consolidated quality check workflow via the presentation adapter.

    Args:
        arguments: Raw MCP payload containing ``episode_number`` and optional metadata.

    Returns:
        dict[str, Any]: Normalised payload with score, issues, execution time, and metadata.
    """
    request = ToolRequest(
        episode_number=arguments["episode_number"],
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = RunQualityChecksTool()
    response = tool.execute(request)
    result = {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": issue.type,
                "severity": issue.severity,
                "message": issue.message,
                "line_number": issue.line_number,
                "suggestion": issue.suggestion,
                "end_line_number": getattr(issue, "end_line_number", None),
                "file_path": getattr(issue, "file_path", None),
                "line_hash": getattr(issue, "line_hash", None),
                "block_hash": getattr(issue, "block_hash", None),
                "reason_code": getattr(issue, "reason_code", None),
                "details": getattr(issue, "details", None),
                "issue_id": getattr(issue, "issue_id", None),
            }
            for issue in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }
    return _apply_lightweight_output(result, arguments)


async def improve_quality_until(arguments: dict[str, Any]) -> dict[str, Any]:
    """Iteratively improve manuscript quality using the presentation adapter.

    Args:
        arguments: Raw MCP payload containing ``episode_number`` and improvement parameters.

    Returns:
        dict[str, Any]: Normalised payload containing score progression and metadata.
    """
    request = ToolRequest(
        episode_number=arguments["episode_number"],
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = ImproveQualityUntilTool()
    response = tool.execute(request)
    result = {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": issue.type,
                "severity": issue.severity,
                "message": issue.message,
                "line_number": issue.line_number,
                "suggestion": issue.suggestion,
                "end_line_number": getattr(issue, "end_line_number", None),
                "file_path": getattr(issue, "file_path", None),
                "line_hash": getattr(issue, "line_hash", None),
                "block_hash": getattr(issue, "block_hash", None),
                "reason_code": getattr(issue, "reason_code", None),
                "details": getattr(issue, "details", None),
                "issue_id": getattr(issue, "issue_id", None),
            }
            for issue in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }
    return _apply_lightweight_output(result, arguments)


async def fix_quality_issues(arguments: dict[str, Any]) -> dict[str, Any]:
    """Apply lightweight fixes using the quality issues tool."""

    request = ToolRequest(
        episode_number=arguments["episode_number"],
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = FixQualityIssuesTool()
    response = tool.execute(request)
    result = {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": issue.type,
                "severity": issue.severity,
                "message": issue.message,
                "line_number": issue.line_number,
                "suggestion": issue.suggestion,
                "end_line_number": getattr(issue, "end_line_number", None),
                "file_path": getattr(issue, "file_path", None),
                "line_hash": getattr(issue, "line_hash", None),
                "block_hash": getattr(issue, "block_hash", None),
                "reason_code": getattr(issue, "reason_code", None),
                "details": getattr(issue, "details", None),
                "issue_id": getattr(issue, "issue_id", None),
            }
            for issue in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }
    return _apply_lightweight_output(result, arguments)


async def get_issue_context(arguments: dict[str, Any]) -> dict[str, Any]:
    """Return contextual snippets around detected quality issues."""

    request = ToolRequest(
        episode_number=arguments["episode_number"],
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = GetIssueContextTool()
    response = tool.execute(request)
    return {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": issue.type,
                "severity": issue.severity,
                "message": issue.message,
                "line_number": issue.line_number,
                "suggestion": issue.suggestion,
                "end_line_number": getattr(issue, "end_line_number", None),
                "file_path": getattr(issue, "file_path", None),
                "line_hash": getattr(issue, "line_hash", None),
                "block_hash": getattr(issue, "block_hash", None),
                "reason_code": getattr(issue, "reason_code", None),
                "details": getattr(issue, "details", None),
                "issue_id": getattr(issue, "issue_id", None),
            }
            for issue in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }


async def export_quality_report(arguments: dict[str, Any]) -> dict[str, Any]:
    """Export quality reports in the requested format."""

    request = ToolRequest(
        episode_number=arguments["episode_number"],
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = ExportQualityReportTool()
    response = tool.execute(request)
    result = {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": issue.type,
                "severity": issue.severity,
                "message": issue.message,
                "line_number": issue.line_number,
                "suggestion": issue.suggestion,
                "end_line_number": getattr(issue, "end_line_number", None),
                "file_path": getattr(issue, "file_path", None),
                "line_hash": getattr(issue, "line_hash", None),
                "block_hash": getattr(issue, "block_hash", None),
                "reason_code": getattr(issue, "reason_code", None),
                "details": getattr(issue, "details", None),
                "issue_id": getattr(issue, "issue_id", None),
            }
            for issue in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }
    return _apply_lightweight_output(result, arguments)


async def analyze_test_results(arguments: dict[str, Any]) -> dict[str, Any]:
    request = ToolRequest(
        episode_number=arguments.get("episode_number", 1),
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = ResultAnalysisTool()
    response = tool.execute(request)
    return {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": issue.type,
                "severity": issue.severity,
                "message": issue.message,
                "line_number": issue.line_number,
                "suggestion": issue.suggestion,
            }
            for issue in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }


async def backup_management(arguments: dict[str, Any]) -> dict[str, Any]:
    """Run BackupTool and normalise its response.

    Supports operations like create/list/restore/delete based on additional_params.
    """
    request = ToolRequest(
        episode_number=arguments.get("episode_number", 1),
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = BackupTool()
    response = tool.execute(request)
    result = {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": issue.type,
                "severity": issue.severity,
                "message": issue.message,
                "line_number": issue.line_number,
                "suggestion": issue.suggestion,
            }
            for issue in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }
    return _apply_lightweight_output(result, arguments)


# Polish adapters

async def polish_manuscript(arguments: dict[str, Any]) -> dict[str, Any]:
    request = ToolRequest(
        episode_number=arguments["episode_number"],
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = PolishManuscriptTool()
    response = tool.execute(request)
    result = {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": i.type,
                "severity": i.severity,
                "message": i.message,
                "line_number": i.line_number,
                "suggestion": i.suggestion,
                "end_line_number": getattr(i, "end_line_number", None),
                "file_path": getattr(i, "file_path", None),
                "line_hash": getattr(i, "line_hash", None),
                "block_hash": getattr(i, "block_hash", None),
                "reason_code": getattr(i, "reason_code", None),
                "details": getattr(i, "details", None),
                "issue_id": getattr(i, "issue_id", None),
            }
            for i in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }
    return _apply_lightweight_output(result, arguments)


async def polish_manuscript_apply(arguments: dict[str, Any]) -> dict[str, Any]:
    # Preflight: Extract and validate Creative Intention if provided
    intention, ci_error = _extract_creative_intention(arguments)
    is_valid, error_response = _validate_creative_intention_for_polish(intention, ci_error)

    if not is_valid:
        # Return error response without executing tool
        return error_response or {
            "success": False,
            "error_type": "CreativeIntentionDeserializationError",
            "metadata": {"error_count": 0},
        }

    request = ToolRequest(
        episode_number=arguments["episode_number"],
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool_factory = _get_tool_class_with_fallback("PolishManuscriptApplyTool")
    tool = tool_factory() if tool_factory is not None else PolishManuscriptApplyTool()
    response = tool.execute(request)
    result = {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": i.type,
                "severity": i.severity,
                "message": i.message,
                "line_number": i.line_number,
                "suggestion": i.suggestion,
                "end_line_number": getattr(i, "end_line_number", None),
                "file_path": getattr(i, "file_path", None),
                "line_hash": getattr(i, "line_hash", None),
                "block_hash": getattr(i, "block_hash", None),
                "reason_code": getattr(i, "reason_code", None),
                "details": getattr(i, "details", None),
                "issue_id": getattr(i, "issue_id", None),
            }
            for i in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }

    # Add Creative Intention metadata if validation succeeded
    if intention is not None:
        result["metadata"]["creative_intention_validated"] = True
        result["metadata"]["creative_intention_episode"] = intention.episode_number

    return _apply_lightweight_output(result, arguments)


async def restore_manuscript_from_artifact(arguments: dict[str, Any]) -> dict[str, Any]:
    request = ToolRequest(
        episode_number=arguments["episode_number"],
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = RestoreManuscriptFromArtifactTool()
    response = tool.execute(request)
    result = {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": i.type,
                "severity": i.severity,
                "message": i.message,
                "line_number": i.line_number,
                "suggestion": i.suggestion,
                "end_line_number": getattr(i, "end_line_number", None),
                "file_path": getattr(i, "file_path", None),
                "line_hash": getattr(i, "line_hash", None),
                "block_hash": getattr(i, "block_hash", None),
                "reason_code": getattr(i, "reason_code", None),
                "details": getattr(i, "details", None),
                "issue_id": getattr(i, "issue_id", None),
            }
            for i in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }
    return _apply_lightweight_output(result, arguments)


async def polish(arguments: dict[str, Any]) -> dict[str, Any]:
    request = ToolRequest(
        episode_number=arguments["episode_number"],
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = PolishTool()
    response = tool.execute(request)
    result = {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": i.type,
                "severity": i.severity,
                "message": i.message,
                "line_number": i.line_number,
                "suggestion": i.suggestion,
                "end_line_number": getattr(i, "end_line_number", None),
                "file_path": getattr(i, "file_path", None),
                "line_hash": getattr(i, "line_hash", None),
                "block_hash": getattr(i, "block_hash", None),
                "reason_code": getattr(i, "reason_code", None),
                "details": getattr(i, "details", None),
                "issue_id": getattr(i, "issue_id", None),
            }
            for i in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }
    return _apply_lightweight_output(result, arguments)


# Artifact helpers (lightweight facades)

async def fetch_artifact(arguments: dict[str, Any]) -> dict[str, Any]:
    artifact_id = arguments.get("artifact_id")
    if not artifact_id:
        return {"success": False, "error": "artifact_id を指定してください"}
    section = arguments.get("section")
    fmt = arguments.get("format", "raw")
    ps = resolve_path_service(arguments.get("project_root"))
    if ps is None or not _ARTIFACT_AVAILABLE:
        return {"success": False, "error": "artifact store not available"}
    storage_dir = ps.project_root / ".noveler" / "artifacts"
    store = create_artifact_store(storage_dir=storage_dir)
    content = store.fetch(artifact_id, section=section)
    if content is None:
        return {"success": False, "error": f"アーティファクトが見つかりません: {artifact_id}"}
    if fmt == "json":
        try:
            content = json.dumps(json.loads(content), ensure_ascii=False, indent=2)
        except Exception:
            pass
    meta = store.get_metadata(artifact_id)
    return {
        "success": True,
        "artifact_id": artifact_id,
        "content": content,
        "section": section,
        "metadata": {
            "created_at": getattr(meta, "created_at", None),
            "content_type": getattr(meta, "content_type", None),
            "size_bytes": getattr(meta, "size_bytes", None),
            "source_file": getattr(meta, "source_file", None),
        },
    }


async def list_artifacts(arguments: dict[str, Any]) -> dict[str, Any]:
    ps = resolve_path_service(arguments.get("project_root"))
    if ps is None or not _ARTIFACT_AVAILABLE:
        return {"success": False, "error": "artifact store not available"}
    storage_dir = ps.project_root / ".noveler" / "artifacts"
    store = create_artifact_store(storage_dir=storage_dir)
    return {"success": True, "artifacts": store.list_artifacts()}


# Write helper (I/O)

async def write_file(arguments: dict[str, Any]) -> dict[str, Any]:
    """Write file contents relative to project root.

    Expected arguments: relative_path (str), content (str), project_root (optional).
    """
    relative_path = arguments["relative_path"]
    content = arguments["content"]
    project_root = arguments.get("project_root")
    if project_root:
        ps = resolve_path_service(project_root)
        base_path = getattr(ps, "project_root", Path(project_root).absolute()) if ps else Path(project_root).absolute()
    else:
        base_path = Path.cwd()
    file_path = base_path / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return {
        "success": True,
        "message": f"ファイルを作成しました: {relative_path}",
        "absolute_path": str(file_path),
        "relative_path": relative_path,
        "content_length": len(content),
        "project_root": str(base_path),
    }

def _apply_lightweight_output(result: dict[str, Any], arguments: dict[str, Any]) -> dict[str, Any]:
    """B20 lightweight output (opt-in). See docs/B20_Claude_Code開発作業指示書.md.

    - format: summary | ndjson | full
    - page/page_size pagination (page_size<=200)
    - ndjson: metadata.ndjson holds paged issues; issues become []
    - summary: issues reduced to reference fields
    - default: unchanged unless MCP_LIGHTWEIGHT_DEFAULT=1
    """
    try:
        issues = result.get('issues')
        if not isinstance(issues, list):
            return result
        fmt = arguments.get('format') or ('summary' if str(os.getenv('MCP_LIGHTWEIGHT_DEFAULT')) in ('1','true','on') else None)
        if not fmt or fmt == 'full':
            return result
        try:
            page = max(1, int(arguments.get('page', 1)))
        except Exception:
            page = 1
        try:
            page_size = int(arguments.get('page_size', 50))
        except Exception:
            page_size = 50
        MAX_DETAILS = 200
        page_size = min(page_size, MAX_DETAILS)
        total = len(issues)
        start = (page - 1) * page_size
        end = min(start + page_size, total)
        paged = issues[start:end] if 0 <= start < total else []
        def _ref(d):
            # support both attr and dict-like
            getter = (lambda k: getattr(d, k, None)) if not isinstance(d, dict) else (lambda k: d.get(k))
            keys = ('type','severity','line_number','end_line_number','file_path','line_hash','block_hash','reason_code','issue_id')
            return {k: getter(k) for k in keys if getter(k) is not None}
        ref_list = [_ref(i) for i in paged]
        pagination = {'page': page, 'page_size': page_size, 'total': total, 'total_pages': (total + page_size - 1)//page_size if page_size else 0}
        meta = result.setdefault('metadata', {})
        meta['total_issues'] = total
        meta['returned_issues'] = len(ref_list)
        meta['pagination'] = pagination
        meta['truncated'] = total > page_size
        if fmt == 'ndjson':
            ndjson_blob = '\n'.join(json.dumps(i, ensure_ascii=False) for i in ref_list)
            meta['ndjson'] = ndjson_blob
            result['issues'] = []
        else:
            result['issues'] = ref_list
        return result
    except Exception:
        return result


# --- Utility tool wrappers (convert/validate/file-info/hash) ---

async def convert_cli_to_json_util(arguments: dict[str, Any]) -> dict[str, Any]:
    return _legacy_convert_cli_to_json(arguments["cli_result"])  # type: ignore[return-value]


async def validate_json_response_util(arguments: dict[str, Any]) -> dict[str, Any]:
    return _legacy_validate_json_response(arguments["json_data"])  # type: ignore[return-value]


async def get_file_reference_info_util(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        json_adapter = importlib.import_module("mcp_servers.noveler.json_conversion_adapter")
        _gfri = getattr(json_adapter, "get_file_reference_info")
        return _gfri(arguments["file_path"])  # type: ignore[return-value]
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


async def get_file_by_hash_util(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        json_adapter = importlib.import_module("mcp_servers.noveler.json_conversion_adapter")
        _gfbh = getattr(json_adapter, "get_file_by_hash")
        return _gfbh(arguments["hash"])  # type: ignore[return-value]
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


async def check_file_changes_util(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        json_adapter = importlib.import_module("mcp_servers.noveler.json_conversion_adapter")
        _cfc = getattr(json_adapter, "check_file_changes")
        return _cfc(arguments["file_paths"])  # type: ignore[return-value]
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


async def list_files_with_hashes_util(arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        json_adapter = importlib.import_module("mcp_servers.noveler.json_conversion_adapter")
        _lfwh = getattr(json_adapter, "list_files_with_hashes")
        return _lfwh()  # type: ignore[return-value]
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


# --- Progressive writing: tasks/step/status ---

async def get_writing_tasks(arguments: dict[str, Any]) -> dict[str, Any]:
    episode_number = int(arguments["episode_number"])
    project_root = arguments.get("project_root")
    if project_root:
        ps = resolve_path_service(project_root)
        resolved_project_root = str(getattr(ps, "project_root", Path(project_root).absolute())) if ps else str(Path(project_root).absolute())
    else:
        resolved_project_root = str(Path.cwd())
    try:
        factory_module = importlib.import_module("noveler.infrastructure.factories.progressive_write_manager_factory")
        _cpwm = getattr(factory_module, "create_progressive_write_manager")
        task_manager = _cpwm(resolved_project_root, episode_number)
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}
    tasks_info = task_manager.get_writing_tasks()
    return {
        "success": True,
        "episode_number": episode_number,
        "tasks_info": tasks_info,
        "message": "タスクリスト取得完了",
        "execution_method": "progressive_task_manager",
    }


async def execute_writing_step(arguments: dict[str, Any]) -> dict[str, Any]:
    episode_number = int(arguments["episode_number"])
    step_id = arguments["step_id"]
    project_root = arguments.get("project_root")
    dry_run = arguments.get("dry_run", False)
    if project_root:
        ps = resolve_path_service(project_root)
        resolved_project_root = str(getattr(ps, "project_root", Path(project_root).absolute())) if ps else str(Path(project_root).absolute())
    else:
        resolved_project_root = str(Path.cwd())
    try:
        factory_module = importlib.import_module("noveler.infrastructure.factories.progressive_write_manager_factory")
        _cpwm = getattr(factory_module, "create_progressive_write_manager")
        task_manager = _cpwm(resolved_project_root, episode_number)
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}
    execution_result = await task_manager.execute_writing_step_async(step_id, dry_run)
    return {
        "success": execution_result.get("success", True),
        "episode_number": episode_number,
        "step_id": step_id,
        "dry_run": dry_run,
        "execution_result": execution_result,
        "message": "ステップ実行完了" if execution_result.get("success", True) else "ステップ実行失敗",
        "execution_method": "progressive_task_manager",
    }


async def get_task_status(arguments: dict[str, Any]) -> dict[str, Any]:
    episode_number = int(arguments["episode_number"])
    project_root = arguments.get("project_root")
    if project_root:
        ps = resolve_path_service(project_root)
        resolved_project_root = str(getattr(ps, "project_root", Path(project_root).absolute())) if ps else str(Path(project_root).absolute())
    else:
        resolved_project_root = str(Path.cwd())
    try:
        factory_module = importlib.import_module("noveler.infrastructure.factories.progressive_write_manager_factory")
        _cpwm = getattr(factory_module, "create_progressive_write_manager")
        task_manager = _cpwm(resolved_project_root, episode_number)
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}
    status_info = task_manager.get_task_status()
    return {
        "success": True,
        "episode_number": episode_number,
        "status_info": status_info,
        "message": "進捗状況確認完了",
        "execution_method": "progressive_task_manager",
    }


# --- Progressive check: tasks/step/status/history ---

async def get_check_tasks(arguments: dict[str, Any]) -> dict[str, Any]:
    episode_number = int(arguments["episode_number"])
    check_type = arguments.get("check_type", "all")
    project_root = arguments.get("project_root")
    if project_root:
        ps = resolve_path_service(project_root)
        resolved_project_root = str(getattr(ps, "project_root", Path(project_root).absolute())) if ps else str(Path(project_root).absolute())
    else:
        resolved_project_root = str(Path.cwd())
    try:
        check_module = importlib.import_module("noveler.domain.services.progressive_check_manager")
        _PCM = getattr(check_module, "ProgressiveCheckManager")
        check_manager = _PCM(resolved_project_root, episode_number)
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}
    tasks_info = check_manager.get_check_tasks()
    return {
        "success": True,
        "episode_number": episode_number,
        "session_id": tasks_info.get("session_id"),
        "check_type": check_type,
        "tasks_info": tasks_info,
        "message": "品質チェックタスクリスト取得完了",
        "execution_method": "progressive_check_manager",
    }


async def execute_check_step(arguments: dict[str, Any]) -> dict[str, Any]:
    episode_number = int(arguments["episode_number"])
    step_id = arguments["step_id"]
    input_data = arguments["input_data"]
    project_root = arguments.get("project_root")
    dry_run = arguments.get("dry_run", False)
    if project_root:
        ps = resolve_path_service(project_root)
        resolved_project_root = str(getattr(ps, "project_root", Path(project_root).absolute())) if ps else str(Path(project_root).absolute())
    else:
        resolved_project_root = str(Path.cwd())
    try:
        check_module = importlib.import_module("noveler.domain.services.progressive_check_manager")
        _PCM = getattr(check_module, "ProgressiveCheckManager")
        check_manager = _PCM(resolved_project_root, episode_number)
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}
    execution_result = check_manager.execute_check_step(step_id, input_data, dry_run)
    # Inject session_id when manager exposes it and result lacks it
    try:
        session_id = getattr(check_manager, "session_id", None)
        if session_id and isinstance(execution_result, dict) and "session_id" not in execution_result:
            execution_result["session_id"] = session_id
    except Exception:
        pass
    if "session_reset_required" not in execution_result:
        execution_result["session_reset_required"] = False
    return {
        "success": execution_result.get("success", True),
        "episode_number": episode_number,
        "step_id": step_id,
        "dry_run": dry_run,
        "execution_result": execution_result,
        "message": "品質チェックステップ実行完了" if execution_result.get("success", True) else "品質チェックステップ実行失敗",
        "execution_method": "progressive_check_manager",
    }


async def get_check_status(arguments: dict[str, Any]) -> dict[str, Any]:
    episode_number = int(arguments["episode_number"])
    project_root = arguments.get("project_root")
    if project_root:
        ps = resolve_path_service(project_root)
        resolved_project_root = str(getattr(ps, "project_root", Path(project_root).absolute())) if ps else str(Path(project_root).absolute())
    else:
        resolved_project_root = str(Path.cwd())
    try:
        check_module = importlib.import_module("noveler.domain.services.progressive_check_manager")
        _PCM = getattr(check_module, "ProgressiveCheckManager")
        check_manager = _PCM(resolved_project_root, episode_number)
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}
    status_info = check_manager.get_check_status()
    session_id = getattr(check_manager, "session_id", None)
    if session_id and isinstance(status_info, dict) and "session_id" not in status_info:
        status_info["session_id"] = session_id
    return {
        "success": True,
        "episode_number": episode_number,
        "session_id": status_info.get("session_id", session_id),
        "status_info": status_info,
        "message": "品質チェック進捗状況確認完了",
        "execution_method": "progressive_check_manager",
    }


async def get_check_history(arguments: dict[str, Any]) -> dict[str, Any]:
    episode_number = int(arguments["episode_number"])
    limit = arguments.get("limit", 10)
    project_root = arguments.get("project_root")
    if project_root:
        ps = resolve_path_service(project_root)
        resolved_project_root = str(getattr(ps, "project_root", Path(project_root).absolute())) if ps else str(Path(project_root).absolute())
    else:
        resolved_project_root = str(Path.cwd())
    try:
        check_module = importlib.import_module("noveler.domain.services.progressive_check_manager")
        _PCM = getattr(check_module, "ProgressiveCheckManager")
        check_manager = _PCM(resolved_project_root, episode_number)
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}
    history_info = check_manager.get_check_history(limit)
    return {
        "success": True,
        "episode_number": episode_number,
        "limit": limit,
        "history_info": history_info,
        "message": "品質チェック履歴取得完了",
        "execution_method": "progressive_check_manager",
    }


# --- Enhanced writing helpers ---

async def enhanced_get_writing_tasks(arguments: dict[str, Any]) -> dict[str, Any]:
    episode_number = int(arguments["episode_number"])
    project_root = arguments.get("project_root")
    if project_root:
        ps = resolve_path_service(project_root)
        resolved_project_root = str(getattr(ps, "project_root", Path(project_root).absolute())) if ps else str(Path(project_root).absolute())
    else:
        resolved_project_root = str(Path.cwd())
    try:
        use_case_module = importlib.import_module("noveler.application.use_cases.enhanced_writing_use_case")
        EnhancedWritingUseCase = getattr(use_case_module, "EnhancedWritingUseCase")
        uc = EnhancedWritingUseCase(resolved_project_root, episode_number)
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}
    tasks = uc.get_writing_tasks_with_error_handling()
    return {"success": True, "episode_number": episode_number, "tasks": tasks, "execution_method": "enhanced_use_case"}


async def enhanced_execute_writing_step(arguments: dict[str, Any]) -> dict[str, Any]:
    episode_number = int(arguments["episode_number"])
    step_id = int(arguments["step_id"])  # allow numeric
    dry_run = bool(arguments.get("dry_run", False))
    project_root = arguments.get("project_root")
    if project_root:
        ps = resolve_path_service(project_root)
        resolved_project_root = str(getattr(ps, "project_root", Path(project_root).absolute())) if ps else str(Path(project_root).absolute())
    else:
        resolved_project_root = str(Path.cwd())

    # Preflight: For Step 12, validate Creative Intention if provided
    intention: Any | None = None
    if step_id == 12:
        intention, ci_error = _extract_creative_intention(arguments)
        is_valid, error_response = _validate_creative_intention_for_polish(intention, ci_error)
        if not is_valid:
            # Return error response without executing
            return error_response or {
                "success": False,
                "error_type": "CreativeIntentionDeserializationError",
                "metadata": {"error_count": 0},
            }

    try:
        use_case_module = importlib.import_module("noveler.application.use_cases.enhanced_writing_use_case")
        EnhancedWritingUseCase = getattr(use_case_module, "EnhancedWritingUseCase")
        uc = EnhancedWritingUseCase(resolved_project_root, episode_number)
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}
    result = await uc.execute_writing_step_with_recovery_async(step_id, dry_run, enable_recovery=True)
    if step_id == 12 and intention is not None:
        metadata = result.setdefault("metadata", {})
        metadata["creative_intention_validated"] = True
        metadata["creative_intention_episode"] = getattr(intention, "episode_number", None)
    return {"success": result.get("success", True), "episode_number": episode_number, "step_id": step_id, "result": result, "execution_method": "enhanced_use_case"}


async def enhanced_resume_from_partial_failure(arguments: dict[str, Any]) -> dict[str, Any]:
    episode_number = int(arguments["episode_number"])
    recovery_point = int(arguments["recovery_point"])  # step index
    project_root = arguments.get("project_root")
    if project_root:
        ps = resolve_path_service(project_root)
        resolved_project_root = str(getattr(ps, "project_root", Path(project_root).absolute())) if ps else str(Path(project_root).absolute())
    else:
        resolved_project_root = str(Path.cwd())
    try:
        use_case_module = importlib.import_module("noveler.application.use_cases.enhanced_writing_use_case")
        EnhancedWritingUseCase = getattr(use_case_module, "EnhancedWritingUseCase")
        uc = EnhancedWritingUseCase(resolved_project_root, episode_number)
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}
    result = await uc.resume_from_partial_failure_async(recovery_point)
    return {"success": result.get("success", True), "episode_number": episode_number, "recovery_point": recovery_point, "result": result, "execution_method": "enhanced_use_case"}


# --- Episode preview generation ---

async def generate_episode_preview(arguments: dict[str, Any]) -> dict[str, Any]:
    tool_name = "generate_episode_preview"
    try:
        episode_number = int(arguments["episode_number"])
    except KeyError as exc:
        return {"success": False, "error": f"missing field: {exc.args[0]}", "tool": tool_name}
    except Exception as exc:
        return {"success": False, "error": f"invalid episode_number: {exc!s}", "tool": tool_name}

    project_name = arguments.get("project_name") or arguments.get("project_root")
    additional_params = {k: v for k, v in arguments.items() if k not in {"episode_number", "project_name", "project_root"}}

    try:
        request = ToolRequest(episode_number=episode_number, project_name=project_name, additional_params=additional_params or None)
        try:
            preview_module = importlib.import_module("mcp_servers.noveler.tools.generate_episode_preview_tool")
            GenerateEpisodePreviewTool = getattr(preview_module, "GenerateEpisodePreviewTool")
            tool = GenerateEpisodePreviewTool()
        except ImportError as e:
            return {"success": False, "error": f"モジュールが見つかりません: {e}", "tool": tool_name}
        response = tool.execute(request)
        issues = [{"type": i.type, "severity": i.severity, "message": i.message, "line_number": i.line_number, "suggestion": i.suggestion} for i in response.issues]
        metadata = dict(response.metadata)
        return {
            "success": response.success,
            "score": response.score,
            "issues": issues,
            "execution_time_ms": response.execution_time_ms,
            "metadata": metadata,
            "preview_text": metadata.get("preview_text"),
            "preview": metadata.get("preview", {}),
            "quality": metadata.get("quality", {}),
            "source": metadata.get("source", {}),
            "config": metadata.get("config", {}),
        }
    except Exception as exc:
        return {"success": False, "error": str(exc), "tool": tool_name}


# --- Status helper ---

async def status(arguments: dict[str, Any]) -> dict[str, Any]:
    project_root = arguments.get("project_root")
    try:
        main_module = importlib.import_module("mcp_servers.noveler.main")
        _exec_status = getattr(main_module, "execute_status_command")
        return await _exec_status(project_root)
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


# --- Conversation design helpers ---

async def design_conversations(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        conv_module = importlib.import_module("mcp_servers.noveler.tools.conversation_design_tool")
        _fn = getattr(conv_module, "design_conversations_tool")
        return _fn(arguments["episode_number"], arguments["scene_number"], arguments["dialogues"])  # type: ignore[return-value]
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


async def track_emotions(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        conv_module = importlib.import_module("mcp_servers.noveler.tools.conversation_design_tool")
        _fn = getattr(conv_module, "track_emotions_tool")
        return _fn(arguments["emotions"])  # type: ignore[return-value]
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


async def design_scenes(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        conv_module = importlib.import_module("mcp_servers.noveler.tools.conversation_design_tool")
        _fn = getattr(conv_module, "design_scenes_tool")
        return _fn(arguments["scenes"])  # type: ignore[return-value]
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


async def design_senses(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        conv_module = importlib.import_module("mcp_servers.noveler.tools.conversation_design_tool")
        _fn = getattr(conv_module, "design_senses_tool")
        return _fn(arguments["triggers"])  # type: ignore[return-value]
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


async def manage_props(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        conv_module = importlib.import_module("mcp_servers.noveler.tools.conversation_design_tool")
        _fn = getattr(conv_module, "manage_props_tool")
        return _fn(arguments["props"])  # type: ignore[return-value]
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


async def get_conversation_context(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        conv_module = importlib.import_module("mcp_servers.noveler.tools.conversation_design_tool")
        _fn = getattr(conv_module, "get_conversation_context_tool")
        return _fn(arguments["conversation_id"])  # type: ignore[return-value]
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


async def export_design_data(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        conv_module = importlib.import_module("mcp_servers.noveler.tools.conversation_design_tool")
        _fn = getattr(conv_module, "export_design_data_tool")
        return _fn(arguments["episode_number"])  # type: ignore[return-value]
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


# --- Langsmith helpers ---

async def langsmith_generate_artifacts(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        langsmith_module = importlib.import_module("mcp_servers.noveler.tools.langsmith_bugfix_tool")
        _gen = getattr(langsmith_module, "generate_langsmith_artifacts")
        return _gen(
            run_json_path=arguments.get("run_json_path"),
            run_json_content=arguments.get("run_json_content"),
            output_dir=arguments.get("output_dir"),
            dataset_name=arguments.get("dataset_name"),
            expected_behavior=arguments.get("expected_behavior"),
            project_root=arguments.get("project_root"),
        )
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


async def langsmith_apply_patch(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        langsmith_module = importlib.import_module("mcp_servers.noveler.tools.langsmith_bugfix_tool")
        _apply = getattr(langsmith_module, "apply_langsmith_patch")
        return _apply(
            patch_text=arguments.get("patch_text"),
            patch_file=arguments.get("patch_file"),
            strip=arguments.get("strip", 1),
            project_root=arguments.get("project_root"),
        )
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


async def langsmith_run_verification(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        langsmith_module = importlib.import_module("mcp_servers.noveler.tools.langsmith_bugfix_tool")
        _run = getattr(langsmith_module, "run_langsmith_verification")
        cmd = arguments.get("command") or arguments.get("verify_command")
        if cmd is None:
            return {"success": False, "error": "command を指定してください"}
        return _run(command=cmd, project_root=arguments.get("project_root"))
    except ImportError as e:
        return {"success": False, "error": f"モジュールが見つかりません: {e}"}


async def check_rhythm(arguments: dict[str, Any]) -> dict[str, Any]:
    """Run rhythm check and normalise payload similar to other checkers.

    Adds optional file_path/file_hash metadata when available to keep
    compatibility with main.py's prior behaviour.
    """
    request = ToolRequest(
        episode_number=arguments["episode_number"],
        project_name=arguments.get("project_name"),
        additional_params=arguments,
    )
    tool = CheckRhythmTool()
    response = tool.execute(request)

    result: dict[str, Any] = {
        "success": response.success,
        "score": response.score,
        "issues": [
            {
                "type": i.type,
                "severity": i.severity,
                "message": i.message,
                "line_number": i.line_number,
                "suggestion": i.suggestion,
                "end_line_number": getattr(i, "end_line_number", None),
                "file_path": getattr(i, "file_path", None),
                "line_hash": getattr(i, "line_hash", None),
                "block_hash": getattr(i, "block_hash", None),
                "reason_code": getattr(i, "reason_code", None),
                "details": getattr(i, "details", None),
                "issue_id": getattr(i, "issue_id", None),
            }
            for i in response.issues
        ],
        "execution_time_ms": response.execution_time_ms,
        "metadata": response.metadata,
    }

    # Optional: attach file_path and file_hash to metadata if available
    try:
        fp = arguments.get("file_path")
        if isinstance(fp, str):
            p = Path(fp)
            if p.exists():
                content = p.read_text(encoding="utf-8")
                result["metadata"]["file_path"] = str(p)
                result["metadata"]["file_hash"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    except Exception:
        pass

    return _apply_lightweight_output(result, arguments)


# ─────────────────────────────────────────────────────────────────────────────
# Creative Intention Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _extract_creative_intention(arguments: dict[str, Any]) -> tuple[Any | None, str | None]:
    """Extract and deserialize CreativeIntention from arguments.
    
    Args:
        arguments: Arguments dict that may contain 'creative_intention' key.
    
    Returns:
        Tuple of (CreativeIntention object or None, error message or None).
        If no creative_intention in arguments, returns (None, None).
        If creative_intention is a dict, attempts to deserialize to CreativeIntention.
        If creative_intention is already a CreativeIntention object, returns it as-is.
    """
    from noveler.domain.value_objects.creative_intention import CreativeIntention
    
    ci_raw = arguments.get("creative_intention")
    if ci_raw is None:
        # No creative intention provided
        return None, None
    
    # If already a CreativeIntention object, return as-is
    if isinstance(ci_raw, CreativeIntention):
        return ci_raw, None
    
    # If dict, attempt deserialization
    if isinstance(ci_raw, dict):
        try:
            # Reconstruct from dict (handles nested CharacterArc)
            from noveler.domain.value_objects.creative_intention import CharacterArc
            
            arc_data = ci_raw.get("character_arc", {})
            arc = CharacterArc(
                before_state=arc_data.get("before_state", ""),
                transition=arc_data.get("transition", ""),
                after_state=arc_data.get("after_state", ""),
            )
            
            intention = CreativeIntention(
                scene_goal=ci_raw.get("scene_goal", ""),
                emotional_goal=ci_raw.get("emotional_goal", ""),
                character_arc=arc,
                world_via_action=ci_raw.get("world_via_action", ""),
                voice_constraints=ci_raw.get("voice_constraints", ""),
                episode_number=ci_raw.get("episode_number"),
            )
            return intention, None
        except Exception as e:
            return None, f"Failed to deserialize creative_intention: {e}"
    
    # Otherwise, invalid type
    return None, f"creative_intention must be dict or CreativeIntention, got {type(ci_raw).__name__}"


def _validate_creative_intention_for_polish(
    intention: Any | None, error: str | None
) -> tuple[bool, dict[str, Any] | None]:
    """Validate CreativeIntention for polish_manuscript_apply.
    
    Args:
        intention: CreativeIntention object or None.
        error: Deserialization error message or None.
    
    Returns:
        Tuple of (is_valid: bool, error_response_dict or None).
        
    Validation rules:
    - If error is not None (deserialization failed), return False with error_response.
    - If intention is None and error is None, return True (optional field).
    - If intention is a valid CreativeIntention object, return True.
    """
    if error is not None:
        # Deserialization error
        return False, {
            "success": False,
            "error_type": "CreativeIntentionDeserializationError",
            "error_message": error,
            "validation_issues": [error],
            "metadata": {"error_count": 1},
        }
    
    if intention is None:
        # Optional field - no error if not provided
        return True, None
    
    # intention is valid
    return True, None


def _get_tool_class_with_fallback(tool_name: str) -> Callable[[], Any] | None:
    """Return a tool factory callable for the requested tool.

    Tests may monkeypatch a tool class (or factory) directly on this module; we
    honour that first before falling back to the statically imported classes.

    Args:
        tool_name: Name of the tool (e.g. "PolishManuscriptApplyTool").

    Returns:
        Zero-argument callable yielding a tool instance when invoked, or None
        when the tool is unknown.
    """
    override = globals().get(tool_name)
    if callable(override):
        return override  # type: ignore[return-value]

    tool_map: dict[str, Callable[[], Any]] = {
        "PolishManuscriptApplyTool": PolishManuscriptApplyTool,
        "RunQualityChecksTool": RunQualityChecksTool,
        "CheckReadabilityTool": CheckReadabilityTool,
        "CheckGrammarTool": CheckGrammarTool,
        "CheckStyleTool": CheckStyleTool,
        "CheckRhythmTool": CheckRhythmTool,
        "PolishManuscriptTool": PolishManuscriptTool,
        "BackupTool": BackupTool,
        "FixQualityIssuesTool": FixQualityIssuesTool,
    }

    return tool_map.get(tool_name)
