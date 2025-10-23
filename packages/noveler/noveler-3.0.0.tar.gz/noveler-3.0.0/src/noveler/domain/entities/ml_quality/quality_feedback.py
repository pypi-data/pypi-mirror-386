# File: src/noveler/domain/entities/ml_quality/quality_feedback.py
# Purpose: Quality feedback entity for ML learning
# Context: Represents evaluation feedback records for model training

"""
Quality Feedback Entity.

This entity represents a feedback record from quality evaluation,
including automated scores, human scores, and user corrections.

Contract: SPEC-QUALITY-140 §3.2
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EvaluationOutcome(Enum):
    """Outcome of quality evaluation."""
    PASS = "pass"
    FAIL = "fail"
    MANUAL_OVERRIDE = "manual_override"
    SKIPPED = "skipped"


class FeedbackSource(Enum):
    """Source of feedback."""
    AUTHOR = "author"
    EDITOR = "editor"
    READER = "reader"
    AUTOMATED = "automated"


@dataclass(frozen=True)
class CorrectionRecord:
    """
    User correction record.

    Represents a single correction made by the user in response
    to automated quality check suggestions.

    Attributes:
        issue_id: ID of the issue being corrected
        automated_suggestion: What the system suggested
        user_action: What the user actually did
        accepted: Whether user accepted the automated fix
        correction_timestamp: When the correction was made
    """
    issue_id: str
    automated_suggestion: str
    user_action: str
    accepted: bool
    correction_timestamp: datetime


@dataclass(frozen=True)
class QualityFeedback:
    """
    Quality feedback entity.

    This entity represents feedback from a quality evaluation,
    used for ML model training and optimization.

    Attributes:
        feedback_id: Unique identifier
        episode_number: Episode that was evaluated
        evaluation_timestamp: When evaluation occurred
        automated_scores: Scores from automated checks
        human_scores: Scores from human review (optional)
        user_corrections: List of user corrections
        outcome: Evaluation outcome (PASS, FAIL, etc.)
        feedback_source: Who provided the feedback
        aspects_checked: Which aspects were evaluated
        notes: Optional feedback notes

    Invariants:
        - feedback_id must be unique
        - episode_number must be > 0
        - automated_scores must not be empty
        - If outcome is MANUAL_OVERRIDE, human_scores must be present

    Contract: SPEC-QUALITY-140 §3.2
    """
    feedback_id: str
    episode_number: int
    evaluation_timestamp: datetime
    automated_scores: dict[str, float]
    outcome: EvaluationOutcome
    feedback_source: FeedbackSource
    human_scores: Optional[dict[str, float]] = None
    user_corrections: list[CorrectionRecord] = field(default_factory=list)
    aspects_checked: list[str] = field(default_factory=list)
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate invariants."""
        if not self.feedback_id:
            raise ValueError("feedback_id cannot be empty")

        if self.episode_number <= 0:
            raise ValueError(f"episode_number must be > 0, got {self.episode_number}")

        if not self.automated_scores:
            raise ValueError("automated_scores cannot be empty")

        if self.outcome == EvaluationOutcome.MANUAL_OVERRIDE and not self.human_scores:
            raise ValueError("human_scores required when outcome is MANUAL_OVERRIDE")

    def is_false_positive(self) -> bool:
        """
        Check if this feedback represents a false positive.

        Returns:
            True if automated check failed but human review passed
        """
        if not self.human_scores:
            return False

        automated_pass = self._compute_pass_fail(self.automated_scores)
        human_pass = self._compute_pass_fail(self.human_scores)

        return not automated_pass and human_pass

    def is_false_negative(self) -> bool:
        """
        Check if this feedback represents a false negative.

        Returns:
            True if automated check passed but human review failed
        """
        if not self.human_scores:
            return False

        automated_pass = self._compute_pass_fail(self.automated_scores)
        human_pass = self._compute_pass_fail(self.human_scores)

        return automated_pass and not human_pass

    def _compute_pass_fail(self, scores: dict[str, float], threshold: float = 80.0) -> bool:
        """
        Compute pass/fail based on overall score.

        Args:
            scores: Score dictionary
            threshold: Pass threshold (default: 80.0)

        Returns:
            True if overall score >= threshold
        """
        overall_score = scores.get("overall", 0.0)
        return overall_score >= threshold

    def get_correction_acceptance_rate(self) -> float:
        """
        Calculate percentage of automated corrections accepted by user.

        Returns:
            Acceptance rate (0.0-1.0)
        """
        if not self.user_corrections:
            return 0.0

        accepted_count = sum(1 for c in self.user_corrections if c.accepted)
        return accepted_count / len(self.user_corrections)

    def get_score_delta(self, aspect: str) -> Optional[float]:
        """
        Get difference between automated and human score for an aspect.

        Args:
            aspect: Aspect name (rhythm, readability, etc.)

        Returns:
            human_score - automated_score, or None if human_scores unavailable
        """
        if not self.human_scores:
            return None

        automated = self.automated_scores.get(aspect, 0.0)
        human = self.human_scores.get(aspect, 0.0)

        return human - automated

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "feedback_id": self.feedback_id,
            "episode_number": self.episode_number,
            "evaluation_timestamp": self.evaluation_timestamp.isoformat(),
            "automated_scores": self.automated_scores,
            "human_scores": self.human_scores,
            "user_corrections": [
                {
                    "issue_id": c.issue_id,
                    "automated_suggestion": c.automated_suggestion,
                    "user_action": c.user_action,
                    "accepted": c.accepted,
                    "correction_timestamp": c.correction_timestamp.isoformat()
                }
                for c in self.user_corrections
            ],
            "outcome": self.outcome.value,
            "feedback_source": self.feedback_source.value,
            "aspects_checked": self.aspects_checked,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QualityFeedback":
        """
        Create QualityFeedback from dictionary.

        Args:
            data: Dictionary with feedback data

        Returns:
            QualityFeedback instance
        """
        user_corrections = [
            CorrectionRecord(
                issue_id=c["issue_id"],
                automated_suggestion=c["automated_suggestion"],
                user_action=c["user_action"],
                accepted=c["accepted"],
                correction_timestamp=datetime.fromisoformat(c["correction_timestamp"])
            )
            for c in data.get("user_corrections", [])
        ]

        return cls(
            feedback_id=data["feedback_id"],
            episode_number=data["episode_number"],
            evaluation_timestamp=datetime.fromisoformat(data["evaluation_timestamp"]),
            automated_scores=data["automated_scores"],
            outcome=EvaluationOutcome(data["outcome"]),
            feedback_source=FeedbackSource(data["feedback_source"]),
            human_scores=data.get("human_scores"),
            user_corrections=user_corrections,
            aspects_checked=data.get("aspects_checked", []),
            notes=data.get("notes")
        )

    def get_summary(self) -> str:
        """
        Get human-readable summary.

        Returns:
            Summary string
        """
        auto_overall = self.automated_scores.get("overall", 0)
        human_overall = self.human_scores.get("overall", 0) if self.human_scores else None

        if human_overall is not None:
            delta = human_overall - auto_overall
            return (
                f"Episode {self.episode_number}: Auto={auto_overall:.1f}, "
                f"Human={human_overall:.1f} (Δ{delta:+.1f}), "
                f"{self.outcome.value}"
            )
        else:
            return (
                f"Episode {self.episode_number}: Auto={auto_overall:.1f}, "
                f"{self.outcome.value}"
            )
