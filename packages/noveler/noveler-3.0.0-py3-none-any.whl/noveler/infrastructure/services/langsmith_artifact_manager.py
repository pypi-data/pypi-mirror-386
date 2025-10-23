"""Infrastructure.services.langsmith_artifact_manager
Where: Infrastructure service managing LangSmith artifacts.
What: Loads LangSmith runs and writes summaries, prompts, and datasets to disk.
Why: Supports LangSmith-driven workflows with consistent artifact handling.
"""

from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path
from typing import Any, Iterable, Sequence

from noveler.domain.value_objects.langsmith_artifacts import (
    LangSmithRun,
    PatchResult,
    VerificationResult,
)
from noveler.presentation.shared.shared_utilities import console, get_logger


class LangSmithArtifactManager:
    """LangSmith関連成果物の生成と更新を担当するサービス"""

    def __init__(self, logger=None, console_service=None) -> None:
        self.logger = logger or get_logger(__name__)
        self.console = console_service or console

    # === Run情報のロード ===
    def load_run(self, run_path: Path | str) -> LangSmithRun:
        """LangSmithのrun.jsonを読み込み値オブジェクトを生成"""

        path = Path(run_path)
        with path.open(encoding="utf-8") as fp:
            payload: dict[str, Any] = json.load(fp)

        run_id = payload.get("id") or payload.get("run_id") or "unknown-run"
        name = payload.get("name") or payload.get("run_name") or "unknown"
        status = payload.get("status") or payload.get("state") or "unknown"
        error_value = payload.get("error")
        error_message = self._extract_error_message(error_value)
        trace_url = payload.get("url") or payload.get("trace_url")
        inputs = payload.get("inputs") or {}
        outputs = payload.get("outputs") or {}
        metadata = payload.get("metadata") or {}
        tags = payload.get("tags") or []
        if not isinstance(tags, list):
            tags = [str(tags)]

        run = LangSmithRun(
            run_id=run_id,
            name=name,
            status=str(status),
            error=error_message,
            trace_url=trace_url,
            inputs=self._ensure_dict(inputs),
            outputs=self._ensure_dict(outputs),
            metadata=self._ensure_dict(metadata),
            tags=[str(tag) for tag in tags],
        )
        self.logger.debug("Loaded LangSmith run %s", run.run_id)
        return run

    def _ensure_dir(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)

    def _ensure_dict(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        return {}

    def _extract_error_message(self, error_value: Any) -> str | None:
        if isinstance(error_value, dict):
            return error_value.get("message") or error_value.get("text") or json.dumps(error_value, ensure_ascii=False)
        if error_value is None:
            return None
        return str(error_value)

    # === 成果物生成 ===
    def write_summary(self, run: LangSmithRun, output_dir: Path) -> Path:
        """LangSmithランのサマリーMarkdownを出力"""
        self._ensure_dir(output_dir)
        summary_content = self._render_summary(run)
        summary_path = output_dir / f"{run.run_id}_summary.md"
        summary_path.write_text(summary_content, encoding="utf-8")
        return summary_path

    def write_prompt(
        self,
        run: LangSmithRun,
        output_dir: Path,
        expected_behavior: str | None = None,
    ) -> Path:
        """LLM向けのプロンプトテンプレートを出力"""
        self._ensure_dir(output_dir)
        prompt_content = self._render_prompt(run, expected_behavior)
        prompt_path = output_dir / f"{run.run_id}_prompt.txt"
        prompt_path.write_text(prompt_content, encoding="utf-8")
        return prompt_path

    def update_dataset(
        self,
        run: LangSmithRun,
        dataset_path: Path,
        expected_behavior: str | None = None,
    ) -> Path:
        """JSONLデータセットにrun情報を追記（run_id重複を除外）"""
        self._ensure_dir(dataset_path.parent)

        entries = self._read_dataset_entries(dataset_path)
        existing_ids = {entry.get("run_id") for entry in entries}
        if run.run_id not in existing_ids:
            entries.append(run.to_dataset_entry(expected_behavior))
            self._write_dataset_entries(dataset_path, entries)
            self.logger.info("Appended LangSmith run %s to %s", run.run_id, dataset_path)
        else:
            self.logger.debug("Run %s already exists in dataset %s", run.run_id, dataset_path)
        return dataset_path

    def _read_dataset_entries(self, dataset_path: Path) -> list[dict[str, Any]]:
        if not dataset_path.exists():
            return []
        entries: list[dict[str, Any]] = []
        for line in dataset_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                self.logger.warning("Skip invalid dataset entry line")
        return entries

    def _write_dataset_entries(self, dataset_path: Path, entries: Iterable[dict[str, Any]]) -> None:
        with dataset_path.open("w", encoding="utf-8") as fp:
            for entry in entries:
                fp.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # === パッチ適用 / コマンド実行 ===
    def apply_patch(self, patch_text: str, project_root: Path, strip: int = 1) -> PatchResult:
        """patchコマンドで差分を適用"""
        command = ["patch", f"-p{strip}"]
        try:
            completed = subprocess.run(
                command,
                input=patch_text,
                text=True,
                capture_output=True,
                cwd=project_root,
                check=False,
            )
        except FileNotFoundError as exc:  # pragma: no cover - 環境依存
            self.logger.error("patch command not available: %s", exc)
            return PatchResult(applied=False, stdout="", stderr=str(exc), command=command)

        applied = completed.returncode == 0
        if applied:
            self.console.print_success("✅ パッチ適用に成功しました")
            self.logger.info("Patch applied successfully")
        else:
            self.console.print_error("❌ パッチ適用に失敗しました")
            self.logger.error("Patch apply failed: %s", completed.stderr)
        return PatchResult(
            applied=applied,
            stdout=completed.stdout,
            stderr=completed.stderr,
            command=command,
        )

    def run_command(self, command: Sequence[str], project_root: Path) -> VerificationResult:
        """検証コマンドを実行"""
        completed = subprocess.run(
            list(command),
            text=True,
            capture_output=True,
            cwd=project_root,
            check=False,
        )
        if completed.returncode == 0:
            self.console.print_success("✅ 検証コマンドが成功しました")
        else:
            self.console.print_error("❌ 検証コマンドが失敗しました")
        self.logger.info("Verification command finished with code %s", completed.returncode)
        return VerificationResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            command=list(command),
        )

    # === レンダリング ===
    def _render_summary(self, run: LangSmithRun) -> str:
        inputs_json = json.dumps(run.inputs, indent=2, ensure_ascii=False)
        outputs_json = json.dumps(run.outputs, indent=2, ensure_ascii=False)
        metadata_json = json.dumps(run.metadata, indent=2, ensure_ascii=False)
        summary = textwrap.dedent(
            f"""
            # {run.headline()}

            - **Status**: {run.status}
            - **Trace URL**: {run.trace_url or 'N/A'}
            - **Captured At**: {run.captured_at.isoformat()}
            - **Tags**: {', '.join(run.tags) if run.tags else 'なし'}

            ## 💥 Error
            {run.error or 'No error information provided.'}

            ## 🔢 Inputs
            ```json
            {inputs_json}
            ```

            ## 📤 Outputs
            ```json
            {outputs_json}
            ```

            ## 🧾 Metadata
            ```json
            {metadata_json}
            ```
            """
        ).strip()
        return summary + "\n"

    def _render_prompt(self, run: LangSmithRun, expected_behavior: str | None) -> str:
        inputs_json = json.dumps(run.inputs, indent=2, ensure_ascii=False)
        outputs_json = json.dumps(run.outputs, indent=2, ensure_ascii=False)
        expected = expected_behavior or "Describe the intended fix for this failure."
        prompt = textwrap.dedent(
            f"""
            You are an engineer assisting with a regression fix captured by LangSmith.

            Run ID: {run.run_id}
            Name: {run.name}
            Status: {run.status}
            Trace URL: {run.trace_url or 'N/A'}

            ## Current Error
            {run.error or 'No error message available.'}

            ## Inputs
            ```json
            {inputs_json}
            ```

            ## Observed Output
            ```json
            {outputs_json}
            ```

            ## Expected Behaviour
            {expected}

            1. Explain the root cause based on the inputs and error.
            2. Suggest a patch in unified diff format.
            3. List verification commands to confirm the fix.
            """
        ).strip()
        return prompt + "\n"


__all__ = [
    "LangSmithArtifactManager",
    "LangSmithRun",
    "PatchResult",
    "VerificationResult",
]
