"""Factory for building ProgressiveWriteLLMExecutor implementations."""

from __future__ import annotations

import asyncio
from typing import Any

from noveler.application.use_cases.universal_llm_use_case import UniversalLLMUseCase
from noveler.domain.interfaces.progressive_write_llm_executor import (
    LLMExecutionRequest,
    LLMExecutionResult,
    ProgressiveWriteLLMExecutor,
)
from noveler.domain.value_objects.universal_prompt_execution import (
    ProjectContext,
    PromptType,
    UniversalPromptRequest,
)
from noveler.infrastructure.integrations.universal_claude_code_service import (
    UniversalClaudeCodeService,
)


class UniversalProgressiveWriteLLMExecutor(ProgressiveWriteLLMExecutor):
    """Universal Claude Code backed implementation of the LLM facade."""

    def __init__(self, use_case: UniversalLLMUseCase) -> None:
        self._use_case = use_case

    def _build_prompt_request(self, request: LLMExecutionRequest) -> UniversalPromptRequest:
        context = ProjectContext(
            project_root=request.project_root,
            project_name=request.project_root.name,
        )
        return UniversalPromptRequest(
            prompt_type=PromptType.WRITING,
            prompt_content=request.prompt_text,
            project_context=context,
            output_format="json",
            max_turns=1,
            type_specific_config={
                "episode_number": request.episode_number,
                "step_id": request.step_id,
                "input_data": dict(request.input_data),
                "artifacts": list(request.artifact_ids),
            },
        )

    def _convert_response(self, response: Any) -> LLMExecutionResult:
        return LLMExecutionResult(
            success=getattr(response, "success", False),
            response_content=getattr(response, "response_content", ""),
            extracted_data=dict(getattr(response, "extracted_data", {}) or {}),
            metadata=dict(getattr(response, "metadata", {}) or {}),
            error_message=getattr(response, "error_message", None),
        )

    async def run(self, request: LLMExecutionRequest) -> LLMExecutionResult:
        prompt_request = self._build_prompt_request(request)
        response = await self._use_case.execute_with_fallback(prompt_request, True)
        return self._convert_response(response)

    def run_sync(self, request: LLMExecutionRequest) -> LLMExecutionResult:
        prompt_request = self._build_prompt_request(request)
        execute = self._use_case.execute_with_fallback

        if hasattr(execute, "__wrapped__"):
            response = execute.__wrapped__(self._use_case, prompt_request, True)
            return self._convert_response(response)

        return asyncio.run(self.run(request))


def create_progressive_write_llm_executor() -> ProgressiveWriteLLMExecutor | None:
    """Build the default facade implementation or return None if unavailable."""

    try:
        service = UniversalClaudeCodeService()
    except Exception:
        return None

    try:
        use_case = UniversalLLMUseCase(service)
    except Exception:
        return None

    return UniversalProgressiveWriteLLMExecutor(use_case)
