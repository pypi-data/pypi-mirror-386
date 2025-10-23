"""Scripts.presentation.cli.shared_utilities
Where: Shared utility functions for CLI scripts.
What: Implements helper routines reused across CLI commands.
Why: Avoids duplication when building command-line tooling.
"""

from noveler.presentation.shared.shared_utilities import (
    console,
    get_common_path_service,
    get_logger,
)


def handle_command_error(message: str) -> str:
    """Compatibility shim for legacy error handler used in tests.

    Returns the message for simple assertions and prints to console.
    """
    try:
        console.print(f"[red]ERROR:[/red] {message}")
    except Exception:
        pass
    return message

__all__ = [
    "console",
    "get_common_path_service",
    "get_logger",
    "handle_command_error",
]
