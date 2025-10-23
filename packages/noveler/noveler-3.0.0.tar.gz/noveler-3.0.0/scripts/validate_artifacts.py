#!/usr/bin/env python3
# File: scripts/validate_artifacts.py
# Purpose: Validate LLM artifact outputs against template acceptance criteria.
# Context: Provides a CI-friendly checker that loads prompt templates, parses
#          concrete artifacts (or template examples), evaluates acceptance
#          checklists/metrics/by_task rules, and emits machine-readable
#          summaries.

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

import yaml

MARKDOWN_META_PATTERN = re.compile(r"^\s*<!--(.*?)-->", re.DOTALL)

JsonLike = dict[str, Any]


@dataclass
class EvaluationEntry:
    """Container describing one validation job."""

    name: str
    template_path: Path
    artifact_path: Path | None
    variables: dict[str, str]
    use_example: bool = False


@dataclass
class EvaluationResult:
    """Structured summary for a single evaluation."""

    name: str
    template: Path
    artifact: Path | None
    format: str
    success: bool
    checklist: list[JsonLike]
    metrics: list[JsonLike]
    by_task: list[JsonLike]
    errors: list[str]

    def to_dict(self) -> JsonLike:
        """Return a serialisable representation."""

        return {
            "name": self.name,
            "template": str(self.template),
            "artifact": str(self.artifact) if self.artifact else None,
            "format": self.format,
            "success": self.success,
            "checklist": self.checklist,
            "metrics": self.metrics,
            "by_task": self.by_task,
            "errors": self.errors,
        }


def load_yaml(path: Path) -> JsonLike:
    """Load YAML content from a file."""

    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def extract_markdown_meta(text: str) -> dict[str, Any]:
    """Extract YAML meta block from leading HTML comment in Markdown."""

    match = MARKDOWN_META_PATTERN.match(text)
    if not match:
        return {}

    content = match.group(1)
    try:
        data = yaml.safe_load(content) or {}
    except Exception:
        return {}

    if isinstance(data, dict):
        if "meta" in data:
            return data
        # Allow shorthand where the comment root is meta itself.
        return {"meta": data}
    return {}


def parse_manifest(path: Path) -> list[EvaluationEntry]:
    """Load evaluation entries from a YAML/JSON manifest."""

    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict) or "entries" not in data:
        raise ValueError("Manifest must contain top-level 'entries'.")

    entries_raw = data["entries"]
    if not isinstance(entries_raw, Iterable):
        raise ValueError("'entries' must be a list of jobs")

    entries: list[EvaluationEntry] = []
    for idx, item in enumerate(entries_raw):
        if not isinstance(item, dict):
            raise ValueError(f"entry #{idx} is not a mapping")

        template = Path(item.get("template", ""))
        if not template:
            raise ValueError(f"entry #{idx} missing template path")

        artifact = item.get("artifact")
        artifact_path = Path(artifact) if artifact else None
        use_example = bool(item.get("use_example", False))

        name = item.get("name") or template.stem
        variables = item.get("variables") or {}
        if not isinstance(variables, dict):
            raise ValueError(f"entry #{idx} has invalid variables mapping")

        entries.append(
            EvaluationEntry(
                name=str(name),
                template_path=template,
                artifact_path=artifact_path,
                variables={str(k): str(v) for k, v in variables.items()},
                use_example=use_example,
            )
        )
    return entries


def load_artifact(
    template: JsonLike,
    artifact_path: Path | None,
    variables: dict[str, str],
    use_example: bool,
) -> tuple[Any, str | None, str]:
    """Load artifact according to template format.

    Returns (data, text, format).
    """

    artifacts_cfg = template.get("artifacts", {}) or {}
    fmt = str(artifacts_cfg.get("format", "yaml")).lower()

    if artifact_path is None and use_example:
        example = artifacts_cfg.get("example")
        if example is None:
            raise ValueError("No artifact path and template lacks example")
        raw = example
        if isinstance(raw, dict):
            data = raw
        elif fmt in {"yaml", "yml"}:
            data = yaml.safe_load(raw) or {}
        elif fmt == "json":
            data = json.loads(raw)
        else:
            data = None
        text = raw if fmt in {"md", "markdown"} else None
        return data, text, fmt

    if artifact_path is None:
        raise ValueError("Artifact path is required unless use_example is enabled")

    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    raw = artifact_path.read_text(encoding="utf-8")
    if fmt in {"yaml", "yml"}:
        return yaml.safe_load(raw) or {}, None, fmt
    if fmt == "json":
        return json.loads(raw), None, fmt
    if fmt in {"md", "markdown"}:
        meta = extract_markdown_meta(raw)
        return meta, raw, fmt
    raise ValueError(f"Unsupported artifact format: {fmt}")


def _split_path(path: str) -> list[str]:
    return [part for part in path.split(".") if part]


