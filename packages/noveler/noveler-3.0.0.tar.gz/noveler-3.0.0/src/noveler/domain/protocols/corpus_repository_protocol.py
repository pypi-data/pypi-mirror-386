# File: src/noveler/domain/protocols/corpus_repository_protocol.py
# Purpose: Protocol definition for corpus repository
# Context: Define interface for corpus data access in ML quality optimization

"""
Corpus Repository Protocol.

This protocol defines the interface for accessing and managing corpus data
(similar works used for ML baseline extraction).

Contract: SPEC-QUALITY-140 §6.2.1
"""

from pathlib import Path
from typing import Optional, Protocol


class CorpusSample:
    """
    A single corpus sample (similar work excerpt).

    Attributes:
        sample_id: Unique identifier
        genre: Genre classification
        target_audience: Target audience classification
        text: Sample text content
        metadata: Additional metadata (author, publication date, etc.)
    """
    def __init__(
        self,
        sample_id: str,
        genre: str,
        target_audience: str,
        text: str,
        metadata: Optional[dict] = None
    ):
        self.sample_id = sample_id
        self.genre = genre
        self.target_audience = target_audience
        self.text = text
        self.metadata = metadata or {}


class ICorpusRepository(Protocol):
    """
    Protocol for corpus data repository.

    This protocol defines methods for accessing and managing corpus samples
    used in ML-based quality optimization.

    Implementations:
    - YamlCorpusRepository: File-based corpus storage
    - SQLiteCorpusRepository: Database-based corpus storage (future)

    Contract: SPEC-QUALITY-140 §6.2.1
    """

    def save_corpus_sample(
        self,
        genre: str,
        target_audience: str,
        sample_text: str,
        metadata: dict,
        project_root: Path
    ) -> str:
        """
        Save a corpus sample and return sample_id.

        Args:
            genre: Genre classification (fantasy, mystery, romance, etc.)
            target_audience: Target audience (young_adult, adult, general)
            sample_text: Sample text content
            metadata: Additional metadata (author, source, etc.)
            project_root: Project root for corpus resolution

        Returns:
            sample_id: Unique identifier for saved sample

        Raises:
            CorpusSaveError: If save operation fails
        """
        ...

    def load_corpus(
        self,
        genre: str,
        target_audience: str,
        project_root: Path,
        limit: Optional[int] = None
    ) -> list[CorpusSample]:
        """
        Load corpus samples for a genre and audience.

        Args:
            genre: Genre classification
            target_audience: Target audience
            project_root: Project root for corpus resolution
            limit: Maximum number of samples to load (None = all)

        Returns:
            List of CorpusSample objects

        Raises:
            CorpusNotFoundError: If corpus not found
        """
        ...

    def get_corpus_metrics(
        self,
        genre: str,
        target_audience: str,
        project_root: Path
    ) -> Optional[dict]:
        """
        Retrieve pre-computed corpus metrics.

        This is an optimization to avoid re-computing metrics on every request.

        Args:
            genre: Genre classification
            target_audience: Target audience
            project_root: Project root for corpus resolution

        Returns:
            Pre-computed corpus metrics dict, or None if not available

        Note:
            If metrics are not pre-computed, callers should use
            CorpusAnalyzer.build_baseline_metrics() to compute them.
        """
        ...

    def update_corpus_metrics(
        self,
        genre: str,
        target_audience: str,
        metrics: dict,
        project_root: Path
    ) -> None:
        """
        Update (cache) computed corpus metrics.

        This allows CorpusAnalyzer to store computed metrics for future retrieval.

        Args:
            genre: Genre classification
            target_audience: Target audience
            metrics: Computed corpus metrics to cache
            project_root: Project root for corpus resolution

        Raises:
            CorpusUpdateError: If update operation fails

        Note:
            Cached metrics should include a timestamp for TTL management.
        """
        ...

    def delete_corpus_sample(
        self,
        sample_id: str,
        project_root: Path
    ) -> bool:
        """
        Delete a corpus sample by ID.

        Args:
            sample_id: Sample identifier
            project_root: Project root for corpus resolution

        Returns:
            True if deleted, False if not found

        Raises:
            CorpusDeleteError: If delete operation fails
        """
        ...
