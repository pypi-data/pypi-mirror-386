#!/usr/bin/env python3
# File: tests/unit/domain/services/test_creative_intention_validator.py
# Purpose: Unit tests for CreativeIntentionValidator service
# Context: Validates 5-point creative intention validation logic

"""Tests for CreativeIntentionValidator service."""

import pytest

from noveler.domain.value_objects.creative_intention import (
    CharacterArc,
    CreativeIntention,
)
from noveler.domain.services.creative_intention_validator import (
    CreativeIntentionValidator,
    ValidationIssue,
    ValidationResult,
)


class TestValidationIssue:
    """Test ValidationIssue dataclass."""

    def test_validation_issue_creation(self):
        """Test creating a ValidationIssue."""
        issue = ValidationIssue(
            field_name="scene_goal",
            severity="error",
            message="Scene goal too short",
            suggestion="Add more detail"
        )

        assert issue.field_name == "scene_goal"
        assert issue.severity == "error"
        assert issue.message == "Scene goal too short"
        assert issue.suggestion == "Add more detail"


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_has_errors_true(self):
        """Test has_errors returns True when errors exist."""
        result = ValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue("field1", "error", "Error message"),
                ValidationIssue("field2", "warning", "Warning message")
            ]
        )

        assert result.has_errors() is True
        assert result.has_warnings() is True

    def test_has_errors_false(self):
        """Test has_errors returns False when only warnings exist."""
        result = ValidationResult(
            is_valid=True,
            issues=[
                ValidationIssue("field1", "warning", "Warning message")
            ]
        )

        assert result.has_errors() is False
        assert result.has_warnings() is True

    def test_get_error_count(self):
        """Test get_error_count returns correct count."""
        result = ValidationResult(
            is_valid=False,
            issues=[
                ValidationIssue("field1", "error", "Error 1"),
                ValidationIssue("field2", "error", "Error 2"),
                ValidationIssue("field3", "warning", "Warning")
            ]
        )

        assert result.get_error_count() == 2
        assert result.get_warning_count() == 1


