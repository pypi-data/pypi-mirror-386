"""Domain.services.dialogue_ratio_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DialogueRatioFinding:
    ratio: float
    min_ratio: float
    max_ratio: float
    severity: str  # "low"|"medium"


class DialogueRatioService:
    def compute_ratio(self, lines: List[str]) -> float:
        non_empty = [ln for ln in lines if (ln or "").strip()]
        if not non_empty:
            return 0.0
        dialogue_lines = [ln for ln in non_empty if ("「" in ln and "」" in ln)]
        return len(dialogue_lines) / max(len(non_empty), 1)

    def analyze(self, lines: List[str], *, min_ratio: float, max_ratio: float) -> DialogueRatioFinding | None:
        ratio = self.compute_ratio(lines)
        if ratio < min_ratio or ratio > max_ratio:
            sev = "medium" if abs(ratio - (min_ratio + max_ratio) / 2) > 0.2 else "low"
            return DialogueRatioFinding(ratio=ratio, min_ratio=min_ratio, max_ratio=max_ratio, severity=sev)
        return None
