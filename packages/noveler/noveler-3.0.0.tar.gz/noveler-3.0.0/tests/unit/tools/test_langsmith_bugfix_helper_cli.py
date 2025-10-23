"""Tests.tests.unit.tools.test_langsmith_bugfix_helper_cli
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

import json
from pathlib import Path

from noveler.tools.langsmith_bugfix_helper import main


def create_run_file(project_root: Path) -> Path:
    payload = {
        "id": "run-789",
        "name": "quality-bug",
        "status": "error",
        "error": {"message": "RuntimeError", "stack": "Traceback"},
        "inputs": {"text": "bar"},
        "outputs": {"result": None},
        "metadata": {"dataset": "quality"},
        "url": "https://smith.langchain.com/runs/run-789",
        "tags": ["quality"],
    }
    run_json = project_root / "run.json"
    run_json.write_text(json.dumps(payload), encoding="utf-8")
    return run_json


def test_cli_summarize_creates_artifacts(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    run_json = create_run_file(project_root)
    output_dir = project_root / "reports" / "langsmith"

    exit_code = main(
        [
            "summarize",
            "--run-json",
            str(run_json),
            "--project-root",
            str(project_root),
            "--output-dir",
            str(output_dir),
            "--dataset-name",
            "quality_dataset",
            "--expected-behavior",
            "Quality bug should be resolved",
        ]
    )

    assert exit_code == 0
    summary_files = list(output_dir.glob("*_summary.md"))
    prompt_files = list(output_dir.glob("*_prompt.txt"))
    assert summary_files and prompt_files
    dataset_file = project_root / "50_管理資料" / "quality_datasets" / "quality_dataset.jsonl"
    assert dataset_file.exists()
    assert "run-789" in dataset_file.read_text(encoding="utf-8")


def test_cli_apply_and_verify(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    target = project_root / "module.py"
    target.write_text("print('before')\n", encoding="utf-8")
    patch_text = """diff --git a/module.py b/module.py\nindex 1111111..2222222 100644\n--- a/module.py\n+++ b/module.py\n@@ -1 +1 @@\n-print('before')\n+print('after')\n"""
    patch_file = project_root / "patch.diff"
    patch_file.write_text(patch_text, encoding="utf-8")

    apply_exit = main(
        [
            "apply",
            "--patch-file",
            str(patch_file),
            "--project-root",
            str(project_root),
            "--strip",
            "1",
        ]
    )
    assert apply_exit == 0
    assert target.read_text(encoding="utf-8").strip() == "print('after')"

    verify_exit = main(
        [
            "verify",
            "--project-root",
            str(project_root),
            "--",
            "python",
            "-c",
            "print('ok')",
        ]
    )
    assert verify_exit == 0
