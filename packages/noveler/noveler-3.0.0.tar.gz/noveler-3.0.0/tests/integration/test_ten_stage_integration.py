# File: tests/integration/test_ten_stage_integration.py
# Purpose: Integration tests for 10-stage system with A30CompatibilityAdapter
# Context: Phase 2-A validation - ensures all components work together

"""Integration tests for 10-stage writing system components."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from noveler.application.services.a30_compatibility_adapter import (
    A30CompatibilityAdapter,
    CompatibilityMode,
)
from noveler.application.services.ten_stage_orchestration_service import (
    OrchestrationConfig,
    TenStageOrchestrationService,
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


@pytest.fixture
def project_root(tmp_path):
    """Create a temporary project root for testing."""
    project = tmp_path / "test_project"
    project.mkdir()
    (project / "manuscripts").mkdir()
    return project


@pytest.fixture
def writing_request(project_root):
    """Create a sample writing request."""
    return FiveStageWritingRequest(
        episode_number=1,
        project_root=project_root,
        genre="fantasy",
        viewpoint="三人称単元視点",
        viewpoint_character="主人公",
        word_count_target=3500
    )


@pytest.fixture
def orchestration_config():
    """Create orchestration configuration."""
    return OrchestrationConfig(
        enable_progress_tracking=True,
        compatibility_mode=CompatibilityMode.A30_DETAILED_TEN_STAGE,
        max_retries_per_stage=2,
        checkpoint_frequency=3
    )


class TestTenStageIntegration:
    """Integration tests for 10-stage writing system."""

    @pytest.mark.asyncio
    async def test_progress_tracking_with_compatibility_adapter(self, project_root):
        """Test that progress tracking works with compatibility adapter."""
        # Initialize components
        progress_use_case = TenStageProgressUseCase()
        adapter = A30CompatibilityAdapter(CompatibilityMode.A30_DETAILED_TEN_STAGE)

        # Start progress tracking
        start_request = TenStageProgressRequest(
            episode_number=1,
            project_root=project_root,
            operation="start"
        )
        start_response = await progress_use_case.execute(start_request)
        assert start_response.success is True

        # Simulate stage execution with adapter
        for stage in list(DetailedExecutionStage)[:3]:  # Test first 3 stages
            # Get execution plan from adapter
            execution_plan = adapter.get_execution_plan(1)
            assert "a30_detailed_ten_stage" in execution_plan["mode"]

            # Create stage-specific prompt
            context = {"episode_number": 1, "stage": stage.value}
            prompt_data = adapter.create_stage_specific_prompt(stage, context)
            assert "system" in prompt_data
            assert "user" in prompt_data

            # Simulate execution and create output
            raw_output = {f"{stage.value}_result": "test_output"}
            quality_scores = {"overall": 0.85}
            structured_output = adapter.create_compatible_output(
                stage, raw_output, quality_scores
            )

            # Update progress
            update_request = TenStageProgressRequest(
                episode_number=1,
                project_root=project_root,
                operation="update",
                stage=stage,
                stage_output=structured_output
            )
            update_response = await progress_use_case.execute(update_request)
            assert update_response.success is True

        # Query final progress
        query_request = TenStageProgressRequest(
            episode_number=1,
            project_root=project_root,
            operation="query"
        )
        query_response = await progress_use_case.execute(query_request)

        assert len(query_response.completed_stages) == 3
        assert query_response.overall_progress > 0

    @pytest.mark.asyncio
    async def test_orchestration_service_full_flow(
        self, writing_request, orchestration_config, project_root
    ):
        """Test complete orchestration flow."""
        # Initialize orchestration service
        service = TenStageOrchestrationService(config=orchestration_config)

        # Execute orchestration
        result = await service.orchestrate_episode_writing(writing_request)

        assert result.success is True
        assert result.episode_number == 1
        assert result.manuscript_path is not None
        assert result.manuscript_path.exists()
        assert result.total_turns_used > 0
        assert result.total_cost_usd > 0
        assert len(result.stage_outputs) == len(DetailedExecutionStage)

    @pytest.mark.asyncio
    async def test_stage_mapping_consistency(self):
        """Test that stage mapping between legacy and detailed is consistent."""
        adapter = A30CompatibilityAdapter(CompatibilityMode.A30_DETAILED_TEN_STAGE)

        # Test forward mapping
        for legacy_stage in ExecutionStage:
            detailed_stages = adapter.convert_legacy_to_detailed(legacy_stage)
            assert len(detailed_stages) > 0

            # Test reverse mapping
            for detailed_stage in detailed_stages:
                reverse_legacy = adapter.convert_detailed_to_legacy(detailed_stage)
                assert reverse_legacy == legacy_stage

    @pytest.mark.asyncio
    async def test_compatibility_mode_switching(self, project_root):
        """Test switching between different compatibility modes."""
        episode_number = 1

        # Test with LEGACY_FIVE_STAGE mode
        legacy_adapter = A30CompatibilityAdapter(CompatibilityMode.LEGACY_FIVE_STAGE)
        legacy_plan = legacy_adapter.get_execution_plan(episode_number)
        assert legacy_plan["total_stages"] == 5
        assert legacy_plan["a30_coverage"] == 0.30

        # Test with A30_DETAILED_TEN_STAGE mode
        detailed_adapter = A30CompatibilityAdapter(CompatibilityMode.A30_DETAILED_TEN_STAGE)
        detailed_plan = detailed_adapter.get_execution_plan(episode_number)
        assert detailed_plan["total_stages"] == len(DetailedExecutionStage)
        assert detailed_plan["a30_coverage"] == 0.80

        # Test with HYBRID_GRADUAL_MIGRATION mode
        hybrid_adapter = A30CompatibilityAdapter(CompatibilityMode.HYBRID_GRADUAL_MIGRATION)
        hybrid_plan = hybrid_adapter.get_execution_plan(episode_number)
        assert hybrid_plan["a30_coverage"] == 0.60
        assert "priority_migrations" in hybrid_plan

    @pytest.mark.asyncio
    async def test_checkpoint_and_resume(
        self, writing_request, orchestration_config, project_root
    ):
        """Test checkpoint creation and resume functionality."""
        # Configure for frequent checkpoints
        orchestration_config.checkpoint_frequency = 2
        service = TenStageOrchestrationService(config=orchestration_config)

        # Partially execute (simulate failure after 2 stages)
        with patch.object(service, '_execute_single_stage') as mock_execute:
            # Make third stage fail
            async def side_effect(stage, request, outputs):
                if stage == DetailedExecutionStage.LOGIC_VERIFICATION:
                    raise Exception("Simulated failure")
                return MagicMock()

            mock_execute.side_effect = side_effect

            # Execute and expect partial completion
            with pytest.raises(Exception):
                await service.orchestrate_episode_writing(writing_request)

        # Verify checkpoint was created
        assert 1 in service._checkpoints
        checkpoint = service._checkpoints[1]
        assert checkpoint["stages_completed"] >= 2

        # Test resume from checkpoint
        resume_result = await service.resume_from_checkpoint(1, writing_request)
        assert resume_result.success is True

    @pytest.mark.asyncio
    async def test_progress_export_report(self, project_root):
        """Test progress report export functionality."""
        progress_use_case = TenStageProgressUseCase()

        # Initialize and complete some stages
        await progress_use_case.execute(TenStageProgressRequest(
            episode_number=1,
            project_root=project_root,
            operation="start"
        ))

        # Complete a few stages
        for stage in list(DetailedExecutionStage)[:3]:
            await progress_use_case.execute(TenStageProgressRequest(
                episode_number=1,
                project_root=project_root,
                operation="update",
                stage=stage,
                stage_output=MagicMock()
            ))

        # Export report
        report = progress_use_case.export_progress_report(1)

        assert report["episode"] == 1
        assert report["overall_progress"] > 0
        assert len(report["stages"]["completed"]) == 3
        assert report["status"] == "in_progress"
        assert "metrics" in report
        assert "generated_at" in report

    @pytest.mark.asyncio
    async def test_error_recovery_flow(self, writing_request, orchestration_config):
        """Test error recovery and retry logic."""
        service = TenStageOrchestrationService(config=orchestration_config)
        progress_use_case = service.progress_use_case

        # Start tracking
        await progress_use_case.execute(TenStageProgressRequest(
            episode_number=1,
            project_root=writing_request.project_root,
            operation="start"
        ))

        # Simulate stage failure
        stage = DetailedExecutionStage.PLOT_ANALYSIS
        for attempt in range(3):
            await progress_use_case.execute(TenStageProgressRequest(
                episode_number=1,
                project_root=writing_request.project_root,
                operation="update",
                stage=stage,
                error_message=f"Attempt {attempt + 1} failed"
            ))

            # Check if retry is possible
            can_retry = await service._should_retry_stage(1, stage)
            if attempt < 2:
                assert can_retry is True
            else:
                assert can_retry is False

    @pytest.mark.asyncio
    async def test_migration_recommendations(self):
        """Test migration recommendation system."""
        # Test recommendations for each mode
        modes = [
            CompatibilityMode.LEGACY_FIVE_STAGE,
            CompatibilityMode.HYBRID_GRADUAL_MIGRATION,
            CompatibilityMode.A30_DETAILED_TEN_STAGE
        ]

        for mode in modes:
            adapter = A30CompatibilityAdapter(mode)
            recommendations = adapter.get_migration_recommendations()

            assert "current_mode" in recommendations
            assert recommendations["current_mode"] == mode.value
            assert "recommended_next_step" in recommendations
            assert "expected_benefits" in recommendations
            assert "implementation_effort" in recommendations

    @pytest.mark.asyncio
    async def test_quality_metrics_tracking(self, project_root):
        """Test quality metrics tracking across stages."""
        adapter = A30CompatibilityAdapter(CompatibilityMode.A30_DETAILED_TEN_STAGE)
        progress_use_case = TenStageProgressUseCase()

        # Start tracking
        await progress_use_case.execute(TenStageProgressRequest(
            episode_number=1,
            project_root=project_root,
            operation="start"
        ))

        quality_scores_by_stage = {}

        # Execute each stage and track quality
        for stage in list(DetailedExecutionStage)[:5]:
            raw_output = {f"{stage.value}_data": "test"}
            quality_scores = {
                "overall": 0.8 + (0.02 * list(DetailedExecutionStage).index(stage)),
                "completeness": 0.9,
                "consistency": 0.85
            }

            quality_scores_by_stage[stage] = quality_scores

            output = adapter.create_compatible_output(stage, raw_output, quality_scores)

            # Verify quality metrics are properly stored
            assert output.quality_metrics.overall_score == quality_scores["overall"]
            assert output.quality_metrics.specific_metrics == quality_scores

            # Update progress
            await progress_use_case.execute(TenStageProgressRequest(
                episode_number=1,
                project_root=project_root,
                operation="update",
                stage=stage,
                stage_output=output
            ))

        # Verify quality tracking in progress
        query_response = await progress_use_case.execute(TenStageProgressRequest(
            episode_number=1,
            project_root=project_root,
            operation="query"
        ))

        for stage in list(DetailedExecutionStage)[:5]:
            progress = query_response.stage_progresses[stage]
            if progress.last_output:
                assert progress.last_output.quality_metrics.overall_score > 0

    @pytest.mark.asyncio
    async def test_parallel_stage_execution_disabled(self, orchestration_config):
        """Test that parallel execution can be disabled."""
        orchestration_config.enable_parallel_stages = False
        service = TenStageOrchestrationService(config=orchestration_config)

        # Verify configuration
        assert service.config.enable_parallel_stages is False

        # In production, this would ensure sequential execution
        # For now, just verify the configuration is respected
        assert hasattr(service, 'config')
        assert service.config.enable_parallel_stages is False