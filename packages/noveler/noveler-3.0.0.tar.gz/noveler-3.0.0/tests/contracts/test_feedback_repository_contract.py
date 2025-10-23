# File: tests/contracts/test_feedback_repository_contract.py
# Purpose: Contract tests for IFeedbackRepository Protocol
# Context: Validates that any implementation of IFeedbackRepository satisfies the expected interface

"""
Contract tests for IFeedbackRepository.

These tests ensure that any implementation of IFeedbackRepository adheres to the Protocol's contract:
- save_feedback(): Stores feedback and returns ID
- load_recent_feedback(): Retrieves recent feedback with limit
- query_feedback(): Filters by outcome/source
- get_feedback_statistics(): Returns aggregate metrics
- delete_feedback(): Removes feedback by ID
"""

import pytest
from pathlib import Path
from typing import Optional
from datetime import datetime


# Minimal in-memory implementation for contract testing
class InMemoryFeedbackRepository:
    """Minimal in-memory implementation for contract validation."""

    def __init__(self):
        self._feedback: dict[str, dict] = {}

    def save_feedback(
        self,
        feedback: dict,
        project_root: Optional[Path] = None
    ) -> str:
        """Save evaluation feedback and return its ID."""
        feedback_id = f"feedback_{len(self._feedback) + 1:04d}"
        self._feedback[feedback_id] = {
            **feedback,
            "id": feedback_id,
            "created_at": datetime.now().isoformat()
        }
        return feedback_id

    def load_recent_feedback(
        self,
        project_root: Optional[Path] = None,
        limit: int = 50
    ) -> list[dict]:
        """Load recent feedback (newest first)."""
        all_feedback = list(self._feedback.values())
        # Sort by created_at descending (newest first)
        all_feedback.sort(key=lambda x: x["created_at"], reverse=True)
        return all_feedback[:limit]

    def query_feedback(
        self,
        outcome: Optional[str] = None,
        source: Optional[str] = None,
        project_root: Optional[Path] = None,
        limit: int = 100
    ) -> list[dict]:
        """Query feedback with filters."""
        results = list(self._feedback.values())

        if outcome is not None:
            results = [f for f in results if f.get("outcome") == outcome]

        if source is not None:
            results = [f for f in results if f.get("source") == source]

        return results[:limit]

    def get_feedback_statistics(
        self,
        project_root: Optional[Path] = None
    ) -> dict:
        """Get aggregate feedback statistics."""
        total = len(self._feedback)
        outcomes = {}
        sources = {}

        for feedback in self._feedback.values():
            outcome = feedback.get("outcome", "UNKNOWN")
            source = feedback.get("source", "UNKNOWN")

            outcomes[outcome] = outcomes.get(outcome, 0) + 1
            sources[source] = sources.get(source, 0) + 1

        return {
            "total_feedback": total,
            "outcomes": outcomes,
            "sources": sources
        }

    def delete_feedback(
        self,
        feedback_id: str,
        project_root: Optional[Path] = None
    ) -> bool:
        """Delete feedback by ID. Returns True if deleted, False if not found."""
        if feedback_id in self._feedback:
            del self._feedback[feedback_id]
            return True
        return False


@pytest.fixture
def feedback_repo():
    """Provide an in-memory feedback repository for testing."""
    return InMemoryFeedbackRepository()


