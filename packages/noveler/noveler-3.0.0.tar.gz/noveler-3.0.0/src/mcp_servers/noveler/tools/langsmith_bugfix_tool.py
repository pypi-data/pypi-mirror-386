"""LangSmithバグ修正ワークフローをMCPツールとして公開するヘルパー"""
from __future__ import annotations

import json
import shlex
import shutil
import tempfile
from pathlib import Path
from typing import Any, Sequence

from noveler.application.services.langsmith_bugfix_workflow_service import (
    LangSmithBugfixWorkflowService,
)
from noveler.presentation.shared.shared_utilities import CommonPathService


def _build_service(project_root: str | None) -> LangSmithBugfixWorkflowService:
    path_service = CommonPathService(Path(project_root).expanduser()) if project_root else None
    return LangSmithBugfixWorkflowService(path_service=path_service)


def generate_langsmith_artifacts(
    *,
    run_json_path: str | None = None,
    run_json_content: Any | None = None,
    output_dir: str | None = None,
    dataset_name: str | None = None,
    expected_behavior: str | None = None,
    project_root: str | None = None,
) -> dict[str, Any]:
    """LangSmithのrun情報から成果物を生成し、MCPレスポンス形式で返す"""
    if not run_json_path and run_json_content is None:
        raise ValueError("run_json_path か run_json_content のいずれかを指定してください")

    service = _build_service(project_root)

    temp_dir: Path | None = None
    try:
        if run_json_path:
            run_path = Path(run_json_path).expanduser()
        else:
            temp_dir = Path(tempfile.mkdtemp(prefix="langsmith_run_"))
            run_path = temp_dir / "run.json"
            data = run_json_content
            if isinstance(data, str):
                data = json.loads(data)
            run_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        output_path = Path(output_dir).expanduser() if output_dir else None
        artifacts = service.prepare_artifacts(
            run_path,
            output_dir=output_path,
            dataset_name=dataset_name,
            expected_behavior=expected_behavior,
        )

        summary_text = artifacts.summary_path.read_text(encoding="utf-8")
        prompt_text = artifacts.prompt_path.read_text(encoding="utf-8")
        dataset_path = artifacts.dataset_entry_path
        dataset_text = (
            dataset_path.read_text(encoding="utf-8") if dataset_path and dataset_path.exists() else None
        )

        return {
            "success": True,
            "run_id": artifacts.run.run_id,
            "summary_path": str(artifacts.summary_path),
            "prompt_path": str(artifacts.prompt_path),
            "dataset_path": str(dataset_path) if dataset_path else None,
            "summary_content": summary_text,
            "prompt_content": prompt_text,
            "dataset_content": dataset_text,
            "trace_url": artifacts.run.trace_url,
            "status": artifacts.run.status,
            "tags": artifacts.run.tags,
        }
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


def apply_langsmith_patch(
    *,
    patch_text: str | None = None,
    patch_file: str | None = None,
    strip: int = 1,
    project_root: str | None = None,
) -> dict[str, Any]:
    """LangSmithが提案したパッチを適用し、結果を返す"""
    if not patch_text:
        if not patch_file:
            raise ValueError("patch_text か patch_file のいずれかを指定してください")
        patch_text = Path(patch_file).expanduser().read_text(encoding="utf-8")

    service = _build_service(project_root)
    result = service.apply_patch(patch_text, project_root=Path(project_root).expanduser() if project_root else None, strip=strip)
    return {
        "success": result.applied,
        "applied": result.applied,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": list(result.command),
    }


def run_langsmith_verification(
    *,
    command: Sequence[str] | str,
    project_root: str | None = None,
) -> dict[str, Any]:
    """修正後の検証コマンドを実行し、標準出力・終了コードを返す"""
    if isinstance(command, str):
        command_sequence = shlex.split(command)
    else:
        command_sequence = list(command)

    if not command_sequence:
        raise ValueError("command を指定してください")

    service = _build_service(project_root)
    verification = service.run_verification(
        command_sequence,
        project_root=Path(project_root).expanduser() if project_root else None,
    )
    return {
        "success": verification.succeeded,
        "returncode": verification.returncode,
        "stdout": verification.stdout,
        "stderr": verification.stderr,
        "command": list(verification.command),
    }


__all__ = [
    "generate_langsmith_artifacts",
    "apply_langsmith_patch",
    "run_langsmith_verification",
]
