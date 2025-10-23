# File: src/noveler/domain/services/progressive_check/llm_request_builder.py
# Purpose: LLM request construction for Progressive Check system
# Context: Extracted from ProgressiveCheckManager (Phase 6 Step 2)

"""LLM Request Builder for Progressive Check System.

This module handles all LLM request construction operations including:
- Prompt template loading and rendering
- Variable expansion and sanitization
- Manuscript content loading
- Request payload construction
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger
from noveler.domain.interfaces.i_path_service import IPathService
from noveler.domain.repositories import ICheckTemplateRepository
from noveler.domain.value_objects.universal_prompt_execution import (
    UniversalPromptRequest,
    PromptType,
    ProjectContext,
)


class LLMRequestBuilder:
    """Builds LLM requests for Progressive Check execution.

    Responsibilities:
    - Load and render prompt templates
    - Expand template variables
    - Load manuscript content from various sources
    - Construct UniversalPromptRequest payloads
    - Generate enhanced and legacy LLM instructions

    Args:
        project_root: Root directory of the project
        episode_number: Episode number for this request
        template_repository: Repository for loading templates
        path_service: Service for path resolution
        logger: Optional logger instance
    """

    def __init__(
        self,
        project_root: Path,
        episode_number: int,
        template_repository: ICheckTemplateRepository,
        path_service: IPathService,
        logger: ILogger | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.episode_number = episode_number
        self.template_repo = template_repository
        self.path_service = path_service
        self.logger = logger or NullLogger()

        # Template metadata tracking
        self.template_source_log: dict[int, dict[str, Any]] = {}
        self.template_metadata_cache: dict[int, dict[str, Any]] = {}

    def build_step_request_prompt(
        self,
        task: dict[str, Any],
        input_data: dict[str, Any] | None = None,
        *,
        include_context: bool = False,
    ) -> str | tuple[str, dict[str, Any]]:
        """チェックステップ実行時にLLMへ提示する指示文を生成

        外部テンプレートがあれば優先して使用し、なければタスク定義のllm_instructionを使う。

        Args:
            task: Task definition dictionary
            input_data: Optional input data for the step
            include_context: If True, return (prompt, payload) tuple

        Returns:
            Prompt string or (prompt, payload) tuple if include_context=True
        """
        payload = self._prepare_prompt_payload(task, input_data or {})
        prompt = payload.get("prompt") or str(
            task.get("llm_instruction", f"チェックステップ {task.get('id')} を実行してください")
        )
        if include_context:
            return prompt, payload
        return prompt

    def create_llm_request(
        self,
        task: dict[str, Any],
        payload: dict[str, Any],
    ) -> UniversalPromptRequest:
        """Create UniversalPromptRequest from task and payload.

        Args:
            task: Task definition
            payload: Prompt payload from _prepare_prompt_payload

        Returns:
            UniversalPromptRequest instance
        """
        context_files = [
            path for path in payload.get('context_files', [])
            if isinstance(path, Path) and path.exists()
        ]
        project_context = ProjectContext(
            project_root=self.project_root,
            project_name=self.project_root.name,
            additional_context_files=context_files,
        )
        type_specific_config = self._sanitize_for_json(
            {
                'episode_number': self.episode_number,
                'step_id': task.get('id'),
                'phase': task.get('phase'),
                'task_name': task.get('name'),
                'template_source': payload.get('template_source'),
                'variables': payload.get('variables'),
                'input_data': payload.get('sanitized_input'),
            }
        )
        return UniversalPromptRequest(
            prompt_content=payload['prompt'],
            prompt_type=PromptType.QUALITY_CHECK,
            project_context=project_context,
            output_format='json',
            max_turns=1,
            type_specific_config=type_specific_config,
        )

    def generate_enhanced_llm_instruction(
        self,
        task: dict[str, Any],
        result: dict[str, Any],
        next_task: dict[str, Any] | None,
    ) -> str:
        """Generate enhanced LLM instruction with step completion details.

        Args:
            task: Completed task definition
            result: Execution result
            next_task: Next task to execute (if any)

        Returns:
            Enhanced instruction string
        """
        step_id = task.get("id", 0)
        step_name = task.get("name", f"Step {step_id}")

        instruction_parts = [
            f"✓ {step_name} が完了しました。",
            "",
            self._render_main_instruction(result),
        ]

        if next_task:
            next_id = next_task.get("id", 0)
            next_name = next_task.get("name", f"Step {next_id}")
            instruction_parts.extend([
                "",
                f"次は {next_name} に進んでください。",
            ])
        else:
            instruction_parts.extend([
                "",
                "すべてのチェックステップが完了しました。",
            ])

        return "\n".join(instruction_parts)

    def generate_llm_instruction_legacy(
        self,
        task: dict[str, Any],
        result_summary: str,
        next_step_id: int | None,
    ) -> str:
        """Generate legacy format LLM instruction.

        Args:
            task: Task definition
            result_summary: Summary of execution result
            next_step_id: ID of next step (if any)

        Returns:
            Legacy instruction string
        """
        step_id = task.get("id", 0)
        step_name = task.get("name", f"Step {step_id}")

        parts = [
            f"ステップ {step_id} ({step_name}) が完了しました。",
            "",
            result_summary,
        ]

        if next_step_id:
            parts.extend([
                "",
                f"次はステップ {next_step_id} に進んでください。",
            ])

        return "\n".join(parts)

    def generate_error_instruction(
        self,
        task: dict[str, Any],
        error_message: str,
    ) -> str:
        """Generate error instruction for failed step.

        Args:
            task: Task definition
            error_message: Error message

        Returns:
            Error instruction string
        """
        step_id = task.get("id", 0)
        step_name = task.get("name", f"Step {step_id}")

        return "\n".join([
            f"✗ {step_name} の実行中にエラーが発生しました。",
            "",
            f"エラー内容: {error_message}",
            "",
            "エラーを修正して再試行してください。",
        ])

    # Template loading and rendering

    def _load_prompt_template(self, step_id: int) -> dict[str, Any] | None:
        """外部YAMLプロンプトテンプレートを読み込む

        Args:
            step_id: Step ID

        Returns:
            Template data dictionary or None if not found
        """
        template_name = f"check_step{step_id:02d}"
        template_data = self.template_repo.load_template(template_name)

        if template_data is None:
            self.logger.debug("品質チェックテンプレートが見つかりません: %s", template_name)
            return None

        if not isinstance(template_data, dict):
            self.logger.warning(
                "品質チェックテンプレート構造が不正: %s",
                template_name,
            )
            return None

        # Collect metadata
        metadata = self._collect_template_metadata(step_id, template_data, template_name)
        self.template_source_log[step_id] = metadata

        self.logger.info(
            "品質チェックテンプレート読み込み完了: %s (source=%s)",
            template_name,
            metadata.get("source", "unknown"),
        )
        return template_data

    def _collect_template_metadata(
        self,
        step_id: int,
        template_data: dict[str, Any],
        template_name: str,
    ) -> dict[str, Any]:
        """Collect metadata from template.

        Args:
            step_id: Step ID
            template_data: Template data dictionary
            template_name: Template name

        Returns:
            Metadata dictionary
        """
        # Extract resolved source if available (from FileCheckTemplateRepository)
        source = template_data.get("_resolved_source", "template_repository")

        metadata = {
            "source": source,
            "name": template_name,
            "step_id": step_id,
        }

        # Extract version if available
        if "version" in template_data:
            metadata["version"] = template_data["version"]

        # Extract hash (exclude internal metadata from hash)
        hash_data = {k: v for k, v in template_data.items() if not k.startswith("_")}
        metadata["hash"] = self._hash_dict(hash_data)

        # Cache metadata
        self.template_metadata_cache[step_id] = metadata

        return metadata

    def _prepare_prompt_payload(
        self, task: dict[str, Any], input_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Build a payload bundling template data, variables, and manuscript content.

        Args:
            task: Task definition
            input_data: Input data for the step

        Returns:
            Payload dictionary
        """
        step_id = int(task.get('id', 0))
        variables = self._prepare_template_variables(step_id, task)
        variables.setdefault('project_root', str(self.project_root))
        variables.setdefault('episode_number', self.episode_number)
        variables.setdefault('episode_number_formatted', f'{self.episode_number:03d}')
        template_data = self._load_prompt_template(step_id) if isinstance(task, dict) else None
        template_source = self.template_source_log.get(step_id)
        sanitized_input = self._sanitize_for_json(dict(input_data))
        manuscript_content, context_files = self._load_manuscript_content(template_data, variables, input_data)
        prompt_text = ''
        if template_data:
            prompt_text = self._render_quality_template(
                template_data, variables, manuscript_content, sanitized_input
            )
        if not prompt_text:
            fallback = str(task.get('llm_instruction', f'チェックステップ {step_id} を実行してください'))
            prompt_text = self._replace_variables(fallback, variables)
        return {
            'prompt': prompt_text,
            'template_data': template_data,
            'variables': variables,
            'sanitized_input': sanitized_input,
            'manuscript_content': manuscript_content,
            'context_files': context_files,
            'template_source': template_source,
        }

    def _render_quality_template(
        self,
        template_data: dict[str, Any],
        variables: dict[str, Any],
        manuscript_content: str,
        sanitized_input: dict[str, Any],
    ) -> str:
        """Render Schema v2 quality template into an LLM prompt.

        Args:
            template_data: Template data dictionary
            variables: Variable substitution map
            manuscript_content: Manuscript text content
            sanitized_input: Sanitized input data

        Returns:
            Rendered prompt string
        """

        def _fmt_list(items: list[Any]) -> str:
            formatted: list[str] = []
            for item in items:
                if isinstance(item, str):
                    formatted.append(f"- {self._replace_variables(item, variables)}")
                else:
                    formatted.append(
                        f"- {json.dumps(self._sanitize_for_json(item), ensure_ascii=False)}"
                    )
            return '\n'.join(formatted)

        role_messages = (template_data.get('llm_config') or {}).get('role_messages', {})
        system_msg = role_messages.get('system', '').strip()
        user_msg = role_messages.get('user', '').strip()

        prompt_section = template_data.get('prompt', {})
        main_instruction = prompt_section.get('main_instruction', '')
        formatted_instruction = (
            self._replace_variables(main_instruction, variables) if main_instruction else ''
        )

        constraints = template_data.get('constraints', {})
        hard_rules = constraints.get('hard_rules', [])
        soft_targets = constraints.get('soft_targets', [])

        tasks_section = template_data.get('tasks', {})
        task_bullets = tasks_section.get('bullets', [])
        task_details = tasks_section.get('details', [])

        acceptance = template_data.get('acceptance_criteria', {})
        checklist = acceptance.get('checklist', [])
        metrics = acceptance.get('metrics', [])
        by_task = acceptance.get('by_task', [])

        check_criteria = template_data.get('check_criteria', {})

        sections: list[str] = []
        if system_msg:
            sections.append('# System Role\n' + system_msg)
        if user_msg:
            sections.append('# User Instructions\n' + user_msg)
        if formatted_instruction:
            sections.append('# Main Instruction\n' + formatted_instruction)

        if hard_rules or soft_targets:
            rule_lines: list[str] = []
            if hard_rules:
                rule_lines.append('*Hard Rules*\n' + _fmt_list(hard_rules))
            if soft_targets:
                rule_lines.append('*Soft Targets*\n' + _fmt_list(soft_targets))
            sections.append('# Constraints\n' + '\n\n'.join(rule_lines))

        if task_bullets or task_details:
            detail_lines: list[str] = []
            if task_bullets:
                detail_lines.append('*Primary Tasks*\n' + _fmt_list(task_bullets))
            for detail in task_details:
                name = detail.get('name')
                items = detail.get('items', [])
                if items:
                    lines = []
                    for item in items:
                        text = item.get('text') if isinstance(item, dict) else item
                        lines.append(self._replace_variables(str(text), variables))
                    detail_lines.append(
                        f"*{self._replace_variables(str(name), variables)}*\n" + '\n'.join(f'- {line}' for line in lines)
                    )
            sections.append('# Tasks\n' + '\n\n'.join(detail_lines))

        artifacts = template_data.get('artifacts', {})
        if artifacts:
            art_lines: list[str] = [
                f"- format: {artifacts.get('format', 'unknown')}",
                f"- required_fields: {', '.join(artifacts.get('required_fields', []))}",
            ]
            example_payload = artifacts.get('example')
            if example_payload:
                example_text = (
                    example_payload
                    if isinstance(example_payload, str)
                    else json.dumps(self._sanitize_for_json(example_payload), ensure_ascii=False, indent=2)
                )
                art_lines.append('- example:\n' + str(example_text).strip())
            sections.append('# Output Specification\n' + '\n'.join(art_lines))

        acceptance_lines: list[str] = []
        if checklist:
            acceptance_lines.append('*Checklist*\n' + _fmt_list(checklist))
        if metrics:
            metric_lines = [
                f"- {metric.get('name')}: target={metric.get('target')}, method={metric.get('method')}"
                for metric in metrics
            ]
            acceptance_lines.append('*Metrics*\n' + '\n'.join(metric_lines))
        if by_task:
            bt_lines = [
                f"- {entry.get('id')}: field={entry.get('field')}, rule={entry.get('rule')}"
                for entry in by_task
            ]
            acceptance_lines.append('*By Task*\n' + '\n'.join(bt_lines))
        if acceptance_lines:
            sections.append('# Acceptance Criteria\n' + '\n\n'.join(acceptance_lines))

        if check_criteria:
            criteria_lines: list[str] = []
            for key, guidelines in check_criteria.items():
                header = self._replace_variables(str(key), variables)
                if isinstance(guidelines, list):
                    entries = '\n'.join(
                        f"  - {self._replace_variables(str(item), variables)}" for item in guidelines
                    )
                else:
                    entries = str(guidelines)
                criteria_lines.append(f'- {header}\n{entries}')
            sections.append('# Check Criteria\n' + '\n'.join(criteria_lines))

        if sanitized_input:
            sections.append('# Execution Context\n' + json.dumps(sanitized_input, ensure_ascii=False, indent=2))

        manuscript_block = manuscript_content.strip() if manuscript_content else '(原稿を取得できませんでした)'
        sections.append('# Manuscript\n```markdown\n' + manuscript_block + '\n```')

        return '\n\n'.join(section.strip() for section in sections if section and section.strip()) + '\n'

    def _prepare_template_variables(self, step_id: int, task: dict[str, Any]) -> dict[str, Any]:
        """Prepare template variable substitution map.

        Args:
            step_id: Step ID
            task: Task definition

        Returns:
            Variables dictionary
        """
        return {
            "step_id": step_id,
            "step_slug": self._get_step_slug(step_id),
            "task_name": task.get("name", f"Step {step_id}"),
            "phase": task.get("phase", "unknown"),
            "project_root": str(self.project_root),
            "episode_number": self.episode_number,
            "episode_number_formatted": f"{self.episode_number:03d}",
        }

    def _replace_variables(self, text: str, variables: dict[str, Any]) -> str:
        """Replace template variables in text.

        Args:
            text: Text with variable placeholders
            variables: Variable substitution map

        Returns:
            Text with variables replaced
        """
        result = text
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result

    def _get_step_slug(self, step_id: int) -> str:
        """Get slug identifier for step.

        Args:
            step_id: Step ID

        Returns:
            Slug string (e.g., "step_01")
        """
        return f"step_{step_id:02d}"

    # Manuscript loading

    def _load_manuscript_content(
        self,
        template_data: dict[str, Any] | None,
        variables: dict[str, Any],
        input_data: dict[str, Any],
    ) -> tuple[str, list[Path]]:
        """Load manuscript content from various sources.

        Args:
            template_data: Template data (may specify input files)
            variables: Variable substitution map
            input_data: Input data (may specify manuscript_path or manuscript_content)

        Returns:
            Tuple of (manuscript_content, context_file_paths)
        """
        context_paths: list[Path] = []
        manuscript_content = input_data.get('manuscript_content')
        if isinstance(manuscript_content, str) and manuscript_content.strip():
            return manuscript_content, context_paths

        candidate_paths: list[Path] = []
        manual_path = input_data.get('manuscript_path')
        if manual_path:
            manual = Path(manual_path) if isinstance(manual_path, (str, Path)) else None
            if manual is not None and not manual.is_absolute():
                manual = self.project_root / manual
            if manual is not None:
                candidate_paths.append(manual)

        candidate_paths.extend(self._resolve_template_input_files(template_data, variables))
        guessed = self._guess_episode_manuscript_path()
        if guessed:
            candidate_paths.append(guessed)

        for candidate in candidate_paths:
            try:
                if candidate.exists() and candidate.is_file():
                    content = candidate.read_text(encoding='utf-8')
                    context_paths.append(candidate)
                    return content, context_paths
            except Exception:
                continue
        return '', context_paths

    def _resolve_template_input_files(
        self,
        template_data: dict[str, Any] | None,
        variables: dict[str, Any],
    ) -> list[Path]:
        """Resolve input file paths from template data.

        Args:
            template_data: Template data
            variables: Variable substitution map

        Returns:
            List of resolved file paths
        """
        if not template_data:
            return []

        input_spec = template_data.get("input", {})
        if not isinstance(input_spec, dict):
            return []

        file_patterns = input_spec.get("files", [])
        if not isinstance(file_patterns, list):
            return []

        resolved: list[Path] = []
        for pattern in file_patterns:
            if not isinstance(pattern, str):
                continue
            expanded = self._replace_variables(pattern, variables)
            resolved.extend(self._expand_path_pattern(expanded))

        return resolved

    def _expand_path_pattern(self, pattern: str) -> list[Path]:
        """Expand path pattern with glob support.

        Args:
            pattern: Path pattern (may contain wildcards)

        Returns:
            List of matching paths
        """
        pattern_path = Path(pattern)
        if not pattern_path.is_absolute():
            pattern_path = self.project_root / pattern_path

        if "*" in pattern or "?" in pattern:
            # Glob pattern
            parent = pattern_path.parent
            if parent.exists():
                return list(parent.glob(pattern_path.name))
        elif pattern_path.exists():
            return [pattern_path]

        return []

    def _guess_episode_manuscript_path(self) -> Path | None:
        """Guess manuscript path based on episode number.

        Returns:
            Guessed path or None
        """
        # Try path service first
        try:
            episode_dir = self.path_service.get_episode_dir(self.episode_number)
            if episode_dir:
                manuscript_candidates = [
                    episode_dir / f"EP{self.episode_number:03d}.md",
                    episode_dir / f"EP{self.episode_number:04d}.md",
                    episode_dir / "本文.md",
                    episode_dir / "manuscript.md",
                ]
                for candidate in manuscript_candidates:
                    if candidate.exists():
                        return candidate
        except Exception:
            pass

        # Fallback to project root search
        manuscript_candidates = [
            self.project_root / "episodes" / f"EP{self.episode_number:03d}" / "本文.md",
            self.project_root / "episodes" / f"EP{self.episode_number:04d}" / "本文.md",
            self.project_root / f"EP{self.episode_number:03d}.md",
            self.project_root / f"EP{self.episode_number:04d}.md",
        ]

        for candidate in manuscript_candidates:
            if candidate.exists():
                return candidate

        return None

    def _render_main_instruction(self, result: dict[str, Any]) -> str:
        """Render main instruction section from result.

        Args:
            result: Execution result

        Returns:
            Rendered instruction text
        """
        parts = []

        if "summary" in result:
            parts.append(f"結果: {result['summary']}")

        if "issues" in result and isinstance(result["issues"], list):
            issues = result["issues"]
            if issues:
                parts.append(f"\n検出された課題: {len(issues)}件")
                for idx, issue in enumerate(issues[:3], 1):  # Show first 3
                    if isinstance(issue, dict):
                        parts.append(f"  {idx}. {issue.get('description', 'N/A')}")

        return "\n".join(parts) if parts else "実行完了"

    # Utility methods

    def _sanitize_for_json(self, obj: Any) -> Any:
        """Sanitize object for JSON serialization.

        Args:
            obj: Object to sanitize

        Returns:
            JSON-serializable object
        """
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(item) for item in obj]
        elif isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)

    def _hash_dict(self, data: dict[str, Any]) -> str:
        """Generate hash for dictionary.

        Args:
            data: Dictionary to hash

        Returns:
            SHA256 hash string
        """
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]
