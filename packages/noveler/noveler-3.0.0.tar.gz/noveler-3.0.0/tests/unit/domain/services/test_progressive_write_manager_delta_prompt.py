# File: tests/unit/domain/services/test_progressive_write_manager_delta_prompt.py
# Purpose: Test delta prompt generation for by_task validation retry logic
# Context: Tests the Generator Retry Policy feature

"""Unit tests for delta prompt generation in ProgressiveWriteManager.

Tests cover:
- _extract_failed_tasks(): Extraction of failed tasks from validation summary
- _compose_delta_prompt(): Composition of retry prompt with failure context
- Integration with by_task validation retry flow
"""

import pytest

from noveler.domain.services.progressive_write_manager import ProgressiveWriteManager


class TestExtractFailedTasks:
    """Test _extract_failed_tasks() method."""

    def test_extract_single_failed_task(self, mock_deps):
        """Test extracting a single failed task from validation summary."""
        manager = ProgressiveWriteManager(
            project_root="/tmp/test_project",
            episode_number=1,
            deps=mock_deps,
        )

        validation_summary = {
            "success": False,
            "by_task": [
                {
                    "id": "task_001",
                    "status": "fail",
                    "value": None,
                    "notes": ["field_missing"],
                },
                {
                    "id": "task_002",
                    "status": "pass",
                    "value": "valid_value",
                    "notes": [],
                },
            ],
        }

        failed_tasks = manager._extract_failed_tasks(validation_summary)

        assert len(failed_tasks) == 1
        assert failed_tasks[0]["id"] == "task_001"
        assert failed_tasks[0]["value"] is None
        assert "field_missing" in failed_tasks[0]["notes"]

    def test_extract_multiple_failed_tasks(self, mock_deps):
        """Test extracting multiple failed tasks."""
        manager = ProgressiveWriteManager(
            project_root="/tmp/test_project",
            episode_number=1,
            deps=mock_deps,
        )

        validation_summary = {
            "success": False,
            "by_task": [
                {
                    "id": "task_001",
                    "status": "fail",
                    "value": None,
                    "notes": ["field_missing"],
                },
                {
                    "id": "task_002",
                    "status": "fail",
                    "value": "invalid",
                    "notes": ["nonempty"],
                },
                {
                    "id": "task_003",
                    "status": "pass",
                    "value": "valid",
                    "notes": [],
                },
            ],
        }

        failed_tasks = manager._extract_failed_tasks(validation_summary)

        assert len(failed_tasks) == 2
        assert {t["id"] for t in failed_tasks} == {"task_001", "task_002"}

    def test_extract_no_failed_tasks(self, mock_deps):
        """Test extraction when all tasks pass."""
        manager = ProgressiveWriteManager(
            project_root="/tmp/test_project",
            episode_number=1,
            deps=mock_deps,
        )

        validation_summary = {
            "success": True,
            "by_task": [
                {"id": "task_001", "status": "pass", "value": "valid", "notes": []},
                {"id": "task_002", "status": "pass", "value": "valid", "notes": []},
            ],
        }

        failed_tasks = manager._extract_failed_tasks(validation_summary)

        assert len(failed_tasks) == 0

    def test_extract_with_empty_by_task(self, mock_deps):
        """Test extraction with empty by_task list."""
        manager = ProgressiveWriteManager(
            project_root="/tmp/test_project",
            episode_number=1,
            deps=mock_deps,
        )

        validation_summary = {"success": True, "by_task": []}

        failed_tasks = manager._extract_failed_tasks(validation_summary)

        assert len(failed_tasks) == 0


class TestComposeDeltaPrompt:
    """Test _compose_delta_prompt() method."""

    def test_compose_basic_delta_prompt(self, mock_deps):
        """Test basic delta prompt composition with one failed task."""
        manager = ProgressiveWriteManager(
            project_root="/tmp/test_project",
            episode_number=1,
            deps=mock_deps,
        )

        failed_tasks = [
            {
                "id": "task_001",
                "value": None,
                "notes": ["field_missing"],
            }
        ]

        template_data = {
            "control_settings": {
                "by_task": [
                    {
                        "id": "task_001",
                        "field": "output.character_name",
                        "rule": "nonempty",
                    }
                ]
            }
        }

        original_prompt = "Generate character information for episode 1"

        delta_prompt = manager._compose_delta_prompt(
            failed_tasks=failed_tasks,
            template_data=template_data,
            original_prompt=original_prompt,
            retry_count=1,
        )

        # Verify structure
        assert "## 前回実行の検証結果" in delta_prompt
        assert "### タスク: task_001" in delta_prompt
        assert "フィールド: `output.character_name`" in delta_prompt
        assert "ルール: `nonempty`" in delta_prompt
        assert "## 修正指示" in delta_prompt
        assert "## 再実行用プロンプト" in delta_prompt
        assert original_prompt in delta_prompt
        assert "これは 1/3 回目のリトライです" in delta_prompt


    def test_compose_with_no_failed_tasks(self, mock_deps):
        """Test that original prompt is returned when no tasks failed."""
        manager = ProgressiveWriteManager(
            project_root="/tmp/test_project",
            episode_number=1,
            deps=mock_deps,
        )

        original_prompt = "Original prompt text"

        delta_prompt = manager._compose_delta_prompt(
            failed_tasks=[],
            template_data=None,
            original_prompt=original_prompt,
            retry_count=1,
        )

        assert delta_prompt == original_prompt


