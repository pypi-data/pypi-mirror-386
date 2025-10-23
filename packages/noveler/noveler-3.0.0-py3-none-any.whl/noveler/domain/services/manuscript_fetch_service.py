# File: src/noveler/domain/services/manuscript_fetch_service.py
# Purpose: Retrieve manuscript excerpts using prioritized tooling with QC-aware fallbacks.
# Context: LangGraph workflow support. Encapsulates fetch_artifact→read_snapshot→request_manual_upload flow.

"""Manuscript fetch coordination for LangGraph-driven quality workflows.

Implements SPEC-QUALITY-120 section 3.4 behaviour:
- Prioritized tools: fetch_artifact → read_snapshot → request_manual_upload
- QC code mapping for failure scenarios (QC-015〜QC-018)
- Exponential backoff retries (1s→2s→4s) without blocking tests via injectable sleep.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Iterable, List, Protocol


__all__ = [
    "ManuscriptFetchError",
    "ManuscriptToolError",
    "ManuscriptToolResponse",
    "ManuscriptFetchAttemptLog",
    "ManuscriptFetchResult",
    "ManuscriptFetchService",
]


class ManuscriptFetchError(RuntimeError):
    """Base error for unrecoverable manuscript fetch failures."""

    def __init__(self, message: str, *, code: str, attempts: List[dict[str, Any]]) -> None:
        super().__init__(message)
        self.code = code
        self.attempts = attempts


class ManuscriptToolError(RuntimeError):
    """Raised by individual tool call when a QC-classified failure occurs."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(slots=True)
class ManuscriptToolResponse:
    """Payload returned by successful tool invocation."""

    content: str
    source_key: str | None = None
    manuscript_hash: str | None = None


@dataclass(slots=True)
class ManuscriptFetchAttemptLog:
    """Telemetry for each fetch attempt."""

    tool_id: str
    attempt_index: int
    result: str
    latency_ms: float
    qc_code: str | None = None
    excerpt_hash: str | None = None
    excerpt_length: int | None = None
    source_key: str | None = None
    extra: dict[str, Any] | None = None


