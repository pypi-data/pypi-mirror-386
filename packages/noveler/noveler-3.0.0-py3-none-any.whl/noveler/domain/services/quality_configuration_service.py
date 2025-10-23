#!/usr/bin/env python3
"""
Quality Configuration Service - Pure Domain Service

Responsible for managing quality check configurations, rules, and settings.
"""

from dataclasses import dataclass, field
from typing import Any

from noveler.domain.value_objects.project_time import project_now
from noveler.domain.value_objects.quality_types import QualityCheckType, QualitySeverity


@dataclass
class QualityCheckConfig:
    """Configuration for quality checks"""

    check_type: QualityCheckType = QualityCheckType.BASIC
    include_suggestions: bool = True
    max_suggestions: int = 10
    severity_threshold: QualitySeverity = QualitySeverity.INFO
    custom_rules: dict[str, Any] = field(default_factory=dict)
    project_specific: bool = False
    adaptive_learning: bool = False
    viewpoint_aware: bool = False


@dataclass
class A31ChecklistItem:
    """A31 checklist item configuration"""

    id: str
    name: str
    description: str
    weight: float = 1.0
    enabled: bool = True
    evaluation_criteria: dict[str, Any] = field(default_factory=dict)


class QualityConfigurationService:
    """
    Domain service for quality configuration management

    Responsibilities:
    - Manage quality check configurations
    - Provide default and custom quality rules
    - Configure A31 checklist items
    - Handle project-specific quality settings
    - Manage adaptive learning parameters
    """

    def __init__(self) -> None:
        """Initialize quality configuration service"""
        self._default_configs = self._load_default_configurations()
        self._project_configs = {}
        self._a31_checklist = self._load_a31_checklist()
        self._quality_rules = self._load_default_quality_rules()

    def get_quality_config(
        self,
        check_type: QualityCheckType,
        project_name: str | None = None,
        custom_overrides: dict[str, Any] | None = None,
    ) -> QualityCheckConfig:
        """Get quality check configuration

        Args:
            check_type: Type of quality check
            project_name: Project identifier for project-specific config
            custom_overrides: Custom configuration overrides

        Returns:
            QualityCheckConfig: Quality check configuration
        """
        # Start with default config
        config = self._default_configs.get(check_type, QualityCheckConfig(check_type=check_type))

        # Apply project-specific configuration if available
        if project_name and project_name in self._project_configs:
            project_config: dict[str, Any] = self._project_configs[project_name].get(check_type)
            if project_config:
                config = self._merge_configs(config, project_config)

        # Apply custom overrides
        if custom_overrides:
            config = self._apply_config_overrides(config, custom_overrides)

        return config

    def create_project_config(self, project_name: str, config_settings: dict[QualityCheckType, dict[str, Any]]) -> None:
        """Create project-specific quality configuration

        Args:
            project_name: Project identifier
            config_settings: Configuration settings by check type
        """
        project_configs = {}

        for check_type, settings in config_settings.items():
            base_config: dict[str, Any] = self._default_configs.get(
                check_type, QualityCheckConfig(check_type=check_type)
            )
            project_config: dict[str, Any] = self._apply_config_overrides(base_config, settings)
            project_config.project_specific = True
            project_configs[check_type] = project_config

        self._project_configs[project_name] = project_configs

    def get_a31_checklist(self, enabled_only: bool = True) -> list[A31ChecklistItem]:
        """Get A31 manuscript checklist items

        Args:
            enabled_only: Return only enabled items

        Returns:
            list[A31ChecklistItem]: A31 checklist items
        """
        if enabled_only:
            return [item for item in self._a31_checklist if item.enabled]
        return self._a31_checklist.copy()

    def update_a31_checklist_item(self, item_id: str, updates: dict[str, Any]) -> bool:
        """Update A31 checklist item

        Args:
            item_id: Item identifier
            updates: Updates to apply

        Returns:
            bool: True if item was found and updated
        """
        for item in self._a31_checklist:
            if item.id == item_id:
                for key, value in updates.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                return True
        return False

    def get_quality_rules(self, rule_category: str | None = None, project_name: str | None = None) -> dict[str, Any]:
        """Get quality evaluation rules

        Args:
            rule_category: Specific rule category (content, structure, etc.)
            project_name: Project identifier for project-specific rules

        Returns:
            Dict[str, Any]: Quality rules
        """
        rules = self._quality_rules.copy()

        # Apply project-specific rules
        if project_name and project_name in self._project_configs:
            # Check for project-specific rule overrides
            for config in self._project_configs[project_name].values():
                if config.custom_rules:
                    rules.update(config.custom_rules)

        # Filter by category if specified
        if rule_category:
            return rules.get(rule_category, {})

        return rules

    def create_adaptive_config(self, project_name: str, learning_data: dict[str, Any]) -> QualityCheckConfig:
        """Create adaptive quality configuration based on learning data

        Args:
            project_name: Project identifier
            learning_data: Historical learning data

        Returns:
            QualityCheckConfig: Adaptive configuration
        """
        base_config: dict[str, Any] = self._default_configs[QualityCheckType.ADAPTIVE]

        # Adjust configuration based on learning patterns
        adaptive_rules = self._generate_adaptive_rules(learning_data)

        return QualityCheckConfig(
            check_type=QualityCheckType.ADAPTIVE,
            include_suggestions=base_config.include_suggestions,
            max_suggestions=base_config.max_suggestions,
            severity_threshold=base_config.severity_threshold,
            custom_rules=adaptive_rules,
            project_specific=True,
            adaptive_learning=True,
        )

    def create_viewpoint_config(self, viewpoint_info: dict[str, Any]) -> QualityCheckConfig:
        """Create viewpoint-aware quality configuration

        Args:
            viewpoint_info: Viewpoint configuration

        Returns:
            QualityCheckConfig: Viewpoint-aware configuration
        """
        base_config: dict[str, Any] = self._default_configs[QualityCheckType.VIEWPOINT_AWARE]

        # Adjust rules based on viewpoint type
        viewpoint_rules = self._generate_viewpoint_rules(viewpoint_info)

        return QualityCheckConfig(
            check_type=QualityCheckType.VIEWPOINT_AWARE,
            include_suggestions=base_config.include_suggestions,
            max_suggestions=base_config.max_suggestions,
            severity_threshold=base_config.severity_threshold,
            custom_rules=viewpoint_rules,
            project_specific=False,
            viewpoint_aware=True,
        )

    def validate_config(self, config: QualityCheckConfig) -> list[str]:
        """Validate quality check configuration

        Args:
            config: Configuration to validate

        Returns:
            list[str]: Validation errors (empty if valid)
        """
        errors: list[Any] = []

        # Basic validation
        if config.max_suggestions < 1 or config.max_suggestions > 50:
            errors.append("max_suggestions must be between 1 and 50")

        # Check type specific validation
        if config.check_type == QualityCheckType.A31_CHECKLIST:
            if not self._a31_checklist:
                errors.append("A31 checklist items not configured")

        if config.adaptive_learning and not config.project_specific:
            errors.append("Adaptive learning requires project-specific configuration")

        return errors

    def export_project_config(self, project_name: str) -> dict[str, Any] | None:
        """Export project configuration

        Args:
            project_name: Project identifier

        Returns:
            Dict[str, Any]: Exported configuration or None if not found
        """
        if project_name not in self._project_configs:
            return None

        project_configs = self._project_configs[project_name]
        export_data: dict[str, Any] = {}

        for check_type, config in project_configs.items():
            export_data[check_type.value] = {
                "check_type": config.check_type.value,
                "include_suggestions": config.include_suggestions,
                "max_suggestions": config.max_suggestions,
                "severity_threshold": config.severity_threshold.value,
                "custom_rules": config.custom_rules,
                "project_specific": config.project_specific,
                "adaptive_learning": config.adaptive_learning,
                "viewpoint_aware": config.viewpoint_aware,
            }

        return {
            "project_name": project_name,
            "configurations": export_data,
            "export_timestamp": project_now().datetime.isoformat(),
        }

    def import_project_config(self, config_data: dict[str, Any]) -> bool:
        """Import project configuration

        Args:
            config_data: Configuration data to import

        Returns:
            bool: True if import was successful
        """
        try:
            project_name = config_data["project_name"]
            configurations = config_data["configurations"]

            project_configs = {}

            for check_type_str, config_dict in configurations.items():
                check_type = QualityCheckType(check_type_str)
                severity_threshold = QualitySeverity(config_dict["severity_threshold"])

                config = QualityCheckConfig(
                    check_type=check_type,
                    include_suggestions=config_dict["include_suggestions"],
                    max_suggestions=config_dict["max_suggestions"],
                    severity_threshold=severity_threshold,
                    custom_rules=config_dict["custom_rules"],
                    project_specific=config_dict["project_specific"],
                    adaptive_learning=config_dict["adaptive_learning"],
                    viewpoint_aware=config_dict["viewpoint_aware"],
                )

                project_configs[check_type] = config

            self._project_configs[project_name] = project_configs
            return True

        except (KeyError, ValueError):
            return False

    def _load_default_configurations(self) -> dict[QualityCheckType, QualityCheckConfig]:
        """Load default quality configurations

        Returns:
            Dict[QualityCheckType, QualityCheckConfig]: Default configurations
        """
        return {
            QualityCheckType.BASIC: QualityCheckConfig(
                check_type=QualityCheckType.BASIC,
                include_suggestions=True,
                max_suggestions=5,
                severity_threshold=QualitySeverity.INFO,
            ),
            QualityCheckType.COMPREHENSIVE: QualityCheckConfig(
                check_type=QualityCheckType.COMPREHENSIVE,
                include_suggestions=True,
                max_suggestions=10,
                severity_threshold=QualitySeverity.INFO,
            ),
            QualityCheckType.ADAPTIVE: QualityCheckConfig(
                check_type=QualityCheckType.ADAPTIVE,
                include_suggestions=True,
                max_suggestions=8,
                severity_threshold=QualitySeverity.WARNING,
                adaptive_learning=True,
            ),
            QualityCheckType.VIEWPOINT_AWARE: QualityCheckConfig(
                check_type=QualityCheckType.VIEWPOINT_AWARE,
                include_suggestions=True,
                max_suggestions=7,
                severity_threshold=QualitySeverity.INFO,
                viewpoint_aware=True,
            ),
            QualityCheckType.A31_CHECKLIST: QualityCheckConfig(
                check_type=QualityCheckType.A31_CHECKLIST,
                include_suggestions=True,
                max_suggestions=12,
                severity_threshold=QualitySeverity.WARNING,
            ),
        }

    def _load_a31_checklist(self) -> list[A31ChecklistItem]:
        """Load A31 manuscript checklist items

        Returns:
            list[A31ChecklistItem]: A31 checklist items
        """
        return [
            A31ChecklistItem(
                id="opening_appeal",
                name="Opening Appeal",
                description="Evaluate the attractiveness and hook of the opening",
                weight=1.2,
                evaluation_criteria={"first_paragraph": True, "hook_strength": True},
            ),
            A31ChecklistItem(
                id="dialogue_balance",
                name="Dialogue Balance",
                description="Assess balance between dialogue and narrative",
                weight=1.0,
                evaluation_criteria={"dialogue_ratio": True, "natural_flow": True},
            ),
            A31ChecklistItem(
                id="pacing_control",
                name="Pacing Control",
                description="Evaluate story pacing and tempo management",
                weight=1.1,
                evaluation_criteria={"scene_transitions": True, "tension_management": True},
            ),
            A31ChecklistItem(
                id="character_development",
                name="Character Development",
                description="Assess character growth and development",
                weight=1.3,
                evaluation_criteria={"character_arc": True, "consistency": True},
            ),
            A31ChecklistItem(
                id="emotional_impact",
                name="Emotional Impact",
                description="Evaluate emotional resonance and impact",
                weight=1.2,
                evaluation_criteria={"emotional_depth": True, "reader_engagement": True},
            ),
            A31ChecklistItem(
                id="narrative_clarity",
                name="Narrative Clarity",
                description="Assess clarity and coherence of narrative",
                weight=1.0,
                evaluation_criteria={"logical_flow": True, "clear_communication": True},
            ),
            A31ChecklistItem(
                id="world_building",
                name="World Building",
                description="Evaluate world building and setting details",
                weight=0.9,
                evaluation_criteria={"setting_consistency": True, "immersion": True},
            ),
            A31ChecklistItem(
                id="conflict_resolution",
                name="Conflict Resolution",
                description="Assess conflict development and resolution",
                weight=1.1,
                evaluation_criteria={"conflict_clarity": True, "satisfying_resolution": True},
            ),
        ]

    def _load_default_quality_rules(self) -> dict[str, Any]:
        """Load default quality evaluation rules

        Returns:
            Dict[str, Any]: Default quality rules
        """
        return {
            "content": {
                "word_count_min": 1000,
                "word_count_target": 3000,
                "word_count_max": 8000,
                "paragraph_min": 3,
                "paragraph_max": 50,
            },
            "structure": {
                "dialogue_required": True,
                "dialogue_min_ratio": 0.15,
                "dialogue_max_ratio": 0.65,
                "scene_breaks_required": True,
            },
            "expression": {
                "repetition_threshold": 5,
                "sentence_variety_min": 15,
                "emotional_words_min_ratio": 0.05,
                "sensory_words_min_ratio": 0.03,
            },
            "character": {"consistency_check": True, "development_tracking": True, "dialogue_consistency": True},
            "narrative": {
                "internal_thought_min_ratio": 0.1,
                "emotional_depth_min_ratio": 0.2,
                "sensory_description_min_ratio": 0.15,
                "pacing_variation_required": True,
            },
        }

    def _merge_configs(
        self, base_config: QualityCheckConfig, override_config: QualityCheckConfig
    ) -> QualityCheckConfig:
        """Merge two quality configurations

        Args:
            base_config: Base configuration
            override_config: Override configuration

        Returns:
            QualityCheckConfig: Merged configuration
        """
        merged_rules = base_config.custom_rules.copy()
        merged_rules.update(override_config.custom_rules)

        return QualityCheckConfig(
            check_type=override_config.check_type or base_config.check_type,
            include_suggestions=override_config.include_suggestions,
            max_suggestions=override_config.max_suggestions,
            severity_threshold=override_config.severity_threshold,
            custom_rules=merged_rules,
            project_specific=override_config.project_specific,
            adaptive_learning=override_config.adaptive_learning,
            viewpoint_aware=override_config.viewpoint_aware,
        )

    def _apply_config_overrides(self, config: QualityCheckConfig, overrides: dict[str, Any]) -> QualityCheckConfig:
        """Apply configuration overrides

        Args:
            config: Base configuration
            overrides: Override values

        Returns:
            QualityCheckConfig: Updated configuration
        """
        updated_config: dict[str, Any] = QualityCheckConfig(
            check_type=config.check_type,
            include_suggestions=overrides.get("include_suggestions", config.include_suggestions),
            max_suggestions=overrides.get("max_suggestions", config.max_suggestions),
            severity_threshold=overrides.get("severity_threshold", config.severity_threshold),
            custom_rules=config.custom_rules.copy(),
            project_specific=overrides.get("project_specific", config.project_specific),
            adaptive_learning=overrides.get("adaptive_learning", config.adaptive_learning),
            viewpoint_aware=overrides.get("viewpoint_aware", config.viewpoint_aware),
        )

        # Update custom rules
        if "custom_rules" in overrides:
            updated_config.custom_rules.update(overrides["custom_rules"])

        return updated_config

    def _generate_adaptive_rules(self, learning_data: dict[str, Any]) -> dict[str, Any]:
        """Generate adaptive rules based on learning data

        Args:
            learning_data: Historical learning data

        Returns:
            Dict[str, Any]: Adaptive rules
        """
        # Simplified adaptive rule generation
        return {
            "writing_style": learning_data.get("writing_style", "standard"),
            "common_issues": learning_data.get("common_issues", []),
            "strength_areas": learning_data.get("strength_areas", []),
            "focus_areas": learning_data.get("focus_areas", []),
        }

    def _generate_viewpoint_rules(self, viewpoint_info: dict[str, Any]) -> dict[str, Any]:
        """Generate viewpoint-specific rules

        Args:
            viewpoint_info: Viewpoint configuration

        Returns:
            Dict[str, Any]: Viewpoint rules
        """
        viewpoint_type = viewpoint_info.get("type", "single")
        viewpoint_character = viewpoint_info.get("character", "protagonist")

        return {
            "viewpoint_type": viewpoint_type,
            "viewpoint_character": viewpoint_character,
            "consistency_strict": viewpoint_type == "single",
            "perspective_switches_allowed": viewpoint_type in ["multiple", "omniscient"],
            "internal_access_limited": viewpoint_type == "single",
        }
