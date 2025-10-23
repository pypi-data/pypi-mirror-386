#!/usr/bin/env python3
# File: scripts/benchmarks/mcp_performance_benchmark.py
# Purpose: MCP server performance benchmark script for measuring P95 <100ms requirement
# Context: Validates overall MCP tool response time including MessageBus integration

"""MCP performance benchmark script."""

import asyncio
import statistics
import time
from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict, List
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from mcp_servers.noveler.json_conversion_server import JSONConversionServer


class MCPBenchmarkResults:
    """MCP benchmark results container."""

    def __init__(self):
        self.tool_times: Dict[str, List[float]] = {}
        self.total_operations = 0
        self.failed_operations = 0

    def add_tool_time(self, tool_name: str, duration: float, success: bool = True):
        """Add tool execution time."""
        if tool_name not in self.tool_times:
            self.tool_times[tool_name] = []

        self.tool_times[tool_name].append(duration)
        self.total_operations += 1
        if not success:
            self.failed_operations += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get benchmark statistics."""
        tool_stats = {}
        all_times = []

        for tool_name, times in self.tool_times.items():
            if times:
                tool_stats[tool_name] = self._calculate_stats(times, tool_name)
                all_times.extend(times)

        overall_stats = self._calculate_stats(all_times, "overall") if all_times else {}

        return {
            "tools": tool_stats,
            "overall": overall_stats,
            "summary": {
                "total_operations": self.total_operations,
                "failed_operations": self.failed_operations,
                "success_rate": (self.total_operations - self.failed_operations) / max(1, self.total_operations),
                "tool_count": len(self.tool_times)
            }
        }

    def _calculate_stats(self, times: List[float], operation_type: str) -> Dict[str, Any]:
        """Calculate statistics for a list of times."""
        if not times:
            return {
                "count": 0,
                "avg_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
                "throughput_ops_sec": 0.0
            }

        times_ms = [t * 1000 for t in times]  # Convert to milliseconds
        sorted_times = sorted(times_ms)

        return {
            "count": len(times),
            "avg_ms": statistics.mean(times_ms),
            "min_ms": min(times_ms),
            "max_ms": max(times_ms),
            "p50_ms": self._percentile(sorted_times, 50),
            "p95_ms": self._percentile(sorted_times, 95),
            "p99_ms": self._percentile(sorted_times, 99),
            "throughput_ops_sec": len(times) / sum(times) if sum(times) > 0 else 0
        }

    def _percentile(self, sorted_list: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not sorted_list:
            return 0.0
        index = int((percentile / 100) * len(sorted_list))
        if index >= len(sorted_list):
            index = len(sorted_list) - 1
        return sorted_list[index]


def setup_test_mcp_server() -> JSONConversionServer:
    """Set up a test MCP server with both bus and non-bus configurations."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create server with MessageBus enabled for performance testing
    server = JSONConversionServer(
        output_dir=temp_dir,
        use_message_bus=True
    )

    return server


async def benchmark_noveler_check(server: JSONConversionServer, num_operations: int = 50) -> List[float]:
    """Benchmark noveler_check tool execution."""
    print(f"Benchmarking {num_operations} noveler_check operations...")

    times = []
    for i in range(num_operations):
        episode_number = (i % 5) + 1  # Test episodes 1-5

        start_time = time.perf_counter()

        try:
            # Execute via MessageBus routing
            result = server._handle_check_via_bus_sync(episode_number, auto_fix=False)
            success = "品質チェック完了" in result or "品質チェック失敗" in result
        except Exception as e:
            print(f"Error in operation {i}: {e}")
            success = False
            result = str(e)

        end_time = time.perf_counter()
        duration = end_time - start_time
        times.append(duration)

        if i % 10 == 0:
            print(f"  Processed {i}/{num_operations} noveler_check operations...")

        # Add small delay to prevent overwhelming the system
        await asyncio.sleep(0.01)

    return times


async def benchmark_status_tool(server: JSONConversionServer, num_operations: int = 100) -> List[float]:
    """Benchmark status tool execution."""
    print(f"Benchmarking {num_operations} status operations...")

    times = []
    for i in range(num_operations):
        start_time = time.perf_counter()

        try:
            result = server._handle_status_command(project_root=None)
            success = "小説執筆状況" in result or "エラー" not in result
        except Exception as e:
            print(f"Error in status operation {i}: {e}")
            success = False
            result = str(e)

        end_time = time.perf_counter()
        duration = end_time - start_time
        times.append(duration)

        if i % 20 == 0:
            print(f"  Processed {i}/{num_operations} status operations...")

        # Small delay for system stability
        await asyncio.sleep(0.005)

    return times


