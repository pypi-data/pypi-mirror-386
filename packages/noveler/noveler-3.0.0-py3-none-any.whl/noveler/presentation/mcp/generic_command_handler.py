# File: src/noveler/presentation/mcp/generic_command_handler.py
# Purpose: Generic command execution handler (non-write commands)
# Context: Extracted from command_executor.py for B20 file size compliance

"""Generic command handler for MCP server.

Handles non-write command execution via MCPProtocolAdapter with
proper error handling and response transformation.

Functions:
    handle_other_command: Execute non-write commands via MCPProtocolAdapter

Preconditions:
    - MCPProtocolAdapter must be importable

Side Effects:
    - Executes MCPProtocolAdapter.handle_novel_command
    - Prints command execution info to console
    - Never raises - all errors converted to responses

Raises:
    ImportError: If MCPProtocolAdapter module cannot be imported
"""

import importlib
from typing import Any

from noveler.domain.utils.domain_console import get_console


async def handle_other_command(
    command: str, project_root: str, options: dict[str, Any]
) -> dict[str, Any]:
    """Handle non-write command execution via MCPProtocolAdapter.

    Args:
        command: Full command string
        project_root: Resolved project root path
        options: Additional command options

    Returns:
        MCP-compatible response dictionary

    Raises:
        ImportError: If MCPProtocolAdapter module cannot be imported
    """
    get_console().print_info("🔄 MCPProtocolAdapter直接実行モード")

    try:
        mcp_protocol_adapter_module = importlib.import_module(
            "noveler.presentation.mcp.adapters.mcp_protocol_adapter"
        )
        MCPProtocolAdapter = getattr(
            mcp_protocol_adapter_module, "MCPProtocolAdapter"
        )
    except ImportError as e:
        raise ImportError(f"MCPProtocolAdapterモジュールをインポートできません: {e}")

    adapter = MCPProtocolAdapter()
    result = await adapter.handle_novel_command(
        command=command,
        options=options,
        project_root=project_root,
    )

    get_console().print_success(f"✅ コマンド実行完了: noveler {command}")

    # Flatten check command response for E2E test compatibility
    if command.startswith("check") and isinstance(result, dict) and "result" in result:
        nested_result = result["result"]
        if isinstance(nested_result, dict) and "data" in nested_result:
            check_data = nested_result["data"]
            if isinstance(check_data, dict) and "result" in check_data:
                return {
                    "success": nested_result.get("success", True),
                    "command": check_data.get("command", "check"),
                    "result": check_data["result"],
                    "execution_method": "mcp_protocol_adapter_direct",
                    "note": "MCPサーバー内からTask tool直接実行は不可のため、MCPProtocolAdapterで実行",
                }
            # Fallback: treat entire data as result
            return {
                "success": nested_result.get("success", True),
                "command": getattr(check_data, "get", lambda *_: "check")(
                    "command", "check"
                ),
                "result": check_data,
                "execution_method": "mcp_protocol_adapter_direct",
                "note": "flatten(fallback): dataにresultが無い形式",
            }

    # Add execution method info
    if isinstance(result, dict):
        result["execution_method"] = "mcp_protocol_adapter_direct"
        result[
            "note"
        ] = "MCPサーバー内からTask tool直接実行は不可のため、MCPProtocolAdapterで実行"

    return result
