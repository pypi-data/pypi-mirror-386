# File: tests/contracts/test_corpus_repository_contract.py
# Purpose: Contract tests for ICorpusRepository Protocol
# Context: Validates that any implementation of ICorpusRepository satisfies the expected interface

"""
Contract tests for ICorpusRepository.

These tests ensure that any implementation of ICorpusRepository adheres to the Protocol's contract:
- save_corpus_sample(): Creates and returns sample ID
- load_corpus(): Retrieves samples matching genre/audience
- get_corpus_metrics(): Retrieves cached metrics (or None)
- update_corpus_metrics(): Stores computed metrics
"""

import pytest
from pathlib import Path
from typing import Optional
from datetime import datetime
from noveler.domain.protocols.corpus_repository_protocol import ICorpusRepository


# Minimal in-memory implementation for contract testing
class InMemoryCorpusRepository:
    """Minimal in-memory implementation for contract validation."""

    def __init__(self):
        self._samples: dict[str, dict] = {}
        self._metrics: dict[str, dict] = {}

    def save_corpus_sample(
        self,
        genre: str,
        target_audience: str,
        manuscript_path: Path,
        metadata: dict,
        project_root: Optional[Path] = None
    ) -> str:
        """Save a corpus sample and return its ID."""
        sample_id = f"sample_{len(self._samples) + 1:04d}"
        self._samples[sample_id] = {
            "genre": genre,
            "target_audience": target_audience,
            "manuscript_path": manuscript_path,
            "metadata": metadata,
            "created_at": datetime.now().isoformat()
        }
        return sample_id

    def load_corpus(
        self,
        genre: str,
        target_audience: str,
        project_root: Optional[Path] = None,
        limit: int = 100
    ) -> list[dict]:
        """Load corpus samples matching genre/audience."""
        matches = [
            sample for sample in self._samples.values()
            if sample["genre"] == genre and sample["target_audience"] == target_audience
        ]
        return matches[:limit]

    def get_corpus_metrics(
        self,
        genre: str,
        target_audience: str,
        project_root: Optional[Path] = None
    ) -> Optional[dict]:
        """Get cached corpus metrics."""
        cache_key = f"{genre}_{target_audience}"
        return self._metrics.get(cache_key)

    def update_corpus_metrics(
        self,
        genre: str,
        target_audience: str,
        metrics: dict,
        project_root: Optional[Path] = None
    ) -> None:
        """Update cached corpus metrics."""
        cache_key = f"{genre}_{target_audience}"
        self._metrics[cache_key] = {
            **metrics,
            "updated_at": datetime.now().isoformat()
        }


@pytest.fixture
def corpus_repo():
    """Provide an in-memory corpus repository for testing."""
    return InMemoryCorpusRepository()


