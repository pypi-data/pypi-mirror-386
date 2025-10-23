"""Domain.services.ending_repetition_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class EndingRepetitionFinding:
    ending: str
    count: int
    start_sentence_index: int
    end_sentence_index: int


class EndingRepetitionService:
    def _ending(self, s: str) -> str:
        s = (s or "").strip()
        if not s:
            return ""
        return s[-2:]

    def analyze(self, sentences: List[str], *, threshold: int) -> List[EndingRepetitionFinding]:
        out: List[EndingRepetitionFinding] = []
        cur: str | None = None
        count = 0
        start_idx = 0
        for idx, s in enumerate(sentences):
            e = self._ending(s)
            if e == cur and e:
                count += 1
            else:
                if cur and count >= threshold:
                    out.append(
                        EndingRepetitionFinding(ending=cur, count=count, start_sentence_index=start_idx, end_sentence_index=idx - 1)
                    )
                cur = e
                count = 1
                start_idx = idx
        if cur and count >= threshold:
            out.append(EndingRepetitionFinding(ending=cur, count=count, start_sentence_index=start_idx, end_sentence_index=len(sentences) - 1))
        return out
