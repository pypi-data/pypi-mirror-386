# File: src/noveler/infrastructure/services/unified_session_executor.py
# Purpose: Orchestrates unified writing sessions across five and ten stage workflows.
# Context: Bridges legacy Claude pipelines with the newer A30 detailed execution model.
"""Unified session executor bridging five-stage and ten-stage writing flows."""

from __future__ import annotations

import asyncio
import uuid
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, MutableMapping

from noveler.application.services.a30_compatibility_adapter import (
    A30CompatibilityAdapter,
    CompatibilityMode,
)
from noveler.application.use_cases.ten_stage_progress_use_case import (
    TenStageProgressRequest,
    TenStageProgressUseCase,
)
from noveler.domain.value_objects.detailed_execution_stage import DetailedExecutionStage
from noveler.domain.value_objects.five_stage_writing_execution import (
    ExecutionStage,
    FiveStageWritingRequest,
)
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.services.content_validation_service import ContentValidationService

StageKey = ExecutionStage | DetailedExecutionStage


@dataclass
class SessionState:
    """Lightweight state tracker used while a unified writing session executes."""

    session_id: str
    total_turns_available: int = 30
    turns_used: int = 0
    error_count: int = 0
    current_stage: StageKey | None = None
    stage_outputs: dict[StageKey, str] = field(default_factory=dict)
    accumulated_context: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    use_ten_stage: bool = False

    @property
    def remaining_turns(self) -> int:
        """Return the number of turns that can still be consumed."""
        remaining = self.total_turns_available - self.turns_used
        return remaining if remaining > 0 else 0

    def can_continue(self) -> bool:
        """Determine whether the executor should keep processing stages."""
        return self.remaining_turns > 0 and self.error_count < 3


@dataclass
class TurnAllocation:
    """Allocation rule describing how many turns a stage may consume."""

    stage: StageKey
    min_turns: int
    max_turns: int
    priority: int
    actual_turns: int = 0


