"""Application.services.analytics_service

Analytics service interface for application layer.
Abstracts analytics operations without depending on presentation UI.
"""

from pathlib import Path
from typing import Protocol


class IAnalyticsService(Protocol):
    """Analytics service interface.

    Provides analytics capabilities without presentation layer dependency.
    Implementations may use UI systems, data pipelines, or background analyzers.
    """

    def generate_writing_analytics_report(
        self, episode_number: int | None = None
    ) -> dict:
        """Generate writing analytics report.

        Args:
            episode_number: Target episode number. If None, analyze all episodes.

        Returns:
            dict: Analytics report with statistics, trends, insights, etc.
        """
        ...

    def get_writing_statistics(self) -> dict:
        """Get writing statistics summary.

        Returns:
            dict: Statistics including word counts, completion rates, etc.
        """
        ...

    def track_writing_progress(self, episode_number: int) -> dict:
        """Track writing progress for specific episode.

        Args:
            episode_number: Target episode number.

        Returns:
            dict: Progress information with status, milestones, etc.
        """
        ...


class NullAnalyticsService:
    """Null object implementation for testing/fallback."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root

    def generate_writing_analytics_report(
        self, episode_number: int | None = None
    ) -> dict:
        return {
            "status": "not_implemented",
            "message": "Analytics service not available",
        }

    def get_writing_statistics(self) -> dict:
        return {
            "status": "not_implemented",
            "message": "Statistics service not available",
        }

    def track_writing_progress(self, episode_number: int) -> dict:
        return {
            "status": "not_implemented",
            "message": "Progress tracking not available",
        }
