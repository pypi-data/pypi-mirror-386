# File: tests/integration/test_log_aggregation_integration.py
# Purpose: Integration tests for Phase 3 log aggregation and analysis
# Context: Verify log aggregation, analysis, and distributed tracing functionality

"""
Log aggregation and analysis integration tests

Tests the integration between:
- LogAggregatorService (log_aggregator_service.py)
- LogAnalyzer (log_analyzer.py)
- DistributedTracer (distributed_tracing.py)
"""

import asyncio
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from noveler.infrastructure.logging.distributed_tracing import (
    DistributedTracer,
    global_tracer,
    traced,
)
from noveler.infrastructure.logging.log_aggregator_service import (
    AggregatedMetrics,
    LogAggregatorService,
    LogEntry,
)
from noveler.infrastructure.logging.log_analyzer import (
    LogAnalyzer,
    PerformanceBottleneck,
)


@pytest.mark.integration
class TestLogAggregationIntegration:
    """Log aggregation integration tests"""

    @pytest.fixture
    def aggregator(self, tmp_path):
        """Create log aggregator with temp database"""
        db_path = tmp_path / "test_logs.db"
        return LogAggregatorService(db_path)

    @pytest.fixture
    def analyzer(self):
        """Create log analyzer instance"""
        return LogAnalyzer()

    @pytest.fixture
    def sample_logs(self):
        """Generate sample log entries"""
        base_time = time.time()
        logs = []

        # Success logs
        for i in range(10):
            logs.append(LogEntry(
                timestamp=base_time + i,
                level="INFO",
                message=f"Operation {i} completed",
                logger_name="test_logger",
                operation=f"operation_{i % 3}",
                execution_time_ms=100 + (i * 10),
                request_id=f"req-{i}",
                session_id=f"session-{i % 2}"
            ))

        # Error logs
        for i in range(3):
            logs.append(LogEntry(
                timestamp=base_time + 20 + i,
                level="ERROR",
                message=f"Error in operation",
                logger_name="test_logger",
                operation="failing_operation",
                execution_time_ms=50.0,  # エラーでも実行時間を設定
                error_type="ValueError",
                request_id=f"req-err-{i}",
                session_id="session-error"
            ))

        return logs

    def test_log_aggregation_and_storage(self, aggregator, sample_logs):
        """Test log aggregation and persistent storage"""
        # Add logs to aggregator
        aggregator.bulk_add_log_entries(sample_logs)

        # Query logs
        retrieved_logs = aggregator.query_logs(limit=100)
        assert len(retrieved_logs) == len(sample_logs)

        # Verify log content
        first_log = retrieved_logs[-1]  # Oldest log (reversed order)
        assert first_log.message == "Operation 0 completed"
        assert first_log.operation == "operation_0"

    def test_metrics_calculation(self, aggregator, sample_logs):
        """Test metrics calculation from aggregated logs"""
        aggregator.bulk_add_log_entries(sample_logs)

        # Calculate metrics
        start_time = min(log.timestamp for log in sample_logs)
        end_time = max(log.timestamp for log in sample_logs) + 1

        metrics = aggregator.calculate_metrics(start_time, end_time)

        assert metrics.total_requests > 0
        assert metrics.failed_requests == 3
        assert metrics.error_rate > 0
        assert "operation_0" in metrics.operations
        assert "ValueError" in metrics.errors_by_type

    def test_performance_bottleneck_detection(self, analyzer, sample_logs):
        """Test performance bottleneck analysis"""
        # Add some slow operations
        slow_logs = sample_logs.copy()
        base_time = time.time()

        for i in range(20):
            slow_logs.append(LogEntry(
                timestamp=base_time + i,
                level="INFO",
                message="Slow operation",
                logger_name="test_logger",
                operation="slow_operation",
                execution_time_ms=2000 + (i * 100)  # Very slow
            ))

        bottlenecks = analyzer.analyze_performance_bottlenecks(slow_logs)

        # Should detect slow_operation as bottleneck
        assert len(bottlenecks) > 0
        slow_bottleneck = next(
            (b for b in bottlenecks if b.operation == "slow_operation"),
            None
        )
        assert slow_bottleneck is not None
        assert slow_bottleneck.avg_time_ms > 2000
        assert len(slow_bottleneck.recommendations) > 0

    def test_error_pattern_analysis(self, analyzer, sample_logs):
        """Test error pattern detection"""
        # Add more error patterns
        error_logs = sample_logs.copy()
        base_time = time.time()

        # Add increasing error pattern
        for i in range(10):
            error_logs.append(LogEntry(
                timestamp=base_time + (i * 10),
                level="ERROR",
                message=f"Database connection error {i}",
                logger_name="test_logger",
                operation="database_query",
                error_type="ConnectionError"
            ))

        patterns = analyzer.analyze_error_patterns(error_logs)

        # Should detect error patterns
        assert len(patterns) > 0
        connection_pattern = next(
            (p for p in patterns if p.error_type == "ConnectionError"),
            None
        )
        assert connection_pattern is not None
        assert connection_pattern.frequency == 10

    def test_report_generation(self, aggregator, analyzer, sample_logs):
        """Test report generation"""
        aggregator.bulk_add_log_entries(sample_logs)

        start_time = min(log.timestamp for log in sample_logs)
        end_time = max(log.timestamp for log in sample_logs) + 1

        # Generate aggregator report
        markdown_report = aggregator.generate_report(start_time, end_time, "markdown")
        assert "ログ分析レポート" in markdown_report
        assert "サマリー" in markdown_report

        json_report = aggregator.generate_report(start_time, end_time, "json")
        report_data = json.loads(json_report)
        assert "metrics" in report_data
        assert "period" in report_data

        # Generate analyzer optimization report
        optimization_report = analyzer.generate_optimization_report(sample_logs)
        assert "最適化レポート" in optimization_report
        assert "パフォーマンスボトルネック" in optimization_report

    def test_anomaly_detection(self, aggregator, sample_logs):
        """Test anomaly detection"""
        current_time = time.time()

        # Add historical logs with some errors (7分前〜6分前の同時間帯)
        historical_logs = []
        window_seconds = 1 * 60  # 1分
        historical_base = current_time - (window_seconds * 6.5)  # 6.5分前

        # 正常ログ（9件）
        for i in range(9):
            historical_logs.append(LogEntry(
                timestamp=historical_base + i,
                level="INFO",
                message=f"Historical operation {i}",
                logger_name="test_logger",
                operation=f"operation_{i}",
                execution_time_ms=100.0,
                request_id=f"hist-{i}"
            ))

        # 履歴エラーログ（1件）
        historical_logs.append(LogEntry(
            timestamp=historical_base + 9,
            level="ERROR",
            message="Historical error",
            logger_name="test_logger",
            operation="historical_error_op",
            execution_time_ms=120.0,
            error_type="HistoricalError",
            request_id="hist-error-1"
        ))
        aggregator.bulk_add_log_entries(historical_logs)

        # Add current anomalous logs (直近1分間に大量のエラー)
        anomaly_logs = []
        recent_base = current_time - 30  # 30秒前から
        for i in range(20):  # 大量のエラーログ
            anomaly_logs.append(LogEntry(
                timestamp=recent_base + i,
                level="ERROR",
                message="Anomaly error",
                logger_name="test_logger",
                operation="anomaly_operation",
                execution_time_ms=75.0,
                error_type="AnomalyError",
                request_id=f"anomaly-{i}"
            ))

        aggregator.bulk_add_log_entries(anomaly_logs)

        # Detect anomalies
        anomalies = aggregator.detect_anomalies(window_minutes=1)

        # Should detect traffic or error anomalies
        assert len(anomalies) > 0, f"異常が検出されませんでした。anomalies: {anomalies}"
        assert any(anomaly["type"] == "high_error_rate" for anomaly in anomalies), "エラー率異常が検出されていません"

    def test_log_cleanup(self, aggregator, sample_logs):
        """Test old log cleanup"""
        # Add old logs
        old_logs = []
        old_time = time.time() - (40 * 24 * 3600)  # 40 days ago

        for i in range(5):
            old_logs.append(LogEntry(
                timestamp=old_time + i,
                level="INFO",
                message=f"Old log {i}",
                logger_name="test_logger"
            ))

        aggregator.bulk_add_log_entries(old_logs)
        aggregator.bulk_add_log_entries(sample_logs)

        # Clean up old logs
        deleted_count = aggregator.cleanup_old_logs(retention_days=30)
        assert deleted_count == 5

        # Verify old logs are deleted
        all_logs = aggregator.query_logs(limit=100)
        assert len(all_logs) == len(sample_logs)


