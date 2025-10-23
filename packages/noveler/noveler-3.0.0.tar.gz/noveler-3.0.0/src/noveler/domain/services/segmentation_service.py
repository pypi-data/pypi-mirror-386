"""Domain.services.segmentation_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from typing import List, Tuple


class SegmentationService:
    """文分割と行マッピングの補助サービス（純粋関数）。"""

    def split_sentences_with_lines(self, lines: List[str]) -> Tuple[List[str], List[int]]:
        sentences: List[str] = []
        line_map: List[int] = []
        for idx, line in enumerate(lines, 1):
            work = (line or "").strip()
            if not work:
                continue
            parts = [p for p in work.split("。") if p.strip()]
            for p in parts:
                sentences.append(p)
                line_map.append(idx)
        return sentences, line_map
