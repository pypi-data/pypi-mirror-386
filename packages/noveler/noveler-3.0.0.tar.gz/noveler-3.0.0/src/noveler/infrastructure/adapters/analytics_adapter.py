"""Infrastructure.adapters.analytics_adapter

Adapter implementation wrapping presentation UI WritingAnalyticsSystem.
Isolates presentation layer dependency from application/domain layers.
"""

from pathlib import Path

from noveler.infrastructure.logging.unified_logger import get_logger


class AnalyticsAdapter:
    """Adapter for analytics operations.

    Wraps presentation.ui.analytics_system.WritingAnalyticsSystem
    to provide DDD-compliant service interface.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.logger = get_logger(__name__)
        self._analytics_system = None

    def _get_analytics_system(self):
        """Lazy-load analytics system to avoid circular imports."""
        if self._analytics_system is None:
            try:
                from noveler.presentation.ui.analytics_system import (
                    WritingAnalyticsSystem,
                )

                self._analytics_system = WritingAnalyticsSystem(self.project_root)
            except ImportError as e:
                self.logger.warning(
                    f"WritingAnalyticsSystem not available: {e}. Using null implementation."
                )
                from noveler.application.services.analytics_service import (
                    NullAnalyticsService,
                )

                self._analytics_system = NullAnalyticsService(self.project_root)
        return self._analytics_system

    def generate_writing_analytics_report(
        self, episode_number: int | None = None
    ) -> dict:
        """Generate writing analytics report.

        Args:
            episode_number: Target episode number. If None, analyze all episodes.

        Returns:
            dict: Analytics report with statistics, trends, insights, etc.
        """
        try:
            system = self._get_analytics_system()
            return system.generate_writing_analytics_report(episode_number)
        except Exception as e:
            self.logger.error(f"Analytics report generation failed: {e}")
            return {"status": "error", "message": str(e)}

    def get_writing_statistics(self) -> dict:
        """Get writing statistics summary.

        Returns:
            dict: Statistics including word counts, completion rates, etc.
        """
        try:
            system = self._get_analytics_system()
            return system.get_writing_statistics()
        except Exception as e:
            self.logger.error(f"Statistics retrieval failed: {e}")
            return {"status": "error", "message": str(e)}

    def track_writing_progress(self, episode_number: int) -> dict:
        """Track writing progress for specific episode.

        Args:
            episode_number: Target episode number.

        Returns:
            dict: Progress information with status, milestones, etc.
        """
        try:
            system = self._get_analytics_system()
            return system.track_writing_progress(episode_number)
        except Exception as e:
            self.logger.error(f"Progress tracking failed: {e}")
            return {"status": "error", "message": str(e)}
