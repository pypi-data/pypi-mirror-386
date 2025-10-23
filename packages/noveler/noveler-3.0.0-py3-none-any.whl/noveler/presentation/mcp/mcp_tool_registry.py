# File: src/noveler/presentation/mcp/mcp_tool_registry.py
# Purpose: MCP tool registration, discovery, and metadata management
# Context: Consolidated from server_runtime.py for SOLID-SRP compliance (B20 §3)

"""MCP tool registry for Noveler server.

Provides decorator-based tool registration and discovery mechanism
for MCP protocol compliance.

This module consolidates tool registration logic from server_runtime.py
(lines 388-1133) as part of B20 §3 refactoring.

Functions:
    list_tools_async: List all registered MCP tools (async)
    get_legacy_tools: Get legacy tool definitions (backward compatibility)

Preconditions:
    - MCP Tool classes must be importable
    - FastMCP server instance must be available

Side Effects:
    - Imports tool classes on-demand (lazy loading)
    - Returns Tool metadata for MCP protocol

Raises:
    Never raises - errors are logged and empty list returned
"""

import importlib
from typing import Any

from mcp.types import Tool


# Global tool registry for decorator-based registration
_tool_registry: dict[str, Any] = {}


async def list_tools_async() -> list[Tool]:
    """List all registered MCP tools (async version).

    Returns:
        List of Tool metadata objects for MCP protocol

    Raises:
        Never raises - falls back to legacy implementation on errors
    """
    try:
        # Delegate to presentation layer registry if available
        from noveler.presentation.mcp.tool_registry import get_tools_async

        return await get_tools_async()
    except Exception:
        # Fallback to legacy implementation
        return await get_legacy_tools()


async def get_legacy_tools() -> list[Tool]:
    """Get legacy tool definitions for backward compatibility.

    Returns:
        List of Tool metadata objects (legacy format)

    Raises:
        Never raises - returns empty list on errors
    """
    # Import tool classes lazily
    try:
        BackupTool = _get_tool_class("BackupTool")
        CheckGrammarTool = _get_tool_class("CheckGrammarTool")
        CheckReadabilityTool = _get_tool_class("CheckReadabilityTool")
        CheckRhythmTool = _get_tool_class("CheckRhythmTool")
        RunQualityChecksTool = _get_tool_class("RunQualityChecksTool")
        ImproveQualityUntilTool = _get_tool_class("ImproveQualityUntilTool")
        FixQualityIssuesTool = _get_tool_class("FixQualityIssuesTool")
        GetIssueContextTool = _get_tool_class("GetIssueContextTool")
        ExportQualityReportTool = _get_tool_class("ExportQualityReportTool")
        CheckStyleTool = _get_tool_class("CheckStyleTool")
        PolishManuscriptTool = _get_tool_class("PolishManuscriptTool")
        PolishManuscriptApplyTool = _get_tool_class("PolishManuscriptApplyTool")
        RestoreManuscriptFromArtifactTool = _get_tool_class(
            "RestoreManuscriptFromArtifactTool"
        )
        PolishTool = _get_tool_class("PolishTool")
        ResultAnalysisTool = _get_tool_class("ResultAnalysisTool")
        ListQualityPresetsTool = _get_tool_class("ListQualityPresetsTool")
        GetQualitySchemaTool = _get_tool_class("GetQualitySchemaTool")
    except Exception:
        return []

    # Import core tool definitions
    from noveler.presentation.mcp.tool_definitions.core_tools import get_core_tools
    from noveler.presentation.mcp.tool_definitions.quality_tools import (
        get_quality_tools,
    )
    from noveler.presentation.mcp.tool_definitions.writing_tools import (
        get_writing_tools,
    )

    # Combine all tool definitions
    tools = []
    tools.extend(get_core_tools())
    tools.extend(get_writing_tools())
    tools.extend(
        get_quality_tools(
            CheckReadabilityTool,
            RunQualityChecksTool,
            FixQualityIssuesTool,
            GetIssueContextTool,
            ExportQualityReportTool,
            CheckStyleTool,
            ListQualityPresetsTool,
            GetQualitySchemaTool,
            ImproveQualityUntilTool,
            PolishManuscriptTool,
            PolishManuscriptApplyTool,
            RestoreManuscriptFromArtifactTool,
            PolishTool,
            CheckRhythmTool,
            CheckGrammarTool,
            ResultAnalysisTool,
            BackupTool,
        )
    )

    return tools


def _get_tool_class(tool_name: str):
    """Lazy load tool class by name.

    Args:
        tool_name: Tool class name

    Returns:
        Tool class

    Raises:
        ValueError: If tool class is unknown
    """
    module_map = {
        "BackupTool": "mcp_servers.noveler.tools.backup_tool",
        "CheckGrammarTool": "mcp_servers.noveler.tools.check_grammar_tool",
        "CheckReadabilityTool": "mcp_servers.noveler.tools.check_readability_tool",
        "CheckRhythmTool": "mcp_servers.noveler.tools.check_rhythm_tool",
        "RunQualityChecksTool": "mcp_servers.noveler.tools.run_quality_checks_tool",
        "ImproveQualityUntilTool": "mcp_servers.noveler.tools.improve_quality_until_tool",
        "FixQualityIssuesTool": "mcp_servers.noveler.tools.fix_quality_issues_tool",
        "GetIssueContextTool": "mcp_servers.noveler.tools.get_issue_context_tool",
        "ExportQualityReportTool": "mcp_servers.noveler.tools.export_quality_report_tool",
        "CheckStyleTool": "mcp_servers.noveler.tools.check_style_tool",
        "GenerateEpisodePreviewTool": "mcp_servers.noveler.tools.generate_episode_preview_tool",
        "PolishManuscriptTool": "mcp_servers.noveler.tools.polish_manuscript_tool",
        "PolishManuscriptApplyTool": "mcp_servers.noveler.tools.polish_manuscript_apply_tool",
        "RestoreManuscriptFromArtifactTool": "mcp_servers.noveler.tools.restore_manuscript_from_artifact_tool",
        "PolishTool": "mcp_servers.noveler.tools.polish_tool",
        "ResultAnalysisTool": "mcp_servers.noveler.tools.test_result_analysis_tool",
        "ListQualityPresetsTool": "mcp_servers.noveler.tools.quality_metadata_tools",
        "GetQualitySchemaTool": "mcp_servers.noveler.tools.quality_metadata_tools",
    }

    if tool_name not in module_map:
        raise ValueError(f"Unknown tool class: {tool_name}")

    module = importlib.import_module(module_map[tool_name])
    return getattr(module, tool_name)
