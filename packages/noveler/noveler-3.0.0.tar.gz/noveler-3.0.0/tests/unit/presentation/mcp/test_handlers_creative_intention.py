#!/usr/bin/env python3
# File: tests/unit/presentation/mcp/test_handlers_creative_intention.py
# Purpose: Test Creative Intention integration in polish_manuscript_apply handler
# Context: Validates preflight validation for noveler_write.md specification

"""Tests for Creative Intention integration in MCP handlers."""

import pytest
from unittest.mock import Mock, patch

from noveler.domain.value_objects.creative_intention import (
    CharacterArc,
    CreativeIntention,
)
from noveler.presentation.mcp.adapters import handlers


class TestPolishManuscriptApplyWithCreativeIntention:
    """Test polish_manuscript_apply with Creative Intention preflight validation."""

    @pytest.fixture
    def valid_creative_intention_dict(self):
        """Return a valid Creative Intention as dict."""
        return {
            "scene_goal": "主人公の弱点を冒頭で明示し共感獲得",
            "emotional_goal": "絶望→驚き→期待",
            "character_arc": {
                "before_state": "いじめられている被害者",
                "transition": "Brain Burstの授与",
                "after_state": "加速世界への転移",
            },
            "world_via_action": "時間停止を体験シーンで提示",
            "voice_constraints": "「AはBである」形式禁止",
            "episode_number": 1,
        }

    @pytest.fixture
    def invalid_creative_intention_dict(self):
        """Return an invalid Creative Intention (too short fields)."""
        return {
            "scene_goal": "短い",  # Too short
            "emotional_goal": "短",  # Too short
            "character_arc": {
                "before_state": "短",  # Too short
                "transition": "短",  # Too short
                "after_state": "短",  # Too short
            },
            "world_via_action": "短い",  # Too short
            "voice_constraints": "短",  # Too short
        }

    @pytest.fixture
    def mock_polish_tool_response(self):
        """Return a mock PolishManuscriptApplyTool response."""
        mock_response = Mock()
        mock_response.success = True
        mock_response.score = 85.0
        mock_response.issues = []
        mock_response.execution_time_ms = 1000
        mock_response.metadata = {"polish_stage": "stage2"}
        return mock_response

    @pytest.mark.asyncio
    async def test_polish_with_valid_creative_intention(
        self, valid_creative_intention_dict, mock_polish_tool_response
    ):
        """Test polish_manuscript_apply with valid Creative Intention."""
        arguments = {
            "episode_number": 1,
            "project_name": "test_project",
            "creative_intention": valid_creative_intention_dict,
        }

        # Mock tool execution
        with patch.object(
            handlers, "_get_tool_class_with_fallback"
        ) as mock_get_tool:
            mock_tool = Mock()
            mock_tool.execute.return_value = mock_polish_tool_response
            mock_get_tool.return_value = lambda: mock_tool

            result = await handlers.polish_manuscript_apply(arguments)

        # Assertions
        assert result["success"] is True
        assert result["score"] == 85.0
        assert result["metadata"]["creative_intention_validated"] is True
        assert result["metadata"]["creative_intention_episode"] == 1
        assert mock_tool.execute.called

    @pytest.mark.asyncio
    async def test_polish_with_invalid_creative_intention(
        self, invalid_creative_intention_dict
    ):
        """Test polish_manuscript_apply rejects invalid Creative Intention."""
        arguments = {
            "episode_number": 1,
            "project_name": "test_project",
            "creative_intention": invalid_creative_intention_dict,
        }

        # No need to mock tool - validation should fail before tool is accessed
        result = await handlers.polish_manuscript_apply(arguments)

        # Assertions - validation should fail before tool execution
        assert result["success"] is False
        assert result["error_type"] == "CreativeIntentionDeserializationError"
        assert "validation_issues" in result
        assert len(result["validation_issues"]) > 0
        assert result["metadata"]["error_count"] > 0

    @pytest.mark.asyncio
    async def test_polish_without_creative_intention_backward_compatible(
        self, mock_polish_tool_response
    ):
        """Test polish_manuscript_apply without Creative Intention (backward compatible)."""
        arguments = {
            "episode_number": 1,
            "project_name": "test_project",
            # No creative_intention provided
        }

        # Mock tool execution
        with patch.object(
            handlers, "_get_tool_class_with_fallback"
        ) as mock_get_tool:
            mock_tool = Mock()
            mock_tool.execute.return_value = mock_polish_tool_response
            mock_get_tool.return_value = lambda: mock_tool

            result = await handlers.polish_manuscript_apply(arguments)

        # Assertions - should proceed normally
        assert result["success"] is True
        assert result["score"] == 85.0
        assert "creative_intention_validated" not in result["metadata"]
        assert mock_tool.execute.called

    @pytest.mark.asyncio
    async def test_polish_with_pre_instantiated_creative_intention(
        self, mock_polish_tool_response
    ):
        """Test polish_manuscript_apply with pre-instantiated CreativeIntention object."""
        arc = CharacterArc(
            before_state="いじめられている被害者",
            transition="Brain Burstの授与",
            after_state="加速世界への転移",
        )
        intention = CreativeIntention(
            scene_goal="主人公の弱点を冒頭で明示し共感獲得",
            emotional_goal="絶望→驚き→期待",
            character_arc=arc,
            world_via_action="時間停止を体験シーンで提示",
            voice_constraints="「AはBである」形式禁止",
            episode_number=1,
        )

        arguments = {
            "episode_number": 1,
            "project_name": "test_project",
            "creative_intention": intention,  # Pre-instantiated object
        }

        # Mock tool execution
        with patch.object(
            handlers, "_get_tool_class_with_fallback"
        ) as mock_get_tool:
            mock_tool = Mock()
            mock_tool.execute.return_value = mock_polish_tool_response
            mock_get_tool.return_value = lambda: mock_tool

            result = await handlers.polish_manuscript_apply(arguments)

        # Assertions
        assert result["success"] is True
        assert result["metadata"]["creative_intention_validated"] is True
        assert mock_tool.execute.called


