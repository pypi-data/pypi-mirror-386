# File: src/noveler/domain/services/iteration/iteration_policy_service.py
# Purpose: Iteration policy validation and stop condition evaluation
# Context: Extracted from ProgressiveCheckManager._normalize_iteration_policy/_should_stop_iteration

from typing import Any


class IterationPolicyService:
    """Iteration policy management (Domain layer - no I/O).

    Responsibilities:
    - Normalize iteration policy dictionaries
    - Evaluate stop conditions based on policy
    - Determine if iteration should continue

    Extracted from:
    - ProgressiveCheckManager._normalize_iteration_policy (lines 634-669)
    - ProgressiveCheckManager._should_stop_iteration (lines 671-694)
    """

    @staticmethod
    def normalize_policy(policy: dict[str, Any] | None) -> dict[str, Any]:
        """Normalize iteration policy with defaults and validation.

        Args:
            policy: Raw policy dict or None

        Returns:
            Normalized policy with validated types and defaults

        Policy fields:
            - count: Number of iterations (min 1)
            - time_budget_s: Time budget in seconds (None or >= 0)
            - cost_budget: Cost budget (None or >= 0)
            - until_pass: Stop when no issues found
            - min_improvement: Minimum score improvement to continue
            - dry_run: Dry run mode flag
        """
        defaults: dict[str, Any] = {
            "count": 1,
            "time_budget_s": None,
            "cost_budget": None,
            "until_pass": False,
            "min_improvement": 0.0,
            "dry_run": False,
        }

        if not policy:
            return defaults.copy()

        normalized = defaults.copy()
        for key, value in policy.items():
            normalized[key] = value

        # Validate and coerce count (min 1)
        try:
            normalized["count"] = max(1, int(normalized.get("count", 1)))
        except (TypeError, ValueError):
            normalized["count"] = 1

        # Coerce boolean flags
        normalized["dry_run"] = bool(normalized.get("dry_run"))
        normalized["until_pass"] = bool(normalized.get("until_pass"))

        # Validate min_improvement (float >= 0)
        try:
            normalized["min_improvement"] = float(normalized.get("min_improvement") or 0.0)
        except (TypeError, ValueError):
            normalized["min_improvement"] = 0.0

        # Validate time_budget_s (None or >= 0)
        if normalized.get("time_budget_s") is not None:
            try:
                normalized["time_budget_s"] = max(0, int(normalized["time_budget_s"]))
            except (TypeError, ValueError):
                normalized["time_budget_s"] = None

        # Validate cost_budget (None or >= 0)
        if normalized.get("cost_budget") is not None:
            try:
                normalized["cost_budget"] = max(0, int(normalized["cost_budget"]))
            except (TypeError, ValueError):
                normalized["cost_budget"] = None

        return normalized

    @staticmethod
    def should_stop_iteration(
        policy: dict[str, Any],
        attempts: list[dict[str, Any]],
    ) -> tuple[bool, str]:
        """Determine if iteration should stop based on policy and attempts.

        Args:
            policy: Normalized iteration policy
            attempts: List of attempt records with "result" field

        Returns:
            (should_stop, reason) tuple
            - should_stop: True if iteration should stop
            - reason: Stop reason string ("until_pass", "min_improvement", or "")

        Stop conditions:
            1. until_pass: No issues found (issues_found == 0 or score >= 95)
            2. min_improvement: Score improvement below threshold

        Edge cases:
            - Empty attempts: (False, "")
            - Single attempt: min_improvement check skipped
        """
        if not attempts:
            return False, ""

        latest_result = attempts[-1]["result"]

        # Check until_pass condition
        if policy.get("until_pass"):
            issues = latest_result.get("issues_found")
            if issues == 0:
                return True, "until_pass"

            # Fallback: high score (>= 95) when issues_found is None
            score = latest_result.get("overall_score")
            if issues is None and isinstance(score, (int, float)) and score >= 95:
                return True, "until_pass"

        # Check min_improvement condition (requires >= 2 attempts)
        min_improvement = float(policy.get("min_improvement") or 0.0)
        if min_improvement > 0 and len(attempts) >= 2:
            prev_score = attempts[-2]["result"].get("overall_score")
            new_score = latest_result.get("overall_score")

            if isinstance(prev_score, (int, float)) and isinstance(new_score, (int, float)):
                if (new_score - prev_score) < min_improvement:
                    return True, "min_improvement"

        return False, ""
