#!/usr/bin/env python3
# File: src/noveler/domain/value_objects/creative_intention.py
# Purpose: Creative Intention 5-Point Check value object for narrative structure validation
# Context: Implements noveler_write.md specification for pre-execution intent validation

"""Creative Intention value object for pre-execution validation.

This module defines the 5-point creative intention checklist required before
Step 11 (初稿執筆) or polish_manuscript execution, as specified in
docs/drafts/noveler_write_draft.md.

The five mandatory elements are:
1. Scene Goal: Narrative objective for this scene
2. Emotional Goal: Target reader emotion (共感/驚き/期待)
3. Character Arc: before_state → transition → after_state
4. World via Action: Show-don't-tell strategy (行動/五感で説明)
5. Voice Constraints: POV/tense/forbidden expressions

References:
    - docs/drafts/noveler_write_draft.md (lines 52-100)
    - A28_話別プロットプロンプト.md (Stage 2: turning_point design)
    - Gate W1: 構造サニティ (workflow_granularity_map.md)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CharacterArc:
    """Character transformation structure (before/transition/after).

    Attributes:
        before_state: Initial character state (e.g., "いじめられている被害者")
        transition: Trigger event causing change (e.g., "Brain Burstの授与")
        after_state: Resulting character state (e.g., "加速世界への転移")

    Note:
        Uses A28 terminology where "transition" represents the trigger event
        that causes the transformation, aligned with turning_point design.
    """
    before_state: str
    transition: str  # A28: trigger event
    after_state: str

    def __post_init__(self) -> None:
        """Validate minimum content requirements."""
        if not self.before_state or len(self.before_state.strip()) < 5:
            raise ValueError("before_state must be at least 5 characters")
        if not self.transition or len(self.transition.strip()) < 5:
            raise ValueError("transition must be at least 5 characters")
        if not self.after_state or len(self.after_state.strip()) < 5:
            raise ValueError("after_state must be at least 5 characters")


@dataclass
class CreativeIntention:
    """Creative Intention 5-Point Check for narrative structure validation.

    This value object captures the writer's intent before executing Step 11
    (初稿執筆) or polish_manuscript, ensuring structural clarity.

    Attributes:
        scene_goal: Narrative objective (30-60 chars for Lite version)
        emotional_goal: Target reader emotion arc (e.g., "絶望→驚き→期待")
        character_arc: Before/transition/after structure
        world_via_action: Show-don't-tell strategy (avoid exposition)
        voice_constraints: POV/tense/forbidden expressions
        episode_number: Target episode (optional, for context)
        file_path: Target manuscript file (optional, for context)

    Raises:
        ValueError: If any field fails minimum length requirements

    Example:
        >>> arc = CharacterArc(
        ...     before_state="いじめられている被害者",
        ...     transition="Brain Burstの授与",
        ...     after_state="加速世界への転移"
        ... )
        >>> intention = CreativeIntention(
        ...     scene_goal="主人公の弱点を冒頭で明示し共感獲得",
        ...     emotional_goal="絶望→驚き→期待",
        ...     character_arc=arc,
        ...     world_via_action="時間停止を体験シーンで提示",
        ...     voice_constraints="「AはBである」形式禁止"
        ... )
    """
    scene_goal: str
    emotional_goal: str
    character_arc: CharacterArc
    world_via_action: str
    voice_constraints: str
    episode_number: Optional[int] = None
    file_path: Optional[Path] = None

    # Lite version thresholds (1分記入テンプレート)
    MIN_LENGTH_LITE: int = field(default=10, init=False, repr=False)
    MAX_LENGTH_LITE: int = field(default=60, init=False, repr=False)

    def __post_init__(self) -> None:
        """Validate all fields meet minimum requirements.

        Raises:
            ValueError: If any field is too short or missing
        """
        self._validate_scene_goal()
        self._validate_emotional_goal()
        self._validate_world_via_action()
        self._validate_voice_constraints()

    def _validate_scene_goal(self) -> None:
        """Validate scene goal field."""
        if not self.scene_goal or len(self.scene_goal.strip()) < self.MIN_LENGTH_LITE:
            raise ValueError(
                f"scene_goal must be at least {self.MIN_LENGTH_LITE} characters "
                f"(Lite version: 30-60 chars recommended)"
            )

    def _validate_emotional_goal(self) -> None:
        """Validate emotional goal field."""
        if not self.emotional_goal or len(self.emotional_goal.strip()) < 5:
            raise ValueError(
                "emotional_goal must be at least 5 characters "
                "(e.g., '絶望→驚き→期待')"
            )

    def _validate_world_via_action(self) -> None:
        """Validate world-building strategy field."""
        if not self.world_via_action or len(self.world_via_action.strip()) < self.MIN_LENGTH_LITE:
            raise ValueError(
                f"world_via_action must be at least {self.MIN_LENGTH_LITE} characters "
                f"(describe show-don't-tell strategy)"
            )

    def _validate_voice_constraints(self) -> None:
        """Validate voice constraints field."""
        if not self.voice_constraints or len(self.voice_constraints.strip()) < 5:
            raise ValueError(
                "voice_constraints must be at least 5 characters "
                "(e.g., '「AはBである」形式禁止')"
            )

    def is_complete(self) -> bool:
        """Check if all fields are filled with sufficient content.

        Returns:
            True if all validations pass
        """
        try:
            self._validate_scene_goal()
            self._validate_emotional_goal()
            self._validate_world_via_action()
            self._validate_voice_constraints()
            return True
        except ValueError:
            return False

    def to_dict(self) -> dict[str, any]:
        """Serialize to dictionary for JSON/YAML output.

        Returns:
            Dictionary with all fields, including nested character_arc
        """
        return {
            "scene_goal": self.scene_goal,
            "emotional_goal": self.emotional_goal,
            "character_arc": {
                "before_state": self.character_arc.before_state,
                "transition": self.character_arc.transition,
                "after_state": self.character_arc.after_state,
            },
            "world_via_action": self.world_via_action,
            "voice_constraints": self.voice_constraints,
            "episode_number": self.episode_number,
            "file_path": str(self.file_path) if self.file_path else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, any]) -> "CreativeIntention":
        """Deserialize from dictionary.

        Args:
            data: Dictionary with creative intention fields

        Returns:
            CreativeIntention instance

        Raises:
            ValueError: If required fields are missing
        """
        arc_data = data.get("character_arc", {})
        arc = CharacterArc(
            before_state=arc_data.get("before_state", ""),
            transition=arc_data.get("transition", ""),
            after_state=arc_data.get("after_state", ""),
        )

        file_path_str = data.get("file_path")
        file_path = Path(file_path_str) if file_path_str else None

        return cls(
            scene_goal=data.get("scene_goal", ""),
            emotional_goal=data.get("emotional_goal", ""),
            character_arc=arc,
            world_via_action=data.get("world_via_action", ""),
            voice_constraints=data.get("voice_constraints", ""),
            episode_number=data.get("episode_number"),
            file_path=file_path,
        )
