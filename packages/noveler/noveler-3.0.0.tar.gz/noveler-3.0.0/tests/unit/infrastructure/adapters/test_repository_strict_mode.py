"""Tests for repository strict mode enforcement in file-based adapters."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pytest

from noveler.domain.exceptions import RepositoryDataError, RepositoryFallbackError
from noveler.infrastructure.adapters.file_episode_repository import FileEpisodeRepository
from noveler.infrastructure.adapters.file_outbox_repository import FileOutboxRepository
from noveler.infrastructure.config.strict_mode_config import StrictModeConfig, StrictLevel


def _strict_config(level: StrictLevel) -> StrictModeConfig:
    """Helper to build a StrictModeConfig with custom repository strictness."""
    return StrictModeConfig(
        path_service=StrictLevel.WARNING,
        config_service=StrictLevel.WARNING,
        repository_service=level,
    )


def test_file_episode_repository_requires_base_dir_in_strict_mode(tmp_path: Path) -> None:
    """FileEpisodeRepository should reject implicit fallback directories in strict mode."""
    config = _strict_config(StrictLevel.ERROR)

    with pytest.raises(RepositoryFallbackError):
        FileEpisodeRepository(strict_config=config)

    # Providing an explicit directory succeeds.
    repo = FileEpisodeRepository(base_dir=tmp_path / "episodes", strict_config=config)
    assert repo.base_dir.exists()


def test_file_outbox_repository_requires_base_dir_in_strict_mode(tmp_path: Path) -> None:
    """FileOutboxRepository should reject implicit fallback directories in strict mode."""
    config = _strict_config(StrictLevel.ERROR)

    with pytest.raises(RepositoryFallbackError):
        FileOutboxRepository(strict_config=config)

    repo = FileOutboxRepository(base_dir=tmp_path / "outbox", strict_config=config)
    assert repo.base_dir.exists()


def test_file_outbox_repository_missing_payload_raises_in_strict_mode(tmp_path: Path) -> None:
    """Missing required fields should raise RepositoryDataError when strict."""
    config = _strict_config(StrictLevel.ERROR)
    repo = FileOutboxRepository(base_dir=tmp_path, strict_config=config)

    missing_payload = {
        "id": "evt-1",
        "name": "TestEvent",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
    }
    (tmp_path / "evt.json").write_text(json.dumps(missing_payload), encoding="utf-8")

    with pytest.raises(RepositoryDataError):
        repo.load_pending()


def test_file_outbox_repository_warns_and_falls_back_in_warning_mode(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Missing optional fields should emit warnings and use safe defaults in WARNING mode."""
    config = _strict_config(StrictLevel.WARNING)
    repo = FileOutboxRepository(base_dir=tmp_path, strict_config=config)

    # Missing attempts and storage_key -> should warn and fall back.
    valid_payload = {
        "id": "evt-2",
        "name": "TestEvent",
        "payload": {"foo": "bar"},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
    }
    (tmp_path / "evt_2.json").write_text(json.dumps(valid_payload), encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        entries = repo.load_pending()

    assert entries and entries[0].attempts == 0
    assert entries[0].storage_key == "evt_2"
    assert any("[repository]" in record.message for record in caplog.records)
