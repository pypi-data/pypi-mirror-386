# File: src/noveler/application/use_cases/ten_stage_progress_use_case.py
# Purpose: TenStageProgressUseCase - A30 10-stage writing process progress management
# Context: Implements Phase 2-A of backward compatibility removal (SPEC-A30-001)

"""TenStageProgressUseCase implementation for A30 10-stage writing progress management.

This use case manages the progress tracking and state transitions for the
A30-compliant 10-stage writing system. It bridges the gap between the legacy
5-stage system and the new detailed 10-stage execution framework.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from noveler.application.base.abstract_use_case import AbstractUseCase
from noveler.domain.value_objects.detailed_execution_stage import DetailedExecutionStage
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.five_stage_writing_execution import ExecutionStage
from noveler.domain.value_objects.structured_step_output import (
    StepCompletionStatus,
    StructuredStepOutput,
)


class ProgressStatus(Enum):
    """Progress status for each stage."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageProgress:
    """Progress information for a single stage."""

    stage: DetailedExecutionStage
    status: ProgressStatus = ProgressStatus.NOT_STARTED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int = 0
    last_output: Optional[StructuredStepOutput] = None
    error_messages: List[str] = field(default_factory=list)
    turns_used: int = 0
    estimated_turns_remaining: int = 0

    @property
    def duration_seconds(self) -> float:
        """Calculate stage execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0

    @property
    def is_complete(self) -> bool:
        """Check if stage is complete."""
        return self.status == ProgressStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if stage has failed."""
        return self.status == ProgressStatus.FAILED

    @property
    def can_retry(self) -> bool:
        """Check if stage can be retried."""
        return self.status == ProgressStatus.FAILED and self.attempts < 3


@dataclass
class TenStageProgressRequest:
    """Request for ten-stage progress operations."""

    episode_number: int
    project_root: Path
    operation: str  # "start", "update", "query", "reset"
    stage: Optional[DetailedExecutionStage] = None
    stage_output: Optional[StructuredStepOutput] = None
    error_message: Optional[str] = None
    force_reset: bool = False


