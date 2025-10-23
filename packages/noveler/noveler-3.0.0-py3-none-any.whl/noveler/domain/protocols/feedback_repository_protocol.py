# File: src/noveler/domain/protocols/feedback_repository_protocol.py
# Purpose: Protocol definition for quality feedback repository
# Context: Define interface for feedback data access in ML quality optimization

"""
Feedback Repository Protocol.

This protocol defines the interface for accessing and managing quality
feedback data (evaluation results, user corrections, etc.).

Contract: SPEC-QUALITY-140 §6.2.2
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Protocol


class IFeedbackRepository(Protocol):
    """
    Protocol for quality feedback repository.

    This protocol defines methods for accessing and managing feedback records
    used in ML-based quality optimization and weight tuning.

    Implementations:
    - YamlFeedbackRepository: File-based feedback storage
    - SQLiteFeedbackRepository: Database-based feedback storage (future)

    Contract: SPEC-QUALITY-140 §6.2.2
    """

    def save_feedback(
        self,
        feedback: dict,
        project_root: Path
    ) -> str:
        """
        Save feedback record and return feedback_id.

        Args:
            feedback: Feedback dictionary with:
                - episode_number: int
                - evaluation_timestamp: datetime
                - automated_scores: dict[str, float]
                - human_scores: Optional[dict[str, float]]
                - user_corrections: list[dict]
                - outcome: str (PASS, FAIL, MANUAL_OVERRIDE)
                - feedback_source: str (AUTHOR, EDITOR, READER)
            project_root: Project root for feedback resolution

        Returns:
            feedback_id: Unique identifier for saved feedback

        Raises:
            FeedbackSaveError: If save operation fails
        """
        ...

    def load_recent_feedback(
        self,
        project_root: Path,
        limit: int = 50
    ) -> list[dict]:
        """
        Load recent feedback for learning.

        Args:
            project_root: Project root for feedback resolution
            limit: Maximum number of records to load (default: 50)

        Returns:
            List of feedback dictionaries, sorted by timestamp descending

        Raises:
            FeedbackLoadError: If load operation fails
        """
        ...

    def get_feedback_statistics(
        self,
        project_root: Path,
        date_range: Optional[tuple[datetime, datetime]] = None
    ) -> dict:
        """
        Get aggregated feedback statistics.

        Args:
            project_root: Project root for feedback resolution
            date_range: Optional (start_date, end_date) tuple

        Returns:
            Dictionary with:
            - total_evaluations: int
            - avg_automated_score: float
            - avg_human_score: float (if available)
            - false_positive_rate: float
            - false_negative_rate: float
            - user_correction_rate: float

        Raises:
            FeedbackStatisticsError: If statistics computation fails
        """
        ...

    def find_feedback_by_episode(
        self,
        episode_number: int,
        project_root: Path
    ) -> list[dict]:
        """
        Find all feedback records for a specific episode.

        Args:
            episode_number: Episode number
            project_root: Project root for feedback resolution

        Returns:
            List of feedback dictionaries for the episode
        """
        ...

    def query_feedback(
        self,
        outcome: Optional[str] = None,
        source: Optional[str] = None,
        project_root: Optional[Path] = None,
        limit: int = 100
    ) -> list[dict]:
        """
        Query feedback with filters.

        Args:
            outcome: Filter by outcome (PASS, FAIL, etc.)
            source: Filter by source (AUTOMATED, MANUAL, HYBRID)
            project_root: Project root for feedback resolution
            limit: Maximum number of records to return

        Returns:
            List of feedback dictionaries matching filters

        Raises:
            FeedbackQueryError: If query operation fails
        """
        ...

    def delete_feedback(
        self,
        feedback_id: str,
        project_root: Path
    ) -> bool:
        """
        Delete a feedback record by ID.

        Args:
            feedback_id: Feedback identifier
            project_root: Project root for feedback resolution

        Returns:
            True if deleted, False if not found

        Raises:
            FeedbackDeleteError: If delete operation fails
        """
        ...
