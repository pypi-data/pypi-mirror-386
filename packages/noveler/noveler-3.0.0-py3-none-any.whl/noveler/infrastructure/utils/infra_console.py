# File: src/noveler/infrastructure/utils/infra_console.py
# Purpose: Provide infrastructure-safe console access that delegates to domain
#          console utilities, avoiding direct presentation layer dependencies.
# Context: B20/DDD compliance - Infrastructure must not directly import
#          presentation.shared.shared_utilities

"""Infrastructure-safe console access utilities.

This module provides console access for Infrastructure layer services
without violating DDD layering principles. It delegates to domain console
utilities which handle lazy loading of presentation layer components.

Usage:
    from noveler.infrastructure.utils.infra_console import get_console

    console = get_console()
    console.print_info("Starting service...")
    console.print_success("Service initialized")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from noveler.domain.utils.domain_console import DomainConsole
    from noveler.infrastructure.logging.i_logger import ILogger

__all__ = ["get_console", "console", "get_logger"]


def get_console() -> DomainConsole:
    """Return a console instance for infrastructure layer services.

    Delegates to domain console utilities which handle lazy loading
    of presentation layer components without violating DDD boundaries.

    Returns:
        DomainConsole instance that safely wraps presentation console
    """
    from noveler.domain.utils.domain_console import get_console as domain_get_console

    return domain_get_console()


def get_logger(name: str) -> ILogger:
    """Return a logger instance for infrastructure layer services.

    Delegates to unified_logger which provides a consistent logging interface
    across the infrastructure layer.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        ILogger instance for infrastructure layer logging
    """
    from noveler.infrastructure.logging.unified_logger import get_logger as _get_unified_logger

    return _get_unified_logger(name)


# Convenience module-level instance for direct import
console = get_console()