@dataclass(slots=True)
class ManuscriptFetchResult:
    """Final result containing excerpt and telemetry."""

    excerpt: str
    tool_id: str
    attempts: List[ManuscriptFetchAttemptLog] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ManuscriptToolCallable(Protocol):
    """Signature for tool functions used by the service."""

    def __call__(self, *, manuscript_hash: str) -> ManuscriptToolResponse: ...


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ManuscriptFetchService:
    """Coordinates manuscript retrieval with fallback strategies and QC codes."""

    def __init__(
        self,
        *,
        fetch_artifact: ManuscriptToolCallable,
        read_snapshot: ManuscriptToolCallable,
        request_manual_upload: ManuscriptToolCallable,
        sleep: Callable[[float], None] | None = None,
        backoff_schedule: Iterable[float] | None = None,
    ) -> None:
        self._tool_priority: List[tuple[str, ManuscriptToolCallable]] = [
            ("fetch_artifact", fetch_artifact),
            ("read_snapshot", read_snapshot),
            ("request_manual_upload", request_manual_upload),
        ]
        self._sleep = sleep or time.sleep
        self._backoff = list(backoff_schedule or (1.0, 2.0, 4.0))

    def fetch_excerpt(
        self,
        *,
        manuscript_hash: str,
        range_start: int | None = None,
        range_end: int | None = None,
        preferred_tools: Iterable[str] | None = None,
    ) -> ManuscriptFetchResult:
        attempts: List[ManuscriptFetchAttemptLog] = []
        tools = self._prepare_tool_order(preferred_tools)
        last_error: ManuscriptToolError | None = None

        for attempt_index, (tool_id, tool_callable) in enumerate(tools, start=1):
            try:
                attempt_log = self._execute_tool(
                    tool_id,
                    tool_callable,
                    manuscript_hash=manuscript_hash,
                    range_start=range_start,
                    range_end=range_end,
                    attempt_index=attempt_index,
                )
                attempts.append(attempt_log)
                if attempt_log.result == "success":
                    self._promote_tool(tool_id)
                    metadata = {
                        "manuscript_hash": manuscript_hash,
                        "tool_id": tool_id,
                        "excerpt_hash": attempt_log.excerpt_hash,
                        "excerpt_length": attempt_log.excerpt_length,
                    }
                    excerpt_text = ""
                    if attempt_log.extra and "excerpt" in attempt_log.extra:
                        excerpt_text = attempt_log.extra["excerpt"]
                    return ManuscriptFetchResult(
                        excerpt=excerpt_text,
                        tool_id=tool_id,
                        attempts=attempts,
                        metadata=metadata,
                    )
                last_error = ManuscriptToolError("Hash mismatch", code=attempt_log.qc_code or "QC-018")
                self._apply_backoff(attempt_index)
                continue
            except ManuscriptToolError as exc:
                attempts.append(
                    ManuscriptFetchAttemptLog(
                        tool_id=tool_id,
                        attempt_index=attempt_index,
                        result="failure",
                        latency_ms=0.0,
                        qc_code=exc.code,
                    )
                )
                last_error = exc
                self._apply_backoff(attempt_index)
                continue
            except Exception as exc:  # pragma: no cover - safeguard
                attempts.append(
                    ManuscriptFetchAttemptLog(
                        tool_id=tool_id,
                        attempt_index=attempt_index,
                        result="failure",
                        latency_ms=0.0,
                        qc_code="QC-016",
                    )
                )
                last_error = ManuscriptToolError(str(exc), code="QC-016")
                self._apply_backoff(attempt_index)
                continue

        code = last_error.code if last_error else "QC-016"
        raise ManuscriptFetchError("Manuscript retrieval failed", code=code, attempts=[asdict(a) for a in attempts])

    def _prepare_tool_order(self, preferred: Iterable[str] | None) -> List[tuple[str, ManuscriptToolCallable]]:
        if not preferred:
            return list(self._tool_priority)
        preferred_list = list(preferred)
        ordered: List[tuple[str, ManuscriptToolCallable]] = []
        seen = set()
        for name in preferred_list:
            for tool_name, tool_callable in self._tool_priority:
                if tool_name == name and tool_name not in seen:
                    ordered.append((tool_name, tool_callable))
                    seen.add(tool_name)
        for tool_name, tool_callable in self._tool_priority:
            if tool_name not in seen:
                ordered.append((tool_name, tool_callable))
        return ordered

    def _execute_tool(
        self,
        tool_id: str,
        tool: ManuscriptToolCallable,
        *,
        manuscript_hash: str,
        range_start: int | None,
        range_end: int | None,
        attempt_index: int,
    ) -> ManuscriptFetchAttemptLog:
        start_time = time.perf_counter()
        response = tool(manuscript_hash=manuscript_hash)
        latency_ms = (time.perf_counter() - start_time) * 1000

        if not isinstance(response, ManuscriptToolResponse):
            raise ManuscriptToolError("Invalid tool response", code="QC-016")

        content = response.content
        computed_hash = _sha256(content)
        expected_hash = response.manuscript_hash or manuscript_hash
        if expected_hash and computed_hash != expected_hash:
            return ManuscriptFetchAttemptLog(
                tool_id=tool_id,
                attempt_index=attempt_index,
                result="failure",
                latency_ms=latency_ms,
                qc_code="QC-018",
            )

        excerpt = self._extract_excerpt(content, range_start, range_end)
        excerpt_hash = _sha256(excerpt)
        return ManuscriptFetchAttemptLog(
            tool_id=tool_id,
            attempt_index=attempt_index,
            result="success",
            latency_ms=latency_ms,
            qc_code=None,
            excerpt_hash=excerpt_hash,
            excerpt_length=len(excerpt),
            source_key=response.source_key,
            extra={"excerpt": excerpt},
        )

    def _extract_excerpt(self, content: str, start: int | None, end: int | None) -> str:
        if start is None and end is None:
            return content
        start_idx = max(0, start or 0)
        end_idx = len(content) if end is None else min(len(content), end)
        if start_idx >= end_idx:
            return ""
        return content[start_idx:end_idx]

    def _apply_backoff(self, attempt_index: int) -> None:
        if attempt_index - 1 < len(self._backoff):
            delay = self._backoff[attempt_index - 1]
            try:
                self._sleep(delay)
            except Exception:  # pragma: no cover
                pass

    def _promote_tool(self, tool_id: str) -> None:
        for idx, (name, callable_) in enumerate(self._tool_priority):
            if name == tool_id:
                self._tool_priority.insert(0, self._tool_priority.pop(idx))
                break
