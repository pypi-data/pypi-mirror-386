# File: src/noveler/infrastructure/repositories/file_template_repository.py
# Purpose: File system-based template discovery and loading
# Context: Extracted from ProgressiveCheckManager._resolve_template_path and _load_prompt_template

from pathlib import Path

from noveler.infrastructure.logging.unified_logger import get_logger

logger = get_logger(__name__)


class FileTemplateRepository:
    """File system-based implementation of ITemplateRepository.

    Responsibilities:
        - Search for YAML template files in multiple directories
        - Load template content with UTF-8 encoding
        - Provide graceful degradation on file not found

    Template file naming convention:
        check_step{step_id:02d}_{step_slug}.yaml

    Search order:
        1. {templates_dir}/quality/checks/
        2. {templates_dir}/quality/checks/backup/
        3. {templates_dir}/writing/
    """

    def __init__(self, templates_dir: Path) -> None:
        """Initialize repository with base templates directory.

        Args:
            templates_dir: Root directory containing template subdirectories
                Expected structure:
                    templates_dir/
                        quality/
                            checks/
                                check_step01_typo_check.yaml
                            checks/backup/
                                check_step02_consistency.yaml
                        writing/
                            check_step03_pacing.yaml
        """
        self._templates_dir = templates_dir

    def find_template(self, step_id: int, step_slug: str) -> Path | None:
        """Find template file by searching multiple directories.

        Search strategy (first match wins):
            1. quality/checks/check_step{step_id:02d}_{step_slug}.yaml
            2. quality/checks/backup/check_step{step_id:02d}_{step_slug}.yaml
            3. writing/check_step{step_id:02d}_{step_slug}.yaml

        Args:
            step_id: Step number (e.g., 1 → "01")
            step_slug: Step identifier slug (e.g., "typo_check")

        Returns:
            Path to found template file, or None if not found in any directory

        Side Effects:
            Logs debug message if template not found
        """
        template_filename = f"check_step{step_id:02d}_{step_slug}.yaml"

        search_directories = [
            self._templates_dir / "quality" / "checks",
            self._templates_dir / "quality" / "checks" / "backup",
            self._templates_dir / "writing",
        ]

        for directory in search_directories:
            template_path = directory / template_filename
            if template_path.exists():
                logger.debug("Found template: %s", template_path)
                return template_path

        logger.debug(
            "Template not found in any search directory: %s (searched: %s)",
            template_filename,
            [str(d) for d in search_directories],
        )
        return None

    def load_template_content(self, template_path: Path) -> str:
        """Load template file content as UTF-8 string.

        Args:
            template_path: Absolute path to YAML template file

        Returns:
            Template file content as string

        Raises:
            FileNotFoundError: If template_path does not exist
            UnicodeDecodeError: If file is not valid UTF-8
            OSError: If file cannot be read (permissions, I/O error)

        Side Effects:
            Logs debug message on successful load
        """
        if not template_path.exists():
            raise FileNotFoundError(f"Template file does not exist: {template_path}")

        try:
            with template_path.open("r", encoding="utf-8") as f:
                content = f.read()
            logger.debug("Loaded template content: %s (%d bytes)", template_path, len(content))
            return content
        except UnicodeDecodeError as e:
            logger.error("Template file is not valid UTF-8: %s", template_path)
            raise
        except OSError as e:
            logger.error("Failed to read template file: %s - %s", template_path, e)
            raise
