"""Tests.tests.unit.application.test_simple_message_bus
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

import asyncio
import os
from datetime import datetime

import pytest

from noveler.application.simple_message_bus import MessageBus, GenericEvent, BusConfig
from noveler.application.uow import InMemoryUnitOfWork
from noveler.infrastructure.adapters.memory_episode_repository import InMemoryEpisodeRepository
from noveler.infrastructure.adapters.file_outbox_repository import FileOutboxRepository


@pytest.mark.asyncio
async def test_uow_commit_then_emit_event():
    repo = InMemoryEpisodeRepository()
    bus = MessageBus()
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)

    events_seen: list[str] = []

    async def on_written(evt: GenericEvent):
        events_seen.append(evt.event_name)

    async def write_cmd(data: dict, *, uow: InMemoryUnitOfWork):
        uow.episode_repo.save(type("E", (), {"id": "ep-1", "title": "T", "content": ""}))  # simple stub
        uow.add_event("episode_written", {"id": "ep-1"})
        return {"success": True}

    bus.command_handlers["write_episode"] = write_cmd
    bus.event_handlers.setdefault("episode_written", []).append(on_written)

    result = await bus.handle_command("write_episode", {"episode_number": 1})
    assert result.get("success") is True
    assert "episode_written" in events_seen


@pytest.mark.asyncio
async def test_event_handler_retry_then_success(monkeypatch):
    repo = InMemoryEpisodeRepository()
    bus = MessageBus(config=BusConfig(max_retries=2, backoff_base_sec=0.01, backoff_max_sec=0.02, jitter_sec=0))
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)

    attempts = {"count": 0}

    async def flaky(evt: GenericEvent):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("temporary")

    async def write_cmd(data: dict, *, uow: InMemoryUnitOfWork):
        uow.add_event("episode_written", {"id": "ep-2"})
        return {"success": True}

    bus.command_handlers["write_episode"] = write_cmd
    bus.event_handlers.setdefault("episode_written", []).append(flaky)

    result = await bus.handle_command("write_episode", {"episode_number": 2})
    assert result.get("success") is True
    # 1回失敗後に成功していること
    assert attempts["count"] >= 2


@pytest.mark.asyncio
async def test_outbox_and_inline_flush(tmp_path):
    repo = InMemoryEpisodeRepository()
    outbox_dir = tmp_path / "outbox"
    bus = MessageBus()
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
    bus.outbox_repo = FileOutboxRepository(base_dir=outbox_dir)
    bus.dispatch_inline = True

    seen = {"ok": False}

    async def on_evt(evt: GenericEvent):
        seen["ok"] = True

    async def write_cmd(data: dict, *, uow: InMemoryUnitOfWork):
        uow.add_event("episode_written", {"id": "ep-3"})
        return {"success": True}

    bus.command_handlers["write_episode"] = write_cmd
    bus.event_handlers.setdefault("episode_written", []).append(on_evt)

    result = await bus.handle_command("write_episode", {"episode_number": 3})
    assert result.get("success") is True
    # inline flush によりハンドラが呼ばれている
    assert seen["ok"] is True


@pytest.mark.asyncio
async def test_idempotency_store_skips_duplicate():
    from noveler.application.idempotency import InMemoryIdempotencyStore

    bus = MessageBus()
    bus.idempotency_store = InMemoryIdempotencyStore()

    calls = {"n": 0}

    async def on_evt(evt: GenericEvent):
        calls["n"] += 1

    bus.event_handlers.setdefault("dup_evt", []).append(on_evt)

    # 同じIDのイベントを2回publishしても2回目はスキップされる
    e = GenericEvent(event_name="dup_evt", payload={})
    await bus.publish(e)
    await bus.publish(e)

    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_publish_supports_sync_event_handler():
    bus = MessageBus()

    observed = {"count": 0}

    def sync_handler(evt: GenericEvent) -> None:
        observed["count"] += 1

    bus.event_handlers.setdefault("sync_evt", []).append(sync_handler)

    await bus.publish(GenericEvent(event_name="sync_evt", payload={}))

    assert observed["count"] == 1
