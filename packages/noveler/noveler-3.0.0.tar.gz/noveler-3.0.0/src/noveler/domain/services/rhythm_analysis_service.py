"""Domain.services.rhythm_analysis_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from noveler.domain.value_objects.line_width_policy import LineWidthPolicy


@dataclass(frozen=True)
class LineWidthOverflow:
    line_number: int
    length: int
    severity: str  # "medium" or "high"


class RhythmAnalysisService:
    """文章リズム関連のドメインサービス。

    現時点では行幅超過の検出のみ提供（他検出は将来拡張）。
    ツール層/インフラ層に依存せず、純粋な計算のみ行う。
    """

    def check_line_width(self, lines: Iterable[str], policy: LineWidthPolicy) -> list[LineWidthOverflow]:
        out: list[LineWidthOverflow] = []
        for i, raw in enumerate(lines, 1):
            line = (raw or "").rstrip("\n")
            if not line.strip():
                continue
            if policy.is_dialogue_line(line):
                continue
            length = len(line)
            sev = policy.classify_length(length)
            if sev:
                out.append(LineWidthOverflow(line_number=i, length=length, severity=sev))
        return out
