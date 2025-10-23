"""Domain.services.comma_density_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class CommaAvgFinding:
    average: float
    min_avg: float
    max_avg: float


@dataclass(frozen=True)
class CommaOveruseFinding:
    sentence_index: int
    count: int
    max_allowed: int


class CommaDensityService:
    def analyze(self, sentences: List[str], *, min_avg: float, max_avg: float, per_sentence_max: int) -> tuple[CommaAvgFinding | None, List[CommaOveruseFinding]]:
        if not sentences:
            return None, []
        counts = [s.count("、") for s in sentences]
        avg = sum(counts) / max(len(counts), 1)
        avg_finding: CommaAvgFinding | None = None
        if avg < min_avg or avg > max_avg:
            avg_finding = CommaAvgFinding(average=avg, min_avg=min_avg, max_avg=max_avg)
        over: List[CommaOveruseFinding] = []
        for idx, c in enumerate(counts):
            if c > per_sentence_max:
                over.append(CommaOveruseFinding(sentence_index=idx, count=c, max_allowed=per_sentence_max))
        return avg_finding, over
