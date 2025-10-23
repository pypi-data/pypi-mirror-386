"""Simplified deploy scripts use case for unit tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from noveler.domain.deployment.entities import (
    Deployment,
    DeploymentMode,
    DeploymentStatus,
    DeploymentTarget,
)
from noveler.domain.deployment.value_objects import CommitHash
from noveler.domain.value_objects.project_time import project_now


@dataclass
class DeployScriptsRequest:
    """Parameters that control how deployment scripts are executed.

    Attributes:
        targets: Optional collection of deployment targets to process.
        mode: Deployment mode that should be applied to every deployment.
        force: When True, continue despite validation failures.
    """

    targets: Optional[Iterable[DeploymentTarget]] = None
    mode: DeploymentMode = DeploymentMode.PRODUCTION
    force: bool = False


@dataclass
class DeployScriptsResult:
    """Result returned by the deployment use case.

    Attributes:
        success: Indicates whether all deployments finished successfully.
        deployments: Deployment records generated during execution.
        total_time: Total time spent executing the deployments in seconds.
        error_message: Optional message describing a failure.
    """

    success: bool
    deployments: List[Deployment] = field(default_factory=list)
    total_time: float = 0.0
    error_message: Optional[str] = None


class DeployScriptsUseCase:
    """Coordinate deployment service and repositories to deploy scripts."""

    def __init__(self, deployment_repo, deployment_service, version_service) -> None:
        self._deployment_repo = deployment_repo
        self._deployment_service = deployment_service
        self._version_service = version_service

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def execute(self, request: DeployScriptsRequest | None = None, **kwargs) -> DeployScriptsResult:
        """Execute deployments for the provided targets.

        Args:
            request: Deployment parameters; if omitted, kwargs are used.
            **kwargs: Fallback keyword arguments to construct a request.

        Returns:
            DeployScriptsResult: Aggregated deployment information.
        """
        if request is None:
            request = DeployScriptsRequest(**kwargs)

        start_time = project_now().datetime
        deployments: List[Deployment] = []

        try:
            targets = list(request.targets) if request.targets is not None else list(self._deployment_service.find_deployable_projects())
            if not targets:
                return DeployScriptsResult(success=False, error_message="No deployable projects found")

            for target in targets:
                deployment = self._deploy_to_target(target, request.mode, request.force)
                deployments.append(deployment)
                if deployment.status == DeploymentStatus.FAILED and not request.force:
                    self._rollback_deployments(deployments)
                    return DeployScriptsResult(
                        success=False,
                        deployments=deployments,
                        total_time=(project_now().datetime - start_time).total_seconds(),
                        error_message=deployment.error_message or "Deployment failed",
                    )

            total_time = (project_now().datetime - start_time).total_seconds()
            return DeployScriptsResult(success=True, deployments=deployments, total_time=total_time)
        except Exception as exc:  # pragma: no cover - defensive
            self._rollback_deployments(deployments)
            return DeployScriptsResult(
                success=False,
                deployments=deployments,
                total_time=(project_now().datetime - start_time).total_seconds(),
                error_message=str(exc),
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _deploy_to_target(self, target: DeploymentTarget, mode: DeploymentMode, force: bool) -> Deployment:
        """Trigger a deployment workflow for a single target."""
        deployment = self._deployment_service.create_deployment(target, mode)

        is_ready, issues = self._deployment_service.validate_deployment_readiness(deployment)
        if not is_ready and not force:
            deployment.fail(f"Validation failed: {', '.join(issues)}")
            self._deployment_repo.save(deployment)
            return deployment

        try:
            deployment.start()
            self._deployment_repo.save(deployment)
            self._perform_deployment(deployment)
            deployment.complete()
        except Exception as exc:
            deployment.fail(str(exc))
        finally:
            self._deployment_repo.save(deployment)

        return deployment

    def _perform_deployment(self, deployment: Deployment) -> None:
        """Hook patched by tests; by default does nothing."""
        # Simulate minimal work by touching version info if available
        if hasattr(self._version_service, "get_current_commit"):
            commit = self._version_service.get_current_commit()
            if commit:
                deployment.source_commit = CommitHash(str(commit))

    def _rollback_deployments(self, deployments: Iterable[Deployment]) -> None:
        """Rollback deployments that finished before a failure."""
        for deployment in deployments:
            if deployment.status == DeploymentStatus.COMPLETED:
                deployment.status = DeploymentStatus.ROLLED_BACK
            elif deployment.status not in (DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK):
                deployment.fail("Rolled back due to previous failure")
            self._deployment_repo.save(deployment)
