#!/usr/bin/env python3
# File: src/noveler/presentation/mcp/plugins/project_init_plugin.py
# Purpose: MCP plugin for project initialization with DDD orchestration
# Context: Phase 3 implementation - MCP presentation layer for project_init use case
"""Project initialization plugin for MCP.

This plugin exposes project initialization functionality to Claude Code via MCP,
orchestrating the ProjectInitUseCase with proper error handling and response formatting.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from noveler.application.use_cases.project_init_use_case import (
    ProjectInitRequest,
    ProjectInitUseCase,
)
from noveler.domain.services.project_initializer_service import (
    ProjectInitializerService,
)
from noveler.infrastructure.config.configuration_manager import (
    get_configuration_manager,
)
from noveler.infrastructure.repositories.template_repository import (
    TemplateRepository,
)
from noveler.infrastructure.adapters.path_service_adapter import (
    create_path_service,
)
from noveler.presentation.mcp.plugin_base import MCPToolPlugin


class ProjectInitPlugin(MCPToolPlugin):
    """Plugin wrapper for project initialization tool.

    Delegates to ProjectInitUseCase for creating new novel projects with
    standard directory structure and configuration files.
    """

    def get_name(self) -> str:
        """Return the tool identifier.

        Returns:
            'project_init'
        """
        return "project_init"

    def get_handler(self) -> Callable[[dict[str, Any]], Any]:
        """Return the project init handler function.

        The handler is imported lazily when this method is called.

        Returns:
            project_init handler function
        """

        def handler(args: dict[str, Any]) -> dict[str, Any]:
            """Execute project initialization workflow.

            Args:
                args: Tool arguments containing:
                    - project_name: Project name to create (required)
                    - project_root: Parent directory path (optional, defaults to NOVEL_ROOT)
                    - template_name: Template variant (optional, default: "base")
                    - genre: Genre override (optional)
                    - pen_name: Pen name override (optional)

            Returns:
                Result dictionary with:
                    - success: bool - Whether initialization succeeded
                    - project_path: str - Path to created project directory
                    - created_dirs: list[str] - List of created directory paths
                    - config_path: str - Path to project configuration file
                    - error_message: str - Error details if failed

            Examples:
                >>> handler({
                ...     "project_name": "08_時空の図書館",
                ...     "genre": "ファンタジー"
                ... })
                {
                    "success": True,
                    "project_path": "/path/to/08_時空の図書館",
                    "created_dirs": [...],
                    "config_path": "/path/to/08_時空の図書館/プロジェクト設定.yaml"
                }
            """
            # Extract and validate parameters
            project_name = args.get("project_name")
            if not project_name:
                return {
                    "success": False,
                    "error_message": "project_name is required",
                }

            # Resolve project root (default to configured NOVEL_ROOT)
            config_manager = get_configuration_manager()
            project_root_str = args.get("project_root")
            if project_root_str:
                project_root = Path(project_root_str)
            else:
                project_root = config_manager.get_project_root()

            # Collect optional parameters
            template_name = args.get("template_name", "base")
            genre = args.get("genre")
            pen_name = args.get("pen_name")

            try:
                # Initialize dependencies (Dependency Injection)
                path_service = create_path_service(project_root=project_root)
                initializer_service = ProjectInitializerService(
                    path_service=path_service
                )

                # Resolve template directory (relative to repository root)
                # Templates are at repository root, not project root
                from pathlib import Path as PathLib

                # Find repository root (where src/ directory is located)
                repo_root = PathLib(__file__).parent.parent.parent.parent.parent
                templates_dir = repo_root / "templates"

                if not templates_dir.exists():
                    return {
                        "success": False,
                        "error_message": f"Templates directory not found: {templates_dir}",
                    }

                template_repository = TemplateRepository(template_dir=templates_dir)

                # Create use case and execute
                use_case = ProjectInitUseCase(
                    initializer_service=initializer_service,
                    template_repository=template_repository,
                )

                request = ProjectInitRequest(
                    project_name=project_name,
                    project_root=project_root,
                    template_name=template_name,
                    genre=genre,
                    pen_name=pen_name,
                )

                result = use_case.execute(request)

                # Convert Path objects to strings for JSON serialization
                return {
                    "success": result.success,
                    "project_path": (
                        str(result.project_path) if result.project_path else None
                    ),
                    "created_dirs": result.created_dirs or [],
                    "config_path": (
                        str(result.config_path) if result.config_path else None
                    ),
                    "error_message": result.error_message,
                }

            except Exception as e:
                # Catch-all for unexpected errors
                return {
                    "success": False,
                    "error_message": f"Unexpected error during initialization: {str(e)}",
                }

        return handler


def create_plugin() -> MCPToolPlugin:
    """Factory function to create plugin instance.

    Returns:
        ProjectInitPlugin instance
    """
    return ProjectInitPlugin()
