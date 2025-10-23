# File: tests/unit/domain/services/iteration/test_iteration_policy_service.py
# Purpose: Unit tests for IterationPolicyService
# Context: Tests iteration policy normalization and stop condition logic

import pytest
from noveler.domain.services.iteration import IterationPolicyService


# ============================================================================
# Unit Tests - normalize_policy
# ============================================================================


class TestNormalizePolicy:
    """Test normalize_policy() behavior."""

    def test_normalize_none_returns_defaults(self):
        """normalize_policy(None) should return default policy."""
        result = IterationPolicyService.normalize_policy(None)

        assert result == {
            "count": 1,
            "time_budget_s": None,
            "cost_budget": None,
            "until_pass": False,
            "min_improvement": 0.0,
            "dry_run": False,
        }

    def test_normalize_empty_dict_returns_defaults(self):
        """normalize_policy({}) should return defaults."""
        result = IterationPolicyService.normalize_policy({})

        assert result["count"] == 1
        assert result["until_pass"] is False
        assert result["dry_run"] is False

    def test_normalize_preserves_valid_values(self):
        """normalize_policy() should preserve valid values."""
        policy = {
            "count": 5,
            "time_budget_s": 300,
            "cost_budget": 100,
            "until_pass": True,
            "min_improvement": 5.0,
            "dry_run": True,
        }

        result = IterationPolicyService.normalize_policy(policy)

        assert result["count"] == 5
        assert result["time_budget_s"] == 300
        assert result["cost_budget"] == 100
        assert result["until_pass"] is True
        assert result["min_improvement"] == 5.0
        assert result["dry_run"] is True

    def test_normalize_coerces_count_to_min_1(self):
        """normalize_policy() should enforce count >= 1."""
        policy = {"count": 0}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["count"] == 1

        policy = {"count": -5}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["count"] == 1

    def test_normalize_coerces_invalid_count_to_1(self):
        """normalize_policy() should default invalid count to 1."""
        policy = {"count": "invalid"}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["count"] == 1

        policy = {"count": None}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["count"] == 1

    def test_normalize_coerces_boolean_flags(self):
        """normalize_policy() should coerce flags to bool."""
        policy = {"until_pass": 1, "dry_run": "yes"}
        result = IterationPolicyService.normalize_policy(policy)

        assert result["until_pass"] is True
        assert result["dry_run"] is True

        policy = {"until_pass": 0, "dry_run": ""}
        result = IterationPolicyService.normalize_policy(policy)

        assert result["until_pass"] is False
        assert result["dry_run"] is False

    def test_normalize_coerces_min_improvement_to_float(self):
        """normalize_policy() should coerce min_improvement to float."""
        policy = {"min_improvement": "5.5"}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["min_improvement"] == 5.5

        policy = {"min_improvement": 10}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["min_improvement"] == 10.0

    def test_normalize_handles_invalid_min_improvement(self):
        """normalize_policy() should default invalid min_improvement to 0.0."""
        policy = {"min_improvement": "invalid"}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["min_improvement"] == 0.0

        policy = {"min_improvement": None}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["min_improvement"] == 0.0

    def test_normalize_validates_time_budget_s(self):
        """normalize_policy() should validate time_budget_s >= 0 or None."""
        policy = {"time_budget_s": 300}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["time_budget_s"] == 300

        policy = {"time_budget_s": -10}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["time_budget_s"] == 0

        policy = {"time_budget_s": "invalid"}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["time_budget_s"] is None

    def test_normalize_validates_cost_budget(self):
        """normalize_policy() should validate cost_budget >= 0 or None."""
        policy = {"cost_budget": 100}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["cost_budget"] == 100

        policy = {"cost_budget": -50}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["cost_budget"] == 0

        policy = {"cost_budget": "invalid"}
        result = IterationPolicyService.normalize_policy(policy)
        assert result["cost_budget"] is None

    def test_normalize_ignores_unknown_keys(self):
        """normalize_policy() should preserve unknown keys."""
        policy = {"unknown_key": "value", "count": 3}
        result = IterationPolicyService.normalize_policy(policy)

        assert result["count"] == 3
        assert result["unknown_key"] == "value"


# ============================================================================
# Unit Tests - should_stop_iteration
# ============================================================================


