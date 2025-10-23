# File: tests/unit/domain/services/test_manuscript_fetch_service.py
# Purpose: Verify manuscript fetch fallback workflow and QC codes.
# Context: Implements SPEC-QUALITY-120 manuscript fetch requirements.

from __future__ import annotations

import hashlib
from typing import Any

import pytest

from noveler.domain.services.manuscript_fetch_service import (
    ManuscriptFetchAttemptLog,
    ManuscriptFetchError,
    ManuscriptFetchResult,
    ManuscriptFetchService,
    ManuscriptToolError,
    ManuscriptToolResponse,
)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class DummyTool:
    def __init__(self, *, response: ManuscriptToolResponse | None = None, error: ManuscriptToolError | None = None):
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def __call__(self, *, manuscript_hash: str) -> ManuscriptToolResponse:
        self.calls.append({"manuscript_hash": manuscript_hash})
        if self.error is not None:
            raise self.error
        if self.response is None:
            raise ManuscriptToolError("no response", code="QC-016")
        return self.response


def test_fetch_artifact_success_first_try():
    content = "本文データ"
    tool = DummyTool(response=ManuscriptToolResponse(content=content, manuscript_hash=sha(content)))
    service = ManuscriptFetchService(
        fetch_artifact=tool,
        read_snapshot=DummyTool(error=ManuscriptToolError("unused", code="QC-015")),
        request_manual_upload=DummyTool(error=ManuscriptToolError("unused", code="QC-017")),
        sleep=lambda _: None,
    )

    result = service.fetch_excerpt(manuscript_hash=sha(content))

    assert isinstance(result, ManuscriptFetchResult)
    assert result.excerpt == content
    assert result.tool_id == "fetch_artifact"
    assert result.metadata["excerpt_hash"] == sha(content)
    assert result.attempts[0].result == "success"
    assert result.attempts[0].tool_id == "fetch_artifact"


def test_fallback_to_read_snapshot_on_cache_miss():
    cache_miss_tool = DummyTool(error=ManuscriptToolError("cache miss", code="QC-015"))
    content = "最新本文"
    snapshot_tool = DummyTool(response=ManuscriptToolResponse(content=content, manuscript_hash=sha(content)))
    manual_tool = DummyTool(error=ManuscriptToolError("pending", code="QC-017"))
    delays: list[float] = []

    service = ManuscriptFetchService(
        fetch_artifact=cache_miss_tool,
        read_snapshot=snapshot_tool,
        request_manual_upload=manual_tool,
        sleep=lambda sec: delays.append(sec),
    )

    result = service.fetch_excerpt(manuscript_hash=sha(content))

    assert result.tool_id == "read_snapshot"
    assert len(delays) == 1 and delays[0] == 1.0
    assert result.attempts[0].qc_code == "QC-015"
    assert result.attempts[1].result == "success"


def test_hash_mismatch_then_manual_upload_failure():
    wrong_content = "古い本文"
    hash_mismatch_tool = DummyTool(response=ManuscriptToolResponse(content=wrong_content, manuscript_hash=sha("別")))
    storage_fail_tool = DummyTool(error=ManuscriptToolError("storage", code="QC-016"))
    pending_tool = DummyTool(error=ManuscriptToolError("pending", code="QC-017"))

    service = ManuscriptFetchService(
        fetch_artifact=hash_mismatch_tool,
        read_snapshot=storage_fail_tool,
        request_manual_upload=pending_tool,
        sleep=lambda _: None,
    )

    with pytest.raises(ManuscriptFetchError) as exc_info:
        service.fetch_excerpt(manuscript_hash=sha("期待"))

    err = exc_info.value
    assert err.code == "QC-017"
    qc_codes = [attempt.get("qc_code") for attempt in err.attempts]
    assert qc_codes == ["QC-018", "QC-016", "QC-017"]


def test_preferred_tools_reorders_priorities():
    first = DummyTool(response=ManuscriptToolResponse(content="A", manuscript_hash=sha("A")))
    second = DummyTool(response=ManuscriptToolResponse(content="B", manuscript_hash=sha("B")))
    third = DummyTool(response=ManuscriptToolResponse(content="C", manuscript_hash=sha("C")))

    service = ManuscriptFetchService(fetch_artifact=first, read_snapshot=second, request_manual_upload=third, sleep=lambda _: None)

    result = service.fetch_excerpt(manuscript_hash=sha("B"), preferred_tools=["read_snapshot"])

    assert result.tool_id == "read_snapshot"
    assert first.calls == []