class TestCreativeIntentionValidator:
    """Test CreativeIntentionValidator service."""

    @pytest.fixture
    def validator(self):
        """Return a CreativeIntentionValidator instance."""
        return CreativeIntentionValidator()

    @pytest.fixture
    def valid_arc(self):
        """Return a valid CharacterArc."""
        return CharacterArc(
            before_state="いじめられている被害者",
            transition="Brain Burstの授与",
            after_state="加速世界への転移"
        )

    @pytest.fixture
    def valid_intention(self, valid_arc):
        """Return a valid CreativeIntention."""
        return CreativeIntention(
            scene_goal="主人公の弱点を冒頭で明示し共感獲得",
            emotional_goal="絶望→驚き→期待",
            character_arc=valid_arc,
            world_via_action="時間停止を体験シーンで提示",
            voice_constraints="「AはBである」形式禁止"
        )

    def test_validate_valid_intention(self, validator, valid_intention):
        """Test validating a completely valid intention."""
        result = validator.validate(valid_intention)

        assert result.is_valid is True
        assert result.checked_intention == valid_intention
        # May have warnings but no errors
        assert result.get_error_count() == 0

    def test_validate_too_short_scene_goal(self, validator, valid_arc):
        """Test validation catches too-short scene_goal."""
        # This will raise ValueError in CreativeIntention.__post_init__
        with pytest.raises(ValueError, match="scene_goal must be at least"):
            intention = CreativeIntention(
                scene_goal="短すぎ",  # 3 chars - too short
                emotional_goal="絶望→驚き→期待",
                character_arc=valid_arc,
                world_via_action="時間停止を体験シーンで提示",
                voice_constraints="「AはBである」形式禁止"
            )

    def test_validate_brief_scene_goal_warning(self, validator, valid_arc):
        """Test validation warns for brief (but valid) scene_goal."""
        intention = CreativeIntention(
            scene_goal="最小限の10文字以上",  # 10 chars - valid but brief
            emotional_goal="絶望→驚き→期待",
            character_arc=valid_arc,
            world_via_action="時間停止を体験シーンで提示",
            voice_constraints="「AはBである」形式禁止"
        )

        result = validator.validate(intention)

        # Should pass but with warning
        assert result.is_valid is True
        assert result.get_warning_count() > 0

        # Check for scene_goal warning
        scene_goal_warnings = [
            issue for issue in result.issues
            if issue.field_name == "scene_goal" and issue.severity == "warning"
        ]
        assert len(scene_goal_warnings) > 0

    def test_validate_emotional_goal_without_arrow(self, validator, valid_arc):
        """Test validation warns when emotional_goal lacks progression arrow."""
        intention = CreativeIntention(
            scene_goal="主人公の弱点を冒頭で明示し共感獲得",
            emotional_goal="絶望と驚きと期待",  # No arrow - warning
            character_arc=valid_arc,
            world_via_action="時間停止を体験シーンで提示",
            voice_constraints="「AはBである」形式禁止"
        )

        result = validator.validate(intention)

        # Should pass but with warning about arrow
        assert result.is_valid is True
        emotional_warnings = [
            issue for issue in result.issues
            if issue.field_name == "emotional_goal" and "progression" in issue.message
        ]
        assert len(emotional_warnings) > 0

    def test_validate_world_via_action_with_exposition_keywords(self, validator, valid_arc):
        """Test validation warns for exposition keywords in world_via_action."""
        intention = CreativeIntention(
            scene_goal="主人公の弱点を冒頭で明示し共感獲得",
            emotional_goal="絶望→驚き→期待",
            character_arc=valid_arc,
            world_via_action="時間停止の仕組みを説明する",  # 説明 - warning
            voice_constraints="「AはBである」形式禁止"
        )

        result = validator.validate(intention)

        # Should pass but with warning
        assert result.is_valid is True
        world_warnings = [
            issue for issue in result.issues
            if issue.field_name == "world_via_action" and "exposition" in issue.message
        ]
        assert len(world_warnings) > 0

    def test_validate_voice_constraints_without_prohibition(self, validator, valid_arc):
        """Test validation warns when voice_constraints lack prohibition."""
        intention = CreativeIntention(
            scene_goal="主人公の弱点を冒頭で明示し共感獲得",
            emotional_goal="絶望→驚き→期待",
            character_arc=valid_arc,
            world_via_action="時間停止を体験シーンで提示",
            voice_constraints="三人称単一視点で書く"  # No prohibition - warning
        )

        result = validator.validate(intention)

        # Should pass but with warning
        assert result.is_valid is True
        voice_warnings = [
            issue for issue in result.issues
            if issue.field_name == "voice_constraints" and "prohibition" in issue.message
        ]
        assert len(voice_warnings) > 0

    def test_validate_for_step_11_with_episode_number(self, validator, valid_arc):
        """Test validate_for_step_11 with episode_number set."""
        intention = CreativeIntention(
            scene_goal="主人公の弱点を冒頭で明示し共感獲得",
            emotional_goal="絶望→驚き→期待",
            character_arc=valid_arc,
            world_via_action="時間停止を体験シーンで提示",
            voice_constraints="「AはBである」形式禁止",
            episode_number=1
        )

        result = validator.validate_for_step_11(intention)

        assert result.is_valid is True
        # Should not warn about episode_number
        episode_warnings = [
            issue for issue in result.issues
            if issue.field_name == "episode_number"
        ]
        assert len(episode_warnings) == 0

    def test_validate_for_step_11_without_episode_number(self, validator, valid_arc):
        """Test validate_for_step_11 warns without episode_number."""
        intention = CreativeIntention(
            scene_goal="主人公の弱点を冒頭で明示し共感獲得",
            emotional_goal="絶望→驚き→期待",
            character_arc=valid_arc,
            world_via_action="時間停止を体験シーンで提示",
            voice_constraints="「AはBである」形式禁止"
            # episode_number not set
        )

        result = validator.validate_for_step_11(intention)

        assert result.is_valid is True
        # Should warn about episode_number
        episode_warnings = [
            issue for issue in result.issues
            if issue.field_name == "episode_number"
        ]
        assert len(episode_warnings) > 0

    def test_validate_for_polish(self, validator, valid_intention):
        """Test validate_for_polish uses standard validation."""
        result = validator.validate_for_polish(valid_intention)

        assert result.is_valid is True
        assert result.checked_intention == valid_intention

    def test_character_arc_validation_all_fields_too_short(self, validator):
        """Test character arc validation catches all short fields."""
        # Create arc with all fields too short (will raise in __post_init__)
        with pytest.raises(ValueError):
            arc = CharacterArc(
                before_state="短",
                transition="短",
                after_state="短"
            )

    def test_character_arc_validation_meaningful_content(self, validator, valid_intention):
        """Test character arc validation for meaningful content."""
        # Valid intention should have meaningful content
        result = validator.validate(valid_intention)

        # Check no errors about meaningless content
        meaningless_errors = [
            issue for issue in result.issues
            if "meaningful content" in issue.message
        ]
        assert len(meaningless_errors) == 0
