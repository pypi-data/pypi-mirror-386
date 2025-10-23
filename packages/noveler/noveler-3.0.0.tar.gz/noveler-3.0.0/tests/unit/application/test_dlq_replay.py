#!/usr/bin/env python3
# File: tests/unit/application/test_dlq_replay.py
# Purpose: Unit tests for DLQ replay mechanism
# Context: SPEC-901 P1 - Manual replay of failed events from Dead Letter Queue
"""Tests for DLQ replay mechanism."""

import pytest
from collections import defaultdict

from noveler.application.simple_message_bus import MessageBus, BusConfig
from noveler.application.dead_letter_queue import InMemoryDLQRepository, DLQEntry
from noveler.application.uow import InMemoryUnitOfWork
from noveler.infrastructure.adapters.memory_episode_repository import InMemoryEpisodeRepository
from noveler.domain.events.base import DomainEvent


class TestEvent(DomainEvent):
    """Test event for replay testing."""

    def __init__(self, test_id: str, should_fail: bool = False):
        super().__init__()
        self.test_id = test_id
        self.should_fail = should_fail


@pytest.mark.asyncio
@pytest.mark.spec("SPEC-901")
async def test_replay_single_dlq_entry_success():
    """Verify successful replay of a single DLQ entry."""
    repo = InMemoryEpisodeRepository()
    dlq_repo = InMemoryDLQRepository()
    bus = MessageBus(config=BusConfig(max_retries=0))
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
    bus.dlq_repo = dlq_repo
    bus.event_handlers = defaultdict(list)

    # Track handler calls
    handler_calls = []

    def test_handler(event):
        handler_calls.append(event.test_id)

    bus.event_handlers[TestEvent].append(test_handler)

    # Add a DLQ entry manually
    dlq_entry = DLQEntry(
        message_type="event",
        message_name="TestEvent",
        payload={"test_id": "replay-001", "should_fail": False},
        original_error="Original failure",
        attempt_count=3,
    )
    dlq_repo.add(dlq_entry)

    # Verify entry is in DLQ
    assert len(dlq_repo.list_all()) == 1

    # Replay the entry
    result = await bus.replay_dlq_entry(dlq_entry.id)

    # Verify success
    assert result["success"] is True
    assert result["entry_id"] == dlq_entry.id
    assert "replay-001" in handler_calls

    # Verify entry was removed from DLQ
    assert len(dlq_repo.list_all()) == 0


@pytest.mark.asyncio
@pytest.mark.spec("SPEC-901")
async def test_replay_dlq_entry_handler_failure():
    """Verify that replay failure keeps entry in DLQ."""
    repo = InMemoryEpisodeRepository()
    dlq_repo = InMemoryDLQRepository()
    bus = MessageBus(config=BusConfig(max_retries=0))
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
    bus.dlq_repo = dlq_repo
    bus.event_handlers = defaultdict(list)

    # Handler that always fails
    def failing_handler(event):
        raise RuntimeError("Handler still fails")

    bus.event_handlers[TestEvent].append(failing_handler)

    # Add a DLQ entry
    dlq_entry = DLQEntry(
        message_type="event",
        message_name="TestEvent",
        payload={"test_id": "replay-002", "should_fail": True},
        original_error="Original failure",
        attempt_count=3,
    )
    dlq_repo.add(dlq_entry)

    # Replay the entry
    result = await bus.replay_dlq_entry(dlq_entry.id)

    # Verify failure
    assert result["success"] is False
    assert "Handler still fails" in result["error"]

    # Verify entry remains in DLQ
    assert len(dlq_repo.list_all()) == 1


@pytest.mark.asyncio
@pytest.mark.spec("SPEC-901")
async def test_replay_nonexistent_dlq_entry():
    """Verify replay of nonexistent entry returns error."""
    repo = InMemoryEpisodeRepository()
    dlq_repo = InMemoryDLQRepository()
    bus = MessageBus(config=BusConfig(max_retries=0))
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
    bus.dlq_repo = dlq_repo

    # Try to replay nonexistent entry
    result = await bus.replay_dlq_entry("nonexistent-id")

    # Verify error
    assert result["success"] is False
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
@pytest.mark.spec("SPEC-901")
async def test_replay_all_dlq_entries():
    """Verify replay of all DLQ entries."""
    repo = InMemoryEpisodeRepository()
    dlq_repo = InMemoryDLQRepository()
    bus = MessageBus(config=BusConfig(max_retries=0))
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
    bus.dlq_repo = dlq_repo
    bus.event_handlers = defaultdict(list)

    # Track handler calls
    handler_calls = []

    def test_handler(event):
        handler_calls.append(event.test_id)

    bus.event_handlers[TestEvent].append(test_handler)

    # Add multiple DLQ entries
    for i in range(3):
        dlq_entry = DLQEntry(
            message_type="event",
            message_name="TestEvent",
            payload={"test_id": f"replay-{i:03d}", "should_fail": False},
            original_error="Original failure",
            attempt_count=3,
        )
        dlq_repo.add(dlq_entry)

    # Verify entries are in DLQ
    assert len(dlq_repo.list_all()) == 3

    # Replay all entries
    results = await bus.replay_all_dlq()

    # Verify all succeeded
    assert results["total"] == 3
    assert results["succeeded"] == 3
    assert results["failed"] == 0
    assert len(handler_calls) == 3

    # Verify all entries were removed from DLQ
    assert len(dlq_repo.list_all()) == 0


@pytest.mark.asyncio
@pytest.mark.spec("SPEC-901")
async def test_replay_all_dlq_entries_mixed_results():
    """Verify replay of all DLQ entries with mixed success/failure."""
    repo = InMemoryEpisodeRepository()
    dlq_repo = InMemoryDLQRepository()
    bus = MessageBus(config=BusConfig(max_retries=0))
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
    bus.dlq_repo = dlq_repo
    bus.event_handlers = defaultdict(list)

    # Track handler calls
    handler_calls = []

    def test_handler(event):
        handler_calls.append(event.test_id)
        if event.should_fail:
            raise RuntimeError(f"Handler failed for {event.test_id}")

    bus.event_handlers[TestEvent].append(test_handler)

    # Add mixed DLQ entries (2 success, 1 failure)
    for i, should_fail in enumerate([False, True, False]):
        dlq_entry = DLQEntry(
            message_type="event",
            message_name="TestEvent",
            payload={"test_id": f"replay-{i:03d}", "should_fail": should_fail},
            original_error="Original failure",
            attempt_count=3,
        )
        dlq_repo.add(dlq_entry)

    # Verify entries are in DLQ
    assert len(dlq_repo.list_all()) == 3

    # Replay all entries
    results = await bus.replay_all_dlq()

    # Verify mixed results
    assert results["total"] == 3
    assert results["succeeded"] == 2
    assert results["failed"] == 1
    assert len(handler_calls) == 3

    # Verify only failed entry remains in DLQ
    remaining = dlq_repo.list_all()
    assert len(remaining) == 1
    assert "replay-001" in remaining[0].payload["test_id"]


@pytest.mark.asyncio
@pytest.mark.spec("SPEC-901")
async def test_replay_dlq_without_dlq_repo():
    """Verify replay returns error when DLQ repo is not configured."""
    repo = InMemoryEpisodeRepository()
    bus = MessageBus(config=BusConfig(max_retries=0))
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
    # No DLQ repo configured

    # Try to replay
    result = await bus.replay_dlq_entry("any-id")

    # Verify error
    assert result["success"] is False
    assert "not configured" in result["error"].lower()