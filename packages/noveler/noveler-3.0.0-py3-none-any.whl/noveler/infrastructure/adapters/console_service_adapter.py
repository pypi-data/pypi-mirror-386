#!/usr/bin/env python3
"""Bridge the domain console protocol to the presentation console implementation."""

from noveler.domain.interfaces.console_service_protocol import IConsoleService
from noveler.infrastructure.logging.console_log_bridge import get_console_log_bridge
from noveler.presentation.shared.shared_utilities import console as shared_console

# DDD準拠: アダプターパターンで依存性注入による疎結合化


class ConsoleServiceAdapter(IConsoleService):
    """Expose a presentation-level console through the IConsoleService protocol."""

    def __init__(self, logger_service=None, console_service=None) -> None:
        """Initialize the adapter and obtain the shared presentation console.

        Delegates console access to the shared utilities singleton so we avoid duplicating
        Rich console instances across the application.
        """
        selected_console = console_service if console_service else shared_console

        self._console = selected_console

        # 統一ログ/コンソール統合ブリッジ（出力とログを同時に処理）
        try:
            self._bridge = get_console_log_bridge(__name__)
        except Exception:
            # 失敗時はフォールバック（コンソールのみ）
            self._bridge = None

        self.logger_service = logger_service
        self.console_service = console_service

    def print(self, message: str, style: str = "") -> None:
        """Print a message with an optional rich style tag.

        Args:
            message: Text to display.
            style: Rich style name applied to the message body.
        """
        if style:
            self._console.print(f"[{style}]{message}[/{style}]")
        else:
            self._console.print(message)

    def print_info(self, message: str) -> None:
        """Print an informational message using the bridge or console."""
        if getattr(self, "_bridge", None):
            self._bridge.print_info(message)  # type: ignore[union-attr]
            return
        self._console.print(f"[blue]{message}[/blue]")

    def print_success(self, message: str) -> None:
        """Print a success message using the bridge or console."""
        if getattr(self, "_bridge", None):
            self._bridge.print_success(message)  # type: ignore[union-attr]
            return
        self._console.print(f"[green]{message}[/green]")

    def print_warning(self, message: str) -> None:
        """Print a warning message using the bridge or console."""
        if getattr(self, "_bridge", None):
            self._bridge.print_warning(message)  # type: ignore[union-attr]
            return
        self._console.print(f"[yellow]{message}[/yellow]")

    def print_error(self, message: str) -> None:
        """Print an error message using the bridge or console."""
        if getattr(self, "_bridge", None):
            self._bridge.print_error(message)  # type: ignore[union-attr]
            return
        self._console.print(f"[red]{message}[/red]")

    def print_debug(self, message: str) -> None:
        """Print a debug message using the bridge or console."""
        if getattr(self, "_bridge", None):
            self._bridge.print_debug(message)  # type: ignore[union-attr]
            return
        self._console.print(f"[dim]{message}[/dim]")