class TestCreativeIntentionHelpers:
    """Test Creative Intention extraction and validation helpers."""

    def test_extract_creative_intention_from_dict(self):
        """Test _extract_creative_intention with dict input."""
        arguments = {
            "creative_intention": {
                "scene_goal": "主人公の弱点を冒頭で明示し共感獲得",
                "emotional_goal": "絶望→驚き→期待",
                "character_arc": {
                    "before_state": "いじめられている被害者",
                    "transition": "Brain Burstの授与",
                    "after_state": "加速世界への転移",
                },
                "world_via_action": "時間停止を体験シーンで提示",
                "voice_constraints": "「AはBである」形式禁止",
            }
        }

        intention, error = handlers._extract_creative_intention(arguments)

        assert intention is not None
        assert error is None
        assert isinstance(intention, CreativeIntention)
        assert intention.scene_goal == "主人公の弱点を冒頭で明示し共感獲得"

    def test_extract_creative_intention_returns_none_when_missing(self):
        """Test _extract_creative_intention returns None when not provided."""
        arguments = {"episode_number": 1}

        intention, error = handlers._extract_creative_intention(arguments)

        assert intention is None
        assert error is None

    def test_extract_creative_intention_handles_invalid_dict(self):
        """Test _extract_creative_intention handles invalid dict gracefully."""
        arguments = {
            "creative_intention": {
                "invalid_field": "value"
                # Missing required fields
            }
        }

        intention, error = handlers._extract_creative_intention(arguments)

        # Should return None with error message
        assert intention is None
        assert error is not None
        assert "Failed to deserialize" in error

    def test_validate_creative_intention_for_polish_accepts_none(self):
        """Test _validate_creative_intention_for_polish accepts None (lenient)."""
        is_valid, error_response = handlers._validate_creative_intention_for_polish(
            None, None
        )

        assert is_valid is True
        assert error_response is None

    def test_validate_creative_intention_for_polish_rejects_deserialization_error(self):
        """Test _validate_creative_intention_for_polish rejects deserialization errors."""
        is_valid, error_response = handlers._validate_creative_intention_for_polish(
            None, "Failed to parse: missing required field"
        )

        assert is_valid is False
        assert error_response is not None
        assert error_response["error_type"] == "CreativeIntentionDeserializationError"

    def test_validate_creative_intention_for_polish_accepts_valid(self):
        """Test _validate_creative_intention_for_polish accepts valid intention."""
        arc = CharacterArc(
            before_state="いじめられている被害者",
            transition="Brain Burstの授与",
            after_state="加速世界への転移",
        )
        intention = CreativeIntention(
            scene_goal="主人公の弱点を冒頭で明示し共感獲得",
            emotional_goal="絶望→驚き→期待",
            character_arc=arc,
            world_via_action="時間停止を体験シーンで提示",
            voice_constraints="「AはBである」形式禁止",
        )

        is_valid, error_response = handlers._validate_creative_intention_for_polish(
            intention, None
        )

        assert is_valid is True
        assert error_response is None


