"""読みやすさ分析サービス。"""

from __future__ import annotations

import statistics
from collections.abc import Iterable  # noqa: TC003
from dataclasses import dataclass

from noveler.domain.value_objects.readability_finding import (
    ReadabilityAnalysisResult,
    ReadabilityFinding,
    SeverityLiteral,
)


@dataclass(frozen=True)
class ReadabilityThresholds:
    """読みやすさ分析に使用する閾値。"""

    long_sentence_length: int = 80
    very_long_sentence_length: int = 100
    average_sentence_warning: float = 50.0


class ReadabilityAnalysisService:
    """文章の読みやすさを分析するサービス。"""

    _DEFAULT_ASPECTS = ("sentence_length", "vocabulary_complexity", "readability_score")
    _COMPLEX_WORDS = ("煩瑣", "繁雑", "冗漫", "膨大", "顕著")

    def __init__(self, thresholds: ReadabilityThresholds | None = None) -> None:
        self._thresholds = thresholds or ReadabilityThresholds()

    def analyze(
        self,
        content: str,
        *,
        aspects: Iterable[str] | None = None,
        exclude_dialogue_lines: bool = False,
    ) -> ReadabilityAnalysisResult:
        """読みやすさを分析する。"""

        normalized_aspects = list(aspects) if aspects is not None else list(self._DEFAULT_ASPECTS)
        aspect_set = set(normalized_aspects)

        issues: list[ReadabilityFinding] = []
        lines = content.split("\n")

        # 会話行を検出（exclude_dialogue_linesが有効な場合）
        dialogue_flags = None
        if exclude_dialogue_lines:
            dialogue_flags = [self._is_dialogue_line(line) for line in lines]

        for idx, raw_line in enumerate(lines, 1):
            line = raw_line.strip()
            if not line:
                continue

            # 会話行を除外する場合は、文長チェックをスキップ
            should_skip_sentence_length = (
                exclude_dialogue_lines and
                dialogue_flags is not None and
                idx <= len(dialogue_flags) and
                dialogue_flags[idx - 1]
            )

            if "sentence_length" in aspect_set and not should_skip_sentence_length:
                issues.extend(self._check_sentence_length(line, idx))
            if "vocabulary_complexity" in aspect_set:
                issues.extend(self._check_vocabulary_complexity(line, idx))

        average_sentence_length = None
        if "readability_score" in aspect_set:
            readability_issues, average_sentence_length = self._check_overall_readability(content)
            issues.extend(readability_issues)

        score = self._calculate_readability_score(issues, len(content))
        return ReadabilityAnalysisResult(issues=issues, score=score, average_sentence_length=average_sentence_length)

    # ---- individual checks -------------------------------------------------

    def _check_sentence_length(self, line: str, line_number: int) -> list[ReadabilityFinding]:
        findings: list[ReadabilityFinding] = []
        sentences = (segment.strip() for segment in line.split("。"))
        for sentence in sentences:
            if not sentence:
                continue
            length = len(sentence)
            if length > self._thresholds.long_sentence_length:
                severity: SeverityLiteral = "medium" if length > self._thresholds.very_long_sentence_length else "low"
                findings.append(
                    ReadabilityFinding(
                        issue_type="long_sentence",
                        severity=severity,
                        message=f"文が長すぎます（{length}文字）。分割を検討してください。",
                        line_number=line_number,
                        suggestion="長い文を短く分けることで読みやすさが向上します",
                    )
                )
        return findings

    def _check_vocabulary_complexity(self, line: str, line_number: int) -> list[ReadabilityFinding]:
        return [
            ReadabilityFinding(
                issue_type="complex_vocabulary",
                severity="low",
                message=f"難解な語彙が含まれています: {word}",
                line_number=line_number,
                suggestion="より平易な言葉への置き換えを検討してください",
            )
            for word in self._COMPLEX_WORDS
            if word in line
        ]

    def _check_overall_readability(self, content: str) -> tuple[list[ReadabilityFinding], float | None]:
        normalized = content.replace("\n", "")
        sentences = [segment.strip() for segment in normalized.split("。") if segment.strip()]
        if not sentences:
            return ([], None)

        average_length = statistics.fmean(len(sentence) for sentence in sentences)
        if average_length > self._thresholds.average_sentence_warning:
            finding = ReadabilityFinding(
                issue_type="high_average_sentence_length",
                severity="medium",
                message=f"文章全体の平均文長が長めです（{average_length:.1f}文字）",
                suggestion="全体的に文を短くすることで読みやすさが向上します",
            )
            return ([finding], average_length)

        return ([], average_length)

    # ---- scoring -----------------------------------------------------------

    def _calculate_readability_score(self, issues: Iterable[ReadabilityFinding], content_length: int) -> float:
        if content_length == 0:
            return 100.0

        penalty = 0
        for issue in issues:
            penalty += self._penalty_for(issue.severity)
        return max(0.0, 100.0 - float(penalty))

    @staticmethod
    def _penalty_for(severity: SeverityLiteral) -> int:
        if severity == "critical":
            return 20
        if severity == "high":
            return 10
        if severity == "medium":
            return 5
        return 2

    @staticmethod
    def _is_dialogue_line(line: str) -> bool:
        """行が会話行かどうかを判定する。"""
        stripped = line.strip()
        if not stripped:
            return False

        # 「」や『』で始まるか、含まれている行を会話行とみなす
        return (
            stripped.startswith("「") or stripped.startswith("『") or
            "「" in stripped or "『" in stripped or
            "」" in stripped or "』" in stripped
        )
