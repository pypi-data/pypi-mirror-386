#!/usr/bin/env python3
# File: tests/unit/mcp_servers/tools/test_generate_episode_preview_tool.py
# Purpose: Validate the GenerateEpisodePreviewTool returns enriched preview
#          metadata and honours override parameters.
# Context: Exercises the MCP tool in isolation using temporary manuscript
#          projects to ensure CLI/MCP integrations receive stable payloads.
"""Unit tests for the GenerateEpisodePreviewTool."""

from __future__ import annotations

from pathlib import Path

from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest
from mcp_servers.noveler.tools.generate_episode_preview_tool import GenerateEpisodePreviewTool
from noveler.domain.value_objects.preview_configuration import PreviewStyle


def _write_sample_project(root: Path) -> None:
    manuscripts = root / "40_原稿"
    management = root / "50_管理資料"
    manuscripts.mkdir(parents=True, exist_ok=True)
    management.mkdir(parents=True, exist_ok=True)

    content = (
        "第1話　テストタイトル\n\n"
        "「ねえ、これでプレビューは十分かな？」と彼女は微笑んだ。\n"
        "夕暮れの光が差し込む部屋で、僕たちは次の冒険を語り合う。\n"
        "しかし、窓の外には不穏な影が揺れていた……\n"
        "それが何を意味するのか、まだ誰も知らない。"
    )
    (manuscripts / "第001話_テスト.md").write_text(content, encoding="utf-8")


def test_generate_episode_preview_tool_produces_metadata(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_sample_project(project_root)

    tool = GenerateEpisodePreviewTool()
    request = ToolRequest(
        episode_number=1,
        project_name=str(project_root),
        additional_params={"preview_style": "summary"},
    )

    response = tool.execute(request)

    assert response.success is True
    assert response.score >= 0.0
    metadata = response.metadata
    assert metadata.get("preview_text")
    assert isinstance(metadata.get("preview"), dict)
    assert isinstance(metadata.get("quality"), dict)
    assert isinstance(metadata.get("source"), dict)


def test_generate_episode_preview_tool_accepts_overrides(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_sample_project(project_root)

    tool = GenerateEpisodePreviewTool()
    request = ToolRequest(
        episode_number=1,
        project_name=str(project_root),
        additional_params={
            "preview_style": PreviewStyle.DIALOGUE_FOCUS.value,
            "sentence_count": 2,
            "max_length": 120,
        },
    )

    response = tool.execute(request)

    assert response.success is True
    preview_meta = response.metadata.get("preview", {})
    assert isinstance(preview_meta, dict)
    assert preview_meta.get("sentence_count") == 2
