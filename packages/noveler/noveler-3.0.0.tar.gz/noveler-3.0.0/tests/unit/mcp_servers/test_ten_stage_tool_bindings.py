# File: tests/unit/mcp_servers/test_ten_stage_tool_bindings.py
# Purpose: Unit tests for ten_stage_tool_bindings registry
# Context: Validates that ten-stage tools are properly registered on MCP server

"""Unit tests for ten_stage_tool_bindings registry."""

from unittest.mock import MagicMock

import pytest


def test_register_ten_stage_tools():
    """Test that register_ten_stage_tools properly registers ten-stage tools."""
    from mcp_servers.noveler.server.ten_stage_tool_bindings import register_ten_stage_tools

    # Create mock server
    mock_server = MagicMock()
    mock_server.tool = MagicMock(return_value=lambda func: func)

    # Create mock context that implements _SyncTenStageCtx protocol
    mock_ctx = MagicMock()
    mock_ctx._handle_write_ten_stage = MagicMock(return_value="sync result")
    mock_ctx.logger = MagicMock()

    # Register tools
    register_ten_stage_tools(mock_server, mock_ctx)

    # Verify tool decorator was called for each expected tool
    expected_tools = [
        "write_step_1", "write_step_2", "write_step_3", "write_step_4", "write_step_5",
        "write_step_6", "write_step_7", "write_step_8", "write_step_9", "write_step_10"
    ]

    # Check that tool decorator was called
    assert mock_server.tool.call_count == len(expected_tools)

    # Verify the tool names were registered correctly
    registered_names = [call[1]['name'] for call in mock_server.tool.call_args_list]
    for expected_name in expected_tools:
        assert expected_name in registered_names, f"Tool {expected_name} not registered"


@pytest.mark.asyncio
async def test_register_async_ten_stage_tools():
    """Test that register_async_ten_stage_tools properly registers async ten-stage tool."""
    from mcp_servers.noveler.server.ten_stage_tool_bindings import register_async_ten_stage_tools

    # Create mock server
    mock_server = MagicMock()
    mock_server.tool = MagicMock(return_value=lambda func: func)

    # Create mock context that implements _AsyncTenStageCtx protocol
    mock_ctx = MagicMock()
    mock_ctx._execute_ten_stage_step_async = MagicMock(return_value="async result")
    mock_ctx.logger = MagicMock()

    # Register tools
    register_async_ten_stage_tools(mock_server, mock_ctx)

    # Async version registers a single unified tool
    expected_tool_name = "write_step_async"

    # Check that tool decorator was called once
    assert mock_server.tool.call_count == 1

    # Verify the tool name was registered correctly
    call_args = mock_server.tool.call_args_list[0]
    assert call_args[1]['name'] == expected_tool_name
    assert 'description' in call_args[1]
    assert len(call_args[1]['description']) > 0


def test_ten_stage_tool_descriptions():
    """Test that ten-stage tools have proper descriptions."""
    from mcp_servers.noveler.server.ten_stage_tool_bindings import register_ten_stage_tools

    # Create mock server
    mock_server = MagicMock()
    mock_server.tool = MagicMock(return_value=lambda func: func)

    # Create mock context
    mock_ctx = MagicMock()
    mock_ctx._handle_write_ten_stage = MagicMock(return_value="result")
    mock_ctx.logger = MagicMock()

    # Register tools
    register_ten_stage_tools(mock_server, mock_ctx)

    # Check that each tool has a description
    for call in mock_server.tool.call_args_list:
        kwargs = call[1]
        assert 'description' in kwargs, f"Tool {kwargs.get('name')} missing description"
        assert len(kwargs['description']) > 0, f"Tool {kwargs.get('name')} has empty description"