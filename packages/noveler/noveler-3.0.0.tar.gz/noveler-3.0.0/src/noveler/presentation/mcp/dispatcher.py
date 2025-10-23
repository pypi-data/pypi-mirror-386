#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/dispatcher.py
# Purpose: Centralise MCP tool dispatch mapping for presentation-layer adapters.
# Context: Provides a thin indirection so the legacy MCP server can delegate
#          tool execution without hard-coding branching logic, supporting
#          gradual layering toward clean architecture boundaries.
"""Presentation-layer dispatcher for MCP tool handlers."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from noveler.presentation.mcp.adapters import handlers
from noveler.presentation.mcp import entrypoints as eps

ToolHandler = Callable[[dict[str, Any]], Any | Awaitable[Any]]

# Mapping of tool names to their presentation-layer handlers.
_TOOL_DISPATCH_TABLE: dict[str, ToolHandler] = {
    "run_quality_checks": handlers.run_quality_checks,
    "improve_quality_until": handlers.improve_quality_until,
    "fix_quality_issues": handlers.fix_quality_issues,
    "get_issue_context": handlers.get_issue_context,
    "export_quality_report": handlers.export_quality_report,
    "list_quality_presets": handlers.list_quality_presets,
    "get_quality_schema": handlers.get_quality_schema,
    "check_readability": handlers.check_readability,
    "check_grammar": handlers.check_grammar,
    "check_style": handlers.check_style,
    "test_result_analysis": handlers.analyze_test_results,
    "backup_management": handlers.backup_management,
    "polish_manuscript": handlers.polish_manuscript,
    "polish_manuscript_apply": handlers.polish_manuscript_apply,
    "restore_manuscript_from_artifact": handlers.restore_manuscript_from_artifact,
    "polish": handlers.polish,
    "fetch_artifact": handlers.fetch_artifact,
    "list_artifacts": handlers.list_artifacts,
    "write_file": handlers.write_file,

    "convert_cli_to_json": handlers.convert_cli_to_json_util,
    "validate_json_response": handlers.validate_json_response_util,
    "get_file_reference_info": handlers.get_file_reference_info_util,
    "get_file_by_hash": handlers.get_file_by_hash_util,
    "check_file_changes": handlers.check_file_changes_util,
    "list_files_with_hashes": handlers.list_files_with_hashes_util,
    "get_check_tasks": handlers.get_check_tasks,
    "execute_check_step": handlers.execute_check_step,
    "get_check_status": handlers.get_check_status,
    "get_check_history": handlers.get_check_history,
    "get_writing_tasks": handlers.get_writing_tasks,
    "execute_writing_step": handlers.execute_writing_step,
    "get_task_status": handlers.get_task_status,
    "enhanced_get_writing_tasks": handlers.enhanced_get_writing_tasks,
    "enhanced_execute_writing_step": handlers.enhanced_execute_writing_step,
    "enhanced_resume_from_partial_failure": handlers.enhanced_resume_from_partial_failure,
    "generate_episode_preview": handlers.generate_episode_preview,
    "status": handlers.status,
    "write": handlers.write_file,
    "design_conversations": handlers.design_conversations,
    "track_emotions": handlers.track_emotions,
    "design_scenes": handlers.design_scenes,
    "design_senses": handlers.design_senses,
    "manage_props": handlers.manage_props,
    "get_conversation_context": handlers.get_conversation_context,
    "export_design_data": handlers.export_design_data,
    "langsmith_generate_artifacts": handlers.langsmith_generate_artifacts,
    "langsmith_apply_patch": handlers.langsmith_apply_patch,
    "langsmith_run_verification": handlers.langsmith_run_verification,
    "check_rhythm": handlers.check_rhythm,}


def get_handler(name: str) -> ToolHandler | None:
    """Return the registered presentation-layer handler for a tool.

    Args:
        name: MCP tool identifier (e.g., ``"run_quality_checks"``).

    Returns:
        Callable or ``None`` when the tool is not managed by the presentation dispatcher.
    """

    return _TOOL_DISPATCH_TABLE.get(name)


async def dispatch(name: str, arguments: dict[str, Any]) -> Any:
    """Execute the presentation-layer handler when registered.

    Args:
        name: Tool identifier from the MCP request.
        arguments: Payload forwarded by the MCP runtime.

    Returns:
        Any: Normalised handler result when the tool is registered, otherwise ``None``.
    """

    handler = get_handler(name)
    if handler is None:
        return None
    result = handler(arguments)
    if inspect.isawaitable(result):
        return await result
    return result


def get_registered_tools() -> set[str]:
    """Return the set of tool names managed by the dispatcher (useful for tests)."""

    return set(_TOOL_DISPATCH_TABLE.keys())
