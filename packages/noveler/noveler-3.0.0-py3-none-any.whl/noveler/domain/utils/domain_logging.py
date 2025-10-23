# File: src/noveler/domain/utils/domain_logging.py
# Purpose: Provide domain-friendly logging utilities that avoid hard dependencies
#          on presentation/infrastructure layers while allowing optional capture
#          of log messages by upper layers.
# Context: Domain services historically emitted user-facing messages via
#          console print helpers. This module introduces lightweight logging
#          primitives so that those messages can be captured (and UI output can
#          be suppressed) without introducing new layer violations.

"""Domain-level logging helpers.

The domain layer must not depend directly on presentation or infrastructure
components. When domain code needs to emit human-readable progress messages,
it should route them through these helpers so that:

* Upper layers can capture the messages for structured output (e.g. MCP
  responses, API payloads).
* UI output can be suppressed in headless environments (tests, batch runs).
* A Null logger fallback is available when no sink is configured.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Callable, Iterable, List, MutableSequence


LogSink = Callable[[str, str], None]

# Context variable holding the active sink. ``None`` means "no-op".
_sink_var: ContextVar[LogSink | None] = ContextVar("domain_log_sink", default=None)

# Context variable determining whether the underlying console delegate should
# receive UI output. Defaults to ``True`` to preserve legacy behaviour unless a
# caller explicitly suppresses UI.
_delegate_enabled_var: ContextVar[bool] = ContextVar("domain_delegate_enabled", default=True)


def push_domain_log(level: str, message: str) -> None:
    """Emit a log message to the active sink if any.

    Args:
        level: Semantic level (``info``, ``warning``, ``error`` ...).
        message: Human-readable message text.
    """

    sink = _sink_var.get()
    if sink is not None:
        try:
            sink(level, message)
        except Exception:  # pragma: no cover - defensive guard
            # Domain layer must never raise because a sink misbehaved.
            pass


def is_delegate_enabled() -> bool:
    """Return whether UI delegates should be invoked."""

    return _delegate_enabled_var.get()


@contextmanager
def suppress_domain_console_output() -> Iterable[None]:
    """Temporarily suppress delegated console output.

    Domain services will still emit log messages via ``push_domain_log`` but
    any underlying console delegate (e.g. the shared Rich console) is bypassed.
    """

    token = _delegate_enabled_var.set(False)
    try:
        yield
    finally:
        _delegate_enabled_var.reset(token)


@contextmanager
def capture_domain_logs(
    *,
    buffer: MutableSequence[dict[str, str]] | None = None,
    suppress_ui: bool = True,
) -> Iterable[MutableSequence[dict[str, str]]]:
    """Capture domain log entries within the context.

    Args:
        buffer: Optional pre-existing buffer to append log dictionaries to.
        suppress_ui: When ``True`` (default) domain console delegates will not
            emit UI output while logs are captured.

    Yields:
        A mutable sequence of log dictionaries with ``level`` and ``message`` keys.
    """

    logs: MutableSequence[dict[str, str]]
    if buffer is not None:
        logs = buffer
    else:
        logs = []

    def _sink(level: str, message: str) -> None:
        logs.append({"level": level, "message": message})

    sink_token = _sink_var.set(_sink)
    delegate_token = None

    if suppress_ui:
        delegate_token = _delegate_enabled_var.set(False)

    try:
        yield logs
    finally:
        _sink_var.reset(sink_token)
        if delegate_token is not None:
            _delegate_enabled_var.reset(delegate_token)


__all__ = [
    "capture_domain_logs",
    "push_domain_log",
    "suppress_domain_console_output",
    "is_delegate_enabled",
]
