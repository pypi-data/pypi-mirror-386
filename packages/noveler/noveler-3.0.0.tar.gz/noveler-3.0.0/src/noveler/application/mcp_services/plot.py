# File: src/noveler/application/mcp_services/plot.py
# Purpose: Service façade for plot/design-related MCP tools.
# Context: Delegated from plot tool registrations to centralise handler calls
#          and error handling within the application layer.
"""Plot and design tool services for FastMCP registrations."""

from __future__ import annotations

from typing import Any, Dict

from noveler.infrastructure.mcp import handlers

from .base import BaseToolService, ToolServiceError


class PlotToolService(BaseToolService):
    """Expose plot/design related handlers via an application-layer service."""

    async def get_conversation_context(self, *, conversation_id: str) -> Dict[str, Any]:
        payload = {"conversation_id": conversation_id}
        return await self._invoke(
            handlers.get_conversation_context,
            payload,
            reason="conversation_context_failed",
            hint="会話コンテキストの取得に失敗しました。",
        )

    async def export_design_data(self, *, episode_number: int) -> Dict[str, Any]:
        payload = {"episode_number": episode_number}
        return await self._invoke(
            handlers.export_design_data,
            payload,
            reason="export_design_failed",
            hint="設計データのエクスポートに失敗しました。",
        )

    async def get_file_by_hash(self, *, hash_value: str) -> Dict[str, Any]:
        payload = {"hash_value": hash_value}
        return await self._invoke(
            handlers.get_file_by_hash_util,
            payload,
            reason="file_lookup_failed",
            hint="ハッシュでのファイル取得に失敗しました。",
        )

    async def check_file_changes(self, *, file_paths: list[str]) -> Dict[str, Any]:
        payload = {"paths": file_paths}
        return await self._invoke(
            handlers.check_file_changes_util,
            payload,
            reason="change_detection_failed",
            hint="ファイル差分検知に失敗しました。",
        )

    async def list_files_with_hashes(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        return await self._invoke(
            handlers.list_files_with_hashes_util,
            payload,
            reason="hash_listing_failed",
            hint="ハッシュ一覧の取得に失敗しました。",
        )

    async def run_novel_command(
        self,
        *,
        command: str,
        options: Dict[str, Any] | None,
        project_root: str | None,
    ) -> Dict[str, Any]:
        raise ToolServiceError(
            message="novel コマンドはサービス層未対応です。",
            reason="not_implemented",
            hint="MCPProtocolAdapter を使用する既存経路を利用してください。",
        )

    async def status(self, *, project_root: str | None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if project_root:
            payload["project_root"] = project_root
        return await self._invoke(
            handlers.status,
            payload,
            reason="status_failed",
            hint="プロジェクト状況の取得に失敗しました。",
        )

    async def get_file_reference_info(self, *, file_path: str) -> Dict[str, Any]:
        payload = {"file_path": file_path}
        return await self._invoke(
            handlers.get_file_reference_info_util,
            payload,
            reason="file_reference_failed",
            hint="ファイル参照情報の取得に失敗しました。",
        )

    async def convert_cli_to_json(self, *, cli_result: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"cli_result": cli_result}
        return await self._invoke(
            handlers.convert_cli_to_json_util,
            payload,
            reason="cli_conversion_failed",
            hint="CLI結果のJSON変換に失敗しました。",
        )

    async def validate_json_response(self, *, json_data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"json_data": json_data}
        return await self._invoke(
            handlers.validate_json_response_util,
            payload,
            reason="json_validation_failed",
            hint="JSONレスポンス形式の検証に失敗しました。",
        )

    async def analyze_narrative_depth(
        self,
        *,
        episode_number: int,
        analysis_aspects: list[str] | None,
        project_root: str | None,
    ) -> Dict[str, Any]:
        raise ToolServiceError(
            message="analyze_narrative_depth は未実装です。",
            reason="not_implemented",
        )

    async def extract_character_development(
        self,
        *,
        episode_range: Dict[str, int],
        character_names: list[str] | None,
        project_root: str | None,
    ) -> Dict[str, Any]:
        raise ToolServiceError(
            message="extract_character_development は未実装です。",
            reason="not_implemented",
        )

    async def analyze_foreshadowing(
        self,
        *,
        episode_number: int,
        analysis_mode: str,
        project_root: str | None,
    ) -> Dict[str, Any]:
        raise ToolServiceError(
            message="analyze_foreshadowing は未実装です。",
            reason="not_implemented",
        )

    async def generate_scene_descriptions(
        self,
        *,
        scene_requirements: Dict[str, Any],
        writing_style: str,
        project_root: str | None,
    ) -> Dict[str, Any]:
        raise ToolServiceError(
            message="generate_scene_descriptions は未実装です。",
            reason="not_implemented",
        )

    async def optimize_dialogue_flow(
        self,
        *,
        dialogue_draft: str,
        optimization_goals: list[str] | None,
        project_root: str | None,
    ) -> Dict[str, Any]:
        raise ToolServiceError(
            message="optimize_dialogue_flow は未実装です。",
            reason="not_implemented",
        )

    async def enhance_emotional_impact(
        self,
        *,
        content_sections: list[str],
        target_emotions: list[str],
        project_root: str | None,
    ) -> Dict[str, Any]:
        raise ToolServiceError(
            message="enhance_emotional_impact は未実装です。",
            reason="not_implemented",
        )

