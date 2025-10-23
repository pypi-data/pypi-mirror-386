# File: src/noveler/domain/interfaces/template_repository.py
# Purpose: Define repository interfaces for discovering and loading template files.
# Context: Used by template processors to locate YAML templates without embedding filesystem logic in the domain.

"""Purpose: Provide template discovery and loading interfaces for domain services.
Context: Supports dependency inversion by abstracting template file retrieval and loading.
Side Effects: None within the interface declarations.
"""

from pathlib import Path
from typing import Protocol


class ITemplateRepository(Protocol):
    """Purpose: Describe operations for locating and loading template files.

    Side Effects:
        Implementations may interact with the filesystem when searching for templates.
    """

    def find_template(self, step_id: int, step_slug: str) -> Path | None:
        """Purpose: Find a template file path for the given step identifier and slug.

        Args:
            step_id: Numeric step identifier.
            step_slug: Human-readable slug describing the step.

        Returns:
            Path to the template file when found; otherwise None.

        Side Effects:
            Implementation defined; may perform filesystem searches.
        """

    def load_template_content(self, template_path: Path) -> str:
        """Purpose: Load template file content as text.

        Args:
            template_path: Filesystem path to the template file.

        Returns:
            Template content as a UTF-8 encoded string.

        Raises:
            FileNotFoundError: When the template path does not exist.
            UnicodeDecodeError: When the file is not valid UTF-8.
            OSError: When the file cannot be read due to permissions or I/O errors.

        Side Effects:
            Implementation defined; reads from disk.
        """
