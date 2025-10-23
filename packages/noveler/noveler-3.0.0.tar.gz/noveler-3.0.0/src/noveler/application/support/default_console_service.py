# File: src/noveler/application/support/default_console_service.py
# Purpose: Provide a presentation-free fallback console service for application layer components.
# Context: Supplies IConsoleService when dependency injection is unavailable, emitting to STDOUT only.
"""Default console service helpers for the application layer."""

from __future__ import annotations

from typing import Optional

from noveler.domain.interfaces.console_service_protocol import IConsoleService


class _DefaultConsoleService(IConsoleService):
    """Minimal console service that writes plain text to standard output."""

    def print(self, message: str, style: str = "") -> None:
        print(message)

    def print_info(self, message: str) -> None:
        print(f"[INFO] {message}")

    def print_success(self, message: str) -> None:
        print(f"[SUCCESS] {message}")

    def print_warning(self, message: str) -> None:
        print(f"[WARNING] {message}")

    def print_error(self, message: str) -> None:
        print(f"[ERROR] {message}")

    def print_debug(self, message: str) -> None:
        print(f"[DEBUG] {message}")

    # Rich互換エイリアス
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


_DEFAULT_CONSOLE: Optional[_DefaultConsoleService] = None


def _ensure_aliases(service: _DefaultConsoleService) -> None:
    """補助: Rich互換のエイリアスメソッドを確実に提供する。"""

    if not hasattr(service, "info"):
        service.info = service.print_info  # type: ignore[attr-defined]
    if not hasattr(service, "success"):
        service.success = service.print_success  # type: ignore[attr-defined]
    if not hasattr(service, "warning"):
        service.warning = service.print_warning  # type: ignore[attr-defined]
    if not hasattr(service, "error"):
        service.error = service.print_error  # type: ignore[attr-defined]
    if not hasattr(service, "debug"):
        service.debug = service.print_debug  # type: ignore[attr-defined]


def get_default_console_service() -> IConsoleService:
    """Return a singleton fallback console service."""

    global _DEFAULT_CONSOLE
    if _DEFAULT_CONSOLE is None:
        _DEFAULT_CONSOLE = _DefaultConsoleService()
    _ensure_aliases(_DEFAULT_CONSOLE)
    return _DEFAULT_CONSOLE