class TestCorpusRepositoryContract:
    """Contract tests for ICorpusRepository Protocol."""

    def test_save_corpus_sample_returns_string_id(self, corpus_repo, tmp_path):
        """Contract: save_corpus_sample must return a non-empty string ID."""
        manuscript_path = tmp_path / "sample.txt"
        manuscript_path.write_text("Sample manuscript", encoding="utf-8")

        sample_id = corpus_repo.save_corpus_sample(
            genre="fantasy",
            target_audience="young_adult",
            manuscript_path=manuscript_path,
            metadata={"word_count": 1000},
            project_root=tmp_path
        )

        assert isinstance(sample_id, str), "save_corpus_sample must return string ID"
        assert len(sample_id) > 0, "Sample ID must not be empty"

    def test_load_corpus_returns_list(self, corpus_repo, tmp_path):
        """Contract: load_corpus must return a list (possibly empty)."""
        # Save a sample first
        manuscript_path = tmp_path / "sample.txt"
        manuscript_path.write_text("Sample", encoding="utf-8")
        corpus_repo.save_corpus_sample(
            genre="fantasy",
            target_audience="young_adult",
            manuscript_path=manuscript_path,
            metadata={},
            project_root=tmp_path
        )

        # Load corpus
        results = corpus_repo.load_corpus(
            genre="fantasy",
            target_audience="young_adult",
            project_root=tmp_path
        )

        assert isinstance(results, list), "load_corpus must return a list"
        assert len(results) > 0, "Should find at least one saved sample"

    def test_load_corpus_respects_limit(self, corpus_repo, tmp_path):
        """Contract: load_corpus must respect limit parameter."""
        # Save multiple samples
        manuscript_path = tmp_path / "sample.txt"
        manuscript_path.write_text("Sample", encoding="utf-8")

        for i in range(5):
            corpus_repo.save_corpus_sample(
                genre="fantasy",
                target_audience="young_adult",
                manuscript_path=manuscript_path,
                metadata={"index": i},
                project_root=tmp_path
            )

        # Load with limit
        results = corpus_repo.load_corpus(
            genre="fantasy",
            target_audience="young_adult",
            project_root=tmp_path,
            limit=3
        )

        assert len(results) <= 3, "load_corpus must respect limit parameter"

    def test_get_corpus_metrics_returns_none_or_dict(self, corpus_repo, tmp_path):
        """Contract: get_corpus_metrics must return None or dict."""
        result = corpus_repo.get_corpus_metrics(
            genre="fantasy",
            target_audience="young_adult",
            project_root=tmp_path
        )

        assert result is None or isinstance(result, dict), \
            "get_corpus_metrics must return None or dict"

    def test_update_corpus_metrics_accepts_dict(self, corpus_repo, tmp_path):
        """Contract: update_corpus_metrics must accept dict and store it."""
        metrics = {
            "avg_sentence_length": 15.5,
            "p50_sentence_length": 14,
            "dialogue_ratio": 0.45
        }

        # Should not raise exception
        corpus_repo.update_corpus_metrics(
            genre="fantasy",
            target_audience="young_adult",
            metrics=metrics,
            project_root=tmp_path
        )

        # Verify storage
        retrieved = corpus_repo.get_corpus_metrics(
            genre="fantasy",
            target_audience="young_adult",
            project_root=tmp_path
        )

        assert retrieved is not None, "Metrics should be retrievable after update"
        assert "avg_sentence_length" in retrieved, "Metrics should contain saved data"

    def test_empty_corpus_returns_empty_list(self, corpus_repo, tmp_path):
        """Contract: load_corpus on empty corpus must return empty list, not None."""
        results = corpus_repo.load_corpus(
            genre="nonexistent_genre",
            target_audience="nonexistent_audience",
            project_root=tmp_path
        )

        assert isinstance(results, list), "Must return list even when empty"
        assert len(results) == 0, "Should return empty list for nonexistent genre"

    def test_corpus_filtering_by_genre_and_audience(self, corpus_repo, tmp_path):
        """Contract: load_corpus must filter by both genre AND audience."""
        manuscript_path = tmp_path / "sample.txt"
        manuscript_path.write_text("Sample", encoding="utf-8")

        # Save samples with different genre/audience combinations
        corpus_repo.save_corpus_sample(
            genre="fantasy",
            target_audience="young_adult",
            manuscript_path=manuscript_path,
            metadata={"label": "match"},
            project_root=tmp_path
        )
        corpus_repo.save_corpus_sample(
            genre="fantasy",
            target_audience="adult",
            manuscript_path=manuscript_path,
            metadata={"label": "wrong_audience"},
            project_root=tmp_path
        )
        corpus_repo.save_corpus_sample(
            genre="scifi",
            target_audience="young_adult",
            manuscript_path=manuscript_path,
            metadata={"label": "wrong_genre"},
            project_root=tmp_path
        )

        # Load with specific filter
        results = corpus_repo.load_corpus(
            genre="fantasy",
            target_audience="young_adult",
            project_root=tmp_path
        )

        assert len(results) == 1, "Should only match both genre AND audience"
        assert results[0]["metadata"]["label"] == "match", "Should return correct sample"


@pytest.mark.spec("SPEC-QUALITY-140")
class TestCorpusRepositorySpecCompliance:
    """Verify compliance with SPEC-QUALITY-140 requirements."""

    def test_corpus_repository_contract_coverage(self):
        """SPEC-QUALITY-140: Verify all required methods are defined in Protocol."""
        from noveler.domain.protocols.corpus_repository_protocol import ICorpusRepository

        required_methods = [
            "save_corpus_sample",
            "load_corpus",
            "get_corpus_metrics",
            "update_corpus_metrics"
        ]

        for method_name in required_methods:
            assert hasattr(ICorpusRepository, method_name), \
                f"ICorpusRepository must define {method_name} method"

    def test_in_memory_implementation_is_valid_protocol(self):
        """Verify that InMemoryCorpusRepository satisfies ICorpusRepository Protocol."""
        repo = InMemoryCorpusRepository()

        # Python's Protocol check is structural (duck typing)
        # We verify by checking all required methods exist
        required_methods = [
            "save_corpus_sample",
            "load_corpus",
            "get_corpus_metrics",
            "update_corpus_metrics"
        ]

        for method_name in required_methods:
            assert hasattr(repo, method_name), \
                f"Implementation must have {method_name} method"
            assert callable(getattr(repo, method_name)), \
                f"{method_name} must be callable"
