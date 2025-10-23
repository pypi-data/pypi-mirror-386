# File: src/noveler/domain/services/v2_prompt_synthesis_service.py
# Purpose: Synthesize prompts using Schema v2 structured sections
# Context: Prioritizes structured sections over main_instruction for better LLM guidance

"""Schema v2 structured prompt synthesis service."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class V2PromptSynthesisService:
    """Service for synthesizing prompts using Schema v2 structured sections."""

    def __init__(self, logger=None):
        """Initialize the service with optional logger."""
        self.logger = logger

    def synthesize_prompt(
        self,
        template_path: Path,
        variables: Dict[str, Any],
        use_structured_sections: bool = True
    ) -> str:
        """
        Synthesize a prompt from a Schema v2 template.

        Args:
            template_path: Path to the YAML template file
            variables: Variables to substitute in the template
            use_structured_sections: Whether to use structured sections (v2) or fall back to main_instruction

        Returns:
            Synthesized prompt string
        """
        # Load template
        with open(template_path, 'r', encoding='utf-8') as f:
            template = yaml.safe_load(f)

        # Substitute variables in template
        template = self._substitute_variables(template, variables)

        if use_structured_sections and self._has_structured_sections(template):
            return self._synthesize_structured_prompt(template)
        else:
            return self._synthesize_legacy_prompt(template)

    def _has_structured_sections(self, template: Dict[str, Any]) -> bool:
        """Check if template has v2 structured sections."""
        required_sections = ['inputs', 'constraints', 'tasks', 'artifacts']
        return all(section in template for section in required_sections)

    def _synthesize_structured_prompt(self, template: Dict[str, Any]) -> str:
        """Synthesize prompt using v2 structured sections."""
        prompt_parts = []

        # Add role messages if present
        if 'llm_config' in template and 'role_messages' in template['llm_config']:
            role_msgs = template['llm_config']['role_messages']
            if 'system' in role_msgs:
                prompt_parts.append(f"# System Role\n{role_msgs['system'].strip()}\n")
            if 'user' in role_msgs:
                prompt_parts.append(f"# User Request\n{role_msgs['user'].strip()}\n")

        # Add main instruction if present
        if 'prompt' in template and 'main_instruction' in template['prompt']:
            prompt_parts.append(f"# Main Instruction\n{template['prompt']['main_instruction'].strip()}\n")

        # Add inputs section
        if 'inputs' in template:
            prompt_parts.append(self._format_inputs_section(template['inputs']))

        # Add constraints section
        if 'constraints' in template:
            prompt_parts.append(self._format_constraints_section(template['constraints']))

        # Add tasks section
        if 'tasks' in template:
            prompt_parts.append(self._format_tasks_section(template['tasks']))

        # Add artifacts section
        if 'artifacts' in template:
            prompt_parts.append(self._format_artifacts_section(template['artifacts']))

        # Add acceptance criteria section
        if 'acceptance_criteria' in template:
            prompt_parts.append(self._format_acceptance_section(template['acceptance_criteria']))

        # Add output format enforcement
        prompt_parts.append(self._add_output_format_enforcement())

        return "\n".join(prompt_parts)

    def _synthesize_legacy_prompt(self, template: Dict[str, Any]) -> str:
        """Synthesize prompt using legacy main_instruction approach."""
        if 'prompt' in template and 'main_instruction' in template['prompt']:
            return template['prompt']['main_instruction']
        return "No prompt content available"

    def _format_inputs_section(self, inputs: Dict[str, Any]) -> str:
        """Format the inputs section."""
        lines = ["# Inputs"]

        if 'files' in inputs:
            lines.append("\n## Required Files:")
            for file_spec in inputs['files']:
                if isinstance(file_spec, dict):
                    path = file_spec.get('path', '')
                    desc = file_spec.get('description', '')
                    required = file_spec.get('required', False)
                    req_mark = " (REQUIRED)" if required else ""
                    lines.append(f"- {path}: {desc}{req_mark}")

        if 'variables' in inputs:
            lines.append("\n## Variables:")
            for var_name, var_spec in inputs['variables'].items():
                if isinstance(var_spec, dict):
                    var_type = var_spec.get('type', 'string')
                    required = var_spec.get('required', False)
                    req_mark = " (REQUIRED)" if required else ""
                    lines.append(f"- {var_name}: {var_type}{req_mark}")

        return "\n".join(lines) + "\n"

    def _format_constraints_section(self, constraints: Dict[str, Any]) -> str:
        """Format the constraints section."""
        lines = ["# Constraints"]

        if 'hard_rules' in constraints:
            lines.append("\n## Hard Rules (MUST follow):")
            for rule in constraints['hard_rules']:
                lines.append(f"- {rule}")

        if 'soft_targets' in constraints:
            lines.append("\n## Soft Targets (SHOULD follow):")
            for target in constraints['soft_targets']:
                lines.append(f"- {target}")

        return "\n".join(lines) + "\n"

    def _format_tasks_section(self, tasks: Dict[str, Any]) -> str:
        """Format the tasks section."""
        lines = ["# Tasks"]

        if 'bullets' in tasks:
            lines.append("\n## Main Tasks:")
            for task in tasks['bullets']:
                lines.append(f"- {task}")

        if 'details' in tasks:
            lines.append("\n## Detailed Tasks:")
            for detail_group in tasks['details']:
                if isinstance(detail_group, dict):
                    name = detail_group.get('name', 'Tasks')
                    lines.append(f"\n### {name}:")
                    if 'items' in detail_group:
                        for item in detail_group['items']:
                            if isinstance(item, dict):
                                item_id = item.get('id', '')
                                text = item.get('text', '')
                                lines.append(f"- [{item_id}] {text}")

        return "\n".join(lines) + "\n"

    def _format_artifacts_section(self, artifacts: Dict[str, Any]) -> str:
        """Format the artifacts section."""
        lines = ["# Expected Output"]

        lines.append(f"\n## Format: {artifacts.get('format', 'text')}")

        if 'required_fields' in artifacts:
            lines.append("\n## Required Fields:")
            for field in artifacts['required_fields']:
                lines.append(f"- {field}")

        if 'example' in artifacts:
            lines.append("\n## Example Output:")
            lines.append("```")
            lines.append(artifacts['example'].strip())
            lines.append("```")

        return "\n".join(lines) + "\n"

    def _format_acceptance_section(self, acceptance: Dict[str, Any]) -> str:
        """Format the acceptance criteria section."""
        lines = ["# Acceptance Criteria"]

        if 'checklist' in acceptance:
            lines.append("\n## Checklist:")
            for check in acceptance['checklist']:
                lines.append(f"- [ ] {check}")

        if 'metrics' in acceptance:
            lines.append("\n## Metrics:")
            for metric in acceptance['metrics']:
                if isinstance(metric, dict):
                    name = metric.get('name', '')
                    target = metric.get('target', '')
                    method = metric.get('method', '')
                    lines.append(f"- {name}: {target} (Measured by: {method})")

        if 'by_task' in acceptance:
            lines.append("\n## Task-specific Criteria:")
            for task_id, criteria in acceptance['by_task'].items():
                if isinstance(criteria, dict):
                    target = criteria.get('target', '')
                    lines.append(f"- [{task_id}] {target}")

        return "\n".join(lines) + "\n"

    def _add_output_format_enforcement(self) -> str:
        """Add instructions to enforce YAML-only output in fenced code blocks."""
        return """# Output Requirements

**IMPORTANT**: Your output MUST follow these rules:
1. If outputting YAML, it MUST be wrapped in triple backticks (```)
2. NO explanations or text outside the code blocks
3. The YAML must be valid and properly formatted
4. Include all required fields as specified in the artifacts section

Example of correct output format:
```yaml
# Your YAML content here
field1: value1
field2: value2
```

DO NOT add any text before or after the YAML block.
"""

    def _substitute_variables(self, template: Any, variables: Dict[str, Any]) -> Any:
        """Recursively substitute variables in the template."""
        if isinstance(template, dict):
            return {k: self._substitute_variables(v, variables) for k, v in template.items()}
        elif isinstance(template, list):
            return [self._substitute_variables(item, variables) for item in template]
        elif isinstance(template, str):
            # Simple variable substitution using format strings
            for key, value in variables.items():
                template = template.replace(f"{{{key}}}", str(value))
                # Also handle variations like {key:03d}
                if "episode_number" in key:
                    template = template.replace(f"{{{key}:03d}}", f"{int(value):03d}")
            return template
        else:
            return template