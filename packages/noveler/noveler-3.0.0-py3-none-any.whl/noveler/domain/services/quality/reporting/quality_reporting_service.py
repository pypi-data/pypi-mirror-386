# File: src/noveler/domain/services/quality/reporting/quality_reporting_service.py
# Purpose: Generate quality check reports in various formats
# Context: Unified reporting for all quality check results

from typing import Dict, List, Optional
import json
from src.noveler.domain.services.quality.value_objects.quality_value_objects import (
    QualityCheckResult,
    QualityIssue
)


class QualityReportingService:
    """Service for generating quality reports"""

    def generate_report(
        self,
        result: QualityCheckResult,
        format: str = 'summary'
    ) -> str:
        """Generate report in specified format"""
        if format == 'summary':
            return self._generate_summary_report(result)
        elif format == 'json':
            return self._generate_json_report(result)
        elif format == 'detailed':
            return self._generate_detailed_report(result)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_summary_report(self, result: QualityCheckResult) -> str:
        """Generate summary report"""
        lines = []
        lines.append(f"Overall Score: {result.overall_score:.1f}/100")
        lines.append("\nAspect Scores:")

        for aspect, score in result.aspect_scores.items():
            lines.append(f"  {aspect}: {score:.1f}")

        if result.issues:
            lines.append(f"\nTotal Issues: {len(result.issues)}")
            severity_counts = self._count_by_severity(result.issues)
            for severity, count in severity_counts.items():
                if count > 0:
                    lines.append(f"  {severity}: {count}")

        return '\n'.join(lines)

    def _generate_json_report(self, result: QualityCheckResult) -> str:
        """Generate JSON report"""
        report_data = {
            'overall_score': result.overall_score,
            'aspect_scores': result.aspect_scores,
            'total_issues': len(result.issues),
            'issues': [
                {
                    'aspect': issue.aspect,
                    'severity': issue.severity.value,
                    'line_number': issue.line_number,
                    'description': issue.description,
                    'suggestion': issue.suggestion,
                    'reason_code': issue.reason_code
                }
                for issue in result.issues
            ]
        }
        return json.dumps(report_data, ensure_ascii=False, indent=2)

    def _generate_detailed_report(self, result: QualityCheckResult) -> str:
        """Generate detailed report"""
        lines = []
        lines.append("=" * 60)
        lines.append("Quality Check Detailed Report")
        lines.append("=" * 60)

        lines.append(f"\nOverall Score: {result.overall_score:.1f}/100")
        lines.append("\nAspect Breakdown:")

        for aspect, score in result.aspect_scores.items():
            lines.append(f"\n{aspect.upper()}: {score:.1f}/100")
            aspect_issues = [i for i in result.issues if i.aspect == aspect]

            if aspect_issues:
                lines.append(f"  Issues found: {len(aspect_issues)}")
                for issue in aspect_issues[:5]:  # Show first 5 issues
                    if issue.line_number:
                        lines.append(f"    Line {issue.line_number}: {issue.description}")
                    else:
                        lines.append(f"    {issue.description}")

        lines.append("\n" + "=" * 60)
        return '\n'.join(lines)

    def _count_by_severity(self, issues: List[QualityIssue]) -> Dict[str, int]:
        """Count issues by severity"""
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for issue in issues:
            counts[issue.severity.value] += 1
        return counts