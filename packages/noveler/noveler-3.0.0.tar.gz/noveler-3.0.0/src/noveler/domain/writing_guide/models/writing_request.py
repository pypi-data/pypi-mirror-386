# File: src/noveler/domain/writing_guide/models/writing_request.py
# Purpose: Define rich value object for writing request with business logic.
# Context: Domain model for writing guide system, encapsulates request validation and behavior.

"""Rich domain model for writing request.

Purpose:
    Provide a value object that encapsulates writing request parameters
    along with business logic for validation and behavior.

Inputs:
    Genre, word count, viewpoint, and other writing constraints.

Outputs:
    Immutable value object with validated state and business methods.

Preconditions:
    All parameters must satisfy domain invariants (checked in __init__).

Side Effects:
    None (immutable value object).

Exceptions:
    ValueError: When domain invariants are violated.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DetailLevel(Enum):
    """Writing prompt detail level enumeration.

    Purpose:
        Type-safe representation of supported template detail levels.

    Values:
        MINIMAL: Brief prompt with essential guidance only.
        STANDARD: Balanced prompt with moderate detail.
        STEPWISE: Step-by-step structured guidance.
        DETAILED: Comprehensive prompt with extensive detail.
    """

    MINIMAL = "minimal"
    STANDARD = "standard"
    STEPWISE = "stepwise"
    DETAILED = "detailed"


@dataclass(frozen=True)
class WritingRequest:
    """Rich value object representing a writing prompt generation request.

    Purpose:
        Encapsulate writing request parameters with business logic,
        maintaining domain invariants and providing behavioral methods.

    Attributes:
        genre: Target narrative genre (e.g., "fantasy", "mystery").
        word_count: Desired word-count range as string (e.g., "4000-6000").
        viewpoint: Narrative viewpoint description (e.g., "三人称単元視点").
        viewpoint_character: Character whose perspective anchors the story.
        difficulty: Desired complexity level ("beginner", "intermediate", "advanced").
        priority: Request priority level ("critical", "high", "medium", "low").
        detail_level: Template granularity (DetailLevel enum).
        project_path: Optional project root for resolving resources.
        episode_file: Optional episode-specific plot filename.
        custom_requirements: Optional additional constraints.

    Preconditions:
        - genre must not be empty
        - word_count must be in format "NNNN-MMMM"
        - detail_level must be valid DetailLevel enum value

    Side Effects:
        None (immutable).

    Exceptions:
        ValueError: When domain invariants are violated during construction.
    """

    genre: str
    word_count: str
    viewpoint: str
    viewpoint_character: str
    difficulty: str
    priority: str
    detail_level: DetailLevel
    project_path: Optional[str] = None
    episode_file: Optional[str] = None
    custom_requirements: Optional[list[str]] = None

    def __post_init__(self) -> None:
        """Validate domain invariants after initialization.

        Purpose:
            Enforce domain rules to prevent invalid state construction.

        Raises:
            ValueError: When any domain invariant is violated.

        Side Effects:
            None beyond potential exception.
        """
        if not self.genre or not self.genre.strip():
            raise ValueError("Genre must not be empty")

        if not self._is_valid_word_count_format(self.word_count):
            raise ValueError(
                f"Invalid word_count format '{self.word_count}'. "
                f"Expected format: 'NNNN-MMMM' (e.g., '4000-6000')"
            )

        if not isinstance(self.detail_level, DetailLevel):
            raise ValueError(
                f"detail_level must be a DetailLevel enum, got {type(self.detail_level)}"
            )

    @staticmethod
    def _is_valid_word_count_format(word_count: str) -> bool:
        """Validate word count format.

        Purpose:
            Check if word_count matches expected pattern "NNNN-MMMM".

        Args:
            word_count: String to validate.

        Returns:
            bool: True if format is valid, False otherwise.

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        import re

        pattern = r"^\d{3,5}-\d{3,5}$"
        return bool(re.match(pattern, word_count))

    def requires_stepwise_guidance(self) -> bool:
        """Check if request requires step-by-step guidance.

        Purpose:
            Business rule: Determine if stepwise template should be used.

        Returns:
            bool: True if stepwise detail level is requested.

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        return self.detail_level == DetailLevel.STEPWISE

    def is_high_priority(self) -> bool:
        """Check if request has high or critical priority.

        Purpose:
            Business rule: Identify priority requests for special handling.

        Returns:
            bool: True if priority is "critical" or "high".

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        return self.priority.lower() in ("critical", "high")

    def has_custom_requirements(self) -> bool:
        """Check if custom requirements are specified.

        Purpose:
            Business rule: Determine if additional constraints need processing.

        Returns:
            bool: True if custom_requirements list is non-empty.

        Preconditions:
            None.

        Side Effects:
            None.

        Exceptions:
            None.
        """
        return self.custom_requirements is not None and len(self.custom_requirements) > 0

    @classmethod
    def create_default(cls, genre: str = "fantasy") -> "WritingRequest":
        """Factory method for creating request with default values.

        Purpose:
            Provide convenient construction of standard requests.

        Args:
            genre: Target narrative genre (defaults to "fantasy").

        Returns:
            WritingRequest: Instance with sensible defaults.

        Preconditions:
            Genre must be non-empty.

        Side Effects:
            None.

        Exceptions:
            ValueError: If genre is empty or invalid.
        """
        return cls(
            genre=genre,
            word_count="4000-6000",
            viewpoint="三人称単元視点",
            viewpoint_character="主人公",
            difficulty="beginner",
            priority="critical",
            detail_level=DetailLevel.STANDARD,
        )
