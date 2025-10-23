"""文法分析サービス。"""

from __future__ import annotations

import re
from collections.abc import Iterable  # noqa: TC003
from dataclasses import dataclass

from noveler.domain.value_objects.grammar_finding import GrammarAnalysisResult, GrammarFinding, SeverityLiteral


@dataclass(frozen=True)
class GrammarAnalysisConfiguration:
    """文法分析で使用する設定。"""

    typo_patterns: dict[str, str] = None  # type: ignore[assignment]
    particle_patterns: tuple[tuple[str, str], ...] = (
        (r"(.+)は(.+)を行う", "「は」は「が」の方が適切な場合があります"),
        (r"(.+)に対して(.+)を", "「について」の方が自然な場合があります"),
    )
    notation_patterns: tuple[tuple[str, str, str], ...] = (
        (r"(\d+)時", r"(\d+)時間", "時刻と時間の表記に注意"),
        (r"出来る", r"できる", "ひらがな表記で統一することを推奨"),
    )
    long_sentence_without_punctuation: int = 50

    def __post_init__(self) -> None:
        if self.typo_patterns is None:
            object.__setattr__(self, "typo_patterns", {
                r"いいえ": "いえ",
                r"なにか": "何か",
                r"おもしろい": "面白い",
            })


class GrammarAnalysisService:
    """文章の文法上の問題を検出するサービス。"""

    _DEFAULT_TYPES = ("typo", "particle_error", "notation_inconsistency", "punctuation")

    def __init__(self, config: GrammarAnalysisConfiguration | None = None) -> None:
        self._config = config or GrammarAnalysisConfiguration()

    def analyze(self, content: str, *, check_types: Iterable[str] | None = None) -> GrammarAnalysisResult:
        types = set(check_types or self._DEFAULT_TYPES)
        issues: list[GrammarFinding] = []

        for line_number, raw_line in enumerate(content.split("\n"), 1):
            line = raw_line.strip()
            if not line:
                continue

            if "typo" in types:
                issues.extend(self._check_typos(line, line_number))
            if "particle_error" in types:
                issues.extend(self._check_particle_errors(line, line_number))
            if "notation_inconsistency" in types:
                issues.extend(self._check_notation_inconsistency(line, line_number))
            if "punctuation" in types:
                issues.extend(self._check_punctuation(line, line_number))

        score = self._calculate_grammar_score(issues, len(content))
        return GrammarAnalysisResult(issues=issues, score=score)

    # ---- individual checks -------------------------------------------------

    def _check_typos(self, line: str, line_number: int) -> list[GrammarFinding]:
        findings: list[GrammarFinding] = []
        for pattern, correction in self._config.typo_patterns.items():
            if re.search(pattern, line):
                findings.append(
                    GrammarFinding(
                        issue_type="typo",
                        severity="high",
                        message=f"誤字の可能性: '{pattern}' → '{correction}'",
                        line_number=line_number,
                        suggestion=f"'{correction}'への修正を検討してください",
                    )
                )
        return findings

    def _check_particle_errors(self, line: str, line_number: int) -> list[GrammarFinding]:
        findings: list[GrammarFinding] = []
        for pattern, suggestion in self._config.particle_patterns:
            if re.search(pattern, line):
                findings.append(
                    GrammarFinding(
                        issue_type="particle_error",
                        severity="medium",
                        message="助詞の使い方に違和感があります",
                        line_number=line_number,
                        suggestion=suggestion,
                    )
                )
        return findings

    def _check_notation_inconsistency(self, line: str, line_number: int) -> list[GrammarFinding]:
        findings: list[GrammarFinding] = []
        for left, right, message in self._config.notation_patterns:
            if re.search(left, line) and re.search(right, line):
                findings.append(
                    GrammarFinding(
                        issue_type="notation_inconsistency",
                        severity="medium",
                        message=f"表記揺れの可能性: {message}",
                        line_number=line_number,
                        suggestion="文章全体で表記を統一してください",
                    )
                )
        return findings

    def _check_punctuation(self, line: str, line_number: int) -> list[GrammarFinding]:
        findings: list[GrammarFinding] = []
        if len(line) > self._config.long_sentence_without_punctuation and "、" not in line and "。" not in line:
            findings.append(
                GrammarFinding(
                    issue_type="punctuation",
                    severity="medium",
                    message="長い文に句読点がありません",
                    line_number=line_number,
                    suggestion="適切な位置に読点を追加することで読みやすくなります",
                )
            )

        if re.search(r"[、。]{2,}", line):
            findings.append(
                GrammarFinding(
                    issue_type="punctuation",
                    severity="high",
                    message="句読点が連続しています",
                    line_number=line_number,
                    suggestion="不要な句読点を削除してください",
                )
            )
        return findings

    # ---- scoring -----------------------------------------------------------

    def _calculate_grammar_score(self, issues: Iterable[GrammarFinding], content_length: int) -> float:
        if content_length == 0:
            return 100.0

        penalty = 0
        for issue in issues:
            penalty += self._penalty_for(issue.severity)
        return max(0.0, 100.0 - float(penalty))

    @staticmethod
    def _penalty_for(severity: SeverityLiteral) -> int:
        if severity == "critical":
            return 25
        if severity == "high":
            return 15
        if severity == "medium":
            return 8
        return 3
