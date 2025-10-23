# File: tests/unit/application/use_cases/test_ten_stage_progress_use_case.py
# Purpose: Unit tests for TenStageProgressUseCase
# Context: Phase 2-A implementation testing - validates progress tracking functionality

"""Unit tests for TenStageProgressUseCase."""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from noveler.application.use_cases.ten_stage_progress_use_case import (
    ProgressStatus,
    StageProgress,
    TenStageProgressRequest,
    TenStageProgressResponse,
    TenStageProgressUseCase,
)
from noveler.domain.value_objects.detailed_execution_stage import DetailedExecutionStage
from noveler.domain.value_objects.structured_step_output import (
    QualityMetrics,
    StepCompletionStatus,
    StructuredStepOutput,
)


@pytest.fixture
def use_case():
    """Create TenStageProgressUseCase instance for testing."""
    return TenStageProgressUseCase()


@pytest.fixture
def sample_request():
    """Create a sample request for testing."""
    return TenStageProgressRequest(
        episode_number=1,
        project_root=Path("/test/project"),
        operation="start"
    )


@pytest.fixture
def sample_stage_output():
    """Create a sample stage output for testing."""
    return StructuredStepOutput(
        step_id="step_data_collection",
        step_name="Data Collection",
        completion_status=StepCompletionStatus.COMPLETED,
        structured_data={"test": "data"},
        quality_metrics=QualityMetrics(overall_score=0.9, specific_metrics={}),
        validation_passed=True,
        execution_metadata={"turns_used": 2}
    )


