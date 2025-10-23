"""Lightweight deployment domain service for tests."""

from __future__ import annotations

from typing import Iterable, Tuple, List

from noveler.domain.deployment.entities import (
    Deployment,
    DeploymentMode,
    DeploymentTarget,
)
from noveler.domain.deployment.value_objects import CommitHash


class DeploymentService:
    """Facade that coordinates deployment prerequisites via repositories."""

    def __init__(self, git_repository, project_repository) -> None:
        self._git_repository = git_repository
        self._project_repository = project_repository

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------
    def check_uncommitted_changes(self) -> Tuple[bool, List[str]]:
        """Return whether uncommitted changes exist and the associated files."""
        has_changes = bool(self._git_repository.has_uncommitted_changes())
        files: List[str] = []
        if has_changes:
            getter = getattr(self._git_repository, "get_uncommitted_files", None)
            if callable(getter):
                value = getter()
                if isinstance(value, (list, tuple, set)):
                    files = list(value)
                else:
                    # fall back to empty list when mocks return non-iterable placeholders
                    files = []
        return has_changes, files

    def find_deployable_projects(self) -> Iterable[DeploymentTarget]:
        """Delegate to the project repository to enumerate deployable projects."""
        projects = self._project_repository.find_all_projects()
        return list(projects)

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def validate_deployment_readiness(self, deployment: Deployment) -> Tuple[bool, List[str]]:
        """Ensure the deployment has no obvious blockers."""
        issues: List[str] = []

        has_changes, files = self.check_uncommitted_changes()
        if has_changes:
            issues.append("Uncommitted changes detected")
            if files:
                issues.append(
                    "Uncommitted files: " + ", ".join(files[:5]) + ("..." if len(files) > 5 else "")
                )

        if hasattr(self._project_repository, "project_exists"):
            if not self._project_repository.project_exists(deployment.target.project_path):
                issues.append("Project directory does not exist")

        issues.extend(deployment.target.validate())

        return len(issues) == 0, issues

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    def create_deployment(self, target: DeploymentTarget, mode: DeploymentMode) -> Deployment:
        """Create a deployment entity using the current commit hash."""
        commit_value = "0" * 7
        if hasattr(self._git_repository, "get_current_commit"):
            commit = self._git_repository.get_current_commit()
            commit_value = str(commit)
        return Deployment(
            target=target,
            mode=mode,
            source_commit=CommitHash(commit_value),
        )