@dataclass
class UnifiedSessionResponse:
    """Structured response returned after a unified session completes."""

    session_id: str
    status: str
    stage_outputs: Mapping[StageKey, str] = field(default_factory=dict)
    turns_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_responses: list[dict[str, Any]] = field(default_factory=list)
    use_ten_stage: bool = False
    legacy_stage_outputs: Mapping[ExecutionStage, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable view of the response."""
        stage_payload = {
            _stage_key_to_value(stage): output
            for stage, output in self.stage_outputs.items()
        }
        legacy_payload = {
            stage.value: output for stage, output in self.legacy_stage_outputs.items()
        }
        return {
            "session_id": self.session_id,
            "status": self.status,
            "turns_used": self.turns_used,
            "stage_outputs": stage_payload,
            "metadata": self.metadata,
            "raw_responses": self.raw_responses,
            "use_ten_stage": self.use_ten_stage,
            "legacy_stage_outputs": legacy_payload,
        }


class UnifiedSessionExecutor:
    """Coordinates unified writing sessions across multiple execution modes."""

    def __init__(
        self,
        claude_service: Any = None,
        validation_service: ContentValidationService | None = None,
        *,
        compatibility_adapter: A30CompatibilityAdapter | None = None,
        progress_use_case: TenStageProgressUseCase | None = None,
        logger_name: str = __name__,
        total_turn_limit: int = 30,
    ) -> None:
        if claude_service is None:
            raise ValueError("claude_service is required")
        self.claude_service = claude_service
        self.validation_service = validation_service or ContentValidationService()
        self.compatibility_adapter = compatibility_adapter
        self.progress_use_case = progress_use_case
        self.total_turn_limit = total_turn_limit
        self._logger = get_logger(logger_name)

        self.default_allocations_5stage = self._build_default_allocations_5stage()
        self.default_allocations_10stage = self._build_default_allocations_10stage()
        # テスト互換性: default_allocations プロパティを追加
        self.default_allocations = self.default_allocations_5stage

    async def execute_unified_session(self, request: FiveStageWritingRequest) -> UnifiedSessionResponse:
        """Execute a unified writing session (5-stage or 10-stage)."""
        use_ten_stage = self._determine_execution_mode(request)
        allocations = (
            self._calculate_turn_allocations_10stage(request)
            if use_ten_stage
            else self._calculate_turn_allocations_5stage(request)
        )

        session_id = getattr(request, "session_id", f"session-{uuid.uuid4().hex[:8]}")
        state = SessionState(
            session_id=session_id,
            total_turns_available=self.total_turn_limit,
            use_ten_stage=use_ten_stage,
        )

        raw_responses: list[dict[str, Any]] = []
        context = state.accumulated_context

        if use_ten_stage and self.progress_use_case:
            await self._safe_progress_call(
                TenStageProgressRequest(
                    episode_number=request.episode_number,
                    project_root=request.project_root,
                    operation="start",
                )
            )

        for stage, allocation in allocations.items():
            if not state.can_continue():
                break

            state.current_stage = stage
            remaining_turns = state.remaining_turns
            if remaining_turns <= 0:
                break

            max_turns = min(allocation.max_turns, remaining_turns)
            try:
                response = await self.claude_service.execute_with_turn_limit(
                    stage=stage,
                    request=request,
                    max_turns=max_turns,
                    context=context,
                )
            except Exception as exc:  # pragma: no cover - defensive logging path
                state.error_count += 1
                self._logger.exception(
                    "Stage execution failed", extra={"stage": _stage_key_to_value(stage), "error": str(exc)}
                )
                if not state.can_continue():
                    break
                continue

            raw_responses.append({"stage": _stage_key_to_value(stage), "response": response})

            turns_used = int(response.get("turns_used") or 0)
            state.turns_used += turns_used

            output_text = response.get("output") or ""
            cleaned_output = await self._validate_and_clean_output(output_text, stage)
            state.stage_outputs[stage] = cleaned_output

            if cleaned_output:
                context = f"{context}\n{cleaned_output}".strip()
                state.accumulated_context = context

            if not response.get("success", True):
                state.error_count += 1
                if not state.can_continue():
                    break

            if use_ten_stage and self.progress_use_case:
                await self._safe_progress_call(
                    TenStageProgressRequest(
                        episode_number=request.episode_number,
                        project_root=request.project_root,
                        operation="update",
                        stage=stage if isinstance(stage, DetailedExecutionStage) else None,
                    )
                )

            if state.turns_used >= state.total_turns_available:
                break

        status = "completed" if state.error_count < 3 else "failed"
        if state.turns_used >= state.total_turns_available and status == "completed":
            status = "completed_with_turn_limit"

        metadata: dict[str, Any] = {
            "execution_mode": "10-stage" if use_ten_stage else "5-stage",
            "turn_limit": state.total_turns_available,
            "turns_used": state.turns_used,
            "stages_completed": len(state.stage_outputs),
        }
        if use_ten_stage:
            metadata["total_detailed_stages"] = len(DetailedExecutionStage)

        legacy_outputs: Mapping[ExecutionStage, str] = {}
        if use_ten_stage and state.stage_outputs:
            legacy_outputs = self._convert_to_legacy_format(
                {stage: output for stage, output in state.stage_outputs.items() if isinstance(stage, DetailedExecutionStage)}
            )

        return UnifiedSessionResponse(
            session_id=state.session_id,
            status=status,
            stage_outputs=dict(state.stage_outputs),
            turns_used=state.turns_used,
            metadata=metadata,
            raw_responses=raw_responses,
            use_ten_stage=use_ten_stage,
            legacy_stage_outputs=legacy_outputs,
        )

    def get_stage_allocations(self, request: FiveStageWritingRequest) -> Mapping[StageKey, TurnAllocation]:
        """Return an ordered mapping of stage allocations for the request."""
        if self._determine_execution_mode(request):
            return self._calculate_turn_allocations_10stage(request)
        return self._calculate_turn_allocations_5stage(request)

    def _determine_execution_mode(self, request: FiveStageWritingRequest) -> bool:
        """Determine if the current session should run in ten-stage mode."""
        explicit_choice = getattr(request, "use_ten_stage", None)
        if explicit_choice is not None:
            return bool(explicit_choice)

        if self.compatibility_adapter is None:
            return False

        mode = self.compatibility_adapter.compatibility_mode
        if mode == CompatibilityMode.A30_DETAILED_TEN_STAGE:
            return True
        if mode == CompatibilityMode.LEGACY_FIVE_STAGE:
            return False

        return True

    def _build_default_allocations_5stage(self) -> MutableMapping[ExecutionStage, TurnAllocation]:
        """Return default allocations for the legacy five-stage workflow."""
        defaults: dict[ExecutionStage, TurnAllocation] = {
            ExecutionStage.DATA_COLLECTION: TurnAllocation(
                ExecutionStage.DATA_COLLECTION, min_turns=3, max_turns=5, priority=3
            ),
            ExecutionStage.PLOT_ANALYSIS: TurnAllocation(
                ExecutionStage.PLOT_ANALYSIS, min_turns=3, max_turns=6, priority=4
            ),
            ExecutionStage.EPISODE_DESIGN: TurnAllocation(
                ExecutionStage.EPISODE_DESIGN, min_turns=4, max_turns=6, priority=4
            ),
            ExecutionStage.MANUSCRIPT_WRITING: TurnAllocation(
                ExecutionStage.MANUSCRIPT_WRITING, min_turns=6, max_turns=8, priority=5
            ),
            ExecutionStage.QUALITY_FINALIZATION: TurnAllocation(
                ExecutionStage.QUALITY_FINALIZATION, min_turns=3, max_turns=5, priority=4
            ),
        }
        return defaults

    def _build_default_allocations_10stage(self) -> MutableMapping[DetailedExecutionStage, TurnAllocation]:
        """Return default allocations for the detailed ten-stage workflow."""
        priority_map: dict[DetailedExecutionStage, int] = {
            DetailedExecutionStage.DATA_COLLECTION: 3,
            DetailedExecutionStage.PLOT_ANALYSIS: 4,
            DetailedExecutionStage.LOGIC_VERIFICATION: 4,
            DetailedExecutionStage.CHARACTER_CONSISTENCY: 4,
            DetailedExecutionStage.DIALOGUE_DESIGN: 3,
            DetailedExecutionStage.EMOTION_CURVE: 3,
            DetailedExecutionStage.SCENE_ATMOSPHERE: 3,
            DetailedExecutionStage.MANUSCRIPT_WRITING: 5,
            DetailedExecutionStage.QUALITY_FINALIZATION: 4,
        }
        allocations: dict[DetailedExecutionStage, TurnAllocation] = {}
        for stage in DetailedExecutionStage:
            min_turns = max(1, stage.expected_turns - 1)
            max_turns = stage.expected_turns + 1
            allocations[stage] = TurnAllocation(stage, min_turns, max_turns, priority_map.get(stage, 3))
        return allocations

    def _calculate_turn_allocations_5stage(
        self, request: FiveStageWritingRequest
    ) -> MutableMapping[ExecutionStage, TurnAllocation]:
        complexity = self._estimate_complexity(request)
        allocations: dict[ExecutionStage, TurnAllocation] = {}
        for stage, default in self.default_allocations_5stage.items():
            extra = max(0, int(round((default.max_turns - default.min_turns) * complexity)))
            max_turns = min(default.max_turns + extra, default.min_turns + 4)
            allocations[stage] = TurnAllocation(stage, default.min_turns, max_turns, default.priority)
        return allocations

    def _calculate_turn_allocations(
        self, request: FiveStageWritingRequest
    ) -> dict[ExecutionStage, TurnAllocation]:
        """Test-compatible wrapper for _calculate_turn_allocations_5stage.

        This method is used by tests to get turn allocations.
        """
        return self._calculate_turn_allocations_5stage(request)

    def _calculate_turn_allocations_10stage(
        self, request: FiveStageWritingRequest
    ) -> MutableMapping[DetailedExecutionStage, TurnAllocation]:
        complexity = self._estimate_complexity(request)
        allocations: dict[DetailedExecutionStage, TurnAllocation] = {}
        for stage, default in self.default_allocations_10stage.items():
            flex_window = max(1, int(round(stage.expected_turns * 0.5)))
            bonus = max(0, int(round(flex_window * complexity)))
            max_turns = min(default.max_turns + bonus, stage.max_turns)
            allocations[stage] = TurnAllocation(stage, default.min_turns, max_turns, default.priority)
        return allocations

    def _estimate_complexity(self, request: FiveStageWritingRequest) -> float:
        """Estimate request complexity to adjust turn allocations."""
        base = 0.3
        episode_factor = min(request.episode_number / 100.0, 0.4)
        base += episode_factor

        word_target = getattr(request, "word_count_target", 0) or 0
        if word_target > 4000:
            base += 0.1
        if getattr(request, "debug_mode", False):
            base += 0.1
        if getattr(request, "dry_run", False):
            base = max(0.0, base - 0.1)

        return max(0.0, min(1.0, base))

    async def _validate_and_clean_output(self, content: str, stage: StageKey) -> str:
        """Validate and sanitise stage output before storing it."""
        cleaned = self._remove_system_messages(content)
        cleaned = self._remove_prompt_contamination(cleaned)
        cleaned = self._remove_json_metadata(cleaned)

        if not cleaned.strip():
            cleaned = content.strip()

        validation_result = None
        if self.validation_service:
            try:
                result_or_coro = self.validation_service.validate(cleaned, _stage_key_to_value(stage))
                validation_result = await _ensure_awaited(result_or_coro)
            except Exception:  # pragma: no cover - validation is best effort
                self._logger.debug("Validation service raised an exception", exc_info=True)

        if validation_result and getattr(validation_result, "cleaned_content", None):
            cleaned = validation_result.cleaned_content

        return cleaned.strip()

    def _convert_to_legacy_format(
        self, detailed_outputs: Mapping[DetailedExecutionStage, str]
    ) -> Mapping[ExecutionStage, str]:
        """Combine detailed-stage outputs into their legacy equivalents."""
        if not detailed_outputs:
            return {}

        adapter = self.compatibility_adapter or A30CompatibilityAdapter(CompatibilityMode.A30_DETAILED_TEN_STAGE)
        legacy_map: dict[ExecutionStage, list[str]] = {}
        for stage, output in detailed_outputs.items():
            legacy_stage = adapter.convert_detailed_to_legacy(stage)
            legacy_map.setdefault(legacy_stage, []).append(output)

        return {stage: "\n".join(part for part in parts if part).strip() for stage, parts in legacy_map.items()}

    async def _safe_progress_call(self, request: TenStageProgressRequest) -> None:
        """Call the progress use case and suppress non-critical failures."""
        if not self.progress_use_case:
            return
        try:
            result = self.progress_use_case.execute(request)
            await _ensure_awaited(result)
        except Exception:  # pragma: no cover - telemetry only
            self._logger.debug("Progress tracking call failed", exc_info=True)

    @staticmethod
    def _remove_json_metadata(content: str) -> str:
        """Remove inline JSON metadata blocks from content."""
        cleaned = content
        json_block_patterns = [
            ("```json", "```"),
            ("```", "```"),
        ]
        for start_marker, end_marker in json_block_patterns:
            search_start = 0
            while True:
                start = cleaned.lower().find(start_marker, search_start)
                if start == -1:
                    break
                end = cleaned.find(end_marker, start + len(start_marker))
                if end == -1:
                    cleaned = cleaned[:start]
                    break
                cleaned = cleaned[:start] + cleaned[end + len(end_marker) :]
                search_start = start

        lines = []
        for line in cleaned.splitlines():
            stripped = line.strip()
            if stripped.startswith("{") and stripped.endswith("}"):
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                continue
            lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def _remove_prompt_contamination(content: str) -> str:
        """Remove prompt scaffolding that leaks into model output."""
        forbidden_keywords = [
            "## ",
            "���Ă�������",
            "Claude",
            "�K���܂߂�",
            "�`�F�b�N",
        ]
        cleaned_lines: list[str] = []
        for line in content.splitlines():
            if any(keyword in line for keyword in forbidden_keywords):
                continue
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    @staticmethod
    def _remove_system_messages(content: str) -> str:
        """Remove obvious system log markers."""
        prefixes = ["[System]", "[Error]", "[Warning]", "DEBUG:", "INFO:", "WARNING:"]
        return "\n".join(line for line in content.splitlines() if not any(prefix in line for prefix in prefixes))

    @staticmethod
    def _extract_manuscript_text(content: str) -> str:
        """Extract narrative text starting from the first numbered section."""
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("第") and "話" in stripped:
                return "\n".join(lines[idx:]).strip()
        return content.strip()

    @staticmethod
    def _normalize_whitespace(content: str) -> str:
        """Collapse excessive whitespace while preserving sentence order."""
        normalized_lines = [
            re.sub(r"\s+", " ", line).strip() for line in content.splitlines()
        ]
        return "\n".join(line for line in normalized_lines if line)


def _stage_key_to_value(stage: StageKey) -> str:
    """Return a stable string representation for either stage type."""
    if hasattr(stage, "value"):
        return stage.value  # type: ignore[return-value]
    if hasattr(stage, "name"):
        return stage.name  # type: ignore[return-value]
    return str(stage)


async def _ensure_awaited(value: Any) -> Any:
    """Await the value when it behaves like a coroutine."""
    if asyncio.iscoroutine(value) or hasattr(value, "__await__"):
        return await value
    return value
