#!/usr/bin/env python3
# File: tests/unit/scripts/test_build_slash_commands_mcp.py
# Purpose: Test MCP command validation in slash command builder
# Context: SPEC-CLI-050 - Slash Command Management System

import pytest
from scripts.setup.build_slash_commands import CommandValidationError, validate_commands


class TestMCPCommandValidation:
    """Test validation rules for MCP-type slash commands."""

    def test_mcp_command_requires_mcp_tools_field(self):
        """MCP command must have mcp_tools field."""
        commands = [
            {
                "name": "/test-mcp",
                "type": "mcp",
                "description": "Test MCP command",
                # Missing mcp_tools
            }
        ]

        with pytest.raises(CommandValidationError, match="MCP type requires 'mcp_tools' field"):
            validate_commands(commands)

    def test_mcp_tools_must_be_list(self):
        """mcp_tools must be a list."""
        commands = [
            {
                "name": "/test-mcp",
                "type": "mcp",
                "mcp_tools": "not_a_list",  # Wrong type
                "description": "Test MCP command",
            }
        ]

        with pytest.raises(CommandValidationError, match="'mcp_tools' must be a list"):
            validate_commands(commands)

    def test_mcp_tools_must_not_be_empty(self):
        """mcp_tools list must not be empty."""
        commands = [
            {
                "name": "/test-mcp",
                "type": "mcp",
                "mcp_tools": [],  # Empty list
                "description": "Test MCP command",
            }
        ]

        with pytest.raises(CommandValidationError, match="'mcp_tools' must not be empty"):
            validate_commands(commands)

    def test_mcp_tool_must_start_with_mcp_prefix(self):
        """Each MCP tool must start with 'mcp__' prefix."""
        commands = [
            {
                "name": "/test-mcp",
                "type": "mcp",
                "mcp_tools": [
                    "mcp__valid__tool",
                    "invalid_tool",  # Missing mcp__ prefix
                ],
                "description": "Test MCP command",
            }
        ]

        with pytest.raises(CommandValidationError, match="MCP tool 'invalid_tool' must start with 'mcp__'"):
            validate_commands(commands)

    def test_mcp_tool_must_be_string(self):
        """Each MCP tool must be a string."""
        commands = [
            {
                "name": "/test-mcp",
                "type": "mcp",
                "mcp_tools": [
                    "mcp__valid__tool",
                    123,  # Not a string
                ],
                "description": "Test MCP command",
            }
        ]

        with pytest.raises(CommandValidationError, match="MCP tool must be a string"):
            validate_commands(commands)

    def test_valid_mcp_command(self):
        """Valid MCP command should pass validation."""
        commands = [
            {
                "name": "/test-mcp",
                "type": "mcp",
                "mcp_tools": [
                    "mcp__noveler__enhanced_get_writing_tasks",
                    "mcp__noveler__enhanced_execute_writing_step",
                ],
                "description": "Test MCP command",
                "category": "testing",
                "tags": ["test", "mcp"],
            }
        ]

        # Should not raise any exception
        validate_commands(commands)

    def test_script_command_still_works(self):
        """Script-based commands should still work (backward compatibility)."""
        commands = [
            {
                "name": "/test-script",
                "script": "python",
                "args": ["-m", "pytest"],
                "description": "Test script command",
            }
        ]

        # Should not raise any exception
        validate_commands(commands)

    def test_mixed_command_types(self):
        """Mix of MCP and script commands should work."""
        commands = [
            {
                "name": "/test-mcp",
                "type": "mcp",
                "mcp_tools": ["mcp__test__tool"],
                "description": "Test MCP command",
            },
            {
                "name": "/test-script",
                "script": "python",
                "args": ["-m", "pytest"],
                "description": "Test script command",
            },
        ]

        # Should not raise any exception
        validate_commands(commands)
