"""Application.services.batch_processing_service

Batch processing service interface for application layer.
Abstracts batch operations without depending on presentation UI.
"""

from pathlib import Path
from typing import Protocol


class IBatchProcessingService(Protocol):
    """Batch processing service interface.

    Provides batch operation capabilities without presentation layer dependency.
    Implementations may delegate to UI systems, CLI tools, or background workers.
    """

    def process_all_episodes_batch(self, *, dry_run: bool = True) -> dict:
        """Process all episodes in batch mode.

        Args:
            dry_run: If True, perform validation only without applying changes.

        Returns:
            dict: Processing results with status, processed_count, errors, etc.
        """
        ...

    def fix_all_episodes_batch(self, *, dry_run: bool = True) -> dict:
        """Fix all episodes in batch mode.

        Args:
            dry_run: If True, show planned fixes without applying them.

        Returns:
            dict: Fix results with status, fixed_count, errors, etc.
        """
        ...

    def validate_all_episodes_batch(self) -> dict:
        """Validate all episodes in batch mode.

        Returns:
            dict: Validation results with status, valid_count, issues, etc.
        """
        ...


class NullBatchProcessingService:
    """Null object implementation for testing/fallback."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root

    def process_all_episodes_batch(self, *, dry_run: bool = True) -> dict:
        return {
            "status": "not_implemented",
            "message": "Batch processing service not available",
        }

    def fix_all_episodes_batch(self, *, dry_run: bool = True) -> dict:
        return {
            "status": "not_implemented",
            "message": "Batch fix service not available",
        }

    def validate_all_episodes_batch(self) -> dict:
        return {
            "status": "not_implemented",
            "message": "Batch validation service not available",
        }
