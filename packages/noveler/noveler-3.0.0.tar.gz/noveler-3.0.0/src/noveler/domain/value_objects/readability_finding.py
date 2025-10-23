"""読みやすさ分析の値オブジェクト。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SeverityLiteral = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True)
class ReadabilityFinding:
    """読みやすさの課題を表す結果。"""

    issue_type: str
    severity: SeverityLiteral
    message: str
    line_number: int | None = None
    suggestion: str | None = None


@dataclass(frozen=True)
class ReadabilityAnalysisResult:
    """読みやすさ分析の結果。"""

    issues: list[ReadabilityFinding]
    score: float
    average_sentence_length: float | None = None