def _extract_field(data: Any, path: str) -> tuple[Any, bool]:
    """Traverse nested mappings/lists using dot notation."""

    if data is None:
        return None, False

    current = data
    for token in _split_path(path):
        if isinstance(current, dict):
            if token in current:
                current = current[token]
            else:
                return None, False
        elif isinstance(current, list):
            try:
                index = int(token)
            except ValueError:
                return None, False
            if 0 <= index < len(current):
                current = current[index]
            else:
                return None, False
        else:
            return None, False
    return current, True


def _ensure_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _is_nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, tuple, set, dict, str)):
        return len(value) > 0
    return bool(value)


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    if isinstance(value, bool):
        return float(value)
    return None


def _range_spec_to_bounds(spec: str) -> tuple[float | None, float | None]:
    parts = re.split(r"[\-\u2013]", spec)
    if len(parts) != 2:
        raise ValueError(f"Invalid range spec: {spec}")
    min_part, max_part = parts
    min_val = float(min_part) if min_part.strip() else None
    max_val = float(max_part) if max_part.strip() else None
    return min_val, max_val


def _evaluate_rule(rule: str, value: Any) -> tuple[bool, str | None]:
    rule = rule.strip()
    if not rule:
        return True, None
    if rule == "present":
        return value is not None, "present"
    if rule == "nonempty":
        return _is_nonempty(value), "nonempty"
    if rule.startswith("enum:"):
        options = {opt.strip() for opt in rule[len("enum:"):].split("|") if opt.strip()}
        return (str(value) in options), f"enum:{'|'.join(sorted(options))}"
    if rule.startswith("regex:"):
        pattern = rule[len("regex:"):]
        try:
            return bool(re.search(pattern, str(value))), f"regex:{pattern}"
        except re.error:
            return False, f"regex_error:{pattern}"
    return True, rule


def _evaluate_range(range_spec: str, value: Any) -> tuple[bool, str | None]:
    spec = range_spec.strip()
    if not spec:
        return True, None
    numeric = _to_float(value)
    if numeric is None:
        return False, f"range:{spec}"

    if "±" in spec:
        match = re.match(r"([0-9.]+)\s*±\s*([0-9.]+)", spec)
        if not match:
            return False, f"range:{spec}"
        center = float(match.group(1))
        tolerance = float(match.group(2))
        return abs(numeric - center) <= tolerance, f"range:{spec}"

    if re.match(r"^[<>]=?", spec):
        return _evaluate_target(spec, numeric)

    try:
        min_val, max_val = _range_spec_to_bounds(spec)
    except ValueError:
        return False, f"range:{spec}"

    if min_val is not None and numeric < min_val:
        return False, f"range:{spec}"
    if max_val is not None and numeric > max_val:
        return False, f"range:{spec}"
    return True, f"range:{spec}"


def _evaluate_target(target: str, value: Any) -> tuple[bool, str]:
    target = target.strip()
    if target.startswith("enum:"):
        options = {opt.strip() for opt in target[len("enum:"):].split("|") if opt.strip()}
        return str(value) in options, f"enum:{'|'.join(sorted(options))}"

    numeric = _to_float(value)
    if numeric is None and target not in {">= 0", ">= 0"}:
        return False, target

    if target.startswith(">="):
        threshold = float(target[2:].strip())
        return numeric is not None and numeric >= threshold, target
    if target.startswith("<="):
        threshold = float(target[2:].strip())
        return numeric is not None and numeric <= threshold, target
    if target.startswith(">"):  # strict greater
        threshold = float(target[1:].strip())
        return numeric is not None and numeric > threshold, target
    if target.startswith("<"):
        threshold = float(target[1:].strip())
        return numeric is not None and numeric < threshold, target
    if target.startswith("==") and "±" in target:
        match = re.match(r"==\s*([0-9.]+)\s*±\s*([0-9.]+)", target)
        if not match:
            return False, target
        center = float(match.group(1))
        tol = float(match.group(2))
        return numeric is not None and abs(numeric - center) <= tol, target

    if re.search(r"[\-\u2013]", target):
        try:
            min_val, max_val = _range_spec_to_bounds(target)
        except ValueError:
            return False, target
        if numeric is None:
            return False, target
        if min_val is not None and numeric < min_val:
            return False, target
        if max_val is not None and numeric > max_val:
            return False, target
        return True, target

    try:
        target_value = float(target)
        return numeric is not None and math.isclose(numeric, target_value, rel_tol=1e-6), target
    except ValueError:
        return False, target


