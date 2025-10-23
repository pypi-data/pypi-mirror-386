# File: tests/unit/domain/services/progressive_check/test_llm_request_builder.py
# Purpose: Unit tests for LLMRequestBuilder
# Context: Phase 6 Step 2 - LLM request construction extraction

"""Unit tests for LLMRequestBuilder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from noveler.domain.interfaces.logger_interface import NullLogger
from noveler.domain.services.progressive_check.llm_request_builder import LLMRequestBuilder
from noveler.domain.value_objects.universal_prompt_execution import PromptType


class MockCheckTemplateRepository:
    """Mock implementation of ICheckTemplateRepository."""

    def __init__(self) -> None:
        self.templates: dict[str, dict[str, Any]] = {}

    def load_template(self, template_name: str) -> dict[str, Any] | None:
        return self.templates.get(template_name)

    def save_template(self, template_name: str, template_data: dict[str, Any]) -> None:
        self.templates[template_name] = template_data


class MockPathService:
    """Mock implementation of IPathService."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def get_episode_dir(self, episode_number: int) -> Path | None:
        episode_dir = self.project_root / "episodes" / f"EP{episode_number:03d}"
        return episode_dir if episode_dir.exists() else None


@pytest.fixture
def temp_project_root(tmp_path: Path) -> Path:
    """Create temporary project root with necessary directories."""
    episodes_dir = tmp_path / "episodes" / "EP001"
    episodes_dir.mkdir(parents=True, exist_ok=True)

    # Create sample manuscript
    manuscript = episodes_dir / "本文.md"
    manuscript.write_text("# テスト原稿\n\nこれはテスト原稿です。", encoding="utf-8")

    return tmp_path


@pytest.fixture
def mock_template_repo() -> MockCheckTemplateRepository:
    """Create mock template repository."""
    return MockCheckTemplateRepository()


@pytest.fixture
def mock_path_service(temp_project_root: Path) -> MockPathService:
    """Create mock path service."""
    return MockPathService(temp_project_root)


@pytest.fixture
def llm_request_builder(
    temp_project_root: Path,
    mock_template_repo: MockCheckTemplateRepository,
    mock_path_service: MockPathService,
) -> LLMRequestBuilder:
    """Create LLMRequestBuilder instance for testing."""
    return LLMRequestBuilder(
        project_root=temp_project_root,
        episode_number=1,
        template_repository=mock_template_repo,
        path_service=mock_path_service,
        logger=NullLogger(),
    )


class TestLLMRequestBuilderInitialization:
    """Tests for LLMRequestBuilder initialization."""

    def test_init_sets_basic_attributes(
        self,
        llm_request_builder: LLMRequestBuilder,
        temp_project_root: Path,
    ) -> None:
        """Test that initialization sets basic attributes."""
        assert llm_request_builder.project_root == temp_project_root
        assert llm_request_builder.episode_number == 1
        assert llm_request_builder.template_source_log == {}
        assert llm_request_builder.template_metadata_cache == {}

    def test_init_uses_null_logger_if_none(
        self,
        temp_project_root: Path,
        mock_template_repo: MockCheckTemplateRepository,
        mock_path_service: MockPathService,
    ) -> None:
        """Test that NullLogger is used if no logger provided."""
        builder = LLMRequestBuilder(
            project_root=temp_project_root,
            episode_number=1,
            template_repository=mock_template_repo,
            path_service=mock_path_service,
        )

        assert isinstance(builder.logger, NullLogger)


