# File: src/noveler/application/mcp_services/provider.py
# Purpose: Aggregate tool services so FastMCP registrations can retrieve the
#          required implementation without tight coupling to constructors.
# Context: Injected into infrastructure-layer tool registration classes.
"""Service provider for MCP tool registrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .plot import PlotToolService
from .quality import QualityToolService
from .writing import WritingToolService


@dataclass(slots=True)
class ToolServiceProvider:
    """Thin container exposing the different MCP tool services."""

    writing: Optional[WritingToolService] = None
    plot: Optional[PlotToolService] = None
    quality: Optional[QualityToolService] = None

    def require_writing(self) -> WritingToolService:
        if not self.writing:
            raise RuntimeError("WritingToolService has not been configured.")
        return self.writing

    def require_plot(self) -> PlotToolService:
        if not self.plot:
            raise RuntimeError("PlotToolService has not been configured.")
        return self.plot

    def require_quality(self) -> QualityToolService:
        if not self.quality:
            raise RuntimeError("QualityToolService has not been configured.")
        return self.quality

