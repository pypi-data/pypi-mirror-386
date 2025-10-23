"""Tests.tests.unit.infrastructure.services.test_langsmith_artifact_manager
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

import json
from pathlib import Path

import pytest

from noveler.domain.value_objects.langsmith_artifacts import (
    LangSmithRun,
)
from noveler.infrastructure.services.langsmith_artifact_manager import (
    LangSmithArtifactManager,
)


@pytest.fixture()
def sample_run(tmp_path: Path) -> Path:
    run_payload = {
        "id": "run-123",
        "name": "quality-check",
        "status": "error",
        "error": {
            "message": "ValueError: invalid input",
            "stack": "Traceback...",
        },
        "inputs": {"text": "example"},
        "outputs": {"result": None},
        "metadata": {"dataset": "regression"},
        "url": "https://smith.langchain.com/runs/run-123",
        "tags": ["quality", "regression"],
    }
    run_file = tmp_path / "run.json"
    run_file.write_text(json.dumps(run_payload), encoding="utf-8")
    return run_file


def test_load_run_builds_domain_object(sample_run: Path) -> None:
    manager = LangSmithArtifactManager()

    run = manager.load_run(sample_run)

    assert isinstance(run, LangSmithRun)
    assert run.run_id == "run-123"
    assert run.name == "quality-check"
    assert run.error == "ValueError: invalid input"
    assert run.trace_url.endswith("run-123")
    assert run.inputs == {"text": "example"}
    assert run.tags == ["quality", "regression"]


def test_update_dataset_appends_unique_entries(tmp_path: Path) -> None:
    manager = LangSmithArtifactManager()
    run = LangSmithRun(
        run_id="run-123",
        name="quality-check",
        status="error",
        error="ValueError: invalid input",
        trace_url="https://smith.langchain.com/runs/run-123",
        inputs={"text": "example"},
        outputs={"result": None},
        metadata={"dataset": "regression"},
        tags=["quality"],
    )
    dataset_path = tmp_path / "dataset" / "langsmith_quality.jsonl"

    first_path = manager.update_dataset(run, dataset_path)
    second_path = manager.update_dataset(run, dataset_path)

    assert first_path == dataset_path
    assert second_path == dataset_path
    entries = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines()]
    assert len(entries) == 1
    assert entries[0]["run_id"] == "run-123"
    assert entries[0]["inputs"] == {"text": "example"}


def test_apply_patch_updates_target_file(tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    target.write_text("print('before')\n", encoding="utf-8")
    patch_text = """diff --git a/module.py b/module.py\nindex 1111111..2222222 100644\n--- a/module.py\n+++ b/module.py\n@@ -1 +1 @@\n-print('before')\n+print('after')\n"""
    manager = LangSmithArtifactManager()

    result = manager.apply_patch(patch_text, tmp_path, strip=1)

    assert result.applied is True
    assert "patch" in result.command[0]
    assert target.read_text(encoding="utf-8").strip() == "print('after')"
