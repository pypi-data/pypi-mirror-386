# File: src/noveler/domain/services/result/result_builder.py
# Purpose: Build static execution results for quality check steps
# Context: Extracted from ProgressiveCheckManager._generate_static_execution_result

from typing import Any


class ResultBuilder:
    """Static execution result construction (Domain layer - no I/O).

    Responsibilities:
    - Generate static (non-LLM) execution results
    - Generate dry-run simulation results
    - Calculate deterministic quality scores
    - Build result structure with metadata

    Extracted from:
    - ProgressiveCheckManager._generate_static_execution_result (lines 2006-2024)
    - ProgressiveCheckManager._simulate_dry_run_result (lines 1182-1229)

    Design notes:
    - Score calculation: base_score = 75 + min(step_id * 1.8, 18)
    - Score capped at 96.0 to allow room for LLM-based improvements
    - Quality breakdown includes clarity, consistency, readability
    """

    @staticmethod
    def build_dry_run_result(
        task: dict[str, Any],
        input_data: dict[str, Any] | None,
        target_length_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        """Build dry-run simulation result for a check step.

        Args:
            task: Task dict with "id", "name", "phase" fields
            input_data: Optional input data with focus_areas, guidance_mode, etc.
            target_length_snapshot: Target length configuration snapshot

        Returns:
            Complete dry-run result dict with simulated scores and metadata

        Score calculation (dry-run specific):
            - Base score: 74.0 + min(step_id * 2.5, 21.0)
            - Overall score: min(96.0, base_score), rounded to 2 decimals
        """
        input_data = input_data or {}
        focus_areas = list(input_data.get("focus_areas", []))
        guidance_mode = bool(input_data.get("guidance_mode"))
        step_id = int(task.get("id", 0))
        phase = task.get("phase", "unknown")

        base_score = 74.0 + min(step_id * 2.5, 21.0)
        quality_score = round(min(96.0, base_score), 2)
        issues_found = max(0, 3 - (step_id % 4))

        improvements: list[str] = [f"{task.get('name', 'チェック')}の改善提案{i+1}" for i in range(2)]
        if focus_areas:
            improvements.extend(f"{area}の強化" for area in focus_areas)

        findings = focus_areas or [f"{task.get('name', 'チェック')}に関連する確認事項"]

        return {
            "step_id": step_id,
            "step_name": task.get("name"),
            "phase": phase,
            "content": f"[DRY RUN] {task.get('name', f'Step {step_id}')}のシミュレーション結果",
            "dry_run": True,
            "overall_score": quality_score,
            "quality_breakdown": {
                "clarity": min(100.0, quality_score + 2),
                "consistency": quality_score,
                "readability": max(70.0, quality_score - 3),
            },
            "issues_found": issues_found,
            "findings": findings,
            "improvement_suggestions": improvements,
            "guidance_applied": guidance_mode,
            "metrics": {
                "simulated_processing_time": round(0.3 + step_id * 0.05, 3),
                "confidence": round(min(0.99, 0.75 + step_id * 0.02), 2),
            },
            "applied_input": input_data,
            "metadata": {
                "config_snapshot": {
                    "target_length": target_length_snapshot,
                },
            },
        }

    @staticmethod
    def build_static_result(task: dict[str, Any]) -> dict[str, Any]:
        """Build static execution result for a check step.

        Args:
            task: Task dict with "id" and "name" fields

        Returns:
            Complete result dict with:
            - step_id, step_name, content
            - metadata (llm_used=False)
            - overall_score (deterministic calculation)
            - quality_breakdown (clarity, consistency, readability)
            - improvement_suggestions

        Score calculation:
            - Base score: 75.0 + min(step_id * 1.8, 18.0)
            - Overall score: min(96.0, base_score), rounded to 2 decimals
            - Clarity: overall_score
            - Consistency: max(70.0, overall_score - 5)
            - Readability: max(72.0, overall_score - 3)

        Example:
            >>> task = {"id": 1, "name": "誤字脱字チェック"}
            >>> result = ResultBuilder.build_static_result(task)
            >>> result["overall_score"]
            76.8
            >>> result["metadata"]["llm_used"]
            False
        """
        step_id = task.get("id", 0)
        step_name = task.get("name", f"Step {step_id}")

        # Deterministic score calculation
        # Base: 75 + (step_id * 1.8), capped at +18
        # Overall: capped at 96.0
        base_score = 75.0 + min(step_id * 1.8, 18.0)
        overall_score = round(min(96.0, base_score), 2)

        return {
            "step_id": step_id,
            "step_name": step_name,
            "content": f"{step_name}を実行しました",
            "metadata": {"llm_used": False},
            "artifacts": [],
            "overall_score": overall_score,
            "quality_breakdown": {
                "clarity": overall_score,
                "consistency": max(70.0, overall_score - 5),
                "readability": max(72.0, overall_score - 3),
            },
            "improvement_suggestions": [f"{step_name}の改善提案"],
        }
