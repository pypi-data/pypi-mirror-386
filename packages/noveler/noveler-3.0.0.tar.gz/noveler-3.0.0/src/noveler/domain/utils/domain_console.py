# File: src/noveler/domain/utils/domain_console.py
# Purpose: Provide a domain-safe console wrapper that records messages via the
#          domain logging helpers while avoiding hard dependencies on the
#          presentation layer.

"""Domain-safe console access utilities."""

from __future__ import annotations

import importlib
from typing import Any, Callable

from .domain_logging import is_delegate_enabled, push_domain_log

__all__ = ["get_console", "console", "DomainConsole", "NullConsole"]


def _load_console_factory() -> Callable[[], Any] | None:
    """Import the shared presentation console factory if available."""

    try:
        module = importlib.import_module("noveler.presentation.shared.shared_utilities")
    except Exception:
        return None

    return getattr(module, "get_console", None)


class DomainConsole:
    """Console wrapper that routes messages through domain logging helpers."""

    def __init__(self, delegate: Any | None = None) -> None:
        self._delegate = delegate

    # -- helper methods -------------------------------------------------
    def _render(self, *args: Any) -> str:
        return " ".join(str(arg) for arg in args)

    def _emit(self, level: str, message: str, delegate_method: str, *args: Any, **kwargs: Any) -> None:
        push_domain_log(level, message)
        if self._delegate is not None and is_delegate_enabled():
            method = getattr(self._delegate, delegate_method, None) or getattr(self._delegate, "print", None)
            if callable(method):
                try:
                    method(*args, **kwargs)
                except OSError as error:
                    push_domain_log("warning", f"Domain console delegate disabled: {error}")
                    self._delegate = None

    # -- Rich-like API ---------------------------------------------------
    def print(self, *args: Any, **kwargs: Any) -> None:
        self._emit("info", self._render(*args), "print", *args, **kwargs)

    def print_info(self, message: str) -> None:
        self._emit("info", message, "print_info", message)

    def print_success(self, message: str) -> None:
        self._emit("info", message, "print_success", message)

    def print_warning(self, message: str) -> None:
        self._emit("warning", message, "print_warning", message)

    def print_error(self, message: str) -> None:
        self._emit("error", message, "print_error", message)

    def print_debug(self, message: str) -> None:
        self._emit("debug", message, "print_debug", message)

    def rule(self, title: str, **kwargs: Any) -> None:  # pragma: no cover - optional helper
        self._emit("info", title, "rule", title, **kwargs)

    def log(self, *args: Any, **kwargs: Any) -> None:
        """Emit a Rich-compatible log message at info level."""

        self._emit("info", self._render(*args), "log", *args, **kwargs)

    # Compatibility aliases ---------------------------------------------
    def info(self, message: str) -> None:
        self.print_info(message)

    def success(self, message: str) -> None:
        self.print_success(message)

    def warning(self, message: str) -> None:
        self.print_warning(message)

    def error(self, message: str) -> None:
        self.print_error(message)

    def debug(self, message: str) -> None:
        self.print_debug(message)


class NullConsole(DomainConsole):
    """No-op domain console used when shared console is unavailable."""

    def __init__(self) -> None:  # noqa: D401 - explicit init for clarity
        super().__init__(delegate=None)


def get_console() -> DomainConsole:
    """Return a domain console wrapper.

    If the presentation layer exposes a shared console, messages will be
    delegated to it (subject to the domain logging context). Otherwise, a
    ``NullConsole`` instance is returned.
    """

    factory = _load_console_factory()
    if factory is None:
        return NullConsole()

    try:
        delegate = factory()
    except Exception:
        return NullConsole()

    return DomainConsole(delegate)


# Convenience shared instance for modules importing ``console`` at module scope.
console = get_console()
