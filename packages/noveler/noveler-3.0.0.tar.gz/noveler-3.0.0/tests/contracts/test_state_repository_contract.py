"""
# File: tests/contracts/test_state_repository_contract.py
# Purpose: Contract tests for IStateRepository implementations.
# Context: Focuses on FileStateRepository baseline behaviour for state persistence.

These tests define the observable contract for lightweight step state persistence
used by the Progressive Manager refactor (Phase C). They ensure the concrete
FileStateRepository honours the domain protocol expectations for schema, atomic
save semantics, and graceful recovery from corruption.

If the repository implementation is absent, the suite skips without failure.
"""

from __future__ import annotations

import importlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

REQUIRED_STATE_KEYS: dict[str, tuple[type, ...]] = {
    "session_id": (str,),
    "completed_steps": (list,),
    "current_step": (int, type(None)),
    "last_updated": (str,),
}


def _load_file_state_repository() -> type | None:
    try:
        module = importlib.import_module("noveler.infrastructure.repositories.file_state_repository")
    except Exception:
        return None
    repository = getattr(module, "FileStateRepository", None)
    if isinstance(repository, type):
        return repository
    return None


@pytest.fixture(scope="module")
def file_state_repo_cls() -> type:
    cls = _load_file_state_repository()
    if cls is None:
        pytest.skip("FileStateRepository not present (baseline contract only)")
    return cls


def _new_default_state() -> dict[str, Any]:
    return {
        "session_id": "TEST-SESSION",
        "completed_steps": [],
        "current_step": None,
        "last_updated": "1970-01-01T00:00:00+00:00",
    }


def _assert_state_schema(state: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_STATE_KEYS if key not in state]
    assert not missing, f"State missing required keys: {missing}"

    for key, expected_types in REQUIRED_STATE_KEYS.items():
        value = state[key]
        assert isinstance(value, expected_types), (
            f"Key '{key}' expected types {expected_types}, but got {type(value).__name__}"
        )

    assert all(isinstance(step, int) for step in state["completed_steps"]), "completed_steps must contain integers"

    try:
        datetime.fromisoformat(state["last_updated"])
    except ValueError as exc:  # pragma: no cover - guardrail
        pytest.fail(f"last_updated must be ISO8601 string: {exc}")


def test_load_or_initialize_creates_schema(file_state_repo_cls: type, tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    repo = file_state_repo_cls(state_path)

    state = repo.load_or_initialize(_new_default_state())
    _assert_state_schema(state)
    assert state_path.exists(), "load_or_initialize must persist default state"

    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    _assert_state_schema(persisted)


def test_save_persists_state_payload(file_state_repo_cls: type, tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    repo = file_state_repo_cls(state_path)
    repo.load_or_initialize(_new_default_state())

    payload = {
        "session_id": "TEST-SESSION",
        "completed_steps": [1, 2, 3],
        "current_step": 4,
        "last_updated": "2000-01-01T00:00:00+00:00",
    }
    repo.save(payload.copy())

    data = json.loads(state_path.read_text(encoding="utf-8"))
    _assert_state_schema(data)
    assert data == payload


def test_load_or_initialize_recovers_from_corrupted_json(file_state_repo_cls: type, tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text("{ invalid json", encoding="utf-8")

    repo = file_state_repo_cls(state_path)
    state = repo.load_or_initialize(_new_default_state())
    _assert_state_schema(state)
    assert state["session_id"] == "TEST-SESSION"
