# File: src/noveler/infrastructure/repositories/progressive_check/file_template_repository.py
# Purpose: File-based template repository implementation
# Context: Phase 5 - Infrastructure layer I/O implementations

"""File-based template repository implementation.

Provides file-based YAML template loading for Progressive Check system.
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger


class FileCheckTemplateRepository:
    """File-based Progressive Check template loading.

    Implementation of ICheckTemplateRepository protocol using YAML files.

    File Location:
        - templates/ directory (relative to project root or absolute)
        - Configurable via templates_dir parameter
    """

    def __init__(
        self,
        project_root: Path,
        templates_dir: Path | None = None,
        logger: ILogger | None = None
    ):
        """Initialize file template repository.

        Args:
            project_root: Project root directory
            templates_dir: Templates directory (defaults to project_root/templates)
            logger: Optional logger (defaults to NullLogger)
        """
        self.project_root = project_root
        self.templates_dir = templates_dir or (project_root / "templates")
        self.logger = logger or NullLogger()

    def load_template(self, template_name: str) -> dict[str, Any] | None:
        """Load YAML template file.

        Args:
            template_name: Template filename (e.g., "check_step01_typo_check.yaml")

        Returns:
            Parsed YAML content as dict if found, None otherwise

        Side Effects:
            - Reads from file system
            - Parses YAML content
            - Logs warning if template not found or invalid
        """
        template_path = self._resolve_template_path(template_name)

        if template_path is None or not template_path.exists():
            self.logger.warning(f"Template not found: {template_name}")
            return None

        try:
            with template_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    self.logger.warning(f"Invalid template format (not dict): {template_path}")
                    return None
                # Store the resolved source directory for metadata collection
                source_info = self._get_source_from_path(template_path)
                data["_resolved_source"] = source_info
                return data
        except yaml.YAMLError as e:
            self.logger.warning(f"Failed to parse template YAML: {template_path}, error: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"Failed to load template: {template_path}, error: {e}")
            return None

    def _get_source_from_path(self, template_path: Path) -> str:
        """Determine source directory from resolved template path.

        Args:
            template_path: Resolved template path

        Returns:
            Source identifier (e.g., "checks", "checks_backup", "writing")
        """
        try:
            relative_path = template_path.relative_to(self.templates_dir)
            parts = relative_path.parts
            if len(parts) > 1:
                # Extract subdirectory structure
                if parts[0] == "quality":
                    if len(parts) > 2 and parts[1] == "checks":
                        if parts[2] == "backup":
                            return "checks_backup"
                        return "checks"
                elif parts[0] == "writing":
                    return "writing"
                elif parts[0] == "check_steps":
                    return "check_steps"
                elif parts[0] == "progressive_check":
                    return "progressive_check"
        except ValueError:
            # Path is not relative to templates_dir
            pass
        return "template_repository"

    def template_exists(self, template_name: str) -> bool:
        """Check if template file exists.

        Args:
            template_name: Template filename

        Returns:
            True if template file exists, False otherwise
        """
        template_path = self._resolve_template_path(template_name)
        return template_path is not None and template_path.exists()

    def _resolve_template_path(self, template_name: str) -> Path | None:
        """Resolve template name to file path.

        Args:
            template_name: Template filename or relative path

        Returns:
            Resolved Path if template can be found, None otherwise

        Resolution Strategy:
            1. Check templates_dir/template_name (exact match)
            2. Check templates_dir subdirectories (exact match)
            3. Try with .yaml extension if not found
            4. Search with wildcard pattern (e.g., check_step01*.yaml)
            5. Return None if not found
        """
        # Try exact match first
        direct_path = self.templates_dir / template_name
        if direct_path.exists():
            return direct_path

        # Try common subdirectories with exact name
        subdirs = ["check_steps", "progressive_check", "quality/checks", "quality/checks/backup", "writing"]
        for subdir in subdirs:
            candidate = self.templates_dir / subdir / template_name
            if candidate.exists():
                return candidate

        # Try adding .yaml extension if not present
        if not template_name.endswith((".yaml", ".yml")):
            yaml_name = f"{template_name}.yaml"
            direct_yaml = self.templates_dir / yaml_name
            if direct_yaml.exists():
                return direct_yaml

            for subdir in subdirs:
                candidate_yaml = self.templates_dir / subdir / yaml_name
                if candidate_yaml.exists():
                    return candidate_yaml

        # Try wildcard search (e.g., check_step01*.yaml)
        if not template_name.endswith((".yaml", ".yml")):
            pattern = f"{template_name}*.yaml"
            # Search in templates_dir root
            matches = list(self.templates_dir.glob(pattern))
            if matches:
                return matches[0]

            # Search in subdirectories
            for subdir in subdirs:
                subdir_path = self.templates_dir / subdir
                if subdir_path.exists():
                    matches = list(subdir_path.glob(pattern))
                    if matches:
                        return matches[0]

        return None
