#!/usr/bin/env python3
"""ComprehensivePerformanceOptimizerのユニットテスト

このテストは以下をカバーします:
- パフォーマンス最適化機能
- キャッシュ管理システム
- ファイルI/O最適化
- YAML処理最適化
- メモリ効率化


仕様書: SPEC-INFRASTRUCTURE
"""

import tempfile
import time
from pathlib import Path
from typing import NoReturn

import pytest

# パフォーマンス最適化システムが存在する場合のみテストを実行
try:
    from noveler.infrastructure.performance.comprehensive_performance_optimizer import (
        CacheManager,
        ComprehensivePerformanceOptimizer,
        FileIOOptimizer,
        MemoryOptimizer,
        PerformanceProfiler,
        YAMLOptimizer,
        performance_monitor,
    )

    PERFORMANCE_OPTIMIZER_AVAILABLE = True
except ImportError:
    PERFORMANCE_OPTIMIZER_AVAILABLE = False


@pytest.mark.skipif(not PERFORMANCE_OPTIMIZER_AVAILABLE, reason="Performance optimizer not available")
class TestPerformanceProfiler:
    """PerformanceProfilerのテスト"""

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_profiler_initialization(self):
        """プロファイラー初期化テスト"""
        profiler = PerformanceProfiler("test_operation")
        assert profiler.operation_name == "test_operation"
        assert profiler.start_time is not None
        assert profiler.memory_before > 0

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_profiler_stop_and_results(self):
        """プロファイラー停止・結果取得テスト"""
        profiler = PerformanceProfiler("test_operation")
        time.sleep(0.01)  # 短い処理時間をシミュレート

        results = profiler.stop()

        assert "operation_name" in results
        assert "execution_time" in results
        assert "memory_peak_mb" in results
        assert results["execution_time"] > 0


@pytest.mark.skipif(not PERFORMANCE_OPTIMIZER_AVAILABLE, reason="Performance optimizer not available")
class TestCacheManager:
    """CacheManagerのテスト"""

    @pytest.fixture
    def cache_manager(self):
        """テスト用キャッシュマネージャー"""
        return CacheManager(max_size=100, ttl_seconds=300)

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_cache_initialization(self, cache_manager):
        """キャッシュマネージャー初期化テスト"""
        assert cache_manager.max_size == 100
        assert cache_manager.ttl_seconds == 300
        assert cache_manager.hits == 0
        assert cache_manager.misses == 0

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_cache_set_get(self, cache_manager):
        """キャッシュ設定・取得テスト"""
        test_key = "test_key"
        test_value = {"data": "test_data"}

        # データ設定
        cache_manager.set(test_key, test_value)

        # データ取得
        cached_value = cache_manager.get(test_key)

        assert cached_value == test_value
        assert cache_manager.hits == 1

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_cache_miss(self, cache_manager):
        """キャッシュミステスト"""
        non_existent_key = "non_existent_key"

        cached_value = cache_manager.get(non_existent_key)

        assert cached_value is None
        assert cache_manager.misses == 1

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_cache_hit_ratio(self, cache_manager):
        """キャッシュヒット率テスト"""
        # データ設定
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")

        # ヒット
        cache_manager.get("key1")
        cache_manager.get("key2")

        # ミス
        cache_manager.get("key3")

        hit_ratio = cache_manager.get_hit_ratio()
        assert 0.5 <= hit_ratio <= 1.0  # 2ヒット1ミスなので約0.67

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_cache_invalidate(self, cache_manager):
        """キャッシュ無効化テスト"""
        test_key = "test_key"
        cache_manager.set(test_key, "test_value")

        # 無効化前は取得できる
        assert cache_manager.get(test_key) is not None

        # 無効化
        cache_manager.invalidate(test_key)

        # 無効化後は取得できない
        assert cache_manager.get(test_key) is None

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_cache_clear(self, cache_manager):
        """キャッシュクリアテスト"""
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")

        # クリア前は取得できる
        assert cache_manager.get("key1") is not None
        assert cache_manager.get("key2") is not None

        # クリア
        cache_manager.clear()

        # クリア後は取得できない
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None


