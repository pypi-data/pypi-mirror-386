"""Writing Style Configuration Schema.

Domain Layer: Data class definitions for .novelerrc.yaml structure.
Responsible for: Type definitions, validation rules, schema contracts

SOLID Principles:
- SRP: Single responsibility (schema definition only)
- OCP: Open for extension (new fields can be added)
- LSP: N/A (no inheritance)
- ISP: Minimal interface (init + validate)
- DIP: No external dependencies
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


class ValidationError(Exception):
    """Custom exception for configuration validation errors."""
    pass


@dataclass
class WritingStylePreset:
    """Single writing style preset configuration.

    Attributes:
        target_chars_per_episode: Target character count per episode
        target_average: Target average sentence length in characters
        dialogue_mode: Dialogue pacing mode (e.g., "tempo_driven")
        section_ratio: Section distribution ratio (e.g., [15, 70, 15])
    """
    target_chars_per_episode: int
    target_average: int
    dialogue_mode: str
    section_ratio: list[int] = field(default_factory=lambda: [15, 70, 15])

    def validate(self) -> None:
        """Validate preset configuration values.

        Raises:
            ValidationError: If any field contains invalid values

        Validation Rules:
            - target_chars_per_episode: 1000-20000
            - target_average: 10-100
            - dialogue_mode: non-empty string
            - section_ratio: sum must equal 100
        """
        if not (1000 <= self.target_chars_per_episode <= 20000):
            raise ValidationError(
                f"target_chars_per_episode must be 1000-20000, "
                f"got {self.target_chars_per_episode}"
            )

        if not (10 <= self.target_average <= 100):
            raise ValidationError(
                f"target_average must be 10-100, "
                f"got {self.target_average}"
            )

        if not self.dialogue_mode:
            raise ValidationError("dialogue_mode cannot be empty")

        if sum(self.section_ratio) != 100:
            raise ValidationError(
                f"section_ratio must sum to 100, "
                f"got {sum(self.section_ratio)}"
            )


@dataclass
class WritingStyleConfig:
    """Complete writing style configuration from .novelerrc.yaml.

    Attributes:
        active_preset: Name of active preset (e.g., "narou")
        presets: Dictionary of preset name → WritingStylePreset
    """
    active_preset: str
    presets: Dict[str, WritingStylePreset]

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "WritingStyleConfig":
        """Create WritingStyleConfig from dictionary.

        Args:
            config_dict: Dictionary containing writing_style section

        Returns:
            WritingStyleConfig instance

        Raises:
            ValidationError: If required fields are missing

        Example:
            >>> config = {
            ...     "active_preset": "narou",
            ...     "presets": {
            ...         "narou": {
            ...             "target_chars_per_episode": 4000,
            ...             "target_average": 38,
            ...             "dialogue_mode": "tempo_driven",
            ...             "section_ratio": [15, 70, 15]
            ...         }
            ...     }
            ... }
            >>> style_config = WritingStyleConfig.from_dict(config)
        """
        if "active_preset" not in config_dict:
            raise ValidationError("Missing required field: active_preset")

        if "presets" not in config_dict:
            raise ValidationError("Missing required field: presets")

        active_preset = config_dict["active_preset"]
        presets_raw = config_dict["presets"]

        # Convert dict presets to WritingStylePreset instances
        presets = {}
        for name, preset_data in presets_raw.items():
            presets[name] = WritingStylePreset(**preset_data)

        return cls(active_preset=active_preset, presets=presets)

    def validate(self) -> None:
        """Validate entire configuration.

        Raises:
            ValidationError: If configuration is invalid

        Validation Rules:
            - active_preset must exist in presets
            - All presets must pass their individual validation
        """
        if self.active_preset not in self.presets:
            raise ValidationError(
                f"active_preset '{self.active_preset}' "
                f"not found in presets: {list(self.presets.keys())}"
            )

        # Validate all presets
        for name, preset in self.presets.items():
            try:
                preset.validate()
            except ValidationError as e:
                raise ValidationError(
                    f"Preset '{name}' validation failed: {e}"
                ) from e

    def get_active_preset(self) -> WritingStylePreset:
        """Get the currently active preset.

        Returns:
            WritingStylePreset instance for active preset

        Raises:
            ValidationError: If active_preset doesn't exist

        Postcondition:
            Returned preset has passed validation
        """
        if self.active_preset not in self.presets:
            raise ValidationError(
                f"Active preset '{self.active_preset}' not found"
            )

        return self.presets[self.active_preset]
