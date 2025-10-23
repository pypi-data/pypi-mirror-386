# File: tests/unit/domain/services/template/test_template_processor.py
# Purpose: Unit tests for TemplateProcessor domain service
# Context: Tests pure business logic for template variable processing

import pytest
from noveler.domain.services.template import TemplateProcessor


# ============================================================================
# Unit Tests - get_step_slug
# ============================================================================


class TestGetStepSlug:
    """Tests for get_step_slug static method."""

    def test_slug_from_mapping(self):
        """get_step_slug() should use SLUG_MAPPING for known task names."""
        assert TemplateProcessor.get_step_slug("誤字脱字チェック") == "typo_check"
        assert TemplateProcessor.get_step_slug("文法・表記統一チェック") == "grammar_check"
        assert TemplateProcessor.get_step_slug("総合品質認定") == "final_quality_approval"

    def test_slug_generation_for_unknown_task(self):
        """get_step_slug() should generate slug for unknown task names."""
        result = TemplateProcessor.get_step_slug("カスタムチェック・その他")
        # "・" → "_", lowercase
        assert result == "カスタムチェック_その他"

    def test_slug_removes_parentheses(self):
        """get_step_slug() should replace （ with _ and remove ）."""
        result = TemplateProcessor.get_step_slug("テスト（補足）チェック")
        # Actual behavior: replace("（", "_").replace("）", "") → "テスト_補足チェック"
        assert result == "テスト_補足チェック"

    def test_slug_empty_string(self):
        """get_step_slug() should handle empty string."""
        result = TemplateProcessor.get_step_slug("")
        assert result == ""

    def test_slug_returns_string(self):
        """get_step_slug() should always return str."""
        result = TemplateProcessor.get_step_slug("任意のタスク")
        assert isinstance(result, str)


# ============================================================================
# Unit Tests - prepare_template_variables
# ============================================================================


class TestPrepareTemplateVariables:
    """Tests for prepare_template_variables static method."""

    def test_prepare_with_current_task(self):
        """prepare_template_variables() should extract task name and phase."""
        variables = TemplateProcessor.prepare_template_variables(
            step_id=1,
            episode_number=5,
            session_id="EP005_202510041230",
            project_root="/path/to/project",
            current_task={"name": "誤字脱字チェック", "phase": "basic_quality"},
            completed_steps=[],
            total_steps=12,
        )

        assert variables["step_id"] == 1
        assert variables["step_name"] == "誤字脱字チェック"
        assert variables["episode_number"] == 5
        assert variables["episode_number_formatted"] == "005"
        assert variables["project_root"] == "/path/to/project"
        assert variables["session_id"] == "EP005_202510041230"
        assert variables["completed_steps"] == 0  # len([]) = 0
        assert variables["total_steps"] == 12
        assert variables["phase"] == "basic_quality"
        assert variables["next_step_id"] == 2

    def test_prepare_without_current_task(self):
        """prepare_template_variables() should use defaults when current_task is None."""
        variables = TemplateProcessor.prepare_template_variables(
            step_id=3,
            episode_number=1,
            session_id="EP001_202510041230",
            project_root="/project",
            current_task=None,
            completed_steps=[1, 2],
            total_steps=12,
        )

        assert variables["step_name"] == "チェックステップ 3"
        assert variables["phase"] == "unknown"
        assert variables["completed_steps"] == 2  # len([1, 2])

    def test_prepare_last_step(self):
        """prepare_template_variables() should set next_step_id to None for last step."""
        variables = TemplateProcessor.prepare_template_variables(
            step_id=12,
            episode_number=1,
            session_id="EP001_202510041230",
            project_root="/project",
            current_task={"name": "最終チェック", "phase": "final"},
            completed_steps=list(range(1, 12)),
            total_steps=12,
        )

        assert variables["next_step_id"] is None

    def test_prepare_episode_number_formatting(self):
        """prepare_template_variables() should format episode_number with 3 digits."""
        variables = TemplateProcessor.prepare_template_variables(
            step_id=1,
            episode_number=1,
            session_id="test",
            project_root="/project",
            current_task=None,
            completed_steps=[],
            total_steps=10,
        )
        assert variables["episode_number_formatted"] == "001"

        variables = TemplateProcessor.prepare_template_variables(
            step_id=1,
            episode_number=99,
            session_id="test",
            project_root="/project",
            current_task=None,
            completed_steps=[],
            total_steps=10,
        )
        assert variables["episode_number_formatted"] == "099"

        variables = TemplateProcessor.prepare_template_variables(
            step_id=1,
            episode_number=123,
            session_id="test",
            project_root="/project",
            current_task=None,
            completed_steps=[],
            total_steps=10,
        )
        assert variables["episode_number_formatted"] == "123"  # No truncation

    def test_prepare_completed_steps_count(self):
        """prepare_template_variables() should return count of completed_steps, not list."""
        variables = TemplateProcessor.prepare_template_variables(
            step_id=5,
            episode_number=1,
            session_id="test",
            project_root="/project",
            current_task=None,
            completed_steps=[1, 2, 3, 4],
            total_steps=10,
        )

        assert variables["completed_steps"] == 4
        assert isinstance(variables["completed_steps"], int)

    def test_prepare_task_without_phase(self):
        """prepare_template_variables() should default phase to 'unknown' if missing."""
        variables = TemplateProcessor.prepare_template_variables(
            step_id=1,
            episode_number=1,
            session_id="test",
            project_root="/project",
            current_task={"name": "カスタムタスク"},  # No 'phase' key
            completed_steps=[],
            total_steps=10,
        )

        assert variables["phase"] == "unknown"