def evaluate_by_task(template: JsonLike, artifact_data: Any) -> tuple[list[JsonLike], bool]:
    control = template.get("control_settings", {}) or {}
    rules = control.get("by_task") or (template.get("acceptance_criteria", {}) or {}).get("by_task") or []
    if not rules:
        return [], True

    tasks_section = template.get("tasks", {}) or {}
    required_map: dict[str, bool] = {}
    for detail in tasks_section.get("details", []) or []:
        if not isinstance(detail, dict):
            continue
        for item in detail.get("items", []) or []:
            if isinstance(item, dict) and "id" in item:
                required_map[str(item["id"])] = bool(item.get("required", True))

    results: list[JsonLike] = []
    overall_success = True

    for rule_cfg in rules:
        if not isinstance(rule_cfg, dict):
            continue
        task_id = str(rule_cfg.get("id", "")).strip()
        field = str(rule_cfg.get("field", "")).strip()
        if not task_id or not field:
            continue
        required = required_map.get(task_id, True)
        value, present = _extract_field(artifact_data, field)
        status = "pass"
        notes: list[str] = []

        if not present:
            status = "fail" if required else "warn"
            notes.append("field_missing")
        else:
            rule = str(rule_cfg.get("rule", ""))
            ok_rule, note_rule = _evaluate_rule(rule, value)
            if not ok_rule:
                status = "fail" if required else "warn"
            if note_rule:
                notes.append(note_rule)
            range_spec = rule_cfg.get("range")
            if range_spec:
                ok_range, note_range = _evaluate_range(str(range_spec), value)
                if not ok_range:
                    status = "fail" if required else "warn"
                if note_range:
                    notes.append(note_range)

        if status == "fail" and required:
            overall_success = False

        results.append(
            {
                "id": task_id,
                "status": status,
                "value": value if present else None,
                "notes": notes,
            }
        )

    return results, overall_success


def _check_required_fields(template: JsonLike, artifact_data: Any) -> tuple[bool, str]:
    required = template.get("artifacts", {}).get("required_fields", []) or []
    missing: list[str] = []
    for field in required:
        field = str(field)
        value, present = _extract_field(artifact_data, field)
        if not present or value is None:
            missing.append(field)
    return not missing, ", ".join(missing) if missing else ""


def _check_value_range(artifact_data: Any, path: str, lower: float, upper: float) -> tuple[bool, str, Any]:
    value, present = _extract_field(artifact_data, path)
    if not present:
        return False, "missing", None
    numeric = _to_float(value)
    if numeric is None:
        return False, "not_numeric", value
    if numeric < lower or numeric > upper:
        return False, f"outside({lower}-{upper})", numeric
    return True, "", numeric


def _check_enum(artifact_data: Any, path: str, options: set[str]) -> tuple[bool, str, Any]:
    value, present = _extract_field(artifact_data, path)
    if not present:
        return False, "missing", None
    return str(value) in options, "", value


def evaluate_checklist(
    template: JsonLike,
    artifact_data: Any,
    artifact_text: str | None,
    context: dict[str, Any],
) -> list[JsonLike]:
    items = template.get("acceptance_criteria", {}).get("checklist", []) or []
    results: list[JsonLike] = []

    for item in items:
        text = str(item).strip()
        handler = CHECKLIST_HANDLERS.get(text)
        if handler is None:
            results.append({"item": text, "status": "skip", "details": "handler_not_implemented"})
            continue

        try:
            status, details = handler(template, artifact_data, artifact_text, context)
        except Exception as err:  # best effort: capture error and mark failure
            status, details = "fail", f"exception:{err}"

        results.append({"item": text, "status": status, "details": details})

    return results


def _metrics_handler_turning_points(artifact_data: Any) -> Any:
    value, _ = _extract_field(artifact_data, "story_structure.turning_points")
    return len(value) if isinstance(value, list) else 0


def _metrics_handler_subplots_ratio(artifact_data: Any) -> float:
    value, _ = _extract_field(artifact_data, "story_structure.subplots")
    if not isinstance(value, list):
        return 0.0
    total = 0.0
    for item in value:
        if isinstance(item, dict):
            total += float(item.get("weight_ratio", 0) or 0)
    return total


def _metrics_handler_len_improvements(artifact_data: Any) -> int:
    value, _ = _extract_field(artifact_data, "improvements")
    return len(value) if isinstance(value, list) else 0


def _metrics_handler_issue_count(artifact_data: Any) -> int:
    issues, _ = _extract_field(artifact_data, "issues")
    if not isinstance(issues, dict):
        return 0
    total = 0
    for value in issues.values():
        if isinstance(value, list):
            total += len(value)
    return total


def _metrics_handler_word_ratio_sum(artifact_data: Any) -> float:
    sections, _ = _extract_field(artifact_data, "sections")
    if not isinstance(sections, list):
        return 0.0
    total = 0.0
    for section in sections:
        if isinstance(section, dict):
            total += float(section.get("word_ratio", 0) or 0)
    return total


def _metrics_handler_dialogue_ratio_range(artifact_data: Any) -> float:
    sections, _ = _extract_field(artifact_data, "sections")
    if not isinstance(sections, list):
        return None  # type: ignore[return-value]
    for section in sections:
        if isinstance(section, dict):
            ratio = _to_float(section.get("dialogue_ratio"))
            if ratio is None or ratio < 0.40 or ratio > 0.70:
                return None  # type: ignore[return-value]
    return 0.5


