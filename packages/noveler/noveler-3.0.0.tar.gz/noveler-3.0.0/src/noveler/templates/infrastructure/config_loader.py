"""Configuration Loader - .novelerrc.yaml file I/O operations.

Infrastructure Layer: Handles external I/O (file system access).
Responsible for: Reading .novelerrc.yaml and extracting active preset

SOLID Principles:
- SRP: Single responsibility (config file loading only)
- OCP: Open for extension (can support other config formats)
- LSP: N/A (no inheritance)
- ISP: Minimal interface (load + extract_active_preset)
- DIP: Depends on Domain abstractions (WritingStyleConfig)
"""

from pathlib import Path
from typing import Dict, Any
import yaml

from ..domain.config_schema import WritingStyleConfig, ValidationError


class ConfigLoader:
    """Loads and parses .novelerrc.yaml configuration file.

    This class handles file I/O and delegates validation to Domain layer.

    Attributes:
        config_filename: Name of configuration file (default: ".novelerrc.yaml")
    """

    def __init__(self, config_filename: str = ".novelerrc.yaml") -> None:
        """Initialize ConfigLoader.

        Args:
            config_filename: Configuration file name (default: .novelerrc.yaml)
        """
        self.config_filename = config_filename

    def load(self, project_root: Path) -> Dict[str, Any]:
        """Load .novelerrc.yaml from project root.

        Args:
            project_root: Path to project root directory

        Returns:
            Dictionary containing full YAML content

        Raises:
            FileNotFoundError: If .novelerrc.yaml doesn't exist
            yaml.YAMLError: If YAML parsing fails

        Precondition:
            - project_root is a valid directory
            - project_root/.novelerrc.yaml exists

        Postcondition:
            - Returns dictionary containing YAML content
            - File is closed properly
        """
        config_path = project_root / self.config_filename

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Please create .novelerrc.yaml in project root"
            )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                raise ValidationError(
                    f"Invalid .novelerrc.yaml: root must be a dict, "
                    f"got {type(config)}"
                )

            return config

        except yaml.YAMLError as e:
            raise yaml.YAMLError(
                f"Failed to parse {config_path}: {e}"
            ) from e

    def extract_active_preset(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract active preset settings from loaded configuration.

        Args:
            config: Full configuration dictionary from load()

        Returns:
            Dictionary containing active preset settings

        Raises:
            ValidationError: If writing_style section or active preset missing

        Precondition:
            - config contains "writing_style" key
            - writing_style contains "active_preset" and "presets"

        Postcondition:
            - Returns settings dict for active preset
            - Settings are validated by WritingStyleConfig

        Example:
            >>> config = loader.load(project_root)
            >>> active_settings = loader.extract_active_preset(config)
            >>> active_settings["target_average"]
            38
        """
        if "writing_style" not in config:
            raise ValidationError(
                "Missing 'writing_style' section in .novelerrc.yaml"
            )

        writing_style = config["writing_style"]

        # Validate using Domain schema
        style_config = WritingStyleConfig.from_dict(writing_style)
        style_config.validate()

        # Return active preset settings as dict
        active_preset = style_config.get_active_preset()

        return {
            "target_chars_per_episode": active_preset.target_chars_per_episode,
            "target_average": active_preset.target_average,
            "dialogue_mode": active_preset.dialogue_mode,
            "section_ratio": active_preset.section_ratio,
        }

    def get_config_mtime(self, project_root: Path) -> float:
        """Get modification time of .novelerrc.yaml for cache invalidation.

        Args:
            project_root: Path to project root directory

        Returns:
            Modification timestamp (seconds since epoch)

        Raises:
            FileNotFoundError: If config file doesn't exist

        Usage:
            Used by TemplateRenderer to detect config changes and
            invalidate cache when needed.
        """
        config_path = project_root / self.config_filename

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        return config_path.stat().st_mtime