@dataclass
class TenStageProgressResponse:
    """Response from ten-stage progress operations."""

    success: bool
    episode_number: int
    overall_progress: float  # 0.0 to 1.0
    current_stage: Optional[DetailedExecutionStage]
    stage_progresses: Dict[DetailedExecutionStage, StageProgress]
    total_turns_used: int = 0
    estimated_turns_remaining: int = 0
    total_attempts: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Check if all stages are complete."""
        return all(p.is_complete for p in self.stage_progresses.values())

    @property
    def has_failures(self) -> bool:
        """Check if any stages have failed."""
        return any(p.is_failed for p in self.stage_progresses.values())

    @property
    def completed_stages(self) -> List[DetailedExecutionStage]:
        """Get list of completed stages."""
        return [stage for stage, progress in self.stage_progresses.items() if progress.is_complete]

    @property
    def failed_stages(self) -> List[DetailedExecutionStage]:
        """Get list of failed stages."""
        return [stage for stage, progress in self.stage_progresses.items() if progress.is_failed]

    def get_next_stage(self) -> Optional[DetailedExecutionStage]:
        """Get the next stage to execute."""
        for stage in DetailedExecutionStage:
            progress = self.stage_progresses.get(stage)
            if progress and progress.status == ProgressStatus.NOT_STARTED:
                return stage
        return None


class TenStageProgressUseCase(AbstractUseCase[TenStageProgressRequest, TenStageProgressResponse]):
    """Use case for managing 10-stage writing progress.

    This use case provides:
    1. Progress tracking across 10 detailed execution stages
    2. State management and transitions
    3. Error recovery and retry logic
    4. Integration with A30CompatibilityAdapter
    5. Metrics and reporting

    Key responsibilities:
    - Track progress of each detailed stage
    - Manage stage transitions and dependencies
    - Handle failures and retries
    - Provide progress metrics and estimates
    - Support resumption from failures
    """

    def __init__(self, **kwargs):
        """Initialize the use case."""
        super().__init__(**kwargs)
        self._stage_progress_cache: Dict[int, Dict[DetailedExecutionStage, StageProgress]] = {}

    async def execute(self, request: TenStageProgressRequest) -> TenStageProgressResponse:
        """Execute the progress management operation.

        Args:
            request: The progress management request

        Returns:
            TenStageProgressResponse: The operation result
        """
        try:
            # 早期バリデーション
            try:
                episode_number_vo = EpisodeNumber(request.episode_number)
            except ValueError as e:
                return self._create_error_response(
                    request.episode_number,
                    f"無効なエピソード番号: {e}"
                )

            if request.operation == "start":
                return await self._handle_start(request)
            elif request.operation == "update":
                return await self._handle_update(request)
            elif request.operation == "query":
                return await self._handle_query(request)
            elif request.operation == "reset":
                return await self._handle_reset(request)
            else:
                return self._create_error_response(
                    episode_number_vo.value,
                    f"Unknown operation: {request.operation}"
                )
        except Exception as e:
            self.logger.exception("TenStageProgressUseCase execution error")
            return self._create_error_response(
                request.episode_number,
                f"Execution error: {str(e)}"
            )

    async def _handle_start(self, request: TenStageProgressRequest) -> TenStageProgressResponse:
        """Handle start operation - initialize progress tracking."""
        episode = request.episode_number

        # Initialize progress for all stages
        stage_progresses = {}
        for stage in DetailedExecutionStage:
            stage_progresses[stage] = StageProgress(
                stage=stage,
                estimated_turns_remaining=stage.expected_turns
            )

        # Cache the progress
        self._stage_progress_cache[episode] = stage_progresses

        # Calculate initial metrics
        total_estimated_turns = sum(s.expected_turns for s in DetailedExecutionStage)

        self.logger.info(f"Started 10-stage progress tracking for episode {episode}")

        return TenStageProgressResponse(
            success=True,
            episode_number=episode,
            overall_progress=0.0,
            current_stage=DetailedExecutionStage.DATA_COLLECTION,
            stage_progresses=stage_progresses,
            estimated_turns_remaining=total_estimated_turns,
            metadata={
                "started_at": datetime.now(timezone.utc).isoformat(),
                "total_stages": len(DetailedExecutionStage),
                "execution_mode": "a30_ten_stage"
            }
        )

    async def _handle_update(self, request: TenStageProgressRequest) -> TenStageProgressResponse:
        """Handle update operation - update stage progress."""
        episode = request.episode_number

        # Get cached progress
        if episode not in self._stage_progress_cache:
            return self._create_error_response(
                episode,
                f"No progress tracking found for episode {episode}"
            )

        stage_progresses = self._stage_progress_cache[episode]

        if not request.stage:
            return self._create_error_response(episode, "Stage is required for update operation")

        stage_progress = stage_progresses.get(request.stage)
        if not stage_progress:
            return self._create_error_response(
                episode,
                f"Stage {request.stage.value} not found in progress tracking"
            )

        # Update based on provided data
        if request.stage_output is not None:
            # Successful stage completion
            stage_progress.status = ProgressStatus.COMPLETED
            stage_progress.completed_at = datetime.now(timezone.utc)
            stage_progress.last_output = self._sanitize_stage_output(request.stage_output)
            stage_progress.turns_used = self._extract_turns_used(request.stage_output)

            if stage_progress.started_at is None:
                stage_progress.started_at = stage_progress.completed_at

        elif request.error_message:
            # Stage failure
            stage_progress.status = ProgressStatus.FAILED
            stage_progress.error_messages.append(request.error_message)
            stage_progress.attempts += 1

        else:
            # Stage in progress
            stage_progress.status = ProgressStatus.IN_PROGRESS
            if stage_progress.started_at is None:
                stage_progress.started_at = datetime.now(timezone.utc)

        # Calculate metrics
        overall_progress = self._calculate_overall_progress(stage_progresses)
        current_stage = self._determine_current_stage(stage_progresses)
        total_turns_used = sum(p.turns_used for p in stage_progresses.values())
        estimated_turns_remaining = sum(
            p.estimated_turns_remaining
            for p in stage_progresses.values()
            if p.status != ProgressStatus.COMPLETED
        )

        return TenStageProgressResponse(
            success=True,
            episode_number=episode,
            overall_progress=overall_progress,
            current_stage=current_stage,
            stage_progresses=stage_progresses,
            total_turns_used=total_turns_used,
            estimated_turns_remaining=estimated_turns_remaining,
            total_attempts=sum(p.attempts for p in stage_progresses.values()),
            metadata={
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_stage": request.stage.value
            }
        )

    async def _handle_query(self, request: TenStageProgressRequest) -> TenStageProgressResponse:
        """Handle query operation - retrieve current progress."""
        episode = request.episode_number

        if episode not in self._stage_progress_cache:
            # Return empty progress
            return TenStageProgressResponse(
                success=True,
                episode_number=episode,
                overall_progress=0.0,
                current_stage=None,
                stage_progresses={},
                metadata={"status": "not_started"}
            )

        stage_progresses = self._stage_progress_cache[episode]

        overall_progress = self._calculate_overall_progress(stage_progresses)
        current_stage = self._determine_current_stage(stage_progresses)
        total_turns_used = sum(p.turns_used for p in stage_progresses.values())
        estimated_turns_remaining = sum(
            p.estimated_turns_remaining
            for p in stage_progresses.values()
            if p.status != ProgressStatus.COMPLETED
        )

        return TenStageProgressResponse(
            success=True,
            episode_number=episode,
            overall_progress=overall_progress,
            current_stage=current_stage,
            stage_progresses=stage_progresses,
            total_turns_used=total_turns_used,
            estimated_turns_remaining=estimated_turns_remaining,
            total_attempts=sum(p.attempts for p in stage_progresses.values()),
            metadata={
                "queried_at": datetime.now(timezone.utc).isoformat()
            }
        )

    async def _handle_reset(self, request: TenStageProgressRequest) -> TenStageProgressResponse:
        """Handle reset operation - reset progress tracking."""
        episode = request.episode_number

        if not request.force_reset and episode not in self._stage_progress_cache:
            return self._create_error_response(
                episode,
                "No progress to reset. Use force_reset=True to initialize new progress."
            )

        # Reset or initialize progress
        stage_progresses = {}
        for stage in DetailedExecutionStage:
            stage_progresses[stage] = StageProgress(
                stage=stage,
                estimated_turns_remaining=stage.expected_turns
            )

        self._stage_progress_cache[episode] = stage_progresses

        self.logger.info(f"Reset 10-stage progress tracking for episode {episode}")

        return TenStageProgressResponse(
            success=True,
            episode_number=episode,
            overall_progress=0.0,
            current_stage=DetailedExecutionStage.DATA_COLLECTION,
            stage_progresses=stage_progresses,
            estimated_turns_remaining=sum(s.expected_turns for s in DetailedExecutionStage),
            metadata={
                "reset_at": datetime.now(timezone.utc).isoformat(),
                "force_reset": request.force_reset
            }
        )

    def _calculate_overall_progress(self, stage_progresses: Dict[DetailedExecutionStage, StageProgress]) -> float:
        """Calculate overall progress percentage."""
        if not stage_progresses:
            return 0.0

        completed_stages = sum(1 for p in stage_progresses.values() if p.is_complete)
        total_stages = len(stage_progresses)

        return completed_stages / total_stages if total_stages > 0 else 0.0

    def _determine_current_stage(
        self,
        stage_progresses: Dict[DetailedExecutionStage, StageProgress]
    ) -> Optional[DetailedExecutionStage]:
        """Determine the current active stage."""
        # First check for in-progress stages
        for stage, progress in stage_progresses.items():
            if progress.status == ProgressStatus.IN_PROGRESS:
                return stage

        # Then find the first not-started stage
        for stage in DetailedExecutionStage:
            progress = stage_progresses.get(stage)
            if progress and progress.status == ProgressStatus.NOT_STARTED:
                return stage

        # All stages are complete or failed
        return None

    def _create_error_response(self, episode_number: int, error_message: str) -> TenStageProgressResponse:
        """Create an error response."""
        return TenStageProgressResponse(
            success=False,
            episode_number=episode_number,
            overall_progress=0.0,
            current_stage=None,
            stage_progresses={},
            error_message=error_message,
            metadata={"error_at": datetime.now(timezone.utc).isoformat()}
        )

    def get_resumable_stages(self, episode_number: int) -> List[DetailedExecutionStage]:
        """Get list of stages that can be resumed or retried.

        Args:
            episode_number: The episode number

        Returns:
            List of stages that can be resumed
        """
        if episode_number not in self._stage_progress_cache:
            return []

        stage_progresses = self._stage_progress_cache[episode_number]
        resumable = []

        for stage, progress in stage_progresses.items():
            if progress.status in [ProgressStatus.NOT_STARTED, ProgressStatus.IN_PROGRESS]:
                resumable.append(stage)
            elif progress.can_retry:
                resumable.append(stage)

        return resumable

    def export_progress_report(self, episode_number: int) -> Dict[str, Any]:
        """Export a detailed progress report.

        Args:
            episode_number: The episode number

        Returns:
            Detailed progress report
        """
        if episode_number not in self._stage_progress_cache:
            return {"status": "not_found", "episode": episode_number}

        stage_progresses = self._stage_progress_cache[episode_number]

        completed_stages = [s.value for s, p in stage_progresses.items() if p.is_complete]
        failed_stages = [s.value for s, p in stage_progresses.items() if p.is_failed]
        pending_stages = [s.value for s, p in stage_progresses.items()
                         if p.status == ProgressStatus.NOT_STARTED]

        total_duration = sum(p.duration_seconds for p in stage_progresses.values())
        total_turns = sum(p.turns_used for p in stage_progresses.values())

        return {
            "episode": episode_number,
            "overall_progress": self._calculate_overall_progress(stage_progresses),
            "status": self._determine_overall_status(stage_progresses),
            "stages": {
                "completed": completed_stages,
                "failed": failed_stages,
                "pending": pending_stages,
                "total": len(DetailedExecutionStage)
            },
            "metrics": {
                "total_duration_seconds": total_duration,
                "total_turns_used": total_turns,
                "average_turns_per_stage": total_turns / len(completed_stages) if completed_stages else 0
            },
            "errors": [
                {"stage": s.value, "errors": p.error_messages}
                for s, p in stage_progresses.items() if p.error_messages
            ],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    def _determine_overall_status(self, stage_progresses: Dict[DetailedExecutionStage, StageProgress]) -> str:
        """Determine overall execution status."""
        if not stage_progresses:
            return "pending"

        if all(p.is_complete for p in stage_progresses.values()):
            return "completed"
        if any(p.is_failed for p in stage_progresses.values()):
            return "failed_with_errors"
        if any(p.status == ProgressStatus.IN_PROGRESS for p in stage_progresses.values()):
            return "in_progress"
        if any(p.is_complete for p in stage_progresses.values()):
            return "in_progress"
        return "pending"

    def _sanitize_stage_output(self, stage_output: Any) -> Any:
        """Reduce memory footprint for cached stage output."""
        if isinstance(stage_output, StructuredStepOutput):
            return stage_output
        if isinstance(stage_output, dict):
            # avoid retaining large nested structures
            keys_preview = list(stage_output.keys())[:5]
            return {"summary": "stage_output_dict", "keys": keys_preview}
        return repr(stage_output)

    def _extract_turns_used(self, stage_output: Any) -> int:
        """Safely extract turns used metadata from stage output."""
        if isinstance(stage_output, StructuredStepOutput):
            metadata = stage_output.execution_metadata
            if isinstance(metadata, dict):
                return metadata.get("turns_used", 2)

        metadata = getattr(stage_output, "execution_metadata", None)
        if isinstance(metadata, dict):
            return metadata.get("turns_used", 2)

        if isinstance(stage_output, dict):
            return stage_output.get("turns_used", 2)

        return 2
