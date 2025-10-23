# File: tests/unit/domain/services/result/test_result_builder.py
# Purpose: Unit tests for ResultBuilder
# Context: Tests static result construction logic

import pytest
from noveler.domain.services.result import ResultBuilder


# ============================================================================
# Unit Tests - build_static_result
# ============================================================================


class TestBuildStaticResult:
    """Test build_static_result() behavior."""

    def test_build_basic_result(self):
        """build_static_result() should generate complete result structure."""
        task = {"id": 1, "name": "誤字脱字チェック"}

        result = ResultBuilder.build_static_result(task)

        assert result["step_id"] == 1
        assert result["step_name"] == "誤字脱字チェック"
        assert result["content"] == "誤字脱字チェックを実行しました"
        assert result["metadata"]["llm_used"] is False
        assert result["artifacts"] == []
        assert "overall_score" in result
        assert "quality_breakdown" in result
        assert "improvement_suggestions" in result

    def test_build_result_score_calculation(self):
        """build_static_result() should calculate deterministic scores."""
        # Step 1: base = 75 + (1 * 1.8) = 76.8
        task = {"id": 1, "name": "Step 1"}
        result = ResultBuilder.build_static_result(task)
        assert result["overall_score"] == 76.8

        # Step 5: base = 75 + (5 * 1.8) = 84.0
        task = {"id": 5, "name": "Step 5"}
        result = ResultBuilder.build_static_result(task)
        assert result["overall_score"] == 84.0

        # Step 10: base = 75 + (10 * 1.8) = 93.0
        task = {"id": 10, "name": "Step 10"}
        result = ResultBuilder.build_static_result(task)
        assert result["overall_score"] == 93.0

    def test_build_result_score_capped_at_96(self):
        """build_static_result() should cap overall_score at 96.0."""
        # Step 20: base = 75 + min(20 * 1.8, 18) = 75 + 18 = 93.0
        task = {"id": 20, "name": "Step 20"}
        result = ResultBuilder.build_static_result(task)
        assert result["overall_score"] == 93.0

        # Step 100: base = 75 + min(100 * 1.8, 18) = 75 + 18 = 93.0
        task = {"id": 100, "name": "Step 100"}
        result = ResultBuilder.build_static_result(task)
        assert result["overall_score"] == 93.0

        # Verify score never exceeds 96.0
        for step_id in [1, 5, 10, 20, 50, 100]:
            task = {"id": step_id, "name": f"Step {step_id}"}
            result = ResultBuilder.build_static_result(task)
            assert result["overall_score"] <= 96.0

    def test_build_result_quality_breakdown(self):
        """build_static_result() should generate quality breakdown."""
        task = {"id": 5, "name": "Step 5"}
        result = ResultBuilder.build_static_result(task)

        breakdown = result["quality_breakdown"]
        overall_score = result["overall_score"]

        # Clarity = overall_score
        assert breakdown["clarity"] == overall_score

        # Consistency = max(70, overall_score - 5)
        assert breakdown["consistency"] == max(70.0, overall_score - 5)

        # Readability = max(72, overall_score - 3)
        assert breakdown["readability"] == max(72.0, overall_score - 3)

    def test_build_result_quality_breakdown_floor_values(self):
        """build_static_result() should enforce floor values in breakdown."""
        # Step 0: overall_score = 75.0
        task = {"id": 0, "name": "Step 0"}
        result = ResultBuilder.build_static_result(task)

        breakdown = result["quality_breakdown"]

        assert breakdown["clarity"] == 75.0
        assert breakdown["consistency"] == 70.0  # 75 - 5 = 70 (floor)
        assert breakdown["readability"] == 72.0  # 75 - 3 = 72 (floor)

        # Step 1: overall_score = 76.8
        task = {"id": 1, "name": "Step 1"}
        result = ResultBuilder.build_static_result(task)

        breakdown = result["quality_breakdown"]

        assert breakdown["clarity"] == 76.8
        assert breakdown["consistency"] == 71.8  # 76.8 - 5
        assert breakdown["readability"] == 73.8  # 76.8 - 3

    def test_build_result_improvement_suggestions(self):
        """build_static_result() should include improvement suggestions."""
        task = {"id": 1, "name": "誤字脱字チェック"}
        result = ResultBuilder.build_static_result(task)

        suggestions = result["improvement_suggestions"]

        assert isinstance(suggestions, list)
        assert len(suggestions) == 1
        assert suggestions[0] == "誤字脱字チェックの改善提案"

    def test_build_result_handles_missing_id(self):
        """build_static_result() should handle missing id field."""
        task = {"name": "Some check"}
        result = ResultBuilder.build_static_result(task)

        assert result["step_id"] == 0
        assert result["overall_score"] == 75.0  # base score

    def test_build_result_handles_missing_name(self):
        """build_static_result() should generate default name when missing."""
        task = {"id": 3}
        result = ResultBuilder.build_static_result(task)

        assert result["step_name"] == "Step 3"
        assert result["content"] == "Step 3を実行しました"
        assert result["improvement_suggestions"] == ["Step 3の改善提案"]

    def test_build_result_handles_empty_task(self):
        """build_static_result() should handle empty task dict."""
        task = {}
        result = ResultBuilder.build_static_result(task)

        assert result["step_id"] == 0
        assert result["step_name"] == "Step 0"
        assert result["overall_score"] == 75.0
        assert result["metadata"]["llm_used"] is False

    def test_build_result_metadata_structure(self):
        """build_static_result() should include correct metadata."""
        task = {"id": 1, "name": "Check"}
        result = ResultBuilder.build_static_result(task)

        metadata = result["metadata"]

        assert isinstance(metadata, dict)
        assert metadata["llm_used"] is False
        assert len(metadata) == 1  # Only llm_used field

    def test_build_result_artifacts_empty(self):
        """build_static_result() should include empty artifacts list."""
        task = {"id": 1, "name": "Check"}
        result = ResultBuilder.build_static_result(task)

        assert result["artifacts"] == []
        assert isinstance(result["artifacts"], list)


