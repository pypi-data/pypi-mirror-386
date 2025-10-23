# File: tests/contracts/test_metrics_sink_contract.py
# Purpose: Contract tests for MetricsSinkPort to ensure implementation compliance.
# Context: Validates metrics sink implementations adhere to MetricsSinkPort protocol.

"""Contract tests for MetricsSinkPort.

Purpose:
    Verify that all MetricsSinkPort implementations satisfy the protocol contract.
Context:
    Part of B20 Workflow Phase 4 contract testing requirements.
Preconditions:
    None.
Side Effects:
    None (read-only tests).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from noveler.domain.interfaces.metrics_sink_port import MetricsSinkPort

from noveler.domain.events.base import DomainEvent
from noveler.infrastructure.adapters.infrastructure_metrics_sink import LoggingMetricsSink
from noveler.infrastructure.adapters.message_bus_metrics_sink import MessageBusMetricsSink
from noveler.infrastructure.adapters.metrics_sink_composite import CompositeMetricsSink
from noveler.infrastructure.adapters.outbox_metrics_sink import OutboxMetricsSink

pytestmark = pytest.mark.contract


class MockDomainEvent(DomainEvent):
    """Mock domain event for testing."""

    def __init__(self, event_type: str, data: dict):
        self.event_type = event_type
        self.data = data
        # Required by DomainEvent base class __str__
        self.event_id = "mock_event_id_12345678"
        self.aggregate_id = "mock_aggregate"


class TestMetricsSinkContract:
    """Contract tests for MetricsSinkPort protocol.

    Purpose:
        Ensure implementations satisfy metrics publishing contract.
    """

    @pytest.fixture(params=[
        LoggingMetricsSink,
        lambda: MessageBusMetricsSink(None),
        lambda: OutboxMetricsSink(),
        lambda: CompositeMetricsSink([]),
    ])
    def sink(self, request) -> MetricsSinkPort:
        """Provide MetricsSinkPort implementations for testing.

        Returns:
            Various sink implementations as protocol implementations.
        """
        if callable(request.param):
            return request.param()
        return request.param()

    @pytest.mark.spec("SPEC-METRICS_SINK_PORT-PUBLISH_EMPTY")
    def test_publish_accepts_empty_iterable(self, sink: MetricsSinkPort) -> None:
        """Verify publish() accepts empty event iterable without errors."""
        # Should not raise any exception
        sink.publish([])

    @pytest.mark.spec("SPEC-METRICS_SINK_PORT-PUBLISH_SINGLE")
    def test_publish_accepts_single_event(self, sink: MetricsSinkPort) -> None:
        """Verify publish() accepts single event without errors."""
        event = MockDomainEvent("test_event", {"key": "value"})

        # Should not raise any exception
        sink.publish([event])

    @pytest.mark.spec("SPEC-METRICS_SINK_PORT-PUBLISH_MULTIPLE")
    def test_publish_accepts_multiple_events(self, sink: MetricsSinkPort) -> None:
        """Verify publish() accepts multiple events without errors."""
        events = [
            MockDomainEvent("event1", {"data": 1}),
            MockDomainEvent("event2", {"data": 2}),
            MockDomainEvent("event3", {"data": 3}),
        ]

        # Should not raise any exception
        sink.publish(events)

    @pytest.mark.spec("SPEC-METRICS_SINK_PORT-PUBLISH_GENERATOR")
    def test_publish_accepts_generator(self, sink: MetricsSinkPort) -> None:
        """Verify publish() accepts generator iterable."""
        def event_generator():
            for i in range(5):
                yield MockDomainEvent(f"event{i}", {"index": i})

        # Should not raise any exception
        sink.publish(event_generator())


class TestMetricsSinkSpecCompliance:
    """Verify MetricsSinkPort contract coverage and implementation compliance.

    Purpose:
        Meta-tests to ensure contract tests cover the protocol completely.
    """

    @pytest.mark.spec("SPEC-METRICS_SINK_PORT-PROTOCOL_COMPLIANCE")
    def test_logging_sink_is_valid_protocol(self) -> None:
        """Verify LoggingMetricsSink satisfies MetricsSinkPort protocol."""
        from noveler.domain.interfaces.metrics_sink_port import MetricsSinkPort

        sink: MetricsSinkPort = LoggingMetricsSink()

        assert hasattr(sink, "publish")
        assert callable(sink.publish)

    @pytest.mark.spec("SPEC-METRICS_SINK_PORT-COMPOSITE_COMPLIANCE")
    def test_composite_sink_is_valid_protocol(self) -> None:
        """Verify CompositeMetricsSink satisfies MetricsSinkPort protocol."""
        from noveler.domain.interfaces.metrics_sink_port import MetricsSinkPort

        sink: MetricsSinkPort = CompositeMetricsSink([])

        assert hasattr(sink, "publish")
        assert callable(sink.publish)

    @pytest.mark.spec("SPEC-METRICS_SINK_PORT-CONTRACT_COVERAGE")
    def test_metrics_sink_contract_coverage(self) -> None:
        """Verify contract tests cover all critical scenarios."""
        required_scenarios = [
            "empty",      # test_publish_accepts_empty_iterable
            "single",     # test_publish_accepts_single_event
            "multiple",   # test_publish_accepts_multiple_events
            "generator",  # test_publish_accepts_generator
        ]

        test_methods = [
            method
            for method in dir(TestMetricsSinkContract)
            if method.startswith("test_")
        ]

        for scenario in required_scenarios:
            assert any(
                scenario in method for method in test_methods
            ), f"Missing contract test for scenario: {scenario}"