@pytest.mark.skipif(not PERFORMANCE_OPTIMIZER_AVAILABLE, reason="Performance optimizer not available")
class TestFileIOOptimizer:
    """FileIOOptimizerのテスト"""

    @pytest.fixture
    def file_optimizer(self):
        """テスト用ファイルI/O最適化器"""
        return FileIOOptimizer()

    @pytest.fixture
    def temp_file(self):
        """テスト用一時ファイル"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test content\nLine 2\nLine 3")
            temp_path = Path(f.name)

        yield temp_path

        # クリーンアップ
        if temp_path.exists():
            temp_path.unlink()

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_optimized_read(self, file_optimizer, temp_file):
        """最適化読み込みテスト"""
        content = file_optimizer.optimized_read(temp_file)

        assert isinstance(content, str)
        assert "Test content" in content
        assert "Line 2" in content
        assert "Line 3" in content

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_batch_write(self, file_optimizer, tmp_path):
        """バッチ書き込みテスト"""
        write_data = [
            (tmp_path / "file1.txt", "Content 1"),
            (tmp_path / "file2.txt", "Content 2"),
            (tmp_path / "file3.txt", "Content 3"),
        ]

        # バッチ書き込み実行
        results = file_optimizer.batch_write(write_data)

        # 結果検証
        assert len(results) == 3
        for file_path, success in results:
            assert success is True
            assert file_path.exists()
            assert file_path.read_text() in ["Content 1", "Content 2", "Content 3"]

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_cached_read(self, file_optimizer, temp_file):
        """キャッシュ読み込みテスト"""
        # 1回目の読み込み（キャッシュされる）
        content1 = file_optimizer.cached_read(temp_file)

        # 2回目の読み込み（キャッシュから取得）
        content2 = file_optimizer.cached_read(temp_file)

        assert content1 == content2
        assert isinstance(content1, str)

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_async_write(self, file_optimizer, tmp_path):
        """非同期書き込みテスト"""
        output_file = tmp_path / "async_output.txt"
        test_content = "Async write test content"

        # 非同期書き込み実行（同期的にテスト）
        success = file_optimizer.async_write(output_file, test_content)

        assert success is True
        assert output_file.exists()
        assert output_file.read_text() == test_content


@pytest.mark.skipif(not PERFORMANCE_OPTIMIZER_AVAILABLE, reason="Performance optimizer not available")
class TestYAMLOptimizer:
    """YAMLOptimizerのテスト"""

    @pytest.fixture
    def yaml_optimizer(self):
        """テスト用YAML最適化器"""
        return YAMLOptimizer()

    @pytest.fixture
    def sample_yaml_data(self):
        """テスト用YAMLデータ"""
        return {
            "title": "テストプロジェクト",
            "author": "テスト作者",
            "episodes": {"total_planned": 100, "completed": 10},
            "settings": {"genre": "ファンタジー", "target_audience": "一般"},
        }

    @pytest.fixture
    def temp_yaml_file(self, sample_yaml_data):
        """テスト用YAML一時ファイル"""
        import yaml

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml", encoding="utf-8") as f:
            yaml.dump(sample_yaml_data, f, allow_unicode=True)
            temp_path = Path(f.name)

        yield temp_path

        # クリーンアップ
        if temp_path.exists():
            temp_path.unlink()

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_optimized_load(self, yaml_optimizer, temp_yaml_file, sample_yaml_data):
        """最適化YAML読み込みテスト"""
        loaded_data = yaml_optimizer.optimized_load(temp_yaml_file)

        assert loaded_data == sample_yaml_data
        assert loaded_data["title"] == "テストプロジェクト"
        assert loaded_data["episodes"]["total_planned"] == 100

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_optimized_dump(self, yaml_optimizer, sample_yaml_data, tmp_path):
        """最適化YAML書き込みテスト"""
        output_file = tmp_path / "output.yaml"

        success = yaml_optimizer.optimized_dump(sample_yaml_data, output_file)

        assert success is True
        assert output_file.exists()

        # 書き込まれた内容を確認
        import yaml

        with output_file.open("r", encoding="utf-8") as f:
            loaded_data = yaml.safe_load(f)

        assert loaded_data == sample_yaml_data

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_cached_load(self, yaml_optimizer, temp_yaml_file):
        """キャッシュYAML読み込みテスト"""
        # 1回目の読み込み（キャッシュされる）
        data1 = yaml_optimizer.cached_load(temp_yaml_file)

        # 2回目の読み込み（キャッシュから取得）
        data2 = yaml_optimizer.cached_load(temp_yaml_file)

        assert data1 == data2
        assert isinstance(data1, dict)

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_batch_load(self, yaml_optimizer, tmp_path, sample_yaml_data):
        """バッチYAML読み込みテスト"""
        import yaml

        # 複数のYAMLファイルを作成
        yaml_files = []
        for i in range(3):
            file_path = tmp_path / f"test{i}.yaml"
            with file_path.open("w", encoding="utf-8") as f:
                test_data = sample_yaml_data.copy()
                test_data["title"] = f"テストプロジェクト{i}"
                yaml.dump(test_data, f, allow_unicode=True)
            yaml_files.append(file_path)

        # バッチ読み込み実行
        results = yaml_optimizer.batch_load(yaml_files)

        # 結果検証
        assert len(results) == 3
        for i, (file_path, data, success) in enumerate(results):
            assert success is True
            assert data["title"] == f"テストプロジェクト{i}"


@pytest.mark.skipif(not PERFORMANCE_OPTIMIZER_AVAILABLE, reason="Performance optimizer not available")
class TestMemoryOptimizer:
    """MemoryOptimizerのテスト"""

    @pytest.fixture
    def memory_optimizer(self):
        """テスト用メモリ最適化器"""
        return MemoryOptimizer()

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_get_memory_usage(self, memory_optimizer):
        """メモリ使用量取得テスト"""
        memory_usage = memory_optimizer.get_memory_usage()

        assert isinstance(memory_usage, dict)
        assert "rss_mb" in memory_usage
        assert "vms_mb" in memory_usage
        assert memory_usage["rss_mb"] > 0

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_force_garbage_collection(self, memory_optimizer):
        """ガベージコレクション強制実行テスト"""
        # 大きなオブジェクトを作成
        large_data = [list(range(1000)) for _ in range(100)]

        # メモリ使用量取得
        memory_optimizer.get_memory_usage()

        # データを削除
        del large_data

        # ガベージコレクション実行
        collected = memory_optimizer.force_garbage_collection()

        # 結果検証
        assert isinstance(collected, int)
        assert collected >= 0

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_chunk_process_large_data(self, memory_optimizer):
        """大容量データのチャンク処理テスト"""
        # 大容量データ作成
        large_dataset = list(range(1000))

        def simple_processor(chunk):
            return [x * 2 for x in chunk]

        # チャンク処理実行
        results = memory_optimizer.chunk_process_large_data(
            data=large_dataset, processor_func=simple_processor, chunk_size=100
        )

        # 結果検証
        assert len(results) == 1000
        assert results[0] == 0  # 0 * 2
        assert results[999] == 1998  # 999 * 2

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_optimize_data_structure(self, memory_optimizer):
        """データ構造最適化テスト"""
        # 非効率なデータ構造
        inefficient_data = {
            "large_list": list(range(10000)),
            "repeated_strings": ["same_string"] * 1000,
            "nested_dicts": {f"key{i}": {"value": i} for i in range(100)},
        }

        # データ構造最適化実行
        optimized_data = memory_optimizer.optimize_data_structure(inefficient_data)

        # 結果検証
        assert isinstance(optimized_data, dict)
        # 最適化の具体的な効果は実装に依存


@pytest.mark.skipif(not PERFORMANCE_OPTIMIZER_AVAILABLE, reason="Performance optimizer not available")
class TestComprehensivePerformanceOptimizer:
    """ComprehensivePerformanceOptimizerのメインテスト"""

    @pytest.fixture
    def optimizer(self):
        """テスト用包括的パフォーマンス最適化器"""
        return ComprehensivePerformanceOptimizer()

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_optimizer_initialization(self, optimizer):
        """最適化器初期化テスト"""
        assert optimizer.profiler is not None
        assert optimizer.cache_manager is not None
        assert optimizer.file_io_optimizer is not None
        assert optimizer.yaml_optimizer is not None
        assert optimizer.memory_optimizer is not None

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_start_stop_profiling(self, optimizer):
        """プロファイリング開始・停止テスト"""
        operation_name = "test_operation"

        # プロファイリング開始
        optimizer.start_profiling(operation_name)

        # 短い処理をシミュレート
        time.sleep(0.01)

        # プロファイリング停止
        results = optimizer.stop_profiling()

        # 結果検証
        assert "operation_name" in results
        assert "execution_time" in results
        assert results["operation_name"] == operation_name

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_optimize_file_operations(self, optimizer, tmp_path):
        """ファイル操作最適化テスト"""
        # テストファイル作成
        test_files = []
        for i in range(3):
            file_path = tmp_path / f"test{i}.txt"
            file_path.write_text(f"Content {i}")
            test_files.append(file_path)

        # ファイル操作最適化実行
        results = optimizer.optimize_file_operations(test_files, "read")

        # 結果検証
        assert isinstance(results, list)
        assert len(results) == 3

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_optimize_yaml_processing(self, optimizer, tmp_path):
        """YAML処理最適化テスト"""
        # テストYAMLファイル作成
        import yaml

        yaml_files = []
        for i in range(2):
            file_path = tmp_path / f"test{i}.yaml"
            test_data = {"title": f"Test {i}", "value": i}
            with file_path.open("w", encoding="utf-8") as f:
                yaml.dump(test_data, f)
            yaml_files.append(file_path)

        # YAML処理最適化実行
        results = optimizer.optimize_yaml_processing(yaml_files, "load")

        # 結果検証
        assert isinstance(results, list)
        assert len(results) == 2

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_optimize_memory_usage(self, optimizer):
        """メモリ使用量最適化テスト"""
        # 最適化前のメモリ使用量取得
        optimizer.memory_optimizer.get_memory_usage()

        # メモリ最適化実行
        optimization_results = optimizer.optimize_memory_usage()

        # 結果検証
        assert isinstance(optimization_results, dict)
        assert "before_memory_mb" in optimization_results
        assert "after_memory_mb" in optimization_results

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_generate_performance_report(self, optimizer):
        """パフォーマンスレポート生成テスト"""
        # いくつかの操作を実行してデータを蓄積
        optimizer.start_profiling("test_operation_1")
        time.sleep(0.01)
        optimizer.stop_profiling()

        optimizer.start_profiling("test_operation_2")
        time.sleep(0.01)
        optimizer.stop_profiling()

        # レポート生成
        report = optimizer.generate_performance_report()

        # 結果検証
        assert isinstance(report, dict)
        assert "summary" in report
        assert "profiling_results" in report
        assert "cache_performance" in report


@pytest.mark.skipif(not PERFORMANCE_OPTIMIZER_AVAILABLE, reason="Performance optimizer not available")
class TestPerformanceMonitorDecorator:
    """performance_monitorデコレーターのテスト"""

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_decorator_basic_function(self):
        """基本的な関数のデコレーターテスト"""

        @performance_monitor("test_function")
        @pytest.mark.spec("SPEC-INFRASTRUCTURE")
        def test_function(x, y):
            time.sleep(0.01)  # 短い処理時間をシミュレート
            return x + y

        # 関数実行
        result = test_function(2, 3)

        # 結果検証
        assert result == 5

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_decorator_with_exception(self):
        """例外発生時のデコレーターテスト"""

        @performance_monitor("error_function")
        def error_function() -> NoReturn:
            time.sleep(0.01)
            msg = "Test error"
            raise ValueError(msg)

        # 例外が適切に伝播されることを確認
        with pytest.raises(ValueError, match="Test error"):
            error_function()

    @pytest.mark.asyncio
    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    async def test_decorator_async_function(self):
        """非同期関数のデコレーターテスト"""

        @performance_monitor("async_test_function")
        async def async_test_function(delay) -> str:
            await asyncio.sleep(delay)
            return "async_result"

        import asyncio

        # 非同期関数実行
        result = await async_test_function(0.01)

        # 結果検証
        assert result == "async_result"


@pytest.mark.integration
@pytest.mark.skipif(not PERFORMANCE_OPTIMIZER_AVAILABLE, reason="Performance optimizer not available")
class TestPerformanceOptimizerIntegration:
    """統合テスト（実際のファイルシステムとの連携）"""

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_real_world_yaml_optimization(self, tmp_path):
        """実際のYAMLファイル最適化統合テスト"""
        optimizer = ComprehensivePerformanceOptimizer()

        # 実際のプロジェクト設定ファイルを作成
        import yaml

        config_data = {
            "title": "統合テストプロジェクト",
            "author": "テスト作者",
            "episodes": {"total_planned": 100, "completed": 10, "current_episode": 11},
            "characters": [
                {"name": "主人公", "role": "主人公", "age": 20},
                {"name": "ヒロイン", "role": "ヒロイン", "age": 18},
                {"name": "ライバル", "role": "ライバル", "age": 22},
            ],
            "settings": {"world": "ファンタジー世界", "time_period": "中世", "magic_system": "魔法学院制"},
        }

        config_file = tmp_path / "プロジェクト設定.yaml"
        with config_file.open("w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True)

        # YAML最適化実行
        optimizer.start_profiling("yaml_optimization_integration")
        loaded_data = optimizer.yaml_optimizer.cached_load(config_file)
        results = optimizer.stop_profiling()

        # 結果検証
        assert loaded_data == config_data
        assert results["execution_time"] > 0

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_real_world_file_batch_processing(self, tmp_path):
        """実際のファイルバッチ処理統合テスト"""
        optimizer = ComprehensivePerformanceOptimizer()

        # 複数のテキストファイルを作成
        test_files = []
        for i in range(10):
            file_path = tmp_path / f"episode_{i:03d}.txt"
            content = f"第{i + 1}話\n\n" + "テスト内容 " * 100  # 適度な長さのコンテンツ
            file_path.write_text(content, encoding="utf-8")
            test_files.append(file_path)

        # バッチ処理実行
        optimizer.start_profiling("batch_file_processing")
        batch_results = optimizer.file_io_optimizer.batch_read(test_files)
        profiling_results = optimizer.stop_profiling()

        # 結果検証
        assert len(batch_results) == 10
        assert profiling_results["execution_time"] > 0

        for file_path, content, success in batch_results:
            assert success is True
            assert f"第{test_files.index(file_path) + 1}話" in content

    @pytest.mark.spec("SPEC-INFRASTRUCTURE")
    def test_memory_optimization_under_load(self):
        """負荷下でのメモリ最適化統合テスト"""
        optimizer = ComprehensivePerformanceOptimizer()

        # メモリ負荷をシミュレート
        large_datasets = []
        for i in range(5):
            large_data = {f"dataset_{i}": list(range(1000)), "metadata": {"size": 1000, "type": "test_data"}}
            large_datasets.append(large_data)

        # メモリ最適化実行
        optimizer.start_profiling("memory_optimization_under_load")
        optimization_results = optimizer.optimize_memory_usage()
        profiling_results = optimizer.stop_profiling()

        # データクリーンアップ
        del large_datasets

        # 結果検証
        assert "before_memory_mb" in optimization_results
        assert "after_memory_mb" in optimization_results
        assert profiling_results["execution_time"] > 0


if __name__ == "__main__":
    pytest.main([__file__])
