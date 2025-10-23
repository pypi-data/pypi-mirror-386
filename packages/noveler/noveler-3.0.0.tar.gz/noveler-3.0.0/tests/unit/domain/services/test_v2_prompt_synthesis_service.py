# File: tests/unit/domain/services/test_v2_prompt_synthesis_service.py
# Purpose: Test the V2 prompt synthesis service
# Context: Ensures structured sections are properly formatted for LLM consumption

"""Tests for V2 prompt synthesis service."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import yaml

from noveler.domain.services.v2_prompt_synthesis_service import V2PromptSynthesisService


class TestV2PromptSynthesisService:
    """Test cases for V2 prompt synthesis service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = V2PromptSynthesisService()
        self.sample_template = {
            "metadata": {
                "step_id": 12,
                "step_name": "初稿執筆"
            },
            "llm_config": {
                "role_messages": {
                    "system": "You are a skilled novelist.",
                    "user": "Write the first draft."
                }
            },
            "prompt": {
                "main_instruction": "Generate episode {episode_number}"
            },
            "inputs": {
                "files": [
                    {
                        "path": "{project_root}/step*.yaml",
                        "required": True,
                        "description": "Design files"
                    }
                ],
                "variables": {
                    "episode_number": {"type": "int", "required": True},
                    "project_root": {"type": "path", "required": True}
                }
            },
            "constraints": {
                "hard_rules": ["Word count >= 8000", "Single POV per scene"],
                "soft_targets": ["Section balance 15/70/15%", "Dialogue-driven tempo"]
            },
            "tasks": {
                "bullets": ["Integrate designs", "Show don't tell"],
                "details": [
                    {
                        "name": "Integration",
                        "items": [
                            {"id": "integrate.balance", "text": "Balance sections"},
                            {"id": "integrate.emotion", "text": "Follow emotion curve"}
                        ]
                    }
                ]
            },
            "artifacts": {
                "format": "md",
                "required_fields": ["title_heading", "body_present"],
                "example": "# Episode {episode_number}\n\nContent here..."
            },
            "acceptance_criteria": {
                "checklist": ["Meta comment included", "Markdown only"],
                "metrics": [
                    {
                        "name": "unicode_char_count",
                        "target": ">= 8000",
                        "method": "Count Unicode characters"
                    }
                ],
                "by_task": {
                    "integrate.balance": {
                        "rule": "checklist",
                        "target": "Sections are balanced"
                    }
                }
            }
        }

    def test_has_structured_sections(self):
        """Test detection of structured sections."""
        assert self.service._has_structured_sections(self.sample_template) is True

        # Remove a required section
        incomplete = self.sample_template.copy()
        del incomplete['inputs']
        assert self.service._has_structured_sections(incomplete) is False

    def test_format_inputs_section(self):
        """Test formatting of inputs section."""
        result = self.service._format_inputs_section(self.sample_template['inputs'])

        assert "# Inputs" in result
        assert "## Required Files:" in result
        assert "{project_root}/step*.yaml" in result
        assert "(REQUIRED)" in result
        assert "## Variables:" in result
        assert "episode_number: int (REQUIRED)" in result

    def test_format_constraints_section(self):
        """Test formatting of constraints section."""
        result = self.service._format_constraints_section(self.sample_template['constraints'])

        assert "# Constraints" in result
        assert "## Hard Rules (MUST follow):" in result
        assert "Word count >= 8000" in result
        assert "## Soft Targets (SHOULD follow):" in result
        assert "Section balance 15/70/15%" in result

    def test_format_tasks_section(self):
        """Test formatting of tasks section."""
        result = self.service._format_tasks_section(self.sample_template['tasks'])

        assert "# Tasks" in result
        assert "## Main Tasks:" in result
        assert "Integrate designs" in result
        assert "## Detailed Tasks:" in result
        assert "### Integration:" in result
        assert "[integrate.balance] Balance sections" in result

    def test_format_artifacts_section(self):
        """Test formatting of artifacts section."""
        result = self.service._format_artifacts_section(self.sample_template['artifacts'])

        assert "# Expected Output" in result
        assert "## Format: md" in result
        assert "## Required Fields:" in result
        assert "title_heading" in result
        assert "## Example Output:" in result
        assert "```" in result

    def test_format_acceptance_section(self):
        """Test formatting of acceptance criteria section."""
        result = self.service._format_acceptance_section(self.sample_template['acceptance_criteria'])

        assert "# Acceptance Criteria" in result
        assert "## Checklist:" in result
        assert "[ ] Meta comment included" in result
        assert "## Metrics:" in result
        assert "unicode_char_count: >= 8000" in result
        assert "## Task-specific Criteria:" in result
        assert "[integrate.balance] Sections are balanced" in result

    def test_substitute_variables(self):
        """Test variable substitution."""
        template_str = "Episode {episode_number:03d} at {project_root}"
        variables = {"episode_number": 1, "project_root": "/path/to/project"}

        result = self.service._substitute_variables(template_str, variables)
        assert result == "Episode 001 at /path/to/project"

    def test_synthesize_structured_prompt(self):
        """Test synthesis of structured prompt."""
        result = self.service._synthesize_structured_prompt(self.sample_template)

        # Check all major sections are present
        assert "# System Role" in result
        assert "# User Request" in result
        assert "# Main Instruction" in result
        assert "# Inputs" in result
        assert "# Constraints" in result
        assert "# Tasks" in result
        assert "# Expected Output" in result
        assert "# Acceptance Criteria" in result
        assert "# Output Requirements" in result
        assert "IMPORTANT" in result
        assert "triple backticks" in result

    def test_synthesize_legacy_prompt(self):
        """Test fallback to legacy prompt synthesis."""
        legacy_template = {
            "prompt": {
                "main_instruction": "This is a legacy prompt"
            }
        }

        result = self.service._synthesize_legacy_prompt(legacy_template)
        assert result == "This is a legacy prompt"

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_synthesize_prompt_with_file(self, mock_yaml_load, mock_file):
        """Test full prompt synthesis from file."""
        mock_yaml_load.return_value = self.sample_template

        variables = {"episode_number": 1, "project_root": "/project"}
        result = self.service.synthesize_prompt(
            Path("template.yaml"),
            variables,
            use_structured_sections=True
        )

        # Verify file was opened
        mock_file.assert_called_once_with(Path("template.yaml"), 'r', encoding='utf-8')

        # Check structured prompt was generated
        assert "# System Role" in result
        assert "# Inputs" in result
        assert "/project" in result  # Variable was substituted

    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_synthesize_prompt_fallback_to_legacy(self, mock_yaml_load, mock_file):
        """Test fallback to legacy when structured sections missing."""
        legacy_template = {
            "prompt": {
                "main_instruction": "Legacy instruction for episode {episode_number}"
            }
        }
        mock_yaml_load.return_value = legacy_template

        variables = {"episode_number": 1}
        result = self.service.synthesize_prompt(
            Path("template.yaml"),
            variables,
            use_structured_sections=True
        )

        # Should fall back to legacy
        assert result == "Legacy instruction for episode 1"

    def test_output_format_enforcement(self):
        """Test that output format enforcement is added."""
        result = self.service._add_output_format_enforcement()

        assert "IMPORTANT" in result
        assert "triple backticks" in result
        assert "```yaml" in result
        assert "NO explanations" in result
        assert "valid and properly formatted" in result