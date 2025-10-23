# File: tests/unit/application/test_outbox_idempotency.py
# Purpose: Unit tests for Outbox flush failures/retries and Idempotency duplicate prevention
# Context: Validates DLQ movement, retry logic, and idempotency store behavior

"""Outbox/Idempotency異常系テスト

Outbox flush の失敗/再試行、Idempotency の重複抑止を検証

参照: TODO.md SPEC-901残件 - Unit: Outbox flush の失敗/再試行、Idempotency の重複抑止
"""

import pytest
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from noveler.application.simple_message_bus import MessageBus, BusConfig
from noveler.application.outbox import OutboxEntry
from noveler.application.idempotency import InMemoryIdempotencyStore
from noveler.application.uow import InMemoryUnitOfWork
from noveler.infrastructure.adapters.file_outbox_repository import FileOutboxRepository
from noveler.infrastructure.adapters.memory_episode_repository import InMemoryEpisodeRepository


class FailingOutboxRepository(FileOutboxRepository):
    """テスト用：特定の操作で失敗するOutboxRepository"""

    def __init__(self, base_path: Path):
        super().__init__(base_path)
        self.fail_on_add = False
        self.fail_on_load_pending = False
        self.fail_on_mark_dispatched = False
        self.fail_on_increment_attempts = False
        self.fail_on_move_to_dlq = False

    def add(self, entry: OutboxEntry) -> None:
        if self.fail_on_add:
            raise RuntimeError("Failed to add entry to outbox")
        super().add(entry)

    def load_pending(self, limit: int = 100) -> list[OutboxEntry]:
        if self.fail_on_load_pending:
            raise RuntimeError("Failed to load pending entries")
        return super().load_pending(limit)

    def mark_dispatched(self, entry_id: str) -> None:
        if self.fail_on_mark_dispatched:
            raise RuntimeError("Failed to mark entry as dispatched")
        super().mark_dispatched(entry_id)

    def increment_attempts(self, entry_id: str, error_message: str) -> None:
        if self.fail_on_increment_attempts:
            raise RuntimeError("Failed to increment attempts")
        super().increment_attempts(entry_id, error_message)

    def move_to_dlq(self, entry_id: str) -> None:
        if self.fail_on_move_to_dlq:
            raise RuntimeError("Failed to move entry to DLQ")
        super().move_to_dlq(entry_id)


class FailingIdempotencyStore(InMemoryIdempotencyStore):
    """テスト用：特定の操作で失敗するIdempotencyStore"""

    def __init__(self):
        super().__init__()
        self.fail_on_check = False
        self.fail_on_mark = False

    def is_processed(self, event_id: str) -> bool:
        if self.fail_on_check:
            raise RuntimeError("Failed to check idempotency")
        return super().is_processed(event_id)

    def mark_processed(self, event_id: str) -> None:
        if self.fail_on_mark:
            raise RuntimeError("Failed to mark as processed")
        super().mark_processed(event_id)


