#!/usr/bin/env python3
# File: scripts/benchmarks/messagebus_benchmark.py
# Purpose: MessageBus performance benchmark script for SPEC-901 validation
# Context: Measures processing time, throughput, and validates <1ms requirement

"""MessageBus performance benchmark script."""

import asyncio
import statistics
import time
from datetime import datetime
from pathlib import Path
import sys
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from noveler.application.simple_message_bus import MessageBus, BusConfig
from noveler.application.uow import InMemoryUnitOfWork
from noveler.application.idempotency import InMemoryIdempotencyStore
from noveler.infrastructure.adapters.file_outbox_repository import FileOutboxRepository


class BenchmarkResults:
    """Benchmark results container."""

    def __init__(self):
        self.command_times: List[float] = []
        self.event_times: List[float] = []
        self.total_commands = 0
        self.total_events = 0
        self.failed_commands = 0
        self.failed_events = 0

    def add_command_time(self, duration: float, success: bool = True):
        """Add command execution time."""
        self.command_times.append(duration)
        self.total_commands += 1
        if not success:
            self.failed_commands += 1

    def add_event_time(self, duration: float, success: bool = True):
        """Add event execution time."""
        self.event_times.append(duration)
        self.total_events += 1
        if not success:
            self.failed_events += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get benchmark statistics."""
        cmd_stats = self._calculate_stats(self.command_times, "commands")
        event_stats = self._calculate_stats(self.event_times, "events")

        return {
            "commands": cmd_stats,
            "events": event_stats,
            "summary": {
                "total_operations": self.total_commands + self.total_events,
                "total_time": sum(self.command_times) + sum(self.event_times),
                "overall_success_rate": (
                    (self.total_commands + self.total_events - self.failed_commands - self.failed_events) /
                    max(1, self.total_commands + self.total_events)
                )
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


async def setup_test_bus() -> MessageBus:
    """Set up a test MessageBus with minimal configuration."""
    config = BusConfig(
        max_retries=1,  # Minimal retries for benchmark
        backoff_base_sec=0.001,
        backoff_max_sec=0.01,
        jitter_sec=0.001
    )

    # Use in-memory components for speed
    # Provide dummy repo for InMemoryUnitOfWork
    dummy_repo = None  # ベンチマーク用ダミー
    uow_factory = lambda: InMemoryUnitOfWork(episode_repo=dummy_repo)
    idempotency_store = InMemoryIdempotencyStore()

    # Disable outbox for pure performance testing
    bus = MessageBus(
        config=config,
        uow_factory=uow_factory,
        idempotency_store=idempotency_store,
        dispatch_inline=False  # Skip outbox for benchmark
    )

    # Register minimal handlers
    async def empty_command_handler(data: Dict[str, Any]) -> Dict[str, Any]:
        """Minimal command handler for benchmark."""
        return {"success": True, "result": "ok"}

    async def empty_event_handler(event) -> None:
        """Minimal event handler for benchmark."""
        pass

    bus.command_handlers["benchmark_command"] = empty_command_handler
    bus.event_handlers["benchmark_event"] = [empty_event_handler]

    return bus


async def benchmark_commands(bus: MessageBus, num_operations: int = 1000) -> List[float]:
    """Benchmark command processing."""
    print(f"Benchmarking {num_operations} commands...")

    times = []
    for i in range(num_operations):
        start_time = time.perf_counter()

        result = await bus.handle_command("benchmark_command", {"test_data": f"command_{i}"})

        end_time = time.perf_counter()
        duration = end_time - start_time
        times.append(duration)

        if i % 100 == 0:
            print(f"  Processed {i}/{num_operations} commands...")

    return times


async def benchmark_events(bus: MessageBus, num_operations: int = 1000) -> List[float]:
    """Benchmark event processing."""
    print(f"Benchmarking {num_operations} events...")

    times = []
    for i in range(num_operations):
        start_time = time.perf_counter()

        await bus.emit("benchmark_event", {"test_data": f"event_{i}"})

        end_time = time.perf_counter()
        duration = end_time - start_time
        times.append(duration)

        if i % 100 == 0:
            print(f"  Processed {i}/{num_operations} events...")

    return times


async def benchmark_mixed_load(bus: MessageBus, num_operations: int = 1000) -> BenchmarkResults:
    """Benchmark mixed command and event load."""
    print(f"Benchmarking mixed load with {num_operations} operations...")

    results = BenchmarkResults()

    for i in range(num_operations):
        if i % 2 == 0:
            # Process command
            start_time = time.perf_counter()
            try:
                result = await bus.handle_command("benchmark_command", {"test_data": f"mixed_cmd_{i}"})
                success = result.get("success", False)
                end_time = time.perf_counter()
                results.add_command_time(end_time - start_time, success)
            except Exception:
                end_time = time.perf_counter()
                results.add_command_time(end_time - start_time, False)
        else:
            # Process event
            start_time = time.perf_counter()
            try:
                await bus.emit("benchmark_event", {"test_data": f"mixed_event_{i}"})
                end_time = time.perf_counter()
                results.add_event_time(end_time - start_time, True)
            except Exception:
                end_time = time.perf_counter()
                results.add_event_time(end_time - start_time, False)

        if i % 100 == 0:
            print(f"  Processed {i}/{num_operations} mixed operations...")

    return results


def print_results(results: Dict[str, Any], target_ms: float = 1.0):
    """Print benchmark results."""
    print("\n" + "="*60)
    print("MessageBus Benchmark Results")
    print("="*60)

    # Commands
    cmd_stats = results["commands"]
    print(f"\nCOMMANDS ({cmd_stats['count']} operations):")
    print(f"  Average: {cmd_stats['avg_ms']:.3f}ms")
    print(f"  P50:     {cmd_stats['p50_ms']:.3f}ms")
    print(f"  P95:     {cmd_stats['p95_ms']:.3f}ms")
    print(f"  P99:     {cmd_stats['p99_ms']:.3f}ms")
    print(f"  Min:     {cmd_stats['min_ms']:.3f}ms")
    print(f"  Max:     {cmd_stats['max_ms']:.3f}ms")
    print(f"  Throughput: {cmd_stats['throughput_ops_sec']:.0f} ops/sec")

    # Events
    event_stats = results["events"]
    print(f"\nEVENTS ({event_stats['count']} operations):")
    print(f"  Average: {event_stats['avg_ms']:.3f}ms")
    print(f"  P50:     {event_stats['p50_ms']:.3f}ms")
    print(f"  P95:     {event_stats['p95_ms']:.3f}ms")
    print(f"  P99:     {event_stats['p99_ms']:.3f}ms")
    print(f"  Min:     {event_stats['min_ms']:.3f}ms")
    print(f"  Max:     {event_stats['max_ms']:.3f}ms")
    print(f"  Throughput: {event_stats['throughput_ops_sec']:.0f} ops/sec")

    # Summary
    summary = results["summary"]
    print(f"\nSUMMARY:")
    print(f"  Total operations: {summary['total_operations']}")
    print(f"  Total time: {summary['total_time']:.3f}s")
    print(f"  Success rate: {summary['overall_success_rate']:.1%}")

    # Validation against SPEC-901 requirements
    print(f"\nSPEC-901 VALIDATION:")
    cmd_target_met = cmd_stats['p95_ms'] < target_ms
    event_target_met = event_stats['p95_ms'] < target_ms

    print(f"  Command P95 < {target_ms}ms: {'✅ PASS' if cmd_target_met else '❌ FAIL'} ({cmd_stats['p95_ms']:.3f}ms)")
    print(f"  Event P95 < {target_ms}ms: {'✅ PASS' if event_target_met else '❌ FAIL'} ({event_stats['p95_ms']:.3f}ms)")

    overall_pass = cmd_target_met and event_target_met
    print(f"  Overall: {'✅ SPEC-901 REQUIREMENTS MET' if overall_pass else '❌ SPEC-901 REQUIREMENTS NOT MET'}")


async def main():
    """Main benchmark execution."""
    print("MessageBus Performance Benchmark")
    print("Target: <1ms P95 latency (SPEC-901 requirement)")
    print("-" * 50)

    # Setup
    bus = await setup_test_bus()

    # Run benchmarks
    results = BenchmarkResults()

    # Command benchmark
    cmd_times = await benchmark_commands(bus, 1000)
    for t in cmd_times:
        results.add_command_time(t)

    # Event benchmark
    event_times = await benchmark_events(bus, 1000)
    for t in event_times:
        results.add_event_time(t)

    # Mixed load benchmark
    mixed_results = await benchmark_mixed_load(bus, 500)
    results.command_times.extend(mixed_results.command_times)
    results.event_times.extend(mixed_results.event_times)
    results.total_commands += mixed_results.total_commands
    results.total_events += mixed_results.total_events

    # Print results
    stats = results.get_stats()
    print_results(stats)

    # Cleanup
    print(f"\nBenchmark completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
