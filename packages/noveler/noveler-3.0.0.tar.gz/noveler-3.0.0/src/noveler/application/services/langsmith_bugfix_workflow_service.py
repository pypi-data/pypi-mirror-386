"""Application.services.langsmith_bugfix_workflow_service
Where: Application service coordinating LangSmith-driven bugfix workflows.
What: Loads LangSmith runs to build artifacts, apply patches, and run verifications.
Why: Streamlines bugfix remediation so teams can reproduce, patch, and validate issues quickly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from noveler.domain.value_objects.langsmith_artifacts import (
    LangSmithBugfixArtifacts,
    PatchResult,
    VerificationResult,
)
from noveler.infrastructure.services.langsmith_artifact_manager import (
    LangSmithArtifactManager,
)
from noveler.presentation.shared.shared_utilities import (
    CommonPathService,
    console,
    get_common_path_service,
    get_logger,
)


class LangSmithBugfixWorkflowService:
    """Application service assisting with LangSmith bugfix workflows."""

    def __init__(
        self,
        artifact_manager: LangSmithArtifactManager | None = None,
        path_service: CommonPathService | None = None,
        logger=None,
        console_service=None,
    ) -> None:
        self.artifact_manager = artifact_manager or LangSmithArtifactManager()
        self.path_service = path_service or get_common_path_service()
        self.logger = logger or get_logger(__name__)
        self.console = console_service or console

    # === 成果物生成 ===
    def prepare_artifacts(
        self,
        run_json: Path | str,
        output_dir: Path | None = None,
        dataset_name: str | None = None,
        expected_behavior: str | None = None,
    ) -> LangSmithBugfixArtifacts:
        """Generate summary, prompt, and dataset artifacts from a LangSmith run.

        Args:
            run_json: Path to the LangSmith run metadata JSON.
            output_dir: Directory where artifacts should be written.
            dataset_name: Optional dataset name used when updating datasets.
            expected_behavior: Optional description of intended behaviour used in prompts.

        Returns:
            LangSmithBugfixArtifacts: Paths to the generated artifacts along with the run.
        """
        run = self.artifact_manager.load_run(run_json)

        resolved_output_dir = Path(output_dir) if output_dir else self._default_output_dir()
        self.path_service.ensure_directory_exists(resolved_output_dir)

        summary_path = self.artifact_manager.write_summary(run, resolved_output_dir)
        prompt_path = self.artifact_manager.write_prompt(run, resolved_output_dir, expected_behavior)

        dataset_path: Path | None = None
        if dataset_name:
            dataset_dir = self._dataset_dir()
            self.path_service.ensure_directory_exists(dataset_dir)
            dataset_path = dataset_dir / f"{dataset_name}.jsonl"
            dataset_path = self.artifact_manager.update_dataset(run, dataset_path, expected_behavior)

        self.console.print_success(f"LangSmithラン {run.run_id} の成果物を生成しました")
        self.logger.info("Generated LangSmith artifacts for run %s", run.run_id)

        return LangSmithBugfixArtifacts(
            run=run,
            summary_path=summary_path,
            prompt_path=prompt_path,
            dataset_entry_path=dataset_path,
        )

    def _dataset_dir(self) -> Path:
        management_dir = self.path_service.get_management_dir()
        return self._resolve_project_path(management_dir) / "quality_datasets"

    def _default_output_dir(self) -> Path:
        reports_dir = self.path_service.get_reports_dir()
        return self._resolve_project_path(reports_dir) / "langsmith"

    def _resolve_project_path(self, path: Path) -> Path:
        if path.is_absolute():
            return path
        return self.path_service.project_root / path

    # === パッチ適用 ===
    def apply_patch(
        self,
        patch_text: str,
        project_root: Path | None = None,
        strip: int = 1,
    ) -> PatchResult:
        """Apply a unified diff patch to the project tree."""
        target_root = Path(project_root) if project_root else self.path_service.project_root
        result = self.artifact_manager.apply_patch(patch_text, target_root, strip=strip)
        if result.applied:
            self.logger.info("Patch applied on %s", target_root)
        else:
            self.logger.warning("Patch failed on %s", target_root)
        return result

    # === 検証実行 ===
    def run_verification(
        self,
        command: Sequence[str],
        project_root: Path | None = None,
    ) -> VerificationResult:
        """Execute a verification command against the project root."""
        if not command:
            raise ValueError("command must not be empty")
        target_root = Path(project_root) if project_root else self.path_service.project_root
        verification = self.artifact_manager.run_command(command, target_root)
        if verification.succeeded:
            self.logger.info("Verification succeeded: %s", " ".join(command))
        else:
            self.logger.error("Verification failed: %s", verification.stderr)
        return verification

    # === ユーティリティ ===
    def read_patch_file(self, patch_file: Path | str) -> str:
        """Read a patch file from disk using UTF-8 encoding."""
        path = Path(patch_file)
        return path.read_text(encoding="utf-8")


__all__ = ["LangSmithBugfixWorkflowService"]