class TestRetryWithDeltaPromptIntegration:
    """Test _retry_with_delta_prompt() integration with recovery flow."""

    def test_retry_with_delta_prompt_success(self, mock_deps):
        """Test successful retry with delta prompt after by_task validation failure."""
        from unittest.mock import MagicMock

        from noveler.domain.interfaces.progressive_write_llm_executor import (
            LLMExecutionResult,
        )

        # Setup manager
        manager = ProgressiveWriteManager(
            project_root="/tmp/test_project",
            episode_number=1,
            deps=mock_deps,
        )

        # Mock LLM executor for retry
        mock_llm_result = {"content": "Corrected YAML content with required fields"}
        mock_executor = MagicMock()
        mock_executor.run_sync.return_value = mock_llm_result
        manager.llm_executor = mock_executor

        # Mock template loading
        manager._load_prompt_template = MagicMock(
            return_value={
                "prompt": {"main_instruction": "Generate character info"},
                "control_settings": {
                    "by_task": [
                        {
                            "id": "task_001",
                            "field": "output.character_name",
                            "rule": "nonempty",
                        }
                    ]
                },
            }
        )

        # Setup task
        task = {"id": 1, "name": "Character Design"}

        # Setup execution result with validation failure
        execution_result = {
            "step_id": 1,
            "step_name": "Character Design",
            "content": "Invalid YAML",
            "validation": {
                "by_task": [
                    {
                        "id": "task_001",
                        "status": "fail",
                        "value": None,
                        "notes": ["field_missing"],
                    }
                ]
            },
            "artifacts": ["artifact_123"],
            "request_payload": {"prompt_text": "Generate character info"},
        }

        # Execute retry
        retry_result = manager._retry_with_delta_prompt(task, execution_result, retry_count=0)

        # Verify retry was executed
        assert retry_result is not None
        assert retry_result["content"] == "Corrected YAML content with required fields"
        assert retry_result["metadata"]["retry_count"] == 1
        assert retry_result["metadata"]["recovery_applied"] is True
        assert retry_result["metadata"]["recovery_strategy"] == "retry_with_delta_prompt"

        # Verify LLM was called with delta prompt
        mock_executor.run_sync.assert_called_once()
        call_args = mock_executor.run_sync.call_args[0][0]
        assert "前回実行の検証結果" in call_args.prompt_text
        assert "task_001" in call_args.prompt_text

    def test_retry_exceeds_max_retries(self, mock_deps):
        """Test that retry is not attempted when retry_count >= MAX_RETRIES."""
        manager = ProgressiveWriteManager(
            project_root="/tmp/test_project",
            episode_number=1,
            deps=mock_deps,
        )

        task = {"id": 1, "name": "Character Design"}
        execution_result = {
            "validation": {
                "by_task": [
                    {
                        "id": "task_001",
                        "status": "fail",
                        "value": None,
                        "notes": ["field_missing"],
                    }
                ]
            },
        }

        # _attempt_step_recovery should not add retry strategy when retry_count >= MAX_RETRIES
        recovery_result = manager._attempt_step_recovery(task, execution_result, retry_count=3)

        # No retry should be attempted (no strategies added)
        assert recovery_result is None


@pytest.fixture
def mock_deps(tmp_path):
    """Create mock dependencies for ProgressiveWriteManager."""
    from unittest.mock import MagicMock

    from noveler.domain.interfaces.logger import ILogger

    deps = MagicMock()
    deps.create_path_service.return_value = None
    deps.create_artifact_store.return_value = MagicMock()
    deps.get_configuration_manager.return_value = None
    deps.ensure_llm_executor.return_value = None

    # Mock logger
    logger = MagicMock(spec=ILogger)
    deps.create_logger.return_value = logger

    return deps