class TestFeedbackRepositoryContract:
    """Contract tests for IFeedbackRepository Protocol."""

    def test_save_feedback_returns_string_id(self, feedback_repo, tmp_path):
        """Contract: save_feedback must return a non-empty string ID."""
        feedback = {
            "episode_number": 1,
            "outcome": "PASS",
            "source": "AUTOMATED",
            "automated_scores": {"rhythm": 85.0, "readability": 90.0}
        }

        feedback_id = feedback_repo.save_feedback(
            feedback=feedback,
            project_root=tmp_path
        )

        assert isinstance(feedback_id, str), "save_feedback must return string ID"
        assert len(feedback_id) > 0, "Feedback ID must not be empty"

    def test_load_recent_feedback_returns_list(self, feedback_repo, tmp_path):
        """Contract: load_recent_feedback must return a list."""
        # Save some feedback
        for i in range(3):
            feedback_repo.save_feedback(
                feedback={"episode_number": i, "outcome": "PASS"},
                project_root=tmp_path
            )

        results = feedback_repo.load_recent_feedback(project_root=tmp_path)

        assert isinstance(results, list), "load_recent_feedback must return a list"
        assert len(results) == 3, "Should return all saved feedback"

    def test_load_recent_feedback_respects_limit(self, feedback_repo, tmp_path):
        """Contract: load_recent_feedback must respect limit parameter."""
        # Save multiple feedback entries
        for i in range(10):
            feedback_repo.save_feedback(
                feedback={"episode_number": i, "outcome": "PASS"},
                project_root=tmp_path
            )

        results = feedback_repo.load_recent_feedback(
            project_root=tmp_path,
            limit=5
        )

        assert len(results) <= 5, "load_recent_feedback must respect limit"

    def test_query_feedback_filters_by_outcome(self, feedback_repo, tmp_path):
        """Contract: query_feedback must filter by outcome."""
        # Save feedback with different outcomes
        feedback_repo.save_feedback(
            feedback={"episode_number": 1, "outcome": "PASS"},
            project_root=tmp_path
        )
        feedback_repo.save_feedback(
            feedback={"episode_number": 2, "outcome": "FAIL"},
            project_root=tmp_path
        )
        feedback_repo.save_feedback(
            feedback={"episode_number": 3, "outcome": "PASS"},
            project_root=tmp_path
        )

        # Query for PASS only
        results = feedback_repo.query_feedback(
            outcome="PASS",
            project_root=tmp_path
        )

        assert len(results) == 2, "Should return only matching outcomes"
        assert all(f["outcome"] == "PASS" for f in results), "All results must match filter"

    def test_query_feedback_filters_by_source(self, feedback_repo, tmp_path):
        """Contract: query_feedback must filter by source."""
        # Save feedback with different sources
        feedback_repo.save_feedback(
            feedback={"episode_number": 1, "source": "AUTOMATED"},
            project_root=tmp_path
        )
        feedback_repo.save_feedback(
            feedback={"episode_number": 2, "source": "MANUAL"},
            project_root=tmp_path
        )

        # Query for AUTOMATED only
        results = feedback_repo.query_feedback(
            source="AUTOMATED",
            project_root=tmp_path
        )

        assert len(results) == 1, "Should return only matching sources"
        assert results[0]["source"] == "AUTOMATED", "Result must match source filter"

    def test_get_feedback_statistics_returns_dict(self, feedback_repo, tmp_path):
        """Contract: get_feedback_statistics must return a dict with aggregate data."""
        # Save some feedback
        for i in range(5):
            feedback_repo.save_feedback(
                feedback={"episode_number": i, "outcome": "PASS", "source": "AUTOMATED"},
                project_root=tmp_path
            )

        stats = feedback_repo.get_feedback_statistics(project_root=tmp_path)

        assert isinstance(stats, dict), "get_feedback_statistics must return dict"
        assert "total_feedback" in stats, "Must include total_feedback count"
        assert stats["total_feedback"] == 5, "Total should match saved count"

    def test_delete_feedback_returns_bool(self, feedback_repo, tmp_path):
        """Contract: delete_feedback must return bool (True if deleted, False if not found)."""
        # Save a feedback entry
        feedback_id = feedback_repo.save_feedback(
            feedback={"episode_number": 1, "outcome": "PASS"},
            project_root=tmp_path
        )

        # Delete existing feedback
        result = feedback_repo.delete_feedback(
            feedback_id=feedback_id,
            project_root=tmp_path
        )
        assert result is True, "delete_feedback must return True when successful"

        # Try deleting non-existent feedback
        result = feedback_repo.delete_feedback(
            feedback_id="nonexistent",
            project_root=tmp_path
        )
        assert result is False, "delete_feedback must return False when ID not found"

    def test_empty_repository_returns_empty_list(self, feedback_repo, tmp_path):
        """Contract: load_recent_feedback on empty repository must return empty list."""
        results = feedback_repo.load_recent_feedback(project_root=tmp_path)

        assert isinstance(results, list), "Must return list even when empty"
        assert len(results) == 0, "Should return empty list for empty repository"

    def test_query_without_filters_returns_all(self, feedback_repo, tmp_path):
        """Contract: query_feedback without filters must return all feedback."""
        # Save feedback
        for i in range(3):
            feedback_repo.save_feedback(
                feedback={"episode_number": i, "outcome": "PASS"},
                project_root=tmp_path
            )

        # Query without filters
        results = feedback_repo.query_feedback(project_root=tmp_path)

        assert len(results) == 3, "Should return all feedback when no filters applied"


@pytest.mark.spec("SPEC-QUALITY-140")
class TestFeedbackRepositorySpecCompliance:
    """Verify compliance with SPEC-QUALITY-140 requirements."""

    def test_feedback_repository_contract_coverage(self):
        """SPEC-QUALITY-140: Verify all required methods are defined in Protocol."""
        from noveler.domain.protocols.feedback_repository_protocol import IFeedbackRepository

        required_methods = [
            "save_feedback",
            "load_recent_feedback",
            "query_feedback",
            "get_feedback_statistics",
            "delete_feedback"
        ]

        for method_name in required_methods:
            assert hasattr(IFeedbackRepository, method_name), \
                f"IFeedbackRepository must define {method_name} method"

    def test_in_memory_implementation_is_valid_protocol(self):
        """Verify that InMemoryFeedbackRepository satisfies IFeedbackRepository Protocol."""
        repo = InMemoryFeedbackRepository()

        required_methods = [
            "save_feedback",
            "load_recent_feedback",
            "query_feedback",
            "get_feedback_statistics",
            "delete_feedback"
        ]

        for method_name in required_methods:
            assert hasattr(repo, method_name), \
                f"Implementation must have {method_name} method"
            assert callable(getattr(repo, method_name)), \
                f"{method_name} must be callable"