# ============================================================================
# Unit Tests - replace_variables
# ============================================================================


class TestReplaceVariables:
    """Tests for replace_variables static method."""

    def test_replace_single_variable(self):
        """replace_variables() should replace single variable."""
        template = "Episode {episode_number}"
        variables = {"episode_number": 5}

        result = TemplateProcessor.replace_variables(template, variables)

        assert result == "Episode 5"

    def test_replace_multiple_variables(self):
        """replace_variables() should replace multiple variables."""
        template = "Episode {episode_number}: {step_name} (Phase: {phase})"
        variables = {"episode_number": 1, "step_name": "Typo Check", "phase": "basic_quality"}

        result = TemplateProcessor.replace_variables(template, variables)

        assert result == "Episode 1: Typo Check (Phase: basic_quality)"

    def test_replace_with_missing_variable(self):
        """replace_variables() should return template unchanged if variable missing."""
        template = "Episode {episode_number}: {unknown_var}"
        variables = {"episode_number": 1}

        result = TemplateProcessor.replace_variables(template, variables)

        # Should return original template (unchanged)
        assert result == template

    def test_replace_with_empty_variables(self):
        """replace_variables() should return template unchanged if variables is empty."""
        template = "Static text with {variable}"
        variables = {}

        result = TemplateProcessor.replace_variables(template, variables)

        assert result == template

    def test_replace_no_placeholders(self):
        """replace_variables() should return template unchanged if no placeholders."""
        template = "Static text with no placeholders"
        variables = {"episode_number": 1}

        result = TemplateProcessor.replace_variables(template, variables)

        assert result == template

    def test_replace_preserves_japanese_characters(self):
        """replace_variables() should preserve Japanese characters."""
        template = "エピソード {episode_number}: {step_name}"
        variables = {"episode_number": 1, "step_name": "誤字脱字チェック"}

        result = TemplateProcessor.replace_variables(template, variables)

        assert result == "エピソード 1: 誤字脱字チェック"

    def test_replace_with_special_characters(self):
        """replace_variables() should handle special characters in values."""
        template = "Path: {project_root}"
        variables = {"project_root": "C:\\Users\\Test\\Project"}

        result = TemplateProcessor.replace_variables(template, variables)

        assert result == "Path: C:\\Users\\Test\\Project"

    def test_replace_with_numeric_values(self):
        """replace_variables() should handle numeric values."""
        template = "Step {step_id} of {total_steps}"
        variables = {"step_id": 5, "total_steps": 12}

        result = TemplateProcessor.replace_variables(template, variables)

        assert result == "Step 5 of 12"

    def test_replace_repeated_placeholder(self):
        """replace_variables() should replace repeated placeholders."""
        template = "{name} loves {name}"
        variables = {"name": "Alice"}

        result = TemplateProcessor.replace_variables(template, variables)

        assert result == "Alice loves Alice"


# ============================================================================
# Integration Tests
# ============================================================================


class TestTemplateProcessorIntegration:
    """Integration-style tests combining multiple methods."""

    def test_full_workflow(self):
        """Test complete workflow: slug → prepare → replace."""
        # Step 1: Get slug
        task_name = "誤字脱字チェック"
        slug = TemplateProcessor.get_step_slug(task_name)
        assert slug == "typo_check"

        # Step 2: Prepare variables
        variables = TemplateProcessor.prepare_template_variables(
            step_id=1,
            episode_number=5,
            session_id="EP005_202510041230",
            project_root="/project",
            current_task={"name": task_name, "phase": "basic_quality"},
            completed_steps=[],
            total_steps=12,
        )

        # Step 3: Replace in template
        template = "Episode {episode_number_formatted}: {step_name} ({phase})"
        result = TemplateProcessor.replace_variables(template, variables)

        assert result == "Episode 005: 誤字脱字チェック (basic_quality)"

    def test_slug_in_filename_pattern(self):
        """Test slug generation for filename patterns."""
        task_name = "リズム・テンポチェック"
        slug = TemplateProcessor.get_step_slug(task_name)

        variables = TemplateProcessor.prepare_template_variables(
            step_id=11,
            episode_number=1,
            session_id="EP001_202510041230",
            project_root="/project",
            current_task={"name": task_name, "phase": "advanced_quality"},
            completed_steps=list(range(1, 11)),
            total_steps=12,
        )

        filename_template = "check_step{step_id:02d}_{slug}.yaml"
        # Manually add slug to variables (not in prepare_template_variables)
        variables["slug"] = slug

        result = TemplateProcessor.replace_variables(filename_template, variables)

        assert result == "check_step11_rhythm_tempo.yaml"
