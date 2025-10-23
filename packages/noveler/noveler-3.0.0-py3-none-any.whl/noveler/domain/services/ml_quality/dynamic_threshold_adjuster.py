# File: src/noveler/domain/services/ml_quality/dynamic_threshold_adjuster.py
# Purpose: Adjust quality thresholds based on historical feedback
# Context: Auto-tune gate_thresholds to minimize false positives/negatives

"""
Dynamic Threshold Adjuster Service.

This service adjusts quality thresholds based on historical feedback to
minimize false positives and false negatives while maintaining stability.

Responsibilities:
- Learn from past quality check results
- Auto-tune gate_thresholds using statistical methods
- Maintain threshold stability while adapting to project evolution
- Provide confidence intervals for adjustments

Architecture:
- Domain Service (pure business logic)
- Depends on IFeedbackRepository for historical data
- Returns AdjustedThresholds value objects

Contract: SPEC-QUALITY-140 §2.2.3
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger


class AdjustmentPolicy(Enum):
    """Threshold adjustment policy."""
    CONSERVATIVE = "conservative"  # Slow adaptation, high stability
    MODERATE = "moderate"          # Balanced adaptation
    AGGRESSIVE = "aggressive"      # Fast adaptation, lower stability


@dataclass(frozen=True)
class AdjustedThresholds:
    """
    Adjusted quality thresholds with confidence intervals.

    Fields:
        new_thresholds: Optimized threshold values per aspect
        confidence_intervals: (lower, upper) bounds for each threshold
        adjustment_rationale: Explanation for each change
        false_positive_rate_estimate: Estimated FP rate with new thresholds
        false_negative_rate_estimate: Estimated FN rate with new thresholds
        recommended_action: apply | review | keep_current

    Contract: SPEC-QUALITY-140 §2.2.3
    """
    new_thresholds: dict[str, float]
    confidence_intervals: dict[str, tuple[float, float]]
    adjustment_rationale: dict[str, str]
    false_positive_rate_estimate: float
    false_negative_rate_estimate: float
    recommended_action: str


class DynamicThresholdAdjuster:
    """
    Adjust quality thresholds based on historical feedback.

    Responsibilities:
    - Learn from past quality check results
    - Auto-tune gate_thresholds to minimize false positives/negatives
    - Maintain threshold stability while adapting to project evolution
    - Provide explainable threshold adjustments

    Dependencies (injected):
    - feedback_repository: IFeedbackRepository for historical feedback
    - logger: ILogger for diagnostics

    Contract: SPEC-QUALITY-140 §2.2.3
    """

    def __init__(
        self,
        feedback_repository: "IFeedbackRepository",
        logger: Optional[ILogger] = None
    ):
        """
        Initialize dynamic threshold adjuster.

        Args:
            feedback_repository: Repository for feedback history access
            logger: Optional logger (defaults to NullLogger)
        """
        self._feedback_repository = feedback_repository
        self._logger = logger or NullLogger()

    def adjust_thresholds(
        self,
        current_thresholds: dict[str, float],
        corpus_metrics: dict,
        project_root: Path,
        adjustment_policy: AdjustmentPolicy = AdjustmentPolicy.CONSERVATIVE,
        target_fp_rate: float = 0.05,
        target_fn_rate: float = 0.10
    ) -> dict:
        """
        Adjust thresholds based on feedback history and corpus baseline.

        Args:
            current_thresholds: Current gate thresholds from .novelerrc.yaml
            corpus_metrics: Baseline metrics from corpus analysis
            project_root: Project root for feedback lookup
            adjustment_policy: CONSERVATIVE (slow), MODERATE, or AGGRESSIVE (fast)
            target_fp_rate: Target false positive rate (default: 5%)
            target_fn_rate: Target false negative rate (default: 10%)

        Returns:
            Dictionary with:
            - aspect_name: {
                "current": float,
                "adjusted": float,
                "confidence_interval": [lower, upper],
                "rationale": str
              }
            - false_positive_rate_estimate: float
            - false_negative_rate_estimate: float
            - recommended_action: "apply" | "review" | "keep_current"

        Raises:
            ThresholdAdjustmentError: If adjustment fails

        Algorithm:
            1. Load feedback history (past 50-100 evaluations)
            2. Identify false positives (automated FAIL, manual PASS)
            3. Identify false negatives (automated PASS, manual FAIL)
            4. For each aspect:
               a. Compute optimal threshold using ROC curve analysis
               b. Apply adjustment policy (conservative dampening)
               c. Calculate confidence interval (bootstrap method)
               d. Generate rationale
            5. Estimate FP/FN rates with new thresholds
            6. Recommend action based on improvement delta

        Performance:
            - Target: ≤3 seconds for 50 feedback records

        Contract: SPEC-QUALITY-140 §4.3
        """
        self._logger.info(
            f"Adjusting thresholds with {adjustment_policy.value} policy",
            extra={
                "target_fp_rate": target_fp_rate,
                "target_fn_rate": target_fn_rate
            }
        )

        # Load feedback history
        feedback_history = self._feedback_repository.load_recent_feedback(
            project_root=project_root,
            limit=50
        )

        if not feedback_history:
            self._logger.warning("No feedback history available, using corpus baselines only")
            return self._adjust_from_corpus_only(current_thresholds, corpus_metrics)

        # Analyze false positives and false negatives
        fp_cases, fn_cases = self._identify_classification_errors(feedback_history)

        self._logger.info(
            f"Identified {len(fp_cases)} false positives, {len(fn_cases)} false negatives"
        )

        # Adjust each aspect threshold
        adjusted_thresholds = {}
        for aspect, current_value in current_thresholds.items():
            adjusted = self._adjust_aspect_threshold(
                aspect=aspect,
                current_threshold=current_value,
                feedback_history=feedback_history,
                fp_cases=fp_cases,
                fn_cases=fn_cases,
                adjustment_policy=adjustment_policy
            )
            adjusted_thresholds[aspect] = adjusted

        # Estimate FP/FN rates with new thresholds
        new_fp_rate, new_fn_rate = self._estimate_error_rates(
            adjusted_thresholds=adjusted_thresholds,
            feedback_history=feedback_history
        )

        # Determine recommended action
        recommended_action = self._determine_action(
            current_fp_rate=self._estimate_current_fp_rate(feedback_history),
            current_fn_rate=self._estimate_current_fn_rate(feedback_history),
            new_fp_rate=new_fp_rate,
            new_fn_rate=new_fn_rate,
            target_fp_rate=target_fp_rate,
            target_fn_rate=target_fn_rate
        )

        self._logger.info(
            f"Threshold adjustment complete",
            extra={
                "new_fp_rate": new_fp_rate,
                "new_fn_rate": new_fn_rate,
                "recommended_action": recommended_action
            }
        )

        return {
            "thresholds": adjusted_thresholds,
            "false_positive_rate_estimate": new_fp_rate,
            "false_negative_rate_estimate": new_fn_rate,
            "recommended_action": recommended_action
        }

    def _adjust_from_corpus_only(
        self,
        current_thresholds: dict[str, float],
        corpus_metrics: dict
    ) -> dict:
        """
        Adjust thresholds using corpus baselines only (no feedback available).

        Strategy:
        - Use corpus percentiles as reference points
        - Conservative adjustment: move current threshold 10% toward corpus median
        """
        adjusted_thresholds = {}

        for aspect, current_value in current_thresholds.items():
            # Placeholder: minimal adjustment toward corpus baseline
            corpus_baseline = corpus_metrics.get(f"{aspect}_baseline", current_value)
            adjusted_value = current_value * 0.9 + corpus_baseline * 0.1

            adjusted_thresholds[aspect] = {
                "current": current_value,
                "adjusted": adjusted_value,
                "confidence_interval": [adjusted_value - 5, adjusted_value + 5],
                "rationale": "Corpus-based adjustment (no feedback history available)"
            }

        return {
            "thresholds": adjusted_thresholds,
            "false_positive_rate_estimate": 0.05,  # Unknown, use default
            "false_negative_rate_estimate": 0.10,
            "recommended_action": "review"
        }

    def _identify_classification_errors(
        self,
        feedback_history: list
    ) -> tuple[list, list]:
        """
        Identify false positive and false negative cases from feedback.

        Returns:
            (fp_cases, fn_cases) where each is a list of feedback records
        """
        fp_cases = []
        fn_cases = []

        for feedback in feedback_history:
            automated_pass = feedback.get("automated_outcome") == "PASS"
            manual_pass = feedback.get("manual_outcome") == "PASS"

            if not automated_pass and manual_pass:
                # Automated FAIL, Manual PASS → False Positive
                fp_cases.append(feedback)
            elif automated_pass and not manual_pass:
                # Automated PASS, Manual FAIL → False Negative
                fn_cases.append(feedback)

        return fp_cases, fn_cases

    def _adjust_aspect_threshold(
        self,
        aspect: str,
        current_threshold: float,
        feedback_history: list,
        fp_cases: list,
        fn_cases: list,
        adjustment_policy: AdjustmentPolicy
    ) -> dict:
        """
        Adjust threshold for a single aspect.

        Algorithm:
            1. Extract aspect scores from FP and FN cases
            2. Compute optimal threshold (minimize FP + FN)
            3. Apply dampening based on adjustment policy
            4. Calculate confidence interval
            5. Generate rationale
        """
        # TODO: Implement ROC curve analysis for optimal threshold
        # Placeholder: Simple heuristic adjustment

        # If many FP cases, raise threshold (be less strict)
        # If many FN cases, lower threshold (be more strict)
        fp_count_for_aspect = len([c for c in fp_cases if aspect in c.get("aspects", [])])
        fn_count_for_aspect = len([c for c in fn_cases if aspect in c.get("aspects", [])])

        adjustment_delta = 0.0
        if fp_count_for_aspect > fn_count_for_aspect:
            # Too many false positives → raise threshold
            adjustment_delta = 2.0 if adjustment_policy == AdjustmentPolicy.AGGRESSIVE else 1.0
        elif fn_count_for_aspect > fp_count_for_aspect:
            # Too many false negatives → lower threshold
            adjustment_delta = -2.0 if adjustment_policy == AdjustmentPolicy.AGGRESSIVE else -1.0

        adjusted_value = current_threshold + adjustment_delta
        adjusted_value = max(50.0, min(95.0, adjusted_value))  # Clamp to [50, 95]

        return {
            "current": current_threshold,
            "adjusted": adjusted_value,
            "confidence_interval": [adjusted_value - 3, adjusted_value + 3],
            "rationale": f"Adjusted based on {fp_count_for_aspect} FP and {fn_count_for_aspect} FN cases"
        }

    def _estimate_error_rates(
        self,
        adjusted_thresholds: dict,
        feedback_history: list
    ) -> tuple[float, float]:
        """
        Estimate FP and FN rates with new thresholds.

        Method: Replay feedback history with new thresholds
        """
        # TODO: Implement actual replay simulation
        # Placeholder: return conservative estimates
        return 0.05, 0.10

    def _estimate_current_fp_rate(self, feedback_history: list) -> float:
        """Estimate current false positive rate from feedback."""
        if not feedback_history:
            return 0.05
        fp_count = sum(
            1 for f in feedback_history
            if f.get("automated_outcome") == "FAIL" and f.get("manual_outcome") == "PASS"
        )
        return fp_count / len(feedback_history)

    def _estimate_current_fn_rate(self, feedback_history: list) -> float:
        """Estimate current false negative rate from feedback."""
        if not feedback_history:
            return 0.10
        fn_count = sum(
            1 for f in feedback_history
            if f.get("automated_outcome") == "PASS" and f.get("manual_outcome") == "FAIL"
        )
        return fn_count / len(feedback_history)

    def _determine_action(
        self,
        current_fp_rate: float,
        current_fn_rate: float,
        new_fp_rate: float,
        new_fn_rate: float,
        target_fp_rate: float,
        target_fn_rate: float
    ) -> str:
        """
        Determine recommended action based on improvement delta.

        Returns:
            "apply" - Both FP and FN rates improved significantly
            "review" - Mixed results, needs manual review
            "keep_current" - New thresholds are worse
        """
        fp_improvement = current_fp_rate - new_fp_rate
        fn_improvement = current_fn_rate - new_fn_rate

        if fp_improvement > 0.02 and fn_improvement > 0.02:
            return "apply"
        elif fp_improvement < -0.02 or fn_improvement < -0.02:
            return "keep_current"
        else:
            return "review"


# Type hints for forward references
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from noveler.domain.protocols.feedback_repository_protocol import IFeedbackRepository
