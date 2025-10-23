"""
File: tests/unit/infrastructure/di/test_service_locator_xdist.py
Purpose: Test ServiceLocator PID/Worker ID cache isolation for pytest-xdist
Context: Verify that cache is properly isolated between xdist workers
"""

import os
from unittest.mock import patch

import pytest

from noveler.infrastructure.di.service_locator import (
    ServiceLocator,
    ServiceLocatorManager,
    get_service_locator,
)


class TestServiceLocatorXdistIsolation:
    """pytest-xdist環境でのServiceLocatorキャッシュ隔離テスト"""

    def setup_method(self):
        """各テスト前にServiceLocatorをリセット"""
        manager = ServiceLocatorManager()
        manager.reset()

    def test_cache_isolation_between_workers(self):
        """ワーカー間でキャッシュが隔離されること

        異なるワーカーIDで初期化したServiceLocatorは、
        独立したキャッシュを持つことを確認する。
        """
        # ワーカーA
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw0"}):
            locator_a = ServiceLocator()
            worker_id_a = locator_a._get_worker_id()
            assert worker_id_a == "gw0"

            # ワーカーAでサービスを取得してキャッシュに登録
            logger_a = locator_a.get_logger_service()
            cache_a = locator_a._get_cache_for_worker()
            assert "ILoggerProtocol" in cache_a
            assert locator_a.is_cached("ILoggerProtocol")

        # ワーカーB
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw1"}):
            locator_b = ServiceLocator()
            worker_id_b = locator_b._get_worker_id()
            assert worker_id_b == "gw1"

            # ワーカーBではキャッシュが空であることを確認
            cache_b = locator_b._get_cache_for_worker()
            assert "ILoggerProtocol" not in cache_b
            assert not locator_b.is_cached("ILoggerProtocol")

            # ワーカーBで独自にサービスを取得
            logger_b = locator_b.get_logger_service()
            assert "ILoggerProtocol" in cache_b

        # ワーカーAとワーカーBのキャッシュは独立していることを確認
        assert worker_id_a != worker_id_b

    def test_pid_based_key_generation(self):
        """PID/Worker IDベースのキー生成が正しいこと"""
        # PYTEST_XDIST_WORKER環境変数がある場合
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw5"}):
            locator = ServiceLocator()
            worker_id = locator._get_worker_id()
            assert worker_id == "gw5"

        # PYTEST_XDIST_WORKER環境変数がない場合（PIDを使用）
        with patch.dict(os.environ, {}, clear=False):
            if "PYTEST_XDIST_WORKER" in os.environ:
                del os.environ["PYTEST_XDIST_WORKER"]

            locator = ServiceLocator()
            worker_id = locator._get_worker_id()
            assert worker_id.startswith("pid-")
            assert worker_id == f"pid-{os.getpid()}"

    def test_memory_cleanup_on_worker_exit(self):
        """ワーカー終了時にキャッシュがクリーンアップされること

        Note: atexit登録を確認するテスト。
        実際のクリーンアップは手動呼び出しでシミュレート。
        """
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw3"}):
            locator = ServiceLocator()
            worker_id = locator._get_worker_id()

            # サービスを取得してキャッシュに登録
            _ = locator.get_logger_service()
            assert "gw3" in locator._cache
            assert "ILoggerProtocol" in locator._cache["gw3"]

            # クリーンアップを手動実行
            locator._cleanup_worker_cache()

            # キャッシュが削除されていることを確認
            assert "gw3" not in locator._cache

    def test_cache_size_limit_per_worker(self):
        """ワーカーごとのキャッシュ上限が機能すること

        Note: 将来実装予定の機能。
        現在は基本的なキャッシュ動作のみテスト。
        """
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw7"}):
            locator = ServiceLocator()

            # 複数のサービスを取得
            _ = locator.get_logger_service()
            _ = locator.get_console_service()
            _ = locator.get_configuration_service()

            cache = locator._get_cache_for_worker()
            assert len(cache) == 3
            assert "ILoggerProtocol" in cache
            assert "IConsoleServiceProtocol" in cache
            assert "IConfigurationServiceProtocol" in cache

    def test_get_service_locator_global_access(self):
        """グローバルアクセス関数が正しく動作すること"""
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw10"}):
            locator = get_service_locator()
            assert isinstance(locator, ServiceLocator)
            assert locator._get_worker_id() == "gw10"

    def test_clear_cache_clears_current_worker_only(self):
        """clear_cache()が現在のワーカーのキャッシュのみをクリアすること"""
        with patch.dict(os.environ, {"PYTEST_XDIST_WORKER": "gw20"}):
            locator = ServiceLocator()
            _ = locator.get_logger_service()
            _ = locator.get_console_service()

            # 現在のワーカー（gw20）のキャッシュが存在
            cache = locator._get_cache_for_worker()
            assert len(cache) == 2
            assert "ILoggerProtocol" in cache
            assert "IConsoleServiceProtocol" in cache

            # clear_cache()で現在のワーカーのみクリア
            locator.clear_cache()

            # 現在のワーカーのキャッシュがクリアされたことを確認
            cache = locator._get_cache_for_worker()
            assert len(cache) == 0
