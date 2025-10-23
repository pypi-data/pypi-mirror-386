"""Tests.tests.unit.application.services.test_langsmith_bugfix_workflow_service
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

import json
from pathlib import Path

import pytest

from noveler.application.services.langsmith_bugfix_workflow_service import (
    LangSmithBugfixWorkflowService,
)
from noveler.domain.value_objects.langsmith_artifacts import (
    LangSmithBugfixArtifacts,
)
from noveler.infrastructure.services.langsmith_artifact_manager import (
    LangSmithArtifactManager,
)
from noveler.presentation.shared.shared_utilities import CommonPathService


@pytest.fixture()
def run_json(tmp_path: Path) -> Path:
    run_payload = {
        "id": "run-456",
        "name": "quality-eval",
        "status": "error",
        "error": {
            "message": "AssertionError: expected 1", "stack": "Traceback..."
        },
        "inputs": {"text": "foo"},
        "outputs": {"result": 0},
        "metadata": {"dataset": "quality"},
        "url": "https://smith.langchain.com/runs/run-456",
        "tags": ["regression"],
    }
    run_file = tmp_path / "run.json"
    run_file.write_text(json.dumps(run_payload), encoding="utf-8")
    return run_file


def test_prepare_artifacts_creates_summary_and_dataset(tmp_path: Path, run_json: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    path_service = CommonPathService(project_root)
    artifact_manager = LangSmithArtifactManager()
    service = LangSmithBugfixWorkflowService(
        artifact_manager=artifact_manager,
        path_service=path_service,
    )
    output_dir = project_root / "reports" / "langsmith"

    artifacts = service.prepare_artifacts(
        run_json,
        output_dir=output_dir,
        dataset_name="quality_regression",
        expected_behavior="Quality evaluation should return 1",
    )

    assert isinstance(artifacts, LangSmithBugfixArtifacts)
    assert artifacts.summary_path.exists()
    assert artifacts.prompt_path.exists()
    assert artifacts.dataset_entry_path is not None
    dataset_content = artifacts.dataset_entry_path.read_text(encoding="utf-8")
    assert "run-456" in dataset_content
    summary_content = artifacts.summary_path.read_text(encoding="utf-8")
    assert "AssertionError" in summary_content
    prompt_content = artifacts.prompt_path.read_text(encoding="utf-8")
    assert "Quality evaluation should return 1" in prompt_content


def test_apply_patch_and_verify_expose_results(tmp_path: Path) -> None:
    project_root = tmp_path / "workspace"
    project_root.mkdir()
    target = project_root / "app.py"
    target.write_text("print('before')\n", encoding="utf-8")

    service = LangSmithBugfixWorkflowService(
        artifact_manager=LangSmithArtifactManager(),
        path_service=CommonPathService(project_root),
    )

    patch_text = """diff --git a/app.py b/app.py\nindex 1111111..2222222 100644\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-print('before')\n+print('after')\n"""
    patch_result = service.apply_patch(patch_text, project_root=project_root, strip=1)
    assert patch_result.applied is True
    assert target.read_text(encoding="utf-8").strip() == "print('after')"

    verification = service.run_verification(
        ["python", "-c", "print('ok')"], project_root=project_root
    )
    assert verification.returncode == 0
    assert "ok" in verification.stdout
