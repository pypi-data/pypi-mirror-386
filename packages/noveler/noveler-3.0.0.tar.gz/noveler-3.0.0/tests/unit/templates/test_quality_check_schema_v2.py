# File: tests/unit/templates/test_quality_check_schema_v2.py
# Purpose: Validate Schema v2 structure for quality check templates (check_step01-12).
# Context: Ensures ProgressiveCheckManager consumes up-to-date templates without regressions.

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_DIR = REPO_ROOT / "templates" / "quality" / "checks"
REQUIRED_KEYS = {
    "metadata",
    "llm_config",
    "prompt",
    "inputs",
    "constraints",
    "tasks",
    "artifacts",
    "acceptance_criteria",
    "next",
    "variables",
    "control_settings",
    "check_criteria",
}
REQUIRED_FIELDS = {"summary", "issues", "recommendations", "metrics"}
VARIABLES_BASE = {"step_id", "step_name", "episode_number", "completed_steps", "total_steps", "phase"}

TEMPLATE_PATHS = sorted(TEMPLATE_DIR.glob("check_step*_*.yaml"))


@pytest.mark.parametrize("template_path", TEMPLATE_PATHS)
def test_quality_template_schema_v2(template_path: Path) -> None:
    raw = template_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)

    missing = REQUIRED_KEYS.difference(data.keys())
    assert not missing, f"missing keys: {missing} in {template_path.name}"

    metadata = data["metadata"]
    assert metadata.get("version") == "2.0.0"
    assert metadata.get("last_updated"), "last_updated is required"
    assert metadata.get("estimated_duration"), "estimated_duration is required"

    llm_config = data["llm_config"].get("role_messages", {})
    assert "system" in llm_config and "user" in llm_config

    main_instruction = data["prompt"].get("main_instruction", "")
    assert metadata["step_name"] in main_instruction

    inputs = data["inputs"]
    assert inputs["files"], "at least one file input is required"
    assert set(inputs["variables"]).issuperset({"episode_number", "project_root"})

    artifacts = data["artifacts"]
    assert artifacts["format"] == "json"
    assert set(artifacts["required_fields"]) == REQUIRED_FIELDS
    example_payload = artifacts.get("example", "{}")
    json.loads(example_payload)

    acceptance = data["acceptance_criteria"]
    assert acceptance.get("checklist"), "checklist must not be empty"
    assert acceptance.get("metrics"), "metrics must not be empty"

    variable_set = set(data["variables"])
    assert VARIABLES_BASE.issubset(variable_set)

    control_settings = data["control_settings"]
    for flag in ("strict_single_step", "require_completion_confirm", "auto_advance_disabled", "batch_execution_blocked"):
        assert control_settings.get(flag) is True

    by_task = control_settings.get("by_task", [])
    assert by_task, "by_task must be defined"
    for entry in by_task:
        field = entry.get("field", "")
        assert field.startswith("issues."), f"by_task field must reference issues.* (got: {field})"

    if metadata["step_id"] == 12:
        assert control_settings.get("final_step") is True
    else:
        assert "final_step" not in control_settings

    tasks = data["tasks"]
    assert tasks.get("bullets"), "tasks.bullets must not be empty"
    for detail in tasks.get("details", []):
        for item in detail.get("items", []):
            assert item.get("id"), "each task item requires an id"

    criteria_keys = set(data["check_criteria"].keys())
    issue_fields = {entry["field"].split(".", 1)[1] for entry in by_task}
    assert issue_fields.issubset(criteria_keys), "check_criteria must provide definitions for all issues categories"
