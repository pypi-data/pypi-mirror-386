"""Tests.tests.unit.application.test_usecase_bus_integration
Where: Automated test module.
What: Contains test cases for MessageBus and UseCase integration (SPEC-901).
Why: Ensures MCP/UseCase integration through MessageBus works correctly with success/failure scenarios.
"""

import pytest
from pathlib import Path

from noveler.application.simple_message_bus import MessageBus, BusConfig
from noveler.application.adapters.usecase_bus_adapter import (
    UseCaseBusAdapter,
    QualityCheckBusAdapter
)
from noveler.application.uow import InMemoryUnitOfWork
from noveler.infrastructure.adapters.memory_episode_repository import InMemoryEpisodeRepository
from noveler.infrastructure.adapters.file_outbox_repository import FileOutboxRepository
from noveler.application.dead_letter_queue import InMemoryDLQRepository


@pytest.mark.asyncio
@pytest.mark.spec("SPEC-901")
async def test_usecase_bus_integration_success():
    """MessageBus経由でUseCaseを正常実行できることを確認"""
    repo = InMemoryEpisodeRepository()
    bus = MessageBus()
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)

    # Simple mock UseCase
    class MockUseCase:
        def __init__(self, **kwargs):
            self.unit_of_work = kwargs.get('unit_of_work')

        def execute(self, request):
            return {"success": True, "result": "mock_result"}

    # Setup adapter
    adapter = UseCaseBusAdapter(bus)
    adapter.register_usecase("mock_usecase", MockUseCase)

    # Execute UseCase via bus
    response = await adapter.execute_usecase_via_bus(
        "mock_usecase",
        {"param1": "value1"}
    )

    assert response.success is True
    assert response.data is not None
    assert response.data.get("result") == "mock_result"
    assert response.error_message is None


@pytest.mark.asyncio
@pytest.mark.spec("SPEC-901")
async def test_usecase_bus_integration_failure():
    """MessageBus経由でUseCaseが失敗した場合にエラーが返ることを確認"""
    repo = InMemoryEpisodeRepository()
    bus = MessageBus()
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)

    # Failing UseCase
    class FailingUseCase:
        def __init__(self, **kwargs):
            self.unit_of_work = kwargs.get('unit_of_work')

        def execute(self, request):
            raise RuntimeError("UseCase execution failed")

    # Setup adapter
    adapter = UseCaseBusAdapter(bus)
    adapter.register_usecase("failing_usecase", FailingUseCase)

    # Execute UseCase via bus (should not raise, but return error)
    response = await adapter.execute_usecase_via_bus(
        "failing_usecase",
        {"param1": "value1"}
    )

    assert response.success is False
    assert response.error_message is not None
    assert "UseCase execution failed" in response.error_message


@pytest.mark.asyncio
@pytest.mark.spec("SPEC-901")
async def test_usecase_bus_emits_events_to_outbox(tmp_path):
    """UseCaseの実行イベントがOutboxに保存されることを確認"""
    repo = InMemoryEpisodeRepository()
    outbox_repo = FileOutboxRepository(base_dir=tmp_path / "outbox")
    bus = MessageBus()
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
    bus.outbox_repo = outbox_repo
    bus.dispatch_inline = False  # Outboxに保存

    # Success UseCase
    class SuccessUseCase:
        def __init__(self, **kwargs):
            self.unit_of_work = kwargs.get('unit_of_work')

        def execute(self, request):
            return {"success": True, "result": "success"}

    # Setup adapter
    adapter = UseCaseBusAdapter(bus)
    adapter.register_usecase("success_usecase", SuccessUseCase)

    # Execute UseCase
    response = await adapter.execute_usecase_via_bus(
        "success_usecase",
        {"param1": "value1"}
    )

    assert response.success is True

    # Check Outbox contains usecase.executed event
    pending = outbox_repo.load_pending(limit=10)
    assert len(pending) == 1
    assert pending[0].name == "usecase.executed"
    assert pending[0].payload["usecase_name"] == "success_usecase"
    assert pending[0].payload["success"] is True


