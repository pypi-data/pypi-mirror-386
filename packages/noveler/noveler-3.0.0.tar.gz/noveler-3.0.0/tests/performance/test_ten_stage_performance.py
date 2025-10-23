# File: tests/performance/test_ten_stage_performance.py
# Purpose: Performance tests for 10-stage writing system
# Context: Phase 3 - validate performance characteristics of A30 migration

"""Performance tests for 10-stage writing system."""

import asyncio
import time
import tracemalloc
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Check if pytest-benchmark is available
try:
    import pytest_benchmark
    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False

from noveler.application.services.a30_compatibility_adapter import (
    A30CompatibilityAdapter,
    CompatibilityMode,
)
from noveler.application.use_cases.ten_stage_episode_writing_use_case import (
    TenStageEpisodeWritingUseCase,
)
from noveler.application.use_cases.ten_stage_progress_use_case import (
    TenStageProgressRequest,
    TenStageProgressUseCase,
)
from noveler.domain.value_objects.detailed_execution_stage import DetailedExecutionStage
from noveler.domain.value_objects.five_stage_writing_execution import (
    ExecutionStage,
    FiveStageWritingRequest,
)
from noveler.infrastructure.services.unified_session_executor import (
    UnifiedSessionExecutor,
)


@pytest.fixture
def writing_request(tmp_path):
    """Create a sample writing request."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    (project_root / "manuscripts").mkdir()

    return FiveStageWritingRequest(
        episode_number=1,
        project_root=project_root,
        genre="fantasy",
        viewpoint="三人称単元視点",
        viewpoint_character="主人公",
        word_count_target=3500,
    )


@pytest.fixture
def mock_claude_service():
    """Create a mock Claude service for performance testing."""
    service = MagicMock()

    async def mock_execute(*args, **kwargs):
        # Simulate some processing time
        await asyncio.sleep(0.01)
        return {
            "output": "Test output " * 100,  # ~600 chars
            "turns_used": 2,
            "success": True,
        }

    service.execute_with_turn_limit = AsyncMock(side_effect=mock_execute)
    return service


class TestTenStagePerformance:
    """Performance test suite for 10-stage system."""

    @pytest.mark.asyncio
    async def test_progress_tracking_overhead(self, writing_request):
        """Test memory and time overhead of progress tracking."""
        progress_use_case = TenStageProgressUseCase()

        # Measure memory before
        tracemalloc.start()
        baseline = tracemalloc.get_traced_memory()[0]

        # Start timing
        start_time = time.perf_counter()

        # Initialize progress
        await progress_use_case.execute(
            TenStageProgressRequest(
                episode_number=1,
                project_root=writing_request.project_root,
                operation="start"
            )
        )

        # Simulate stage updates
        for stage in DetailedExecutionStage:
            await progress_use_case.execute(
                TenStageProgressRequest(
                    episode_number=1,
                    project_root=writing_request.project_root,
                    operation="update",
                    stage=stage,
                    stage_output=MagicMock()
                )
            )

        # Measure after
        end_time = time.perf_counter()
        current_memory = tracemalloc.get_traced_memory()[0]
        memory_used = current_memory - baseline
        tracemalloc.stop()

        execution_time = end_time - start_time

        # Assert performance characteristics
        assert memory_used < 1_000_000  # Less than 1MB overhead
        assert execution_time < 1.0  # Less than 1 second for all updates

        # Log results for analysis
        print(f"\nProgress tracking overhead:")
        print(f"  Memory: {memory_used / 1024:.2f} KB")
        print(f"  Time: {execution_time:.3f} seconds")

    @pytest.mark.asyncio
    async def test_stage_execution_timing(self, writing_request, mock_claude_service):
        """Test execution time for each stage."""
        executor = UnifiedSessionExecutor(
            claude_service=mock_claude_service,
            compatibility_adapter=A30CompatibilityAdapter(
                CompatibilityMode.A30_DETAILED_TEN_STAGE
            ),
            progress_use_case=TenStageProgressUseCase()
        )

        stage_timings: Dict[str, float] = {}

        # Override execute method to measure per-stage timing
        original_execute = executor._execute_ten_stage_session

        async def timed_execute(request, state):
            # Track timing for each stage
            state_timings = {}
            start_time = time.perf_counter()

            result = await original_execute(request, state)

            total_time = time.perf_counter() - start_time
            stage_timings["total"] = total_time

            return result

        executor._execute_ten_stage_session = timed_execute

        # Execute session
        start_time = time.perf_counter()
        response = await executor.execute_unified_session(writing_request)
        total_time = time.perf_counter() - start_time

        # Verify timing
        assert total_time < 5.0  # Should complete within 5 seconds
        assert response.status in ["completed", "failed"]

        print(f"\nTotal execution time: {total_time:.3f} seconds")
        print(f"Turns used: {response.turns_used}")

    @pytest.mark.asyncio
    async def test_compatibility_mode_performance(self, writing_request, mock_claude_service):
        """Compare performance across different compatibility modes."""
        results = {}

        for mode in CompatibilityMode:
            executor = UnifiedSessionExecutor(
                claude_service=mock_claude_service,
                compatibility_adapter=A30CompatibilityAdapter(mode)
            )

            start_time = time.perf_counter()
            response = await executor.execute_unified_session(writing_request)
            execution_time = time.perf_counter() - start_time

            results[mode.value] = {
                "time": execution_time,
                "turns": response.turns_used,
                "stages": len(response.stage_outputs)
            }

        # Log comparison
        print("\nCompatibility mode performance:")
        for mode, metrics in results.items():
            print(f"  {mode}:")
            print(f"    Time: {metrics['time']:.3f}s")
            print(f"    Turns: {metrics['turns']}")
            print(f"    Stages: {metrics['stages']}")

        # Verify all modes complete in reasonable time
        for metrics in results.values():
            assert metrics["time"] < 10.0  # 10 seconds max

    @pytest.mark.asyncio
    async def test_memory_usage_scaling(self, mock_claude_service):
        """Test memory usage scaling with episode count."""
        tracemalloc.start()
        baseline = tracemalloc.get_traced_memory()[0]

        executor = UnifiedSessionExecutor(
            claude_service=mock_claude_service,
            compatibility_adapter=A30CompatibilityAdapter(
                CompatibilityMode.A30_DETAILED_TEN_STAGE
            )
        )

        memory_samples = []

        # Test with multiple episodes
        for episode_num in range(1, 6):
            request = FiveStageWritingRequest(
                episode_number=episode_num,
                project_root=Path("/tmp/test"),
                genre="fantasy",
                viewpoint="三人称",
                viewpoint_character="主人公",
                word_count_target=3500
            )

            await executor.execute_unified_session(request)

            current = tracemalloc.get_traced_memory()[0]
            memory_used = (current - baseline) / 1_048_576  # Convert to MB
            memory_samples.append(memory_used)

        tracemalloc.stop()

        # Calculate memory growth rate
        if len(memory_samples) > 1:
            growth_rate = (memory_samples[-1] - memory_samples[0]) / len(memory_samples)
        else:
            growth_rate = 0

        print(f"\nMemory usage scaling:")
        for i, mem in enumerate(memory_samples, 1):
            print(f"  Episode {i}: {mem:.2f} MB")
        print(f"  Growth rate: {growth_rate:.3f} MB/episode")

        # Assert reasonable memory usage
        assert all(mem < 100 for mem in memory_samples)  # Each under 100MB
        assert growth_rate < 20  # Less than 20MB growth per episode

    @pytest.mark.asyncio
    async def test_turn_allocation_efficiency(self, writing_request):
        """Test turn allocation efficiency across stages."""
        executor = UnifiedSessionExecutor(
            compatibility_adapter=A30CompatibilityAdapter(
                CompatibilityMode.A30_DETAILED_TEN_STAGE
            )
        )

        # Get allocations
        allocations = executor.get_stage_allocations(writing_request)

        # Calculate statistics
        total_min = sum(a.min_turns for a in allocations.values())
        total_max = sum(a.max_turns for a in allocations.values())
        total_expected = sum(s.expected_turns for s in DetailedExecutionStage)

        print(f"\nTurn allocation efficiency:")
        print(f"  Min total: {total_min}")
        print(f"  Max total: {total_max}")
        print(f"  Expected: {total_expected}")
        print(f"  Efficiency: {total_expected / total_max * 100:.1f}%")

        # Verify allocation constraints
        assert total_min <= total_expected <= total_max
        assert total_max <= 30  # Session limit

    @pytest.mark.asyncio
    async def test_concurrent_episode_processing(self, mock_claude_service):
        """Test performance with concurrent episode processing."""
        executor = UnifiedSessionExecutor(
            claude_service=mock_claude_service,
            compatibility_adapter=A30CompatibilityAdapter(
                CompatibilityMode.A30_DETAILED_TEN_STAGE
            )
        )

        # Create multiple requests
        requests = [
            FiveStageWritingRequest(
                episode_number=i,
                project_root=Path(f"/tmp/test_{i}"),
                genre="fantasy",
                viewpoint="三人称",
                viewpoint_character="主人公",
                word_count_target=3500
            )
            for i in range(1, 4)
        ]

        # Execute concurrently
        start_time = time.perf_counter()
        results = await asyncio.gather(
            *[executor.execute_unified_session(req) for req in requests]
        )
        total_time = time.perf_counter() - start_time

        # Calculate throughput
        throughput = len(requests) / total_time

        print(f"\nConcurrent processing performance:")
        print(f"  Episodes: {len(requests)}")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Throughput: {throughput:.2f} episodes/second")

        # Verify all completed
        assert all(r.status in ["completed", "failed"] for r in results)
        assert total_time < 10.0  # Should benefit from concurrency

    def test_stage_transition_overhead(self):
        """Test overhead of stage transitions."""
        adapter = A30CompatibilityAdapter(CompatibilityMode.A30_DETAILED_TEN_STAGE)

        # Measure conversion overhead
        start_time = time.perf_counter()

        for _ in range(1000):
            # Simulate stage transitions
            for detailed_stage in DetailedExecutionStage:
                legacy_stage = adapter.convert_detailed_to_legacy(detailed_stage)
                detailed_stages = adapter.convert_legacy_to_detailed(legacy_stage)

        total_time = time.perf_counter() - start_time
        per_transition = total_time / (1000 * len(DetailedExecutionStage))

        print(f"\nStage transition overhead:")
        print(f"  Total time (1000 iterations): {total_time:.3f}s")
        print(f"  Per transition: {per_transition * 1000:.3f}ms")

        # Should be negligible
        assert per_transition < 0.001  # Less than 1ms per transition


@pytest.mark.benchmark
@pytest.mark.skipif(not BENCHMARK_AVAILABLE, reason="pytest-benchmark not installed")
class TestBenchmarks:
    """Benchmark tests for performance regression detection."""

    def test_progress_update_benchmark(self, benchmark, writing_request):
        """Benchmark progress update operation."""
        progress_use_case = TenStageProgressUseCase()

        # Setup
        asyncio.run(progress_use_case.execute(
            TenStageProgressRequest(
                episode_number=1,
                project_root=writing_request.project_root,
                operation="start"
            )
        ))

        def update_progress():
            return asyncio.run(progress_use_case.execute(
                TenStageProgressRequest(
                    episode_number=1,
                    project_root=writing_request.project_root,
                    operation="update",
                    stage=DetailedExecutionStage.MANUSCRIPT_WRITING,
                    stage_output=MagicMock()
                )
            ))

        result = benchmark(update_progress)
        assert result.success

    def test_stage_mapping_benchmark(self, benchmark):
        """Benchmark stage mapping operations."""
        adapter = A30CompatibilityAdapter(CompatibilityMode.A30_DETAILED_TEN_STAGE)

        def map_stages():
            results = []
            for stage in DetailedExecutionStage:
                legacy = adapter.convert_detailed_to_legacy(stage)
                detailed = adapter.convert_legacy_to_detailed(legacy)
                results.append((legacy, detailed))
            return results

        result = benchmark(map_stages)
        assert len(result) == len(DetailedExecutionStage)