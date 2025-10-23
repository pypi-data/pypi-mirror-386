# File: src/mcp_servers/noveler/tools/fetch_artifact_tool.py
# Purpose: Provide an MCP tool for retrieving stored artifacts by reference ID.
# Context: Complements polish workflow tooling by allowing clients to load saved outputs.

"""MCP tool implementation for fetching artifacts from the project store."""
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


class FetchArtifactTool(MCPToolBase):
    """Fetch artifact content by ID."""

    def __init__(self) -> None:
        super().__init__(
            tool_name="fetch_artifact",
            tool_description="artifact:XXXX 形式のIDで格納済みアーティファクトを取得する",
        )

    def get_artifact_service(self, project_root: str | None = None):  # pragma: no cover - DI hook
        """Return the artifact service for the provided project."""
        return get_artifact_service(project_root)

    def get_input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "artifact_id": {
                    "type": "string",
                    "description": "取得対象のartifact参照ID",
                },
                "project_root": {
                    "type": "string",
                    "description": "任意指定のプロジェクトルート",
                },
            },
            "required": ["artifact_id"],
        }

    def execute(self, request: ToolRequest) -> ToolResponse:
        start = time.time()
        self._validate_request(request, require_episode_number=False)
        additional = request.additional_params or {}
        artifact_id = additional.get("artifact_id")
        project_root = additional.get("project_root")

        if not isinstance(artifact_id, str) or not artifact_id.strip():
            raise ValueError("artifact_id is required")

        # project_rootが指定されている場合、存在確認
        from pathlib import Path
        if project_root:
            project_path = Path(project_root).expanduser()
            if not project_path.exists():
                error_msg = f"指定された project_root が存在しません: {project_root}"
                response = self._create_response(False, 0.0, [], start, error_message=error_msg)
                response.metadata.update({"project_root": project_root})
                return response

        service = self.get_artifact_service(project_root)
        content = service.fetch(artifact_id)
        if content is None:
            raise FileNotFoundError(f"artifact not found: {artifact_id}")

        issue = ToolIssue(
            type="artifact_fetched",
            severity="low",
            message="アーティファクトを取得しました",
            details={"artifact_id": artifact_id},
        )

        response = self._create_response(True, 100.0, [issue], start)
        response.metadata.update(
            {
                "artifact_id": artifact_id,
                "content": content,
            }
        )
        return response


fetch_artifact_tool = FetchArtifactTool()