class TestEnhancedExecuteWritingStepWithCreativeIntention:
    """Test enhanced_execute_writing_step with Creative Intention preflight for Step 12."""

    @pytest.fixture
    def valid_creative_intention_dict(self):
        """Return a valid Creative Intention as dict."""
        return {
            "scene_goal": "主人公の弱点を冒頭で明示し共感獲得",
            "emotional_goal": "絶望→驚き→期待",
            "character_arc": {
                "before_state": "いじめられている被害者",
                "transition": "Brain Burstの授与",
                "after_state": "加速世界への転移",
            },
            "world_via_action": "時間停止を体験シーンで提示",
            "voice_constraints": "「AはBである」形式禁止",
            "episode_number": 1,
        }

    @pytest.fixture
    def invalid_creative_intention_dict(self):
        """Return an invalid Creative Intention (too short fields)."""
        return {
            "scene_goal": "短い",  # Too short
            "emotional_goal": "短",  # Too short
            "character_arc": {
                "before_state": "短",  # Too short
                "transition": "短",  # Too short
                "after_state": "短",  # Too short
            },
            "world_via_action": "短い",  # Too short
            "voice_constraints": "短",  # Too short
        }

    @pytest.fixture
    def mock_use_case_response(self):
        """Return a mock EnhancedWritingUseCase response."""
        return {
            "success": True,
            "step_id": 12,
            "message": "Step 12 (初稿執筆) 実行完了",
            "metadata": {"execution_time_ms": 2000},
        }

    @pytest.mark.asyncio
    async def test_step_12_with_valid_creative_intention(
        self, valid_creative_intention_dict, mock_use_case_response
    ):
        """Test enhanced_execute_writing_step (Step 12) with valid Creative Intention."""
        arguments = {
            "episode_number": 1,
            "step_id": 12,
            "project_root": "/test/project",
            "creative_intention": valid_creative_intention_dict,
        }

        # Mock EnhancedWritingUseCase
        async def mock_async_execute(*args, **kwargs):
            return mock_use_case_response

        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_use_case_class = Mock()
            mock_use_case_instance = Mock()
            mock_use_case_instance.execute_writing_step_with_recovery_async = mock_async_execute
            mock_use_case_class.return_value = mock_use_case_instance
            mock_module.EnhancedWritingUseCase = mock_use_case_class
            mock_import.return_value = mock_module

            result = await handlers.enhanced_execute_writing_step(arguments)

        # Assertions
        assert result["success"] is True
        assert result["step_id"] == 12
        assert result["result"]["metadata"]["creative_intention_validated"] is True

    @pytest.mark.asyncio
    async def test_step_12_with_invalid_creative_intention(
        self, invalid_creative_intention_dict
    ):
        """Test enhanced_execute_writing_step (Step 12) rejects invalid Creative Intention."""
        arguments = {
            "episode_number": 1,
            "step_id": 12,
            "project_root": "/test/project",
            "creative_intention": invalid_creative_intention_dict,
        }

        # No need to mock use case - validation should fail before use case is accessed
        result = await handlers.enhanced_execute_writing_step(arguments)

        # Assertions - validation should fail before execution
        assert result["success"] is False
        assert result["error_type"] == "CreativeIntentionDeserializationError"
        assert "validation_issues" in result
        assert len(result["validation_issues"]) > 0

    @pytest.mark.asyncio
    async def test_step_12_without_creative_intention_backward_compatible(
        self, mock_use_case_response
    ):
        """Test enhanced_execute_writing_step (Step 12) without Creative Intention (lenient)."""
        arguments = {
            "episode_number": 1,
            "step_id": 12,
            "project_root": "/test/project",
            # No creative_intention provided - should proceed normally
        }

        # Mock EnhancedWritingUseCase
        async def mock_async_execute(*args, **kwargs):
            return mock_use_case_response

        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_use_case_class = Mock()
            mock_use_case_instance = Mock()
            mock_use_case_instance.execute_writing_step_with_recovery_async = mock_async_execute
            mock_use_case_class.return_value = mock_use_case_instance
            mock_module.EnhancedWritingUseCase = mock_use_case_class
            mock_import.return_value = mock_module

            result = await handlers.enhanced_execute_writing_step(arguments)

        # Assertions - should proceed normally (lenient mode)
        assert result["success"] is True
        assert result["step_id"] == 12
        assert "creative_intention_validated" not in result["result"]["metadata"]

    @pytest.mark.asyncio
    async def test_other_steps_skip_creative_intention_check(
        self, valid_creative_intention_dict, mock_use_case_response
    ):
        """Test enhanced_execute_writing_step for non-Step-12 skips Creative Intention check."""
        # Test Step 11 (伏線配置) - should skip Creative Intention check
        arguments = {
            "episode_number": 1,
            "step_id": 11,
            "project_root": "/test/project",
            "creative_intention": valid_creative_intention_dict,
        }

        # Mock EnhancedWritingUseCase
        mock_use_case_response_step_11 = {
            "success": True,
            "step_id": 11,
            "message": "Step 11 (伏線配置) 実行完了",
        }

        async def mock_async_execute(*args, **kwargs):
            return mock_use_case_response_step_11

        with patch("importlib.import_module") as mock_import:
            mock_module = Mock()
            mock_use_case_class = Mock()
            mock_use_case_instance = Mock()
            mock_use_case_instance.execute_writing_step_with_recovery_async = mock_async_execute
            mock_use_case_class.return_value = mock_use_case_instance
            mock_module.EnhancedWritingUseCase = mock_use_case_class
            mock_import.return_value = mock_module

            result = await handlers.enhanced_execute_writing_step(arguments)

        # Assertions - should execute without Creative Intention check
        assert result["success"] is True
        assert result["step_id"] == 11
        assert "creative_intention_validated" not in result.get("metadata", {})
