#!/usr/bin/env python3
"""
Quality Reporting Service - Pure Domain Service

Responsible for generating quality reports, suggestions, and result formatting.
"""

from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.domain.value_objects.quality_types import (
    QualityCheckResult,
    QualityCheckType,
    QualityIssue,
    QualityScore,
    QualitySeverity,
)


class QualityReportingService:
    """
    Domain service for quality reporting and result management

    Responsibilities:
    - Generate comprehensive quality reports
    - Create improvement suggestions
    - Format results for different audiences
    - Calculate overall quality grades
    - Manage quality result persistence
    """

    def __init__(self) -> None:
        """Initialize quality reporting service"""
        self._grade_thresholds = self._load_grade_thresholds()
        self._suggestion_templates = self._load_suggestion_templates()

    def generate_quality_report(
        self,
        scores: list[QualityScore],
        check_type: QualityCheckType,
        project_name: str,
        episode_number: int | None = None,
        execution_time: float | None = None,
    ) -> QualityCheckResult:
        """Generate comprehensive quality report

        Args:
            scores: List of quality scores
            check_type: Type of quality check performed
            project_name: Project identifier
            episode_number: Episode number
            execution_time: Check execution time

        Returns:
            QualityCheckResult: Complete quality check result
        """
        # Calculate totals
        total_score = sum(score.score for score in scores)
        max_total_score = sum(score.max_score for score in scores)
        overall_percentage = (total_score / max_total_score * 100) if max_total_score > 0 else 0

        # Collect all issues
        all_issues = []
        for score in scores:
            all_issues.extend(score.issues)

        # Generate grade
        grade = self.determine_quality_grade(overall_percentage)

        # Generate suggestions
        suggestions = self.generate_improvement_suggestions(all_issues, check_type, overall_percentage)

        return QualityCheckResult(
            success=True,
            check_type=check_type,
            total_score=total_score,
            max_total_score=max_total_score,
            overall_percentage=overall_percentage,
            grade=grade,
            scores=scores,
            all_issues=all_issues,
            suggestions=suggestions,
            execution_time=execution_time,
            check_timestamp=project_now().datetime,
        )

    def determine_quality_grade(self, percentage: float) -> str:
        """Determine quality grade based on score percentage

        Args:
            percentage: Overall quality percentage

        Returns:
            str: Quality grade (A+, A, B+, etc.)
        """
        for grade, threshold in self._grade_thresholds.items():
            if percentage >= threshold:
                return grade

        return "F"  # Fallback grade

    def generate_improvement_suggestions(
        self, issues: list[QualityIssue], check_type: QualityCheckType, overall_percentage: float
    ) -> list[str]:
        """Generate improvement suggestions based on issues and context

        Args:
            issues: List of quality issues
            check_type: Type of quality check
            overall_percentage: Overall quality percentage

        Returns:
            list[str]: Generated improvement suggestions
        """
        suggestions = []

        # Priority-based suggestions
        critical_issues = [issue for issue in issues if issue.severity == QualitySeverity.CRITICAL]
        error_issues = [issue for issue in issues if issue.severity == QualitySeverity.ERROR]
        warning_issues = [issue for issue in issues if issue.severity == QualitySeverity.WARNING]

        # Critical issues first
        if critical_issues:
            suggestions.append("Critical issues require immediate attention")
            for issue in critical_issues[:3]:  # Top 3 critical issues
                if issue.suggestion:
                    suggestions.append(f"CRITICAL: {issue.suggestion}")

        # Error issues
        if error_issues:
            suggestions.append("Error-level issues need correction")
            for issue in error_issues[:3]:  # Top 3 errors
                if issue.suggestion:
                    suggestions.append(f"ERROR: {issue.suggestion}")

        # Warning issues (if not too many higher priority issues)
        if len(suggestions) < 7 and warning_issues:
            for issue in warning_issues[:2]:  # Top 2 warnings
                if issue.suggestion:
                    suggestions.append(f"WARNING: {issue.suggestion}")

        # Check-type specific suggestions
        type_suggestions = self._generate_type_specific_suggestions(check_type, overall_percentage)
        suggestions.extend(type_suggestions)

        # Overall quality suggestions
        if overall_percentage < 60:
            suggestions.extend(self._suggestion_templates["low_quality"])
        elif overall_percentage < 80:
            suggestions.extend(self._suggestion_templates["medium_quality"])
        else:
            suggestions.extend(self._suggestion_templates["high_quality"])

        return suggestions[:10]  # Limit to 10 suggestions

    def format_quality_summary(self, result: QualityCheckResult) -> str:
        """Format quality result as human-readable summary

        Args:
            result: Quality check result

        Returns:
            str: Formatted summary
        """
        summary_lines = []

        # Header
        summary_lines.append(f"Quality Check Summary - {result.check_type.value.title()}")
        summary_lines.append("=" * 50)

        # Overall results
        summary_lines.append(f"Overall Score: {result.total_score:.1f}/{result.max_total_score:.1f}")
        summary_lines.append(f"Percentage: {result.overall_percentage:.1f}%")
        summary_lines.append(f"Grade: {result.grade}")

        if result.execution_time:
            summary_lines.append(f"Execution Time: {result.execution_time:.3f}s")

        # Category breakdown
        if result.scores:
            summary_lines.append("\nCategory Breakdown:")
            summary_lines.append("-" * 30)
            for score in result.scores:
                summary_lines.append(
                    f"{score.category}: {score.score:.1f}/{score.max_score:.1f} ({score.percentage:.1f}%)"
                )

        # Issues summary
        if result.all_issues:
            issue_counts = self._count_issues_by_severity(result.all_issues)
            summary_lines.append("\nIssues Found:")
            summary_lines.append("-" * 20)
            for severity, count in issue_counts.items():
                if count > 0:
                    summary_lines.append(f"{severity.value.title()}: {count}")

        # Top suggestions
        if result.suggestions:
            summary_lines.append("\nTop Recommendations:")
            summary_lines.append("-" * 25)
            for i, suggestion in enumerate(result.suggestions[:5], 1):
                summary_lines.append(f"{i}. {suggestion}")

        return "\n".join(summary_lines)

    def create_detailed_report(self, result: QualityCheckResult) -> dict[str, Any]:
        """Create detailed quality report data structure

        Args:
            result: Quality check result

        Returns:
            Dict[str, Any]: Detailed report data
        """
        return {
            "summary": {
                "check_type": result.check_type.value,
                "total_score": result.total_score,
                "max_total_score": result.max_total_score,
                "overall_percentage": result.overall_percentage,
                "grade": result.grade,
                "execution_time": result.execution_time,
                "timestamp": result.check_timestamp.isoformat() if result.check_timestamp else None,
            },
            "category_scores": [
                {
                    "category": score.category,
                    "score": score.score,
                    "max_score": score.max_score,
                    "percentage": score.percentage,
                    "issue_count": len(score.issues),
                }
                for score in result.scores
            ],
            "issues": {
                "total_count": len(result.all_issues),
                "by_severity": self._count_issues_by_severity(result.all_issues),
                "by_type": self._count_issues_by_type(result.all_issues),
                "detailed_issues": [
                    {
                        "type": issue.type,
                        "severity": issue.severity.value,
                        "message": issue.message,
                        "suggestion": issue.suggestion,
                        "location": issue.location,
                    }
                    for issue in result.all_issues
                ],
            },
            "suggestions": {"count": len(result.suggestions), "recommendations": result.suggestions},
        }

    def generate_a31_specific_suggestions(self, issues: list[QualityIssue]) -> list[str]:
        """Generate A31 manuscript checklist specific suggestions

        Args:
            issues: List of quality issues

        Returns:
            list[str]: A31-specific suggestions
        """
        suggestions = [
            "A31 manuscript execution checklist evaluation completed",
            "Detailed feedback available in individual item assessments",
        ]

        # Critical A31 issues
        critical_issues = [issue for issue in issues if issue.severity == QualitySeverity.CRITICAL]
        if critical_issues:
            suggestions.append("URGENT: Critical A31 checklist items require immediate attention")
            for issue in critical_issues[:3]:
                if issue.suggestion:
                    suggestions.append(f"Critical: {issue.suggestion}")

        # Standard A31 improvement areas
        error_issues = [issue for issue in issues if issue.severity == QualitySeverity.ERROR]
        if error_issues:
            suggestions.append("Important A31 improvements needed:")
            for issue in error_issues[:3]:
                if issue.suggestion:
                    suggestions.append(f"Important: {issue.suggestion}")

        return suggestions

    def calculate_quality_trends(
        self, current_result: QualityCheckResult, historical_results: list[QualityCheckResult]
    ) -> dict[str, Any]:
        """Calculate quality trends based on historical data

        Args:
            current_result: Current quality result
            historical_results: Previous quality results

        Returns:
            Dict[str, Any]: Quality trend analysis
        """
        if not historical_results:
            return {"trend": "no_data", "message": "No historical data available"}

        # Calculate trend
        recent_scores = [result.overall_percentage for result in historical_results[-5:]]
        current_score = current_result.overall_percentage

        if len(recent_scores) >= 2:
            avg_recent = sum(recent_scores) / len(recent_scores)
            if current_score > avg_recent + 5:
                trend = "improving"
            elif current_score < avg_recent - 5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "trend": trend,
            "current_score": current_score,
            "average_recent": sum(recent_scores) / len(recent_scores) if recent_scores else 0,
            "historical_count": len(historical_results),
            "message": self._get_trend_message(trend),
        }

    def _generate_type_specific_suggestions(self, check_type: QualityCheckType, overall_percentage: float) -> list[str]:
        """Generate suggestions specific to check type

        Args:
            check_type: Type of quality check
            overall_percentage: Overall quality percentage

        Returns:
            list[str]: Type-specific suggestions
        """
        suggestions = []

        if check_type == QualityCheckType.COMPREHENSIVE:
            if overall_percentage < 75:
                suggestions.append("Focus on improving character development and narrative depth")
        elif check_type == QualityCheckType.ADAPTIVE:
            suggestions.append("Adaptive quality patterns are being learned for future improvements")
        elif check_type == QualityCheckType.VIEWPOINT_AWARE:
            suggestions.append("Viewpoint consistency has been evaluated against established patterns")
        elif check_type == QualityCheckType.A31_CHECKLIST:
            suggestions.extend(self._suggestion_templates["a31_specific"])

        return suggestions

    def _count_issues_by_severity(self, issues: list[QualityIssue]) -> dict[QualitySeverity, int]:
        """Count issues by severity level

        Args:
            issues: List of quality issues

        Returns:
            Dict[QualitySeverity, int]: Issue counts by severity
        """
        counts = dict.fromkeys(QualitySeverity, 0)
        for issue in issues:
            counts[issue.severity] += 1
        return counts

    def _count_issues_by_type(self, issues: list[QualityIssue]) -> dict[str, int]:
        """Count issues by type

        Args:
            issues: List of quality issues

        Returns:
            Dict[str, int]: Issue counts by type
        """
        counts = {}
        for issue in issues:
            counts[issue.type] = counts.get(issue.type, 0) + 1
        return counts

    def _get_trend_message(self, trend: str) -> str:
        """Get descriptive message for trend

        Args:
            trend: Trend type

        Returns:
            str: Trend description
        """
        messages: dict[str, Any] = {
            "improving": "Quality is improving compared to recent episodes",
            "declining": "Quality has declined compared to recent episodes",
            "stable": "Quality is consistent with recent episodes",
            "insufficient_data": "Not enough data to determine trend",
            "no_data": "No historical data available for comparison",
        }
        return messages.get(trend, "Unknown trend")

    def _load_grade_thresholds(self) -> dict[str, float]:
        """Load quality grade thresholds

        Returns:
            Dict[str, float]: Grade thresholds
        """
        return {"A+": 90.0, "A": 85.0, "B+": 80.0, "B": 75.0, "C+": 70.0, "C": 65.0, "D+": 60.0, "D": 55.0}

    def _load_suggestion_templates(self) -> dict[str, list[str]]:
        """Load suggestion templates

        Returns:
            Dict[str, list[str]]: Suggestion templates
        """
        return {
            "low_quality": [
                "Consider substantial revision focusing on core narrative elements",
                "Review basic writing fundamentals and story structure",
            ],
            "medium_quality": [
                "Focus on enhancing character development and emotional depth",
                "Consider improving dialogue balance and pacing",
            ],
            "high_quality": [
                "Fine-tune narrative elements for optimal impact",
                "Consider advanced techniques for enhanced reader engagement",
            ],
            "a31_specific": [
                "Refer to A31 manuscript execution checklist for detailed criteria",
                "Focus on opening appeal and character growth elements",
            ],
        }