class TestOutboxErrorHandling:
    """Outbox異常系テスト"""

    @pytest.fixture
    def temp_outbox_dir(self):
        """テスト用一時ディレクトリ"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def failing_outbox_repo(self, temp_outbox_dir):
        """失敗可能なOutboxRepository"""
        return FailingOutboxRepository(temp_outbox_dir)

    @pytest.fixture
    def message_bus_with_failing_outbox(self, failing_outbox_repo):
        """失敗するOutboxを使用するMessageBus"""
        repo = InMemoryEpisodeRepository()
        uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
        idempotency_store = InMemoryIdempotencyStore()

        bus = MessageBus(
            config=BusConfig(max_retries=2, dlq_max_attempts=3),
            uow_factory=uow_factory,
            outbox_repo=failing_outbox_repo,
            idempotency_store=idempotency_store
        )
        return bus

    def test_outbox_add_entry_basic(self, temp_outbox_dir):
        """Outbox基本的なエントリ追加"""
        # Given
        repo = FileOutboxRepository(temp_outbox_dir)
        entry = OutboxEntry(
            id="test-event-1",
            name="test_event",
            payload={"data": "test"},
            created_at=datetime.utcnow()
        )

        # When
        repo.add(entry)

        # Then
        pending_entries = repo.load_pending()
        assert len(pending_entries) == 1
        assert pending_entries[0].id == "test-event-1"
        assert pending_entries[0].name == "test_event"

    def test_outbox_load_pending_with_limit(self, temp_outbox_dir):
        """Outbox待機中エントリの制限付き読み込み"""
        # Given
        repo = FileOutboxRepository(temp_outbox_dir)

        # 複数エントリを追加
        for i in range(5):
            entry = OutboxEntry(
                id=f"event-{i}",
                name="test_event",
                payload={"index": i},
                created_at=datetime.utcnow()
            )
            repo.add(entry)

        # When: 制限付きで読み込み
        pending_entries = repo.load_pending(limit=3)

        # Then: 制限数のみ取得
        assert len(pending_entries) == 3

    def test_outbox_increment_attempts_and_dlq_movement(self, temp_outbox_dir):
        """Outboxリトライ回数増加とDLQ移動"""
        # Given
        repo = FileOutboxRepository(temp_outbox_dir)
        entry = OutboxEntry(
            id="failing-event",
            name="failing_event",
            payload={"data": "test"},
            created_at=datetime.utcnow()
        )
        repo.add(entry)

        # When: リトライ回数を増加
        repo.increment_attempts("failing-event", "First failure")
        repo.increment_attempts("failing-event", "Second failure")
        repo.increment_attempts("failing-event", "Third failure")

        # エントリの状態確認
        pending_entries = repo.load_pending()
        if pending_entries:
            entry = pending_entries[0]
            assert entry.attempts == 3
            assert entry.last_error == "Third failure"

        # When: DLQに移動
        repo.move_to_dlq("failing-event")

        # Then: 待機中リストから削除され、DLQに移動
        pending_entries = repo.load_pending()
        assert len(pending_entries) == 0

        dlq_entries = repo.load_dlq_entries()
        assert len(dlq_entries) == 1
        assert dlq_entries[0].id == "failing-event"

    @pytest.mark.asyncio
    async def test_outbox_flush_with_handler_failure_and_retry(self, message_bus_with_failing_outbox):
        """Outboxフラッシュ時のハンドラー失敗とリトライ"""
        # Given
        bus = message_bus_with_failing_outbox
        attempts = {"count": 0}

        async def failing_event_handler(event):
            attempts["count"] += 1
            if attempts["count"] < 3:  # 最初2回は失敗
                raise RuntimeError(f"Handler failure attempt {attempts['count']}")
            # 3回目で成功
            return

        bus.event_handlers["test_event"] = [failing_event_handler]

        # Outboxにエントリを直接追加
        entry = OutboxEntry(
            id="retry-test-event",
            name="test_event",
            payload={"data": "retry_test"},
            created_at=datetime.utcnow()
        )
        bus.outbox_repo.add(entry)

        # When: フラッシュ実行（リトライ含む）
        processed_count = await bus.flush_outbox()

        # Then: 最終的に成功し、エントリが処理される
        assert processed_count == 1
        assert attempts["count"] == 3  # 3回実行された

        # 待機中エントリがなくなっている
        pending_entries = bus.outbox_repo.load_pending()
        assert len(pending_entries) == 0

    @pytest.mark.asyncio
    async def test_outbox_flush_with_dlq_movement(self, message_bus_with_failing_outbox):
        """Outboxフラッシュ時のDLQ移動"""
        # Given
        bus = message_bus_with_failing_outbox

        async def always_failing_event_handler(event):
            raise RuntimeError("Handler always fails")

        bus.event_handlers["failing_event"] = [always_failing_event_handler]

        # Outboxにエントリを追加（既にリトライ上限近く）
        entry = OutboxEntry(
            id="dlq-test-event",
            name="failing_event",
            payload={"data": "dlq_test"},
            created_at=datetime.utcnow(),
            attempts=2  # DLQ移動の閾値(3)に近い
        )
        bus.outbox_repo.add(entry)

        # When: フラッシュ実行
        processed_count = await bus.flush_outbox()

        # Then: エントリがDLQに移動
        assert processed_count == 1

        # DLQに移動していることを確認
        dlq_entries = bus.outbox_repo.load_dlq_entries()
        assert len(dlq_entries) == 1
        assert dlq_entries[0].id == "dlq-test-event"

        # 待機中リストから削除されている
        pending_entries = bus.outbox_repo.load_pending()
        assert len(pending_entries) == 0

    def test_outbox_repository_failure_handling(self, failing_outbox_repo):
        """OutboxRepository操作失敗時のハンドリング"""
        # Given
        repo = failing_outbox_repo

        # When & Then: add操作の失敗
        repo.fail_on_add = True
        entry = OutboxEntry(
            id="test-event",
            name="test_event",
            payload={"data": "test"},
            created_at=datetime.utcnow()
        )

        with pytest.raises(RuntimeError, match="Failed to add entry to outbox"):
            repo.add(entry)

        # When & Then: load_pending操作の失敗
        repo.fail_on_add = False
        repo.add(entry)  # 正常に追加
        repo.fail_on_load_pending = True

        with pytest.raises(RuntimeError, match="Failed to load pending entries"):
            repo.load_pending()


class TestIdempotencyErrorHandling:
    """Idempotency異常系テスト"""

    def test_idempotency_basic_functionality(self):
        """Idempotency基本機能の確認"""
        # Given
        store = InMemoryIdempotencyStore()

        # When & Then: 初回チェック
        assert store.is_processed("event-1") is False

        # When & Then: 処理済みマーク
        store.mark_processed("event-1")
        assert store.is_processed("event-1") is True

        # When & Then: 重複チェック
        assert store.is_processed("event-1") is True  # 重複検知

    def test_idempotency_multiple_events(self):
        """複数イベントのIdempotency管理"""
        # Given
        store = InMemoryIdempotencyStore()

        # When: 複数イベントを処理
        events = ["event-1", "event-2", "event-3"]
        for event_id in events:
            assert store.is_processed(event_id) is False
            store.mark_processed(event_id)

        # Then: 各イベントが正しく管理される
        for event_id in events:
            assert store.is_processed(event_id) is True

        # 新しいイベントは未処理
        assert store.is_processed("event-4") is False

    @pytest.mark.asyncio
    async def test_messagebus_idempotency_duplicate_prevention(self):
        """MessageBusでのIdempotency重複防止"""
        # Given
        repo = InMemoryEpisodeRepository()
        uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
        idempotency_store = InMemoryIdempotencyStore()

        bus = MessageBus(
            config=BusConfig(),
            uow_factory=uow_factory,
            idempotency_store=idempotency_store
        )

        execution_count = {"count": 0}

        async def counting_event_handler(event):
            execution_count["count"] += 1

        bus.event_handlers["duplicate_test_event"] = [counting_event_handler]

        # When: 同じイベントIDで複数回実行
        from noveler.application.simple_message_bus import GenericEvent

        event = GenericEvent(
            event_id="duplicate-event-id",
            event_name="duplicate_test_event",
            payload={"data": "test"}
        )

        # 1回目の実行
        await bus._handle_event(event)
        # 2回目の実行（重複）
        await bus._handle_event(event)
        # 3回目の実行（重複）
        await bus._handle_event(event)

        # Then: 1回のみ実行される
        assert execution_count["count"] == 1

    def test_idempotency_store_failure_handling(self):
        """IdempotencyStore操作失敗時のハンドリング"""
        # Given
        store = FailingIdempotencyStore()

        # When & Then: チェック操作の失敗
        store.fail_on_check = True
        with pytest.raises(RuntimeError, match="Failed to check idempotency"):
            store.is_processed("test-event")

        # When & Then: マーク操作の失敗
        store.fail_on_check = False
        store.fail_on_mark = True
        with pytest.raises(RuntimeError, match="Failed to mark as processed"):
            store.mark_processed("test-event")

    def test_idempotency_memory_management(self):
        """IdempotencyStoreのメモリ管理"""
        # Given
        store = InMemoryIdempotencyStore()

        # When: 大量のイベントを処理
        for i in range(1000):
            event_id = f"event-{i}"
            store.mark_processed(event_id)

        # Then: すべて正しく記録されている
        for i in range(1000):
            event_id = f"event-{i}"
            assert store.is_processed(event_id) is True

        # メモリ使用量の概算確認（大まかなチェック）
        assert len(store._processed_events) == 1000

    @pytest.mark.asyncio
    async def test_outbox_and_idempotency_integration(self):
        """OutboxとIdempotencyの統合動作確認"""
        # Given
        with tempfile.TemporaryDirectory() as temp_dir:
            outbox_repo = FileOutboxRepository(Path(temp_dir))
            idempotency_store = InMemoryIdempotencyStore()

            repo = InMemoryEpisodeRepository()
            uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)

            bus = MessageBus(
                config=BusConfig(),
                uow_factory=uow_factory,
                outbox_repo=outbox_repo,
                idempotency_store=idempotency_store
            )

            execution_count = {"count": 0}

            async def counting_handler(event):
                execution_count["count"] += 1

            bus.event_handlers["integration_test_event"] = [counting_handler]

            # When: イベントをOutboxに追加し、重複処理を試行
            entry1 = OutboxEntry(
                id="integration-event-1",
                name="integration_test_event",
                payload={"data": "test"},
                created_at=datetime.utcnow()
            )
            entry2 = OutboxEntry(
                id="integration-event-1",  # 同じID（重複）
                name="integration_test_event",
                payload={"data": "test"},
                created_at=datetime.utcnow()
            )

            outbox_repo.add(entry1)
            outbox_repo.add(entry2)  # 重複エントリ

            # Outboxフラッシュ実行
            processed_count = await bus.flush_outbox()

            # Then: 重複が適切に処理される
            assert processed_count == 2  # 両方処理されるが
            assert execution_count["count"] == 1  # ハンドラーは1回のみ実行


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
