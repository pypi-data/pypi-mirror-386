"""Tests.tests.unit.application.test_dead_letter_queue
Where: Automated test module.
What: Contains test cases verifying Dead Letter Queue behaviour.
Why: Ensures DLQ implementation is correct and production-ready.
"""

import pytest
from datetime import datetime
from pathlib import Path

from noveler.application.dead_letter_queue import (
    DLQEntry,
    FileDLQRepository,
    InMemoryDLQRepository,
)


@pytest.mark.spec("SPEC-901")
def test_dlq_entry_creation():
    """DLQエントリが正しく作成されることを確認"""
    entry = DLQEntry(
        message_type="event",
        message_name="episode_written",
        payload={"id": "ep-1"},
        original_error="Handler timeout",
        attempt_count=5,
    )

    assert entry.id is not None
    assert entry.message_type == "event"
    assert entry.message_name == "episode_written"
    assert entry.payload == {"id": "ep-1"}
    assert entry.original_error == "Handler timeout"
    assert entry.attempt_count == 5
    assert isinstance(entry.first_failed_at, datetime)
    assert isinstance(entry.last_failed_at, datetime)


@pytest.mark.spec("SPEC-901")
def test_in_memory_dlq_repository():
    """InMemoryDLQRepositoryの基本動作を確認"""
    repo = InMemoryDLQRepository()

    # 追加
    entry1 = DLQEntry(
        message_type="event",
        message_name="test_event",
        payload={"data": "test"},
        original_error="Test error",
        attempt_count=3,
    )
    repo.add(entry1)

    # 取得
    retrieved = repo.get_by_id(entry1.id)
    assert retrieved is not None
    assert retrieved.message_name == "test_event"
    assert retrieved.attempt_count == 3

    # リスト
    all_entries = repo.list_all()
    assert len(all_entries) == 1
    assert all_entries[0].id == entry1.id

    # 削除
    removed = repo.remove(entry1.id)
    assert removed is True
    assert repo.get_by_id(entry1.id) is None


@pytest.mark.spec("SPEC-901")
def test_file_dlq_repository(tmp_path):
    """FileDLQRepositoryの基本動作を確認"""
    dlq_dir = tmp_path / "dlq"
    repo = FileDLQRepository(dlq_dir)

    # 追加
    entry1 = DLQEntry(
        message_type="command",
        message_name="write_episode",
        payload={"episode_number": 42},
        original_error="Database connection failed",
        attempt_count=5,
    )
    repo.add(entry1)

    # ファイルが作成されていることを確認
    entry_file = dlq_dir / f"dlq_{entry1.id}.json"
    assert entry_file.exists()

    # 取得
    retrieved = repo.get_by_id(entry1.id)
    assert retrieved is not None
    assert retrieved.message_name == "write_episode"
    assert retrieved.payload == {"episode_number": 42}
    assert retrieved.attempt_count == 5

    # リスト
    all_entries = repo.list_all()
    assert len(all_entries) == 1

    # 削除
    removed = repo.remove(entry1.id)
    assert removed is True
    assert not entry_file.exists()


@pytest.mark.spec("SPEC-901")
def test_file_dlq_repository_list_limit(tmp_path):
    """FileDLQRepositoryのlimit機能を確認"""
    dlq_dir = tmp_path / "dlq"
    repo = FileDLQRepository(dlq_dir)

    # 複数追加
    for i in range(5):
        entry = DLQEntry(
            message_type="event",
            message_name=f"event_{i}",
            payload={"index": i},
            original_error=f"Error {i}",
            attempt_count=i + 1,
        )
        repo.add(entry)

    # limit指定でリスト
    limited = repo.list_all(limit=3)
    assert len(limited) == 3

    # limit未指定で全件取得
    all_entries = repo.list_all()
    assert len(all_entries) == 5


@pytest.mark.spec("SPEC-901")
def test_file_dlq_repository_clear(tmp_path):
    """FileDLQRepositoryのclear機能を確認"""
    dlq_dir = tmp_path / "dlq"
    repo = FileDLQRepository(dlq_dir)

    # 複数追加
    for i in range(3):
        entry = DLQEntry(
            message_type="event",
            message_name=f"event_{i}",
            payload={},
            original_error="Error",
            attempt_count=1,
        )
        repo.add(entry)

    # クリア
    cleared_count = repo.clear()
    assert cleared_count == 3

    # 全件削除されていることを確認
    all_entries = repo.list_all()
    assert len(all_entries) == 0


@pytest.mark.asyncio
@pytest.mark.spec("SPEC-901")
async def test_message_bus_dlq_integration(tmp_path):
    """MessageBusとDLQの統合動作を確認

    Args:
        tmp_path: pytest standard temporary directory fixture
    """
    from noveler.application.simple_message_bus import MessageBus, BusConfig, GenericEvent
    from noveler.application.uow import InMemoryUnitOfWork
    from noveler.infrastructure.adapters.memory_episode_repository import InMemoryEpisodeRepository
    from noveler.infrastructure.adapters.file_outbox_repository import FileOutboxRepository

    # セットアップ
    repo = InMemoryEpisodeRepository()
    dlq_repo = InMemoryDLQRepository()

    outbox_repo = FileOutboxRepository(base_dir=tmp_path / "outbox")

    bus = MessageBus(
        config=BusConfig(dlq_max_attempts=3),
        dlq_repo=dlq_repo,
        outbox_repo=outbox_repo,
    )
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
    # inline flush無効化（Outboxに溜めてからflushテスト）
    bus.dispatch_inline = False

    # 常に失敗するハンドラ
    attempts = {"count": 0}

    async def failing_handler(evt: GenericEvent):
        attempts["count"] += 1
        raise RuntimeError("Persistent failure")

    bus.event_handlers.setdefault("persistent_failure", []).append(failing_handler)

    # コマンド実行（イベントをOutboxに追加）
    async def write_cmd(data: dict, *, uow):
        uow.add_event("persistent_failure", {"id": "test"})
        return {"success": True}

    bus.command_handlers["write_episode"] = write_cmd

    # コマンド実行
    await bus.handle_command("write_episode", {"episode_number": 1})

    # Outbox内のイベントを手動で複数回試行（DLQへの移動をシミュレート）
    pending = outbox_repo.load_pending()
    assert len(pending) > 0

    # 試行回数を手動で増やしてDLQ移動をトリガー
    entry = pending[0]
    storage_key = getattr(entry, "storage_key", entry.id)

    # 複数回の失敗をシミュレート
    for _ in range(bus.config.dlq_max_attempts):
        outbox_repo.increment_attempts(storage_key, "Simulated failure")

    # flush_outboxでDLQへ移動
    await bus.flush_outbox()

    # DLQに登録されていることを確認
    dlq_entries = dlq_repo.list_all()
    assert len(dlq_entries) >= 1

    dlq_entry = dlq_entries[0]
    assert dlq_entry.message_type == "event"
    assert dlq_entry.message_name == "persistent_failure"
    assert dlq_entry.attempt_count >= bus.config.dlq_max_attempts - 1