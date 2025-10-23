# File: tests/unit/domain/services/test_workflow_state_store.py
# Purpose: Validate filesystem-backed WorkflowStateStore for LangGraph workflows.
# Context: Covers SPEC-QUALITY-120 requirements for session, step, issue, and fetch logging.

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from noveler.domain.services.workflow_state_store import (
    FilesystemWorkflowStateStore,
    IterationPolicy,
    StepExecutionPayload,
    IssuePayload,
    IssueResolutionPayload,
    ManuscriptFetchLog,
)


@pytest.fixture()
def store(tmp_path: Path) -> FilesystemWorkflowStateStore:
    """Create a WorkflowStateStore rooted at a temporary project."""

    return FilesystemWorkflowStateStore(project_root=tmp_path)


def _session_dir(project_root: Path, session_id: str) -> Path:
    return project_root / ".noveler" / "checks" / session_id / "workflow"


def test_begin_session_creates_manifest_and_lock(store: FilesystemWorkflowStateStore, tmp_path: Path) -> None:
    """begin_session should initialize session metadata and lock state."""

    policy = IterationPolicy(count=2, until_pass=True, time_budget_sec=30, min_improvement=0.15)
    context = store.begin_session(episode_number=7, iteration_policy=policy)

    session_dir = _session_dir(tmp_path, context.session_id)
    manifest = session_dir / "session.json"
    lock_file = session_dir / "session.lock"

    assert manifest.exists()
    assert lock_file.exists()

    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["episode_number"] == 7
    assert data["state_version"] == context.state_version
    assert data["iteration_policy"] == {
        "count": 2,
        "until_pass": True,
        "time_budget_sec": 30,
        "min_improvement": 0.15,
    }
    assert lock_file.read_text(encoding="utf-8").strip() == "held"


