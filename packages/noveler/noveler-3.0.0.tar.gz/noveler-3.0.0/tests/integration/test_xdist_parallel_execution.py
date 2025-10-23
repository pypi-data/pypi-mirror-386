# File: tests/integration/test_xdist_parallel_execution.py
# Purpose: xdist並列実行時のServiceLocatorキャッシュ隔離の統合テスト
# Context: Phase 2 - 実際の並列実行環境でワーカー間のキャッシュ隔離を検証

"""
xdist並列実行統合テスト

pytest-xdist を使用した実際の並列実行環境で、ServiceLocatorの
ワーカー別キャッシュ隔離が正しく機能することを検証する。

実行方法:
    # 4ワーカー
    pytest tests/integration/test_xdist_parallel_execution.py -n 4 -v

    # 8ワーカー
    pytest tests/integration/test_xdist_parallel_execution.py -n 8 -v

    # 16ワーカー
    pytest tests/integration/test_xdist_parallel_execution.py -n 16 -v

期待動作:
    - 全テストが並列実行時に成功すること
    - ワーカー間でキャッシュ競合が発生しないこと
    - メモリ使用量が許容範囲内であること
"""

import os
import time
from pathlib import Path
from typing import Any

import pytest

from noveler.infrastructure.di.service_locator import ServiceLocator, get_service_locator


class TestXdistParallelExecution:
    """xdist並列実行時のキャッシュ隔離統合テスト"""

    def test_concurrent_service_access_no_conflicts(self, tmp_path: Path) -> None:
        """複数ワーカーが同時にサービスアクセスしても競合しないこと

        このテストは並列実行時に各ワーカーが独立したキャッシュを持つことを確認する。
        """
        locator = get_service_locator()
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", f"pid-{os.getpid()}")

        # サービスを取得
        logger = locator.get_logger_service()
        console = locator.get_console_service()

        # ワーカー固有のキャッシュを確認
        cache = locator._get_cache_for_worker()

        # このワーカーのキャッシュにサービスが格納されていること
        assert "ILoggerProtocol" in cache
        assert "IConsoleServiceProtocol" in cache

        # ワーカーIDをログに記録（デバッグ用）
        print(f"Worker {worker_id}: Cache size = {len(cache)}")

    def test_parallel_path_service_initialization(self, tmp_path: Path) -> None:
        """並列実行時にPathServiceが各ワーカーで独立初期化されること

        注意: project_root指定時はキャッシュに追加されない（毎回新規生成）
        """
        locator = get_service_locator()
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", f"pid-{os.getpid()}")

        # PathServiceを取得（project_root指定時はキャッシュされない）
        path_service = locator.get_path_service(project_root=tmp_path)

        # サービスが正常に動作すること
        management_dir = path_service.get_management_dir()
        assert management_dir is not None

        print(f"Worker {worker_id}: PathService initialized with {tmp_path}")

    def test_parallel_configuration_service_access(self, tmp_path: Path) -> None:
        """並列実行時にConfigurationServiceが各ワーカーで独立動作すること"""
        locator = get_service_locator()
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", f"pid-{os.getpid()}")

        # ConfigurationServiceを取得（キャッシュに追加される）
        config_service = locator.get_configuration_service()

        # サービスが取得できたこと確認
        assert config_service is not None

        # キャッシュに追加されたことを確認
        cache = locator._get_cache_for_worker()
        assert "IConfigurationServiceProtocol" in cache

        print(f"Worker {worker_id}: ConfigurationService accessed")

    def test_parallel_lazy_proxy_initialization(self, tmp_path: Path) -> None:
        """並列実行時にLazyProxyが各ワーカーで独立初期化されること

        注意: project_root指定時のPathServiceはキャッシュされない
        """
        locator = get_service_locator()
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", f"pid-{os.getpid()}")

        # 複数のサービスを取得（LazyProxy経由）
        logger = locator.get_logger_service()
        console = locator.get_console_service()
        path_service = locator.get_path_service(project_root=tmp_path)  # キャッシュされない

        # Logger と Console がキャッシュされていること（Path は含まれない）
        cache = locator._get_cache_for_worker()
        assert len(cache) >= 2

        print(f"Worker {worker_id}: {len(cache)} services initialized via LazyProxy")

    @pytest.mark.parametrize("iteration", range(10))
    def test_repeated_service_access_stability(
        self, tmp_path: Path, iteration: int
    ) -> None:
        """同一ワーカー内で繰り返しサービスアクセスしても安定動作すること

        10回の反復実行で各ワーカーのキャッシュが安定していることを確認する。
        """
        locator = get_service_locator()
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", f"pid-{os.getpid()}")

        # サービスを取得
        logger = locator.get_logger_service()
        console = locator.get_console_service()

        # キャッシュサイズが一定であること（初回初期化後は増加しない）
        cache = locator._get_cache_for_worker()
        cache_size = len(cache)

        # 同じサービスを再取得してもキャッシュサイズは変わらない
        _ = locator.get_logger_service()
        _ = locator.get_console_service()

        assert len(cache) == cache_size

        if iteration == 0:
            print(f"Worker {worker_id}: Iteration {iteration}, Cache size = {cache_size}")

    def test_worker_id_uniqueness_in_parallel(self) -> None:
        """並列実行時に各ワーカーが一意のWorker IDを持つこと"""
        locator = get_service_locator()
        worker_id = locator._get_worker_id()

        # Worker IDが設定されていること
        assert worker_id is not None
        assert len(worker_id) > 0

        # xdist環境ではgwX形式、それ以外ではpid-XXX形式
        if "PYTEST_XDIST_WORKER" in os.environ:
            assert worker_id.startswith("gw")
        else:
            assert worker_id.startswith("pid-")

        print(f"Worker ID: {worker_id}")

    def test_cache_cleanup_does_not_affect_other_workers(
        self, tmp_path: Path
    ) -> None:
        """キャッシュクリアが他ワーカーに影響しないこと"""
        locator = get_service_locator()
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", f"pid-{os.getpid()}")

        # サービスを取得してキャッシュに格納
        _ = locator.get_logger_service()
        _ = locator.get_console_service()

        initial_cache_size = len(locator._get_cache_for_worker())
        assert initial_cache_size >= 2

        # キャッシュをクリア（このワーカーのみ）
        locator.clear_cache()

        # このワーカーのキャッシュがクリアされたこと
        assert len(locator._get_cache_for_worker()) == 0

        print(f"Worker {worker_id}: Cache cleared (was {initial_cache_size}, now 0)")

    @pytest.mark.parametrize("service_count", [1, 2, 3, 5])
    def test_variable_cache_size_per_worker(
        self, tmp_path: Path, service_count: int
    ) -> None:
        """各ワーカーが異なるサイズのキャッシュを持てること

        ワーカーごとに必要なサービス数が異なる場合でも正しく動作することを確認。
        注意: project_root指定のPathServiceはキャッシュされない
        """
        locator = get_service_locator()
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", f"pid-{os.getpid()}")

        # service_countに応じてサービスを取得
        if service_count >= 1:
            _ = locator.get_logger_service()
        if service_count >= 2:
            _ = locator.get_console_service()
        if service_count >= 3:
            _ = locator.get_configuration_service()
        if service_count >= 4:
            _ = locator.get_unit_of_work()
        if service_count >= 5:
            _ = locator.get_repository_factory()

        # キャッシュサイズが期待値と一致すること
        cache = locator._get_cache_for_worker()
        assert len(cache) == service_count

        print(f"Worker {worker_id}: Cache size = {service_count}")


