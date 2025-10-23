# File: tests/unit/application/test_uow_error_handling.py
# Purpose: Unit tests for UnitOfWork error handling and rollback scenarios
# Context: Validates commit failure→rollback behavior and transaction integrity

"""UnitOfWork異常系テスト

UoW begin/commit/rollback の異常系動作を検証

参照: TODO.md SPEC-901残件 - Unit: UoW begin/commit/rollback 異常系
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict

from noveler.application.uow import InMemoryUnitOfWork
from noveler.application.simple_message_bus import MessageBus, BusConfig
from noveler.infrastructure.adapters.memory_episode_repository import InMemoryEpisodeRepository


class FailingEpisodeRepository:
    """テスト用：commit時に失敗するRepository"""

    def __init__(self, fail_on_save=False):
        self.episodes = {}
        self.fail_on_save = fail_on_save
        self.save_called = False

    def save(self, episode):
        self.save_called = True
        if self.fail_on_save:
            raise RuntimeError("Repository save failed")
        self.episodes[episode.id] = episode

    def get_by_id(self, episode_id):
        return self.episodes.get(episode_id)


class FailingUnitOfWork(InMemoryUnitOfWork):
    """テスト用：commit時に失敗するUnitOfWork"""

    def __init__(self, episode_repo, fail_on_commit=False):
        super().__init__(episode_repo)
        self.fail_on_commit = fail_on_commit
        self.commit_called = False
        self.rollback_called = False

    def commit(self):
        self.commit_called = True
        if self.fail_on_commit:
            # commit失敗時は自動でrollbackが呼ばれることを想定
            self.rollback()
            raise RuntimeError("Unit of Work commit failed")
        super().commit()

    def rollback(self):
        self.rollback_called = True
        super().rollback()


class TestUnitOfWorkErrorHandling:
    """UnitOfWork異常系テスト"""

    def test_uow_begin_commit_rollback_basic_flow(self):
        """基本的なbegin→commit→rollbackフローの確認"""
        # Given
        repo = InMemoryEpisodeRepository()
        uow = InMemoryUnitOfWork(episode_repo=repo)

        # When & Then: 正常フロー
        uow.begin()
        assert uow._started is True

        uow.add_event("test_event", {"data": "test"})
        assert len(uow.get_events()) == 1

        uow.commit()
        assert uow._started is False

        # When & Then: rollbackフロー
        uow.begin()
        uow.add_event("test_event2", {"data": "test2"})
        assert len(uow.get_events()) == 1

        uow.rollback()
        assert uow._started is False

    def test_uow_commit_without_begin(self):
        """begin()なしでcommit()を呼んだ場合の処理"""
        # Given
        repo = InMemoryEpisodeRepository()
        uow = InMemoryUnitOfWork(episode_repo=repo)

        # When: beginなしでcommit
        uow.commit()

        # Then: エラーにならず、何も起こらない
        assert uow._started is False

    def test_uow_rollback_without_begin(self):
        """begin()なしでrollback()を呼んだ場合の処理"""
        # Given
        repo = InMemoryEpisodeRepository()
        uow = InMemoryUnitOfWork(episode_repo=repo)

        # When: beginなしでrollback
        uow.rollback()

        # Then: エラーにならず、状態がFalseのまま
        assert uow._started is False

    def test_uow_events_cleared_on_rollback(self):
        """rollback時にイベントがクリアされることの確認"""
        # Given
        repo = InMemoryEpisodeRepository()
        uow = InMemoryUnitOfWork(episode_repo=repo)

        # When
        uow.begin()
        uow.add_event("event1", {"data": "test1"})
        uow.add_event("event2", {"data": "test2"})
        assert len(uow.get_events()) == 2

        uow.rollback()

        # Then: イベントがクリアされる
        assert len(uow.get_events()) == 0
        assert uow._started is False

    def test_uow_multiple_begin_calls(self):
        """複数回begin()を呼んだ場合の処理"""
        # Given
        repo = InMemoryEpisodeRepository()
        uow = InMemoryUnitOfWork(episode_repo=repo)

        # When
        uow.begin()
        uow.begin()  # 2回目のbegin
        uow.begin()  # 3回目のbegin

        # Then: 状態は変わらずTrueのまま
        assert uow._started is True

        uow.commit()
        assert uow._started is False

    @pytest.mark.asyncio
    async def test_messagebus_uow_commit_failure_handling(self):
        """MessageBus内でUoWのcommit失敗時の処理確認"""
        # Given
        failing_repo = FailingEpisodeRepository(fail_on_save=False)
        failing_uow = FailingUnitOfWork(failing_repo, fail_on_commit=True)

        bus = MessageBus(config=BusConfig(max_retries=1))
        bus.uow_factory = lambda: failing_uow

        async def test_command(data: Dict[str, Any], *, uow: FailingUnitOfWork) -> Dict[str, Any]:
            # Repository操作を実行（失敗する可能性）
            episode = type("Episode", (), {"id": "ep-1", "title": "Test"})
            uow.episode_repo.save(episode)
            uow.add_event("episode_saved", {"episode_id": "ep-1"})
            return {"success": True, "episode_id": "ep-1"}

        bus.command_handlers["test_command"] = test_command

        # When: commit失敗するコマンドを実行
        with pytest.raises(RuntimeError, match="Unit of Work commit failed"):
            await bus.handle_command("test_command", {"data": "test"})

        # Then: rollbackが呼ばれていることを確認
        assert failing_uow.commit_called is True
        assert failing_uow.rollback_called is True

    @pytest.mark.asyncio
    async def test_messagebus_uow_repository_failure_handling(self):
        """MessageBus内でRepository操作失敗時の処理確認"""
        # Given
        failing_repo = FailingEpisodeRepository(fail_on_save=True)
        normal_uow = InMemoryUnitOfWork(failing_repo)

        bus = MessageBus(config=BusConfig(max_retries=1))
        bus.uow_factory = lambda: normal_uow

        async def test_command_with_repo_failure(data: Dict[str, Any], *, uow: InMemoryUnitOfWork) -> Dict[str, Any]:
            # Repository操作で例外が発生
            episode = type("Episode", (), {"id": "ep-1", "title": "Test"})
            uow.episode_repo.save(episode)  # ここで失敗
            uow.add_event("episode_saved", {"episode_id": "ep-1"})
            return {"success": True}

        bus.command_handlers["test_command_repo_fail"] = test_command_with_repo_failure

        # When: Repository操作が失敗するコマンドを実行
        with pytest.raises(RuntimeError, match="Repository save failed"):
            await bus.handle_command("test_command_repo_fail", {"data": "test"})

        # Then: Repository操作は実行されたが失敗
        assert failing_repo.save_called is True

    def test_uow_event_management_after_rollback(self):
        """rollback後のイベント管理状態確認"""
        # Given
        repo = InMemoryEpisodeRepository()
        uow = InMemoryUnitOfWork(episode_repo=repo)

        # When: イベント追加 → rollback → 再度イベント追加
        uow.begin()
        uow.add_event("event1", {"step": 1})
        assert len(uow.get_events()) == 1

        uow.rollback()
        assert len(uow.get_events()) == 0

        # rollback後に新しいトランザクション開始
        uow.begin()
        uow.add_event("event2", {"step": 2})
        assert len(uow.get_events()) == 1

        # Then: 新しいイベントのみが存在
        events = uow.get_events()
        assert len(events) == 1
        assert events[0][0] == "event2"
        assert events[0][1]["step"] == 2

        uow.commit()

    def test_uow_idempotent_operations(self):
        """UoWの冪等性操作の確認"""
        # Given
        repo = InMemoryEpisodeRepository()
        uow = InMemoryUnitOfWork(episode_repo=repo)

        # When: 複数回commit/rollback
        uow.begin()
        uow.add_event("event1", {"data": "test"})

        # 複数回commit（2回目以降は何もしない）
        uow.commit()
        uow.commit()  # 2回目
        uow.commit()  # 3回目

        # Then: 状態が一貫している
        assert uow._started is False

        # rollbackも同様
        uow.rollback()  # 既にcommit済みなので何もしない
        uow.rollback()  # 2回目
        assert uow._started is False

    @pytest.mark.asyncio
    async def test_messagebus_uow_exception_in_event_handler(self):
        """イベントハンドラーでの例外がUoWに影響しないことの確認"""
        # Given
        repo = InMemoryEpisodeRepository()
        uow = InMemoryUnitOfWork(repo)

        bus = MessageBus(config=BusConfig(max_retries=1))
        bus.uow_factory = lambda: uow

        async def test_command(data: Dict[str, Any], *, uow: InMemoryUnitOfWork) -> Dict[str, Any]:
            uow.add_event("failing_event", {"data": "test"})
            return {"success": True}

        async def failing_event_handler(event):
            raise RuntimeError("Event handler failed")

        bus.command_handlers["test_command"] = test_command
        bus.event_handlers["failing_event"] = [failing_event_handler]

        # When: イベントハンドラーが失敗するコマンドを実行
        # Note: イベント処理はコマンド処理後なので、コマンド自体は成功する
        result = await bus.handle_command("test_command", {"data": "test"})

        # Then: コマンドは成功（イベント処理の失敗は別途ハンドリング）
        assert result["success"] is True

    def test_uow_clear_events_method(self):
        """clear_events()メソッドの動作確認"""
        # Given
        repo = InMemoryEpisodeRepository()
        uow = InMemoryUnitOfWork(episode_repo=repo)

        # When
        uow.begin()
        uow.add_event("event1", {"data": "test1"})
        uow.add_event("event2", {"data": "test2"})
        assert len(uow.get_events()) == 2

        uow.clear_events()

        # Then: イベントのみクリアされ、トランザクション状態は維持
        assert len(uow.get_events()) == 0
        assert uow._started is True  # まだトランザクション中

        # 新しいイベントを追加可能
        uow.add_event("event3", {"data": "test3"})
        assert len(uow.get_events()) == 1

        uow.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
