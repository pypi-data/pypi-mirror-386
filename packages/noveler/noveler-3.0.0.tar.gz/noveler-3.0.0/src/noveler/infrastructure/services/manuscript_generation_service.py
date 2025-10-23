"""Five stage manuscript generation infrastructure services.

This module provides a pragmatic, test-friendly implementation of the
five-stage writing workflow used throughout the codebase.  The focus is
on small, dependency-light primitives that are easy to exercise from
unit tests while remaining faithful to the design documented in
SPEC-FIVE-STAGE-001.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Tuple
import uuid

from noveler.domain.value_objects.five_stage_writing_execution import (
    ExecutionStage,
    FiveStageExecutionContext,
    FiveStageWritingRequest,
    FiveStageWritingResponse,
    StageExecutionResult,
    StageExecutionStatus,
)
from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.services.content_validation_service import ContentValidationService, ValidationLevel
from noveler.infrastructure.services.independent_session_executor import IndependentSessionExecutor


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _safe_stage_max_turns(stage: ExecutionStage) -> int:
    """Return the maximum number of turns allowed for a stage.

    Older value-object revisions did not expose ``max_turns`` so we
    compute a reasonable default from ``expected_turns``.
    """

    return getattr(stage, "max_turns", stage.expected_turns * 2)


def _to_jsonable(value: Any) -> Any:
    """Best-effort conversion to JSON serialisable structures."""

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(v) for v in value]
    return repr(value)


def _execution_time_ms(result: Any) -> float:
    ms = getattr(result, "execution_time_ms", None)
    if isinstance(ms, (int, float)):
        return float(ms)
    seconds = getattr(result, "execution_time_seconds", None)
    if isinstance(seconds, (int, float)):
        return float(seconds) * 1000
    return 0.0


# ---------------------------------------------------------------------------
# Progress monitor
# ---------------------------------------------------------------------------


class FiveStageProgressMonitor:
    """Simple progress reporter used by the execution service."""

    def __init__(self, context: FiveStageExecutionContext) -> None:
        self.context = context
        self.logger = get_logger(__name__)

    def _get_console(self):  # pragma: no cover - exercised via tests
        from noveler.presentation.shared import shared_utilities as shared_utils

        return shared_utils.console

    def display_stage_start(self, stage: ExecutionStage) -> None:
        console = self._get_console()
        progress = self.context.get_progress_percentage()
        stage_index = list(ExecutionStage).index(stage) + 1
        console.print(f"\n[blue]🚀 Stage {stage_index}/5: {stage.display_name} 開始[/blue]")
        console.print(f"[dim]予想ターン数: {stage.expected_turns}[/dim]")
        total_turns_used = getattr(self.context, "total_turns_used", 0)
        turns_display = total_turns_used if isinstance(total_turns_used, (int, float)) else str(total_turns_used)
        console.print(f"[dim]全体進捗: {progress:.1f}% (累計 {turns_display} ターン)[/dim]")

    def display_stage_progress(
        self, stage: ExecutionStage, turns_used: int, status_message: str = ""
    ) -> None:
        console = self._get_console()
        max_turns = _safe_stage_max_turns(stage)
        console.print(f"[yellow]⚡ {stage.display_name}: {turns_used}/{max_turns}ターン使用[/yellow]")
        if status_message:
            console.print(f"[dim]{status_message}[/dim]")

    def display_stage_complete(self, stage: ExecutionStage, result: StageExecutionResult) -> None:
        console = self._get_console()
        elapsed_ms = getattr(result, "execution_time_ms", None)
        if elapsed_ms is None and hasattr(result, "execution_time_seconds"):
            maybe_seconds = getattr(result, "execution_time_seconds")
            if isinstance(maybe_seconds, (int, float)):
                elapsed_ms = maybe_seconds * 1000
        if isinstance(elapsed_ms, (int, float)):
            elapsed_display = f"{elapsed_ms:.0f}ms"
        else:
            elapsed_display = "N/A"

        if result.is_success():
            console.print(
                f"[green]✅ {stage.display_name} 完了[/green] "
                f"({result.turns_used}ターン, {elapsed_display})"
            )
            console.print(f"[dim]出力: {result.get_output_summary()}[/dim]")
        else:
            console.print(
                f"[red]❌ {stage.display_name} 失敗[/red] "
                f"({result.turns_used}ターン): {result.error_message or '原因不明'}"
            )

    def display_overall_progress(self, completed_stages: Iterable[ExecutionStage] | None = None) -> None:
        console = self._get_console()
        if completed_stages is None:
            completed = sum(
                1 for stage in ExecutionStage if stage in self.context.stage_results and self.context.stage_results[stage].is_success()
            )
        else:
            completed = len(list(completed_stages))
        total = len(ExecutionStage)
        progress = self.context.get_progress_percentage()
        console.print(f"\n[blue]📊 実行進捗: {completed}/{total}段階完了 ({progress:.1f}%)[/blue]")
        turns_used = getattr(self.context, "total_turns_used", "N/A")
        total_cost = getattr(self.context, "total_cost_usd", 0.0)
        cost_display = f"${total_cost:.4f}" if isinstance(total_cost, (int, float)) else str(total_cost)
        console.print(f"[dim]総ターン数: {turns_used}, 総コスト: {cost_display}[/dim]")


# ---------------------------------------------------------------------------
# Persistence manager
# ---------------------------------------------------------------------------


class FiveStageDataPersistenceManager:
    """Minimal JSON-based session persistence helper."""

    _SESSION_META_FILE = "session.json"

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)
        self.path_service = create_path_service(self.project_root)
        self.session_dir = self.path_service.get_management_dir() / "five_stage_sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def create_session_directory(self, session_id: str) -> Path:
        session_path = self.session_dir / session_id
        session_path.mkdir(parents=True, exist_ok=True)
        return session_path

    def save_session_metadata(self, session_id: str, metadata: dict[str, Any]) -> Path:
        session_path = self.create_session_directory(session_id)
        meta_file = session_path / self._SESSION_META_FILE
        meta_file.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        return meta_file

    def load_session_data(self, session_id: str) -> dict[str, Any] | None:
        meta_file = self.session_dir / session_id / self._SESSION_META_FILE
        if not meta_file.exists():
            return None
        try:
            return json.loads(meta_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.logger.warning("セッションメタデータの解析に失敗しました: %s", meta_file)
            return None

    def save_stage_result(self, session_id: str, stage: ExecutionStage, result: StageExecutionResult) -> Path:
        session_path = self.create_session_directory(session_id)
        result_file = session_path / f"stage_{stage.value}_result.json"
        output_data = getattr(result, "output_data", None)
        if output_data is None:
            output_data = getattr(result, "stage_outputs", {})
        output_data = _to_jsonable(output_data)

        payload = {
            "stage": stage.value,
            "status": result.status.value,
            "turns_used": result.turns_used,
            "execution_time_ms": result.execution_time_ms,
            "error_message": result.error_message,
            "output_data": output_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        result_file.write_text(json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")
        return result_file

    def load_stage_result(self, session_id: str, stage: ExecutionStage) -> StageExecutionResult | None:
        result_file = self.session_dir / session_id / f"stage_{stage.value}_result.json"
        if not result_file.exists():
            return None
        try:
            payload = json.loads(result_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.logger.warning("段階結果の解析に失敗しました: %s", result_file)
            return None

        return StageExecutionResult(
            stage=stage,
            status=StageExecutionStatus(payload.get("status", StageExecutionStatus.FAILED.value)),
            execution_time_ms=payload.get("execution_time_ms", 0.0),
            turns_used=payload.get("turns_used", 0),
            error_message=payload.get("error_message"),
            output_data=payload.get("output_data", {}),
        )

    def cleanup_session(self, session_id: str) -> None:
        session_path = self.session_dir / session_id
        if session_path.exists():
            for child in session_path.glob("**/*"):
                if child.is_file():
                    child.unlink()
            for child in sorted(session_path.glob("**"), reverse=True):
                if child.is_dir():
                    child.rmdir()
            session_path.rmdir()


# ---------------------------------------------------------------------------
# Error recovery manager
# ---------------------------------------------------------------------------


class FiveStageErrorRecoveryManager:
    """Thin async wrapper around Claude recovery strategies."""

    def __init__(self, claude_service: Any) -> None:
        self.claude_service = claude_service
        self.logger = get_logger(__name__)

    async def _execute_recovery_strategy(
        self,
        stage: ExecutionStage,
        result: StageExecutionResult,
        context: FiveStageExecutionContext,
    ) -> StageExecutionResult:
        """Fallback strategy: re-use the previous result but mark as retry."""

        await asyncio.sleep(0)  # allow cooperative scheduling during tests
        recovered = StageExecutionResult(
            stage=stage,
            status=StageExecutionStatus.IN_PROGRESS,
            execution_time_ms=result.execution_time_ms,
            turns_used=result.turns_used,
            error_message=result.error_message,
            output_data=dict(result.output_data),
        )
        recovered.output_data.setdefault("recovery_attempted", True)
        return recovered

    async def attempt_stage_recovery(
        self,
        stage: ExecutionStage,
        original_result: StageExecutionResult,
        context: FiveStageExecutionContext,
    ) -> StageExecutionResult | None:
        if original_result.is_success():
            return original_result
        try:
            return await self._execute_recovery_strategy(stage, original_result, context)
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.exception("段階復旧戦略の実行に失敗: %s", exc)
            return None


# ---------------------------------------------------------------------------
# Manuscript generation service
# ---------------------------------------------------------------------------


class ManuscriptGenerationService:
    """High level orchestrator for the five stage execution flow."""

    def __init__(self, claude_service: Any, project_root: Path) -> None:
        self.claude_service = claude_service
        self.project_root = Path(project_root)
        self.logger = get_logger(__name__)
        self.persistence_manager = FiveStageDataPersistenceManager(self.project_root)
        self.error_recovery_manager = FiveStageErrorRecoveryManager(claude_service)
        self.independent_executor = IndependentSessionExecutor({"claude_service": claude_service})
        self.content_validator = ContentValidationService(ValidationLevel.STANDARD)
        self._path_service = None
        self.console_service = self._get_console()

    # ------------------------------------------------------------------
    # Lazy helpers
    # ------------------------------------------------------------------
    def _get_console(self):  # pragma: no cover - behaviour verified in tests
        from noveler.presentation.shared import shared_utilities as shared_utils

        return shared_utils.console

    def _get_path_service(self):  # pragma: no cover - exercised in tests
        current = self.__dict__.get("_path_service", None)
        if current is None:
            from noveler.infrastructure.adapters import path_service_adapter

            path_service = path_service_adapter.create_path_service(self.project_root)
            object.__setattr__(self, "_path_service", path_service)
            current = path_service
        return current

    # ------------------------------------------------------------------
    # Core execution logic
    # ------------------------------------------------------------------
    async def execute_five_stage_writing(self, request: FiveStageWritingRequest) -> FiveStageWritingResponse:
        context_candidate: FiveStageExecutionContext | None = None
        if hasattr(request, "create_execution_context"):
            try:
                maybe_context = request.create_execution_context()
                if isinstance(maybe_context, FiveStageExecutionContext):
                    context_candidate = maybe_context
            except Exception:
                context_candidate = None

        if context_candidate is None:
            episode_number = getattr(request, "episode_number", 0) or 0
            word_count_target = getattr(request, "word_count_target", 3500)
            genre = getattr(request, "genre", "unknown")
            viewpoint = getattr(request, "viewpoint", "三人称一元視点")
            viewpoint_character = getattr(request, "viewpoint_character", "主人公")
            custom_requirements = list(getattr(request, "custom_requirements", []))

            context_candidate = FiveStageExecutionContext(
                session_id=str(uuid.uuid4()),
                episode_number=episode_number,
                project_root=self.project_root,
                word_count_target=word_count_target,
                genre=genre,
                viewpoint=viewpoint,
                viewpoint_character=viewpoint_character,
                custom_requirements=custom_requirements,
                total_execution_start=datetime.now(timezone.utc),
            )

        context = context_candidate
        monitor = FiveStageProgressMonitor(context)
        stage_results: dict[ExecutionStage, StageExecutionResult] = {}
        previous_transfers: list[Any] = []

        for stage in ExecutionStage:
            monitor.display_stage_start(stage)
            result, transfer = await self._execute_single_stage_independent(stage, context, previous_transfers)
            stage_results[stage] = result
            if transfer is not None:
                previous_transfers.append(transfer)
                self._update_shared_data(context, transfer)
            monitor.display_stage_complete(stage, result)
            if not result.is_success():
                recovery = await self.error_recovery_manager.attempt_stage_recovery(stage, result, context)
                suggestions = []
                if recovery and recovery.output_data:
                    suggestions = [f"{stage.display_name}を再実行"]
                total_time_ms = sum(_execution_time_ms(res) for res in stage_results.values())
                return FiveStageWritingResponse(
                    success=False,
                    session_id=context.session_id,
                    stage_results=stage_results,
                    failed_stage=stage,
                    error_message=result.error_message,
                    total_execution_time_ms=total_time_ms,
                    total_turns_used=getattr(context, "total_turns_used", 0),
                    total_cost_usd=getattr(context, "total_cost_usd", 0.0),
                    recovery_suggestions=suggestions,
                )

        monitor.display_overall_progress()
        total_time_ms = sum(_execution_time_ms(res) for res in stage_results.values())
        return FiveStageWritingResponse(
            success=True,
            session_id=context.session_id,
            stage_results=stage_results,
            total_execution_time_ms=total_time_ms,
            total_turns_used=getattr(context, "total_turns_used", 0),
            total_cost_usd=getattr(context, "total_cost_usd", 0.0),
        )

    async def _execute_single_stage_independent(
        self,
        stage: ExecutionStage,
        context: FiveStageExecutionContext,
        previous_transfers: list[Any] | None = None,
    ) -> Tuple[StageExecutionResult, Any | None]:
        transfers = previous_transfers or []
        call_result = self.independent_executor.execute_stage_independently(stage, context, transfers)
        if inspect.isawaitable(call_result):
            result, transfer = await call_result
        else:
            result, transfer = call_result

        stage_results = getattr(context, "stage_results", None)
        if not isinstance(stage_results, dict):
            stage_results = {}
            setattr(context, "stage_results", stage_results)
        stage_results[stage] = result

        raw_turns = getattr(result, "turns_used", 0)
        turns_used = raw_turns if isinstance(raw_turns, (int, float)) else 0
        cost_increment = self._estimate_cost(turns_used)
        updated = False
        try:
            context.update_performance_metrics(turns_used, cost_increment)
            updated = True
        except Exception:
            pass
        if not updated:
            total_turns = getattr(context, "total_turns_used", 0)
            if isinstance(total_turns, (int, float)):
                setattr(context, "total_turns_used", total_turns + turns_used)
            total_cost = getattr(context, "total_cost_usd", 0.0)
            if isinstance(total_cost, (int, float)):
                setattr(context, "total_cost_usd", total_cost + cost_increment)
        return result, transfer

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------
    def _extract_stage_output(self, stage: ExecutionStage, response: Any) -> dict[str, Any]:
        raw = getattr(response, "response", "")
        if not raw:
            return {}
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
            return {"data": data}
        except json.JSONDecodeError:
            return {"raw_output": raw}

    def _emergency_text_extraction(self, text: str, required_keys: Iterable[str]) -> dict[str, str]:
        extracted: dict[str, str] = {}
        lowered = text.lower()
        for key in required_keys:
            pattern = re.compile(rf"{re.escape(key)}\s*[:：]\s*(.+)", re.IGNORECASE)
            match = pattern.search(text)
            if match:
                extracted[key] = match.group(1).strip()
                continue
            if key.lower() in lowered:
                sentence = re.findall(r"[^。！？.!?]*" + re.escape(key) + r"[^。！？.!?]*", text)
                if sentence:
                    extracted[key] = sentence[0].strip()
        return extracted

    def _extract_manuscript_from_text(self, text: str) -> str:
        pattern = re.compile(r"(#\s*第\d+話.*)", re.DOTALL)
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
        return text.strip()

    def _update_shared_data(self, context: FiveStageExecutionContext, transfer: Any | None) -> None:
        if not transfer or not hasattr(transfer, "key_data"):
            return
        data = getattr(transfer, "key_data", {}) or {}
        if hasattr(context, "shared_data"):
            context.shared_data.update(data)
        else:  # pragma: no cover - legacy safeguard
            setattr(context, "shared_data", dict(data))

    def _estimate_turns_used(self, stage: ExecutionStage, response_length: int) -> int:
        base = max(1, response_length // 600)
        return max(base, stage.expected_turns)

    def _estimate_cost(self, turns_used: int) -> float:
        return round(0.05 * max(turns_used, 0), 4)

    async def _save_final_manuscript(self, response: Any, stage_results: Iterable[Any]) -> Path:
        path_service = self._get_path_service()
        manuscript_dir = path_service.get_manuscript_dir()
        Path(manuscript_dir).mkdir(parents=True, exist_ok=True)
        episode = getattr(response, "episode_number", 0) or 0
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_path = manuscript_dir / f"第{episode:03d}話_最終稿_{timestamp}.md"
        content = getattr(response, "final_manuscript", "").strip()
        if not content:
            summaries = [getattr(r, "get_output_summary", lambda: "")() for r in stage_results]
            content = "\n\n".join(filter(None, summaries))
        file_path.write_text(content, encoding="utf-8")
        return file_path

    async def _save_quality_report(self, response: Any) -> Path:
        path_service = self._get_path_service()
        quality_dir = path_service.get_quality_records_dir() if hasattr(path_service, "get_quality_records_dir") else path_service.get_management_dir() / "品質記録"
        Path(quality_dir).mkdir(parents=True, exist_ok=True)
        episode = getattr(response, "episode_number", 0) or 0
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_path = quality_dir / f"quality_ep{episode:03d}_{timestamp}.json"
        payload = {
            "episode_number": episode,
            "quality_metrics": getattr(response, "quality_metrics", {}),
            "total_cost": getattr(response, "total_cost", 0.0),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        file_path.write_text(json.dumps(_to_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")
        return file_path

    # ------------------------------------------------------------------
    # Quality helpers used in tests/integration
    # ------------------------------------------------------------------
    def _extract_quality_scores(self, context: FiveStageExecutionContext) -> dict[str, Any]:
        scores = {}
        for stage, result in context.stage_results.items():
            if result.output_data:
                for key, value in result.output_data.items():
                    if isinstance(value, (int, float)):
                        scores[f"{stage.value}_{key}"] = value
        return scores


# Backwards compatibility alias ------------------------------------------------
FiveStageExecutionService = ManuscriptGenerationService

__all__ = [
    "FiveStageProgressMonitor",
    "FiveStageDataPersistenceManager",
    "FiveStageErrorRecoveryManager",
    "ManuscriptGenerationService",
    "FiveStageExecutionService",
]