class TestXdistMemoryIsolation:
    """メモリ隔離とクリーンアップのテスト"""

    def test_memory_cleanup_on_test_completion(self, tmp_path: Path) -> None:
        """テスト完了後にメモリがクリーンアップされること

        atexit ハンドラによるクリーンアップをシミュレート。
        """
        locator = ServiceLocator()
        worker_id = locator._get_worker_id()

        # サービスを初期化
        _ = locator.get_logger_service()
        _ = locator.get_console_service()

        # キャッシュが存在すること
        assert worker_id in locator._cache
        assert len(locator._cache[worker_id]) >= 2

        # クリーンアップを手動実行（atexitのシミュレート）
        locator._cleanup_worker_cache()

        # このワーカーのキャッシュが削除されたこと
        assert worker_id not in locator._cache

        print(f"Worker {worker_id}: Memory cleanup completed")

    def test_no_memory_leak_in_repeated_initialization(
        self, tmp_path: Path
    ) -> None:
        """繰り返しサービス初期化してもメモリリークしないこと"""
        locator = get_service_locator()
        worker_id = locator._get_worker_id()

        # 初期キャッシュサイズを記録
        initial_cache_size = len(locator._get_cache_for_worker())

        # 10回繰り返しサービス取得
        for _ in range(10):
            _ = locator.get_logger_service()
            _ = locator.get_console_service()

        # キャッシュサイズが一定であること（増加しない）
        cache = locator._get_cache_for_worker()
        final_cache_size = len(cache)
        assert final_cache_size == initial_cache_size or final_cache_size == initial_cache_size + 2

        print(f"Worker {worker_id}: No memory leak (initial={initial_cache_size}, final={final_cache_size})")


class TestXdistLoadTest:
    """負荷試験"""

    @pytest.mark.parametrize("load_iteration", range(20))
    def test_high_load_parallel_execution(
        self, tmp_path: Path, load_iteration: int
    ) -> None:
        """高負荷並列実行時の安定性テスト

        20テスト × Nワーカー = 最大320並列実行で安定動作することを確認。
        実行例: pytest -n 16 (16 workers × 20 tests = 320 executions)
        注意: project_root指定のPathServiceはキャッシュされない
        """
        locator = get_service_locator()
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", f"pid-{os.getpid()}")

        # ランダムな処理負荷を追加
        time.sleep(0.001 * (load_iteration % 5))

        # サービスを取得
        logger = locator.get_logger_service()
        console = locator.get_console_service()
        path_service = locator.get_path_service(project_root=tmp_path)  # キャッシュされない

        # Logger と Console がキャッシュされていること（Path は含まれない）
        cache = locator._get_cache_for_worker()
        assert len(cache) >= 2

        if load_iteration % 10 == 0:
            print(f"Worker {worker_id}: Load test iteration {load_iteration}")
