# File: tests/unit/domain/services/writing_steps/test_section_balance_orchestrator.py
# Purpose: Validate SectionBalanceOrchestrator coordination logic after import refactor.
# Context: Uses stub services to ensure orchestration flow completes without heavy dependencies.

from __future__ import annotations

from typing import Iterator

from pytest import MonkeyPatch, approx

from noveler.domain.services.section_analysis.balance_calculator import (
    BalanceMetrics,
    BalanceRequirements,
)
from noveler.domain.services.section_analysis.experience_optimizer import (
    ExperienceMetrics,
    ExperienceOptimizationResult,
)
from noveler.domain.services.section_analysis.optimization_engine import (
    OptimizationResult,
)
from noveler.domain.services.section_analysis.section_analyzer import (
    SectionAnalysisResult,
)
from noveler.domain.services.writing_steps.section_balance_orchestrator import (
    SectionBalanceOrchestrator,
    SectionBalanceRequest,
)


class _StubSectionAnalyzer:
    def analyze_section_structure(self, plot_data: dict, phase_structure: dict) -> SectionAnalysisResult:
        sections = [
            {
                "id": "section_1",
                "title": "イントロ",
                "estimated_length": 500,
                "type": "narrative",
                "pacing_requirements": {"speed": "slow"},
            },
            {
                "id": "section_2",
                "title": "クライマックス",
                "estimated_length": 1000,
                "type": "action",
                "pacing_requirements": {"speed": "fast"},
            },
        ]
        return SectionAnalysisResult(
            structure_assessment={"ok": True},
            natural_sections=sections,
            section_characteristics=[{"dialogue_ratio": 0.2}, {"dialogue_ratio": 0.5}],
            narrative_weights=[0.4, 0.6],
            emotional_intensities=[0.3, 0.8],
            pacing_requirements=[{"speed": "slow"}, {"speed": "fast"}],
            engagement_levels=[0.5, 0.7],
        )


class _StubBalanceCalculator:
    def calculate_balance_requirements(
        self,
        sections: list[dict],
        phase_structure: dict,
        target_episode_length: int,
    ) -> BalanceRequirements:
        return BalanceRequirements(
            length_balance={
                "target_lengths": [700, 800],
                "total_target": 1500,
            },
            intensity_balance={"ideal_intensity_curve": [0.4, 0.8]},
            pacing_balance={"tempo_changes": {"narrative": "medium", "action": "medium"}},
            content_balance={
                "dialogue_target_range": (0.3, 0.6),
                "action_target_range": (0.2, 0.5),
            },
            reader_experience_requirements={},
        )

    def assess_current_balance(
        self, sections: list[dict], requirements: BalanceRequirements
    ) -> BalanceMetrics:
        return BalanceMetrics(
            overall_balance_score=0.85,
            length_distribution=[0.5, 0.5],
            intensity_curve=[0.4, 0.8],
            pacing_variation=[0.2],
            content_ratios=[{"dialogue": 0.3}, {"dialogue": 0.4}],
            engagement_consistency=0.9,
        )


class _StubOptimizationEngine:
    def optimize_sections(self, request) -> OptimizationResult:
        optimized_sections = [
            {
                "id": "section_1",
                "title": "イントロ",
                "estimated_length": request.balance_requirements["length_balance"]["target_lengths"][0],
                "pacing_requirements": {"speed": "medium"},
            },
            {
                "id": "section_2",
                "title": "クライマックス",
                "estimated_length": request.balance_requirements["length_balance"]["target_lengths"][1],
                "pacing_requirements": {"speed": "medium"},
            },
        ]
        return OptimizationResult(
            optimized_sections=optimized_sections,
            optimization_score=0.82,
            improvements=[{"section_index": 0}],
            warnings=[],
            execution_time=0.05,
        )


class _StubExperienceOptimizer:
    def optimize_reader_experience(
        self,
        sections: list[dict],
        reader_preferences: dict | None,
        genre_constraints: dict | None,
    ) -> ExperienceOptimizationResult:
        metrics = ExperienceMetrics(
            engagement_levels=[0.6, 0.75],
            satisfaction_points=[0.7, 0.8],
            cognitive_load=[0.4, 0.5],
            emotional_journey=[0.3, 0.9],
            immersion_consistency=0.85,
            overall_experience_score=0.78,
        )
        return ExperienceOptimizationResult(
            optimized_sections=sections,
            experience_metrics=metrics,
            recommendations=[],
            experience_issues=[],
            improvement_score=0.12,
        )


def test_execute_section_balance_optimization_with_stubs(monkeypatch: MonkeyPatch) -> None:
    """スタブサービスで統合処理が成功することを確認する。"""

    time_values: Iterator[float] = iter((10.0, 10.3))
    monkeypatch.setattr(
        "noveler.domain.services.writing_steps.section_balance_orchestrator.time.time",
        lambda: next(time_values),
    )

    orchestrator = SectionBalanceOrchestrator()
    orchestrator._section_analyzer = _StubSectionAnalyzer()
    orchestrator._balance_calculator = _StubBalanceCalculator()
    orchestrator._optimization_engine = _StubOptimizationEngine()
    orchestrator._experience_optimizer = _StubExperienceOptimizer()

    request = SectionBalanceRequest(
        plot_data={"story": "example"},
        phase_structure={"phases": [{"name": "phase1"}, {"name": "phase2"}]},
        target_episode_length=1500,
        optimization_level="moderate",
    )

    result = orchestrator.execute_section_balance_optimization(request)

    assert result.overall_success is True
    assert result.execution_summary["execution_time"] == approx(0.3)
    assert len(result.final_sections) == 2
    assert result.final_sections[0]["estimated_length"] == 700
    assert result.optimization_result.optimization_score == approx(0.82)
