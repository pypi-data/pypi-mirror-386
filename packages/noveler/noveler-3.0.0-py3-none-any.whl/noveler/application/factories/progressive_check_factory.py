"""Factory for creating ProgressiveCheckManager with infrastructure dependencies.

This module belongs to the Application layer and is responsible for
assembling ProgressiveCheckManager instances with concrete infrastructure
implementations, maintaining DDD layer separation.
"""

from pathlib import Path
from typing import Any

from noveler.domain.interfaces.logger_interface import ILogger
from noveler.domain.services.progressive_check_manager import ProgressiveCheckManager
from noveler.infrastructure.repositories.progressive_check import (
    FileStateRepository,
    FileManifestRepository,
    FileStepIORepository,
    FileCheckTemplateRepository,
    FileConfigRepository,
)


def create_progressive_check_manager(
    project_root: Path,
    episode_number: int,
    logger: ILogger,
    session_id: str | None = None,
    resume: bool = False,
    dry_run: bool = False,
    prompt_templates_dir: Path | None = None,
) -> ProgressiveCheckManager:
    """Create a ProgressiveCheckManager with infrastructure dependencies injected.

    This factory function assembles all necessary infrastructure components
    and injects them into the domain service, maintaining clean architecture
    boundaries.

    Args:
        project_root: Project root directory
        episode_number: Episode number to check
        logger: Logger instance (must be provided)
        session_id: Optional session ID for resuming
        resume: Whether to resume from existing session
        dry_run: Whether to run in dry-run mode
        prompt_templates_dir: Directory containing prompt templates
            (defaults to project_root / "templates")

    Returns:
        Configured ProgressiveCheckManager instance

    Raises:
        ImportError: If infrastructure repositories not available
    """
    # Setup infrastructure repositories
    state_repo = FileStateRepository(project_root, logger)
    manifest_repo = FileManifestRepository(project_root, logger)
    step_io_repo = FileStepIORepository(project_root, logger)
    template_repo = FileCheckTemplateRepository(project_root, logger=logger)
    config_repo = FileConfigRepository(project_root, logger=logger)

    # Determine templates directory
    if prompt_templates_dir is None:
        prompt_templates_dir = project_root / "templates"

    # Create manager with injected dependencies
    manager = ProgressiveCheckManager(
        project_root=project_root,
        episode_number=episode_number,
        logger=logger,
        session_id=session_id,
        resume=resume,
        dry_run=dry_run,
        state_repo=state_repo,
        manifest_repo=manifest_repo,
        step_io_repo=step_io_repo,
        template_repo=template_repo,
        config_repo=config_repo,
        prompt_templates_dir=prompt_templates_dir,
    )

    return manager
