# File: tests/unit/application/test_message_bus_outbox.py
# Purpose: Validate SPEC-901 outbox and idempotency integrations in MessageBus.
# Context: Ensures new persistence helpers operate safely without external
#          dependencies.
"""Unit tests for the enhanced MessageBus outbox/idempotency support."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from noveler.application.message_bus import MessageBus
from noveler.domain.commands.base import DomainCommand
from noveler.domain.events.base import DomainEvent
from noveler.infrastructure.repositories.outbox_repository import FileOutboxRepository
from noveler.infrastructure.services.idempotency_store import FileIdempotencyStore


@dataclass
class _TestCommand(DomainCommand):
    value: int = 0


@dataclass
class _TestEvent(DomainEvent):
    description: str = ""


def test_idempotency_store_returns_cached_result(tmp_path: Path) -> None:
    """Second execution with identical idempotency key returns cached value."""

    outbox_repo = FileOutboxRepository(tmp_path / "outbox")
    idempotency_store = FileIdempotencyStore(tmp_path / "outbox" / "idempotency.json")
    counter = {"calls": 0}

    def handler(cmd: _TestCommand) -> Any:
        counter["calls"] += 1
        return {"success": True, "value": cmd.value, "calls": counter["calls"]}

    bus = MessageBus(
        command_handlers={_TestCommand: handler},
        outbox_repository=outbox_repo,
        idempotency_store=idempotency_store,
    )
    cmd = _TestCommand(value=1)
    cmd.add_metadata("idempotency_key", "cmd-123")

    first = bus.handle(cmd)
    assert first == {"success": True, "value": 1, "calls": 1}

    second = bus.handle(cmd)
    assert second == {"success": True, "value": 1, "calls": 1}
    assert counter["calls"] == 1


def test_outbox_enqueue_occurs_for_events(tmp_path: Path) -> None:
    """Events processed by the bus get persisted into the outbox repository."""

    outbox_repo = FileOutboxRepository(tmp_path / "outbox")
    bus = MessageBus(outbox_repository=outbox_repo)

    event = _TestEvent(description="spec-901 integration event")
    bus.handle(event)

    pending_files = list((tmp_path / "outbox" / "pending").glob("*.json"))
    assert len(pending_files) == 1
    data = pending_files[0].read_text(encoding="utf-8")
    assert "spec-901 integration event" in data


def test_idempotency_records_failures(tmp_path: Path) -> None:
    """Handler failures still record idempotency attempts."""

    outbox_repo = FileOutboxRepository(tmp_path / "outbox")
    idempotency_store = FileIdempotencyStore(tmp_path / "outbox" / "idempotency.json")

    def handler(_cmd: _TestCommand) -> Any:
        raise RuntimeError("boom")

    bus = MessageBus(
        command_handlers={_TestCommand: handler},
        outbox_repository=outbox_repo,
        idempotency_store=idempotency_store,
    )

    cmd = _TestCommand(value=7)
    cmd.add_metadata("idempotency_key", "cmd-err")

    result = bus.handle(cmd)
    assert result["success"] is False

    record = idempotency_store.get("cmd-err")
    assert record is not None
    assert record.status == "failed"
