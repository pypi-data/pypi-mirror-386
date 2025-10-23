# File: src/mcp_servers/noveler/tools/list_artifacts_tool.py
# Purpose: Provide an MCP tool to enumerate artifacts stored for a project.
# Context: Enables clients to browse polish/apply outputs without direct filesystem access.

"""MCP tool implementation for listing stored artifacts."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolIssue,
    ToolRequest,
    ToolResponse,
)
from noveler.domain.services.artifact_store_service import create_artifact_store


def get_artifact_service(project_root: str | None = None):
    """Return an artifact store service rooted at the given project directory."""
    base_dir = Path(project_root).expanduser() if isinstance(project_root, str) else Path.cwd()
    storage_dir = (base_dir / ".noveler" / "artifacts").resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)
    return create_artifact_store(storage_dir=storage_dir)


class ListArtifactsTool(MCPToolBase):
    """List artifact metadata for the current project."""

    def __init__(self) -> None:
        super().__init__(
            tool_name="list_artifacts",
            tool_description="プロジェクト内のアーティファクト一覧を返す",
        )

    def get_artifact_service(self, project_root: str | None = None):  # pragma: no cover - DI hook
        """Return the artifact service for the provided project."""
        return get_artifact_service(project_root)

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "project_root": {
                    "type": "string",
                    "description": "任意指定のプロジェクトルート",
                },
            },
        }

    def execute(self, request: ToolRequest) -> ToolResponse:
        start = time.time()
        self._validate_request(request, require_episode_number=False)
        additional = request.additional_params or {}
        project_root = additional.get("project_root")

        # project_rootが指定されている場合、存在確認
        if project_root:
            project_path = Path(project_root).expanduser()
            if not project_path.exists():
                error_msg = f"指定された project_root が存在しません: {project_root}"
                response = self._create_response(False, 0.0, [], start, error_message=error_msg)
                response.metadata.update({"project_root": project_root})
                return response

        service = self.get_artifact_service(project_root)
        catalog = service.list_artifacts()
        if hasattr(catalog, "as_list"):
            artifacts = catalog.as_list()
            total = len(artifacts)
        elif isinstance(catalog, dict):
            artifacts = list(catalog.get("artifacts", []))
            total = int(catalog.get("total", len(artifacts)))
        else:
            artifacts = []
            total = 0

        issue = ToolIssue(
            type="artifacts_listed",
            severity="low",
            message="アーティファクト一覧を取得しました",
            details={"count": total},
        )

        response = self._create_response(True, 100.0, [issue], start)
        response.metadata.update(
            {
                "artifacts": artifacts,
                "total": total,
            }
        )
        return response


list_artifacts_tool = ListArtifactsTool()
