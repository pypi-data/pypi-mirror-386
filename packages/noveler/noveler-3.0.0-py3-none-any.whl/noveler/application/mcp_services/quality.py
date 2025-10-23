# File: src/noveler/application/mcp_services/quality.py
# Purpose: Service façade for quality-related MCP tools.
# Context: Keeps FastMCP registrations thin by delegating to shared handlers and
#          providing consistent error handling.
"""Quality-analysis tool services for FastMCP registrations."""

from __future__ import annotations

from typing import Any, Dict

from noveler.infrastructure.mcp import handlers

from .base import BaseToolService


class QualityToolService(BaseToolService):
    """Execute quality, backup, and design related MCP handlers."""

    async def get_check_tasks(
        self,
        *,
        episode_number: int,
        check_type: str,
        project_root: str | None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "episode_number": episode_number,
            "check_type": check_type,
        }
        if project_root:
            payload["project_root"] = project_root
        return await self._invoke(
            handlers.get_check_tasks,
            payload,
            reason="quality_task_fetch_failed",
            hint="品質チェックタスクの取得に失敗しました。",
        )

    async def execute_check_step(
        self,
        *,
        episode_number: int,
        step_id: float,
        input_data: Dict[str, Any],
        dry_run: bool,
        project_root: str | None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "episode_number": episode_number,
            "step_id": step_id,
            "input_data": input_data,
            "dry_run": dry_run,
        }
        if project_root:
            payload["project_root"] = project_root
        return await self._invoke(
            handlers.execute_check_step,
            payload,
            reason="quality_step_failed",
            hint="品質チェックステップの実行に失敗しました。",
        )

    async def get_check_status(self, *, episode_number: int, project_root: str | None) -> Dict[str, Any]:
        payload = {"episode_number": episode_number}
        if project_root:
            payload["project_root"] = project_root
        return await self._invoke(
            handlers.get_check_status,
            payload,
            reason="quality_status_failed",
            hint="品質チェックの進捗取得に失敗しました。",
        )

    async def get_check_history(
        self,
        *,
        episode_number: int,
        limit: int,
        project_root: str | None,
    ) -> Dict[str, Any]:
        payload = {"episode_number": episode_number, "limit": limit}
        if project_root:
            payload["project_root"] = project_root
        return await self._invoke(
            handlers.get_check_history,
            payload,
            reason="quality_history_failed",
            hint="品質チェック履歴の取得に失敗しました。",
        )

    async def check_readability(
        self,
        *,
        episode_number: int,
        project_name: str | None,
        check_aspects: list[str] | None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"episode_number": episode_number}
        if project_name:
            payload["project_name"] = project_name
        if check_aspects is not None:
            payload["check_aspects"] = check_aspects
        return await self._invoke(
            handlers.check_readability,
            payload,
            reason="readability_check_failed",
            hint="読みやすさチェックの実行に失敗しました。",
        )

    async def check_grammar(
        self,
        *,
        episode_number: int,
        project_name: str | None,
        check_types: list[str] | None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"episode_number": episode_number}
        if project_name:
            payload["project_name"] = project_name
        if check_types is not None:
            payload["check_types"] = check_types
        return await self._invoke(
            handlers.check_grammar,
            payload,
            reason="grammar_check_failed",
            hint="文法チェックの実行に失敗しました。",
        )

    async def test_result_analysis(
        self,
        *,
        test_result_json: Dict[str, Any],
        focus_on_failures: bool,
        include_suggestions: bool,
        max_issues: int,
    ) -> Dict[str, Any]:
        payload = {
            "test_result_json": test_result_json,
            "focus_on_failures": focus_on_failures,
            "include_suggestions": include_suggestions,
            "max_issues": max_issues,
        }
        return await self._invoke(
            handlers.analyze_test_results,
            payload,
            reason="test_result_analysis_failed",
            hint="テスト結果解析に失敗しました。",
        )

    async def backup_management(
        self,
        *,
        episode_number: int,
        action: str,
        backup_id: str | None,
        backup_name: str | None,
        file_path: str | None,
        restore_path: str | None,
        filter_pattern: str | None,
        project_name: str | None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "episode_number": episode_number,
            "action": action,
            "backup_id": backup_id,
            "backup_name": backup_name,
            "file_path": file_path,
            "restore_path": restore_path,
            "filter_pattern": filter_pattern,
            "project_name": project_name,
        }
        return await self._invoke(
            handlers.backup_management,
            payload,
            reason="backup_operation_failed",
            hint="バックアップ操作に失敗しました。",
        )

    async def design_conversations(
        self,
        *,
        episode_number: int,
        scene_number: int,
        dialogues: list[dict[str, Any]],
    ) -> Dict[str, Any]:
        payload = {
            "episode_number": episode_number,
            "scene_number": scene_number,
            "dialogues": dialogues,
        }
        return await self._invoke(
            handlers.design_conversations,
            payload,
            reason="design_conversations_failed",
            hint="会話設計の実行に失敗しました。",
        )

    async def track_emotions(self, *, emotions: list[dict[str, Any]]) -> Dict[str, Any]:
        payload = {"emotions": emotions}
        return await self._invoke(
            handlers.track_emotions,
            payload,
            reason="track_emotions_failed",
            hint="感情曲線の追跡に失敗しました。",
        )

    async def design_scenes(self, *, scenes: list[dict[str, Any]]) -> Dict[str, Any]:
        payload = {"scenes": scenes}
        return await self._invoke(
            handlers.design_scenes,
            payload,
            reason="design_scenes_failed",
            hint="情景設計の実行に失敗しました。",
        )

    async def design_senses(self, *, triggers: list[dict[str, Any]]) -> Dict[str, Any]:
        payload = {"triggers": triggers}
        return await self._invoke(
            handlers.design_senses,
            payload,
            reason="design_senses_failed",
            hint="五感描写設計の実行に失敗しました。",
        )

    async def manage_props(self, *, props: list[dict[str, Any]]) -> Dict[str, Any]:
        payload = {"props": props}
        return await self._invoke(
            handlers.manage_props,
            payload,
            reason="manage_props_failed",
            hint="小道具管理の実行に失敗しました。",
        )

