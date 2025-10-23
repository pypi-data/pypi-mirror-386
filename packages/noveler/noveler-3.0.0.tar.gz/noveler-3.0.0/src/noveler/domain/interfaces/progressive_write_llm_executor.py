"""Interface definition for ProgressiveWriteManager LLM executor facade."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol


@dataclass
class LLMExecutionRequest:
    """Input payload for invoking an LLM step during progressive writing."""

    episode_number: int
    step_id: int | float
    step_name: str
    prompt_text: str
    input_data: Mapping[str, Any]
    artifact_ids: list[str]
    project_root: Path


@dataclass
class LLMExecutionResult:
    """Normalized result structure returned from an LLM execution."""

    success: bool
    response_content: str
    extracted_data: Mapping[str, Any]
    metadata: Mapping[str, Any]
    error_message: str | None = None


class ProgressiveWriteLLMExecutor(Protocol):
    """Facade contract for executing LLM steps on behalf of ProgressiveWriteManager."""

    async def run(self, request: LLMExecutionRequest) -> LLMExecutionResult:
        """Execute a progressive-writing LLM step and return structured results."""

    def run_sync(self, request: LLMExecutionRequest) -> LLMExecutionResult:
        """Synchronous variant for contexts where event loop control is unavailable."""
