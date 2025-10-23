# File: src/noveler/application/mcp_services/writing.py
# Purpose: Application-layer service wrapper for writing-oriented MCP tools.
# Context: Delegated from FastMCP registration classes to keep presentation
#          layers thin while reusing existing handlers.
"""Writing-related tool service implementation for FastMCP registrations."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

from noveler.domain.services.artifact_store_service import create_artifact_store
from noveler.domain.value_objects.project_time import project_now
from noveler.infrastructure.factories.path_service_factory import (
    create_mcp_aware_path_service,
    create_path_service,
)
from noveler.infrastructure.factories.progressive_write_llm_executor_factory import (
    create_progressive_write_llm_executor,
)
from noveler.infrastructure.factories.progressive_write_manager_factory import (
    create_progressive_write_manager,
)
from noveler.infrastructure.adapters.batch_processing_adapter import (
    BatchProcessingAdapter,
)
from noveler.infrastructure.mcp import handlers

from .base import BaseToolService, ToolServiceError


class WritingToolService(BaseToolService):
    """Expose writing-focused MCP handlers via a service façade."""

    def __init__(self) -> None:
        super().__init__()
        self._batch_processors: dict[str, BatchProcessingAdapter] = {}

    async def write_file(self, *, relative_path: str, content: str, project_root: str | None = None) -> Dict[str, Any]:
        payload = {
            "relative_path": relative_path,
            "content": content,
        }
        if project_root:
            payload["project_root"] = project_root
        return await self._invoke(
            handlers.write_file,
            payload,
            reason="write_file_failed",
            hint="ファイル書き込み時にエラーが発生しました。",
        )

    async def get_writing_tasks(self, *, episode_number: int, project_root: str | None = None) -> Dict[str, Any]:
        project_dir = project_root or "."

        def _fetch_tasks() -> Dict[str, Any]:
            manager = create_progressive_write_manager(
                project_dir,
                episode_number,
                llm_executor=create_progressive_write_llm_executor(),
            )
            return manager.get_writing_tasks()

        try:
            tasks = await asyncio.to_thread(_fetch_tasks)
        except Exception as exc:
            raise ToolServiceError(
                message=str(exc),
                reason="task_fetch_failed",
                error_type=type(exc).__name__,
            ) from exc

        return {"success": True, "tasks": tasks}

    async def execute_writing_step(
        self,
        *,
        episode_number: int,
        step_id: float,
        dry_run: bool = False,
        project_root: str | None = None,
    ) -> Dict[str, Any]:
        project_dir = project_root or "."
        try:
            manager = create_progressive_write_manager(
                project_dir,
                episode_number,
                llm_executor=create_progressive_write_llm_executor(),
            )
            result = await manager.execute_writing_step_async(step_id, dry_run)
        except Exception as exc:
            raise ToolServiceError(
                message=str(exc),
                reason="step_execution_failed",
                error_type=type(exc).__name__,
            ) from exc

        payload = result if isinstance(result, dict) else {"result": result}
        payload.setdefault("success", True)
        return payload

    async def get_task_status(self, *, episode_number: int, project_root: str | None = None) -> Dict[str, Any]:
        project_dir = project_root or "."

        def _fetch_status() -> Dict[str, Any]:
            manager = create_progressive_write_manager(
                project_dir,
                episode_number,
                llm_executor=create_progressive_write_llm_executor(),
            )
            return manager.get_task_status()

        try:
            status = await asyncio.to_thread(_fetch_status)
        except Exception as exc:
            raise ToolServiceError(
                message=str(exc),
                reason="status_lookup_failed",
                error_type=type(exc).__name__,
            ) from exc

        return {"success": True, "status": status}

    async def analyze_episode_quality(
        self,
        *,
        episode_number: int,
        analysis_type: str,
        project_root: str | None = None,
    ) -> Dict[str, Any]:
        raise ToolServiceError(
            message="analyze_episode_quality は未実装です。",
            reason="not_implemented",
            hint="対応するユースケースが実装された後にサービスを拡張してください。",
        )

    async def get_progress_display(self, *, project_root: str | None = None) -> Dict[str, Any]:
        raise ToolServiceError(
            message="get_progress_display は未実装です。",
            reason="not_implemented",
        )

    async def export_ui_reports(
        self,
        *,
        report_types: list[str],
        output_format: str,
        project_root: str | None = None,
    ) -> Dict[str, Any]:
        raise ToolServiceError(
            message="export_ui_reports は未実装です。",
            reason="not_implemented",
        )

    async def create_batch_job(
        self,
        *,
        episode_numbers: list[int],
        step_ranges: list[dict[str, Any]],
        job_name: str,
        project_root: str | None,
    ) -> Dict[str, Any]:
        processor = self._get_batch_processor(project_root)
        expanded_steps = self._expand_step_ranges(step_ranges)
        default_steps = list(range(1, 19))
        effective_steps = expanded_steps or default_steps

        try:
            job_id = await asyncio.to_thread(
                processor.create_batch_job,
                episode_numbers,
                effective_steps,
                job_name,
            )
        except Exception as exc:
            raise ToolServiceError(
                message=str(exc),
                reason="batch_job_creation_failed",
                error_type=type(exc).__name__,
            ) from exc

        return {
            "success": True,
            "job_id": job_id,
            "episode_count": len(episode_numbers),
            "step_count": len(effective_steps),
        }

    async def execute_batch_job(
        self,
        *,
        job_id: str,
        dry_run: bool,
        project_root: str | None,
    ) -> Dict[str, Any]:
        if dry_run:
            return {"success": True, "dry_run": True, "job_id": job_id}

        processor = self._get_batch_processor(project_root)
        try:
            result = await processor.execute_batch_job(job_id)
        except Exception as exc:
            raise ToolServiceError(
                message=str(exc),
                reason="batch_job_execution_failed",
                error_type=type(exc).__name__,
            ) from exc

        return {
            "success": True,
            "job_id": job_id,
            "result": self._serialize_batch_result(result),
        }

    async def get_batch_status(self, *, job_id: str, project_root: str | None) -> Dict[str, Any]:
        processor = self._get_batch_processor(project_root)
        try:
            status = processor.get_batch_status(job_id)
        except Exception as exc:
            raise ToolServiceError(
                message=str(exc),
                reason="batch_status_failed",
                error_type=type(exc).__name__,
            ) from exc

        return {"success": True, "status": status}

    async def write_with_claude(
        self,
        *,
        episode_number: int,
        dry_run: bool,
    ) -> Dict[str, Any]:
        def _build_prompt() -> Dict[str, Any]:
            path_service = create_mcp_aware_path_service()
            project_path = path_service.project_root

            plot_file = path_service.get_episode_plot_path(episode_number)
            if not plot_file or not plot_file.exists():
                raise ToolServiceError(
                    message=f"プロットファイルが見つかりません: 第{episode_number:03d}話",
                    reason="plot_not_found",
                )

            plot_content = plot_file.read_text(encoding="utf-8")
            plot_title = self._extract_title_from_plot(plot_content)

            manuscript_path = create_path_service().get_manuscript_path(episode_number)

            prompt = (
                f"# 第{episode_number:03d}話 原稿生成\n\n"
                "## 執筆要件\n"
                "- 視点: 三人称単一視点\n"
                "- 文体: ライトノベル調\n"
                "- 感情表現: 身体反応・感覚比喩・内面独白を最低3回\n"
                "- 会話比率: 約60%\n\n"
                "## プロット\n"
                f"{plot_content}\n"
            )

            return {
                "success": True,
                "prompt": prompt,
                "episode": episode_number,
                "plot_title": plot_title,
                "manuscript_path": str(manuscript_path),
                "dry_run": dry_run,
                "generated_at": project_now().datetime.isoformat(),
            }

        try:
            return await asyncio.to_thread(_build_prompt)
        except ToolServiceError:
            raise
        except Exception as exc:
            raise ToolServiceError(
                message=str(exc),
                reason="write_with_claude_failed",
                error_type=type(exc).__name__,
            ) from exc

    async def write_manuscript_draft(
        self,
        *,
        episode_number: int,
        plot_analysis: dict[str, Any] | None,
        writing_settings: dict[str, Any] | None,
    ) -> Dict[str, Any]:
        def _generate() -> Dict[str, Any]:
            path_service = create_mcp_aware_path_service()
            project_path = path_service.project_root

            artifact_store = create_artifact_store(storage_dir=project_path / ".noveler" / "artifacts")

            plot_artifact_id: str | None = None
            if plot_analysis and (plot_content := plot_analysis.get("content")):
                plot_artifact_id = artifact_store.store(
                    content=plot_content,
                    content_type="text",
                    description=f"第{episode_number:03d}話プロット（解析結果）",
                )
            else:
                plot_file = path_service.get_episode_plot_path(episode_number)
                if plot_file and plot_file.exists():
                    plot_artifact_id = artifact_store.store(
                        content=plot_file.read_text(encoding="utf-8"),
                        content_type="text",
                        source_file=str(plot_file),
                        description=f"第{episode_number:03d}話プロット",
                    )

            if not plot_artifact_id:
                raise ToolServiceError(
                    message=f"プロットが見つかりません: 第{episode_number:03d}話",
                    reason="plot_not_found",
                )

            word_count_target = (writing_settings or {}).get("word_count_target", 4000)
            prompt = (
                f"# 第{episode_number:03d}話 原稿執筆\n"
                f"- プロット参照: {plot_artifact_id}\n"
                f"- 目標文字数: {word_count_target}\n"
                "- 出力形式: Markdown\n"
            )

            return {
                "success": True,
                "prompt": prompt,
                "plot_artifact_id": plot_artifact_id,
                "episode": episode_number,
                "created_at": project_now().datetime.isoformat(),
            }

        try:
            return await asyncio.to_thread(_generate)
        except ToolServiceError:
            raise
        except Exception as exc:
            raise ToolServiceError(
                message=str(exc),
                reason="write_manuscript_draft_failed",
                error_type=type(exc).__name__,
            ) from exc

    # Helpers -----------------------------------------------------------------

    def _get_batch_processor(self, project_root: str | None) -> BatchProcessingAdapter:
        root = str(Path(project_root or ".").resolve())
        if root not in self._batch_processors:
            self._batch_processors[root] = BatchProcessingAdapter(root)
        return self._batch_processors[root]

    @staticmethod
    def _expand_step_ranges(step_ranges: List[dict[str, Any]] | None) -> List[int] | None:
        if not step_ranges:
            return None
        step_ids: List[int] = []
        for entry in step_ranges:
            if not isinstance(entry, dict):
                continue
            if "steps" in entry and isinstance(entry["steps"], Iterable):
                step_ids.extend(int(s) for s in entry["steps"] if isinstance(s, (int, float)))
                continue
            start = entry.get("start")
            end = entry.get("end", start)
            if start is None:
                continue
            try:
                start_int = int(start)
                end_int = int(end)
            except (TypeError, ValueError):
                continue
            step_ids.extend(range(start_int, end_int + 1))
        return sorted(set(step_ids)) if step_ids else None

    @staticmethod
    def _serialize_batch_result(result: Any) -> Dict[str, Any]:
        return {
            "total_episodes": getattr(result, "total_episodes", 0),
            "successful_episodes": getattr(result, "successful_episodes", 0),
            "failed_episodes": getattr(result, "failed_episodes", 0),
            "total_steps": getattr(result, "total_steps", 0),
            "successful_steps": getattr(result, "successful_steps", 0),
            "failed_steps": getattr(result, "failed_steps", 0),
            "execution_time": getattr(result, "execution_time", 0.0),
            "start_time": getattr(result, "start_time", None).isoformat()
            if getattr(result, "start_time", None)
            else None,
            "end_time": getattr(result, "end_time", None).isoformat()
            if getattr(result, "end_time", None)
            else None,
            "detailed_results": getattr(result, "detailed_results", {}),
            "errors": getattr(result, "errors", []),
        }

    @staticmethod
    def _extract_title_from_plot(plot_content: str) -> str | None:

        patterns = [
            r"[-*]\s*タイトル[:：]\s*(.+)",
            r"##?\s*タイトル[:：]?\s*(.+)",
            r"タイトル[:：]\s*(.+)",
            r"#\s*第\d+話\s+(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, plot_content)
            if match:
                title = match.group(1).strip()
                return title if title else None
        return None
