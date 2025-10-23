"""
Plot Quality Service - Pure Domain Service

Responsible for plot quality assessment and improvement based on business rules.
Contains domain knowledge about storytelling quality metrics and improvement strategies.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from noveler.domain.services.plot_structure_service import NarrativeTension, PlotStructure


class QualityAspect(Enum):
    """Domain-defined quality aspects for plot assessment"""

    NARRATIVE_COHERENCE = "narrative_coherence"
    CHARACTER_DEVELOPMENT = "character_development"
    PACING = "pacing"
    TENSION_MANAGEMENT = "tension_management"
    DIALOGUE_QUALITY = "dialogue_quality"
    WORLD_BUILDING = "world_building"
    ORIGINALITY = "originality"
    READER_ENGAGEMENT = "reader_engagement"


class QualityLevel(Enum):
    """Quality assessment levels"""

    POOR = "poor"
    BELOW_AVERAGE = "below_average"
    AVERAGE = "average"
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class QualityScore:
    """Domain entity representing quality assessment"""

    overall_score: float  # 0.0 to 1.0
    aspect_scores: dict[QualityAspect, float]
    quality_level: QualityLevel
    strengths: list[str]
    weaknesses: list[str]
    improvement_priority: list[QualityAspect]


@dataclass
class QualityImprovement:
    """Domain entity representing quality improvement suggestion"""

    aspect: QualityAspect
    current_score: float
    target_score: float
    improvement_strategy: str
    specific_actions: list[str]
    estimated_impact: float


@dataclass
class ImprovedPlot:
    """Domain entity representing plot after quality improvements"""

    original_structure: PlotStructure
    improved_structure: PlotStructure
    improvements_applied: list[QualityImprovement]
    quality_delta: float
    revision_notes: str


class PlotQualityService:
    """
    Pure domain service for plot quality assessment and improvement

    Contains business rules for:
    - Quality metric calculation
    - Storytelling best practices
    - Plot improvement strategies
    - Reader engagement optimization
    """

    def __init__(self) -> None:
        self._quality_weights = self._initialize_quality_weights()
        self._improvement_strategies = self._initialize_improvement_strategies()
        self._genre_quality_standards = self._initialize_genre_standards()

    def calculate_quality_score(self, plot: PlotStructure) -> QualityScore:
        """Calculate comprehensive quality score based on business rules

        Args:
            plot: Plot structure to assess

        Returns:
            QualityScore: Comprehensive quality assessment
        """
        aspect_scores = {}

        # Assess each quality aspect using domain rules
        aspect_scores[QualityAspect.NARRATIVE_COHERENCE] = self._assess_narrative_coherence(plot)
        aspect_scores[QualityAspect.CHARACTER_DEVELOPMENT] = self._assess_character_development(plot)
        aspect_scores[QualityAspect.PACING] = self._assess_pacing(plot)
        aspect_scores[QualityAspect.TENSION_MANAGEMENT] = self._assess_tension_management(plot)
        aspect_scores[QualityAspect.DIALOGUE_QUALITY] = self._assess_dialogue_quality(plot)
        aspect_scores[QualityAspect.WORLD_BUILDING] = self._assess_world_building(plot)
        aspect_scores[QualityAspect.ORIGINALITY] = self._assess_originality(plot)
        aspect_scores[QualityAspect.READER_ENGAGEMENT] = self._assess_reader_engagement(plot)

        # Calculate overall score using weighted average
        overall_score = self._calculate_weighted_average(aspect_scores)

        # Determine quality level
        quality_level = self._determine_quality_level(overall_score)

        # Identify strengths and weaknesses
        strengths = self._identify_strengths(aspect_scores)
        weaknesses = self._identify_weaknesses(aspect_scores)

        # Prioritize improvements
        improvement_priority = self._prioritize_improvements(aspect_scores)

        return QualityScore(
            overall_score=overall_score,
            aspect_scores=aspect_scores,
            quality_level=quality_level,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_priority=improvement_priority,
        )

    def generate_quality_improvements(
        self, plot: PlotStructure, quality_score: QualityScore
    ) -> list[QualityImprovement]:
        """Generate specific quality improvement suggestions

        Args:
            plot: Plot structure to improve
            quality_score: Current quality assessment

        Returns:
            list[QualityImprovement]: Prioritized improvement suggestions
        """
        improvements = []

        # Generate improvements for priority aspects
        for aspect in quality_score.improvement_priority:
            current_score = quality_score.aspect_scores[aspect]

            if current_score < 0.7:  # Below good threshold:
                improvement = self._create_improvement_plan(aspect, current_score, plot)
                improvements.append(improvement)

        # Sort by estimated impact
        improvements.sort(key=lambda x: x.estimated_impact, reverse=True)

        return improvements

    def apply_quality_improvements(self, plot: PlotStructure, improvements: list[QualityImprovement]) -> ImprovedPlot:
        """Apply quality improvements to plot structure

        Args:
            plot: Original plot structure
            improvements: List of improvements to apply

        Returns:
            ImprovedPlot: Plot with improvements applied
        """
        improved_structure = self._apply_improvements_to_structure(plot, improvements)

        # Calculate quality improvement
        original_quality = self.calculate_quality_score(plot)
        improved_quality = self.calculate_quality_score(improved_structure)
        quality_delta = improved_quality.overall_score - original_quality.overall_score

        # Generate revision notes
        revision_notes = self._generate_revision_notes(improvements)

        return ImprovedPlot(
            original_structure=plot,
            improved_structure=improved_structure,
            improvements_applied=improvements,
            quality_delta=quality_delta,
            revision_notes=revision_notes,
        )

    def assess_for_publication_readiness(self, plot: PlotStructure, target_audience: str = "general") -> dict[str, Any]:
        """Assess if plot meets publication quality standards

        Args:
            plot: Plot structure to assess
            target_audience: Target audience for publication

        Returns:
            dict: Publication readiness assessment
        """
        quality_score = self.calculate_quality_score(plot)

        # Publication thresholds based on business rules
        publication_thresholds = {
            "general": 0.7,
            "amateur": 0.5,  # Narou, etc.
            "professional": 0.85,
        }

        threshold = publication_thresholds.get(target_audience, 0.7)
        ready_for_publication = quality_score.overall_score >= threshold

        # Critical issues that block publication
        blocking_issues = self._identify_blocking_issues(quality_score)

        return {
            "ready_for_publication": ready_for_publication and len(blocking_issues) == 0,
            "overall_score": quality_score.overall_score,
            "required_threshold": threshold,
            "quality_level": quality_score.quality_level.value,
            "blocking_issues": blocking_issues,
            "recommended_improvements": quality_score.improvement_priority[:3],
            "strengths": quality_score.strengths,
            "estimated_revision_time": self._estimate_revision_time(quality_score),
        }

    def _initialize_quality_weights(self) -> dict[QualityAspect, float]:
        """Initialize quality aspect weights for overall score calculation"""
        return {
            QualityAspect.NARRATIVE_COHERENCE: 0.20,
            QualityAspect.CHARACTER_DEVELOPMENT: 0.15,
            QualityAspect.PACING: 0.15,
            QualityAspect.TENSION_MANAGEMENT: 0.15,
            QualityAspect.DIALOGUE_QUALITY: 0.10,
            QualityAspect.WORLD_BUILDING: 0.10,
            QualityAspect.ORIGINALITY: 0.10,
            QualityAspect.READER_ENGAGEMENT: 0.05,
        }

    def _initialize_improvement_strategies(self) -> dict[QualityAspect, dict[str, Any]]:
        """Initialize improvement strategies for each quality aspect"""
        return {
            QualityAspect.NARRATIVE_COHERENCE: {
                "strategy": "Strengthen plot logic and causality",
                "actions": [
                    "Review cause-and-effect relationships",
                    "Eliminate plot holes",
                    "Ensure consistent character motivations",
                    "Clarify timeline and sequence",
                ],
            },
            QualityAspect.CHARACTER_DEVELOPMENT: {
                "strategy": "Deepen character arcs and growth",
                "actions": [
                    "Define clear character goals",
                    "Add meaningful character obstacles",
                    "Show character growth through actions",
                    "Balance character screen time",
                ],
            },
            QualityAspect.PACING: {
                "strategy": "Optimize story rhythm and flow",
                "actions": [
                    "Balance action and reflection",
                    "Vary sentence and paragraph length",
                    "Use scene breaks effectively",
                    "Control information release",
                ],
            },
            QualityAspect.TENSION_MANAGEMENT: {
                "strategy": "Enhance dramatic tension",
                "actions": [
                    "Increase stakes throughout story",
                    "Add meaningful obstacles",
                    "Create tension through conflict",
                    "Build to satisfying climax",
                ],
            },
        }

    def _initialize_genre_standards(self) -> dict[str, dict[QualityAspect, float]]:
        """Initialize genre-specific quality standards"""
        return {
            "fantasy": {
                QualityAspect.WORLD_BUILDING: 0.8,
                QualityAspect.ORIGINALITY: 0.7,
                QualityAspect.CHARACTER_DEVELOPMENT: 0.7,
            },
            "slice_of_life": {
                QualityAspect.CHARACTER_DEVELOPMENT: 0.9,
                QualityAspect.DIALOGUE_QUALITY: 0.8,
                QualityAspect.PACING: 0.6,  # Slower pacing acceptable
            },
        }

    def _assess_narrative_coherence(self, plot: PlotStructure) -> float:
        """Assess narrative coherence using business rules"""
        score = 0.5  # Base score

        # Check for clear progression
        if len(plot.opening) > 50 and len(plot.resolution) > 50:
            score += 0.2

        # Check for logical structure
        if plot.climax and "climax" in plot.climax.lower():
            score += 0.1

        # Check character arc coherence
        if len(plot.character_arcs) > 0:
            score += 0.1

        # Check foreshadowing integration
        if len(plot.foreshadowing_elements) > 0:
            score += 0.1

        return min(score, 1.0)

    def _assess_character_development(self, plot: PlotStructure) -> float:
        """Assess character development quality"""
        if not plot.character_arcs:
            return 0.3  # Minimal score for no character development

        score = 0.4  # Base score for having character arcs

        # Assess character arc quality
        for arc in plot.character_arcs:
            if isinstance(arc, dict):
                if arc.get("development"):
                    score += 0.15
                if arc.get("arc_type") == "growth":
                    score += 0.1

        return min(score, 1.0)

    def _assess_pacing(self, plot: PlotStructure) -> float:
        """Assess story pacing quality"""
        score = 0.5  # Base score

        # Check tension curve variety
        if len(set(plot.tension_curve)) > 2:
            score += 0.2

        # Check for pacing notes
        if plot.pacing_notes and "pacing" in plot.pacing_notes.lower():
            score += 0.1

        # Check structure balance
        section_lengths = [len(plot.opening), len(plot.development), len(plot.climax), len(plot.resolution)]
        if max(section_lengths) - min(section_lengths) < 100:  # Balanced sections:
            score += 0.2

        return min(score, 1.0)

    def _assess_tension_management(self, plot: PlotStructure) -> float:
        """Assess tension management quality"""
        score = 0.4  # Base score

        # Check for climactic moments
        if NarrativeTension.CLIMACTIC in plot.tension_curve:
            score += 0.3

        # Check for tension variation
        if len(set(plot.tension_curve)) >= 3:
            score += 0.2

        # Check climax quality
        if plot.climax and len(plot.climax) > 50:
            score += 0.1

        return min(score, 1.0)

    def _assess_dialogue_quality(self, plot: PlotStructure) -> float:
        """Assess dialogue quality (simplified for plot structure)"""
        # Since plot structure doesn't contain actual dialogue,
        # assess based on character interaction potential
        score = 0.6  # Base score

        if len(plot.character_arcs) > 1:
            score += 0.2  # Multiple characters enable dialogue

        return min(score, 1.0)

    def _assess_world_building(self, plot: PlotStructure) -> float:
        """Assess world building quality"""
        score = 0.5  # Base score

        # Check for world building elements in structure
        if "world" in plot.opening.lower() or "setting" in plot.opening.lower():
            score += 0.2

        if len(plot.foreshadowing_elements) > 2:
            score += 0.1  # Rich foreshadowing suggests detailed world

        return min(score, 1.0)

    def _assess_originality(self, plot: PlotStructure) -> float:
        """Assess originality of plot elements"""
        score = 0.6  # Base score - difficult to assess automatically

        # Check for unique structure elements
        if plot.structure_type.value != "three_act":  # Non-standard structure:
            score += 0.1

        if len(plot.foreshadowing_elements) > 3:
            score += 0.1  # Complex foreshadowing suggests originality

        return min(score, 1.0)

    def _assess_reader_engagement(self, plot: PlotStructure) -> float:
        """Assess potential reader engagement"""
        score = 0.5  # Base score

        # Check for engagement elements
        if len(plot.foreshadowing_elements) > 0:
            score += 0.2  # Foreshadowing creates anticipation

        if NarrativeTension.HIGH in plot.tension_curve:
            score += 0.2  # High tension engages readers

        return min(score, 1.0)

    def _calculate_weighted_average(self, aspect_scores: dict[QualityAspect, float]) -> float:
        """Calculate weighted average of aspect scores"""
        total_weighted_score = 0.0
        total_weight = 0.0

        for aspect, score in aspect_scores.items():
            weight = self._quality_weights.get(aspect, 0.1)
            total_weighted_score += score * weight
            total_weight += weight

        return total_weighted_score / total_weight if total_weight > 0 else 0.0

    def _determine_quality_level(self, overall_score: float) -> QualityLevel:
        """Determine quality level from overall score"""
        if overall_score >= 0.9:
            return QualityLevel.EXCELLENT
        if overall_score >= 0.8:
            return QualityLevel.GOOD
        if overall_score >= 0.6:
            return QualityLevel.AVERAGE
        if overall_score >= 0.4:
            return QualityLevel.BELOW_AVERAGE
        return QualityLevel.POOR

    def _identify_strengths(self, aspect_scores: dict[QualityAspect, float]) -> list[str]:
        """Identify quality strengths"""
        strengths = []
        for aspect, score in aspect_scores.items():
            if score >= 0.8:
                strengths.append(f"Strong {aspect.value.replace('_', ' ')}")
        return strengths

    def _identify_weaknesses(self, aspect_scores: dict[QualityAspect, float]) -> list[str]:
        """Identify quality weaknesses"""
        weaknesses = []
        for aspect, score in aspect_scores.items():
            if score < 0.6:
                weaknesses.append(f"Weak {aspect.value.replace('_', ' ')}")
        return weaknesses

    def _prioritize_improvements(self, aspect_scores: dict[QualityAspect, float]) -> list[QualityAspect]:
        """Prioritize improvements by impact and importance"""
        # Sort by score (lowest first) and weight (highest first)
        prioritized = sorted(aspect_scores.items(), key=lambda x: (x[1], -self._quality_weights.get(x[0], 0.1)))

        return [aspect for aspect, score in prioritized if score < 0.8]

    def _create_improvement_plan(
        self, aspect: QualityAspect, current_score: float, plot: PlotStructure
    ) -> QualityImprovement:
        """Create specific improvement plan for aspect"""
        strategy_info = self._improvement_strategies.get(aspect, {})
        target_score = min(current_score + 0.2, 0.9)  # Realistic improvement

        return QualityImprovement(
            aspect=aspect,
            current_score=current_score,
            target_score=target_score,
            improvement_strategy=strategy_info.get("strategy", "General improvement"),
            specific_actions=strategy_info.get("actions", ["Review and revise"]),
            estimated_impact=self._quality_weights.get(aspect, 0.1) * (target_score - current_score),
        )

    def _apply_improvements_to_structure(
        self, plot: PlotStructure, improvements: list[QualityImprovement]
    ) -> PlotStructure:
        """Apply improvements to create improved plot structure"""
        # Create improved structure (simplified implementation)
        return PlotStructure(
            episode_number=plot.episode_number,
            chapter_number=plot.chapter_number,
            structure_type=plot.structure_type,
            opening=f"IMPROVED: {plot.opening}",
            development=f"ENHANCED: {plot.development}",
            climax=f"STRENGTHENED: {plot.climax}",
            resolution=f"REFINED: {plot.resolution}",
            character_arcs=plot.character_arcs,
            tension_curve=plot.tension_curve,
            foreshadowing_elements=[*plot.foreshadowing_elements, "Added improvement hook"],
            pacing_notes=f"{plot.pacing_notes} | Quality improvements applied",
        )

    def _generate_revision_notes(self, improvements: list[QualityImprovement]) -> str:
        """Generate revision notes for applied improvements"""
        notes = ["Quality improvements applied:"]

        for improvement in improvements:
            aspect_name = improvement.aspect.value.replace("_", " ").title()
            notes.append(f"- {aspect_name}: {improvement.improvement_strategy}")

        return "\n".join(notes)

    def _identify_blocking_issues(self, quality_score: QualityScore) -> list[str]:
        """Identify issues that block publication"""
        blocking_issues = []

        # Critical quality thresholds
        if quality_score.aspect_scores.get(QualityAspect.NARRATIVE_COHERENCE, 0) < 0.5:
            blocking_issues.append("Narrative coherence below acceptable threshold")

        if quality_score.overall_score < 0.4:
            blocking_issues.append("Overall quality too low for publication")

        return blocking_issues

    def _estimate_revision_time(self, quality_score: QualityScore) -> str:
        """Estimate time needed for revisions"""
        if quality_score.overall_score >= 0.8:
            return "1-2 hours (minor polish)"
        if quality_score.overall_score >= 0.6:
            return "4-8 hours (moderate revision)"
        if quality_score.overall_score >= 0.4:
            return "1-2 days (major revision)"
        return "3+ days (substantial rewrite)"
