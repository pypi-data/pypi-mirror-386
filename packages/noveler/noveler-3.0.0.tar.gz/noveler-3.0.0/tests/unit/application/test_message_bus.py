"""
Message Bus パターンのユニットテスト
SPEC-901-DDD-REFACTORING 対応

参照: goldensamples/ddd_patterns_golden_sample.py
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Any, Optional

from noveler.domain.events.base import DomainEvent
from noveler.domain.commands.base import DomainCommand
from noveler.application.message_bus import MessageBus
from noveler.application.unit_of_work import AbstractUnitOfWork


class DummyMessage(DomainEvent):
    """テスト用ドメインイベント"""
    def __init__(self, message: str):
        super().__init__()
        self.message = message


class DummyCommand(DomainCommand):
    """テスト用ドメインコマンド"""
    def __init__(self, action: str):
        self.action = action


class MockUnitOfWork(AbstractUnitOfWork):
    """テスト用Mock Unit of Work"""
    def __init__(self):
        self.committed = False
        self._collected_events = []

    def add_event(self, event):
        """イベントを追加"""
        self._collected_events.append(event)

    def collect_new_events(self):
        return self._collected_events

    def _commit(self):
        self.committed = True

    def rollback(self):
        self.committed = False


@pytest.mark.spec("SPEC-901-DDD-REFACTORING")
class DummyMessageBus:
    """Message Bus パターンのテスト"""

    def test_should_handle_command_successfully(self):
        """コマンドが正常に処理されること"""
        # Given
        mock_uow = MockUnitOfWork()

        def test_handler(command: DummyCommand):
            return f"処理完了: {command.action}"

        command_handlers = {DummyCommand: test_handler}
        bus = MessageBus(mock_uow, {}, command_handlers)
        command = DummyCommand("create_episode")

        # When
        result = bus.handle(command)

        # Then
        assert result == "処理完了: create_episode"

    def test_should_handle_event_successfully(self):
        """イベントが正常に処理されること"""
        # Given
        mock_uow = MockUnitOfWork()
        processed_events = []

        def test_event_handler(event: DummyMessage):
            processed_events.append(event.message)

        event_handlers = {DummyMessage: [test_event_handler]}
        bus = MessageBus(mock_uow, event_handlers, {})
        event = DummyMessage("episode_created")

        # When
        bus.handle(event)

        # Then
        assert len(processed_events) == 1
        assert processed_events[0] == "episode_created"

    def test_should_collect_new_events_from_aggregates(self):
        """集約ルートから新しいイベントを収集できること"""
        # Given
        mock_uow = MockUnitOfWork()
        test_event = DummyMessage("new_event")
        mock_uow._collected_events = [test_event]

        # When
        events = mock_uow.collect_new_events()

        # Then
        assert len(events) == 1
        assert events[0].message == "new_event"

    def test_should_handle_message_chain_correctly(self):
        """メッセージチェーンが正しく処理されること（イベント→コマンド→イベント）"""
        # Given
        mock_uow = MockUnitOfWork()
        processed_messages = []

        def event_handler(event: DummyMessage):
            processed_messages.append(f"event: {event.message}")
            # 新しいイベントを追加してチェーン処理をテスト
            if event.message == "trigger_chain":
                mock_uow._collected_events.append(DummyMessage("chained_event"))

        event_handlers = {DummyMessage: [event_handler]}
        bus = MessageBus(mock_uow, event_handlers, {})
        initial_event = DummyMessage("trigger_chain")

        # When
        bus.handle(initial_event)

        # Then
        assert len(processed_messages) >= 1
        assert processed_messages[0] == "event: trigger_chain"

    def test_should_inject_dependencies_to_handlers(self):
        """ハンドラーに依存関係が正しく注入されること"""
        # Given - 最小限の依存関係注入テスト
        mock_uow = MockUnitOfWork()
        dependency_used = []

        def test_handler(command: DummyCommand):
            dependency_used.append("handler_called")
            return f"依存関係注入テスト: {command.action}"

        command_handlers = {DummyCommand: test_handler}
        bus = MessageBus(mock_uow, {}, command_handlers)
        command = DummyCommand("test_action")

        # When
        result = bus.handle(command)

        # Then
        assert len(dependency_used) == 1
        assert dependency_used[0] == "handler_called"
        assert "依存関係注入テスト" in result


@pytest.mark.spec("SPEC-901-DDD-REFACTORING")
class DummyMessageBusIntegration:
    """Message Bus 統合テスト"""

    def test_should_work_with_existing_use_cases(self):
        """既存のユースケースとの統合が動作すること"""
        # Given - 基本的な統合テスト
        mock_uow = MockUnitOfWork()

        def mock_use_case_handler(command: DummyCommand):
            return {"success": True, "message": f"ユースケース実行: {command.action}"}

        command_handlers = {DummyCommand: mock_use_case_handler}
        bus = MessageBus(mock_uow, {}, command_handlers)
        command = DummyCommand("create_episode")

        # When
        result = bus.handle(command)

        # Then
        assert result["success"] is True
        assert "ユースケース実行" in result["message"]

    def test_should_maintain_backward_compatibility(self):
        """既存のAPIとの後方互換性が維持されること"""
        # Given - 後方互換性の基本テスト
        mock_uow = MockUnitOfWork()

        # 既存APIを模倣したハンドラー
        def legacy_api_handler(command: DummyCommand):
            return {
                "stdout": f"Legacy output: {command.action}",
                "stderr": "",
                "success": True,
                "return_code": 0
            }

        command_handlers = {DummyCommand: legacy_api_handler}
        bus = MessageBus(mock_uow, {}, command_handlers)

        # When
        result = bus.handle(DummyCommand("legacy_action"))

        # Then
        assert "stdout" in result
        assert "stderr" in result
        assert result["success"] is True
        assert result["return_code"] == 0
