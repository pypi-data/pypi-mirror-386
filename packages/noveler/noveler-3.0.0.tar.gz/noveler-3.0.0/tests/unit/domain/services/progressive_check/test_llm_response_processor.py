# File: tests/unit/domain/services/progressive_check/test_llm_response_processor.py
# Purpose: Unit tests for LLMResponseProcessor
# Context: Phase 6 Step 3 - LLM response processing extraction

"""Unit tests for LLMResponseProcessor."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import Mock

import pytest

from noveler.domain.interfaces.logger_interface import NullLogger
from noveler.domain.services.progressive_check.llm_response_processor import LLMResponseProcessor
from noveler.domain.value_objects.universal_prompt_execution import UniversalPromptResponse, PromptType


@pytest.fixture
def processor() -> LLMResponseProcessor:
    """Create LLMResponseProcessor instance for testing."""
    return LLMResponseProcessor(logger=NullLogger())


@pytest.fixture
def sample_task() -> dict[str, Any]:
    """Create sample task definition."""
    return {
        "id": 1,
        "name": "Test Step",
        "phase": "validation",
    }


@pytest.fixture
def sample_payload() -> dict[str, Any]:
    """Create sample request payload."""
    return {
        "prompt": "テストプロンプト" * 300,  # Long prompt for truncation test (8 chars * 300 = 2400 > 2000)
        "template_source": {"name": "check_step01"},
        "context_files": [],
        "sanitized_input": {"test": "data"},
    }


class TestLLMResponseProcessorInitialization:
    """Tests for LLMResponseProcessor initialization."""

    def test_init_uses_provided_logger(self) -> None:
        """Test that provided logger is used."""
        mock_logger = Mock()
        processor = LLMResponseProcessor(logger=mock_logger)

        assert processor.logger == mock_logger

    def test_init_uses_null_logger_if_none(self) -> None:
        """Test that NullLogger is used if no logger provided."""
        processor = LLMResponseProcessor()

        assert isinstance(processor.logger, NullLogger)


class TestProcessLLMResponse:
    """Tests for process_llm_response method."""

    def test_process_response_with_extracted_data(
        self,
        processor: LLMResponseProcessor,
        sample_task: dict[str, Any],
        sample_payload: dict[str, Any],
    ) -> None:
        """Test processing response with extracted_data."""
        response = UniversalPromptResponse(
            success=True,
            response_content="Response text",
            extracted_data={
                "summary": {"overview": "テスト完了", "score": 85.5},
                "metrics": {"score": 85.5, "issue_count": 3},
                "issues": {"critical": [{"id": "ISS-1"}]},
                "recommendations": ["改善案1", "改善案2"],
            },
            prompt_type=PromptType.QUALITY_CHECK,
            execution_time_ms=1500,
            error_message=None,
        )

        result = processor.process_llm_response(sample_task, sample_payload, response)

        assert result["step_id"] == 1
        assert result["step_name"] == "Test Step"
        assert result["content"] == "テスト完了"
        assert result["overall_score"] == 85.5
        assert result["issues_found"] == 3
        assert result["improvement_suggestions"] == ["改善案1", "改善案2"]
        assert result["metadata"]["llm_used"] is True
        assert result["metadata"]["execution_time_ms"] == 1500

    def test_process_response_with_json_content(
        self,
        processor: LLMResponseProcessor,
        sample_task: dict[str, Any],
        sample_payload: dict[str, Any],
    ) -> None:
        """Test processing response with JSON in response_content."""
        json_content = json.dumps({
            "summary": {"overview": "JSON解析テスト"},
            "metrics": {"score": 90.0},
        })

        response = UniversalPromptResponse(
            success=True,
            response_content=json_content,
            extracted_data={},
            prompt_type=PromptType.QUALITY_CHECK,
            execution_time_ms=1000,
            error_message=None,
        )

        result = processor.process_llm_response(sample_task, sample_payload, response)

        assert result["content"] == "JSON解析テスト"
        assert result["overall_score"] == 90.0

    def test_process_response_fallback_to_raw_content(
        self,
        processor: LLMResponseProcessor,
        sample_task: dict[str, Any],
        sample_payload: dict[str, Any],
    ) -> None:
        """Test processing response falls back to raw content when no structured data."""
        response = UniversalPromptResponse(
            success=True,
            response_content="Plain text response",
            extracted_data={},
            prompt_type=PromptType.QUALITY_CHECK,
            execution_time_ms=500,
            error_message=None,
        )

        result = processor.process_llm_response(sample_task, sample_payload, response)

        assert result["content"] == "Plain text response"
        assert result["overall_score"] is None

    def test_process_response_handles_error_message(
        self,
        processor: LLMResponseProcessor,
        sample_task: dict[str, Any],
        sample_payload: dict[str, Any],
    ) -> None:
        """Test processing response with error message."""
        response = UniversalPromptResponse(
            success=False,
            response_content="Error occurred",
            extracted_data={},
            prompt_type=PromptType.QUALITY_CHECK,
            execution_time_ms=100,
            error_message="LLM API error",
        )

        result = processor.process_llm_response(sample_task, sample_payload, response)

        assert result["metadata"]["llm_error"] == "LLM API error"

    def test_process_response_truncates_prompt_preview(
        self,
        processor: LLMResponseProcessor,
        sample_task: dict[str, Any],
        sample_payload: dict[str, Any],
    ) -> None:
        """Test that prompt preview is truncated to 2000 chars."""
        response = UniversalPromptResponse(
            success=True,
            response_content="Test",
            extracted_data={},
            prompt_type=PromptType.QUALITY_CHECK,
            execution_time_ms=100,
            error_message=None,
        )

        result = processor.process_llm_response(sample_task, sample_payload, response)

        assert len(result["metadata"]["prompt_preview"]) == 2000

    def test_process_response_counts_issues_from_dict(
        self,
        processor: LLMResponseProcessor,
        sample_task: dict[str, Any],
        sample_payload: dict[str, Any],
    ) -> None:
        """Test issue counting from issues dictionary."""
        response = UniversalPromptResponse(
            success=True,
            response_content="Test",
            extracted_data={
                "issues": {
                    "critical": [{"id": "1"}, {"id": "2"}],
                    "warning": [{"id": "3"}],
                },
            },
            prompt_type=PromptType.QUALITY_CHECK,
            execution_time_ms=100,
            error_message=None,
        )

        result = processor.process_llm_response(sample_task, sample_payload, response)

        assert result["issues_found"] == 3


class TestExtractIssueIds:
    """Tests for extract_issue_ids method."""

    def test_extract_issue_ids_from_issues_list(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test extracting issue IDs from issues list."""
        final_result = {
            "issues": [
                {"issue_id": "ISS-1", "description": "Issue 1"},
                {"id": "ISS-2", "description": "Issue 2"},
            ],
        }

        issue_ids = processor.extract_issue_ids(final_result)

        assert issue_ids == ["ISS-1", "ISS-2"]

    def test_extract_issue_ids_from_metadata(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test extracting issue IDs from metadata."""
        final_result = {
            "metadata": {
                "issues": [
                    {"issue_id": "META-1"},
                    {"id": "META-2"},
                ],
            },
        }

        issue_ids = processor.extract_issue_ids(final_result)

        assert issue_ids == ["META-1", "META-2"]

    def test_extract_issue_ids_handles_string_issues(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test extracting issue IDs when issues are strings."""
        final_result = {
            "issues": ["ISS-1", "ISS-2", None],
        }

        issue_ids = processor.extract_issue_ids(final_result)

        assert issue_ids == ["ISS-1", "ISS-2"]

    def test_extract_issue_ids_returns_none_when_no_issues(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test that None is returned when no issues found."""
        final_result = {"metadata": {}}

        issue_ids = processor.extract_issue_ids(final_result)

        assert issue_ids is None


class TestExtractAvailableTools:
    """Tests for extract_available_tools method."""

    def test_extract_tools_from_metadata(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test extracting tools from metadata."""
        final_result = {
            "metadata": {
                "available_tools": ["tool1", "tool2", "tool3"],
            },
        }

        tools = processor.extract_available_tools(final_result)

        assert tools == ["tool1", "tool2", "tool3"]

    def test_extract_tools_from_top_level(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test extracting tools from top-level result."""
        final_result = {
            "available_tools": ["tool_a", "tool_b"],
        }

        tools = processor.extract_available_tools(final_result)

        assert tools == ["tool_a", "tool_b"]

    def test_extract_tools_returns_none_when_empty(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test that None is returned for empty tools list."""
        final_result = {
            "metadata": {
                "available_tools": [],
            },
        }

        tools = processor.extract_available_tools(final_result)

        assert tools is None

    def test_extract_tools_returns_none_when_not_list(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test that None is returned when tools is not a list."""
        final_result = {
            "metadata": {
                "available_tools": "not a list",
            },
        }

        tools = processor.extract_available_tools(final_result)

        assert tools is None


class TestExtractToolSelectionStatus:
    """Tests for extract_tool_selection_status method."""

    def test_extract_tool_selection_from_metadata(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test extracting tool selection status from metadata."""
        final_result = {
            "metadata": {
                "tool_selection_status": {"selected": "tool1", "reason": "best fit"},
            },
        }

        status = processor.extract_tool_selection_status(final_result)

        assert status == {"selected": "tool1", "reason": "best fit"}

    def test_extract_tool_selection_from_top_level(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test extracting tool selection status from top-level."""
        final_result = {
            "tool_selection_status": {"selected": "tool2"},
        }

        status = processor.extract_tool_selection_status(final_result)

        assert status == {"selected": "tool2"}

    def test_extract_tool_selection_returns_none_when_empty(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test that None is returned for empty status dict."""
        final_result = {
            "metadata": {
                "tool_selection_status": {},
            },
        }

        status = processor.extract_tool_selection_status(final_result)

        assert status is None


class TestExtractManuscriptHashRefs:
    """Tests for extract_manuscript_hash_refs method."""

    def test_extract_refs_from_metadata(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test extracting manuscript refs from metadata."""
        final_result = {
            "metadata": {
                "manuscript_hash_refs": [
                    {"hash": "abc123", "line": 10},
                    {"hash": "def456", "line": 20},
                ],
            },
        }

        refs = processor.extract_manuscript_hash_refs(final_result, {})

        assert refs == [{"hash": "abc123", "line": 10}, {"hash": "def456", "line": 20}]

    def test_extract_refs_from_sanitized_input(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test extracting manuscript refs from sanitized_input."""
        final_result = {"metadata": {}}
        sanitized_input = {
            "manuscript_hash_refs": [
                {"hash": "input123", "line": 5},
            ],
        }

        refs = processor.extract_manuscript_hash_refs(final_result, sanitized_input)

        assert refs == [{"hash": "input123", "line": 5}]

    def test_extract_refs_filters_non_dict_entries(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test that non-dict entries are filtered out."""
        final_result = {
            "metadata": {
                "manuscript_hash_refs": [
                    {"hash": "valid", "line": 1},
                    "invalid",
                    None,
                    123,
                ],
            },
        }

        refs = processor.extract_manuscript_hash_refs(final_result, {})

        assert refs == [{"hash": "valid", "line": 1}]

    def test_extract_refs_returns_none_when_empty(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test that None is returned when no refs found."""
        final_result = {"metadata": {}}

        refs = processor.extract_manuscript_hash_refs(final_result, {})

        assert refs is None


class TestExtractFallbackReason:
    """Tests for extract_fallback_reason method."""

    def test_extract_fallback_reason(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test extracting fallback reason from metadata."""
        final_result = {
            "metadata": {
                "fallback_reason": "Template not found",
            },
        }

        reason = processor.extract_fallback_reason(final_result)

        assert reason == "Template not found"

    def test_extract_fallback_reason_returns_none_when_missing(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test that None is returned when fallback_reason is missing."""
        final_result = {"metadata": {}}

        reason = processor.extract_fallback_reason(final_result)

        assert reason is None


class TestHashForStateLog:
    """Tests for hash_for_state_log method."""

    def test_hash_none_returns_empty_string(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test that None returns empty string."""
        result = processor.hash_for_state_log(None)

        assert result == ""

    def test_hash_string_value(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test hashing string value."""
        result = processor.hash_for_state_log("test string")

        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hex length

    def test_hash_dict_value(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test hashing dictionary value."""
        data = {"key": "value", "number": 123}

        result = processor.hash_for_state_log(data)

        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_dict_order_independence(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test that dict key order doesn't affect hash."""
        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}

        hash1 = processor.hash_for_state_log(data1)
        hash2 = processor.hash_for_state_log(data2)

        assert hash1 == hash2

    def test_hash_handles_non_serializable_objects(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test hashing non-JSON-serializable objects."""
        class CustomObject:
            def __str__(self) -> str:
                return "custom_object"

        obj = CustomObject()

        result = processor.hash_for_state_log(obj)

        assert isinstance(result, str)
        assert len(result) == 64


class TestSafeJsonLoads:
    """Tests for _safe_json_loads helper method."""

    def test_safe_json_loads_valid_json(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test parsing valid JSON."""
        json_str = '{"key": "value", "number": 123}'

        result = processor._safe_json_loads(json_str)

        assert result == {"key": "value", "number": 123}

    def test_safe_json_loads_json_in_markdown(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test parsing JSON from markdown code block."""
        content = '''Some text before
```json
{"data": "extracted"}
```
Some text after'''

        result = processor._safe_json_loads(content)

        assert result == {"data": "extracted"}

    def test_safe_json_loads_invalid_json_returns_none(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test that invalid JSON returns None."""
        invalid_json = "not valid json"

        result = processor._safe_json_loads(invalid_json)

        assert result is None

    def test_safe_json_loads_handles_malformed_markdown(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test handling of malformed markdown code block."""
        content = "```json\n{incomplete json"  # No closing backticks

        result = processor._safe_json_loads(content)

        assert result is None


class TestSafeDict:
    """Tests for _safe_dict helper method."""

    def test_safe_dict_returns_dict_unchanged(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test that dict is returned unchanged."""
        data = {"key": "value"}

        result = processor._safe_dict(data)

        assert result == data
        assert result is data  # Same object

    def test_safe_dict_returns_empty_for_non_dict(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test that empty dict is returned for non-dict input."""
        assert processor._safe_dict("string") == {}
        assert processor._safe_dict(123) == {}
        assert processor._safe_dict(None) == {}
        assert processor._safe_dict([1, 2, 3]) == {}


class TestProcessorEdgeCases:
    """Tests for edge cases in LLMResponseProcessor."""

    def test_process_response_with_nested_summary(
        self,
        processor: LLMResponseProcessor,
        sample_task: dict[str, Any],
        sample_payload: dict[str, Any],
    ) -> None:
        """Test processing response with nested summary structure."""
        response = UniversalPromptResponse(
            success=True,
            response_content="Test",
            extracted_data={
                "summary": {
                    "overview": "Nested overview",
                    "details": "Additional details",
                },
            },
            prompt_type=PromptType.QUALITY_CHECK,
            execution_time_ms=100,
            error_message=None,
        )

        result = processor.process_llm_response(sample_task, sample_payload, response)

        assert result["content"] == "Nested overview"

    def test_process_response_with_score_variations(
        self,
        processor: LLMResponseProcessor,
        sample_task: dict[str, Any],
        sample_payload: dict[str, Any],
    ) -> None:
        """Test processing response with various score formats."""
        test_cases = [
            ({"metrics": {"score": 75}}, 75),
            ({"metrics": {"score": 75.5}}, 75.5),
            ({"summary": {"score": 80}}, 80),
            ({"metrics": {"score": "90"}}, 90.0),  # String score conversion
        ]

        for extracted_data, expected_score in test_cases:
            response = UniversalPromptResponse(
                success=True,
                response_content="Test",
                extracted_data=extracted_data,
                prompt_type=PromptType.QUALITY_CHECK,
                execution_time_ms=100,
                error_message=None,
            )

            result = processor.process_llm_response(sample_task, sample_payload, response)
            assert result["overall_score"] == expected_score

    def test_process_response_with_recommendations_variations(
        self,
        processor: LLMResponseProcessor,
        sample_task: dict[str, Any],
        sample_payload: dict[str, Any],
    ) -> None:
        """Test processing response with various recommendation formats."""
        response = UniversalPromptResponse(
            success=True,
            response_content="Test",
            extracted_data={
                "recommendations": ["Rec 1", "Rec 2"],
            },
            prompt_type=PromptType.QUALITY_CHECK,
            execution_time_ms=100,
            error_message=None,
        )

        result = processor.process_llm_response(sample_task, sample_payload, response)

        assert result["improvement_suggestions"] == ["Rec 1", "Rec 2"]

    def test_process_response_counts_issues_from_list(
        self,
        processor: LLMResponseProcessor,
        sample_task: dict[str, Any],
        sample_payload: dict[str, Any],
    ) -> None:
        """Test issue counting from metrics.issue_count when available."""
        response = UniversalPromptResponse(
            success=True,
            response_content="Test",
            extracted_data={
                "metrics": {"issue_count": 2},
                "issues": [
                    {"id": "1", "description": "Issue 1"},
                    {"id": "2", "description": "Issue 2"},
                ],
            },
            prompt_type=PromptType.QUALITY_CHECK,
            execution_time_ms=100,
            error_message=None,
        )

        result = processor.process_llm_response(sample_task, sample_payload, response)

        assert result["issues_found"] == 2

    def test_extract_issue_ids_handles_mixed_formats(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test extracting issue IDs with mixed key formats."""
        final_result = {
            "issues": [
                {"issue_id": "ISS-1"},  # issue_id key
                {"id": "ISS-2"},  # id key
                "ISS-3",  # String format
            ],
        }

        issue_ids = processor.extract_issue_ids(final_result)

        assert "ISS-1" in issue_ids
        assert "ISS-2" in issue_ids
        assert "ISS-3" in issue_ids

    def test_hash_for_state_log_with_complex_objects(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test hashing complex nested objects."""
        complex_obj = {
            "nested": {
                "list": [1, 2, {"inner": "value"}],
                "dict": {"a": 1, "b": 2},
            },
        }

        hash_result = processor.hash_for_state_log(complex_obj)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 64

        # Verify consistency
        hash_result2 = processor.hash_for_state_log(complex_obj)
        assert hash_result == hash_result2

    def test_safe_json_loads_handles_nested_code_blocks(
        self,
        processor: LLMResponseProcessor,
    ) -> None:
        """Test parsing JSON from nested markdown structures."""
        content = '''
        Some explanation text

        ```json
        {
            "data": "first block"
        }
        ```

        More text
        '''

        result = processor._safe_json_loads(content)

        assert result == {"data": "first block"}

    def test_process_response_metadata_completeness(
        self,
        processor: LLMResponseProcessor,
        sample_task: dict[str, Any],
        sample_payload: dict[str, Any],
    ) -> None:
        """Test that all expected metadata fields are populated."""
        response = UniversalPromptResponse(
            success=True,
            response_content="Test response",
            extracted_data={"summary": {"overview": "Complete"}},
            prompt_type=PromptType.QUALITY_CHECK,
            execution_time_ms=1234,
            error_message=None,
        )

        result = processor.process_llm_response(sample_task, sample_payload, response)

        # Verify all expected metadata fields
        assert "metadata" in result
        metadata = result["metadata"]
        assert "llm_used" in metadata
        assert "execution_time_ms" in metadata
        assert "prompt_preview" in metadata
        assert "template_source" in metadata
        assert metadata["llm_used"] is True
        assert metadata["execution_time_ms"] == 1234
