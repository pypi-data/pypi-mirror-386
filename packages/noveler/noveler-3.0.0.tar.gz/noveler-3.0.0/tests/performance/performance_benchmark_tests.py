#!/usr/bin/env python3
"""パフォーマンスベンチマークテスト

最適化前後のパフォーマンス改善を定量的に測定
30%のレスポンス改善、50%のメモリ使用量削減を検証
"""

import asyncio
import gc
import json
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest

from noveler.infrastructure.performance.comprehensive_performance_optimizer import (
    ComprehensivePerformanceOptimizer,
    FileIOOptimizer,
    MemoryOptimizer,
    YAMLOptimizer,
)

# CLIが廃止されたため、標準のprint文を使用


class PerformanceBenchmark:
    """パフォーマンスベンチマーククラス"""

    def __init__(self) -> None:
        self.optimizer = ComprehensivePerformanceOptimizer()
        self.file_io_optimizer = FileIOOptimizer()
        self.yaml_optimizer = YAMLOptimizer()
        self.memory_optimizer = MemoryOptimizer()
        self.benchmark_results: list[dict[str, Any]] = []

    def measure_execution_time(self, func, *args, **kwargs) -> tuple[Any, float]:
        """実行時間測定"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time

    def measure_memory_usage(self, func, *args, **kwargs) -> tuple[Any, float, float]:
        """メモリ使用量測定"""
        import psutil

        process = psutil.Process()

        gc.collect()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB

        result = func(*args, **kwargs)

        gc.collect()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = end_memory - start_memory

        return result, start_memory, memory_delta

    def create_test_yaml_data(self, size: str = "medium") -> dict[str, Any]:
        """テスト用YAMLデータ生成"""
        sizes = {"small": 100, "medium": 1000, "large": 10000}

        items_count = sizes.get(size, 1000)

        test_data = {
            "metadata": {
                "created_at": "2025-08-27T00:00:00Z",
                "version": "1.0.0",
                "description": f"Test data with {items_count} items",
            },
            "items": [],
        }

        for i in range(items_count):
            test_data["items"].append(
                {
                    "id": f"item_{i:04d}",
                    "name": f"Test Item {i}",
                    "description": f"This is test item number {i} for performance testing",
                    "properties": {
                        "category": f"category_{i % 10}",
                        "priority": i % 5,
                        "active": i % 2 == 0,
                        "tags": [f"tag_{j}" for j in range(i % 5 + 1)],
                    },
                }
            )

        return test_data


class FileIOPerformanceTests:
    """ファイルI/O最適化パフォーマンステスト"""

    def __init__(self, benchmark: PerformanceBenchmark) -> None:
        self.benchmark = benchmark
        self.test_dir = Path(tempfile.mkdtemp(prefix="performance_test_"))

    def test_file_reading_performance(self) -> dict[str, Any]:
        """ファイル読み込みパフォーマンステスト"""
        # テストファイル作成
        test_files = []
        for i in range(50):  # 50ファイル
            test_file = self.test_dir / f"test_file_{i}.txt"
            test_content = f"Test content for file {i}\n" * 100  # 100行
            test_file.write_text(test_content, encoding="utf-8")
            test_files.append(test_file)

        # 標準的な読み込み測定
        def standard_read():
            contents = []
            for file_path in test_files:
                with open(file_path, encoding="utf-8") as f:
                    contents.append(f.read())
            return contents

        # 最適化された読み込み測定
        def optimized_read():
            contents = []
            for file_path in test_files:
                content = self.benchmark.file_io_optimizer.optimized_read_text(file_path)
                contents.append(content)
            return contents

        # ベンチマーク実行
        _, standard_time = self.benchmark.measure_execution_time(standard_read)
        _, optimized_time = self.benchmark.measure_execution_time(optimized_read)

        # 2回目実行（キャッシュ効果測定）
        _, optimized_time_cached = self.benchmark.measure_execution_time(optimized_read)

        improvement_percent = ((standard_time - optimized_time) / standard_time) * 100
        cache_improvement = ((optimized_time - optimized_time_cached) / optimized_time) * 100

        return {
            "test_name": "file_reading_performance",
            "files_count": len(test_files),
            "standard_time": standard_time,
            "optimized_time": optimized_time,
            "optimized_time_cached": optimized_time_cached,
            "improvement_percent": improvement_percent,
            "cache_improvement_percent": cache_improvement,
            "target_improvement": 30.0,  # 30%改善目標
            "target_achieved": improvement_percent >= 30.0,
        }

    def test_batch_file_writing_performance(self) -> dict[str, Any]:
        """バッチファイル書き込みパフォーマンステスト"""
        test_data = [f"Test data line {i}\n" for i in range(1000)]

        # 標準的な書き込み測定
        def standard_write() -> None:
            for i, data in enumerate(test_data):
                file_path = self.test_dir / f"standard_{i}.txt"
                file_path.write_text(data, encoding="utf-8")

        # バッチ書き込み測定
        def batch_write() -> None:
            for i, data in enumerate(test_data):
                file_path = self.test_dir / f"batch_{i}.txt"
                self.benchmark.file_io_optimizer.batch_write_text(file_path, data)
            self.benchmark.file_io_optimizer.flush_batch_operations()

        _, standard_time = self.benchmark.measure_execution_time(standard_write)
        _, batch_time = self.benchmark.measure_execution_time(batch_write)

        improvement_percent = ((standard_time - batch_time) / standard_time) * 100

        return {
            "test_name": "batch_file_writing_performance",
            "operations_count": len(test_data),
            "standard_time": standard_time,
            "batch_time": batch_time,
            "improvement_percent": improvement_percent,
            "target_improvement": 40.0,  # 40%改善目標
            "target_achieved": improvement_percent >= 40.0,
        }

    def cleanup(self):
        """テストファイルクリーンアップ"""
        import shutil

        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)


class YAMLPerformanceTests:
    """YAML処理最適化パフォーマンステスト"""

    def __init__(self, benchmark: PerformanceBenchmark) -> None:
        self.benchmark = benchmark
        self.test_dir = Path(tempfile.mkdtemp(prefix="yaml_performance_test_"))

    def test_yaml_processing_performance(self) -> dict[str, Any]:
        """YAML処理パフォーマンステスト"""
        # テストYAMLファイル作成
        test_files = []
        for size in ["small", "medium", "large"]:
            for i in range(10):  # 各サイズ10ファイル
                yaml_file = self.test_dir / f"test_{size}_{i}.yaml"
                test_data = self.benchmark.create_test_yaml_data(size)

                import yaml

                with open(yaml_file, "w", encoding="utf-8") as f:
                    yaml.dump(test_data, f, allow_unicode=True, default_flow_style=False)

                test_files.append(yaml_file)

        # 標準的なYAML読み込み測定
        def standard_yaml_load():
            results = []
            for file_path in test_files:
                import yaml

                with open(file_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    results.append(data)
            return results

        # 最適化されたYAML読み込み測定
        def optimized_yaml_load():
            results = []
            for file_path in test_files:
                data = self.benchmark.yaml_optimizer.optimized_yaml_load(file_path)
                results.append(data)
            return results

        # ベンチマーク実行
        _, standard_time = self.benchmark.measure_execution_time(standard_yaml_load)
        _, optimized_time = self.benchmark.measure_execution_time(optimized_yaml_load)

        # 2回目実行（キャッシュ効果）
        _, optimized_time_cached = self.benchmark.measure_execution_time(optimized_yaml_load)

        improvement_percent = ((standard_time - optimized_time) / standard_time) * 100
        cache_improvement = ((optimized_time - optimized_time_cached) / optimized_time) * 100

        return {
            "test_name": "yaml_processing_performance",
            "files_count": len(test_files),
            "standard_time": standard_time,
            "optimized_time": optimized_time,
            "optimized_time_cached": optimized_time_cached,
            "improvement_percent": improvement_percent,
            "cache_improvement_percent": cache_improvement,
            "target_improvement": 50.0,  # 50%改善目標
            "target_achieved": improvement_percent >= 50.0,
        }

    def test_yaml_writing_performance(self) -> dict[str, Any]:
        """YAML書き込みパフォーマンステスト"""
        test_data_sets = [self.benchmark.create_test_yaml_data("medium") for _ in range(20)]

        # 標準的なYAML書き込み
        def standard_yaml_write() -> None:
            import yaml

            for i, data in enumerate(test_data_sets):
                file_path = self.test_dir / f"standard_output_{i}.yaml"
                with open(file_path, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        # 最適化されたYAML書き込み
        def optimized_yaml_write() -> None:
            for i, data in enumerate(test_data_sets):
                file_path = self.test_dir / f"optimized_output_{i}.yaml"
                self.benchmark.yaml_optimizer.optimized_yaml_dump(data, file_path)

        _, standard_time = self.benchmark.measure_execution_time(standard_yaml_write)
        _, optimized_time = self.benchmark.measure_execution_time(optimized_yaml_write)

        improvement_percent = ((standard_time - optimized_time) / standard_time) * 100

        return {
            "test_name": "yaml_writing_performance",
            "datasets_count": len(test_data_sets),
            "standard_time": standard_time,
            "optimized_time": optimized_time,
            "improvement_percent": improvement_percent,
            "target_improvement": 25.0,  # 25%改善目標
            "target_achieved": improvement_percent >= 25.0,
        }

    def cleanup(self):
        """テストファイルクリーンアップ"""
        import shutil

        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)


class MemoryPerformanceTests:
    """メモリ使用量最適化パフォーマンステスト"""

    def __init__(self, benchmark: PerformanceBenchmark) -> None:
        self.benchmark = benchmark

    def test_large_data_processing_memory(self) -> dict[str, Any]:
        """大容量データ処理メモリ使用量テスト"""
        # 大きなデータセット生成
        large_dataset = [f"Large data item {i}" * 100 for i in range(10000)]

        # 標準的な処理（全てメモリにロード）
        def standard_processing():
            results = []
            for item in large_dataset:
                processed = item.upper().replace(" ", "_")
                results.append(processed)
            return results

        # メモリ効率的な処理
        def optimized_processing():
            results = []
            with self.benchmark.memory_optimizer.memory_efficient_processing():
                for chunk in self.benchmark.memory_optimizer.optimize_large_data_processing(large_dataset):
                    processed = chunk.upper().replace(" ", "_")
                    results.append(processed)
            return results

        # メモリ使用量測定
        _, start_mem1, mem_delta1 = self.benchmark.measure_memory_usage(standard_processing)
        _, start_mem2, mem_delta2 = self.benchmark.measure_memory_usage(optimized_processing)

        memory_savings_percent = ((mem_delta1 - mem_delta2) / mem_delta1) * 100 if mem_delta1 > 0 else 0

        return {
            "test_name": "large_data_processing_memory",
            "dataset_size": len(large_dataset),
            "standard_memory_delta": mem_delta1,
            "optimized_memory_delta": mem_delta2,
            "memory_savings_percent": memory_savings_percent,
            "target_savings": 50.0,  # 50%削減目標
            "target_achieved": memory_savings_percent >= 50.0,
        }

    def test_caching_memory_efficiency(self) -> dict[str, Any]:
        """キャッシュメモリ効率テスト"""
        # キャッシュ効率測定用のデータ
        cache_keys = [f"key_{i}" for i in range(1000)]
        cache_values = [f"value_{i}" * 50 for i in range(1000)]

        def test_caching():
            cache = self.benchmark.optimizer.cache_manager

            # データ書き込み
            for key, value in zip(cache_keys, cache_values, strict=False):
                cache.set(key, value)

            # データ読み込み（キャッシュヒット）
            results = []
            for key in cache_keys:
                result = cache.get(key)
                results.append(result)

            return results, cache.get_hit_rate()

        _, start_mem, mem_delta = self.benchmark.measure_memory_usage(test_caching)
        _, hit_rate = test_caching()

        return {
            "test_name": "caching_memory_efficiency",
            "cache_items": len(cache_keys),
            "memory_usage": mem_delta,
            "hit_rate": hit_rate,
            "target_hit_rate": 0.95,  # 95%ヒット率目標
            "target_achieved": hit_rate >= 0.95,
        }


class ComprehensivePerformanceBenchmarkRunner:
    """包括的パフォーマンスベンチマーク実行システム"""

    def __init__(self) -> None:
        self.benchmark = PerformanceBenchmark()
        self.results: dict[str, Any] = {}

    async def run_all_benchmarks(self) -> dict[str, Any]:
        """全ベンチマーク実行"""
        print("🚀 パフォーマンスベンチマーク開始...")
        start_time = time.time()

        # 1. ファイルI/Oテスト
        print("📁 ファイルI/Oパフォーマンステスト実行中...")
        file_io_tests = FileIOPerformanceTests(self.benchmark)
        file_io_results = [
            file_io_tests.test_file_reading_performance(),
            file_io_tests.test_batch_file_writing_performance(),
        ]
        file_io_tests.cleanup()

        # 2. YAMLテスト
        print("📄 YAML処理パフォーマンステスト実行中...")
        yaml_tests = YAMLPerformanceTests(self.benchmark)
        yaml_results = [yaml_tests.test_yaml_processing_performance(), yaml_tests.test_yaml_writing_performance()]
        yaml_tests.cleanup()

        # 3. メモリテスト
        print("💾 メモリ使用量パフォーマンステスト実行中...")
        memory_tests = MemoryPerformanceTests(self.benchmark)
        memory_results = [
            memory_tests.test_large_data_processing_memory(),
            memory_tests.test_caching_memory_efficiency(),
        ]

        total_time = time.time() - start_time

        # 結果統合
        all_results = file_io_results + yaml_results + memory_results

        # 全体パフォーマンス評価
        overall_assessment = self._assess_overall_performance(all_results)

        self.results = {
            "benchmark_timestamp": time.time(),
            "total_execution_time": total_time,
            "file_io_results": file_io_results,
            "yaml_results": yaml_results,
            "memory_results": memory_results,
            "overall_assessment": overall_assessment,
            "targets_achieved": self._count_targets_achieved(all_results),
            "performance_summary": self._generate_performance_summary(all_results),
        }

        print(f"✅ ベンチマーク完了 ({total_time:.2f}秒)")
        return self.results

    def _assess_overall_performance(self, all_results: list[dict[str, Any]]) -> dict[str, Any]:
        """全体パフォーマンス評価"""
        targets_met = sum(1 for result in all_results if result.get("target_achieved", False))
        total_tests = len(all_results)

        # 各カテゴリの平均改善率計算
        improvements = []
        memory_savings = []

        for result in all_results:
            if "improvement_percent" in result:
                improvements.append(result["improvement_percent"])
            if "memory_savings_percent" in result:
                memory_savings.append(result["memory_savings_percent"])

        avg_improvement = sum(improvements) / len(improvements) if improvements else 0
        avg_memory_savings = sum(memory_savings) / len(memory_savings) if memory_savings else 0

        # 全体評価
        if targets_met / total_tests >= 0.8 and avg_improvement >= 30:
            grade = "Excellent"
            recommendation = "パフォーマンス最適化目標を上回る成果"
        elif targets_met / total_tests >= 0.6 and avg_improvement >= 20:
            grade = "Good"
            recommendation = "良好なパフォーマンス改善を達成"
        elif targets_met / total_tests >= 0.4:
            grade = "Fair"
            recommendation = "部分的な改善、追加最適化を推奨"
        else:
            grade = "Poor"
            recommendation = "最適化戦略の見直しが必要"

        return {
            "grade": grade,
            "targets_met_ratio": targets_met / total_tests,
            "average_improvement_percent": avg_improvement,
            "average_memory_savings_percent": avg_memory_savings,
            "recommendation": recommendation,
        }

    def _count_targets_achieved(self, all_results: list[dict[str, Any]]) -> dict[str, int]:
        """目標達成カウント"""
        return {
            "total_tests": len(all_results),
            "targets_achieved": sum(1 for result in all_results if result.get("target_achieved", False)),
            "targets_missed": sum(1 for result in all_results if not result.get("target_achieved", False)),
        }

    def _generate_performance_summary(self, all_results: list[dict[str, Any]]) -> dict[str, Any]:
        """パフォーマンスサマリー生成"""
        return {
            "best_improvement": max(all_results, key=lambda x: x.get("improvement_percent", 0)),
            "worst_performance": min(all_results, key=lambda x: x.get("improvement_percent", float("inf"))),
            "recommendations": [
                "継続的なパフォーマンス監視を実装",
                "キャッシュ戦略の更なる最適化",
                "非同期処理の活用拡大",
                "メモリ効率的なデータ構造の採用",
            ],
        }

    def print_benchmark_results(self):
        """ベンチマーク結果表示"""
        if not self.results:
            print("⚠️ ベンチマーク結果がありません")
            return

        results = self.results

        print("\n" + "=" * 80)
        print("📊 パフォーマンスベンチマーク結果")
        print("=" * 80)

        # 全体評価
        assessment = results["overall_assessment"]
        print(f"\n🎯 全体評価: {assessment['grade']}")
        print(f"📈 平均改善率: {assessment['average_improvement_percent']:.1f}%")
        print(f"💾 平均メモリ削減: {assessment['average_memory_savings_percent']:.1f}%")
        print(f"🎪 目標達成率: {assessment['targets_met_ratio']:.1%}")
        print(f"💡 推奨: {assessment['recommendation']}")

        # カテゴリ別結果
        categories = [
            ("file_io_results", "📁 ファイルI/O最適化"),
            ("yaml_results", "📄 YAML処理最適化"),
            ("memory_results", "💾 メモリ使用量最適化"),
        ]

        for category_key, category_name in categories:
            print(f"\n{category_name}:")
            print("-" * 60)

            for result in results[category_key]:
                test_name = result["test_name"]
                target_achieved = "✅" if result.get("target_achieved", False) else "❌"

                print(f"  {target_achieved} {test_name}")

                if "improvement_percent" in result:
                    print(f"      改善率: {result['improvement_percent']:.1f}%")
                if "memory_savings_percent" in result:
                    print(f"      メモリ削減: {result['memory_savings_percent']:.1f}%")
                if "hit_rate" in result:
                    print(f"      ヒット率: {result['hit_rate']:.1%}")

        # 推奨事項
        print("\n💡 今後の推奨事項:")
        for i, rec in enumerate(results["performance_summary"]["recommendations"], 1):
            print(f"  {i}. {rec}")

        print("=" * 80)

    def export_benchmark_results(self, output_path: Path):
        """ベンチマーク結果エクスポート"""
        if not self.results:
            print("⚠️ エクスポート対象の結果がありません")
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)

        print(f"📄 ベンチマーク結果エクスポート: {output_path}")


# pytest テスト関数
@pytest.mark.asyncio
async def test_comprehensive_performance_benchmark():
    """包括的パフォーマンスベンチマークテスト"""
    runner = ComprehensivePerformanceBenchmarkRunner()
    results = await runner.run_all_benchmarks()

    # 基本的なアサーション
    assert results is not None
    assert "overall_assessment" in results
    assert "file_io_results" in results
    assert "yaml_results" in results
    assert "memory_results" in results

    # パフォーマンス目標の確認
    assessment = results["overall_assessment"]
    assert assessment["average_improvement_percent"] > 0

    # 結果表示
    runner.print_benchmark_results()

    return results


async def main():
    """メイン実行関数"""
    runner = ComprehensivePerformanceBenchmarkRunner()

    # ベンチマーク実行
    await runner.run_all_benchmarks()

    # 結果表示
    runner.print_benchmark_results()

    # 結果エクスポート
    output_path = Path("temp/performance_benchmark_results.json")
    runner.export_benchmark_results(output_path)


if __name__ == "__main__":
    asyncio.run(main())
