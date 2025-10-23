"""Domain.services.punctuation_style_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class PunctuationFinding:
    kind: str  # "ellipsis_style" | "ellipsis_odd_count" | "dash_style"
    line_index: int
    found: Optional[str] = None
    count: Optional[int] = None


class PunctuationStyleService:
    """約物スタイルの統一検出サービス。

    三点リーダ（……）/ダッシュ（――）のスタイル逸脱を検出する。
    """

    def analyze_lines(self, lines: List[str]) -> List[PunctuationFinding]:
        findings: List[PunctuationFinding] = []
        for i, raw in enumerate(lines, 1):
            line = (raw or "").strip()
            if not line:
                continue
            # 三点リーダの半端/異スタイル
            if "..." in line or "・・・" in line:
                findings.append(
                    PunctuationFinding(kind="ellipsis_style", line_index=i, found=("..." if "..." in line else "・・・"))
                )
            ellipsis_count = line.count("…")
            if ellipsis_count % 2 == 1:
                findings.append(
                    PunctuationFinding(kind="ellipsis_odd_count", line_index=i, count=ellipsis_count)
                )
            # ダッシュ
            if ("—" in line or "－" in line) and "――" not in line:
                findings.append(PunctuationFinding(kind="dash_style", line_index=i))
        return findings
