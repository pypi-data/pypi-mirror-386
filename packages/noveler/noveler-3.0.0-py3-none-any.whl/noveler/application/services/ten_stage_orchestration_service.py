# File: src/noveler/application/services/ten_stage_orchestration_service.py
# Purpose: Orchestrate 10-stage writing with progress tracking and compatibility adapter
# Context: Phase 2-A implementation - integrates TenStageProgressUseCase with A30CompatibilityAdapter

"""TenStageOrchestrationService for coordinating 10-stage writing execution.

This service orchestrates the entire 10-stage writing process by:
1. Managing progress through TenStageProgressUseCase
2. Adapting between legacy and detailed stages via A30CompatibilityAdapter
3. Coordinating with TenStageEpisodeWritingUseCase for execution
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from noveler.application.services.a30_compatibility_adapter import (
    A30CompatibilityAdapter,
    CompatibilityMode,
)
from noveler.application.use_cases.ten_stage_progress_use_case import (
    TenStageProgressRequest,
    TenStageProgressResponse,
    TenStageProgressUseCase,
)
from noveler.domain.value_objects.detailed_execution_stage import DetailedExecutionStage
from noveler.domain.value_objects.five_stage_writing_execution import (
    ExecutionStage,
    FiveStageWritingRequest,
    FiveStageWritingResponse,
)
from noveler.domain.value_objects.structured_step_output import StructuredStepOutput
from noveler.infrastructure.logging.unified_logger import get_logger


@dataclass
class OrchestrationConfig:
    """Configuration for orchestration service."""

    enable_progress_tracking: bool = True
    compatibility_mode: CompatibilityMode = CompatibilityMode.A30_DETAILED_TEN_STAGE
    max_retries_per_stage: int = 3
    enable_parallel_stages: bool = False
    checkpoint_frequency: int = 2  # Save checkpoint every N stages


@dataclass
class OrchestrationResult:
    """Result from orchestration execution."""

    success: bool
    episode_number: int
    manuscript_path: Optional[Path]
    progress_report: Dict[str, Any]
    stage_outputs: Dict[DetailedExecutionStage, StructuredStepOutput]
    total_turns_used: int
    total_cost_usd: float
    error_message: Optional[str] = None
    recovery_suggestions: List[str] = None


class TenStageOrchestrationError(Exception):
    """Raised when orchestration fails and partial progress is available."""

    def __init__(self, message: str, error_result: OrchestrationResult) -> None:
        super().__init__(message)
        self.error_result = error_result


class TenStageOrchestrationService:
    """Service for orchestrating 10-stage writing execution.

    This service provides the main integration point for Phase 2-A,
    coordinating between progress tracking, compatibility adaptation,
    and actual execution.
    """

    def __init__(
        self,
        config: Optional[OrchestrationConfig] = None,
        progress_use_case: Optional[TenStageProgressUseCase] = None,
        compatibility_adapter: Optional[A30CompatibilityAdapter] = None,
    ):
        """Initialize the orchestration service.

        Args:
            config: Orchestration configuration
            progress_use_case: Progress tracking use case
            compatibility_adapter: Compatibility adapter for stage mapping
        """
        self.config = config or OrchestrationConfig()
        self.logger = get_logger(__name__)

        # Initialize dependencies
        self.progress_use_case = progress_use_case or TenStageProgressUseCase()
        self.compatibility_adapter = compatibility_adapter or A30CompatibilityAdapter(
            compatibility_mode=self.config.compatibility_mode
        )

        self._checkpoints: Dict[int, Dict[str, Any]] = {}

    async def orchestrate_episode_writing(
        self,
        request: FiveStageWritingRequest
    ) -> OrchestrationResult:
        """Orchestrate the complete 10-stage writing process.

        Args:
            request: Writing request with episode details

        Returns:
            OrchestrationResult: Complete orchestration result
        """
        episode_number = request.episode_number
        self.logger.info(f"Starting 10-stage orchestration for episode {episode_number}")

        try:
            # Initialize progress tracking
            if self.config.enable_progress_tracking:
                await self._initialize_progress(episode_number, request.project_root)

            # Execute stages with progress tracking
            stage_outputs = await self._execute_all_stages(request)

            # Generate final manuscript
            manuscript_path = await self._generate_manuscript(
                episode_number,
                request.project_root,
                stage_outputs
            )

            # Get final progress report
            progress_report = await self._get_final_progress_report(episode_number)

            # Calculate metrics
            total_turns = self._calculate_total_turns(stage_outputs)
            total_cost = self._calculate_total_cost(total_turns)

            return OrchestrationResult(
                success=True,
                episode_number=episode_number,
                manuscript_path=manuscript_path,
                progress_report=progress_report,
                stage_outputs=stage_outputs,
                total_turns_used=total_turns,
                total_cost_usd=total_cost
            )

        except Exception as exc:  # noqa: BLE001 - bubble up with context
            self.logger.exception(f"Orchestration failed for episode {episode_number}")
            partial_report = await self._get_partial_progress_report(episode_number)
            error_result = self._create_error_result(
                episode_number,
                str(exc),
                partial_report
            )
            raise TenStageOrchestrationError(str(exc), error_result) from exc

    async def _initialize_progress(self, episode_number: int, project_root: Path) -> None:
        """Initialize progress tracking for the episode."""
        request = TenStageProgressRequest(
            episode_number=episode_number,
            project_root=project_root,
            operation="start"
        )
        response = await self.progress_use_case.execute(request)
        if not response.success:
            raise RuntimeError(f"Failed to initialize progress: {response.error_message}")

    async def _execute_all_stages(
        self,
        request: FiveStageWritingRequest
    ) -> Dict[DetailedExecutionStage, StructuredStepOutput]:
        """Execute all 10 detailed stages with progress tracking.

        Args:
            request: Writing request

        Returns:
            Dictionary of stage outputs
        """
        stage_outputs = {}
        episode_number = request.episode_number

        for stage in DetailedExecutionStage:
            self.logger.info(f"Executing stage: {stage.display_name}")

            attempt = 0
            while True:
                try:
                    # Update progress to in-progress for this attempt
                    await self._update_progress_in_progress(
                        episode_number,
                        stage,
                        request.project_root
                    )

                    # Execute the stage
                    output = await self._execute_single_stage(stage, request, stage_outputs)
                    stage_outputs[stage] = output

                    # Update progress to completed
                    await self._update_progress_completed(
                        episode_number,
                        stage,
                        request.project_root,
                        output
                    )

                    # Create checkpoint if needed
                    if len(stage_outputs) % self.config.checkpoint_frequency == 0:
                        await self._create_checkpoint(episode_number, stage_outputs)

                    break  # Stage succeeded

                except Exception as e:  # noqa: PERF203 - retries are explicit here
                    attempt += 1
                    self.logger.error(f"Stage {stage.value} failed: {e}")

                    await self._update_progress_failed(
                        episode_number,
                        stage,
                        request.project_root,
                        str(e)
                    )

                    should_retry = (
                        attempt <= self.config.max_retries_per_stage
                        and await self._should_retry_stage(
                            episode_number,
                            stage,
                            request.project_root
                        )
                    )

                    if should_retry:
                        self.logger.info(
                            "Retrying stage %s (attempt %s/%s)",
                            stage.value,
                            attempt,
                            self.config.max_retries_per_stage,
                        )
                        continue

                    raise

        return stage_outputs

    async def _execute_single_stage(
        self,
        stage: DetailedExecutionStage,
        request: FiveStageWritingRequest,
        previous_outputs: Dict[DetailedExecutionStage, StructuredStepOutput]
    ) -> StructuredStepOutput:
        """Execute a single detailed stage.

        Args:
            stage: The stage to execute
            request: Writing request
            previous_outputs: Outputs from previous stages

        Returns:
            StructuredStepOutput: Stage execution result
        """
        # Build context from previous outputs
        context_data = self._build_stage_context(stage, request, previous_outputs)

        # Create stage-specific prompt using compatibility adapter
        prompt_data = self.compatibility_adapter.create_stage_specific_prompt(
            stage,
            context_data
        )

        # Simulate stage execution (placeholder for actual execution)
        # In production, this would call the actual execution service
        raw_output = await self._simulate_stage_execution(stage, prompt_data)

        # Calculate quality scores
        quality_scores = self._calculate_quality_scores(stage, raw_output)

        # Create compatible output
        return self.compatibility_adapter.create_compatible_output(
            stage,
            raw_output,
            quality_scores
        )

    async def _simulate_stage_execution(
        self,
        stage: DetailedExecutionStage,
        prompt_data: Dict[str, str]
    ) -> Dict[str, Any]:
        """Simulate stage execution (placeholder).

        In production, this would integrate with the actual
        Claude Code execution service.
        """
        await asyncio.sleep(0.1)  # Simulate execution time

        # Return simulated output based on stage
        stage_output_map = {
            DetailedExecutionStage.DATA_COLLECTION: {
                "collected_data": {
                    "plot_summary": "Episode plot data collected",
                    "character_info": "Character information gathered",
                    "world_settings": "World settings retrieved"
                }
            },
            DetailedExecutionStage.PLOT_ANALYSIS: {
                "plot_analysis_result": {
                    "key_events": ["Event 1", "Event 2"],
                    "conflict_points": ["Main conflict"],
                    "resolution_path": "Resolution strategy"
                }
            },
            DetailedExecutionStage.LOGIC_VERIFICATION: {
                "logic_verification_result": {
                    "consistency_check": "passed",
                    "plot_holes": [],
                    "timeline_issues": []
                }
            },
            DetailedExecutionStage.CHARACTER_CONSISTENCY: {
                "character_consistency_result": {
                    "character_arcs": "Consistent",
                    "personality_check": "passed",
                    "dialogue_appropriateness": "verified"
                }
            },
            DetailedExecutionStage.DIALOGUE_DESIGN: {
                "dialogue_design_result": {
                    "dialogue_structure": "Designed",
                    "character_voices": "Differentiated",
                    "conversation_flow": "Natural"
                }
            },
            DetailedExecutionStage.EMOTION_CURVE: {
                "emotion_curve_result": {
                    "emotional_peaks": [0.3, 0.7, 0.9],
                    "tension_progression": "Rising",
                    "reader_engagement": "High"
                }
            },
            DetailedExecutionStage.SCENE_ATMOSPHERE: {
                "scene_atmosphere_result": {
                    "atmosphere_elements": "Defined",
                    "sensory_details": "Rich",
                    "mood_consistency": "Maintained"
                }
            },
            DetailedExecutionStage.MANUSCRIPT_WRITING: {
                "manuscript": "Generated manuscript content...",
                "word_count": 3500
            },
            DetailedExecutionStage.QUALITY_FINALIZATION: {
                "quality_checks": {
                    "grammar": "checked",
                    "consistency": "verified",
                    "readability": "optimized"
                },
                "final_manuscript": "Finalized manuscript content..."
            }
        }

        return stage_output_map.get(stage, {"default_output": f"Output for {stage.value}"})

    def _build_stage_context(
        self,
        stage: DetailedExecutionStage,
        request: FiveStageWritingRequest,
        previous_outputs: Dict[DetailedExecutionStage, StructuredStepOutput]
    ) -> Dict[str, Any]:
        """Build context data for stage execution."""
        context = {
            "episode_number": request.episode_number,
            "genre": request.genre,
            "viewpoint": request.viewpoint,
            "viewpoint_character": request.viewpoint_character,
            "word_count_target": request.word_count_target,
        }

        # Add outputs from previous stages
        for prev_stage, output in previous_outputs.items():
            if output.structured_data:
                context[f"{prev_stage.value}_output"] = output.structured_data

        return context

    def _calculate_quality_scores(
        self,
        stage: DetailedExecutionStage,
        output: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate quality scores for stage output."""
        # Placeholder quality scoring
        base_score = 0.85
        scores = {
            "overall": base_score,
            "completeness": 0.9,
            "consistency": 0.85,
            "clarity": 0.88
        }

        # Stage-specific scoring adjustments
        if stage == DetailedExecutionStage.MANUSCRIPT_WRITING:
            word_count = output.get("word_count", 0)
            scores["word_count_adherence"] = min(1.0, word_count / 3500)
        elif stage == DetailedExecutionStage.DIALOGUE_DESIGN:
            scores["dialogue_naturalness"] = 0.87
            scores["character_voice_distinction"] = 0.83

        return scores

    async def _update_progress_in_progress(
        self,
        episode_number: int,
        stage: DetailedExecutionStage,
        project_root: Path | None = None
    ) -> None:
        """Update progress to in-progress for a stage."""
        if not self.config.enable_progress_tracking:
            return

        request = TenStageProgressRequest(
            episode_number=episode_number,
            project_root=project_root,
            operation="update",
            stage=stage
        )
        await self.progress_use_case.execute(request)

    async def _update_progress_completed(
        self,
        episode_number: int,
        stage: DetailedExecutionStage,
        project_root: Path,
        output: StructuredStepOutput
    ) -> None:
        """Update progress to completed for a stage."""
        if not self.config.enable_progress_tracking:
            return

        request = TenStageProgressRequest(
            episode_number=episode_number,
            project_root=project_root,
            operation="update",
            stage=stage,
            stage_output=output
        )
        await self.progress_use_case.execute(request)

    async def _update_progress_failed(
        self,
        episode_number: int,
        stage: DetailedExecutionStage,
        project_root: Path,
        error_message: str
    ) -> None:
        """Update progress to failed for a stage."""
        if not self.config.enable_progress_tracking:
            return

        request = TenStageProgressRequest(
            episode_number=episode_number,
            project_root=project_root,
            operation="update",
            stage=stage,
            error_message=error_message
        )
        await self.progress_use_case.execute(request)

    async def _should_retry_stage(
        self,
        episode_number: int,
        stage: DetailedExecutionStage,
        project_root: Path | None = None
    ) -> bool:
        """Check if a stage should be retried."""
        if not self.config.enable_progress_tracking:
            return False

        # Query current progress
        effective_project_root = project_root or Path(".")

        request = TenStageProgressRequest(
            episode_number=episode_number,
            project_root=effective_project_root,
            operation="query"
        )
        response = await self.progress_use_case.execute(request)

        if response.success and response.stage_progresses:
            progress = response.stage_progresses.get(stage)
            if progress:
                if progress.attempts > self.config.max_retries_per_stage:
                    return False
                return progress.can_retry

        return False

    async def _create_checkpoint(
        self,
        episode_number: int,
        stage_outputs: Dict[DetailedExecutionStage, StructuredStepOutput]
    ) -> None:
        """Create a checkpoint of current progress."""
        checkpoint = {
            "episode": episode_number,
            "stages_completed": len(stage_outputs),
            "outputs": {
                stage.value: output.to_dict() if hasattr(output, 'to_dict') else str(output)
                for stage, output in stage_outputs.items()
            }
        }
        self._checkpoints[episode_number] = checkpoint
        self.logger.info(f"Checkpoint created for episode {episode_number}")

    async def _generate_manuscript(
        self,
        episode_number: int,
        project_root: Path,
        stage_outputs: Dict[DetailedExecutionStage, StructuredStepOutput]
    ) -> Path:
        """Generate final manuscript from stage outputs."""
        manuscript_dir = project_root / "manuscripts"
        manuscript_dir.mkdir(exist_ok=True)

        manuscript_path = manuscript_dir / f"episode_{episode_number:03d}.md"

        # Extract manuscript content from final stage
        final_output = stage_outputs.get(DetailedExecutionStage.QUALITY_FINALIZATION)
        if final_output and final_output.structured_data:
            content = final_output.structured_data.get(
                "final_manuscript",
                "Manuscript generation pending"
            )
        else:
            content = "Manuscript generation failed"

        if not isinstance(content, str):
            content = str(content)

        manuscript_path.write_text(content, encoding="utf-8")
        return manuscript_path

    async def _get_final_progress_report(self, episode_number: int) -> Dict[str, Any]:
        """Get final progress report."""
        if not self.config.enable_progress_tracking:
            return {"status": "progress_tracking_disabled"}

        return self.progress_use_case.export_progress_report(episode_number)

    async def _get_partial_progress_report(self, episode_number: int) -> Dict[str, Any]:
        """Get partial progress report for error scenarios."""
        if not self.config.enable_progress_tracking:
            return {}

        request = TenStageProgressRequest(
            episode_number=episode_number,
            project_root=Path("."),
            operation="query"
        )
        response = await self.progress_use_case.execute(request)

        if response.success:
            return {
                "completed_stages": [s.value for s in response.completed_stages],
                "failed_stages": [s.value for s in response.failed_stages],
                "overall_progress": response.overall_progress,
                "total_turns_used": response.total_turns_used
            }
        return {}

    def _calculate_total_turns(
        self,
        stage_outputs: Dict[DetailedExecutionStage, StructuredStepOutput]
    ) -> int:
        """Calculate total turns used."""
        total = 0
        for output in stage_outputs.values():
            if output.execution_metadata:
                total += output.execution_metadata.get("turns_used", 2)
        return total

    def _calculate_total_cost(self, total_turns: int) -> float:
        """Calculate total cost in USD."""
        # Assuming $0.025 per turn
        cost_per_turn = 0.025
        return total_turns * cost_per_turn

    def _create_error_result(
        self,
        episode_number: int,
        error_message: str,
        partial_progress: Dict[str, Any]
    ) -> OrchestrationResult:
        """Create error result."""
        return OrchestrationResult(
            success=False,
            episode_number=episode_number,
            manuscript_path=None,
            progress_report=partial_progress,
            stage_outputs={},
            total_turns_used=partial_progress.get("total_turns_used", 0),
            total_cost_usd=0.0,
            error_message=error_message,
            recovery_suggestions=[
                "Check the error logs for detailed information",
                "Ensure all required services are running",
                "Verify the episode configuration is correct",
                "Consider retrying with reduced complexity"
            ]
        )

    async def resume_from_checkpoint(
        self,
        episode_number: int,
        request: FiveStageWritingRequest
    ) -> OrchestrationResult:
        """Resume execution from a checkpoint.

        Args:
            episode_number: Episode to resume
            request: Original writing request

        Returns:
            OrchestrationResult: Resumption result
        """
        checkpoint = self._checkpoints.get(episode_number)
        if not checkpoint:
            return self._create_error_result(
                episode_number,
                f"No checkpoint found for episode {episode_number}",
                {}
            )

        self.logger.info(f"Resuming from checkpoint for episode {episode_number}")

        # Restore stage outputs
        stage_outputs = {}
        for stage_str, output_data in checkpoint["outputs"].items():
            # Convert string back to DetailedExecutionStage
            for stage in DetailedExecutionStage:
                if stage.value == stage_str:
                    # Simplified restoration - in production would deserialize properly
                    stage_outputs[stage] = output_data
                    break

        # Continue execution from next stage
        try:
            remaining_outputs = await self._execute_remaining_stages(
                request,
                stage_outputs
            )
            stage_outputs.update(remaining_outputs)

            # Generate manuscript and complete
            manuscript_path = await self._generate_manuscript(
                episode_number,
                request.project_root,
                stage_outputs
            )

            progress_report = await self._get_final_progress_report(episode_number)

            return OrchestrationResult(
                success=True,
                episode_number=episode_number,
                manuscript_path=manuscript_path,
                progress_report=progress_report,
                stage_outputs=stage_outputs,
                total_turns_used=self._calculate_total_turns(stage_outputs),
                total_cost_usd=self._calculate_total_cost(
                    self._calculate_total_turns(stage_outputs)
                )
            )
        except Exception as e:
            self.logger.exception(f"Resume failed for episode {episode_number}")
            return self._create_error_result(
                episode_number,
                f"Resume failed: {str(e)}",
                await self._get_partial_progress_report(episode_number)
            )

    async def _execute_remaining_stages(
        self,
        request: FiveStageWritingRequest,
        completed_outputs: Dict[DetailedExecutionStage, Any]
    ) -> Dict[DetailedExecutionStage, StructuredStepOutput]:
        """Execute remaining stages after checkpoint."""
        remaining_outputs = {}
        completed_stages = set(completed_outputs.keys())

        for stage in DetailedExecutionStage:
            if stage not in completed_stages:
                output = await self._execute_single_stage(stage, request, completed_outputs)
                remaining_outputs[stage] = output
                completed_outputs[stage] = output

        return remaining_outputs
