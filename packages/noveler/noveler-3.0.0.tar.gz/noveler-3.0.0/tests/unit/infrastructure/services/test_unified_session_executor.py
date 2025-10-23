# File: tests/unit/infrastructure/services/test_unified_session_executor.py
# Purpose: Unit tests for UnifiedSessionExecutor with 10-stage support
# Context: Phase 2-C testing - validates unified execution for both 5 and 10 stages

"""Unit tests for UnifiedSessionExecutor."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from noveler.application.services.a30_compatibility_adapter import (
    A30CompatibilityAdapter,
    CompatibilityMode,
)
from noveler.application.use_cases.ten_stage_progress_use_case import (
    TenStageProgressUseCase,
)
from noveler.domain.value_objects.detailed_execution_stage import DetailedExecutionStage
from noveler.domain.value_objects.five_stage_writing_execution import (
    ExecutionStage,
    FiveStageWritingRequest,
)
from noveler.infrastructure.services.unified_session_executor import (
    SessionState,
    TurnAllocation,
    UnifiedSessionExecutor,
    UnifiedSessionResponse,
)


@pytest.fixture
def writing_request():
    """Create a sample writing request."""
    return FiveStageWritingRequest(
        episode_number=1,
        project_root=Path("/test/project"),
        genre="fantasy",
        viewpoint="三人称単元視点",
        viewpoint_character="主人公",
        word_count_target=3500,
    )


@pytest.fixture
def mock_claude_service():
    """Create a mock Claude service."""
    service = MagicMock()
    service.execute_with_turn_limit = AsyncMock(
        return_value={
            "output": "Test output content",
            "turns_used": 2,
            "success": True,
        }
    )
    return service


@pytest.fixture
def mock_validation_service():
    """Create a mock validation service."""
    service = MagicMock()
    service.validate = MagicMock(
        return_value=MagicMock(cleaned_content="Cleaned output content")
    )
    return service


@pytest.fixture
def compatibility_adapter():
    """Create a compatibility adapter."""
    return A30CompatibilityAdapter(CompatibilityMode.A30_DETAILED_TEN_STAGE)


@pytest.fixture
def progress_use_case():
    """Create a progress use case."""
    return TenStageProgressUseCase()


@pytest.fixture
def unified_executor(
    mock_claude_service,
    mock_validation_service,
    compatibility_adapter,
    progress_use_case,
):
    """Create UnifiedSessionExecutor instance."""
    return UnifiedSessionExecutor(
        claude_service=mock_claude_service,
        validation_service=mock_validation_service,
        compatibility_adapter=compatibility_adapter,
        progress_use_case=progress_use_case,
    )


class TestUnifiedSessionExecutor:
    """Test suite for UnifiedSessionExecutor."""

    def test_initialization(self, unified_executor):
        """Test executor initialization."""
        assert unified_executor.claude_service is not None
        assert unified_executor.validation_service is not None
        assert unified_executor.compatibility_adapter is not None
        assert unified_executor.progress_use_case is not None
        assert len(unified_executor.default_allocations_5stage) == 5
        assert len(unified_executor.default_allocations_10stage) == len(
            DetailedExecutionStage
        )

    def test_session_state_properties(self):
        """Test SessionState properties."""
        state = SessionState(session_id="test_001", total_turns_available=30)

        assert state.remaining_turns == 30
        assert state.can_continue() is True

        state.turns_used = 25
        assert state.remaining_turns == 5
        assert state.can_continue() is True

        state.turns_used = 30
        assert state.remaining_turns == 0
        assert state.can_continue() is False

        state.turns_used = 10
        state.error_count = 3
        assert state.can_continue() is False

    def test_turn_allocation_defaults_5stage(self, unified_executor):
        """Test default turn allocations for 5-stage."""
        allocations = unified_executor.default_allocations_5stage

        assert len(allocations) == 5
        assert ExecutionStage.DATA_COLLECTION in allocations
        assert ExecutionStage.MANUSCRIPT_WRITING in allocations

        manuscript_allocation = allocations[ExecutionStage.MANUSCRIPT_WRITING]
        assert manuscript_allocation.min_turns == 6
        assert manuscript_allocation.max_turns == 8
        assert manuscript_allocation.priority == 5

    def test_turn_allocation_defaults_10stage(self, unified_executor):
        """Test default turn allocations for 10-stage."""
        allocations = unified_executor.default_allocations_10stage

        assert len(allocations) == len(DetailedExecutionStage)

        # Check specific stage allocations
        manuscript_allocation = allocations[DetailedExecutionStage.MANUSCRIPT_WRITING]
        assert manuscript_allocation.priority == 5

        data_collection_allocation = allocations[
            DetailedExecutionStage.DATA_COLLECTION
        ]
        expected_turns = DetailedExecutionStage.DATA_COLLECTION.expected_turns
        assert data_collection_allocation.min_turns == max(1, expected_turns - 1)
        assert data_collection_allocation.max_turns == expected_turns + 1

    def test_complexity_estimation(self, unified_executor, writing_request):
        """Test complexity estimation."""
        complexity = unified_executor._estimate_complexity(writing_request)
        assert 0 <= complexity <= 1

        # Test with different episode numbers
        writing_request.episode_number = 50
        complexity_50 = unified_executor._estimate_complexity(writing_request)
        assert complexity_50 > complexity

        writing_request.episode_number = 100
        complexity_100 = unified_executor._estimate_complexity(writing_request)
        assert complexity_100 >= complexity_50

    def test_turn_allocations_calculation_5stage(
        self, unified_executor, writing_request
    ):
        """Test turn allocation calculation for 5-stage."""
        allocations = unified_executor._calculate_turn_allocations_5stage(
            writing_request
        )

        assert len(allocations) == 5
        for stage, allocation in allocations.items():
            assert isinstance(allocation, TurnAllocation)
            assert allocation.stage == stage
            assert allocation.min_turns <= allocation.max_turns

    def test_turn_allocations_calculation_10stage(
        self, unified_executor, writing_request
    ):
        """Test turn allocation calculation for 10-stage."""
        allocations = unified_executor._calculate_turn_allocations_10stage(
            writing_request
        )

        assert len(allocations) == len(DetailedExecutionStage)
        for stage, allocation in allocations.items():
            assert isinstance(allocation, TurnAllocation)
            assert allocation.stage == stage
            assert allocation.min_turns <= allocation.max_turns

    def test_content_cleaning_methods(self, unified_executor):
        """Test content cleaning methods."""
        # Test JSON metadata removal
        content_with_json = "Some text\n```json\n{\"test\": true}\n```\nMore text"
        cleaned = unified_executor._remove_json_metadata(content_with_json)
        assert "```json" not in cleaned
        assert "More text" in cleaned

        # Test prompt contamination removal
        content_with_prompt = "## 指示\n以下の指示に従って\nActual content"
        cleaned = unified_executor._remove_prompt_contamination(content_with_prompt)
        assert "## 指示" not in cleaned
        assert "Actual content" in cleaned

        # Test system message removal
        content_with_system = "[System] Message\nDEBUG: info\nActual content"
        cleaned = unified_executor._remove_system_messages(content_with_system)
        assert "[System]" not in cleaned
        assert "DEBUG:" not in cleaned
        assert "Actual content" in cleaned

        # Test manuscript extraction
        content_with_title = "Preamble\n第001話 タイトル\n本文内容"
        extracted = unified_executor._extract_manuscript_text(content_with_title)
        assert extracted.startswith("第001話")
        assert "Preamble" not in extracted

        # Test whitespace normalization
        content_with_spaces = "Line1\n\n\n\nLine2\n\n\nLine3"
        normalized = unified_executor._normalize_whitespace(content_with_spaces)
        assert "\n\n\n" not in normalized

    def test_execution_mode_determination(self, unified_executor, writing_request):
        """Test execution mode determination."""
        # Default should be based on adapter configuration
        use_ten_stage = unified_executor._determine_execution_mode(writing_request)
        assert use_ten_stage is True  # A30_DETAILED_TEN_STAGE has 0.8 coverage

        # Test with legacy mode adapter
        unified_executor.compatibility_adapter = A30CompatibilityAdapter(
            CompatibilityMode.LEGACY_FIVE_STAGE
        )
        use_ten_stage = unified_executor._determine_execution_mode(writing_request)
        assert use_ten_stage is False  # LEGACY has 0.3 coverage

        # Test with explicit request setting
        writing_request.use_ten_stage = True
        use_ten_stage = unified_executor._determine_execution_mode(writing_request)
        assert use_ten_stage is True

        # Test without adapter
        unified_executor.compatibility_adapter = None
        delattr(writing_request, "use_ten_stage")
        use_ten_stage = unified_executor._determine_execution_mode(writing_request)
        assert use_ten_stage is False  # Default to 5-stage

    @pytest.mark.asyncio
    async def test_validate_and_clean_output(self, unified_executor):
        """Test output validation and cleaning."""
        content = "[System] Debug\n## 指示\n第001話 テスト\n本文"
        stage = ExecutionStage.MANUSCRIPT_WRITING

        cleaned = await unified_executor._validate_and_clean_output(content, stage)

        assert "[System]" not in cleaned
        assert "## 指示" not in cleaned
        assert "Cleaned output content" in cleaned  # From mock validation service

    @pytest.mark.asyncio
    async def test_execute_five_stage_session(self, unified_executor, writing_request):
        """Test 5-stage session execution."""
        # Force 5-stage mode
        unified_executor.compatibility_adapter = A30CompatibilityAdapter(
            CompatibilityMode.LEGACY_FIVE_STAGE
        )

        response = await unified_executor.execute_unified_session(writing_request)

        assert isinstance(response, UnifiedSessionResponse)
        assert response.status == "completed"
        assert response.use_ten_stage is False
        assert len(response.stage_outputs) > 0
        assert response.turns_used > 0
        assert response.metadata["execution_mode"] == "5-stage"

        # Verify that the mock was called
        assert unified_executor.claude_service.execute_with_turn_limit.called
        # At least some stages should have been executed
        call_count = unified_executor.claude_service.execute_with_turn_limit.call_count
        assert call_count > 0

    @pytest.mark.asyncio
    async def test_execute_ten_stage_session(self, unified_executor, writing_request):
        """Test 10-stage session execution."""
        # Ensure 10-stage mode (adapter already set to A30_DETAILED_TEN_STAGE)
        response = await unified_executor.execute_unified_session(writing_request)

        assert isinstance(response, UnifiedSessionResponse)
        assert response.status in ["completed", "failed"]  # May fail due to turn limit
        assert response.use_ten_stage is True
        assert response.turns_used > 0
        assert response.metadata["execution_mode"] == "10-stage"
        assert response.metadata["total_detailed_stages"] == len(
            DetailedExecutionStage
        )

    @pytest.mark.asyncio
    async def test_session_error_handling(self, unified_executor, writing_request):
        """Test error handling during session execution."""
        # Make claude service fail after a few stages
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                return {"output": "Success", "turns_used": 2, "success": True}
            else:
                return {"output": "", "turns_used": 1, "success": False}

        unified_executor.claude_service.execute_with_turn_limit.side_effect = (
            side_effect
        )

        response = await unified_executor.execute_unified_session(writing_request)

        # Should continue until error limit reached
        assert response.turns_used > 0

    @pytest.mark.asyncio
    async def test_progress_tracking_integration(
        self, unified_executor, writing_request
    ):
        """Test progress tracking during 10-stage execution."""
        with patch.object(
            unified_executor.progress_use_case, "execute"
        ) as mock_execute:
            mock_execute.return_value = AsyncMock(return_value=MagicMock(success=True))

            response = await unified_executor.execute_unified_session(writing_request)

            assert response.use_ten_stage is True
            # Should have called progress tracking
            assert mock_execute.called
            # At least one call for "start" operation
            start_calls = [
                call
                for call in mock_execute.call_args_list
                if call[0][0].operation == "start"
            ]
            assert len(start_calls) >= 1

    def test_convert_to_legacy_format(self, unified_executor):
        """Test conversion from 10-stage to 5-stage format."""
        detailed_outputs = {
            DetailedExecutionStage.DATA_COLLECTION: "Data output",
            DetailedExecutionStage.PLOT_ANALYSIS: "Plot output",
            DetailedExecutionStage.CHARACTER_CONSISTENCY: "Character output",
        }

        legacy_outputs = unified_executor._convert_to_legacy_format(detailed_outputs)

        assert len(legacy_outputs) > 0
        assert ExecutionStage.DATA_COLLECTION in legacy_outputs
        assert ExecutionStage.PLOT_ANALYSIS in legacy_outputs

    def test_response_to_dict(self):
        """Test UnifiedSessionResponse to_dict conversion."""
        response = UnifiedSessionResponse(
            session_id="test_001",
            status="completed",
            stage_outputs={
                ExecutionStage.DATA_COLLECTION: "Output 1",
                ExecutionStage.PLOT_ANALYSIS: "Output 2",
            },
            turns_used=10,
            metadata={"test": "value"},
            use_ten_stage=False,
        )

        result_dict = response.to_dict()

        assert result_dict["session_id"] == "test_001"
        assert result_dict["status"] == "completed"
        assert result_dict["turns_used"] == 10
        assert result_dict["use_ten_stage"] is False
        assert "data_collection" in result_dict["stage_outputs"]  # Enum value, not name

    @pytest.mark.asyncio
    async def test_session_state_management(self, unified_executor, writing_request):
        """Test session state is properly managed."""
        # Mock to track state changes
        states_captured = []

        async def capture_state(*args, **kwargs):
            # Capture current state from context parameter if present
            if "context" in kwargs:
                states_captured.append(kwargs["context"])
            return {"output": "Test", "turns_used": 1, "success": True}

        unified_executor.claude_service.execute_with_turn_limit.side_effect = (
            capture_state
        )
        unified_executor.compatibility_adapter = A30CompatibilityAdapter(
            CompatibilityMode.LEGACY_FIVE_STAGE
        )

        await unified_executor.execute_unified_session(writing_request)

        # Context should accumulate across stages
        assert len(states_captured) > 1
        # Later contexts should contain earlier content
        if len(states_captured) > 2:
            # Context grows with each stage
            assert len(states_captured[-1]) >= len(states_captured[0])

    def test_get_stage_allocations(self, unified_executor, writing_request):
        """Test getting stage allocations for a request."""
        # Test 10-stage allocations
        allocations = unified_executor.get_stage_allocations(writing_request)
        assert len(allocations) == len(DetailedExecutionStage)

        # Test 5-stage allocations
        unified_executor.compatibility_adapter = A30CompatibilityAdapter(
            CompatibilityMode.LEGACY_FIVE_STAGE
        )
        allocations = unified_executor.get_stage_allocations(writing_request)
        assert len(allocations) == 5

    @pytest.mark.asyncio
    async def test_turn_limit_enforcement(self, unified_executor, writing_request):
        """Test that turn limits are properly enforced."""
        # Set up to use many turns per stage
        async def high_turn_usage(*args, **kwargs):
            return {"output": "Test", "turns_used": 10, "success": True}

        unified_executor.claude_service.execute_with_turn_limit.side_effect = (
            high_turn_usage
        )

        response = await unified_executor.execute_unified_session(writing_request)

        # Should stop when turns are exhausted
        assert response.turns_used <= 30  # Default session limit
        # Not all stages will complete due to turn limit
        assert len(response.stage_outputs) < len(DetailedExecutionStage)