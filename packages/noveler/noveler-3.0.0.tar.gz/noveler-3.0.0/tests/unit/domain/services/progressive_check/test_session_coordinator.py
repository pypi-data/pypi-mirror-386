# File: tests/unit/domain/services/progressive_check/test_session_coordinator.py
# Purpose: Unit tests for SessionCoordinator
# Context: Phase 6 Step 1 - Session management extraction

"""Unit tests for SessionCoordinator."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock

import pytest

from noveler.domain.interfaces.logger_interface import NullLogger
from noveler.domain.services.progressive_check.session_coordinator import SessionCoordinator


class MockStateRepository:
    """Mock implementation of IStateRepository."""

    def __init__(self) -> None:
        self.states: dict[tuple[str, int], dict[str, Any]] = {}

    def load_state(self, session_id: str, episode_number: int) -> dict[str, Any] | None:
        return self.states.get((session_id, episode_number))

    def save_state(self, session_id: str, episode_number: int, state: dict[str, Any]) -> None:
        self.states[(session_id, episode_number)] = state

    def state_exists(self, session_id: str, episode_number: int) -> bool:
        return (session_id, episode_number) in self.states


class MockManifestRepository:
    """Mock implementation of IManifestRepository."""

    def __init__(self) -> None:
        self.manifests: dict[str, dict[str, Any]] = {}

    def load_manifest(self, session_id: str) -> dict[str, Any] | None:
        return self.manifests.get(session_id)

    def save_manifest(self, session_id: str, manifest: dict[str, Any]) -> None:
        self.manifests[session_id] = manifest

    def manifest_exists(self, session_id: str) -> bool:
        return session_id in self.manifests


@pytest.fixture
def temp_project_root(tmp_path: Path) -> Path:
    """Create temporary project root with necessary directories."""
    checks_dir = tmp_path / ".noveler" / "checks" / "EP0001" / "io"
    checks_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture
def mock_state_repo() -> MockStateRepository:
    """Create mock state repository."""
    return MockStateRepository()


@pytest.fixture
def mock_manifest_repo() -> MockManifestRepository:
    """Create mock manifest repository."""
    return MockManifestRepository()


@pytest.fixture
def session_coordinator(
    temp_project_root: Path,
    mock_state_repo: MockStateRepository,
    mock_manifest_repo: MockManifestRepository,
) -> SessionCoordinator:
    """Create SessionCoordinator instance for testing."""
    return SessionCoordinator(
        project_root=temp_project_root,
        episode_number=1,
        session_id="20251004120000000000",
        state_repository=mock_state_repo,
        manifest_repository=mock_manifest_repo,
        logger=NullLogger(),
    )


class TestSessionCoordinatorInitialization:
    """Tests for SessionCoordinator initialization."""

    def test_init_creates_session_id_if_none(
        self,
        temp_project_root: Path,
        mock_state_repo: MockStateRepository,
        mock_manifest_repo: MockManifestRepository,
    ) -> None:
        """Test that session ID is auto-generated if not provided."""
        coordinator = SessionCoordinator(
            project_root=temp_project_root,
            episode_number=1,
            session_id=None,
            state_repository=mock_state_repo,
            manifest_repository=mock_manifest_repo,
        )

        assert coordinator.session_id is not None
        assert len(coordinator.session_id) > 0
        assert coordinator.session_id.isdigit()

    def test_init_uses_provided_session_id(
        self,
        temp_project_root: Path,
        mock_state_repo: MockStateRepository,
        mock_manifest_repo: MockManifestRepository,
    ) -> None:
        """Test that provided session ID is used."""
        session_id = "20251004120000000000"
        coordinator = SessionCoordinator(
            project_root=temp_project_root,
            episode_number=1,
            session_id=session_id,
            state_repository=mock_state_repo,
            manifest_repository=mock_manifest_repo,
        )

        assert coordinator.session_id == session_id

    def test_init_sets_paths_correctly(self, session_coordinator: SessionCoordinator) -> None:
        """Test that paths are set correctly on initialization."""
        assert session_coordinator.checks_root.name == "checks"
        assert session_coordinator.io_dir.name == "io"
        assert "EP0001" in str(session_coordinator.io_dir)
        assert session_coordinator.manifest_path.name == "manifest.json"


class TestSessionLifecycle:
    """Tests for session lifecycle operations."""

    def test_start_new_session_creates_initial_state(
        self,
        session_coordinator: SessionCoordinator,
        mock_state_repo: MockStateRepository,
    ) -> None:
        """Test that starting a new session creates initial state."""
        state = session_coordinator.initialize_session(resume=False)

        assert state["episode_number"] == 1
        assert state["current_step"] == 1
        assert state["completed_steps"] == []
        assert state["failed_steps"] == []
        assert state["overall_status"] == "not_started"
        assert "created_at" in state
        assert "last_updated" in state

        # Verify state was saved
        assert mock_state_repo.state_exists("20251004120000000000", 1)

    def test_resume_session_loads_existing_state(
        self,
        session_coordinator: SessionCoordinator,
        mock_state_repo: MockStateRepository,
    ) -> None:
        """Test that resuming a session loads existing state."""
        # Pre-populate state
        existing_state = {
            "episode_number": 1,
            "current_step": 3,
            "completed_steps": [1, 2],
            "overall_status": "in_progress",
        }
        mock_state_repo.save_state("20251004120000000000", 1, existing_state)

        # Resume session
        state = session_coordinator.initialize_session(resume=True)

        assert state["current_step"] == 3
        assert state["completed_steps"] == [1, 2]
        assert state["overall_status"] == "in_progress"

    def test_resume_session_raises_if_not_found(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test that resuming non-existent session raises error."""
        with pytest.raises(FileNotFoundError, match="Session state not found"):
            session_coordinator.initialize_session(resume=True)

    def test_can_resume_session_returns_true_if_exists(
        self,
        session_coordinator: SessionCoordinator,
        mock_state_repo: MockStateRepository,
    ) -> None:
        """Test can_resume_session returns True for existing session."""
        mock_state_repo.save_state("20251004120000000000", 1, {"test": "data"})

        assert session_coordinator.can_resume_session("20251004120000000000") is True

    def test_can_resume_session_returns_false_if_not_exists(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test can_resume_session returns False for non-existent session."""
        assert session_coordinator.can_resume_session("nonexistent") is False


class TestStateManagement:
    """Tests for state persistence operations."""

    def test_save_state_persists_to_repository(
        self,
        session_coordinator: SessionCoordinator,
        mock_state_repo: MockStateRepository,
    ) -> None:
        """Test that save_state persists to repository."""
        test_state = {"episode_number": 1, "current_step": 5}

        session_coordinator.save_state(test_state)

        loaded = mock_state_repo.load_state("20251004120000000000", 1)
        assert loaded == test_state

    def test_get_execution_status_returns_correct_info(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test get_execution_status returns correct metadata."""
        current_state = {
            "completed_steps": [1, 2, 3],
            "failed_steps": [4],
            "current_step": 5,
            "overall_status": "in_progress",
        }

        status = session_coordinator.get_execution_status(current_state)

        assert status["session_id"] == "20251004120000000000"
        assert status["episode_number"] == 1
        assert status["completed_steps"] == 3
        assert status["last_completed_step"] == 3
        assert status["overall_status"] == "in_progress"
        assert status["progress"]["completed"] == 3
        assert status["progress"]["failed"] == 1
        assert status["progress"]["current_step"] == 5

    def test_get_execution_status_handles_empty_completed(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test get_execution_status handles empty completed_steps."""
        current_state = {
            "completed_steps": [],
            "overall_status": "not_started",
        }

        status = session_coordinator.get_execution_status(current_state)

        assert status["last_completed_step"] == 0
        assert status["progress"]["completed"] == 0


class TestTimestampManagement:
    """Tests for session timestamp operations."""

    def test_ensure_session_start_ts_generates_if_not_set(
        self,
        session_coordinator: SessionCoordinator,
        mock_manifest_repo: MockManifestRepository,
    ) -> None:
        """Test that ensure_session_start_ts generates timestamps."""
        manifest = {}

        ts, iso = session_coordinator.ensure_session_start_ts(manifest)

        assert ts is not None
        assert iso is not None
        assert len(ts) == 12  # YYYYMMDDHHmm
        assert "T" in iso  # ISO format

        # Verify persisted to manifest
        assert "first_step_started_at" in manifest
        assert manifest["first_step_started_at"]["compact"] == ts
        assert manifest["first_step_started_at"]["iso"] == iso

    def test_ensure_session_start_ts_uses_cached_if_available(
        self,
        session_coordinator: SessionCoordinator,
        mock_manifest_repo: MockManifestRepository,
    ) -> None:
        """Test that cached timestamps are reused."""
        session_coordinator.session_start_ts = "202510041200"
        session_coordinator.session_start_iso = "2025-10-04T12:00:00+00:00"

        manifest = {}
        ts, iso = session_coordinator.ensure_session_start_ts(manifest)

        assert ts == "202510041200"
        assert iso == "2025-10-04T12:00:00+00:00"

    def test_ensure_session_start_ts_parses_from_manifest(
        self,
        session_coordinator: SessionCoordinator,
        mock_manifest_repo: MockManifestRepository,
    ) -> None:
        """Test that timestamps are parsed from manifest."""
        manifest = {
            "first_step_started_at": {
                "compact": "202510041200",
                "iso": "2025-10-04T12:00:00+00:00",
            }
        }

        ts, iso = session_coordinator.ensure_session_start_ts(manifest)

        assert ts == "202510041200"
        assert iso == "2025-10-04T12:00:00+00:00"

    def test_hydrate_session_start_from_manifest(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test hydrating timestamps from manifest."""
        manifest = {
            "first_step_started_at": {
                "compact": "202510041200",
                "iso": "2025-10-04T12:00:00+00:00",
            }
        }

        session_coordinator.hydrate_session_start_from_manifest(manifest)

        assert session_coordinator.session_start_ts == "202510041200"
        assert session_coordinator.session_start_iso == "2025-10-04T12:00:00+00:00"


class TestPreviousSessionMerge:
    """Tests for merging previous session data."""

    def test_merge_previous_session_completion_merges_steps(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test merging completed steps from previous session."""
        current_state = {
            "completed_steps": [3, 4],
            "step_results": {},
        }
        manifest = {
            "previous_session_completed_steps": [1, 2],
        }

        updated_state = session_coordinator.merge_previous_session_completion(
            current_state, manifest
        )

        assert updated_state["completed_steps"] == [1, 2, 3, 4]

    def test_merge_previous_session_completion_merges_results(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test merging step results from manifest history."""
        current_state = {
            "completed_steps": [],
            "step_results": {},
        }
        manifest = {
            "previous_session_completed_steps": [],
            "step_execution_history": {
                "1": {"status": "completed", "result": {"data": "test"}},
                "2": {"status": "completed", "result": {"data": "test2"}},
            },
        }

        updated_state = session_coordinator.merge_previous_session_completion(
            current_state, manifest
        )

        assert "1" in updated_state["step_results"]
        assert updated_state["step_results"]["1"]["status"] == "completed"
        assert updated_state["step_results"]["1"]["result"]["data"] == "test"

    def test_merge_previous_session_completion_handles_missing_data(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test merge handles missing previous session data."""
        current_state = {"completed_steps": [1, 2]}
        manifest = {}  # No previous session data

        updated_state = session_coordinator.merge_previous_session_completion(
            current_state, manifest
        )

        assert updated_state["completed_steps"] == [1, 2]


class TestWorkflowIntegration:
    """Tests for workflow state store integration."""

    def test_initialize_workflow_store_creates_store(
        self,
        temp_project_root: Path,
        mock_state_repo: MockStateRepository,
        mock_manifest_repo: MockManifestRepository,
    ) -> None:
        """Test workflow store initialization."""
        mock_factory = Mock(return_value=Mock())

        coordinator = SessionCoordinator(
            project_root=temp_project_root,
            episode_number=1,
            session_id="test",
            state_repository=mock_state_repo,
            manifest_repository=mock_manifest_repo,
            workflow_state_store_factory=mock_factory,
        )

        coordinator._initialize_workflow_store()

        assert coordinator._workflow_state_store is not None
        mock_factory.assert_called_once()

    def test_ensure_workflow_session_creates_session(
        self,
        temp_project_root: Path,
        mock_state_repo: MockStateRepository,
        mock_manifest_repo: MockManifestRepository,
    ) -> None:
        """Test workflow session creation."""
        mock_store = Mock()
        mock_session = Mock()
        mock_store.create_session.return_value = mock_session
        mock_factory = Mock(return_value=mock_store)

        coordinator = SessionCoordinator(
            project_root=temp_project_root,
            episode_number=1,
            session_id="test",
            state_repository=mock_state_repo,
            manifest_repository=mock_manifest_repo,
            workflow_state_store_factory=mock_factory,
        )

        coordinator._initialize_workflow_store()
        session = coordinator.ensure_workflow_session()

        assert session == mock_session
        mock_store.create_session.assert_called_once_with(
            session_id="test",
            episode_number=1,
        )

    def test_record_step_execution_to_workflow_store(
        self,
        temp_project_root: Path,
        mock_state_repo: MockStateRepository,
        mock_manifest_repo: MockManifestRepository,
    ) -> None:
        """Test recording step execution to workflow store."""
        mock_session = Mock()
        mock_store = Mock()
        mock_store.create_session.return_value = mock_session
        mock_factory = Mock(return_value=mock_store)

        coordinator = SessionCoordinator(
            project_root=temp_project_root,
            episode_number=1,
            session_id="test",
            state_repository=mock_state_repo,
            manifest_repository=mock_manifest_repo,
            workflow_state_store_factory=mock_factory,
        )

        coordinator._initialize_workflow_store()
        coordinator.record_step_execution_to_workflow_store(
            step_id=1,
            execution_data={"test": "data"},
        )

        mock_session.record_step_execution.assert_called_once_with(
            step_id=1,
            data={"test": "data"},
        )

    def test_workflow_operations_handle_no_factory(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test workflow operations handle missing factory gracefully."""
        # No factory provided in fixture
        session_coordinator._initialize_workflow_store()
        assert session_coordinator._workflow_state_store is None

        session = session_coordinator.ensure_workflow_session()
        assert session is None

        # Should not raise
        session_coordinator.record_step_execution_to_workflow_store(
            step_id=1,
            execution_data={},
        )


class TestParseSessionStartRecord:
    """Tests for _parse_session_start_record method (coverage improvement)."""

    def test_parse_iso_format_successfully(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test parsing session start record with ISO format."""
        record = {"iso": "2025-10-04T12:00:00+00:00"}

        result = session_coordinator._parse_session_start_record(record)

        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 10
        assert result.day == 4

    def test_parse_compact_format_successfully(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test parsing session start record with compact format."""
        record = {"compact": "20251004120000000000"}

        result = session_coordinator._parse_session_start_record(record)

        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 10
        assert result.day == 4

    def test_parse_invalid_iso_format_returns_none(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test that invalid ISO format returns None."""
        record = {"iso": "not-a-valid-iso-date"}

        result = session_coordinator._parse_session_start_record(record)

        assert result is None

    def test_parse_invalid_compact_format_returns_none(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test that invalid compact format returns None."""
        record = {"compact": "invalid"}

        result = session_coordinator._parse_session_start_record(record)

        assert result is None

    def test_parse_non_dict_record_returns_none(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test that non-dict record returns None."""
        assert session_coordinator._parse_session_start_record("not a dict") is None
        assert session_coordinator._parse_session_start_record(123) is None
        assert session_coordinator._parse_session_start_record(None) is None
        assert session_coordinator._parse_session_start_record([]) is None

    def test_parse_empty_dict_returns_none(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test that empty dict returns None."""
        result = session_coordinator._parse_session_start_record({})

        assert result is None

    def test_parse_iso_fallback_to_compact(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test that parsing falls back to compact when ISO fails."""
        record = {"iso": "invalid-iso", "compact": "20251004120000000000"}

        result = session_coordinator._parse_session_start_record(record)

        assert result is not None
        assert result.year == 2025

    def test_parse_non_string_values_returns_none(
        self,
        session_coordinator: SessionCoordinator,
    ) -> None:
        """Test that non-string values in iso/compact return None."""
        assert session_coordinator._parse_session_start_record({"iso": 123}) is None
        assert session_coordinator._parse_session_start_record({"compact": 456}) is None
