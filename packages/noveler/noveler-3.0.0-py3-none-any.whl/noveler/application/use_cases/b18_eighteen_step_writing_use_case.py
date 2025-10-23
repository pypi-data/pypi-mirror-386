"""Legacy compatibility shims for tests expecting the B18 writing use case module."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class EighteenStepWritingRequest:
    """Minimal request placeholder used by historical tests."""

    episode_number: int
    project_root: Path | str | None = None
    options: dict[str, Any] | None = None


class EighteenStepWritingUseCase:
    """Thin shell that surfaces NotImplemented errors for test doubles."""

    async def execute(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError(
            "EighteenStepWritingUseCase is a legacy shim; use IntegratedWritingUseCase instead."
        )