class TestShouldStopIteration:
    """Test should_stop_iteration() behavior."""

    def test_empty_attempts_returns_false(self):
        """should_stop_iteration() with empty attempts should return (False, "")."""
        policy = {"until_pass": True}
        should_stop, reason = IterationPolicyService.should_stop_iteration(policy, [])

        assert should_stop is False
        assert reason == ""

    def test_until_pass_stops_when_no_issues(self):
        """should_stop_iteration() should stop when issues_found == 0 and until_pass=True."""
        policy = {"until_pass": True}
        attempts = [
            {"result": {"issues_found": 0, "overall_score": 85}},
        ]

        should_stop, reason = IterationPolicyService.should_stop_iteration(policy, attempts)

        assert should_stop is True
        assert reason == "until_pass"

    def test_until_pass_stops_when_score_high(self):
        """should_stop_iteration() should stop when score >= 95 and until_pass=True (fallback)."""
        policy = {"until_pass": True}
        attempts = [
            {"result": {"issues_found": None, "overall_score": 95}},
        ]

        should_stop, reason = IterationPolicyService.should_stop_iteration(policy, attempts)

        assert should_stop is True
        assert reason == "until_pass"

        # Edge case: score = 94.9 should not stop
        attempts = [
            {"result": {"issues_found": None, "overall_score": 94.9}},
        ]

        should_stop, reason = IterationPolicyService.should_stop_iteration(policy, attempts)

        assert should_stop is False
        assert reason == ""

    def test_until_pass_continues_when_issues_present(self):
        """should_stop_iteration() should continue when issues > 0 and until_pass=True."""
        policy = {"until_pass": True}
        attempts = [
            {"result": {"issues_found": 5, "overall_score": 70}},
        ]

        should_stop, reason = IterationPolicyService.should_stop_iteration(policy, attempts)

        assert should_stop is False
        assert reason == ""

    def test_min_improvement_stops_when_below_threshold(self):
        """should_stop_iteration() should stop when improvement < min_improvement."""
        policy = {"min_improvement": 5.0}
        attempts = [
            {"result": {"overall_score": 70}},
            {"result": {"overall_score": 73}},  # +3 < 5.0
        ]

        should_stop, reason = IterationPolicyService.should_stop_iteration(policy, attempts)

        assert should_stop is True
        assert reason == "min_improvement"

    def test_min_improvement_continues_when_above_threshold(self):
        """should_stop_iteration() should continue when improvement >= min_improvement."""
        policy = {"min_improvement": 5.0}
        attempts = [
            {"result": {"overall_score": 70}},
            {"result": {"overall_score": 80}},  # +10 >= 5.0
        ]

        should_stop, reason = IterationPolicyService.should_stop_iteration(policy, attempts)

        assert should_stop is False
        assert reason == ""

    def test_min_improvement_requires_two_attempts(self):
        """should_stop_iteration() should ignore min_improvement with < 2 attempts."""
        policy = {"min_improvement": 5.0}
        attempts = [
            {"result": {"overall_score": 70}},
        ]

        should_stop, reason = IterationPolicyService.should_stop_iteration(policy, attempts)

        assert should_stop is False
        assert reason == ""

    def test_min_improvement_handles_none_scores(self):
        """should_stop_iteration() should handle None scores gracefully."""
        policy = {"min_improvement": 5.0}
        attempts = [
            {"result": {"overall_score": None}},
            {"result": {"overall_score": 80}},
        ]

        should_stop, reason = IterationPolicyService.should_stop_iteration(policy, attempts)

        assert should_stop is False
        assert reason == ""

    def test_no_policy_conditions_returns_false(self):
        """should_stop_iteration() should return (False, "") when no conditions met."""
        policy = {"until_pass": False, "min_improvement": 0.0}
        attempts = [
            {"result": {"issues_found": 5, "overall_score": 70}},
            {"result": {"issues_found": 3, "overall_score": 75}},
        ]

        should_stop, reason = IterationPolicyService.should_stop_iteration(policy, attempts)

        assert should_stop is False
        assert reason == ""

    def test_until_pass_takes_precedence(self):
        """should_stop_iteration() should check until_pass before min_improvement."""
        policy = {"until_pass": True, "min_improvement": 5.0}
        attempts = [
            {"result": {"issues_found": 0, "overall_score": 70}},
        ]

        should_stop, reason = IterationPolicyService.should_stop_iteration(policy, attempts)

        assert should_stop is True
        assert reason == "until_pass"


# ============================================================================
# Integration Tests
# ============================================================================


class TestIterationPolicyServiceIntegration:
    """Integration tests for complete workflow."""

    def test_full_workflow_with_normalized_policy(self):
        """Test normalize + should_stop workflow."""
        # Normalize policy
        raw_policy = {
            "count": "3",
            "until_pass": 1,
            "min_improvement": "2.5",
        }

        normalized = IterationPolicyService.normalize_policy(raw_policy)

        assert normalized["count"] == 3
        assert normalized["until_pass"] is True
        assert normalized["min_improvement"] == 2.5

        # Check stop condition (until_pass)
        attempts = [
            {"result": {"issues_found": 0}},
        ]

        should_stop, reason = IterationPolicyService.should_stop_iteration(normalized, attempts)

        assert should_stop is True
        assert reason == "until_pass"

    def test_iteration_continues_until_min_improvement_threshold(self):
        """Test multiple iterations with min_improvement policy."""
        policy = IterationPolicyService.normalize_policy({"min_improvement": 3.0})

        # Attempt 1: No stop (single attempt)
        attempts = [{"result": {"overall_score": 70}}]
        should_stop, _ = IterationPolicyService.should_stop_iteration(policy, attempts)
        assert should_stop is False

        # Attempt 2: +5 improvement (continue)
        attempts.append({"result": {"overall_score": 75}})
        should_stop, _ = IterationPolicyService.should_stop_iteration(policy, attempts)
        assert should_stop is False

        # Attempt 3: +2 improvement (stop, below 3.0 threshold)
        attempts.append({"result": {"overall_score": 77}})
        should_stop, reason = IterationPolicyService.should_stop_iteration(policy, attempts)
        assert should_stop is True
        assert reason == "min_improvement"