class TestBuildStepRequestPrompt:
    """Tests for build_step_request_prompt method."""

    def test_returns_fallback_when_no_template(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test that fallback instruction is used when no template exists."""
        task = {
            "id": 1,
            "name": "Test Step",
            "llm_instruction": "テストを実行してください",
        }

        prompt = llm_request_builder.build_step_request_prompt(task)

        assert "テストを実行してください" in prompt

    def test_returns_tuple_when_include_context_true(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test that tuple is returned when include_context=True."""
        task = {
            "id": 1,
            "name": "Test Step",
            "llm_instruction": "テストを実行してください",
        }

        result = llm_request_builder.build_step_request_prompt(task, include_context=True)

        assert isinstance(result, tuple)
        assert len(result) == 2
        prompt, payload = result
        assert isinstance(prompt, str)
        assert isinstance(payload, dict)

    def test_uses_template_when_available(
        self,
        llm_request_builder: LLMRequestBuilder,
        mock_template_repo: MockCheckTemplateRepository,
    ) -> None:
        """Test that template is used when available."""
        mock_template_repo.templates["check_step01"] = {
            "llm_config": {
                "role_messages": {
                    "system": "システムメッセージ",
                    "user": "ユーザーメッセージ",
                }
            },
            "prompt": {
                "main_instruction": "メイン指示: {{task_name}}",
            },
        }

        task = {"id": 1, "name": "Test Step"}

        prompt = llm_request_builder.build_step_request_prompt(task)

        assert "システムメッセージ" in prompt
        assert "Test Step" in prompt


class TestCreateLLMRequest:
    """Tests for create_llm_request method."""

    def test_creates_universal_prompt_request(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test that UniversalPromptRequest is created correctly."""
        task = {"id": 1, "name": "Test Step", "phase": "test"}
        payload = {
            "prompt": "テストプロンプト",
            "template_source": {"name": "check_step01"},
            "variables": {"step_id": 1},
            "sanitized_input": {},
            "context_files": [],
        }

        request = llm_request_builder.create_llm_request(task, payload)

        assert request.prompt_content == "テストプロンプト"
        assert request.prompt_type == PromptType.QUALITY_CHECK
        assert request.output_format == "json"
        assert request.max_turns == 1
        assert request.project_context.project_root == llm_request_builder.project_root

    def test_filters_non_existent_context_files(
        self,
        llm_request_builder: LLMRequestBuilder,
        temp_project_root: Path,
    ) -> None:
        """Test that non-existent context files are filtered out."""
        existing_file = temp_project_root / "test.txt"
        existing_file.write_text("test")
        non_existent = temp_project_root / "nonexistent.txt"

        task = {"id": 1, "name": "Test Step"}
        payload = {
            "prompt": "テストプロンプト",
            "context_files": [existing_file, non_existent, "not a path"],
            "template_source": {},
            "variables": {},
            "sanitized_input": {},
        }

        request = llm_request_builder.create_llm_request(task, payload)

        assert len(request.project_context.additional_context_files) == 1
        assert request.project_context.additional_context_files[0] == existing_file


class TestInstructionGeneration:
    """Tests for instruction generation methods."""

    def test_generate_enhanced_llm_instruction_with_next_task(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test enhanced instruction generation with next task."""
        task = {"id": 1, "name": "Step 1"}
        result = {"summary": "完了しました"}
        next_task = {"id": 2, "name": "Step 2"}

        instruction = llm_request_builder.generate_enhanced_llm_instruction(task, result, next_task)

        assert "Step 1 が完了しました" in instruction
        assert "完了しました" in instruction
        assert "Step 2 に進んでください" in instruction

    def test_generate_enhanced_llm_instruction_without_next_task(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test enhanced instruction generation without next task."""
        task = {"id": 3, "name": "Final Step"}
        result = {"summary": "全て完了"}

        instruction = llm_request_builder.generate_enhanced_llm_instruction(task, result, None)

        assert "Final Step が完了しました" in instruction
        assert "すべてのチェックステップが完了しました" in instruction

    def test_generate_llm_instruction_legacy_with_next_step(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test legacy instruction generation with next step."""
        task = {"id": 1, "name": "Step 1"}
        result_summary = "結果サマリー"

        instruction = llm_request_builder.generate_llm_instruction_legacy(task, result_summary, 2)

        assert "ステップ 1 (Step 1) が完了しました" in instruction
        assert "結果サマリー" in instruction
        assert "ステップ 2 に進んでください" in instruction

    def test_generate_error_instruction(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test error instruction generation."""
        task = {"id": 1, "name": "Error Step"}
        error_message = "テストエラーが発生しました"

        instruction = llm_request_builder.generate_error_instruction(task, error_message)

        assert "Error Step の実行中にエラーが発生しました" in instruction
        assert "テストエラーが発生しました" in instruction
        assert "再試行してください" in instruction


class TestTemplateLoading:
    """Tests for template loading operations."""

    def test_load_prompt_template_success(
        self,
        llm_request_builder: LLMRequestBuilder,
        mock_template_repo: MockCheckTemplateRepository,
    ) -> None:
        """Test successful template loading."""
        template_data = {
            "version": "2.0",
            "prompt": {"main_instruction": "Test instruction"},
        }
        mock_template_repo.templates["check_step01"] = template_data

        loaded = llm_request_builder._load_prompt_template(1)

        assert loaded == template_data
        assert 1 in llm_request_builder.template_source_log
        assert llm_request_builder.template_source_log[1]["name"] == "check_step01"

    def test_load_prompt_template_not_found(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test template loading when template not found."""
        loaded = llm_request_builder._load_prompt_template(99)

        assert loaded is None

    def test_load_prompt_template_invalid_structure(
        self,
        llm_request_builder: LLMRequestBuilder,
        mock_template_repo: MockCheckTemplateRepository,
    ) -> None:
        """Test template loading with invalid structure."""
        mock_template_repo.templates["check_step01"] = "invalid"  # Not a dict

        loaded = llm_request_builder._load_prompt_template(1)

        assert loaded is None

    def test_collect_template_metadata(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test template metadata collection."""
        template_data = {
            "version": "2.0",
            "prompt": {"main_instruction": "Test"},
        }

        metadata = llm_request_builder._collect_template_metadata(1, template_data, "check_step01")

        assert metadata["source"] == "template_repository"
        assert metadata["name"] == "check_step01"
        assert metadata["step_id"] == 1
        assert metadata["version"] == "2.0"
        assert "hash" in metadata


class TestVariableHandling:
    """Tests for variable handling operations."""

    def test_prepare_template_variables(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test template variable preparation."""
        task = {"id": 3, "name": "Test Step", "phase": "validation"}

        variables = llm_request_builder._prepare_template_variables(3, task)

        assert variables["step_id"] == 3
        assert variables["step_slug"] == "step_03"
        assert variables["task_name"] == "Test Step"
        assert variables["phase"] == "validation"
        assert variables["episode_number"] == 1
        assert variables["episode_number_formatted"] == "001"

    def test_replace_variables(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test variable replacement in text."""
        text = "Step {{step_id}}: {{task_name}} in {{phase}}"
        variables = {
            "step_id": 1,
            "task_name": "Test",
            "phase": "validation",
        }

        result = llm_request_builder._replace_variables(text, variables)

        assert result == "Step 1: Test in validation"

    def test_get_step_slug(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test step slug generation."""
        assert llm_request_builder._get_step_slug(1) == "step_01"
        assert llm_request_builder._get_step_slug(12) == "step_12"


class TestManuscriptLoading:
    """Tests for manuscript loading operations."""

    def test_load_manuscript_from_input_data_content(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test loading manuscript from input_data.manuscript_content."""
        input_data = {"manuscript_content": "直接提供された原稿"}

        content, paths = llm_request_builder._load_manuscript_content(None, {}, input_data)

        assert content == "直接提供された原稿"
        assert paths == []

    def test_load_manuscript_from_input_data_path(
        self,
        llm_request_builder: LLMRequestBuilder,
        temp_project_root: Path,
    ) -> None:
        """Test loading manuscript from input_data.manuscript_path."""
        manuscript_file = temp_project_root / "custom.md"
        manuscript_file.write_text("カスタム原稿", encoding="utf-8")

        input_data = {"manuscript_path": str(manuscript_file)}

        content, paths = llm_request_builder._load_manuscript_content(None, {}, input_data)

        assert content == "カスタム原稿"
        assert manuscript_file in paths

    def test_load_manuscript_from_episode_guess(
        self,
        llm_request_builder: LLMRequestBuilder,
        temp_project_root: Path,
    ) -> None:
        """Test loading manuscript from episode path guess."""
        content, paths = llm_request_builder._load_manuscript_content(None, {}, {})

        assert "テスト原稿" in content
        assert len(paths) == 1

    def test_load_manuscript_returns_empty_when_not_found(
        self,
        temp_project_root: Path,
        mock_template_repo: MockCheckTemplateRepository,
        mock_path_service: MockPathService,
    ) -> None:
        """Test that empty string is returned when manuscript not found."""
        # Create builder with episode that doesn't exist
        builder = LLMRequestBuilder(
            project_root=temp_project_root,
            episode_number=999,
            template_repository=mock_template_repo,
            path_service=mock_path_service,
        )

        content, paths = builder._load_manuscript_content(None, {}, {})

        assert content == ""
        assert paths == []

    def test_guess_episode_manuscript_path(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test episode manuscript path guessing."""
        path = llm_request_builder._guess_episode_manuscript_path()

        assert path is not None
        assert path.exists()
        assert "本文.md" in str(path)


class TestUtilityMethods:
    """Tests for utility methods."""

    def test_sanitize_for_json_handles_dict(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test JSON sanitization for dict."""
        test_path = Path("/test/path")
        data = {"key": "value", "path": test_path}

        result = llm_request_builder._sanitize_for_json(data)

        assert result["key"] == "value"
        assert result["path"] == str(test_path)

    def test_sanitize_for_json_handles_list(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test JSON sanitization for list."""
        test_path = Path("/test")
        data = ["text", 123, test_path, True, None]

        result = llm_request_builder._sanitize_for_json(data)

        assert result == ["text", 123, str(test_path), True, None]

    def test_sanitize_for_json_handles_primitives(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test JSON sanitization for primitives."""
        assert llm_request_builder._sanitize_for_json("text") == "text"
        assert llm_request_builder._sanitize_for_json(123) == 123
        assert llm_request_builder._sanitize_for_json(12.5) == 12.5
        assert llm_request_builder._sanitize_for_json(True) is True
        assert llm_request_builder._sanitize_for_json(None) is None

    def test_hash_dict(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test dictionary hashing."""
        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}  # Same content, different order
        data3 = {"a": 1, "b": 3}  # Different content

        hash1 = llm_request_builder._hash_dict(data1)
        hash2 = llm_request_builder._hash_dict(data2)
        hash3 = llm_request_builder._hash_dict(data3)

        assert hash1 == hash2  # Order doesn't matter
        assert hash1 != hash3  # Different content = different hash
        assert len(hash1) == 16  # Hash is truncated to 16 chars


class TestRenderMainInstruction:
    """Tests for _render_main_instruction method."""

    def test_render_with_summary_only(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering instruction with summary only."""
        result = {"summary": "処理完了"}

        instruction = llm_request_builder._render_main_instruction(result)

        assert "結果: 処理完了" in instruction

    def test_render_with_issues(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering instruction with issues."""
        result = {
            "summary": "課題検出",
            "issues": [
                {"description": "Issue 1"},
                {"description": "Issue 2"},
                {"description": "Issue 3"},
                {"description": "Issue 4"},  # Only first 3 shown
            ],
        }

        instruction = llm_request_builder._render_main_instruction(result)

        assert "検出された課題: 4件" in instruction
        assert "Issue 1" in instruction
        assert "Issue 3" in instruction
        assert "Issue 4" not in instruction  # 4th issue not shown

    def test_render_with_empty_result(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering instruction with empty result."""
        result = {}

        instruction = llm_request_builder._render_main_instruction(result)

        assert instruction == "実行完了"


class TestPreparePromptPayload:
    """Tests for _prepare_prompt_payload method."""

    def test_prepare_payload_with_template(
        self,
        llm_request_builder: LLMRequestBuilder,
        mock_template_repo: MockCheckTemplateRepository,
    ) -> None:
        """Test payload preparation with template."""
        mock_template_repo.templates["check_step01"] = {
            "version": "2.0",
            "llm_config": {"role_messages": {"system": "System", "user": "User"}},
            "prompt": {"main_instruction": "Test {{step_id}}"},
        }

        task = {"id": 1, "name": "Test Step"}
        input_data = {"test_key": "test_value"}

        payload = llm_request_builder._prepare_prompt_payload(task, input_data)

        assert "prompt" in payload
        assert "template_data" in payload
        assert "template_source" in payload
        assert "variables" in payload
        assert "sanitized_input" in payload
        assert payload["sanitized_input"]["test_key"] == "test_value"

    def test_prepare_payload_without_template(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test payload preparation without template (fallback)."""
        task = {"id": 99, "name": "Fallback Step", "llm_instruction": "Fallback instruction"}
        input_data = {}

        payload = llm_request_builder._prepare_prompt_payload(task, input_data)

        assert "prompt" in payload
        assert "Fallback instruction" in payload["prompt"]
        assert payload["template_data"] is None

    def test_prepare_payload_includes_project_root(
        self,
        llm_request_builder: LLMRequestBuilder,
        temp_project_root: Path,
    ) -> None:
        """Test that payload includes project_root in variables."""
        task = {"id": 1, "name": "Test"}

        payload = llm_request_builder._prepare_prompt_payload(task, {})

        assert str(temp_project_root) in payload["variables"]["project_root"]

    def test_prepare_payload_includes_episode_number(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test that payload includes episode_number in variables."""
        task = {"id": 1, "name": "Test"}

        payload = llm_request_builder._prepare_prompt_payload(task, {})

        assert payload["variables"]["episode_number"] == 1
        assert payload["variables"]["episode_number_formatted"] == "001"


class TestRenderQualityTemplate:
    """Tests for _render_quality_template method."""

    def test_render_template_with_role_messages(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering template with role messages."""
        template_data = {
            "llm_config": {
                "role_messages": {
                    "system": "You are a checker",
                    "user": "Check the manuscript",
                },
            },
            "prompt": {
                "main_instruction": "Perform quality check",
            },
        }
        variables = {"step_id": 1}

        rendered = llm_request_builder._render_quality_template(
            template_data, variables, "Test manuscript", {}
        )

        assert "You are a checker" in rendered
        assert "Check the manuscript" in rendered
        assert "Perform quality check" in rendered

    def test_render_template_with_variable_substitution(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test variable substitution in template rendering."""
        template_data = {
            "llm_config": {"role_messages": {}},
            "prompt": {
                "main_instruction": "Step {{step_id}}: {{task_name}}",
            },
        }
        variables = {"step_id": 5, "task_name": "Quality Check"}

        rendered = llm_request_builder._render_quality_template(
            template_data, variables, "", {}
        )

        assert "Step 5: Quality Check" in rendered

    def test_render_template_with_criteria_list(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering template with constraints."""
        template_data = {
            "llm_config": {"role_messages": {}},
            "prompt": {
                "main_instruction": "Check criteria",
            },
            "constraints": {
                "hard_rules": [
                    "Criterion 1",
                    "Criterion 2: {{step_id}}",
                ],
            },
        }
        variables = {"step_id": 3}

        rendered = llm_request_builder._render_quality_template(
            template_data, variables, "", {}
        )

        assert "# Constraints" in rendered
        assert "- Criterion 1" in rendered
        assert "- Criterion 2: 3" in rendered

    def test_render_template_with_soft_targets(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering template with soft_targets in constraints."""
        template_data = {
            "llm_config": {"role_messages": {}},
            "prompt": {"main_instruction": "Check"},
            "constraints": {
                "hard_rules": ["Rule 1"],
                "soft_targets": ["Target 1", "Target 2"],
            },
        }

        rendered = llm_request_builder._render_quality_template(
            template_data, {}, "", {}
        )

        assert "# Constraints" in rendered
        assert "*Hard Rules*" in rendered
        assert "*Soft Targets*" in rendered
        assert "- Target 1" in rendered
        assert "- Target 2" in rendered

    def test_render_template_with_dict_items_in_list(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering template with dict items in constraints (coverage for line 372-374)."""
        template_data = {
            "llm_config": {"role_messages": {}},
            "prompt": {"main_instruction": "Check"},
            "constraints": {
                "hard_rules": [
                    "String rule",
                    {"type": "structured", "value": "complex rule"},
                ],
            },
        }

        rendered = llm_request_builder._render_quality_template(
            template_data, {}, "", {}
        )

        assert "# Constraints" in rendered
        assert "String rule" in rendered
        assert '"type": "structured"' in rendered or '"type":"structured"' in rendered

    def test_render_template_with_task_details(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering template with task details (coverage for line 422-432)."""
        template_data = {
            "llm_config": {"role_messages": {}},
            "prompt": {"main_instruction": "Check"},
            "tasks": {
                "bullets": ["Primary task"],
                "details": [
                    {
                        "name": "Detail Section {{step_id}}",
                        "items": [
                            "Item 1",
                            {"text": "Item 2"},
                            "Item 3",
                        ],
                    },
                ],
            },
        }
        variables = {"step_id": 7}

        rendered = llm_request_builder._render_quality_template(
            template_data, variables, "", {}
        )

        assert "# Tasks" in rendered
        assert "*Primary Tasks*" in rendered
        assert "*Detail Section 7*" in rendered
        assert "- Item 1" in rendered
        assert "- Item 2" in rendered
        assert "- Item 3" in rendered

    def test_render_template_with_artifacts(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering template with artifacts (coverage for line 437-449)."""
        template_data = {
            "llm_config": {"role_messages": {}},
            "prompt": {"main_instruction": "Check"},
            "artifacts": {
                "format": "json",
                "required_fields": ["summary", "issues"],
                "example": {"summary": "Example summary", "issues": []},
            },
        }

        rendered = llm_request_builder._render_quality_template(
            template_data, {}, "", {}
        )

        assert "# Output Specification" in rendered
        assert "- format: json" in rendered
        assert "- required_fields: summary, issues" in rendered
        assert "- example:" in rendered
        assert '"summary": "Example summary"' in rendered or '"summary":"Example summary"' in rendered

    def test_render_template_with_acceptance_criteria_metrics(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering template with metrics in acceptance_criteria (coverage for line 454-459)."""
        template_data = {
            "llm_config": {"role_messages": {}},
            "prompt": {"main_instruction": "Check"},
            "acceptance_criteria": {
                "checklist": ["Item 1"],
                "metrics": [
                    {"name": "Score", "target": ">= 80", "method": "automated"},
                    {"name": "Coverage", "target": "100%", "method": "manual"},
                ],
            },
        }

        rendered = llm_request_builder._render_quality_template(
            template_data, {}, "", {}
        )

        assert "# Acceptance Criteria" in rendered
        assert "*Metrics*" in rendered
        assert "- Score: target=>= 80, method=automated" in rendered
        assert "- Coverage: target=100%, method=manual" in rendered

    def test_render_template_with_acceptance_criteria_by_task(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering template with by_task in acceptance_criteria (coverage for line 460-465)."""
        template_data = {
            "llm_config": {"role_messages": {}},
            "prompt": {"main_instruction": "Check"},
            "acceptance_criteria": {
                "by_task": [
                    {"id": "TASK-1", "field": "status", "rule": "completed"},
                    {"id": "TASK-2", "field": "quality", "rule": "high"},
                ],
            },
        }

        rendered = llm_request_builder._render_quality_template(
            template_data, {}, "", {}
        )

        assert "# Acceptance Criteria" in rendered
        assert "*By Task*" in rendered
        assert "- TASK-1: field=status, rule=completed" in rendered
        assert "- TASK-2: field=quality, rule=high" in rendered

    def test_render_template_with_check_criteria(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering template with check_criteria (coverage for line 469-480)."""
        template_data = {
            "llm_config": {"role_messages": {}},
            "prompt": {"main_instruction": "Check"},
            "check_criteria": {
                "Grammar": ["Check spelling", "Check punctuation"],
                "Style {{step_id}}": ["Check consistency", "Check tone"],
                "Length": "Must be under 5000 characters",
            },
        }
        variables = {"step_id": 3}

        rendered = llm_request_builder._render_quality_template(
            template_data, variables, "", {}
        )

        assert "# Check Criteria" in rendered
        assert "- Grammar" in rendered
        assert "  - Check spelling" in rendered
        assert "  - Check punctuation" in rendered
        assert "- Style 3" in rendered
        assert "  - Check consistency" in rendered
        assert "  - Check tone" in rendered
        assert "- Length" in rendered
        assert "Must be under 5000 characters" in rendered

    def test_render_template_with_manuscript_placeholder(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering template with {{manuscript}} placeholder."""
        template_data = {
            "llm_config": {"role_messages": {}},
            "prompt": {
                "main_instruction": "Check: {{manuscript}}",
            },
        }
        variables = {}
        manuscript = "Sample manuscript content"

        rendered = llm_request_builder._render_quality_template(
            template_data, variables, manuscript, {}
        )

        assert "Sample manuscript content" in rendered

    def test_render_template_with_tasks_section(
        self,
        llm_request_builder: LLMRequestBuilder,
    ) -> None:
        """Test rendering template with tasks section."""
        template_data = {
            "llm_config": {"role_messages": {}},
            "prompt": {
                "main_instruction": "Check",
            },
            "tasks": {
                "bullets": [
                    "Task 1",
                    "Task 2: {{step_id}}",
                ],
            },
        }
        variables = {"step_id": 5}

        rendered = llm_request_builder._render_quality_template(
            template_data, variables, "", {}
        )

        assert "# Tasks" in rendered
        assert "- Task 1" in rendered
        assert "- Task 2: 5" in rendered
