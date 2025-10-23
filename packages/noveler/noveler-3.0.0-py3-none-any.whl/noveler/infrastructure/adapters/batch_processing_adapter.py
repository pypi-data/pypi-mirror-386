"""Infrastructure.adapters.batch_processing_adapter

Adapter implementation wrapping presentation UI BatchProcessingSystem.
Isolates presentation layer dependency from application/domain layers.
"""

from pathlib import Path

from noveler.infrastructure.logging.unified_logger import get_logger


class BatchProcessingAdapter:
    """Adapter for batch processing operations.

    Wraps presentation.ui.batch_processor.BatchProcessingSystem
    to provide DDD-compliant service interface.
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.logger = get_logger(__name__)
        self._batch_system = None

    def _get_batch_system(self):
        """Lazy-load batch processing system to avoid circular imports."""
        if self._batch_system is None:
            try:
                from noveler.presentation.ui.batch_processor import (
                    BatchProcessingSystem,
                )

                self._batch_system = BatchProcessingSystem(self.project_root)
            except ImportError as e:
                self.logger.warning(
                    f"BatchProcessingSystem not available: {e}. Using null implementation."
                )
                from noveler.application.services.batch_processing_service import (
                    NullBatchProcessingService,
                )

                self._batch_system = NullBatchProcessingService(self.project_root)
        return self._batch_system

    def process_all_episodes_batch(self, *, dry_run: bool = True) -> dict:
        """Process all episodes in batch mode.

        Args:
            dry_run: If True, perform validation only without applying changes.

        Returns:
            dict: Processing results with status, processed_count, errors, etc.
        """
        try:
            system = self._get_batch_system()
            return system.process_all_episodes_batch(dry_run=dry_run)
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            return {"status": "error", "message": str(e)}

    def fix_all_episodes_batch(self, *, dry_run: bool = True) -> dict:
        """Fix all episodes in batch mode.

        Args:
            dry_run: If True, show planned fixes without applying them.

        Returns:
            dict: Fix results with status, fixed_count, errors, etc.
        """
        try:
            system = self._get_batch_system()
            return system.fix_all_episodes_batch(dry_run=dry_run)
        except Exception as e:
            self.logger.error(f"Batch fix failed: {e}")
            return {"status": "error", "message": str(e)}

    def validate_all_episodes_batch(self) -> dict:
        """Validate all episodes in batch mode.

        Returns:
            dict: Validation results with status, valid_count, issues, etc.
        """
        try:
            system = self._get_batch_system()
            return system.validate_all_episodes_batch()
        except Exception as e:
            self.logger.error(f"Batch validation failed: {e}")
            return {"status": "error", "message": str(e)}
