# File: src/noveler/presentation/mcp/command_executor.py
# Purpose: Command parsing, dispatch, and execution logic
# Context: Extracted from server_runtime.py for SOLID-SRP compliance (B20 §3)

"""Command executor for MCP server.

Handles command parsing, validation, and execution with proper
error handling and logging.

This module provides:
- CommandExecutor: Main command execution class with command dispatch
- Command parsing and validation logic
- Project root resolution and environment variable management

Extracted from server_runtime.py (lines 1191-1409) as part of B20 §3 refactoring.
Handlers are delegated to write_command_handler.py and generic_command_handler.py.

Classes:
    CommandExecutor: Execute Noveler CLI commands via MCP protocol

Functions:
    None (all logic encapsulated in CommandExecutor class)

Preconditions:
    - Command handlers must be available (write_command_handler, generic_command_handler)
    - Project root must be accessible (via parameter or Path.cwd())

Side Effects:
    - Sets PROJECT_ROOT and TARGET_PROJECT_ROOT environment variables
    - Prints command execution info/errors to console
    - Never raises - all errors converted to MCP error responses

Raises:
    Never raises - all exceptions caught and converted to error dictionaries
"""

import os
from pathlib import Path
from typing import Any

from noveler.domain.utils.domain_console import get_console
from noveler.presentation.mcp.adapters.io import resolve_path_service
from noveler.presentation.mcp.generic_command_handler import handle_other_command
from noveler.presentation.mcp.write_command_handler import handle_write_command


class CommandExecutor:
    """Execute Noveler CLI commands via MCP protocol.

    Provides command parsing, validation, and execution with
    proper dependency injection and error handling.

    Methods:
        execute: Main entry point for command execution
        _parse_command: Parse command string into base command and episode number
        _resolve_project_root: Resolve and normalize project root path
    """

    async def execute(
        self, command: str, project_root: str | None, options: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute command and return MCP-compatible response.

        Args:
            command: Command string (e.g., "write 1", "check 1")
            project_root: Project root directory path (optional)
            options: Additional command options

        Returns:
            MCP-compatible response dictionary with success/error status

        Raises:
            Never raises - all exceptions caught and converted to error dictionaries

        Side Effects:
            - Prints command execution info to console
            - Sets PROJECT_ROOT and TARGET_PROJECT_ROOT environment variables
            - Executes use cases and adapters
        """
        try:
            get_console().print_info(f"🎯 MCPコマンド実行: noveler {command}")

            # Parse command
            base_command, episode_number = self._parse_command(command)

            # Resolve project root
            resolved_project_root = self._resolve_project_root(project_root)

            # Set environment variables for fallback compatibility
            if project_root:
                normalized = str(Path(resolved_project_root).absolute())
                os.environ["PROJECT_ROOT"] = normalized
                os.environ["TARGET_PROJECT_ROOT"] = normalized

            # Dispatch to appropriate handler
            if base_command == "write":
                return await handle_write_command(
                    command, episode_number, resolved_project_root, options
                )
            else:
                return await handle_other_command(
                    command, resolved_project_root, options
                )

        except Exception as e:
            get_console().print_error(f"❌ MCPコマンド実行エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command,
                "execution_method": "internal_mcp_adapter",
            }

    def _parse_command(self, command: str) -> tuple[str, int | None]:
        """Parse command string into base command and episode number.

        Args:
            command: Command string (e.g., "write 1", "check 2 --basic")

        Returns:
            Tuple of (base_command, episode_number)
            episode_number is None if not provided or invalid

        Raises:
            Never raises - returns ("", None) on empty command
        """
        cmd_parts = (command or "").strip().split()
        base_command = cmd_parts[0] if cmd_parts else ""
        episode_number = None

        if len(cmd_parts) >= 2:
            try:
                episode_number = int(cmd_parts[1])
            except Exception:
                episode_number = None

        return base_command, episode_number

    def _resolve_project_root(self, project_root: str | None) -> str:
        """Resolve and normalize project root path.

        Args:
            project_root: Project root path (optional)

        Returns:
            Resolved absolute project root path as string

        Raises:
            Never raises - falls back to Path.cwd() on errors
        """
        if project_root:
            ps = resolve_path_service(project_root)
            detected_root = getattr(ps, "project_root", None) if ps is not None else None
            return (
                str(Path(project_root).absolute())
                if not detected_root
                else str(detected_root)
            )
        else:
            return str(Path.cwd())
