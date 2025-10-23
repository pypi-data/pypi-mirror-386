#!/usr/bin/env python3
"""Minimal ProgressiveTaskManager for tests (noveler.domain.services).

Provides only the APIs required by tests and loads YAML prompt templates
from the project's `templates/` directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass
class _Task:
    id: int
    slug: str
    name: str
    phase: str = "structural_design"


class ProgressiveTaskManager:
    def __init__(self, project_root: str | Path, episode_number: int) -> None:
        self.project_root = Path(project_root)
        self.episode_number = int(episode_number)

        self.prompt_templates_dir: Path = self.project_root / "templates"
        self.tasks_config: Dict[str, Any] = {
            "total_steps": 19,  # step00..step18
            "tasks": [
                {"id": 0, "slug": "scope_definition", "name": "スコープ定義", "phase": "structural_design"}
            ],
        }
        self.current_state: Dict[str, Any] = {"current_step": 0, "completed_steps": []}

    def _get_step_slug(self, step_id: int) -> str:
        return "scope_definition" if step_id == 0 else f"step{step_id:02d}"

    def _get_task_by_id(self, tasks: List[Dict[str, Any]], step_id: int) -> Dict[str, Any] | None:
        for t in tasks:
            if int(t.get("id", -1)) == step_id:
                return t
        return None

    def _load_prompt_template(self, step_id: int) -> Dict[str, Any] | None:
        slug = self._get_step_slug(step_id)
        candidates = [
            self.prompt_templates_dir / "writing" / f"write_step{step_id:02d}_{slug}.yaml",
            # レガシーフォールバック（移行期間のみ）
            self.prompt_templates_dir / "legacy" / f"step{step_id:02d}_{slug}.yaml",
        ]
        for path in candidates:
            if path.exists():
                try:
                    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                except Exception:
                    return None
        return None

    def _prepare_template_variables(self, step_id: int, current_task: Dict[str, Any] | None) -> Dict[str, Any]:
        total_steps = int(self.tasks_config.get("total_steps", 18))
        completed_steps = len(self.current_state.get("completed_steps", []))
        return {
            "step_id": step_id,
            "step_name": (current_task or {}).get("name", self._get_step_slug(step_id)),
            "episode_number": self.episode_number,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "phase": (current_task or {}).get("phase", "structural_design"),
        }

    def _replace_variables(self, text: str, variables: Dict[str, Any]) -> str:
        result = text or ""
        for k, v in variables.items():
            result = result.replace("{" + str(k) + "}", str(v))
        return result

    def get_writing_tasks(self) -> Dict[str, Any]:
        step_id = int(self.current_state.get("current_step", 0))
        tpl = self._load_prompt_template(step_id) or {}
        current_task = self._get_task_by_id(self.tasks_config["tasks"], step_id) or {
            "id": step_id,
            "name": self._get_step_slug(step_id),
            "phase": "structural_design",
        }
        variables = self._prepare_template_variables(step_id, current_task)
        main_instruction = ((tpl.get("prompt") or {}).get("main_instruction") or "")
        llm_instruction = self._replace_variables(main_instruction, variables)
        if not llm_instruction.strip():
            default_tpl = (
                "エピソード{episode_number:03d}のスコープを定義し、目的・制約・成功基準を明確にせよ。\n"
                "現在のステップ: {step_id} ({step_name}) / 進捗: {completed_steps}/{total_steps}.\n"
                "このステップのみを実行し、未指定の後続ステップは実行しないこと。"
            )
            llm_instruction = self._replace_variables(default_tpl, variables)
        return {
            "episode_number": self.episode_number,
            "current_task": current_task,
            "progress": {"completed": variables["completed_steps"], "total": variables["total_steps"]},
            "next_action": "次のステップは別途指示があるまで実行しないでください",
            "llm_instruction": llm_instruction,
        }

    def execute_writing_step(self, step_id: int, dry_run: bool = True) -> Dict[str, Any]:
        tpl = self._load_prompt_template(step_id) or {}
        current_task = self._get_task_by_id(self.tasks_config["tasks"], step_id) or {
            "id": step_id,
            "name": self._get_step_slug(step_id),
            "phase": "structural_design",
        }
        variables = self._prepare_template_variables(step_id, current_task)
        main_instruction = (
            ((tpl.get("prompt") or {}).get("main_instruction") or "このステップのみを実行してください。\n複数ステップを一括で実行しないでください。")
        )
        llm_instruction = self._replace_variables(main_instruction, variables)
        if not llm_instruction.strip():
            default_tpl = (
                "エピソード{episode_number:03d}のスコープを定義し、目的・制約・成功基準を明確にせよ。\n"
                "現在のステップ: {step_id} ({step_name}) / 進捗: {completed_steps}/{total_steps}.\n"
                "このステップのみを実行し、未指定の後続ステップは実行しないこと。"
            )
            llm_instruction = self._replace_variables(default_tpl, variables)
        return {"episode_number": self.episode_number, "step_id": step_id, "status": "simulated", "llm_instruction": llm_instruction}

    def get_task_status(self) -> Dict[str, Any]:
        current_step = int(self.current_state.get("current_step", 0))
        status = "not_started" if current_step == 0 else "in_progress"
        return {"overall_status": status, "current_step": current_step, "completed_steps": list(self.current_state.get("completed_steps", []))}
