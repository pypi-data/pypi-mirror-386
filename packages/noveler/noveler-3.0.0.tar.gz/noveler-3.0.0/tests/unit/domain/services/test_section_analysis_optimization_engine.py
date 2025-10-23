# File: tests/unit/domain/services/test_section_analysis_optimization_engine.py
# Purpose: Ensure OptimizationEngine applies balancing rules and reports execution metadata reliably.
# Context: Guards PLC0415対応後のトップレベルimportとセクション最適化ロジックの回帰防止。

from __future__ import annotations

from typing import Iterator

from pytest import MonkeyPatch, approx

from noveler.domain.services.section_analysis.optimization_engine import (
    OptimizationEngine,
    OptimizationRequest,
)


def test_optimize_sections_returns_balanced_result(monkeypatch: MonkeyPatch) -> None:
    """最適化処理が調整結果・改善点・警告を返すことを検証する。"""

    time_sequence: Iterator[float] = iter((100.0, 100.2))

    monkeypatch.setattr(
        "noveler.domain.services.section_analysis.optimization_engine.time.time",
        lambda: next(time_sequence),
    )

    engine = OptimizationEngine()
    request = OptimizationRequest(
        sections=[
            {
                "title": "プロローグ",
                "estimated_length": 500,
                "emotional_intensity": 0.1,
                "pacing_requirements": {"speed": "slow"},
                "characteristics": {"dialogue_ratio": 0.1, "action_ratio": 0.7},
                "type": "dialogue",
            },
            {
                "title": "クライマックス",
                "estimated_length": 1500,
                "emotional_intensity": 0.9,
                "pacing_requirements": {"speed": "fast"},
                "characteristics": {"dialogue_ratio": 0.8, "action_ratio": 0.1},
                "type": "action",
            },
        ],
        balance_requirements={
            "length_balance": {"target_lengths": [800, 900]},
            "intensity_balance": {"ideal_intensity_curve": [0.4, 0.8]},
            "pacing_balance": {"tempo_changes": {"dialogue": "medium", "action": "medium"}},
            "content_balance": {
                "dialogue_target_range": (0.3, 0.6),
                "action_target_range": (0.2, 0.4),
            },
        },
        target_metrics={},
        constraints={
            "max_section_length": 850,
            "min_section_length": 400,
            "target_total_length": 1500,
        },
    )

    result = engine.optimize_sections(request)

    assert len(result.optimized_sections) == 2
    assert result.optimized_sections[0]["estimated_length"] == 800
    assert result.optimized_sections[0]["requires_length_adjustment"] is True
    assert result.optimized_sections[0]["pacing_requirements"]["speed"] == "medium"
    assert result.improvements, "改善点が検出されるべき"
    assert result.warnings, "制約違反による警告が生成されるべき"
    assert result.execution_time == approx(0.2)
