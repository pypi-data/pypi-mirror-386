# File: src/noveler/presentation/mcp/entrypoints.py
# Purpose: Expose presentation-layer MCP tool wrappers for CLI/server compatibility.
# Context: Keeps mcp_servers.noveler.main thin by delegating tool execution to
#          presentation adapters while preserving legacy import paths for the CLI facade.
"""Presentation-layer execution wrappers for MCP tools.

The server entrypoint and CLI adapter historically imported coroutine helpers from
``mcp_servers.noveler.main``. This module centralises those helpers so the main
module can simply re-export them while remaining a thin delegate layer.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from noveler.domain.utils.domain_logging import capture_domain_logs
from noveler.presentation.mcp.adapters import handlers
from noveler.presentation.shared.shared_utilities import get_console


AsyncHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


async def _safe_async(
    tool_name: str,
    func: AsyncHandler,
    arguments: dict[str, Any],
    *,
    include_arguments: bool = False,
) -> dict[str, Any]:
    """Run the handler and convert exceptions into structured error payloads."""

    with capture_domain_logs() as domain_logs:
        try:
            result = await func(arguments)
        except Exception as exc:  # pragma: no cover - exercised via specialised tests
            error_result: dict[str, Any] = {
                "success": False,
                "error": str(exc),
                "tool": tool_name,
            }
            if include_arguments:
                error_result["arguments"] = arguments
            if domain_logs:
                error_result["domain_logs"] = list(domain_logs)
            return error_result

    if isinstance(result, dict):
        if domain_logs:
            metadata = result.setdefault("metadata", {})
            # Preserve existing metadata, appending logs under a dedicated key.
            metadata.setdefault("domain_logs", list(domain_logs))
    return result


async def execute_run_quality_checks(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("run_quality_checks", handlers.run_quality_checks, arguments)


async def execute_improve_quality_until(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("improve_quality_until", handlers.improve_quality_until, arguments)


async def execute_fix_quality_issues(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("fix_quality_issues", handlers.fix_quality_issues, arguments)


async def execute_get_issue_context(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("get_issue_context", handlers.get_issue_context, arguments)


async def execute_export_quality_report(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("export_quality_report", handlers.export_quality_report, arguments)


async def execute_list_quality_presets(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("list_quality_presets", handlers.list_quality_presets, arguments)


async def execute_get_quality_schema(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("get_quality_schema", handlers.get_quality_schema, arguments)


async def execute_check_readability(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("check_readability", handlers.check_readability, arguments)


async def execute_check_grammar(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("check_grammar", handlers.check_grammar, arguments)


async def execute_check_style(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("check_style", handlers.check_style, arguments)


async def execute_polish_manuscript(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("polish_manuscript", handlers.polish_manuscript, arguments)


async def execute_polish_manuscript_apply(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("polish_manuscript_apply", handlers.polish_manuscript_apply, arguments)


async def execute_restore_manuscript_from_artifact(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async(
        "restore_manuscript_from_artifact",
        handlers.restore_manuscript_from_artifact,
        arguments,
    )


async def execute_polish(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("polish", handlers.polish, arguments)


async def execute_backup_management(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("backup_management", handlers.backup_management, arguments)


async def execute_test_result_analysis(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("test_result_analysis", handlers.analyze_test_results, arguments)


async def execute_fetch_artifact(arguments: dict[str, Any]) -> dict[str, Any]:
    with capture_domain_logs() as domain_logs:
        try:
            result = await handlers.fetch_artifact(arguments)
        except Exception as exc:  # pragma: no cover - depends on optional services
            get_console().print_error(f"❌ fetch_artifactエラー: {exc}")
            error_result = {"success": False, "error": str(exc)}
            if domain_logs:
                error_result["domain_logs"] = list(domain_logs)
            return error_result

    if isinstance(result, dict) and domain_logs:
        metadata = result.setdefault("metadata", {})
        metadata.setdefault("domain_logs", list(domain_logs))
    return result


async def execute_list_artifacts(arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        return await handlers.list_artifacts(arguments)
    except Exception as exc:  # pragma: no cover - depends on optional services
        get_console().print_error(f"❌ list_artifactsエラー: {exc}")
        return {"success": False, "error": str(exc)}


async def execute_write_file(arguments: dict[str, Any]) -> dict[str, Any]:
    return await _safe_async("write", handlers.write_file, arguments, include_arguments=True)


# Enhanced writing use case tools
async def execute_enhanced_get_writing_tasks(arguments: dict[str, Any]) -> dict[str, Any]:
    """18ステップ執筆タスクリストの取得"""
    return await _safe_async("enhanced_get_writing_tasks", handlers.enhanced_get_writing_tasks, arguments)


async def execute_enhanced_execute_writing_step(arguments: dict[str, Any]) -> dict[str, Any]:
    """指定された執筆ステップの実行"""
    return await _safe_async("enhanced_execute_writing_step", handlers.enhanced_execute_writing_step, arguments)


async def execute_enhanced_resume_from_partial_failure(arguments: dict[str, Any]) -> dict[str, Any]:
    """部分失敗からの執筆再開"""
    return await _safe_async("enhanced_resume_from_partial_failure", handlers.enhanced_resume_from_partial_failure, arguments)


# Progressive check tools (compliance)
async def execute_get_check_tasks(arguments: dict[str, Any]) -> dict[str, Any]:
    """チェックタスクリストの取得"""
    return await _safe_async("get_check_tasks", handlers.get_check_tasks, arguments)


async def execute_check_step_command(arguments: dict[str, Any]) -> dict[str, Any]:
    """チェックステップの実行"""
    return await _safe_async("execute_check_step", handlers.execute_check_step, arguments)


async def execute_get_check_status(arguments: dict[str, Any]) -> dict[str, Any]:
    """チェックステータスの取得"""
    return await _safe_async("get_check_status", handlers.get_check_status, arguments)


async def execute_get_check_history(arguments: dict[str, Any]) -> dict[str, Any]:
    """チェック履歴の取得"""
    return await _safe_async("get_check_history", handlers.get_check_history, arguments)


async def execute_generate_episode_preview(arguments: dict[str, Any]) -> dict[str, Any]:
    """エピソードプレビューの生成"""
    return await _safe_async("generate_episode_preview", handlers.generate_episode_preview, arguments)
