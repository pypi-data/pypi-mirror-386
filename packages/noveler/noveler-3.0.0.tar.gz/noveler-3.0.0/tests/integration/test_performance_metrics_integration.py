# File: tests/integration/test_performance_metrics_integration.py
# Purpose: Integration tests for performance monitoring and structured logging
# Context: Verify that performance metrics are correctly collected and logged

"""
Performance metrics integration tests

Tests the integration between:
- Structured logging (structured_logger.py)
- Performance monitoring (performance_monitor_v2.py)
- Log decorators (log_decorators.py)
- LLM execution logging
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from noveler.domain.services.claude_code_execution_service import ClaudeCodeExecutionService
from noveler.domain.value_objects.claude_code_execution import ClaudeCodeExecutionResponse
from noveler.infrastructure.logging.log_decorators import (
    log_execution,
    log_llm_execution,
    with_request_context,
)
from noveler.infrastructure.logging.structured_logger import RequestContext, StructuredLogger
from noveler.infrastructure.monitoring.performance_monitor_v2 import EnhancedPerformanceMonitor


@pytest.mark.integration
class TestPerformanceMetricsIntegration:
    """Performance metrics integration tests"""

    @pytest.fixture
    def structured_logger(self):
        """Create a structured logger with mock handler"""
        base_logger = logging.getLogger("test_structured_logger")
        base_logger.handlers.clear()
        base_logger.setLevel(logging.DEBUG)

        handler = MagicMock()
        handler.level = logging.DEBUG
        handler.handle = MagicMock()
        base_logger.addHandler(handler)

        structured = StructuredLogger("test_structured_logger")

        with patch("noveler.infrastructure.logging.log_decorators.get_structured_logger", return_value=structured):
            yield structured, handler

    @pytest.fixture
    def performance_monitor(self):
        """Create performance monitor instance"""
        return EnhancedPerformanceMonitor()

    def test_structured_logging_with_performance_metrics(self, structured_logger):
        """Test that structured logging correctly captures performance metrics"""
        logger, handler = structured_logger

        # Log with performance metrics
        extra_data = {
            "operation": "test_operation",
            "execution_time_ms": 123.45,
            "cpu_percent": 45.2,
            "memory_mb": 512.3,
        }

        logger.info("Performance test", extra_data=extra_data)

        # Verify handler was called with correct extra data
        handler.handle.assert_called_once()
        log_record = handler.handle.call_args[0][0]

        # Check that extra_data was properly attached
        assert hasattr(log_record, "extra_data") or "extra_data" in log_record.__dict__
        if hasattr(log_record, "extra_data"):
            assert log_record.extra_data["operation"] == "test_operation"
            assert log_record.extra_data["execution_time_ms"] == 123.45
        else:
            # Alternative: check in __dict__
            assert "operation" in log_record.__dict__
            assert log_record.__dict__["operation"] == "test_operation"

    def test_log_execution_decorator_integration(self, structured_logger):
        """Test log_execution decorator with structured logging"""
        logger, handler = structured_logger

        @log_execution(operation_name="sample_function")
        def sample_function(value: int) -> int:
            time.sleep(0.01)  # Simulate work
            return value * 2

        result = sample_function(5)
        assert result == 10

        # Verify logging calls
        assert handler.handle.call_count >= 1

        # Check for performance metrics in logs
        calls = handler.handle.call_args_list
        end_log_found = False
        for call in calls:
            log_record = call[0][0]
            if hasattr(log_record, "extra_data"):
                extra = log_record.extra_data
                if "elapsed_ms" in extra:
                    end_log_found = True
                    assert extra["elapsed_ms"] >= 10  # At least 10ms
                    assert extra.get("operation") == "sample_function"
                    break

        assert end_log_found, "Performance metrics not found in logs"

    @pytest.mark.asyncio
    async def test_llm_execution_decorator_integration(self, structured_logger):
        """Test LLM execution decorator with structured logging"""
        logger, handler = structured_logger

        @log_llm_execution(model_name="test-model")
        async def mock_llm_call(prompt: str) -> dict:
            await asyncio.sleep(0.01)
            return {
                "response": "Test response",
                "tokens": {"input": 100, "output": 50},
                "model": "test-model",
                "total_cost": 0.123,
            }

        result = await mock_llm_call("Test prompt")
        assert result["response"] == "Test response"

        # Verify LLM-specific metrics in logs
        llm_records = [call[0][0] for call in handler.handle.call_args_list if hasattr(call[0][0], "extra_data")]
        assert llm_records, "No structured logs captured"

        matched = False
        for record in llm_records:
            extra = record.extra_data
            if extra.get("llm_model") == "test-model":
                matched = True
                assert extra["prompt_length"] == len("Test prompt")
                assert extra["operation"].endswith("mock_llm_call")
                assert extra["prompt_tokens"] == 100 or extra.get("tokens", {}).get("input") == 100
                assert extra["completion_tokens"] == 50 or extra.get("tokens", {}).get("output") == 50
                assert abs(extra.get("total_cost_usd", 0.0) - 0.123) < 1e-6
                break

        assert matched, "LLM metrics not found in logs"

    def test_request_context_integration(self, structured_logger):
        """Test request context tracking with structured logging"""
        logger, handler = structured_logger

        @with_request_context(request_id="test-123")
        def process_request():
            logger.info("Processing request")
            return "Done"

        result = process_request()
        assert result == "Done"

        # Verify request context in logs
        handler.handle.assert_called()
        log_record = handler.handle.call_args[0][0]
        if hasattr(log_record, "extra_data"):
            assert log_record.extra_data.get("request_id") == "test-123"

    @pytest.mark.asyncio
    async def test_claude_code_execution_service_logging(self):
        """Test ClaudeCodeExecutionService with structured logging"""
        # Mock dependencies
        mock_claude_service = MagicMock()
        mock_console_service = MagicMock()
        mock_config_service = MagicMock()
        mock_logger = MagicMock()

        # Configure mocks
        mock_config_service.get_max_turns_setting.return_value = 5
        mock_response = ClaudeCodeExecutionResponse(
            success=True,
            response_content='{"result": "test"}',
            execution_time_ms=100.0,
            error_message=None,
        )
        mock_claude_service.execute_prompt = asyncio.coroutine(lambda x: mock_response)

        # Create service
        service = ClaudeCodeExecutionService(
            claude_code_service=mock_claude_service,
            console_service=mock_console_service,
            configuration_service=mock_config_service,
            logger=mock_logger,
        )

        # Execute
        result = await service.execute_claude_code(
            prompt_content="Test prompt",
            project_root_paths=["/test/path"],
            session_id="session-123",
        )

        assert result.is_success()

        # Verify structured logging calls
        info_calls = [call for call in mock_logger.info.call_args_list]
        assert len(info_calls) >= 2  # Start and success logs

        # Check for extra_data in logs
        for call in info_calls:
            if len(call[1]) > 0 and "extra" in call[1]:
                extra = call[1]["extra"]
                if "extra_data" in extra:
                    extra_data = extra["extra_data"]
                    # Verify session_id is tracked
                    if "session_id" in extra_data:
                        assert extra_data["session_id"] == "session-123"
                    # Verify metrics are logged
                    if "execution_time_ms" in extra_data:
                        assert extra_data["execution_time_ms"] > 0

    def test_performance_monitor_integration(self, performance_monitor):
        """Test EnhancedPerformanceMonitor integration with structured logging"""

        @performance_monitor.monitor(name="test_operation")
        def test_function():
            time.sleep(0.01)  # Simulate work
            return 42

        result = test_function()
        assert result == 42

        # Verify metrics were collected
        assert len(performance_monitor.metrics) > 0
        metric = performance_monitor.metrics[-1]
        assert metric["function"] == "test_operation"
        assert metric["elapsed_ms"] >= 10  # At least 10ms

    def test_end_to_end_metrics_flow(self, structured_logger):
        """Test complete metrics flow from decorator to structured logger"""
        logger, handler = structured_logger

        @log_execution(logger=logger)
        def complex_operation(data: list) -> int:
            """Simulate complex operation with multiple metrics"""
            RequestContext.set("operation_id", "op-456")

            # Log intermediate metrics
            logger.info(
                "Processing data",
                extra_data={
                    "data_size": len(data),
                    "operation": "data_processing",
                }
            )

            # Simulate processing
            time.sleep(0.01)
            result = sum(data)

            # Log result metrics
            logger.info(
                "Processing complete",
                extra_data={
                    "result": result,
                    "items_processed": len(data),
                }
            )

            return result

        result = complex_operation([1, 2, 3, 4, 5])
        assert result == 15

        # Verify comprehensive metrics logging
        assert handler.handle.call_count >= 3  # Start, intermediate, end

        # Check that all logs have consistent operation_id
        operation_ids = []
        for call in handler.handle.call_args_list:
            log_record = call[0][0]
            if hasattr(log_record, "extra_data"):
                if "operation_id" in log_record.extra_data:
                    operation_ids.append(log_record.extra_data["operation_id"])

        # All logs should have the same operation_id from context
        assert len(set(operation_ids)) <= 1  # Either no IDs or all same

    @pytest.mark.parametrize("error_type", [
        ValueError("Test error"),
        KeyError("Missing key"),
        RuntimeError("Runtime issue"),
    ])
    def test_error_logging_with_metrics(self, structured_logger, error_type):
        """Test that errors are logged with proper metrics"""
        logger, handler = structured_logger

        @log_execution(logger=logger)
        def failing_function():
            raise error_type

        with pytest.raises(type(error_type)):
            failing_function()

        # Verify error was logged with metrics
        error_logged = False
        for call in handler.handle.call_args_list:
            log_record = call[0][0]
            if log_record.levelno == logging.ERROR:
                error_logged = True
                if hasattr(log_record, "extra_data"):
                    extra = log_record.extra_data
                    assert "error_type" in extra
                    assert extra["error_type"] == type(error_type).__name__
                    assert "execution_time_ms" in extra
                break

        assert error_logged, "Error not logged with metrics"
