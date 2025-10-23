# File: src/mcp_servers/noveler/tools/test_result_analysis_components.py
# Purpose: Provide reusable helper classes for enhanced test result analysis
#          features (delta analysis, error grouping, hierarchical context).
# Context: Imported by ResultAnalysisTool to keep the main tool implementation
#          focused on orchestration while encapsulating analytic logic.

"""Helper components for the enhanced test result analysis workflow."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Sequence

from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolIssue

__all__ = [
    "DeltaAnalysis",
    "ErrorGroup",
    "ErrorGrouper",
    "HierarchicalContext",
    "IncrementalAnalyzer",
    "TestError",
]


@dataclass(frozen=True, slots=True)
class DeltaAnalysis:
    """Represent the delta between the current and previous test runs."""

    newly_failed: list[str]
    newly_passed: list[str]
    still_failing: list[str]
    regressions: list[str]
    improvement_rate: float

    def to_metadata(self, *, compact: bool = False) -> dict[str, Any]:
        """Convert the delta analysis into a metadata payload."""
        rounded_rate = round(self.improvement_rate, 2)
        if compact:
            return {
                "improvement_rate": rounded_rate,
                "counts": {
                    "newly_failed": len(self.newly_failed),
                    "newly_passed": len(self.newly_passed),
                    "still_failing": len(self.still_failing),
                    "regressions": len(self.regressions),
                },
            }
        return {
            "improvement_rate": rounded_rate,
            "newly_failed": self.newly_failed,
            "newly_passed": self.newly_passed,
            "still_failing": self.still_failing,
            "regressions": self.regressions,
        }


@dataclass(frozen=True, slots=True)
class TestError:
    """Normalised representation of a failing test case."""

    nodeid: str
    error_type: str
    severity: str
    message: str
    module: str

    def to_example(self) -> dict[str, str]:
        """Return a lightweight example structure suitable for metadata."""
        headline = self.message.splitlines()[0].strip() if self.message else ""
        snippet = headline[:160]
        return {
            "nodeid": self.nodeid,
            "message": snippet,
            "severity": self.severity,
        }


@dataclass(frozen=True, slots=True)
class ErrorGroup:
    """Hold a group of similar errors for token-efficient reporting."""

    pattern: str
    error_type: str
    count: int
    examples: list[TestError]
    affected_modules: set[str]
    highest_severity: str

    def to_metadata(self, *, example_limit: int | None = None) -> dict[str, Any]:
        """Convert the group into a serialisable structure."""
        limit = example_limit if example_limit is not None else len(self.examples)
        limited_examples = [example.to_example() for example in self.examples[:limit]]
        return {
            "pattern": self.pattern,
            "error_type": self.error_type,
            "count": self.count,
            "severity": self.highest_severity,
            "examples": limited_examples,
            "affected_modules": sorted(self.affected_modules),
        }


class IncrementalAnalyzer:
    """Analyse deltas between pytest runs without retaining heavy state."""

    __slots__ = ()

    def analyze_delta(
        self,
        current_results: dict[str, Any],
        previous_results: dict[str, Any] | None = None,
    ) -> DeltaAnalysis:
        current_map = self._build_outcome_map(current_results)
        previous_map = self._build_outcome_map(previous_results)

        current_failed = {node for node, outcome in current_map.items() if self._is_failure(outcome)}
        previous_failed = {node for node, outcome in previous_map.items() if self._is_failure(outcome)}

        previous_nodes = set(previous_map)
        newly_failed = sorted(
            node for node in current_failed if node not in previous_nodes
        )
        still_failing = sorted(current_failed & previous_failed)
        newly_passed = sorted(node for node in previous_failed if node not in current_failed)
        regressions = sorted(
            node
            for node in current_failed
            if node in previous_map and not self._is_failure(previous_map[node])
        )

        improvement_rate = self._calculate_improvement_rate(previous_failed, still_failing)

        return DeltaAnalysis(
            newly_failed=newly_failed,
            newly_passed=newly_passed,
            still_failing=still_failing,
            regressions=regressions,
            improvement_rate=improvement_rate,
        )

    @staticmethod
    def _build_outcome_map(results: dict[str, Any] | None) -> dict[str, str]:
        if not results:
            return {}
        outcome_map: dict[str, str] = {}
        for test in results.get("tests", []):
            nodeid = test.get("nodeid")
            if not nodeid:
                continue
            outcome_map[nodeid] = test.get("outcome", "unknown").lower()
        return outcome_map

    @staticmethod
    def _is_failure(outcome: str | None) -> bool:
        return (outcome or "").lower() in {"failed", "error"}

    @staticmethod
    def _calculate_improvement_rate(previous_failed: set[str], still_failing: list[str]) -> float:
        if not previous_failed:
            return 0.0
        denominator = len(previous_failed)
        improved = denominator - len(still_failing)
        rate = (improved / denominator) * 100 if denominator else 0.0
        return max(0.0, min(100.0, rate))


class ErrorGrouper:
    """Group similar test errors to shrink downstream payloads."""

    __slots__ = ()

    _SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    def group_similar_errors(self, errors: Sequence[TestError]) -> list[ErrorGroup]:
        if not errors:
            return []

        buckets: dict[tuple[str, str], dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "examples": [],
                "modules": set(),
                "highest_severity": "low",
            }
        )

        for error in errors:
            pattern = self._normalise_message(error.message)
            key = (error.error_type, pattern)
            bucket = buckets[key]
            bucket["count"] += 1
            if len(bucket["examples"]) < 3:
                bucket["examples"].append(error)
            bucket["modules"].add(error.module)
            if self._SEVERITY_ORDER.get(error.severity, 3) < self._SEVERITY_ORDER.get(bucket["highest_severity"], 3):
                bucket["highest_severity"] = error.severity

        groups: list[ErrorGroup] = []
        for (error_type, pattern), bucket in buckets.items():
            groups.append(
                ErrorGroup(
                    pattern=pattern,
                    error_type=error_type,
                    count=bucket["count"],
                    examples=bucket["examples"],
                    affected_modules=bucket["modules"],
                    highest_severity=bucket["highest_severity"],
                )
            )

        groups.sort(key=lambda grp: (-grp.count, grp.pattern))
        return groups

    @staticmethod
    def _normalise_message(message: str | None) -> str:
        if not message:
            return "unknown"
        first_line = message.splitlines()[0].strip().lower()
        first_line = re.sub(r"https?://\S+", "<url>", first_line)
        first_line = re.sub(r"'[^']+'", "<str>", first_line)
        first_line = re.sub(r'"[^"]+"', "<str>", first_line)
        first_line = re.sub(r"\d+", "<num>", first_line)
        return first_line


class HierarchicalContext:
    """Build hierarchical context payloads for the MCP response."""

    __slots__ = ()

    def build_context(
        self,
        issues: Sequence[ToolIssue],
        *,
        detail_level: int = 1,
        summary: dict[str, Any] | None = None,
        delta: DeltaAnalysis | None = None,
        error_groups: Sequence[ErrorGroup] | None = None,
    ) -> dict[str, Any]:
        level = self._clamp_level(detail_level)
        context: dict[str, Any] = {
            "detail_level": level,
            "total_issues": len(issues),
            "severity_breakdown": self._count_by_severity(issues),
        }

        if summary:
            context["summary"] = self._select_summary_fields(summary)

        if delta:
            context["delta"] = delta.to_metadata(compact=level == 1)

        if level >= 2:
            context["high_priority_issues"] = self._extract_high_priority(issues)
            if error_groups:
                context["top_error_groups"] = [
                    group.to_metadata(example_limit=2) for group in list(error_groups)[:3]
                ]

        if level >= 3:
            context["issues"] = [self._issue_to_dict(issue) for issue in issues]
            if error_groups:
                context["error_groups"] = [group.to_metadata() for group in error_groups]

        return context

    @staticmethod
    def _clamp_level(level: int | float | str) -> int:
        try:
            value = int(level)
        except (TypeError, ValueError):
            value = 1
        return max(1, min(3, value))

    @staticmethod
    def _count_by_severity(issues: Sequence[ToolIssue]) -> dict[str, int]:
        counter = Counter(issue.severity for issue in issues)
        return dict(counter)

    @staticmethod
    def _select_summary_fields(summary: dict[str, Any]) -> dict[str, Any]:
        keys = ("total", "collected", "passed", "failed", "error", "skipped", "duration")
        return {key: summary[key] for key in keys if key in summary}

    @staticmethod
    def _extract_high_priority(issues: Sequence[ToolIssue]) -> list[dict[str, Any]]:
        high_priority = [issue for issue in issues if issue.severity in {"critical", "high"}]
        high_priority.sort(key=lambda item: item.severity)
        return [
            {
                "type": issue.type,
                "message": issue.message,
                "suggestion": issue.suggestion,
                "file_path": issue.file_path,
                "line_number": issue.line_number,
            }
            for issue in high_priority[:5]
        ]

    @staticmethod
    def _issue_to_dict(issue: ToolIssue) -> dict[str, Any]:
        return asdict(issue)


def build_test_error(nodeid: str, error_type: str, severity: str, message: str) -> TestError:
    """Factory helper to construct a :class:`TestError` instance."""
    module = nodeid.split("::", 1)[0] if nodeid else "unknown"
    return TestError(
        nodeid=nodeid,
        error_type=error_type,
        severity=severity,
        message=message or "",
        module=module,
    )
