"""CLI compatibility shim for shared utilities.

Provides backwards-compatible imports for console and helpers under
noveler.presentation.cli.shared_utilities by re-exporting from
noveler.presentation.shared.shared_utilities.
"""
from __future__ import annotations

from noveler.presentation.shared.shared_utilities import (  # noqa: F401
    console,  # Rich Console singleton
    get_console,
    get_logger,
    get_common_path_service,
    get_app_state,
)