def test_commit_persists_step_execution(store: FilesystemWorkflowStateStore, tmp_path: Path) -> None:
    """record_step_execution + commit should append JSONL entry with hashed snapshots."""

    context = store.begin_session(episode_number=1, iteration_policy=IterationPolicy(count=1, until_pass=False))

    started_at = datetime(2025, 9, 26, 10, 0, tzinfo=timezone.utc)
    completed_at = started_at + timedelta(seconds=1.5)
    payload = StepExecutionPayload(
        session_id=context.session_id,
        step_id=3,
        attempt=1,
        started_at=started_at,
        completed_at=completed_at,
        request_prompt_hash="reqhash",
        input_snapshot_hash="inphash",
        output_snapshot_hash="outhash",
        issues_detected=["ISSUE-001"],
        duration_ms=1500.0,
        fallback_reason=None,
        available_tools=["tool_a", "tool_b"],
        tool_selection_status={"selected": "tool_a"},
        manuscript_hash_refs=[{"hash": "abc123", "type": "manuscript"}],
    )

    store.record_step_execution(payload)
    store.commit()

    session_dir = _session_dir(tmp_path, context.session_id)
    step_log = session_dir / "step_executions.jsonl"
    assert step_log.exists()
    lines = [line for line in step_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["step_id"] == 3
    assert entry["attempt"] == 1
    assert entry["request_prompt_hash"] == "reqhash"
    assert entry["manuscript_hash_refs"] == [{"hash": "abc123", "type": "manuscript"}]
    assert entry["duration_ms"] == pytest.approx(1500.0)


def test_commit_updates_manifest_and_audit(store: FilesystemWorkflowStateStore, tmp_path: Path) -> None:
    policy = IterationPolicy(count=1, until_pass=False)
    context = store.begin_session(episode_number=5, iteration_policy=policy)
    payload = StepExecutionPayload(
        session_id=context.session_id,
        step_id=2,
        attempt=1,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        request_prompt_hash="req",
        input_snapshot_hash="inp",
        output_snapshot_hash="out",
        issues_detected=["ISSUE-42"],
        duration_ms=123.0,
        fallback_reason=None,
        available_tools=["tool_a"],
        tool_selection_status={"selected": "tool_a"},
        manuscript_hash_refs=[{"hash": "abc", "type": "manuscript"}],
        metadata={"iteration_policy": {"count": 1}},
    )
    store.record_step_execution(payload)
    fetch = ManuscriptFetchLog(
        fetch_id="fetch-123",
        session_id=context.session_id,
        manuscript_hash="hash-abc",
        tool_id="fetch_artifact",
        result="success",
        latency_ms=50,
        attempt_index=1,
        qc_code=None,
        metadata={"excerpt_hash": "xyz"},
    )
    store.append_fetch_log(fetch)
    store.commit()

    workflow_dir = tmp_path / ".noveler" / "checks" / context.session_id / "workflow"
    manifest_path = workflow_dir / "manifest.json"
    audit_path = workflow_dir / "workflow_audit.jsonl"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["steps"]
    assert manifest["steps"][0]["step_id"] == 2
    assert manifest["manuscript_fetch"][0]["tool_id"] == "fetch_artifact"
    audit_lines = [line for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert audit_lines
    audit_entry = json.loads(audit_lines[-1])
    assert audit_entry["steps_written"] == 1

def test_commit_persists_issue_and_resolution(store: FilesystemWorkflowStateStore, tmp_path: Path) -> None:
    """Issues, resolutions, and fetch logs are persisted on commit."""

    context = store.begin_session(episode_number=2, iteration_policy=IterationPolicy(count=1, until_pass=False))

    issue = IssuePayload(
        issue_id="ISSUE-123",
        session_id=context.session_id,
        step_id=4,
        manuscript_hash="hash-001",
        text_range={"start_char": 10, "end_char": 40},
        range_checksum="chk-xyz",
        category="typo",
        severity="medium",
        state="New",
        adjustment_method="exact_match",
        confidence_score=0.9,
        adjustment_attempts=[{"strategy": "exact_match", "confidence": 0.9}],
        metadata={"note": "sample"},
    )

    resolution = IssueResolutionPayload(
        issue_id="ISSUE-123",
        resolution_attempt=1,
        applied_fix_description="Fixed typo",
        tool_used="rewrite_tool",
        diff_ref="diff-abc",
        verification_status="passed",
        recurrence_score=0.1,
        metadata={"reviewer": "qa"},
    )

    fetch = ManuscriptFetchLog(
        fetch_id="fetch-1",
        session_id=context.session_id,
        manuscript_hash="hash-001",
        tool_id="fetch_artifact",
        result="success",
        latency_ms=120,
        attempt_index=0,
        qc_code="QC-015",
        metadata={"excerpt_hash": "ehash"},
    )

    store.record_issue(issue)
    store.record_issue_resolution(resolution)
    store.append_fetch_log(fetch)
    store.commit()

    session_dir = _session_dir(tmp_path, context.session_id)

    issues_log = session_dir / "issues.jsonl"
    resolutions_log = session_dir / "issue_resolutions.jsonl"
    fetch_log = session_dir / "manuscript_fetch.jsonl"

    assert json.loads(issues_log.read_text(encoding="utf-8").splitlines()[0])["issue_id"] == "ISSUE-123"
    assert json.loads(resolutions_log.read_text(encoding="utf-8").splitlines()[0])["verification_status"] == "passed"
    assert json.loads(fetch_log.read_text(encoding="utf-8").splitlines()[0])["tool_id"] == "fetch_artifact"


def test_rollback_discards_pending_changes(store: FilesystemWorkflowStateStore, tmp_path: Path) -> None:
    """rollback should clear buffered records and avoid filesystem writes."""

    context = store.begin_session(episode_number=3, iteration_policy=IterationPolicy(count=1, until_pass=False))
    payload = StepExecutionPayload(
        session_id=context.session_id,
        step_id=1,
        attempt=1,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        request_prompt_hash="req",
        input_snapshot_hash="inp",
        output_snapshot_hash="out",
        issues_detected=None,
        duration_ms=10.0,
        fallback_reason=None,
        available_tools=None,
        tool_selection_status=None,
        manuscript_hash_refs=None,
    )

    store.record_step_execution(payload)
    store.rollback()

    session_dir = _session_dir(tmp_path, context.session_id)
    assert not (session_dir / "step_executions.jsonl").exists()
