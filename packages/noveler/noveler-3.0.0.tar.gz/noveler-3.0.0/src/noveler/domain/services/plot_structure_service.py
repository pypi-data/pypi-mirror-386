"""
Plot Structure Service - Pure Domain Service

Responsible for core business rules around plot structure generation.
Contains domain knowledge about narrative structure and storytelling rules.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PlotStructureType(Enum):
    """Domain-defined plot structure types"""

    THREE_ACT = "three_act"
    KISHŌTENKETSU = "kishotenketsu"  # Japanese 4-act structure
    HERO_JOURNEY = "hero_journey"
    EPISODIC = "episodic"
    CLIFFHANGER = "cliffhanger"


class NarrativeTension(Enum):
    """Narrative tension levels for story pacing"""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CLIMACTIC = "climactic"


@dataclass
class PlotParameters:
    """Domain entity for plot generation parameters"""

    episode_number: int
    chapter_number: int
    total_episodes_planned: int | None = None
    genre: str | None = None
    target_word_count: int | None = None
    structure_type: PlotStructureType = PlotStructureType.KISHŌTENKETSU
    character_focus: str | None = None


@dataclass
class PlotStructure:
    """Domain entity representing generated plot structure"""

    episode_number: int
    chapter_number: int
    structure_type: PlotStructureType
    opening: str
    development: str
    climax: str
    resolution: str
    character_arcs: list[dict[str, Any]]
    tension_curve: list[NarrativeTension]
    foreshadowing_elements: list[str]
    pacing_notes: str


@dataclass
class CharacterArc:
    """Domain entity for character development"""

    character_name: str
    starting_state: str
    development_goal: str
    obstacles: list[str]
    growth_moment: str
    ending_state: str


class PlotStructureService:
    """
    Pure domain service for plot structure generation

    Contains business rules for:
    - Narrative structure patterns
    - Character development rules
    - Story pacing and tension management
    - Genre-specific conventions
    """

    def __init__(self) -> None:
        self._structure_templates = self._initialize_structure_templates()
        self._tension_patterns = self._initialize_tension_patterns()
        self._genre_conventions = self._initialize_genre_conventions()

    def generate_plot_structure(self, parameters: PlotParameters) -> PlotStructure:
        """Generate plot structure based on business rules

        Args:
            parameters: Plot generation parameters

        Returns:
            PlotStructure: Generated plot structure following domain rules
        """
        structure_template = self._get_structure_template(parameters.structure_type)

        # Apply business rules for structure adaptation
        adapted_structure = self._adapt_structure_for_episode(structure_template, parameters)

        # Generate character arcs using domain rules
        character_arcs = self._generate_character_arcs(parameters)

        # Create tension curve following narrative principles
        tension_curve = self._create_tension_curve(parameters)

        # Generate foreshadowing elements
        foreshadowing = self._generate_foreshadowing_elements(parameters)

        # Apply pacing rules
        pacing_notes = self._generate_pacing_notes(parameters, tension_curve)

        return PlotStructure(
            episode_number=parameters.episode_number,
            chapter_number=parameters.chapter_number,
            structure_type=parameters.structure_type,
            opening=adapted_structure["opening"],
            development=adapted_structure["development"],
            climax=adapted_structure["climax"],
            resolution=adapted_structure["resolution"],
            character_arcs=character_arcs,
            tension_curve=tension_curve,
            foreshadowing_elements=foreshadowing,
            pacing_notes=pacing_notes,
        )

    def structure_character_development(
        self, characters: list[str], episode_context: dict[str, Any]
    ) -> list[CharacterArc]:
        """Apply character development business rules

        Args:
            characters: List of character names
            episode_context: Context for character development

        Returns:
            list[CharacterArc]: Structured character development plans
        """
        arcs = []

        for character in characters:
            arc = self._create_character_arc(character, episode_context)
            arcs.append(arc)

        # Apply business rules for character interaction
        arcs = self._balance_character_screen_time(arcs)
        return self._ensure_character_growth_coherence(arcs)

    def validate_plot_coherence(self, structure: PlotStructure) -> list[str]:
        """Validate plot structure against business rules

        Args:
            structure: Plot structure to validate

        Returns:
            list[str]: List of validation issues found
        """
        issues = []

        # Check narrative flow
        if not self._has_clear_narrative_progression(structure):
            issues.append("Narrative progression lacks clarity")

        # Check character development
        if not self._character_arcs_are_balanced(structure.character_arcs):
            issues.append("Character development is unbalanced")

        # Check tension curve
        if not self._tension_curve_is_valid(structure.tension_curve):
            issues.append("Tension curve needs improvement")

        # Check foreshadowing placement
        if not self._foreshadowing_is_appropriate(structure.foreshadowing_elements):
            issues.append("Foreshadowing needs better integration")

        return issues

    def adapt_structure_for_serial(
        self,
        base_structure: PlotStructure,
        previous_episode: PlotStructure | None = None,
        next_episode_preview: dict[str, Any] | None = None,
    ) -> PlotStructure:
        """Adapt structure for serial publication (Narou-style)

        Args:
            base_structure: Base plot structure
            previous_episode: Previous episode for continuity
            next_episode_preview: Preview of next episode for setup

        Returns:
            PlotStructure: Adapted structure for serial format
        """
        # Business rules for serial adaptation
        adapted_opening = self._adapt_opening_for_serial(base_structure.opening, previous_episode)

        adapted_resolution = self._adapt_resolution_for_serial(base_structure.resolution, next_episode_preview)

        # Add hook elements for reader retention
        enhanced_foreshadowing = self._enhance_foreshadowing_for_serial(base_structure.foreshadowing_elements)

        return PlotStructure(
            episode_number=base_structure.episode_number,
            chapter_number=base_structure.chapter_number,
            structure_type=base_structure.structure_type,
            opening=adapted_opening,
            development=base_structure.development,
            climax=base_structure.climax,
            resolution=adapted_resolution,
            character_arcs=base_structure.character_arcs,
            tension_curve=base_structure.tension_curve,
            foreshadowing_elements=enhanced_foreshadowing,
            pacing_notes=f"{base_structure.pacing_notes} | Serial adaptation applied",
        )

    def _initialize_structure_templates(self) -> dict[PlotStructureType, dict[str, str]]:
        """Initialize narrative structure templates"""
        return {
            PlotStructureType.KISHŌTENKETSU: {
                "opening": "Introduction (起) - Establish setting and characters",
                "development": "Development (承) - Build situation and relationships",
                "climax": "Twist (転) - Introduce unexpected element or conflict",
                "resolution": "Conclusion (結) - Resolve and reflect on changes",
            },
            PlotStructureType.THREE_ACT: {
                "opening": "Act I - Setup and inciting incident",
                "development": "Act II - Rising action and complications",
                "climax": "Act II Climax - Major turning point",
                "resolution": "Act III - Falling action and resolution",
            },
            PlotStructureType.EPISODIC: {
                "opening": "Episode setup - Establish this episode's focus",
                "development": "Episode progression - Develop main conflict",
                "climax": "Episode climax - Peak moment of tension",
                "resolution": "Episode wrap-up - Resolve and setup next",
            },
        }

    def _initialize_tension_patterns(self) -> dict[PlotStructureType, list[NarrativeTension]]:
        """Initialize tension curve patterns for different structures"""
        return {
            PlotStructureType.KISHŌTENKETSU: [
                NarrativeTension.LOW,  # 起 - calm introduction
                NarrativeTension.MODERATE,  # 承 - building situation
                NarrativeTension.HIGH,  # 転 - twist/conflict
                NarrativeTension.MODERATE,  # 結 - resolution
            ],
            PlotStructureType.THREE_ACT: [
                NarrativeTension.MODERATE,  # Act I
                NarrativeTension.HIGH,  # Act II part 1
                NarrativeTension.CLIMACTIC,  # Act II climax
                NarrativeTension.LOW,  # Act III
            ],
        }

    def _initialize_genre_conventions(self) -> dict[str, dict[str, Any]]:
        """Initialize genre-specific conventions"""
        return {
            "fantasy": {
                "typical_elements": ["magic system", "world building", "character abilities"],
                "pacing": "moderate",
                "character_focus": "growth_oriented",
            },
            "slice_of_life": {
                "typical_elements": ["daily activities", "character interactions", "subtle emotions"],
                "pacing": "slow",
                "character_focus": "relationship_oriented",
            },
            "adventure": {
                "typical_elements": ["challenges", "exploration", "action sequences"],
                "pacing": "fast",
                "character_focus": "goal_oriented",
            },
        }

    def _get_structure_template(self, structure_type: PlotStructureType) -> dict[str, str]:
        """Get appropriate structure template"""
        return self._structure_templates.get(structure_type, self._structure_templates[PlotStructureType.KISHŌTENKETSU])

    def _adapt_structure_for_episode(self, template: dict[str, str], parameters: PlotParameters) -> dict[str, str]:
        """Adapt generic template for specific episode"""
        adapted = {}

        for section, template_text in template.items():
            adapted[section] = f"Episode {parameters.episode_number}: {template_text}"

            # Add episode-specific details
            if parameters.character_focus:
                adapted[section] += f" (Focus: {parameters.character_focus})"

        return adapted

    def _generate_character_arcs(self, parameters: PlotParameters) -> list[dict[str, Any]]:
        """Generate character arcs based on domain rules"""
        # Simplified character arc generation
        main_arc = {
            "character": parameters.character_focus or "protagonist",
            "development": f"Character growth in episode {parameters.episode_number}",
            "arc_type": "growth",
            "completion_percentage": min(parameters.episode_number * 10, 100),
        }

        return [main_arc]

    def _create_tension_curve(self, parameters: PlotParameters) -> list[NarrativeTension]:
        """Create tension curve following narrative principles"""
        base_pattern = self._tension_patterns.get(
            parameters.structure_type, self._tension_patterns[PlotStructureType.KISHŌTENKETSU]
        )

        # Modify based on episode position in series
        if parameters.total_episodes_planned:
            series_position = parameters.episode_number / parameters.total_episodes_planned
            if series_position > 0.8:  # Near end of series:
                # Increase overall tension
                return [self._intensify_tension(t) for t in base_pattern]

        return base_pattern

    def _generate_foreshadowing_elements(self, parameters: PlotParameters) -> list[str]:
        """Generate foreshadowing elements using domain rules"""
        foreshadowing = []

        # Early episodes setup future events
        if parameters.episode_number <= 3:
            foreshadowing.append("Establish mysterious background element")
            foreshadowing.append("Hint at character's hidden potential")

        # Middle episodes develop setup
        elif parameters.episode_number <= 10:
            foreshadowing.append("Develop consequences of earlier decisions")
            foreshadowing.append("Build toward mid-series revelation")

        # Later episodes payoff setup
        else:
            foreshadowing.append("Pay off early episode setup")
            foreshadowing.append("Setup for series conclusion")

        return foreshadowing

    def _generate_pacing_notes(self, parameters: PlotParameters, tension_curve: list[NarrativeTension]) -> str:
        """Generate pacing guidance based on business rules"""
        pacing_advice = []

        # Word count considerations
        if parameters.target_word_count:
            if parameters.target_word_count < 2000:
                pacing_advice.append("Tight pacing required for short format")
            elif parameters.target_word_count > 5000:
                pacing_advice.append("Allow for slower character development")

        # Tension curve considerations
        if NarrativeTension.CLIMACTIC in tension_curve:
            pacing_advice.append("Build carefully to climactic moment")

        # Episode position considerations
        if parameters.episode_number == 1:
            pacing_advice.append("Balance introduction with engagement")

        return " | ".join(pacing_advice) if pacing_advice else "Standard pacing"

    def _create_character_arc(self, character: str, context: dict[str, Any]) -> CharacterArc:
        """Create individual character arc"""
        return CharacterArc(
            character_name=character,
            starting_state=f"{character} current state",
            development_goal=f"{character} growth goal",
            obstacles=["internal conflict", "external challenge"],
            growth_moment=f"{character} breakthrough moment",
            ending_state=f"{character} evolved state",
        )

    def _balance_character_screen_time(self, arcs: list[CharacterArc]) -> list[CharacterArc]:
        """Apply business rules for balanced character development"""
        # Ensure no single character dominates
        return arcs  # Simplified implementation

    def _ensure_character_growth_coherence(self, arcs: list[CharacterArc]) -> list[CharacterArc]:
        """Ensure character growth follows coherent patterns"""
        return arcs  # Simplified implementation

    def _has_clear_narrative_progression(self, structure: PlotStructure) -> bool:
        """Check if narrative has clear progression"""
        return len(structure.opening) > 0 and len(structure.resolution) > 0

    def _character_arcs_are_balanced(self, arcs: list[dict[str, Any]]) -> bool:
        """Check if character arcs are balanced"""
        return len(arcs) > 0

    def _tension_curve_is_valid(self, curve: list[NarrativeTension]) -> bool:
        """Check if tension curve follows good narrative principles"""
        return len(curve) >= 3  # Minimum structure

    def _foreshadowing_is_appropriate(self, elements: list[str]) -> bool:
        """Check if foreshadowing is appropriate for episode"""
        return len(elements) > 0

    def _adapt_opening_for_serial(self, base_opening: str, previous_episode: PlotStructure | None) -> str:
        """Adapt opening for serial continuity"""
        if previous_episode:
            return f"Continuing from previous episode: {base_opening}"
        return base_opening

    def _adapt_resolution_for_serial(self, base_resolution: str, next_episode_preview: dict[str, Any] | None) -> str:
        """Adapt resolution to setup next episode"""
        if next_episode_preview:
            return f"{base_resolution} | Setup for next: {next_episode_preview.get('hook', '')}"
        return base_resolution

    def _enhance_foreshadowing_for_serial(self, base_elements: list[str]) -> list[str]:
        """Enhance foreshadowing for serial format"""
        enhanced = base_elements.copy()
        enhanced.append("Add hook for next episode")
        enhanced.append("Reinforce series-long mystery")
        return enhanced

    def _intensify_tension(self, tension: NarrativeTension) -> NarrativeTension:
        """Intensify tension level for series climax"""
        intensity_map = {
            NarrativeTension.LOW: NarrativeTension.MODERATE,
            NarrativeTension.MODERATE: NarrativeTension.HIGH,
            NarrativeTension.HIGH: NarrativeTension.CLIMACTIC,
            NarrativeTension.CLIMACTIC: NarrativeTension.CLIMACTIC,
        }
        return intensity_map.get(tension, tension)