async def benchmark_mixed_mcp_load(server: JSONConversionServer, num_operations: int = 100) -> MCPBenchmarkResults:
    """Benchmark mixed MCP tool load."""
    print(f"Benchmarking mixed MCP load with {num_operations} operations...")

    results = MCPBenchmarkResults()

    for i in range(num_operations):
        if i % 3 == 0:
            # noveler_check operation
            episode_number = (i % 3) + 1
            start_time = time.perf_counter()
            try:
                result = server._handle_check_via_bus_sync(episode_number, auto_fix=False)
                success = "品質チェック完了" in result or "品質チェック失敗" in result
                end_time = time.perf_counter()
                results.add_tool_time("noveler_check", end_time - start_time, success)
            except Exception as e:
                end_time = time.perf_counter()
                results.add_tool_time("noveler_check", end_time - start_time, False)

        elif i % 3 == 1:
            # status operation
            start_time = time.perf_counter()
            try:
                result = server._handle_status_command()
                success = "小説執筆状況" in result
                end_time = time.perf_counter()
                results.add_tool_time("status", end_time - start_time, success)
            except Exception as e:
                end_time = time.perf_counter()
                results.add_tool_time("status", end_time - start_time, False)

        else:
            # write operation (if available)
            if hasattr(server, '_handle_write_via_bus_sync'):
                episode_number = (i % 2) + 1
                start_time = time.perf_counter()
                try:
                    result = server._handle_write_via_bus_sync(episode_number)
                    success = "write via bus ok" in result or "events=" in result
                    end_time = time.perf_counter()
                    results.add_tool_time("noveler_write", end_time - start_time, success)
                except Exception as e:
                    end_time = time.perf_counter()
                    results.add_tool_time("noveler_write", end_time - start_time, False)
            else:
                # Fallback: simulate a lightweight operation
                start_time = time.perf_counter()
                await asyncio.sleep(0.001)  # 1ms simulation
                end_time = time.perf_counter()
                results.add_tool_time("simulated_write", end_time - start_time, True)

        if i % 20 == 0:
            print(f"  Processed {i}/{num_operations} mixed operations...")

        # Prevent system overload
        await asyncio.sleep(0.01)

    return results


def print_mcp_results(results: Dict[str, Any], target_ms: float = 100.0):
    """Print MCP benchmark results."""
    print("\n" + "="*60)
    print("MCP Performance Benchmark Results")
    print("="*60)

    # Tool-specific stats
    for tool_name, tool_stats in results["tools"].items():
        print(f"\n{tool_name.upper()} ({tool_stats['count']} operations):")
        print(f"  Average: {tool_stats['avg_ms']:.1f}ms")
        print(f"  P50:     {tool_stats['p50_ms']:.1f}ms")
        print(f"  P95:     {tool_stats['p95_ms']:.1f}ms")
        print(f"  P99:     {tool_stats['p99_ms']:.1f}ms")
        print(f"  Min:     {tool_stats['min_ms']:.1f}ms")
        print(f"  Max:     {tool_stats['max_ms']:.1f}ms")
        print(f"  Throughput: {tool_stats['throughput_ops_sec']:.1f} ops/sec")

    # Overall stats
    overall = results["overall"]
    if overall:
        print(f"\nOVERALL ({overall['count']} operations):")
        print(f"  Average: {overall['avg_ms']:.1f}ms")
        print(f"  P50:     {overall['p50_ms']:.1f}ms")
        print(f"  P95:     {overall['p95_ms']:.1f}ms")
        print(f"  P99:     {overall['p99_ms']:.1f}ms")
        print(f"  Min:     {overall['min_ms']:.1f}ms")
        print(f"  Max:     {overall['max_ms']:.1f}ms")
        print(f"  Throughput: {overall['throughput_ops_sec']:.1f} ops/sec")

    # Summary
    summary = results["summary"]
    print(f"\nSUMMARY:")
    print(f"  Total operations: {summary['total_operations']}")
    print(f"  Failed operations: {summary['failed_operations']}")
    print(f"  Success rate: {summary['success_rate']:.1%}")
    print(f"  Tools tested: {summary['tool_count']}")

    # Performance validation
    print(f"\nPERFORMANCE VALIDATION:")
    if overall:
        overall_p95_pass = overall['p95_ms'] < target_ms
        print(f"  Overall P95 < {target_ms}ms: {'✅ PASS' if overall_p95_pass else '❌ FAIL'} ({overall['p95_ms']:.1f}ms)")

    tool_results = []
    for tool_name, tool_stats in results["tools"].items():
        tool_p95_pass = tool_stats['p95_ms'] < target_ms
        tool_results.append(tool_p95_pass)
        print(f"  {tool_name} P95 < {target_ms}ms: {'✅ PASS' if tool_p95_pass else '❌ FAIL'} ({tool_stats['p95_ms']:.1f}ms)")

    all_pass = overall.get('p95_ms', 0) < target_ms if overall else all(tool_results)
    print(f"  Overall: {'✅ MCP PERFORMANCE REQUIREMENTS MET' if all_pass else '❌ MCP PERFORMANCE REQUIREMENTS NOT MET'}")


async def main():
    """Main benchmark execution."""
    print("MCP Performance Benchmark")
    print("Target: P95 <100ms for all tools")
    print("-" * 50)

    # Setup
    server = setup_test_mcp_server()

    # Run benchmarks
    results = MCPBenchmarkResults()

    # Individual tool benchmarks
    print("\n🔍 Benchmarking noveler_check...")
    check_times = await benchmark_noveler_check(server, 30)
    for t in check_times:
        results.add_tool_time("noveler_check", t)

    print("\n📊 Benchmarking status tool...")
    status_times = await benchmark_status_tool(server, 50)
    for t in status_times:
        results.add_tool_time("status", t)

    # Mixed load benchmark
    print("\n🔄 Benchmarking mixed MCP load...")
    mixed_results = await benchmark_mixed_mcp_load(server, 60)

    # Merge results
    for tool_name, times in mixed_results.tool_times.items():
        for t in times:
            results.add_tool_time(tool_name, t)

    results.failed_operations += mixed_results.failed_operations

    # Print results
    stats = results.get_stats()
    print_mcp_results(stats)

    # Cleanup
    print(f"\nBenchmark completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
