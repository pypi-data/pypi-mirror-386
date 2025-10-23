# File: src/noveler/domain/services/ml_quality/severity_estimator.py
# Purpose: Estimate issue severity based on position, frequency, and context
# Context: Provide context-aware severity adjustments for quality issues

"""
Severity Estimator Service.

This service estimates issue severity based on position within the manuscript,
frequency of similar issues, and narrative context.

Responsibilities:
- Compute position-weighted severity (opening/climax have higher impact)
- Aggregate frequency-based penalties
- Adjust severity based on narrative structure
- Provide explainable severity adjustments

Architecture:
- Domain Service (pure business logic)
- No external dependencies (stateless computation)
- Returns SeverityEstimate value objects

Contract: SPEC-QUALITY-140 §2.2.5
"""

from dataclasses import dataclass
from typing import Optional

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger


@dataclass(frozen=True)
class SeverityEstimate:
    """
    Issue severity estimate with context awareness.

    Fields:
        base_severity: Original severity from detector (1.0-3.0)
        position_multiplier: Impact based on location (1.0-2.0)
        frequency_penalty: Aggregated penalty for repeated violations (1.0-2.0)
        adjusted_severity: Final severity score (base × position × frequency)
        explanation: Human-readable reasoning

    Contract: SPEC-QUALITY-140 §2.2.5
    """
    base_severity: float
    position_multiplier: float
    frequency_penalty: float
    adjusted_severity: float
    explanation: str
    issue_id: str
    line_number: int


class SeverityEstimator:
    """
    Estimate issue severity based on position, frequency, and context.

    Responsibilities:
    - Compute position-weighted severity (opening/climax have higher impact)
    - Aggregate frequency-based penalties for repeated violations
    - Adjust severity based on narrative structure
    - Provide explainable severity adjustments

    Dependencies (injected):
    - logger: ILogger for diagnostics

    Contract: SPEC-QUALITY-140 §2.2.5
    """

    # Position multipliers by manuscript region
    POSITION_MULTIPLIERS = {
        "opening": 1.5,      # First 10%
        "climax": 1.8,       # 80-90%
        "ending": 2.0,       # Last 5%
        "middle": 1.0        # Default
    }

    def __init__(
        self,
        logger: Optional[ILogger] = None
    ):
        """
        Initialize severity estimator.

        Args:
            logger: Optional logger (defaults to NullLogger)
        """
        self._logger = logger or NullLogger()

    def estimate_severity(
        self,
        issue: dict,
        manuscript: str,
        total_lines: int
    ) -> dict:
        """
        Estimate issue severity with context awareness.

        Args:
            issue: Quality issue dict with:
                - issue_id: Unique identifier
                - line_number: Line where issue occurs
                - severity: Base severity (low=1.0, medium=2.0, high=3.0)
                - reason_code: Issue type identifier
            manuscript: Full manuscript text (for context analysis)
            total_lines: Total number of lines in manuscript

        Returns:
            Dictionary with:
            - issue_id: str
            - base_severity: float
            - position_multiplier: float (1.0-2.0)
            - frequency_penalty: float (1.0-2.0)
            - adjusted_severity: float
            - explanation: str

        Algorithm:
            1. Determine manuscript region (opening/middle/climax/ending)
            2. Apply position multiplier
            3. Count similar issues (same reason_code)
            4. Apply frequency penalty: min(1.0 + (count * 0.1), 2.0)
            5. Calculate final severity: base × position × frequency
            6. Generate explanation

        Performance:
            - Target: ≤100ms per issue

        Contract: SPEC-QUALITY-140 §4.4
        """
        issue_id = issue.get("issue_id", "unknown")
        line_number = issue.get("line_number", 0)
        base_severity = self._parse_base_severity(issue.get("severity", "medium"))
        reason_code = issue.get("reason_code", "UNKNOWN")

        # Step 1: Determine position multiplier
        position_pct = line_number / total_lines if total_lines > 0 else 0.5
        region = self._determine_region(position_pct)
        position_multiplier = self.POSITION_MULTIPLIERS.get(region, 1.0)

        # Step 2: Calculate frequency penalty
        similar_count = self._count_similar_issues(
            reason_code=reason_code,
            manuscript=manuscript
        )
        frequency_penalty = min(1.0 + (similar_count * 0.1), 2.0)

        # Step 3: Calculate adjusted severity
        adjusted_severity = base_severity * position_multiplier * frequency_penalty

        # Step 4: Generate explanation
        explanation = self._generate_explanation(
            region=region,
            similar_count=similar_count,
            position_multiplier=position_multiplier,
            frequency_penalty=frequency_penalty
        )

        self._logger.debug(
            f"Estimated severity for {issue_id}",
            extra={
                "base": base_severity,
                "adjusted": adjusted_severity,
                "region": region
            }
        )

        return {
            "issue_id": issue_id,
            "line_number": line_number,
            "base_severity": base_severity,
            "position_multiplier": position_multiplier,
            "frequency_penalty": frequency_penalty,
            "adjusted_severity": adjusted_severity,
            "explanation": explanation
        }

    def _parse_base_severity(self, severity: str) -> float:
        """
        Parse severity string to numeric value.

        Mapping:
            low → 1.0
            medium → 2.0
            high → 3.0
        """
        severity_map = {
            "low": 1.0,
            "medium": 2.0,
            "high": 3.0
        }
        return severity_map.get(severity.lower(), 2.0)

    def _determine_region(self, position_pct: float) -> str:
        """
        Determine manuscript region based on position percentage.

        Regions:
            0-10%: opening
            80-90%: climax
            95-100%: ending
            else: middle
        """
        if position_pct < 0.1:
            return "opening"
        elif 0.8 <= position_pct < 0.9:
            return "climax"
        elif position_pct >= 0.95:
            return "ending"
        else:
            return "middle"

    def _count_similar_issues(
        self,
        reason_code: str,
        manuscript: str
    ) -> int:
        """
        Count occurrences of similar issues in manuscript.

        This is a placeholder implementation. In production, this should:
        - Accept a full issue list from quality checker
        - Count issues with matching reason_code
        - Consider issue proximity (clustering)
        """
        # Placeholder: estimate based on manuscript length
        # TODO: Integrate with actual issue list
        return 0

    def _generate_explanation(
        self,
        region: str,
        similar_count: int,
        position_multiplier: float,
        frequency_penalty: float
    ) -> str:
        """Generate human-readable severity explanation."""
        parts = []

        if position_multiplier > 1.0:
            parts.append(f"Issue in {region} region (×{position_multiplier:.1f} impact)")

        if frequency_penalty > 1.0:
            parts.append(f"{similar_count} similar issues (×{frequency_penalty:.1f} penalty)")

        if not parts:
            return "Standard severity (no adjustments)"

        return "; ".join(parts)
