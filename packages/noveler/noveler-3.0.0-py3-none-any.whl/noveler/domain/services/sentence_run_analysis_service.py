"""Domain.services.sentence_run_analysis_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ConsecutiveRunFinding:
    kind: str  # "long" or "short"
    count: int
    start_sentence_index: int
    end_sentence_index: int


class SentenceRunAnalysisService:
    """長文/短文の連続を検出するサービス。"""

    def classify(self, sentence: str, long_len: int, short_len: int) -> str:
        n = len(sentence or "")
        if n >= long_len:
            return "long"
        if n <= short_len:
            return "short"
        return "mid"

    def find_consecutive_runs(
        self, sentences: List[str], *, long_len: int, short_len: int, long_thr: int, short_thr: int
    ) -> List[ConsecutiveRunFinding]:
        out: List[ConsecutiveRunFinding] = []
        cur_kind: str | None = None
        cur_count = 0
        start_idx = 0
        for idx, s in enumerate(sentences):
            k = self.classify(s, long_len, short_len)
            if k == cur_kind:
                cur_count += 1
            else:
                if cur_kind in ("long", "short"):
                    out.append(
                        ConsecutiveRunFinding(
                            kind=cur_kind, count=cur_count, start_sentence_index=start_idx, end_sentence_index=idx - 1
                        )
                    )
                cur_kind = k
                cur_count = 1
                start_idx = idx
        if cur_kind in ("long", "short"):
            out.append(
                ConsecutiveRunFinding(kind=cur_kind, count=cur_count, start_sentence_index=start_idx, end_sentence_index=len(sentences) - 1)
            )

        # しきい値でフィルタ
        filtered: List[ConsecutiveRunFinding] = []
        for f in out:
            if f.kind == "long" and f.count >= long_thr:
                filtered.append(f)
            if f.kind == "short" and f.count >= short_thr:
                filtered.append(f)
        return filtered
