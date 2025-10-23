"""Domain repository interfaces and compatibility exports.

This module re-exports the most commonly consumed repository types so that
legacy imports (e.g. ``from noveler.domain.repositories import
IStateRepository``) continue to function after repository modules were
re-organised.  Centralising the exports also keeps ``__all__`` accurate for the
pytest ``--strict-config`` setup used across the project.
"""

from noveler.domain.repositories.file_system_repository import FileSystemRepository
from noveler.domain.repositories.manuscript_plot_link_repository import ManuscriptPlotLinkRepository
from noveler.domain.repositories.plot_progress_repository import PlotProgressRepository
from noveler.domain.repositories.plot_version_repository import PlotVersionRepository

# Progressive check repository protocols
from noveler.domain.repositories.check_state_repository import (
    IManifestRepository,
    IStepIORepository,
    IStateRepository,
)
from noveler.domain.repositories.check_template_repository import ICheckTemplateRepository
from noveler.domain.repositories.config_repository import IConfigRepository

__all__ = [
    # Legacy concrete repositories
    "FileSystemRepository",
    "ManuscriptPlotLinkRepository",
    "PlotProgressRepository",
    "PlotVersionRepository",
    # Progressive check protocols
    "IStateRepository",
    "IManifestRepository",
    "IStepIORepository",
    "ICheckTemplateRepository",
    "IConfigRepository",
]
