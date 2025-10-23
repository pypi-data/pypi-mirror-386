#!/usr/bin/env python3
# File: src/mcp_servers/noveler/tools/generate_episode_preview_tool.py
# Purpose: Expose episode preview generation as an MCP tool, returning
#          metadata-rich preview/quality/source sections for clients.
# Context: Loaded by the Noveler MCP server and CLI. Relies on domain
#          services and PathService adapters for manuscript access.
"""Generate episode preview MCP tool.

Exposes the :class:`EpisodePreviewGenerationService` via the MCP facade so
clients (CLI/MCP/LLM) can fetch preview text and the enriched metadata
sections (`preview`, `quality`, `source`).
"""

from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolRequest,
    ToolResponse,
)
from noveler.domain.exceptions.base import DomainValidationError
from noveler.domain.services.episode_preview_generation_service import (
    EpisodePreviewGenerationService,
)
from noveler.domain.value_objects.preview_configuration import (
    PreviewConfiguration,
    PreviewStyle,
)
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.caching.file_cache_service import get_file_cache_service


class GenerateEpisodePreviewTool(MCPToolBase):
    """Generate metadata-rich previews for a manuscript episode."""

    _STYLE_FACTORIES: dict[str, PreviewConfiguration] = {
        "summary": PreviewConfiguration.create_default(),
        "teaser": PreviewConfiguration.create_teaser(),
        "dialogue_focus": PreviewConfiguration.create_dialogue_focus(),
        "excerpt": PreviewConfiguration(
            max_length=220,
            sentence_count=3,
            preview_style=PreviewStyle.EXCERPT,
            content_filters=(),
            preserve_formatting=True,
            include_metadata=True,
        ),
    }

    def __init__(self) -> None:
        super().__init__(
            tool_name="generate_episode_preview",
            tool_description="エピソードプレビューを生成し、preview/quality/sourceメタを返す",
        )
        self._service = EpisodePreviewGenerationService()

    def get_input_schema(self) -> dict[str, Any]:
        schema = self._get_common_input_schema()
        schema["properties"].update(
            {
                "preview_style": {
                    "type": "string",
                    "enum": list(self._STYLE_FACTORIES.keys()),
                    "default": "summary",
                    "description": "プレビュースタイル (summary/teaser/dialogue_focus/excerpt)",
                },
                "sentence_count": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "description": "抽出する文数 (スタイル既定値を上書き)",
                },
                "max_length": {
                    "type": "integer",
                    "minimum": 50,
                    "maximum": 1000,
                    "description": "プレビュー最大文字数 (スタイル既定値を上書き)",
                },
            }
        )
        schema["required"] = ["episode_number"]
        return schema

    def execute(self, request: ToolRequest) -> ToolResponse:
        start = time.time()
        try:
            self._validate_request(request)

            params = request.additional_params or {}
            style_key = (params.get("preview_style") or "summary").lower()
            base_config = self._STYLE_FACTORIES.get(style_key)
            if base_config is None:
                raise ValueError(f"preview_style '{style_key}' is not supported")

            config = self._apply_overrides(base_config, params)

            content, path_service = self._load_manuscript(request)

            preview_result = self._service.generate_preview(content, config)
            metadata = preview_result.metadata
            score = float(metadata.get("quality", {}).get("score", 0.0)) * 100

            response = self._create_response(True, score, [], start)
            response.metadata.update(
                {
                    "preview_text": preview_result.preview_text,
                    "preview": metadata.get("preview", {}),
                    "quality": metadata.get("quality", {}),
                    "source": metadata.get("source", {}),
                    "config": metadata.get("config", {}),
                }
            )
            self._ps_collect_fallback(path_service)
            self._apply_fallback_metadata(response)
            return response

        except (FileNotFoundError, DomainValidationError, ValueError) as exc:
            response = self._create_response(False, 0.0, [], start, str(exc))
            self._apply_fallback_metadata(response)
            return response
        except Exception as exc:  # pragma: no cover - defensive catch
            response = self._create_response(False, 0.0, [], start, f"Unhandled error: {exc!s}")
            self._apply_fallback_metadata(response)
            return response

    def _load_manuscript(self, request: ToolRequest) -> tuple[str, Any]:
        project_root: Path | None = None
        if request.project_name:
            project_root = Path(request.project_name)

        path_service = create_path_service(project_root)
        cache_service = get_file_cache_service()

        manuscript_dir = path_service.get_manuscript_dir()
        episode_file = cache_service.get_episode_file_cached(manuscript_dir, request.episode_number)
        if not episode_file or not episode_file.exists():
            raise FileNotFoundError(f"Episode {request.episode_number} file not found in {manuscript_dir}")

        content = episode_file.read_text(encoding="utf-8")
        return content, path_service

    def _apply_overrides(
        self,
        config: PreviewConfiguration,
        params: dict[str, Any],
    ) -> PreviewConfiguration:
        overrides = {}
        if "sentence_count" in params:
            overrides["sentence_count"] = int(params["sentence_count"])
        if "max_length" in params:
            overrides["max_length"] = int(params["max_length"])
        if not overrides:
            return config
        try:
            return replace(config, **overrides)
        except DomainValidationError as exc:
            raise DomainValidationError(
                exc.entity,
                exc.field,
                exc.message,
                exc.value,
            ) from exc
