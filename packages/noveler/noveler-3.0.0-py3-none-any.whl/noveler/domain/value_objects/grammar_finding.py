"""文法分析の値オブジェクト。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SeverityLiteral = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True)
class GrammarFinding:
    """文法上の課題を表す結果。"""

    issue_type: str
    severity: SeverityLiteral
    message: str
    line_number: int | None = None
    suggestion: str | None = None


@dataclass(frozen=True)
class GrammarAnalysisResult:
    """文法分析の結果。"""

    issues: list[GrammarFinding]
    score: float
