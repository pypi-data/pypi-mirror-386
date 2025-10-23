#!/usr/bin/env python3
# File: tests/unit/infrastructure/test_idempotency_stores.py
# Purpose: Unit tests for idempotency store implementations
# Context: SPEC-901 P1 - Validate file and DB-based idempotency stores
"""Tests for Idempotency Store implementations (File and SQLite)."""

import pytest
from pathlib import Path
from noveler.infrastructure.services.idempotency_store import (
    FileIdempotencyStore,
    SQLiteIdempotencyStore,
)


@pytest.fixture
def file_store(tmp_path: Path):
    """Fixture for FileIdempotencyStore."""
    return FileIdempotencyStore(tmp_path / "idempotency.json")


@pytest.fixture
def sqlite_store(tmp_path: Path):
    """Fixture for SQLiteIdempotencyStore."""
    return SQLiteIdempotencyStore(tmp_path / "idempotency.db")


def test_file_store_record_pending(file_store):
    """Verify FileIdempotencyStore can record pending state."""
    file_store.record_pending("cmd-001")

    record = file_store.get("cmd-001")
    assert record is not None
    assert record.key == "cmd-001"
    assert record.status == "pending"
    assert record.result is None
    assert record.last_error is None


def test_file_store_record_success(file_store):
    """Verify FileIdempotencyStore can record success state."""
    file_store.record_pending("cmd-002")
    file_store.record_success("cmd-002", {"result": "success"})

    record = file_store.get("cmd-002")
    assert record is not None
    assert record.status == "success"
    assert record.result == {"result": "success"}
    assert record.last_error is None


def test_file_store_record_failure(file_store):
    """Verify FileIdempotencyStore can record failure state."""
    file_store.record_pending("cmd-003")
    file_store.record_failure("cmd-003", "Command failed")

    record = file_store.get("cmd-003")
    assert record is not None
    assert record.status == "failed"
    assert record.result is None
    assert record.last_error == "Command failed"


def test_file_store_get_nonexistent_key(file_store):
    """Verify FileIdempotencyStore returns None for nonexistent key."""
    record = file_store.get("nonexistent")
    assert record is None


def test_sqlite_store_record_pending(sqlite_store):
    """Verify SQLiteIdempotencyStore can record pending state."""
    sqlite_store.record_pending("cmd-001")

    record = sqlite_store.get("cmd-001")
    assert record is not None
    assert record.key == "cmd-001"
    assert record.status == "pending"
    assert record.result is None
    assert record.last_error is None


def test_sqlite_store_record_success(sqlite_store):
    """Verify SQLiteIdempotencyStore can record success state."""
    sqlite_store.record_pending("cmd-002")
    sqlite_store.record_success("cmd-002", {"result": "success"})

    record = sqlite_store.get("cmd-002")
    assert record is not None
    assert record.status == "success"
    assert record.result == {"result": "success"}
    assert record.last_error is None


def test_sqlite_store_record_failure(sqlite_store):
    """Verify SQLiteIdempotencyStore can record failure state."""
    sqlite_store.record_pending("cmd-003")
    sqlite_store.record_failure("cmd-003", "Command failed")

    record = sqlite_store.get("cmd-003")
    assert record is not None
    assert record.status == "failed"
    assert record.result is None
    assert record.last_error == "Command failed"


def test_sqlite_store_get_nonexistent_key(sqlite_store):
    """Verify SQLiteIdempotencyStore returns None for nonexistent key."""
    record = sqlite_store.get("nonexistent")
    assert record is None


def test_sqlite_store_update_pending_to_success(sqlite_store):
    """Verify SQLiteIdempotencyStore can update from pending to success."""
    sqlite_store.record_pending("cmd-004")
    record1 = sqlite_store.get("cmd-004")
    assert record1.status == "pending"

    sqlite_store.record_success("cmd-004", {"data": "result"})
    record2 = sqlite_store.get("cmd-004")
    assert record2.status == "success"
    assert record2.result == {"data": "result"}
    # created_at should remain the same
    assert record1.created_at == record2.created_at


def test_file_store_update_pending_to_success(file_store):
    """Verify FileIdempotencyStore can update from pending to success."""
    file_store.record_pending("cmd-004")
    record1 = file_store.get("cmd-004")
    assert record1.status == "pending"

    file_store.record_success("cmd-004", {"data": "result"})
    record2 = file_store.get("cmd-004")
    assert record2.status == "success"
    assert record2.result == {"data": "result"}
    # created_at should remain the same
    assert record1.created_at == record2.created_at


@pytest.mark.spec("SPEC-901")
def test_store_implementations_are_interchangeable(tmp_path: Path):
    """Verify File and SQLite stores implement the same protocol."""
    file_store = FileIdempotencyStore(tmp_path / "file_idem.json")
    sqlite_store = SQLiteIdempotencyStore(tmp_path / "sqlite_idem.db")

    # Both stores should support the same operations
    for store in [file_store, sqlite_store]:
        store.record_pending("test-key")
        record = store.get("test-key")
        assert record.status == "pending"

        store.record_success("test-key", "result")
        record = store.get("test-key")
        assert record.status == "success"