# ============================================================================
# Integration Tests
# ============================================================================


class TestResultBuilderIntegration:
    """Integration tests for complete workflow."""

    def test_build_results_for_multiple_steps(self):
        """Test building results for multiple sequential steps."""
        tasks = [
            {"id": 1, "name": "誤字脱字チェック"},
            {"id": 2, "name": "文法チェック"},
            {"id": 3, "name": "表記統一チェック"},
        ]

        results = [ResultBuilder.build_static_result(task) for task in tasks]

        # All results should have expected structure
        for i, result in enumerate(results):
            assert result["step_id"] == i + 1
            assert result["metadata"]["llm_used"] is False
            assert result["overall_score"] > 75.0

        # Scores should increase with step_id
        scores = [r["overall_score"] for r in results]
        assert scores[0] < scores[1] < scores[2]

    def test_score_progression_across_steps(self):
        """Test score progression follows formula correctly."""
        step_ids = [1, 2, 3, 5, 10]
        tasks = [{"id": i, "name": f"Step {i}"} for i in step_ids]

        results = [ResultBuilder.build_static_result(task) for task in tasks]

        # Verify formula: 75 + min(step_id * 1.8, 18), capped at 96
        for i, step_id in enumerate(step_ids):
            expected_base = 75.0 + min(step_id * 1.8, 18.0)
            expected_overall = round(min(96.0, expected_base), 2)

            assert results[i]["overall_score"] == expected_overall

    def test_quality_breakdown_consistency(self):
        """Test quality breakdown values are consistent with overall score."""
        task = {"id": 8, "name": "Quality check"}
        result = ResultBuilder.build_static_result(task)

        overall = result["overall_score"]
        breakdown = result["quality_breakdown"]

        # All breakdown values should be <= overall_score
        assert breakdown["clarity"] == overall
        assert breakdown["consistency"] <= overall
        assert breakdown["readability"] <= overall

        # All breakdown values should be >= 70
        assert all(v >= 70.0 for v in breakdown.values())
