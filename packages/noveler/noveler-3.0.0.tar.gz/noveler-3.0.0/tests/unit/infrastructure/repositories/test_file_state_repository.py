# File: tests/unit/infrastructure/repositories/test_file_state_repository.py
# Purpose: Unit and contract tests for FileStateRepository.
# Context: Validates IStateRepository contract compliance and JSON persistence logic.

"""Test suite for FileStateRepository.

Test Coverage:
- Contract tests: Verify IStateRepository protocol compliance
- Unit tests: Test JSON file I/O, error handling, atomicity
- Edge cases: Corrupted files, missing directories, race conditions

SPEC-901: Contract tests ensure backward compatibility when refactoring.
B20 Guide §8.2: Minimum 80% coverage required.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from noveler.infrastructure.repositories.file_state_repository import FileStateRepository


class TestFileStateRepositoryContract:
    """Contract tests for IStateRepository protocol compliance.

    These tests ensure FileStateRepository correctly implements the IStateRepository protocol.
    Changes to these tests indicate a breaking contract change (requires major version bump).
    """

    def test_load_or_initialize_returns_dict(self, tmp_path: Path) -> None:
        """Contract: load_or_initialize() must return a dict."""
        repo = FileStateRepository(tmp_path / "state.json")
        default = {"session_id": "test", "completed_steps": []}

        result = repo.load_or_initialize(default)

        assert isinstance(result, dict), "load_or_initialize must return dict"

    def test_save_accepts_dict(self, tmp_path: Path) -> None:
        """Contract: save() must accept dict without raising."""
        repo = FileStateRepository(tmp_path / "state.json")
        state = {"session_id": "test", "completed_steps": [1, 2]}

        # Should not raise
        repo.save(state)

    def test_protocol_method_signatures(self) -> None:
        """Contract: FileStateRepository has all IStateRepository methods."""
        repo_class = FileStateRepository

        assert hasattr(repo_class, "load_or_initialize"), "Missing load_or_initialize method"
        assert hasattr(repo_class, "save"), "Missing save method"

        # Verify signatures
        import inspect
        load_sig = inspect.signature(repo_class.load_or_initialize)
        save_sig = inspect.signature(repo_class.save)

        assert "default_state" in load_sig.parameters, "load_or_initialize missing default_state param"
        assert "state" in save_sig.parameters, "save missing state param"


class TestFileStateRepositoryUnit:
    """Unit tests for FileStateRepository implementation."""

    def test_init_does_not_create_file(self, tmp_path: Path) -> None:
        """Lazy initialization: file should not be created on __init__."""
        state_file = tmp_path / "state.json"
        FileStateRepository(state_file)

        assert not state_file.exists(), "File should not be created on init"

    def test_load_or_initialize_creates_file_with_defaults(self, tmp_path: Path) -> None:
        """When file doesn't exist, create it with default state."""
        state_file = tmp_path / "state.json"
        repo = FileStateRepository(state_file)
        default = {"session_id": "EP001", "completed_steps": []}

        result = repo.load_or_initialize(default)

        assert result == default, "Should return default state"
        assert state_file.exists(), "Should create state file"

        # Verify file content
        with state_file.open("r") as f:
            saved_data = json.load(f)
        assert saved_data == default, "File should contain default state"

    def test_load_or_initialize_loads_existing_file(self, tmp_path: Path) -> None:
        """When file exists, load and return its content."""
        state_file = tmp_path / "state.json"
        existing_state = {"session_id": "EP002", "completed_steps": [1, 2, 3]}

        # Pre-create file
        with state_file.open("w") as f:
            json.dump(existing_state, f)

        repo = FileStateRepository(state_file)
        default = {"session_id": "default", "completed_steps": []}

        result = repo.load_or_initialize(default)

        assert result == existing_state, "Should load existing state"
        assert result != default, "Should not use default when file exists"

    def test_save_creates_parent_directories(self, tmp_path: Path) -> None:
        """save() should create parent directories if they don't exist."""
        state_file = tmp_path / "nested" / "dir" / "state.json"
        repo = FileStateRepository(state_file)
        state = {"session_id": "test"}

        repo.save(state)

        assert state_file.exists(), "File should be created"
        assert state_file.parent.exists(), "Parent directories should be created"

    def test_save_persists_state_as_json(self, tmp_path: Path) -> None:
        """save() should write state as formatted JSON."""
        state_file = tmp_path / "state.json"
        repo = FileStateRepository(state_file)
        state = {"session_id": "EP003", "completed_steps": [1, 2], "current_step": 3}

        repo.save(state)

        # Verify file content
        with state_file.open("r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded == state, "Saved state should match input"

        # Verify formatting (indented, UTF-8)
        content = state_file.read_text(encoding="utf-8")
        assert "  " in content, "Should be indented"
        assert '"session_id"' in content, "Should contain session_id key"

    def test_load_or_initialize_handles_corrupted_json(self, tmp_path: Path) -> None:
        """When file contains invalid JSON, return default state."""
        state_file = tmp_path / "state.json"
        state_file.write_text("{invalid json}", encoding="utf-8")

        repo = FileStateRepository(state_file)
        default = {"session_id": "fallback", "completed_steps": []}

        result = repo.load_or_initialize(default)

        assert result == default, "Should return default on corrupted file"

    def test_save_does_not_raise_on_permission_error(self, tmp_path: Path) -> None:
        """save() should log errors but not raise exceptions."""
        state_file = tmp_path / "state.json"
        repo = FileStateRepository(state_file)
        state = {"session_id": "test"}

        # Mock file open to raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("No write access")):
            # Should not raise
            repo.save(state)

    def test_state_roundtrip_preserves_data(self, tmp_path: Path) -> None:
        """Integration test: save → load should preserve all data."""
        state_file = tmp_path / "state.json"
        repo = FileStateRepository(state_file)

        original_state = {
            "session_id": "EP004_202510041230",
            "completed_steps": [1, 2, 3, 4],
            "current_step": 5,
            "last_updated": "2025-10-04T12:30:00+09:00",
        }

        repo.save(original_state)
        loaded_state = repo.load_or_initialize({})

        assert loaded_state == original_state, "Roundtrip should preserve data"

    def test_utf8_characters_preserved(self, tmp_path: Path) -> None:
        """save() should handle Japanese characters correctly."""
        state_file = tmp_path / "state.json"
        repo = FileStateRepository(state_file)
        state = {"session_id": "エピソード001", "completed_steps": []}

        repo.save(state)
        loaded = repo.load_or_initialize({})

        assert loaded["session_id"] == "エピソード001", "UTF-8 should be preserved"


class TestFileStateRepositoryEdgeCases:
    """Edge case tests for robustness."""

    def test_empty_dict_save_and_load(self, tmp_path: Path) -> None:
        """Should handle empty dict gracefully."""
        state_file = tmp_path / "state.json"
        repo = FileStateRepository(state_file)

        repo.save({})
        loaded = repo.load_or_initialize({"default": "value"})

        assert loaded == {}, "Should load empty dict"

    def test_nested_dict_preserved(self, tmp_path: Path) -> None:
        """Should preserve nested dictionary structure."""
        state_file = tmp_path / "state.json"
        repo = FileStateRepository(state_file)

        nested_state = {
            "session_id": "test",
            "metadata": {
                "created_at": "2025-10-04",
                "tasks": [
                    {"id": 1, "status": "completed"},
                    {"id": 2, "status": "pending"},
                ],
            },
        }

        repo.save(nested_state)
        loaded = repo.load_or_initialize({})

        assert loaded == nested_state, "Nested structure should be preserved"

    def test_concurrent_saves_last_write_wins(self, tmp_path: Path) -> None:
        """Last save() should win in concurrent scenarios."""
        state_file = tmp_path / "state.json"
        repo1 = FileStateRepository(state_file)
        repo2 = FileStateRepository(state_file)

        repo1.save({"session_id": "first"})
        repo2.save({"session_id": "second"})

        loaded = repo1.load_or_initialize({})
        assert loaded["session_id"] == "second", "Last write should win"


# Pytest fixture for test isolation
@pytest.fixture
def tmp_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Provide isolated temporary directory for each test."""
    return tmp_path_factory.mktemp("state_repo_tests")
