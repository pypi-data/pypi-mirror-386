# File: src/noveler/domain/services/progressive_check/llm_response_processor.py
# Purpose: LLM response processing for Progressive Check system
# Context: Extracted from ProgressiveCheckManager (Phase 6 Step 3)

"""LLM Response Processor for Progressive Check System.

This module handles all LLM response processing operations including:
- Response parsing and validation
- Structured data extraction
- Metadata extraction (issue IDs, tools, manuscript refs)
- Result generation and formatting
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger
from noveler.domain.value_objects.universal_prompt_execution import UniversalPromptResponse


class LLMResponseProcessor:
    """Processes LLM responses for Progressive Check execution.

    Responsibilities:
    - Parse and validate LLM responses
    - Extract structured data from responses
    - Extract metadata (issue IDs, available tools, manuscript refs)
    - Generate formatted results
    - Handle response errors gracefully

    Args:
        logger: Optional logger instance
    """

    def __init__(
        self,
        logger: ILogger | None = None,
    ) -> None:
        self.logger = logger or NullLogger()

    def process_llm_response(
        self,
        task: dict[str, Any],
        payload: dict[str, Any],
        response: UniversalPromptResponse,
    ) -> dict[str, Any]:
        """Process LLM response and generate result dictionary.

        Args:
            task: Task definition
            payload: Request payload (from LLMRequestBuilder)
            response: LLM response object

        Returns:
            Result dictionary with processed data
        """
        structured_output = response.extracted_data or self._safe_json_loads(response.response_content) or {}
        summary = structured_output.get('summary', {}) if isinstance(structured_output, dict) else {}
        metrics = structured_output.get('metrics', {}) if isinstance(structured_output, dict) else {}
        issues = structured_output.get('issues', {}) if isinstance(structured_output, dict) else {}
        content_summary = summary.get('overview') or response.response_content

        overall_score = metrics.get('score') or summary.get('score')
        try:
            if isinstance(overall_score, str):
                overall_score = float(overall_score)
        except ValueError:
            overall_score = None

        issue_count = metrics.get('issue_count')
        if issue_count is None and isinstance(issues, dict):
            issue_count = sum(len(v) for v in issues.values() if isinstance(v, list))

        metadata = {
            'llm_used': True,
            'template_source': payload.get('template_source'),
            'execution_time_ms': response.execution_time_ms,
            'context_files': [str(path) for path in payload.get('context_files', [])],
            'structured_output': structured_output,
            'prompt_preview': payload.get('prompt', '')[:2000],
            'input_summary': payload.get('sanitized_input'),
        }
        if response.error_message:
            metadata['llm_error'] = response.error_message

        result = {
            'step_id': task.get('id'),
            'step_name': task.get('name'),
            'content': content_summary,
            'metadata': metadata,
            'overall_score': overall_score,
            'quality_breakdown': {
                'summary': summary,
                'metrics': metrics,
            },
            'issues_found': issue_count,
            'improvement_suggestions': structured_output.get('recommendations', []),
            'artifacts': structured_output.get('artifacts', []),
            'raw_response': response.response_content,
        }
        return result

    def extract_issue_ids(self, final_result: dict[str, Any]) -> list[str] | None:
        """Extract issue IDs from result.

        Args:
            final_result: Processed result dictionary

        Returns:
            List of issue ID strings or None if no issues
        """
        metadata = self._safe_dict(final_result.get("metadata"))
        issues = final_result.get("issues") or metadata.get("issues") or final_result.get("issues_found") or metadata.get("issues_found")
        if not isinstance(issues, list):
            return None
        collected: list[str] = []
        for entry in issues:
            if isinstance(entry, dict):
                issue_id = entry.get("issue_id") or entry.get("id")
                if issue_id:
                    collected.append(str(issue_id))
            elif entry is not None:
                collected.append(str(entry))
        return collected or None

    def extract_available_tools(self, final_result: dict[str, Any]) -> list[Any] | None:
        """Extract available tools from result metadata.

        Args:
            final_result: Processed result dictionary

        Returns:
            List of available tools or None
        """
        metadata = self._safe_dict(final_result.get("metadata"))
        tools = metadata.get("available_tools")
        if tools is None:
            tools = final_result.get("available_tools")
        if isinstance(tools, list):
            return list(tools) or None
        return None

    def extract_tool_selection_status(self, final_result: dict[str, Any]) -> dict[str, Any] | None:
        """Extract tool selection status from result metadata.

        Args:
            final_result: Processed result dictionary

        Returns:
            Tool selection status dictionary or None
        """
        metadata = self._safe_dict(final_result.get("metadata"))
        status = metadata.get("tool_selection_status")
        if status is None:
            status = final_result.get("tool_selection_status")
        if isinstance(status, dict):
            return dict(status) or None
        return None

    def extract_manuscript_hash_refs(
        self, final_result: dict[str, Any], sanitized_input: dict[str, Any]
    ) -> list[dict[str, Any]] | None:
        """Extract manuscript hash references from result or input.

        Args:
            final_result: Processed result dictionary
            sanitized_input: Sanitized input data

        Returns:
            List of manuscript hash reference dictionaries or None
        """
        metadata = self._safe_dict(final_result.get("metadata"))
        refs = metadata.get("manuscript_hash_refs")
        if not isinstance(refs, list):
            refs = sanitized_input.get("manuscript_hash_refs") if isinstance(sanitized_input, dict) else None
        if isinstance(refs, list):
            filtered = [ref for ref in refs if isinstance(ref, dict)]
            return filtered or None
        return None

    def extract_fallback_reason(self, final_result: dict[str, Any]) -> str | None:
        """Extract fallback reason from result metadata.

        Args:
            final_result: Processed result dictionary

        Returns:
            Fallback reason string or None
        """
        metadata = self._safe_dict(final_result.get("metadata"))
        reason = metadata.get("fallback_reason")
        return str(reason) if reason else None

    def hash_for_state_log(self, value: Any) -> str:
        """Generate a stable SHA256 hash for stored workflow payloads.

        Args:
            value: Value to hash

        Returns:
            SHA256 hash string
        """
        if value is None:
            return ""
        if isinstance(value, str):
            serialized = value
        else:
            try:
                serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
            except TypeError:
                serialized = str(value)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    # Private helper methods

    def _safe_json_loads(self, content: str) -> dict[str, Any] | None:
        """Safely parse JSON from string, handling markdown code blocks.

        Args:
            content: String content to parse

        Returns:
            Parsed dictionary or None if parsing fails
        """
        try:
            return json.loads(content)
        except (TypeError, ValueError):
            marker = '```json'
            if marker in content:
                try:
                    segment = content.split(marker, 1)[1]
                    segment = segment.split('```', 1)[0]
                    return json.loads(segment)
                except (IndexError, ValueError, TypeError):
                    return None
            return None

    def _safe_dict(self, obj: Any) -> dict[str, Any]:
        """Safely convert object to dictionary.

        Args:
            obj: Object to convert

        Returns:
            Dictionary or empty dict if conversion fails
        """
        return obj if isinstance(obj, dict) else {}
