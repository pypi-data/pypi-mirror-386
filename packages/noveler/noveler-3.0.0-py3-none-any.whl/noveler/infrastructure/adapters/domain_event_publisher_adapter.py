"""Publish domain events to the shared console implementation.

Specification: SPEC-DDD-COMPLIANCE-004
"""

from typing import Any

from noveler.domain.interfaces.event_publisher_protocol import (
    DomainEvent,
    EventLevel,
    IDomainEventPublisher,
    ProgressEvent,
    ValidationEvent,
)
from noveler.presentation.shared.shared_utilities import console


class ConsoleEventPublisherAdapter(IDomainEventPublisher):
    """Publish domain events to a Rich console target."""

    def __init__(self) -> None:
        self.console_service = console

    def _resolve_console(self) -> Any:
        service = getattr(self, "console_service", console)
        return service

    def publish(self, event: DomainEvent) -> None:
        """Publish the provided domain event.

        Args:
            event: Domain event scheduled for publication.
        """
        if isinstance(event, ProgressEvent):
            self._publish_progress_event(event)
        elif isinstance(event, ValidationEvent):
            self._publish_validation_event(event)
        else:
            self._publish_basic_event(event)

    def publish_info(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Publish an informational message as a domain event.

        Args:
            message: Message body to display.
            context: Optional contextual metadata.
        """
        event = DomainEvent(message=message, level=EventLevel.INFO, context=context)
        self.publish(event)

    def publish_warning(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Publish a warning-level domain event.

        Args:
            message: Message body to display.
            context: Optional contextual metadata.
        """
        event = DomainEvent(message=message, level=EventLevel.WARNING, context=context)
        self.publish(event)

    def publish_error(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Publish an error-level domain event.

        Args:
            message: Message body to display.
            context: Optional contextual metadata.
        """
        event = DomainEvent(message=message, level=EventLevel.ERROR, context=context)
        self.publish(event)

    def publish_progress(self, message: str, current: int, total: int) -> None:
        """Publish a progress event to report completion percentage.

        Args:
            message: Progress message to display.
            current: Current completed value.
            total: Total value representing 100%.
        """
        event = ProgressEvent(message=message, current=current, total=total, level=EventLevel.INFO)
        self.publish(event)

    def _publish_basic_event(self, event: DomainEvent) -> None:
        """Render a non-progress, non-validation event to the console.

        Args:
            event: Domain event describing the message and metadata.
        """
        message = event.message
        service = self._resolve_console()
        printer = getattr(service, "print", console.print)
        if event.level == EventLevel.INFO:
            printer(f"INFO: {message}")
        elif event.level == EventLevel.WARNING:
            printer(f"WARNING: {message}")
        elif event.level == EventLevel.ERROR:
            printer(f"ERROR: {message}")
        elif event.level == EventLevel.SUCCESS:
            printer(f"SUCCESS: {message}")
        elif event.level == EventLevel.DEBUG:
            printer(f"DEBUG: {message}")
        else:
            printer(message)
        if event.context:
            for key, value in event.context.items():
                printer(f"  {key}: {value}")

    def _publish_progress_event(self, event: ProgressEvent) -> None:
        """Render a progress event with percentage output.

        Args:
            event: Progress event carrying completion metrics.
        """
        percentage = event.current / event.total * 100 if event.total > 0 else 0
        service = self._resolve_console()
        printer = getattr(service, "print", console.print)
        printer(f"PROGRESS: {event.message} [{event.current}/{event.total}] ({percentage:.1f}%)")

    def _publish_validation_event(self, event: ValidationEvent) -> None:
        """Render a validation event summarizing its outcome.

        Args:
            event: Validation event containing success and detail data.
        """
        service = self._resolve_console()
        printer = getattr(service, "print", console.print)
        if event.is_valid:
            printer(f"VALIDATION: OK - {event.message}")
        else:
            printer(f"VALIDATION: FAIL - {event.message}")
        if event.details:
            for key, value in event.details.items():
                printer(f"  {key}: {value}")


_event_publisher = ConsoleEventPublisherAdapter()


def get_domain_event_publisher() -> IDomainEventPublisher:
    """Return the shared domain event publisher instance.

    Returns:
        IDomainEventPublisher: Console-backed event publisher singleton.
    """
    return _event_publisher
