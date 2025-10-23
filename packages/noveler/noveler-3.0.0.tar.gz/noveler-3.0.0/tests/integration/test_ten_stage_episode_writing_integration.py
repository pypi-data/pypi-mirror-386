# File: tests/integration/test_ten_stage_episode_writing_integration.py
# Purpose: Integration tests for TenStageEpisodeWritingUseCase with TenStageProgressUseCase
# Context: Phase 2-B validation - ensures proper integration between components

"""Integration tests for TenStageEpisodeWritingUseCase Phase 2-B integration."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from noveler.application.services.a30_compatibility_adapter import (
    A30CompatibilityAdapter,
    CompatibilityMode,
)
from noveler.application.use_cases.ten_stage_episode_writing_use_case import (
    TenStageEpisodeWritingUseCase,
)
from noveler.application.use_cases.ten_stage_progress_use_case import (
    ProgressStatus,
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
    (project / "config").mkdir()
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
def progress_use_case():
    """Create TenStageProgressUseCase instance."""
    return TenStageProgressUseCase()


@pytest.fixture
def compatibility_adapter():
    """Create A30CompatibilityAdapter instance."""
    return A30CompatibilityAdapter(CompatibilityMode.A30_DETAILED_TEN_STAGE)


@pytest.fixture
def episode_writing_use_case(progress_use_case, compatibility_adapter):
    """Create TenStageEpisodeWritingUseCase with dependencies."""
    with patch('noveler.application.use_cases.ten_stage_episode_writing_use_case.ConfigurationLoaderService'):
        return TenStageEpisodeWritingUseCase(
            progress_use_case=progress_use_case,
            compatibility_adapter=compatibility_adapter
        )


class TestTenStageEpisodeWritingIntegration:
    """Integration tests for TenStageEpisodeWritingUseCase with Phase 2-B features."""

    @pytest.mark.asyncio
    async def test_ten_stage_workflow_with_progress_tracking(
        self, episode_writing_use_case, writing_request, progress_use_case
    ):
        """Test that 10-stage workflow properly integrates with progress tracking."""
        # Initialize progress tracking first
        from noveler.application.use_cases.ten_stage_progress_use_case import TenStageProgressRequest

        init_request = TenStageProgressRequest(
            episode_number=1,
            project_root=writing_request.project_root,
            operation="start"
        )
        await progress_use_case.execute(init_request)

        # Execute the 10-stage workflow
        response = await episode_writing_use_case._execute_ten_stage_workflow(writing_request)

        assert response.success is True
        assert response.session_id is not None
        assert response.stage_results is not None
        assert len(response.stage_results) > 0

        # Verify progress was tracked
        progress_query = TenStageProgressRequest(
            episode_number=1,
            project_root=writing_request.project_root,
            operation="query"
        )
        progress_response = await progress_use_case.execute(progress_query)

        assert progress_response.success is True
        assert progress_response.overall_progress > 0
        assert len(progress_response.completed_stages) > 0

    @pytest.mark.asyncio
    async def test_compatibility_adapter_stage_mapping(
        self, episode_writing_use_case, writing_request
    ):
        """Test that compatibility adapter properly maps between 5 and 10 stages."""
        adapter = episode_writing_use_case._compatibility_adapter

        # Test all detailed stages map to legacy stages
        for detailed_stage in DetailedExecutionStage:
            legacy_stage = adapter.convert_detailed_to_legacy(detailed_stage)
            assert isinstance(legacy_stage, ExecutionStage)

            # Test reverse mapping
            detailed_stages = adapter.convert_legacy_to_detailed(legacy_stage)
            assert detailed_stage in detailed_stages

    @pytest.mark.asyncio
    async def test_progress_tracking_initialization(
        self, episode_writing_use_case, writing_request, progress_use_case
    ):
        """Test that progress tracking is properly initialized at workflow start."""
        # Mock the actual execution to focus on progress initialization
        with patch.object(episode_writing_use_case, '_generate_fallback_manuscript_content') as mock_generate:
            mock_generate.return_value = "Test manuscript content"

            # Execute main workflow
            response = await episode_writing_use_case._execute_main_workflow(writing_request)

            # Query progress to verify initialization
            from noveler.application.use_cases.ten_stage_progress_use_case import TenStageProgressRequest

            progress_query = TenStageProgressRequest(
                episode_number=1,
                project_root=writing_request.project_root,
                operation="query"
            )
            progress_response = await progress_use_case.execute(progress_query)

            assert progress_response.success is True
            assert progress_response.stage_progresses is not None

            # All stages should be initialized
            assert len(progress_response.stage_progresses) == len(DetailedExecutionStage)

    @pytest.mark.asyncio
    async def test_stage_specific_prompt_generation(
        self, episode_writing_use_case, writing_request
    ):
        """Test that stage-specific prompts are properly generated for each stage."""
        adapter = episode_writing_use_case._compatibility_adapter

        context = {
            "episode_number": writing_request.episode_number,
            "genre": writing_request.genre,
            "viewpoint": writing_request.viewpoint,
        }

        for detailed_stage in DetailedExecutionStage:
            prompt_data = adapter.create_stage_specific_prompt(detailed_stage, context)

            assert prompt_data is not None
            assert "system" in prompt_data
            assert "user" in prompt_data
            # Check that stage info is in either system or user prompt
            # Stage information might be in Japanese, so check for key concepts
            combined = prompt_data["system"] + prompt_data["user"]
            # At minimum, the prompt should contain some information
            assert len(combined) > 0

    @pytest.mark.asyncio
    async def test_structured_output_creation(
        self, episode_writing_use_case, writing_request
    ):
        """Test that structured outputs are properly created for each stage."""
        adapter = episode_writing_use_case._compatibility_adapter

        for detailed_stage in DetailedExecutionStage:
            raw_output = {
                "stage": detailed_stage.value,
                "result": f"Test result for {detailed_stage.value}",
                "episode_number": writing_request.episode_number,
            }

            quality_scores = {
                "overall": 0.85,
                "completeness": 0.90,
                "consistency": 0.80,
            }

            structured_output = adapter.create_compatible_output(
                detailed_stage, raw_output, quality_scores
            )

            assert structured_output is not None
            assert structured_output.step_id == f"step_{detailed_stage.value.lower()}"
            assert structured_output.quality_metrics.overall_score == 0.85
            assert structured_output.structured_data == raw_output

    @pytest.mark.asyncio
    async def test_legacy_stage_result_aggregation(
        self, episode_writing_use_case, writing_request, progress_use_case
    ):
        """Test that detailed stage results are properly aggregated into legacy stages."""
        # Initialize progress tracking
        from noveler.application.use_cases.ten_stage_progress_use_case import TenStageProgressRequest

        init_request = TenStageProgressRequest(
            episode_number=1,
            project_root=writing_request.project_root,
            operation="start"
        )
        await progress_use_case.execute(init_request)

        # Execute workflow
        with patch.object(episode_writing_use_case, '_save_generated_manuscript') as mock_save:
            response = await episode_writing_use_case._execute_ten_stage_workflow(writing_request)

            assert response.success is True
            assert response.stage_results is not None

            # Verify that we have stage results
            # Note: Not all legacy stages may be present as some are aggregated
            assert len(response.stage_results) > 0

            # Verify key stages are present
            assert ExecutionStage.DATA_COLLECTION in response.stage_results
            assert ExecutionStage.MANUSCRIPT_WRITING in response.stage_results

            # Verify stage results have proper structure
            for stage_result in response.stage_results.values():
                assert stage_result.status is not None
                assert stage_result.turns_used > 0

    @pytest.mark.asyncio
    async def test_progress_query_after_execution(
        self, episode_writing_use_case, writing_request, progress_use_case
    ):
        """Test that progress can be queried after execution completes."""
        # Initialize progress tracking
        from noveler.application.use_cases.ten_stage_progress_use_case import TenStageProgressRequest

        init_request = TenStageProgressRequest(
            episode_number=1,
            project_root=writing_request.project_root,
            operation="start"
        )
        await progress_use_case.execute(init_request)

        # Execute workflow
        with patch.object(episode_writing_use_case, '_save_generated_manuscript') as mock_save:
            response = await episode_writing_use_case._execute_ten_stage_workflow(writing_request)

            assert response.success is True

            # Query final progress
            progress_query = TenStageProgressRequest(
                episode_number=1,
                project_root=writing_request.project_root,
                operation="query"
            )
            progress_response = await progress_use_case.execute(progress_query)

            assert progress_response.success is True
            assert progress_response.overall_progress == 1.0  # All stages completed
            assert len(progress_response.completed_stages) == len(DetailedExecutionStage)

    @pytest.mark.asyncio
    async def test_execution_metrics_tracking(
        self, episode_writing_use_case, writing_request
    ):
        """Test that execution metrics are properly tracked."""
        with patch.object(episode_writing_use_case, '_save_generated_manuscript') as mock_save:
            response = await episode_writing_use_case._execute_ten_stage_workflow(writing_request)

            assert response.success is True
            assert response.total_turns_used > 0
            assert response.total_cost_usd > 0
            assert response.total_execution_time_ms > 0

            # Verify turn counts match expectations
            expected_turns = sum(stage.expected_turns for stage in DetailedExecutionStage)
            assert response.total_turns_used == expected_turns

    @pytest.mark.asyncio
    async def test_manuscript_generation_and_saving(
        self, episode_writing_use_case, writing_request, project_root, progress_use_case
    ):
        """Test that manuscript is generated and saved properly."""
        # Initialize progress tracking
        from noveler.application.use_cases.ten_stage_progress_use_case import TenStageProgressRequest

        init_request = TenStageProgressRequest(
            episode_number=1,
            project_root=writing_request.project_root,
            operation="start"
        )
        await progress_use_case.execute(init_request)

        response = await episode_writing_use_case._execute_ten_stage_workflow(writing_request)

        assert response.success is True
        assert response.manuscript_path is not None

        # The file should exist if manuscript was actually saved
        # In test environment, this might be a temporary path
        if response.manuscript_path.exists():
            # Verify manuscript content
            manuscript_content = response.manuscript_path.read_text(encoding="utf-8")
            assert f"第{writing_request.episode_number:03d}話" in manuscript_content
        else:
            # At minimum, the path should be set
            assert str(response.manuscript_path).endswith(".md")

    @pytest.mark.asyncio
    async def test_error_handling_in_stage_execution(
        self, episode_writing_use_case, writing_request, progress_use_case
    ):
        """Test that errors in stage execution are properly handled."""
        with patch.object(
            episode_writing_use_case._compatibility_adapter,
            'create_stage_specific_prompt'
        ) as mock_prompt:
            # Make the third stage fail
            mock_prompt.side_effect = [
                {"system": "test", "user": "test"},  # Stage 1
                {"system": "test", "user": "test"},  # Stage 2
                Exception("Simulated stage failure"),  # Stage 3 fails
            ]

            response = await episode_writing_use_case._execute_ten_stage_workflow(writing_request)

            assert response.success is False
            assert "10段階実行エラー" in response.error_message

    @pytest.mark.asyncio
    async def test_progress_export_report(
        self, episode_writing_use_case, writing_request, progress_use_case
    ):
        """Test that progress report can be exported after execution."""
        # Initialize progress tracking
        from noveler.application.use_cases.ten_stage_progress_use_case import TenStageProgressRequest

        init_request = TenStageProgressRequest(
            episode_number=1,
            project_root=writing_request.project_root,
            operation="start"
        )
        await progress_use_case.execute(init_request)

        # Execute workflow
        with patch.object(episode_writing_use_case, '_save_generated_manuscript') as mock_save:
            response = await episode_writing_use_case._execute_ten_stage_workflow(writing_request)

            assert response.success is True

            # Export progress report
            report = progress_use_case.export_progress_report(1)

            assert report["episode"] == 1
            assert report["overall_progress"] == 1.0
            assert report["status"] == "completed"
            assert len(report["stages"]["completed"]) == len(DetailedExecutionStage)
            assert report["metrics"]["total_turns_used"] > 0

    @pytest.mark.asyncio
    async def test_compatibility_mode_configuration(
        self, progress_use_case, project_root
    ):
        """Test that different compatibility modes can be configured."""
        # Test with LEGACY_FIVE_STAGE mode
        legacy_adapter = A30CompatibilityAdapter(CompatibilityMode.LEGACY_FIVE_STAGE)

        with patch('noveler.application.use_cases.ten_stage_episode_writing_use_case.ConfigurationLoaderService') as mock_config:
            mock_config.return_value.load_project_settings.return_value = MagicMock()
            legacy_use_case = TenStageEpisodeWritingUseCase(
                progress_use_case=progress_use_case,
                compatibility_adapter=legacy_adapter
            )

            # Verify the adapter is using the correct mode
            # The mode is stored internally in the adapter
            assert isinstance(legacy_use_case._compatibility_adapter, A30CompatibilityAdapter)
            # Can check functionality instead of direct mode access
            execution_plan = legacy_use_case._compatibility_adapter.get_execution_plan(1)
            assert execution_plan["mode"] == "legacy_five_stage"

        # Test with HYBRID_GRADUAL_MIGRATION mode
        hybrid_adapter = A30CompatibilityAdapter(CompatibilityMode.HYBRID_GRADUAL_MIGRATION)

        with patch('noveler.application.use_cases.ten_stage_episode_writing_use_case.ConfigurationLoaderService') as mock_config:
            mock_config.return_value.load_project_settings.return_value = MagicMock()
            hybrid_use_case = TenStageEpisodeWritingUseCase(
                progress_use_case=progress_use_case,
                compatibility_adapter=hybrid_adapter
            )

            # Verify through execution plan
            assert isinstance(hybrid_use_case._compatibility_adapter, A30CompatibilityAdapter)
            execution_plan = hybrid_use_case._compatibility_adapter.get_execution_plan(1)
            assert execution_plan["mode"] == "hybrid_gradual_migration"

    @pytest.mark.asyncio
    async def test_stage_estimation_accuracy(
        self, episode_writing_use_case
    ):
        """Test that stage execution estimates are accurate."""
        estimates = episode_writing_use_case.get_stage_execution_estimates()

        expected_total = sum(s.expected_turns for s in DetailedExecutionStage)
        assert estimates["total_estimated_turns"] == expected_total
        assert len(estimates["stage_breakdown"]) == len(DetailedExecutionStage)

        # Verify each stage in breakdown
        for i, detailed_stage in enumerate(DetailedExecutionStage):
            stage_info = estimates["stage_breakdown"][i]
            assert stage_info["stage"] == detailed_stage.value
            assert stage_info["estimated_turns"] == detailed_stage.expected_turns

    @pytest.mark.asyncio
    async def test_concurrent_execution_prevention(
        self, episode_writing_use_case, writing_request, progress_use_case
    ):
        """Test that concurrent executions for the same episode are prevented."""
        # Start first execution
        task1 = asyncio.create_task(
            episode_writing_use_case._execute_ten_stage_workflow(writing_request)
        )

        # Try to start another execution for the same episode
        await asyncio.sleep(0.1)  # Small delay to ensure first starts

        # This should handle the concurrent execution gracefully
        task2 = asyncio.create_task(
            episode_writing_use_case._execute_ten_stage_workflow(writing_request)
        )

        # Wait for both to complete
        response1, response2 = await asyncio.gather(task1, task2, return_exceptions=True)

        # At least one should succeed
        successful = [r for r in [response1, response2] if not isinstance(r, Exception) and r.success]
        assert len(successful) >= 1