def _metrics_handler_micro_turn_ratio(artifact_data: Any) -> float:
    sections, _ = _extract_field(artifact_data, "sections")
    if not isinstance(sections, list) or not sections:
        return 0.0
    hits = 0
    for section in sections:
        if isinstance(section, dict) and section.get("micro_turn"):
            hits += 1
    return hits / len(sections)


def _metrics_handler_unicode_count(_: Any, text: str | None) -> int:
    return len(text or "")


def _metrics_handler_kpi_footer(_: Any, text: str | None) -> int:
    if not text:
        return 0
    tail = text.strip().lower()
    return 1 if "kpi" in tail else 0


def _metrics_handler_total_score(artifact_data: Any) -> float:
    value, _ = _extract_field(artifact_data, "total_score")
    return _to_float(value) or 0.0


def _metrics_handler_typo_error_rate(artifact_data: Any) -> float:
    value, _ = _extract_field(artifact_data, "extended_kpi.typo_error_rate")
    return _to_float(value) or 0.0


def _metrics_handler_non_visual_ratio(artifact_data: Any) -> float:
    value, found = _extract_field(artifact_data, "extended_kpi.senses_non_visual_ratio")
    if found:
        return _to_float(value) or 0.0
    scenes, _ = _extract_field(artifact_data, "scenes")
    if not isinstance(scenes, list) or not scenes:
        return 0.0
    total_ratio = 0.0
    count = 0
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        mix = scene.get("sensory_mix")
        if not isinstance(mix, dict):
            continue
        values = [float(v) for v in mix.values() if isinstance(v, (int, float))]
        if not values:
            continue
        total = sum(values)
        non_visual = sum(values[1:]) if len(values) > 1 else 0.0
        if total > 0:
            total_ratio += non_visual / total
            count += 1
    return total_ratio / count if count else 0.0


def _metrics_handler_beats_average(artifact_data: Any) -> float:
    scenes, _ = _extract_field(artifact_data, "scenes")
    if not isinstance(scenes, list) or not scenes:
        return 0.0
    total_beats = 0
    for scene in scenes:
        if isinstance(scene, dict):
            beats = scene.get("beats")
            if isinstance(beats, list):
                total_beats += len(beats)
    return total_beats / len(scenes)


METRIC_HANDLERS: dict[str, Callable[[Any, str | None], Any]] = {
    "turning_points の件数": lambda data, text=None: _metrics_handler_turning_points(data),
    "subplots.weight_ratio の合計": lambda data, text=None: _metrics_handler_subplots_ratio(data),
    "len(improvements)": lambda data, text=None: _metrics_handler_len_improvements(data),
    "issues.* の総件数": lambda data, text=None: _metrics_handler_issue_count(data),
    "summary.hook_type の列挙検証": lambda data, text=None: _extract_field(data, "summary.hook_type")[0],
    "word_ratio の合計": lambda data, text=None: _metrics_handler_word_ratio_sum(data),
    "各セクションの dialogue_ratio が範囲内": lambda data, text=None: _metrics_handler_dialogue_ratio_range(data),
    "micro_turn=true のセクション比率": lambda data, text=None: _metrics_handler_micro_turn_ratio(data),
    "本文のUnicode文字数": lambda data, text=None: _metrics_handler_unicode_count(data, text),
    "本文末尾にKPI自己チェックの簡易記録がある（任意セクション名でも可）": lambda data, text=None: _metrics_handler_kpi_footer(data, text),
    "extended/basicを統合した総合点": lambda data, text=None: _metrics_handler_total_score(data),
    "誤字率（0.1%以下）": lambda data, text=None: _metrics_handler_typo_error_rate(data),
    "五感描写の割合（推定）": lambda data, text=None: _metrics_handler_non_visual_ratio(data),
    "beats の平均個数": lambda data, text=None: _metrics_handler_beats_average(data),
    "metrics.score の範囲検証": lambda data, text=None: _extract_field(data, "metrics.score")[0],
}


def evaluate_metrics(
    template: JsonLike,
    artifact_data: Any,
    artifact_text: str | None,
) -> list[JsonLike]:
    metrics_cfg = template.get("acceptance_criteria", {}).get("metrics", []) or []
    results: list[JsonLike] = []

    for metric in metrics_cfg:
        if not isinstance(metric, dict):
            continue
        name = str(metric.get("name", "unnamed"))
        method = str(metric.get("method", "")).strip()
        target = str(metric.get("target", "")).strip()
        handler = METRIC_HANDLERS.get(method)
        if handler is None:
            results.append({
                "name": name,
                "status": "skip",
                "target": target,
                "details": f"handler_not_implemented:{method}",
            })
            continue

        try:
            value = handler(artifact_data, artifact_text)
        except Exception as err:
            results.append({
                "name": name,
                "status": "fail",
                "target": target,
                "value": None,
                "details": f"exception:{err}",
            })
            continue

        ok, detail = _evaluate_target(target, value)
        results.append({
            "name": name,
            "status": "pass" if ok else "fail",
            "target": target,
            "value": value,
            "details": detail,
        })

    return results


