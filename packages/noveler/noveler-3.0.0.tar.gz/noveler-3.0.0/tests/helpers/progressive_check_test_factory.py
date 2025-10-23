"""Test factory for creating ProgressiveCheckManager instances in tests.

This helper maintains backward compatibility with existing tests while
using the new Application layer factory pattern.
"""

from pathlib import Path
from typing import Any, Callable

from noveler.domain.interfaces.logger_interface import ILogger
from noveler.domain.services.progressive_check_manager import ProgressiveCheckManager
from noveler.infrastructure.logging.unified_logger import get_logger
from noveler.infrastructure.repositories.progressive_check import (
    FileStateRepository,
    FileManifestRepository,
    FileStepIORepository,
    FileCheckTemplateRepository,
    FileConfigRepository,
)


def create_test_progressive_check_manager(
    project_root: str | Path,
    episode_number: int,
    logger: ILogger | None = None,
    session_id: str | None = None,
    resume: bool = False,
    manifest: dict[str, Any] | None = None,
    prompt_templates_dir: Path | None = None,
    **kwargs: Any,
) -> ProgressiveCheckManager:
    """Create ProgressiveCheckManager for testing with all dependencies injected.

    This factory function provides backward compatibility for existing tests
    while using the new dependency injection pattern.

    Args:
        project_root: Project root directory
        episode_number: Episode number to check
        logger: Optional logger (defaults to test logger)
        session_id: Optional session ID for resuming
        resume: Whether to resume from existing session
        manifest: Optional pre-loaded manifest
        prompt_templates_dir: Optional templates directory
        **kwargs: Additional arguments passed to ProgressiveCheckManager

    Returns:
        Configured ProgressiveCheckManager instance
    """
    project_root = Path(project_root)

    # Setup logger
    if logger is None:
        logger = get_logger(__name__)

    # Setup repositories
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
        state_repo=state_repo,
        manifest_repo=manifest_repo,
        step_io_repo=step_io_repo,
        template_repo=template_repo,
        config_repo=config_repo,
        prompt_templates_dir=prompt_templates_dir,
        session_id=session_id,
        resume=resume,
        manifest=manifest,
        **kwargs,
    )

    return manager