@pytest.mark.asyncio
@pytest.mark.spec("SPEC-901")
async def test_usecase_bus_failure_emits_failed_event(tmp_path):
    """UseCase失敗時にusecase.failedイベントがOutboxに保存されることを確認"""
    repo = InMemoryEpisodeRepository()
    outbox_repo = FileOutboxRepository(base_dir=tmp_path / "outbox")
    bus = MessageBus()
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
    bus.outbox_repo = outbox_repo
    bus.dispatch_inline = False

    # Failing UseCase
    class FailingUseCase:
        def __init__(self, **kwargs):
            self.unit_of_work = kwargs.get('unit_of_work')

        def execute(self, request):
            raise RuntimeError("Intentional failure")

    # Setup adapter
    adapter = UseCaseBusAdapter(bus)
    adapter.register_usecase("failing_usecase", FailingUseCase)

    # Execute failing UseCase
    response = await adapter.execute_usecase_via_bus(
        "failing_usecase",
        {"param1": "value1"}
    )

    assert response.success is False

    # Check Outbox contains usecase.failed event
    pending = outbox_repo.load_pending(limit=10)
    assert len(pending) == 1
    assert pending[0].name == "usecase.failed"
    assert pending[0].payload["usecase_name"] == "failing_usecase"
    assert "Intentional failure" in pending[0].payload["error"]


@pytest.mark.asyncio
@pytest.mark.spec("SPEC-901")
async def test_usecase_bus_with_dlq_integration(tmp_path):
    """UseCase実行イベントが繰り返し失敗した場合にDLQに移動することを確認"""
    repo = InMemoryEpisodeRepository()
    outbox_repo = FileOutboxRepository(base_dir=tmp_path / "outbox")
    dlq_repo = InMemoryDLQRepository()
    bus = MessageBus(config=BusConfig(max_retries=0, dlq_max_attempts=3))
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)
    bus.outbox_repo = outbox_repo
    bus.dlq_repo = dlq_repo
    bus.dispatch_inline = False

    # Success UseCase (but event handler will fail)
    class SuccessUseCase:
        def __init__(self, **kwargs):
            self.unit_of_work = kwargs.get('unit_of_work')

        def execute(self, request):
            return {"success": True, "result": "success"}

    # Setup adapter
    adapter = UseCaseBusAdapter(bus)
    adapter.register_usecase("success_usecase", SuccessUseCase)

    # Mock publish to always fail
    original_publish = bus.publish

    async def failing_publish(event):
        raise RuntimeError("Publish infrastructure failure")

    # Execute UseCase (successful, but event will be in Outbox)
    response = await adapter.execute_usecase_via_bus(
        "success_usecase",
        {"param1": "value1"}
    )
    assert response.success is True

    # Mock publish failure for flush
    bus.publish = failing_publish

    # Initial state: 1 event in Outbox, 0 in DLQ
    pending = outbox_repo.load_pending(limit=10)
    assert len(pending) == 1
    assert len(dlq_repo.list_all()) == 0

    # Flush 3 times (will increment attempts each time)
    await bus.flush_outbox(limit=10)  # attempts=1
    await bus.flush_outbox(limit=10)  # attempts=2
    await bus.flush_outbox(limit=10)  # attempts=2 >= dlq_max_attempts-1, move to DLQ

    # Outbox should be empty, DLQ should have 1 entry
    assert len(outbox_repo.load_pending(limit=10)) == 0
    dlq_entries = dlq_repo.list_all()
    assert len(dlq_entries) == 1
    assert dlq_entries[0].message_name == "usecase.executed"
    assert dlq_entries[0].payload["usecase_name"] == "success_usecase"


@pytest.mark.asyncio
@pytest.mark.spec("SPEC-901")
async def test_usecase_bus_unknown_usecase_returns_error():
    """未登録のUseCaseを実行しようとするとエラーが返ることを確認"""
    repo = InMemoryEpisodeRepository()
    bus = MessageBus()
    bus.uow_factory = lambda: InMemoryUnitOfWork(episode_repo=repo)

    adapter = UseCaseBusAdapter(bus)

    # Try to execute unregistered UseCase
    response = await adapter.execute_usecase_via_bus(
        "unknown_usecase",
        {"param1": "value1"}
    )

    assert response.success is False
    assert "Unknown usecase" in response.error_message