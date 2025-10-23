#!/usr/bin/env python3
# File: tests/unit/domain/value_objects/test_creative_intention.py
# Purpose: Unit tests for CreativeIntention value object
# Context: Validates 5-point creative intention structure

"""Tests for CreativeIntention value object."""

import pytest
from pathlib import Path

from noveler.domain.value_objects.creative_intention import (
    CharacterArc,
    CreativeIntention,
)


class TestCharacterArc:
    """Test CharacterArc value object."""

    def test_valid_character_arc(self):
        """Test creating a valid CharacterArc."""
        arc = CharacterArc(
            before_state="いじめられている被害者",
            transition="Brain Burstの授与",
            after_state="加速世界への転移"
        )

        assert arc.before_state == "いじめられている被害者"
        assert arc.transition == "Brain Burstの授与"
        assert arc.after_state == "加速世界への転移"

    def test_character_arc_too_short_before_state(self):
        """Test CharacterArc rejects too-short before_state."""
        with pytest.raises(ValueError, match="before_state must be at least 5 characters"):
            CharacterArc(
                before_state="短い",
                transition="trigger event",
                after_state="after state"
            )

    def test_character_arc_too_short_transition(self):
        """Test CharacterArc rejects too-short transition."""
        with pytest.raises(ValueError, match="transition must be at least 5 characters"):
            CharacterArc(
                before_state="before state",
                transition="短",
                after_state="after state"
            )

    def test_character_arc_too_short_after_state(self):
        """Test CharacterArc rejects too-short after_state."""
        with pytest.raises(ValueError, match="after_state must be at least 5 characters"):
            CharacterArc(
                before_state="before state",
                transition="trigger event",
                after_state="短"
            )


class TestCreativeIntention:
    """Test CreativeIntention value object."""

    @pytest.fixture
    def valid_arc(self):
        """Return a valid CharacterArc for testing."""
        return CharacterArc(
            before_state="いじめられている被害者",
            transition="Brain Burstの授与",
            after_state="加速世界への転移"
        )

    @pytest.fixture
    def valid_intention(self, valid_arc):
        """Return a valid CreativeIntention for testing."""
        return CreativeIntention(
            scene_goal="主人公の弱点を冒頭で明示し共感獲得",
            emotional_goal="絶望→驚き→期待",
            character_arc=valid_arc,
            world_via_action="時間停止を体験シーンで提示",
            voice_constraints="「AはBである」形式禁止",
            episode_number=1
        )

    def test_valid_creative_intention(self, valid_intention):
        """Test creating a valid CreativeIntention."""
        assert valid_intention.scene_goal == "主人公の弱点を冒頭で明示し共感獲得"
        assert valid_intention.emotional_goal == "絶望→驚き→期待"
        assert valid_intention.world_via_action == "時間停止を体験シーンで提示"
        assert valid_intention.voice_constraints == "「AはBである」形式禁止"
        assert valid_intention.episode_number == 1

    def test_creative_intention_too_short_scene_goal(self, valid_arc):
        """Test CreativeIntention rejects too-short scene_goal."""
        with pytest.raises(ValueError, match="scene_goal must be at least"):
            CreativeIntention(
                scene_goal="短い",
                emotional_goal="絶望→驚き→期待",
                character_arc=valid_arc,
                world_via_action="時間停止を体験シーンで提示",
                voice_constraints="「AはBである」形式禁止"
            )

    def test_creative_intention_too_short_emotional_goal(self, valid_arc):
        """Test CreativeIntention rejects too-short emotional_goal."""
        with pytest.raises(ValueError, match="emotional_goal must be at least"):
            CreativeIntention(
                scene_goal="主人公の弱点を冒頭で明示し共感獲得",
                emotional_goal="短",
                character_arc=valid_arc,
                world_via_action="時間停止を体験シーンで提示",
                voice_constraints="「AはBである」形式禁止"
            )

    def test_creative_intention_too_short_world_via_action(self, valid_arc):
        """Test CreativeIntention rejects too-short world_via_action."""
        with pytest.raises(ValueError, match="world_via_action must be at least"):
            CreativeIntention(
                scene_goal="主人公の弱点を冒頭で明示し共感獲得",
                emotional_goal="絶望→驚き→期待",
                character_arc=valid_arc,
                world_via_action="短い",
                voice_constraints="「AはBである」形式禁止"
            )

    def test_creative_intention_too_short_voice_constraints(self, valid_arc):
        """Test CreativeIntention rejects too-short voice_constraints."""
        with pytest.raises(ValueError, match="voice_constraints must be at least"):
            CreativeIntention(
                scene_goal="主人公の弱点を冒頭で明示し共感獲得",
                emotional_goal="絶望→驚き→期待",
                character_arc=valid_arc,
                world_via_action="時間停止を体験シーンで提示",
                voice_constraints="短"
            )

    def test_is_complete_true_for_valid(self, valid_intention):
        """Test is_complete returns True for valid intention."""
        assert valid_intention.is_complete() is True

    def test_to_dict_serialization(self, valid_intention):
        """Test serialization to dictionary."""
        data = valid_intention.to_dict()

        assert data["scene_goal"] == "主人公の弱点を冒頭で明示し共感獲得"
        assert data["emotional_goal"] == "絶望→驚き→期待"
        assert data["character_arc"]["before_state"] == "いじめられている被害者"
        assert data["character_arc"]["transition"] == "Brain Burstの授与"
        assert data["character_arc"]["after_state"] == "加速世界への転移"
        assert data["world_via_action"] == "時間停止を体験シーンで提示"
        assert data["voice_constraints"] == "「AはBである」形式禁止"
        assert data["episode_number"] == 1

    def test_from_dict_deserialization(self, valid_intention):
        """Test deserialization from dictionary."""
        data = valid_intention.to_dict()
        restored = CreativeIntention.from_dict(data)

        assert restored.scene_goal == valid_intention.scene_goal
        assert restored.emotional_goal == valid_intention.emotional_goal
        assert restored.character_arc.before_state == valid_intention.character_arc.before_state
        assert restored.character_arc.transition == valid_intention.character_arc.transition
        assert restored.character_arc.after_state == valid_intention.character_arc.after_state
        assert restored.world_via_action == valid_intention.world_via_action
        assert restored.voice_constraints == valid_intention.voice_constraints
        assert restored.episode_number == valid_intention.episode_number

    def test_with_file_path(self, valid_arc):
        """Test CreativeIntention with file_path."""
        file_path = Path("40_原稿/第001話_test.md")
        intention = CreativeIntention(
            scene_goal="主人公の弱点を冒頭で明示し共感獲得",
            emotional_goal="絶望→驚き→期待",
            character_arc=valid_arc,
            world_via_action="時間停止を体験シーンで提示",
            voice_constraints="「AはBである」形式禁止",
            file_path=file_path
        )

        assert intention.file_path == file_path

        # Verify serialization includes file_path
        data = intention.to_dict()
        assert data["file_path"] == str(file_path)

    def test_lite_version_minimum_lengths(self, valid_arc):
        """Test Lite version minimum lengths (10 chars)."""
        intention = CreativeIntention(
            scene_goal="最小限度の文字数確認",  # 10 chars
            emotional_goal="絶望→期待",
            character_arc=valid_arc,
            world_via_action="行動的に世界を提示中",  # 10 chars
            voice_constraints="地の文は禁止す"  # 7 chars
        )

        assert intention.is_complete() is True