def _check_sections_have_hook(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    sections, _ = _extract_field(artifact_data, "sections")
    if not isinstance(sections, list):
        return "fail", "sections_missing"
    missing = [idx for idx, section in enumerate(sections) if not isinstance(section, dict) or not section.get("hook")]
    if missing:
        return "fail", f"missing_hook:{missing}"
    return "pass", ""


def _check_sections_range(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    sections, _ = _extract_field(artifact_data, "sections")
    if not isinstance(sections, list):
        return "fail", "sections_missing"
    count = len(sections)
    return ("pass", "") if 4 <= count <= 6 else ("fail", f"count={count}")


def _check_ratio_sum(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    sections, _ = _extract_field(artifact_data, "sections")
    if not isinstance(sections, list) or not sections:
        return "fail", "sections_missing"
    ratio_sum = sum(float(section.get("word_ratio", 0) or 0) for section in sections if isinstance(section, dict))
    words_sum = sum(float(section.get("planned_words", 0) or 0) for section in sections if isinstance(section, dict))
    ratio_ok = abs(ratio_sum - 1.0) <= 0.05
    words_ok = abs(words_sum - 8000) <= 800
    if ratio_ok and words_ok:
        return "pass", ""
    return "fail", f"ratio={ratio_sum:.3f},words={words_sum:.0f}"


def _check_sections_fields(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    required_keys = {"pov", "dialogue_ratio", "beats_target", "hook_type"}
    sections, _ = _extract_field(artifact_data, "sections")
    if not isinstance(sections, list):
        return "fail", "sections_missing"
    missing: list[int] = []
    for idx, section in enumerate(sections):
        if not isinstance(section, dict):
            missing.append(idx)
            continue
        if not required_keys.issubset(section.keys()):
            missing.append(idx)
    if missing:
        return "fail", f"missing_fields:{missing}"
    return "pass", ""


def _check_sections_conflict(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    sections, _ = _extract_field(artifact_data, "sections")
    if not isinstance(sections, list):
        return "fail", "sections_missing"
    failing: list[int] = []
    for idx, section in enumerate(sections):
        if not isinstance(section, dict):
            failing.append(idx)
            continue
        has_conflict = any(section.get(key) for key in ("conflict", "conflicts", "conflict_type", "decision"))
        if not has_conflict:
            failing.append(idx)
    if failing:
        return "fail", f"no_conflict:{failing}"
    return "pass", ""


def _check_issues_or_fix_plan(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    issues, _ = _extract_field(artifact_data, "issues")
    fix_plan, _ = _extract_field(artifact_data, "fix_plan")
    issues_count = len(issues) if isinstance(issues, list) else 0
    fix_count = len(fix_plan) if isinstance(fix_plan, list) else 0
    return ("pass", "") if (issues_count + fix_count) > 0 else ("fail", "no_items")


def _check_story_structure_present(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    value, present = _extract_field(artifact_data, "story_structure")
    if not present or value is None:
        return "fail", "missing"
    return "pass", ""


def _check_field_range_story(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    ok, details, _ = _check_value_range(artifact_data, "story_structure.climax.position_ratio", 0.5, 0.9)
    return ("pass", "") if ok else ("fail", details)


def _check_field_range_density(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    ok, details, _ = _check_value_range(artifact_data, "story_structure.approval_density_per_1000", 3.0, 5.0)
    return ("pass", "") if ok else ("fail", details)


def _check_main_subplots_ratio(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    main, present = _extract_field(artifact_data, "story_structure.main_plot.weight_ratio")
    if not present:
        return "fail", "main_missing"
    try:
        main = float(main)
    except (TypeError, ValueError):
        return "fail", "main_not_numeric"
    if not (0.60 <= main <= 0.70):
        return "fail", f"main={main}"

    subplots, _ = _extract_field(artifact_data, "story_structure.subplots")
    if not isinstance(subplots, list) or not subplots:
        return "fail", "subplots_missing"
    for idx, subplot in enumerate(subplots):
        if not isinstance(subplot, dict):
            return "fail", f"subplot_invalid:{idx}"
        ratio = _to_float(subplot.get("weight_ratio"))
        if ratio is None or not (0.30 <= ratio <= 0.40):
            return "fail", f"subplot_ratio:{idx}:{ratio}"
    return "pass", ""


def _check_tasks_mapped(template: JsonLike, artifact_data: Any, context: dict[str, Any], *_: Any) -> tuple[str, str]:
    by_task = context.get("by_task_results", [])
    if not by_task:
        return "skip", "by_task_not_available"
    failing = [entry["id"] for entry in by_task if entry.get("status") == "fail"]
    if failing:
        return "fail", f"by_task_fail:{failing}"
    return "pass", ""


def _check_improvements(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    improvements, _ = _extract_field(artifact_data, "improvements")
    if not isinstance(improvements, list) or not improvements:
        return "fail", "improvements_missing"
    expected_keys = {"field", "issue", "after_text", "rationale"}
    missing: list[int] = []
    for idx, item in enumerate(improvements):
        if not isinstance(item, dict) or not expected_keys.issubset(item.keys()):
            missing.append(idx)
    if missing:
        return "fail", f"missing_keys:{missing}"
    return "pass", ""


def _check_improvements_type(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    improvements, _ = _extract_field(artifact_data, "improvements")
    if not isinstance(improvements, list) or not improvements:
        return "fail", "improvements_missing"
    expected_keys = {"type", "impact", "after_text", "rationale"}
    missing: list[int] = []
    for idx, item in enumerate(improvements):
        if not isinstance(item, dict) or not expected_keys.issubset(item.keys()):
            missing.append(idx)
    if missing:
        return "fail", f"missing_keys:{missing}"
    return "pass", ""


def _check_summary_changed_sections(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    value, present = _extract_field(artifact_data, "summary.changed_sections")
    if not present:
        return "fail", "missing"
    numeric = _to_float(value)
    if numeric is None or numeric < 1:
        return "fail", f"value={value}"
    return "pass", ""


def _check_summary_page_turn(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    value, present = _extract_field(artifact_data, "summary.page_turn_score")
    if not present:
        return "fail", "missing"
    numeric = _to_float(value)
    if numeric is None or numeric < 60:
        return "fail", f"value={value}"
    return "pass", ""


def _check_manuscript_code_block(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    manuscript, present = _extract_field(artifact_data, "manuscript")
    if not present or not isinstance(manuscript, str):
        return "fail", "missing"
    stripped = manuscript.strip()
    if not (stripped.startswith("```markdown") and stripped.endswith("```")):
        return "fail", "code_block_missing"
    inner = stripped[len("```markdown"):].strip().strip("`").strip()
    if not inner:
        return "fail", "empty_content"
    return "pass", ""


def _check_manuscript_nonempty(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    manuscript, present = _extract_field(artifact_data, "manuscript")
    if not present or not isinstance(manuscript, str):
        return "fail", "missing"
    return ("pass", "") if manuscript.strip() else ("fail", "empty")


def _check_title_proofreading(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    title_check, present_title = _extract_field(artifact_data, "publication.title_check")
    proof, present_proof = _extract_field(artifact_data, "publication.final_proofreading")
    if not (present_title and present_proof):
        return "fail", "missing"
    if bool(title_check) and bool(proof):
        return "pass", ""
    return "fail", f"title={title_check},proof={proof}"


def _check_release_verdict(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    verdict, present = _extract_field(artifact_data, "release_decision.verdict")
    if not present:
        return "fail", "missing"
    if str(verdict) in {"pass", "hold"}:
        return "pass", ""
    return "fail", f"value={verdict}"


def _check_verdict_pass_fail(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    verdict, present = _extract_field(artifact_data, "verdict")
    if not present:
        return "fail", "missing"
    if str(verdict) in {"pass", "fail"}:
        return "pass", ""
    return "fail", f"value={verdict}"


def _check_summary_metrics(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    summary, present_summary = _extract_field(artifact_data, "summary.overview")
    score, present_score = _extract_field(artifact_data, "metrics.score")
    if present_summary and summary and present_score:
        return "pass", ""
    return "fail", "missing"


def _check_issues_shape(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    issues, present = _extract_field(artifact_data, "issues")
    if not present or not isinstance(issues, dict):
        return "fail", "issues_missing"
    required_keys = {"before_text", "after_text", "severity", "priority", "rationale"}
    failing: list[str] = []
    for category, items in issues.items():
        if not isinstance(items, list):
            failing.append(category)
            continue
        for idx, item in enumerate(items):
            if not isinstance(item, dict) or not required_keys.issubset(item.keys()):
                failing.append(f"{category}:{idx}")
    if failing:
        return "fail", f"missing_fields:{failing}"
    return "pass", ""


def _check_scene_requirements(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    scenes, present = _extract_field(artifact_data, "scenes")
    if not present or not isinstance(scenes, list):
        return "fail", "scenes_missing"
    failing: list[int] = []
    for idx, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            failing.append(idx)
            continue
        if not scene.get("pov") or not scene.get("hook"):
            failing.append(idx)
    if failing:
        return "fail", f"missing:{failing}"
    return "pass", ""


def _check_scene_sensory_mix(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    scenes, present = _extract_field(artifact_data, "scenes")
    if not present or not isinstance(scenes, list):
        return "fail", "scenes_missing"
    failing: list[int] = []
    for idx, scene in enumerate(scenes):
        mix = scene.get("sensory_mix") if isinstance(scene, dict) else None
        if not isinstance(mix, dict):
            failing.append(idx)
            continue
        total = sum(float(v) for v in mix.values() if isinstance(v, (int, float)))
        if abs(total - 1.0) > 0.05:
            failing.append(idx)
    if failing:
        return "fail", f"imbalance:{failing}"
    return "pass", ""


def _check_scene_non_visual_ratio(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    ratio = _metrics_handler_non_visual_ratio(artifact_data)
    if ratio >= 0.30:
        return "pass", ""
    return "fail", f"ratio={ratio:.2f}"


def _check_character_examples(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    characters, present = _extract_field(artifact_data, "characters")
    if not present or not isinstance(characters, list):
        return "fail", "characters_missing"
    failing: list[int] = []
    for idx, char in enumerate(characters):
        if not isinstance(char, dict):
            failing.append(idx)
            continue
        speech = char.get("speech_style")
        examples = speech.get("examples") if isinstance(speech, dict) else None
        if not isinstance(examples, list) or len(examples) < 3:
            failing.append(idx)
    if failing:
        return "fail", f"insufficient_examples:{failing}"
    return "pass", ""


def _check_required_fields_entry(template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    ok, missing = _check_required_fields(template, artifact_data)
    return ("pass", "") if ok else ("fail", missing)


def _check_delta_entry(_template: JsonLike, artifact_data: Any, *_: Any) -> tuple[str, str]:
    status, details = _check_delta_alignment(artifact_data)
    return status, details


def _check_markdown_meta_present(
    _template: JsonLike,
    artifact_data: Any,
    artifact_text: str | None,
    *_: Any,
) -> tuple[str, str]:
    if artifact_text is None:
        return "fail", "no_markdown"
    if isinstance(artifact_data, dict) and artifact_data:
        return "pass", ""
    return "fail", "meta_missing"


CHECKLIST_HANDLERS: dict[str, Callable[[JsonLike, Any, str | None, dict[str, Any]], tuple[str, str]]] = {
    "required_fields がすべて存在する": _check_required_fields_entry,
    "story_structure が存在する": _check_story_structure_present,
    "climax.position_ratio が 0.5–0.9 の範囲": _check_field_range_story,
    "approval_density_per_1000 が 3–5 の範囲": _check_field_range_density,
    "main_plot と subplots の比重が 0.6–0.7 : 0.3–0.4 に収まる": _check_main_subplots_ratio,
    "tasks.details の観点が story_structure に反映されている": _check_tasks_mapped,
    "sections が4–6件": _check_sections_range,
    "ratio_sum ≈ 1.0 かつ planned_words 総和≈8000": _check_ratio_sum,
    "各セクションに pov/dialogue_ratio/beats_target/hook_type がある": _check_sections_fields,
    "各セクションに conflict または decision が最低1つ": _check_sections_conflict,
    "issues または fix_plan のいずれかが1件以上": _check_issues_or_fix_plan,
    "全セクションに hook がある": _check_sections_have_hook,
    "すべてのシーンに pov と hook がある": _check_scene_requirements,
    "全シーンで sensory_mix の合計 ≈ 1.0": _check_scene_sensory_mix,
    "非視覚感覚比率 ≥ 0.30": _check_scene_non_visual_ratio,
    "各キャラに台詞例が3つある": _check_character_examples,
    "delta = after - before が全て整合": _check_delta_entry,
    "improvements が1件以上存在し、各要素に field/issue/after_text/rationale が含まれる": _check_improvements,
    "improvements が1件以上あり、各要素に field/issue/after_text/rationale が存在する": _check_improvements,
    "improvements が1件以上あり、type/impact/after_text/rationale を含む": _check_improvements_type,
    "improvements が1件以上存在し、type/impact/after_text/rationale を含む": _check_improvements_type,
    "summary.changed_sections >= 1": _check_summary_changed_sections,
    "summary.page_turn_score が 60 以上": _check_summary_page_turn,
    "meta コメント（HTML）を先頭に含める": _check_markdown_meta_present,
    "manuscript が ```markdown コードブロックで始まり終わる": _check_manuscript_code_block,
    "manuscript のコードブロックが存在し、改稿後本文が含まれている": _check_manuscript_code_block,
    "manuscript のコードブロックが存在し空でない": _check_manuscript_nonempty,
    "summary.overview と metrics.score を出力している": _check_summary_metrics,
    "issues.<category>[] の各要素に before_text / after_text / severity / priority / rationale が含まれている": _check_issues_shape,
    "title_check と final_proofreading が true": _check_title_proofreading,
    "release_decision.verdict が pass|hold": _check_release_verdict,
    "verdict が pass|fail のいずれか": _check_verdict_pass_fail,
}


def _check_delta_alignment(artifact_data: Any) -> tuple[str, str]:
    items, present = _extract_field(artifact_data, "emotion_curve")
    if not present or not isinstance(items, list):
        return "fail", "emotion_curve_missing"
    failing: list[int] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            failing.append(idx)
            continue
        before = _to_float(item.get("before"))
        after = _to_float(item.get("after"))
        delta = _to_float(item.get("delta"))
        if None in {before, after, delta}:
            failing.append(idx)
            continue
        if not math.isclose(delta, after - before, rel_tol=1e-6, abs_tol=1e-6):
            failing.append(idx)
    if failing:
        return "fail", f"delta_mismatch:{failing}"
    return "pass", ""


def evaluate_acceptance(entry: EvaluationEntry) -> EvaluationResult:
    template = load_yaml(entry.template_path)
    if "acceptance_criteria" not in template:
        raise ValueError(f"Template lacks acceptance_criteria: {entry.template_path}")

    try:
        artifact_data, artifact_text, fmt = load_artifact(
            template, entry.artifact_path, entry.variables, entry.use_example
        )
    except Exception as err:
        return EvaluationResult(
            name=entry.name,
            template=entry.template_path,
            artifact=entry.artifact_path,
            format="unknown",
            success=False,
            checklist=[],
            metrics=[],
            by_task=[],
            errors=[str(err)],
        )

    by_task_results, by_task_success = evaluate_by_task(template, artifact_data)
    context = {
        "by_task_results": by_task_results,
        "by_task_success": by_task_success,
        "meta": artifact_data,
    }

    checklist_results = evaluate_checklist(template, artifact_data, artifact_text, context)
    metrics_results = evaluate_metrics(template, artifact_data, artifact_text)

    errors: list[str] = []
    if not by_task_success:
        errors.append("by_task_failure")

    def _has_failure(items: list[JsonLike]) -> bool:
        return any(entry.get("status") == "fail" for entry in items)

    success = not errors and not _has_failure(checklist_results) and not _has_failure(metrics_results)

    return EvaluationResult(
        name=entry.name,
        template=entry.template_path,
        artifact=entry.artifact_path,
        format=fmt,
        success=success,
        checklist=checklist_results,
        metrics=metrics_results,
        by_task=by_task_results,
        errors=errors,
    )


def write_reports(results: list[EvaluationResult], output_dir: Path, output_prefix: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{output_prefix}.json"
    md_path = output_dir / f"{output_prefix}.md"

    with json_path.open("w", encoding="utf-8") as fh:
        json.dump([result.to_dict() for result in results], fh, ensure_ascii=False, indent=2)

    lines: list[str] = ["# Artifact Validation Summary", ""]
    for result in results:
        lines.append(f"## {result.name}")
        lines.append(f"- Template: `{result.template}`")
        lines.append(f"- Artifact: `{result.artifact}`")
        lines.append(f"- Format: `{result.format}`")
        lines.append(f"- Success: {'✅' if result.success else '❌'}")
        if result.errors:
            lines.append(f"- Errors: {', '.join(result.errors)}")
        if result.checklist:
            lines.append("### Checklist")
            for item in result.checklist:
                lines.append(f"- [{item['status']}] {item['item']} ({item.get('details','')})")
        if result.metrics:
            lines.append("### Metrics")
            for metric in result.metrics:
                lines.append(
                    f"- [{metric['status']}] {metric['name']} value={metric.get('value')} target={metric.get('target')}"
                )
        if result.by_task:
            lines.append("### By Task")
            for task in result.by_task:
                lines.append(
                    f"- [{task['status']}] {task['id']} value={task.get('value')} notes={','.join(task.get('notes', []))}"
                )
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")


def parse_cli(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate artifacts against acceptance criteria.")
    parser.add_argument("--template", type=str, help="Path to template YAML file")
    parser.add_argument("--artifact", type=str, help="Path to artifact file")
    parser.add_argument("--use-example", action="store_true", help="Use template artifacts.example content")
    parser.add_argument("--var", action="append", default=[], help="Template variable override key=value")
    parser.add_argument("--manifest", type=str, help="Path to manifest YAML listing validation entries")
    parser.add_argument("--output-dir", type=str, default="reports", help="Directory for summary files")
    parser.add_argument("--output-prefix", type=str, default="artifact_validation", help="Output file prefix")
    return parser.parse_args(argv)


def _parse_var_pairs(pairs: list[str]) -> dict[str, str]:
    variables: dict[str, str] = {}
    for item in pairs:
        if "=" not in item:
            raise ValueError(f"Invalid variable format: {item}")
        key, value = item.split("=", 1)
        variables[key.strip()] = value.strip()
    return variables


def collect_entries(args: argparse.Namespace) -> list[EvaluationEntry]:
    entries: list[EvaluationEntry] = []
    if args.manifest:
        entries.extend(parse_manifest(Path(args.manifest)))

    if args.template:
        template = Path(args.template)
        artifact = Path(args.artifact) if args.artifact else None
        variables = _parse_var_pairs(args.var)
        entries.append(
            EvaluationEntry(
                name=template.stem,
                template_path=template,
                artifact_path=artifact,
                variables=variables,
                use_example=args.use_example,
            )
        )

    if not entries:
        raise ValueError("No evaluation entries specified")
    return entries


def main(argv: list[str]) -> int:
    args = parse_cli(argv)
    try:
        entries = collect_entries(args)
    except Exception as err:
        print(f"[validate_artifacts] configuration error: {err}", file=sys.stderr)
        return 2

    results: list[EvaluationResult] = []
    for entry in entries:
        result = evaluate_acceptance(entry)
        results.append(result)

    write_reports(results, Path(args.output_dir), args.output_prefix)

    return 0 if all(result.success for result in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