@pytest.mark.integration
class TestDistributedTracingIntegration:
    """Distributed tracing integration tests"""

    @pytest.fixture
    def tracer(self):
        """Create distributed tracer instance"""
        return DistributedTracer(service_name="test_service")

    def test_basic_tracing(self, tracer):
        """Test basic trace and span creation"""
        # Start trace
        context = tracer.start_trace("test_operation", tags={"user_id": "123"})
        assert context.trace_id is not None

        # Create child span
        span = tracer.start_span("child_operation", component="test")
        assert span.parent_id is not None
        assert span.trace_id == context.trace_id

        # Finish span
        tracer.finish_span(span, status="success")
        assert span.duration_ms is not None
        assert span.status == "success"

    def test_traced_decorator(self):
        """Test @traced decorator"""
        call_count = 0

        @traced(operation="test_function", component="test")
        def test_function(value):
            nonlocal call_count
            call_count += 1
            return value * 2

        result = test_function(5)
        assert result == 10
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_traced_decorator(self):
        """Test @traced decorator with async functions"""
        call_count = 0

        @traced(operation="async_test_function")
        async def async_test_function(value):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return value * 2

        result = await async_test_function(5)
        assert result == 10
        assert call_count == 1

    def test_trace_context_propagation(self, tracer):
        """Test trace context propagation through headers"""
        # Start trace
        context = tracer.start_trace("api_request")

        # Inject context into headers
        headers = {}
        headers = tracer.inject_context(headers)
        assert "X-Trace-Id" in headers
        assert headers["X-Trace-Id"] == context.trace_id

        # Extract context from headers
        new_tracer = DistributedTracer(service_name="downstream_service")
        extracted_context = new_tracer.extract_context(headers)
        assert extracted_context is not None
        assert extracted_context.trace_id == context.trace_id

    def test_trace_summary_generation(self, tracer):
        """Test trace summary generation"""
        # Create complex trace
        context = tracer.start_trace("main_operation")
        trace_id = context.trace_id

        # Create multiple spans
        span1 = tracer.start_span("database_query")
        time.sleep(0.01)
        tracer.finish_span(span1)

        span2 = tracer.start_span("api_call")
        time.sleep(0.02)
        tracer.finish_span(span2)

        span3 = tracer.start_span("cache_lookup")
        tracer.finish_span(span3, status="error", error=ValueError("Cache miss"))

        # Generate summary
        summary = tracer.create_trace_summary(trace_id)

        assert summary["trace_id"] == trace_id
        assert summary["span_count"] >= 4  # main + 3 children
        assert summary["error_count"] == 1
        assert "span_tree" in summary
        assert "critical_path" in summary

    def test_span_tagging_and_logging(self, tracer):
        """Test span tagging and log entry"""
        context = tracer.start_trace("test_operation")
        span = tracer.start_span("test_span")

        # Add tags
        span.add_tag("user_id", "123")
        span.add_tag("request_type", "GET")
        assert span.tags["user_id"] == "123"

        # Add logs
        span.add_log("Processing started", item_count=10)
        span.add_log("Processing completed", success=True)
        assert len(span.logs) == 2

        tracer.finish_span(span)

    def test_error_handling_in_traced_function(self):
        """Test error handling with @traced decorator"""

        @traced(operation="failing_function")
        def failing_function():
            raise RuntimeError("Intentional error")

        with pytest.raises(RuntimeError):
            failing_function()

        # Check that span was marked as error (would need access to tracer internals)

    def test_baggage_propagation(self, tracer):
        """Test baggage data propagation"""
        context = tracer.start_trace("test_operation")
        context.baggage["tenant_id"] = "tenant-123"
        context.baggage["feature_flag"] = "enabled"

        # Inject and extract context
        headers = tracer.inject_context({})
        new_tracer = DistributedTracer()
        extracted_context = new_tracer.extract_context(headers)

        assert extracted_context.baggage["tenant_id"] == "tenant-123"
        assert extracted_context.baggage["feature_flag"] == "enabled"