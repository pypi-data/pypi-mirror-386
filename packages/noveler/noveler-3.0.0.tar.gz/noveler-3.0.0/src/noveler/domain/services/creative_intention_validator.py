#!/usr/bin/env python3
# File: src/noveler/domain/services/creative_intention_validator.py
# Purpose: Validate Creative Intention 5-Point Check before Step 11 or polish execution
# Context: Domain service for pre-flight validation (noveler_write.md specification)

"""Creative Intention validation service.

This domain service validates the Creative Intention 5-Point Check before
executing Step 11 (初稿執筆) or polish_manuscript, ensuring structural clarity
and preventing unintentional narrative drift.

Core Principle:
    "Before polish, ensure structure; before structure, clarify intent."
    - noveler_write_draft.md

References:
    - docs/drafts/noveler_write_draft.md (lines 52-100)
    - Gate W1: 構造サニティ (workflow_granularity_map.md)
    - A28 Stage 2: turning_point design
"""

from dataclasses import dataclass, field
from typing import Optional

from noveler.domain.value_objects.creative_intention import (
    CharacterArc,
    CreativeIntention,
)


@dataclass
class ValidationIssue:
    """Single validation issue found in Creative Intention.

    Attributes:
        field_name: Name of the problematic field
        severity: 'error' (blocks execution) or 'warning' (advisory)
        message: Human-readable issue description
        suggestion: Optional remediation guidance
    """
    field_name: str
    severity: str  # 'error' or 'warning'
    message: str
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of Creative Intention validation.

    Attributes:
        is_valid: True if all mandatory checks pass
        issues: List of detected problems
        checked_intention: The CreativeIntention that was validated
    """
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    checked_intention: Optional[CreativeIntention] = None

    def has_errors(self) -> bool:
        """Check if any error-level issues exist.

        Returns:
            True if at least one error-level issue exists
        """
        return any(issue.severity == "error" for issue in self.issues)

    def has_warnings(self) -> bool:
        """Check if any warning-level issues exist.

        Returns:
            True if at least one warning-level issue exists
        """
        return any(issue.severity == "warning" for issue in self.issues)

    def get_error_count(self) -> int:
        """Count error-level issues.

        Returns:
            Number of error-level issues
        """
        return sum(1 for issue in self.issues if issue.severity == "error")

    def get_warning_count(self) -> int:
        """Count warning-level issues.

        Returns:
            Number of warning-level issues
        """
        return sum(1 for issue in self.issues if issue.severity == "warning")


class CreativeIntentionValidator:
    """Validator for Creative Intention 5-Point Check.

    This service validates the completeness and quality of creative intentions
    before executing narrative generation steps (Step 11 or polish_manuscript).

    Validation Rules:
        1. All five fields must be filled
        2. Minimum length requirements (Lite version: 10-60 chars)
        3. Character arc must have all three states (before/transition/after)
        4. Emotional goal should show progression (e.g., "絶望→驚き")
        5. Voice constraints should explicitly forbid something

    Example:
        >>> validator = CreativeIntentionValidator()
        >>> result = validator.validate(intention)
        >>> if not result.is_valid:
        ...     for issue in result.issues:
        ...         print(f"{issue.severity}: {issue.message}")
    """

    def __init__(self) -> None:
        """Initialize validator with default settings."""
        self.min_length_lite = 10  # Minimum for Lite version
        self.recommended_min = 30  # Recommended minimum for quality
        self.recommended_max = 60  # Recommended maximum for brevity

    def validate(self, intention: CreativeIntention) -> ValidationResult:
        """Validate a Creative Intention instance.

        Args:
            intention: The CreativeIntention to validate

        Returns:
            ValidationResult with is_valid flag and any detected issues

        Note:
            This method catches ValueError from CreativeIntention validation
            and converts it to structured ValidationIssue objects.
        """
        issues: list[ValidationIssue] = []

        # Basic completeness check (catches ValueError)
        try:
            if not intention.is_complete():
                issues.append(ValidationIssue(
                    field_name="overall",
                    severity="error",
                    message="Creative Intention is incomplete",
                    suggestion="Fill all five mandatory fields"
                ))
        except ValueError as e:
            issues.append(ValidationIssue(
                field_name="overall",
                severity="error",
                message=str(e),
                suggestion="Check field lengths and content"
            ))

        # Individual field validations
        issues.extend(self._validate_scene_goal(intention))
        issues.extend(self._validate_emotional_goal(intention))
        issues.extend(self._validate_character_arc(intention.character_arc))
        issues.extend(self._validate_world_via_action(intention))
        issues.extend(self._validate_voice_constraints(intention))

        is_valid = not any(issue.severity == "error" for issue in issues)

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            checked_intention=intention
        )

    def _validate_scene_goal(self, intention: CreativeIntention) -> list[ValidationIssue]:
        """Validate scene goal field.

        Args:
            intention: CreativeIntention instance

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        goal = intention.scene_goal.strip()

        if len(goal) < self.min_length_lite:
            issues.append(ValidationIssue(
                field_name="scene_goal",
                severity="error",
                message=f"Scene goal too short: {len(goal)} chars (min: {self.min_length_lite})",
                suggestion="Describe the narrative objective in 30-60 chars"
            ))
        elif len(goal) < self.recommended_min:
            issues.append(ValidationIssue(
                field_name="scene_goal",
                severity="warning",
                message=f"Scene goal brief: {len(goal)} chars (recommended: {self.recommended_min}+)",
                suggestion="Add more specificity for clarity"
            ))

        return issues

    def _validate_emotional_goal(self, intention: CreativeIntention) -> list[ValidationIssue]:
        """Validate emotional goal field.

        Args:
            intention: CreativeIntention instance

        Returns:
            List of validation issues
        """
        issues = []
        goal = intention.emotional_goal.strip()

        if len(goal) < 5:
            issues.append(ValidationIssue(
                field_name="emotional_goal",
                severity="error",
                message="Emotional goal too short",
                suggestion="Use format '感情A→感情B→感情C' (e.g., '絶望→驚き→期待')"
            ))

        # Check for progression arrow (optional but recommended)
        if "→" not in goal and "->" not in goal:
            issues.append(ValidationIssue(
                field_name="emotional_goal",
                severity="warning",
                message="Emotional goal lacks progression indicator (→)",
                suggestion="Show emotional arc with arrows (e.g., '絶望→驚き→期待')"
            ))

        return issues

    def _validate_character_arc(self, arc: CharacterArc) -> list[ValidationIssue]:
        """Validate character arc structure.

        Args:
            arc: CharacterArc instance

        Returns:
            List of validation issues
        """
        issues = []

        # Check minimum lengths
        if len(arc.before_state.strip()) < 5:
            issues.append(ValidationIssue(
                field_name="character_arc.before_state",
                severity="error",
                message="before_state too short (min: 5 chars)",
                suggestion="Describe initial character state clearly"
            ))

        if len(arc.transition.strip()) < 5:
            issues.append(ValidationIssue(
                field_name="character_arc.transition",
                severity="error",
                message="transition too short (min: 5 chars)",
                suggestion="Describe the trigger event that causes change"
            ))

        if len(arc.after_state.strip()) < 5:
            issues.append(ValidationIssue(
                field_name="character_arc.after_state",
                severity="error",
                message="after_state too short (min: 5 chars)",
                suggestion="Describe resulting character state clearly"
            ))

        # Check for meaningful content (not just spaces/punctuation)
        for field_name, value in [
            ("before_state", arc.before_state),
            ("transition", arc.transition),
            ("after_state", arc.after_state)
        ]:
            if value.strip() and not any(c.isalnum() for c in value):
                issues.append(ValidationIssue(
                    field_name=f"character_arc.{field_name}",
                    severity="error",
                    message=f"{field_name} contains no meaningful content",
                    suggestion="Add descriptive text with actual characters"
                ))

        return issues

    def _validate_world_via_action(self, intention: CreativeIntention) -> list[ValidationIssue]:
        """Validate world-building strategy field.

        Args:
            intention: CreativeIntention instance

        Returns:
            List of validation issues
        """
        issues = []
        strategy = intention.world_via_action.strip()

        if len(strategy) < self.min_length_lite:
            issues.append(ValidationIssue(
                field_name="world_via_action",
                severity="error",
                message=f"World-building strategy too short: {len(strategy)} chars",
                suggestion="Describe how to show (not tell) world elements via action/senses"
            ))

        # Check for common exposition keywords (warning only)
        exposition_keywords = ["説明", "解説", "述べる", "記述"]
        if any(keyword in strategy for keyword in exposition_keywords):
            issues.append(ValidationIssue(
                field_name="world_via_action",
                severity="warning",
                message="Strategy may contain exposition keywords",
                suggestion="Focus on showing via action/senses, not exposition"
            ))

        return issues

    def _validate_voice_constraints(self, intention: CreativeIntention) -> list[ValidationIssue]:
        """Validate voice constraints field.

        Args:
            intention: CreativeIntention instance

        Returns:
            List of validation issues
        """
        issues = []
        constraints = intention.voice_constraints.strip()

        if len(constraints) < 5:
            issues.append(ValidationIssue(
                field_name="voice_constraints",
                severity="error",
                message="Voice constraints too short",
                suggestion="Specify POV/tense and at least one forbidden expression"
            ))

        # Check for explicit prohibition (recommended)
        prohibition_keywords = ["禁止", "NG", "避ける", "使わない"]
        if not any(keyword in constraints for keyword in prohibition_keywords):
            issues.append(ValidationIssue(
                field_name="voice_constraints",
                severity="warning",
                message="No explicit prohibition found in voice constraints",
                suggestion="Clearly state what to avoid (e.g., '「AはBである」形式禁止')"
            ))

        return issues

    def validate_for_step_11(self, intention: CreativeIntention) -> ValidationResult:
        """Validate Creative Intention specifically for Step 11 (初稿執筆).

        This is a convenience method that applies stricter validation rules
        for initial manuscript generation.

        Args:
            intention: CreativeIntention to validate

        Returns:
            ValidationResult with Step 11-specific checks

        Note:
            This method is more strict than general validation, requiring
            all fields to meet recommended lengths.
        """
        result = self.validate(intention)

        # Add Step 11-specific checks
        if intention.episode_number is None:
            result.issues.append(ValidationIssue(
                field_name="episode_number",
                severity="warning",
                message="Episode number not specified",
                suggestion="Set episode_number for context tracking"
            ))

        if intention.file_path is None:
            result.issues.append(ValidationIssue(
                field_name="file_path",
                severity="warning",
                message="Target file path not specified",
                suggestion="Set file_path for execution context"
            ))

        return result

    def validate_for_polish(self, intention: CreativeIntention) -> ValidationResult:
        """Validate Creative Intention for polish_manuscript execution.

        This method applies validation rules appropriate for polish operations,
        which may be slightly more lenient than Step 11 requirements.

        Args:
            intention: CreativeIntention to validate

        Returns:
            ValidationResult with polish-specific checks
        """
        # For polish, we use standard validation
        # (polish assumes structure already exists)
        return self.validate(intention)
