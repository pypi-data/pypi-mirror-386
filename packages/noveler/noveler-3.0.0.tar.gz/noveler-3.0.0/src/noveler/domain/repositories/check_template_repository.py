# File: src/noveler/domain/repositories/check_template_repository.py
# Purpose: Repository protocol for Progressive Check template loading
# Context: Phase 5 - Separate I/O from Domain layer

"""Repository protocol for Progressive Check YAML template loading.

This module defines the Protocol interface for loading YAML template files
used by ProgressiveCheckManager. Concrete implementations are in Infrastructure layer.
"""

from typing import Any, Protocol


class ICheckTemplateRepository(Protocol):
    """Progressive Check template file loading interface.

    Responsibilities:
        - Load YAML template files for check steps
        - Check template existence
        - Parse YAML content to dict

    Template Types:
        - check_step*.yaml: Step-specific check templates
        - Custom templates as needed

    File Location:
        - templates/ directory (configurable per implementation)
    """

    def load_template(self, template_name: str) -> dict[str, Any] | None:
        """Load YAML template file.

        Args:
            template_name: Template filename (e.g., "check_step01_typo_check.yaml")
                or template path relative to templates directory

        Returns:
            Parsed YAML content as dict if found, None otherwise

        Side Effects:
            - Reads from file system
            - Parses YAML content
            - May log warnings if template invalid or not found

        Examples:
            >>> repo.load_template("check_step01_typo_check.yaml")
            {"name": "誤字脱字チェック", "prompt": "...", ...}

            >>> repo.load_template("nonexistent.yaml")
            None
        """
        ...

    def template_exists(self, template_name: str) -> bool:
        """Check if template file exists.

        Args:
            template_name: Template filename or relative path

        Returns:
            True if template file exists, False otherwise

        Side Effects:
            - Checks file system existence

        Examples:
            >>> repo.template_exists("check_step01_typo_check.yaml")
            True

            >>> repo.template_exists("nonexistent.yaml")
            False
        """
        ...
