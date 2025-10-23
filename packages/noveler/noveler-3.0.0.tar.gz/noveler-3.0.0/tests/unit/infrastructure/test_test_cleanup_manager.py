"""Tests.tests.unit.infrastructure.test_test_cleanup_manager
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from noveler.infrastructure.shared.test_cleanup_manager import TestCleanupManager

if TYPE_CHECKING:
    from pathlib import Path


def test_cleanup_manager_fast_mode_limits_scope(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    monkeypatch.setenv("NOVELER_TEST_CLEANUP_MODE", "fast")
    cache_dir = tmp_path / ".pytest_cache"
    cache_dir.mkdir()
    (cache_dir / "temp.txt").write_text("dummy", encoding="utf-8")

    other_dir = tmp_path / "custom_output"
    other_dir.mkdir()
    (other_dir / "keep.txt").write_text("keep", encoding="utf-8")

    manager = TestCleanupManager(tmp_path)
    result = manager.cleanup_test_artifacts(dry_run=False)

    assert not cache_dir.exists()
    assert other_dir.exists()
    assert (other_dir / "keep.txt").exists()
    assert result["aborted"] is False
    monkeypatch.delenv("NOVELER_TEST_CLEANUP_MODE", raising=False)


def test_cleanup_manager_preserves_gitignore_in_cache_dir(tmp_path: Path) -> None:
    cache_dir = tmp_path / ".ruff_cache"
    cache_dir.mkdir()
    (cache_dir / ".gitignore").write_text("", encoding="utf-8")
    (cache_dir / "cache.tmp").write_text("dummy", encoding="utf-8")

    manager = TestCleanupManager(tmp_path)
    result = manager.cleanup_test_artifacts(dry_run=False)

    assert (cache_dir / ".gitignore").exists()
    assert not (cache_dir / "cache.tmp").exists()
    assert cache_dir.exists()
    assert result["errors"] == []


def test_cleanup_manager_removes_cache_dir_without_protected_files(tmp_path: Path) -> None:
    cache_dir = tmp_path / ".pytest_cache"
    cache_dir.mkdir()
    (cache_dir / "cache.tmp").write_text("dummy", encoding="utf-8")

    manager = TestCleanupManager(tmp_path)
    manager.cleanup_test_artifacts(dry_run=False)

    assert not cache_dir.exists()


def test_cleanup_manager_honors_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    assert isinstance(monkeypatch, pytest.MonkeyPatch)
    base = 100.0
    calls = {"count": 0}

    def fake_monotonic() -> float:
        calls["count"] += 1
        return base if calls["count"] == 1 else base + 10.0

    monkeypatch.setenv("NOVELER_TEST_CLEANUP_TIMEOUT", "0.5")
    monkeypatch.setattr(
        "noveler.infrastructure.shared.test_cleanup_manager.time.monotonic",
        fake_monotonic,
    )

    target = tmp_path / "temp"
    target.mkdir()
    (target / "stale.txt").write_text("stale", encoding="utf-8")

    manager = TestCleanupManager(tmp_path)
    result = manager.cleanup_test_artifacts(dry_run=False)

    assert result["aborted"] is True
    assert result["errors"]  # timeoutメッセージが記録される
    assert (target / "stale.txt").exists()  # 打ち切りで残る
    monkeypatch.delenv("NOVELER_TEST_CLEANUP_TIMEOUT", raising=False)
