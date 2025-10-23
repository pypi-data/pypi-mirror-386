# File: tests/unit/scripts/test_service_locator_diagnosis.py
# Purpose: Validate the diagnostic helper for ServiceLocator cache inspection.
# Context: Ensures the PID/xDist isolation plan has reliable instrumentation.

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.diagnostics import service_locator_xdist_diagnosis as diag


def test_collect_snapshot_contains_core_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Collecting a snapshot should include process and cache metadata."""

    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw42")
    snapshot = diag.collect_snapshot()

    assert snapshot["process"]["worker_id"] == "gw42"
    assert "service_locator" in snapshot
    assert "path_service" in snapshot
    assert isinstance(snapshot["service_locator"]["cached_services"], list)
    assert "timestamp" in snapshot["meta"]


def test_detect_conflicts_flags_shared_objects() -> None:
    """Conflict detection reports shared ServiceLocator and CommonPathService."""

    base = {
        "process": {"worker_id": "gw0"},
        "service_locator": {"object_id": 100, "cached_services": []},
        "path_service": {"object_id": 200},
        "environment": {"PROJECT_ROOT": "/tmp/a", "TARGET_PROJECT_ROOT": "/tmp/a"},
    }

    current = {
        "process": {"worker_id": "gw1"},
        "service_locator": {"object_id": 100, "cached_services": []},
        "path_service": {"object_id": 200},
        "environment": {"PROJECT_ROOT": "/tmp/a", "TARGET_PROJECT_ROOT": "/tmp/b"},
    }

    conflicts = diag.detect_conflicts(current, [base])

    assert any("ServiceLocator object 100" in msg for msg in conflicts)
    assert any("CommonPathService object 200" in msg for msg in conflicts)
    assert any("Environment mismatch for TARGET_PROJECT_ROOT" in msg for msg in conflicts)


def test_write_and_load_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Snapshot serialization should be idempotent and reloadable."""

    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw7")
    snapshot = diag.collect_snapshot()
    path = diag.write_snapshot(snapshot, tmp_path)

    assert path.exists()
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["process"]["worker_id"] == "gw7"

    loaded = diag.load_existing_snapshots(tmp_path)
    assert loaded[-1]["process"]["worker_id"] == "gw7"