class TestTenStageProgressUseCase:
    """Test suite for TenStageProgressUseCase."""

    @pytest.mark.asyncio
    async def test_start_operation_initializes_progress(self, use_case, sample_request):
        """Test that start operation initializes progress tracking."""
        response = await use_case.execute(sample_request)

        assert response.success is True
        assert response.episode_number == 1
        assert response.overall_progress == 0.0
        assert response.current_stage == DetailedExecutionStage.DATA_COLLECTION
        assert len(response.stage_progresses) == len(DetailedExecutionStage)

        # Verify all stages are initialized as NOT_STARTED
        for stage, progress in response.stage_progresses.items():
            assert progress.status == ProgressStatus.NOT_STARTED
            assert progress.stage == stage
            assert progress.estimated_turns_remaining == stage.expected_turns

    @pytest.mark.asyncio
    async def test_update_operation_marks_stage_completed(
        self, use_case, sample_request, sample_stage_output
    ):
        """Test that update operation correctly marks stage as completed."""
        # First start tracking
        await use_case.execute(sample_request)

        # Update with completed stage
        update_request = TenStageProgressRequest(
            episode_number=1,
            project_root=Path("/test/project"),
            operation="update",
            stage=DetailedExecutionStage.DATA_COLLECTION,
            stage_output=sample_stage_output
        )

        response = await use_case.execute(update_request)

        assert response.success is True
        progress = response.stage_progresses[DetailedExecutionStage.DATA_COLLECTION]
        assert progress.status == ProgressStatus.COMPLETED
        assert progress.last_output == sample_stage_output
        assert progress.turns_used == 2
        assert response.overall_progress > 0.0

    @pytest.mark.asyncio
    async def test_update_operation_handles_stage_failure(self, use_case, sample_request):
        """Test that update operation correctly handles stage failures."""
        # Start tracking
        await use_case.execute(sample_request)

        # Update with failure
        update_request = TenStageProgressRequest(
            episode_number=1,
            project_root=Path("/test/project"),
            operation="update",
            stage=DetailedExecutionStage.PLOT_ANALYSIS,
            error_message="Stage execution failed"
        )

        response = await use_case.execute(update_request)

        assert response.success is True
        progress = response.stage_progresses[DetailedExecutionStage.PLOT_ANALYSIS]
        assert progress.status == ProgressStatus.FAILED
        assert "Stage execution failed" in progress.error_messages
        assert progress.attempts == 1
        assert progress.can_retry is True

    @pytest.mark.asyncio
    async def test_query_operation_returns_current_progress(self, use_case, sample_request):
        """Test that query operation returns current progress."""
        # Start and update some progress
        await use_case.execute(sample_request)

        # Mark first stage as completed
        update_request = TenStageProgressRequest(
            episode_number=1,
            project_root=Path("/test/project"),
            operation="update",
            stage=DetailedExecutionStage.DATA_COLLECTION,
            stage_output=sample_stage_output
        )
        await use_case.execute(update_request)

        # Query progress
        query_request = TenStageProgressRequest(
            episode_number=1,
            project_root=Path("/test/project"),
            operation="query"
        )

        response = await use_case.execute(query_request)

        assert response.success is True
        assert response.overall_progress > 0.0
        assert DetailedExecutionStage.DATA_COLLECTION in response.completed_stages

    @pytest.mark.asyncio
    async def test_query_nonexistent_episode_returns_empty(self, use_case):
        """Test that querying non-existent episode returns empty progress."""
        query_request = TenStageProgressRequest(
            episode_number=999,
            project_root=Path("/test/project"),
            operation="query"
        )

        response = await use_case.execute(query_request)

        assert response.success is True
        assert response.overall_progress == 0.0
        assert response.current_stage is None
        assert len(response.stage_progresses) == 0
        assert response.metadata["status"] == "not_started"

    @pytest.mark.asyncio
    async def test_reset_operation_clears_progress(self, use_case, sample_request):
        """Test that reset operation clears existing progress."""
        # Start and make some progress
        await use_case.execute(sample_request)

        # Update some stages
        update_request = TenStageProgressRequest(
            episode_number=1,
            project_root=Path("/test/project"),
            operation="update",
            stage=DetailedExecutionStage.DATA_COLLECTION,
            stage_output=sample_stage_output
        )
        await use_case.execute(update_request)

        # Reset progress
        reset_request = TenStageProgressRequest(
            episode_number=1,
            project_root=Path("/test/project"),
            operation="reset",
            force_reset=True
        )

        response = await use_case.execute(reset_request)

        assert response.success is True
        assert response.overall_progress == 0.0
        assert response.current_stage == DetailedExecutionStage.DATA_COLLECTION

        # All stages should be reset to NOT_STARTED
        for progress in response.stage_progresses.values():
            assert progress.status == ProgressStatus.NOT_STARTED
            assert progress.turns_used == 0

    @pytest.mark.asyncio
    async def test_invalid_operation_returns_error(self, use_case):
        """Test that invalid operation returns error response."""
        invalid_request = TenStageProgressRequest(
            episode_number=1,
            project_root=Path("/test/project"),
            operation="invalid_op"
        )

        response = await use_case.execute(invalid_request)

        assert response.success is False
        assert "Unknown operation" in response.error_message

    @pytest.mark.asyncio
    async def test_progress_calculation_accuracy(self, use_case, sample_request, sample_stage_output):
        """Test accuracy of overall progress calculation."""
        await use_case.execute(sample_request)

        total_stages = len(DetailedExecutionStage)
        completed_count = 0

        # Complete stages one by one and verify progress
        for stage in list(DetailedExecutionStage)[:3]:  # Complete first 3 stages
            update_request = TenStageProgressRequest(
                episode_number=1,
                project_root=Path("/test/project"),
                operation="update",
                stage=stage,
                stage_output=sample_stage_output
            )
            response = await use_case.execute(update_request)
            completed_count += 1

            expected_progress = completed_count / total_stages
            assert abs(response.overall_progress - expected_progress) < 0.01

    @pytest.mark.asyncio
    async def test_stage_retry_limit(self, use_case, sample_request):
        """Test that stages have a retry limit."""
        await use_case.execute(sample_request)

        # Fail the same stage multiple times
        for i in range(4):  # Try 4 times (more than limit)
            update_request = TenStageProgressRequest(
                episode_number=1,
                project_root=Path("/test/project"),
                operation="update",
                stage=DetailedExecutionStage.PLOT_ANALYSIS,
                error_message=f"Attempt {i+1} failed"
            )
            response = await use_case.execute(update_request)

            progress = response.stage_progresses[DetailedExecutionStage.PLOT_ANALYSIS]
            if i < 2:  # First 2 failures should allow retry (attempts will be 1, then 2)
                assert progress.can_retry is True
            else:
                # After 3 attempts, should not be able to retry
                assert progress.can_retry is False

    @pytest.mark.asyncio
    async def test_get_resumable_stages(self, use_case, sample_request, sample_stage_output):
        """Test getting resumable stages."""
        await use_case.execute(sample_request)

        # Mark some stages as completed, some as failed
        stages_to_complete = [
            DetailedExecutionStage.DATA_COLLECTION,
            DetailedExecutionStage.PLOT_ANALYSIS
        ]

        for stage in stages_to_complete:
            update_request = TenStageProgressRequest(
                episode_number=1,
                project_root=Path("/test/project"),
                operation="update",
                stage=stage,
                stage_output=sample_stage_output
            )
            await use_case.execute(update_request)

        # Fail one stage
        fail_request = TenStageProgressRequest(
            episode_number=1,
            project_root=Path("/test/project"),
            operation="update",
            stage=DetailedExecutionStage.LOGIC_VERIFICATION,
            error_message="Failed"
        )
        await use_case.execute(fail_request)

        resumable = use_case.get_resumable_stages(1)

        # Failed stage should be resumable
        assert DetailedExecutionStage.LOGIC_VERIFICATION in resumable
        # Not-started stages should be resumable
        assert DetailedExecutionStage.CHARACTER_CONSISTENCY in resumable
        # Completed stages should not be resumable
        assert DetailedExecutionStage.DATA_COLLECTION not in resumable

    @pytest.mark.asyncio
    async def test_export_progress_report(self, use_case, sample_request, sample_stage_output):
        """Test exporting progress report."""
        await use_case.execute(sample_request)

        # Complete some stages
        for stage in list(DetailedExecutionStage)[:2]:
            update_request = TenStageProgressRequest(
                episode_number=1,
                project_root=Path("/test/project"),
                operation="update",
                stage=stage,
                stage_output=sample_stage_output
            )
            await use_case.execute(update_request)

        report = use_case.export_progress_report(1)

        assert report["episode"] == 1
        assert report["overall_progress"] > 0.0
        assert len(report["stages"]["completed"]) == 2
        assert report["metrics"]["total_turns_used"] == 4  # 2 stages * 2 turns
        assert "generated_at" in report

    @pytest.mark.asyncio
    async def test_concurrent_stage_updates(self, use_case, sample_request, sample_stage_output):
        """Test handling concurrent stage updates."""
        await use_case.execute(sample_request)

        # Create multiple update tasks
        update_tasks = []
        stages = list(DetailedExecutionStage)[:3]

        for stage in stages:
            update_request = TenStageProgressRequest(
                episode_number=1,
                project_root=Path("/test/project"),
                operation="update",
                stage=stage,
                stage_output=sample_stage_output
            )
            update_tasks.append(use_case.execute(update_request))

        # Execute concurrently
        responses = await asyncio.gather(*update_tasks)

        # All should succeed
        for response in responses:
            assert response.success is True

        # Verify final state
        query_request = TenStageProgressRequest(
            episode_number=1,
            project_root=Path("/test/project"),
            operation="query"
        )
        final_response = await use_case.execute(query_request)

        assert len(final_response.completed_stages) == 3

    @pytest.mark.asyncio
    async def test_stage_duration_tracking(self, use_case, sample_request, sample_stage_output):
        """Test that stage duration is tracked correctly."""
        await use_case.execute(sample_request)

        # Start a stage
        start_request = TenStageProgressRequest(
            episode_number=1,
            project_root=Path("/test/project"),
            operation="update",
            stage=DetailedExecutionStage.DATA_COLLECTION
        )
        await use_case.execute(start_request)

        # Simulate some work
        await asyncio.sleep(0.1)

        # Complete the stage
        complete_request = TenStageProgressRequest(
            episode_number=1,
            project_root=Path("/test/project"),
            operation="update",
            stage=DetailedExecutionStage.DATA_COLLECTION,
            stage_output=sample_stage_output
        )
        response = await use_case.execute(complete_request)

        progress = response.stage_progresses[DetailedExecutionStage.DATA_COLLECTION]
        assert progress.duration_seconds > 0

    def test_stage_progress_properties(self):
        """Test StageProgress properties."""
        progress = StageProgress(
            stage=DetailedExecutionStage.DATA_COLLECTION,
            status=ProgressStatus.COMPLETED
        )

        assert progress.is_complete is True
        assert progress.is_failed is False
        assert progress.can_retry is False

        # Test failed stage
        failed_progress = StageProgress(
            stage=DetailedExecutionStage.PLOT_ANALYSIS,
            status=ProgressStatus.FAILED,
            attempts=1
        )

        assert failed_progress.is_complete is False
        assert failed_progress.is_failed is True
        assert failed_progress.can_retry is True

        # Test retry limit
        failed_progress.attempts = 3
        assert failed_progress.can_retry is False

    def test_response_properties(self):
        """Test TenStageProgressResponse properties."""
        stage_progresses = {
            DetailedExecutionStage.DATA_COLLECTION: StageProgress(
                stage=DetailedExecutionStage.DATA_COLLECTION,
                status=ProgressStatus.COMPLETED
            ),
            DetailedExecutionStage.PLOT_ANALYSIS: StageProgress(
                stage=DetailedExecutionStage.PLOT_ANALYSIS,
                status=ProgressStatus.FAILED
            ),
            DetailedExecutionStage.LOGIC_VERIFICATION: StageProgress(
                stage=DetailedExecutionStage.LOGIC_VERIFICATION,
                status=ProgressStatus.NOT_STARTED
            )
        }

        response = TenStageProgressResponse(
            success=True,
            episode_number=1,
            overall_progress=0.33,
            current_stage=DetailedExecutionStage.LOGIC_VERIFICATION,
            stage_progresses=stage_progresses
        )

        assert response.is_complete is False
        assert response.has_failures is True
        assert DetailedExecutionStage.DATA_COLLECTION in response.completed_stages
        assert DetailedExecutionStage.PLOT_ANALYSIS in response.failed_stages
        assert response.get_next_stage() == DetailedExecutionStage.LOGIC_VERIFICATION