# File: src/noveler/domain/services/workflow_state_store.py
# Purpose: Persist LangGraph-driven workflow state and telemetry for quality checks.
# Context: Domain-level abstraction reusable across MCP/LangGraph integrations.

"""Workflow state persistence layer for LangGraph quality-check orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol
from uuid import uuid4

__all__ = [
    "IterationPolicy",
    "SessionContext",
    "StepExecutionPayload",
    "IssuePayload",
    "IssueResolutionPayload",
    "ManuscriptFetchLog",
    "WorkflowStateStore",
    "FilesystemWorkflowStateStore",
    "StatePersistenceError",
]


class StatePersistenceError(RuntimeError):
    """Raised when workflow state cannot be persisted safely."""

    def __init__(self, message: str, *, code: str = "state_persistence_error", details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


@dataclass(slots=True)
class IterationPolicy:
    """Normalized iteration policy for LangGraph workflow execution."""

    count: int = 1
    until_pass: bool = False
    time_budget_sec: int | None = None
    min_improvement: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dictionary."""
        return {
            "count": self.count,
            "until_pass": self.until_pass,
            "time_budget_sec": self.time_budget_sec,
            "min_improvement": self.min_improvement,
        }


@dataclass(slots=True)
class SessionContext:
    """Holds metadata for an active workflow session."""

    session_id: str
    episode_number: int
    state_version: int
    session_path: Path
    lock_path: Path


@dataclass(slots=True)
class StepExecutionPayload:
    """Captured data for a single step execution attempt."""

    session_id: str
    step_id: int
    attempt: int
    started_at: datetime
    completed_at: datetime
    request_prompt_hash: str
    input_snapshot_hash: str
    output_snapshot_hash: str
    issues_detected: list[str] | None
    duration_ms: float
    fallback_reason: str | None
    available_tools: list[Any] | None
    tool_selection_status: dict[str, Any] | None
    manuscript_hash_refs: list[dict[str, Any]] | None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict including timestamps."""
        return {
            "session_id": self.session_id,
            "step_id": self.step_id,
            "attempt": self.attempt,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "request_prompt_hash": self.request_prompt_hash,
            "input_snapshot_hash": self.input_snapshot_hash,
            "output_snapshot_hash": self.output_snapshot_hash,
            "issues_detected": self.issues_detected,
            "duration_ms": self.duration_ms,
            "fallback_reason": self.fallback_reason,
            "available_tools": self.available_tools,
            "tool_selection_status": self.tool_selection_status,
            "manuscript_hash_refs": self.manuscript_hash_refs,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class IssuePayload:
    """Persistent representation of an issue detected during checks."""

    issue_id: str
    session_id: str
    step_id: int
    manuscript_hash: str
    text_range: dict[str, Any]
    range_checksum: str | None = None
    category: str | None = None
    severity: str | None = None
    state: str | None = None
    adjustment_method: str | None = None
    confidence_score: float | None = None
    adjustment_attempts: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize issue fields for storage."""
        return {
            "issue_id": self.issue_id,
            "session_id": self.session_id,
            "step_id": self.step_id,
            "manuscript_hash": self.manuscript_hash,
            "text_range": self.text_range,
            "range_checksum": self.range_checksum,
            "category": self.category,
            "severity": self.severity,
            "state": self.state,
            "adjustment_method": self.adjustment_method,
            "confidence_score": self.confidence_score,
            "adjustment_attempts": self.adjustment_attempts,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class IssueResolutionPayload:
    """Represents a resolution attempt applied to an issue."""

    issue_id: str
    resolution_attempt: int
    applied_fix_description: str
    tool_used: str | None = None
    diff_ref: str | None = None
    verification_status: str | None = None
    verification_snapshot_id: str | None = None
    recurrence_score: float | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize resolution data for persistence."""
        return {
            "issue_id": self.issue_id,
            "resolution_attempt": self.resolution_attempt,
            "applied_fix_description": self.applied_fix_description,
            "tool_used": self.tool_used,
            "diff_ref": self.diff_ref,
            "verification_status": self.verification_status,
            "verification_snapshot_id": self.verification_snapshot_id,
            "recurrence_score": self.recurrence_score,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class ManuscriptFetchLog:
    """Records a manuscript retrieval attempt for LangGraph workflows."""

    fetch_id: str
    session_id: str
    manuscript_hash: str
    tool_id: str
    result: str
    latency_ms: int
    attempt_index: int
    qc_code: str | None = None
    metadata: dict[str, Any] | None = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize fetch log entry."""
        return {
            "fetch_id": self.fetch_id,
            "session_id": self.session_id,
            "manuscript_hash": self.manuscript_hash,
            "tool_id": self.tool_id,
            "result": self.result,
            "latency_ms": self.latency_ms,
            "attempt_index": self.attempt_index,
            "qc_code": self.qc_code,
            "metadata": self.metadata,
        }


class WorkflowStateStore(Protocol):
    """Protocol describing persistence hooks for LangGraph workflows."""

    def begin_session(self, episode_number: int, iteration_policy: IterationPolicy | dict[str, Any]) -> SessionContext:
        """Create a session record and acquire an exclusive lock."""

    def record_step_execution(self, payload: StepExecutionPayload) -> None:
        """Queue a step execution payload for persistence."""

    def record_issue(self, issue: IssuePayload) -> None:
        """Queue an issue record for persistence."""

    def record_issue_resolution(self, resolution: IssueResolutionPayload) -> None:
        """Queue an issue resolution record for persistence."""

    def append_fetch_log(self, log: ManuscriptFetchLog) -> None:
        """Queue a manuscript fetch log entry for persistence."""

    def commit(self) -> None:
        """Flush queued records atomically."""

    def rollback(self) -> None:
        """Discard queued records and release temporary state."""


class FilesystemWorkflowStateStore(WorkflowStateStore):
    """Filesystem-backed WorkflowStateStore implementation for PoC phase."""

    def __init__(
        self,
        project_root: str | Path,
        *,
        session_id: str | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        self._base_dir = self.project_root / ".noveler" / "checks"
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._session_override = session_id
        self._session: SessionContext | None = None
        self._session_payload: dict[str, Any] | None = None
        self._pending_steps: list[StepExecutionPayload] = []
        self._pending_issues: list[IssuePayload] = []
        self._pending_resolutions: list[IssueResolutionPayload] = []
        self._pending_fetch: list[ManuscriptFetchLog] = []
        self._state_version = 0
        self._manifest_path: Path | None = None
        self._audit_path: Path | None = None

    def begin_session(self, episode_number: int, iteration_policy: IterationPolicy | dict[str, Any]) -> SessionContext:
        if self._session is not None:
            return self._session

        policy = self._normalize_iteration_policy(iteration_policy)
        session_id = self._session_override or self._generate_session_id(episode_number)
        session_dir = self._session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        lock_path = session_dir / "session.lock"
        if lock_path.exists() and lock_path.read_text(encoding="utf-8").strip() == "held":
            raise StatePersistenceError(
                "Workflow session is already locked",
                code="state_lock_held",
                details={"session_id": session_id},
            )
        lock_path.write_text("held", encoding="utf-8")

        session_path = session_dir / "session.json"
        now = self._clock().isoformat()
        payload = {
            "session_id": session_id,
            "episode_number": episode_number,
            "created_at": now,
            "last_committed_at": None,
            "iteration_policy": policy.to_dict(),
            "state_version": 1,
            "lock_status": "held",
            "current_status": "active",
        }
        self._write_json(session_path, payload)

        context = SessionContext(
            session_id=session_id,
            episode_number=episode_number,
            state_version=1,
            session_path=session_path,
            lock_path=lock_path,
        )
        self._session = context
        self._session_payload = payload
        self._state_version = 1
        self._clear_pending()
        self._initialize_manifest(context, policy)
        return context

    def record_step_execution(self, payload: StepExecutionPayload) -> None:
        self._ensure_session()
        self._pending_steps.append(payload)

    def record_issue(self, issue: IssuePayload) -> None:
        self._ensure_session()
        self._pending_issues.append(issue)

    def record_issue_resolution(self, resolution: IssueResolutionPayload) -> None:
        self._ensure_session()
        self._pending_resolutions.append(resolution)

    def append_fetch_log(self, log: ManuscriptFetchLog) -> None:
        self._ensure_session()
        self._pending_fetch.append(log)

    def commit(self) -> None:
        self._ensure_session()
        if not any((self._pending_steps, self._pending_issues, self._pending_resolutions, self._pending_fetch)):
            return

        session_dir = self._session_dir(self._session.session_id)
        self._append_records(session_dir / "step_executions.jsonl", self._pending_steps)
        self._append_records(session_dir / "issues.jsonl", self._pending_issues)
        self._append_records(session_dir / "issue_resolutions.jsonl", self._pending_resolutions)
        self._append_records(session_dir / "manuscript_fetch.jsonl", self._pending_fetch)

        commit_summary = self._build_commit_summary()
        self._state_version += 1
        self._update_session_metadata({
            "state_version": self._state_version,
            "last_committed_at": self._clock().isoformat(),
        })
        self._update_manifest(commit_summary)
        self._append_audit(commit_summary)
        self._clear_pending()

    def rollback(self) -> None:
        self._clear_pending()

    # internal helpers -------------------------------------------------

    def _ensure_session(self) -> None:
        if self._session is None:
            raise StatePersistenceError("Workflow session has not been started", code="session_missing")

    def _clear_pending(self) -> None:
        self._pending_steps.clear()
        self._pending_issues.clear()
        self._pending_resolutions.clear()
        self._pending_fetch.clear()

    def _normalize_iteration_policy(self, policy: IterationPolicy | dict[str, Any]) -> IterationPolicy:
        if isinstance(policy, IterationPolicy):
            return policy
        if not isinstance(policy, dict):
            return IterationPolicy()
        count = policy.get("count", 1)
        try:
            count = max(1, int(count))
        except (TypeError, ValueError):
            count = 1
        until_pass = bool(policy.get("until_pass"))
        time_budget_raw = policy.get("time_budget_sec") or policy.get("time_budget_s")
        try:
            time_budget = int(time_budget_raw) if time_budget_raw is not None else None
        except (TypeError, ValueError):
            time_budget = None
        min_improvement_raw = policy.get("min_improvement")
        try:
            min_improvement = float(min_improvement_raw) if min_improvement_raw is not None else None
        except (TypeError, ValueError):
            min_improvement = None
        return IterationPolicy(
            count=count,
            until_pass=until_pass,
            time_budget_sec=time_budget,
            min_improvement=min_improvement,
        )

    def _session_dir(self, session_id: str) -> Path:
        return self._base_dir / session_id / "workflow"

    def _generate_session_id(self, episode_number: int) -> str:
        uid = uuid4().hex
        return f"QC_EP{episode_number:03d}_{uid}"

    def _initialize_manifest(self, context: SessionContext, policy: IterationPolicy) -> None:
        session_dir = self._session_dir(context.session_id)
        self._manifest_path = session_dir / "manifest.json"
        self._audit_path = session_dir / "workflow_audit.jsonl"
        manifest = {
            "session_id": context.session_id,
            "episode_number": context.episode_number,
            "created_at": self._clock().isoformat(),
            "iteration_policy_history": [policy.to_dict()],
            "steps": [],
            "issues": [],
            "issue_resolutions": [],
            "manuscript_fetch": [],
            "last_updated": None,
        }
        self._write_json(self._manifest_path, manifest)

    def _build_commit_summary(self) -> dict[str, Any]:
        timestamp = self._clock().isoformat()
        step_dicts = [self._serialize_step_payload(p) for p in self._pending_steps]
        issue_dicts = [self._serialize_dataclass(i) for i in self._pending_issues]
        resolution_dicts = [self._serialize_dataclass(r) for r in self._pending_resolutions]
        fetch_dicts = [self._serialize_fetch_log(f) for f in self._pending_fetch]
        iteration_policy = None
        if self._session_payload:
            iteration_policy = self._session_payload.get("iteration_policy")
        return {
            "session_id": self._session.session_id,
            "state_version": self._state_version + 1,
            "timestamp": timestamp,
            "steps": step_dicts,
            "issues": issue_dicts,
            "issue_resolutions": resolution_dicts,
            "manuscript_fetch": fetch_dicts,
            "iteration_policy": iteration_policy,
        }

    def _update_manifest(self, summary: dict[str, Any]) -> None:
        if not self._manifest_path:
            return
        try:
            with self._manifest_path.open("r", encoding="utf-8") as fh:
                manifest = json.load(fh)
        except Exception:
            manifest = {
                "session_id": summary.get("session_id"),
                "episode_number": self._session.episode_number,
                "created_at": self._clock().isoformat(),
                "iteration_policy_history": [],
                "steps": [],
                "issues": [],
                "issue_resolutions": [],
                "manuscript_fetch": [],
            }
        policy = summary.get("iteration_policy")
        if policy:
            history = manifest.setdefault("iteration_policy_history", [])
            if policy not in history:
                history.append(policy)
        manifest.setdefault("steps", []).extend(summary.get("steps", []))
        manifest.setdefault("issues", []).extend(summary.get("issues", []))
        manifest.setdefault("issue_resolutions", []).extend(summary.get("issue_resolutions", []))
        manifest.setdefault("manuscript_fetch", []).extend(summary.get("manuscript_fetch", []))
        manifest["last_updated"] = summary.get("timestamp")
        self._write_json(self._manifest_path, manifest)

    def _append_audit(self, summary: dict[str, Any]) -> None:
        if not self._audit_path:
            return
        record = {
            "timestamp": summary.get("timestamp"),
            "session_id": summary.get("session_id"),
            "state_version": summary.get("state_version"),
            "steps_written": len(summary.get("steps", [])),
            "issues_written": len(summary.get("issues", [])),
            "fetch_written": len(summary.get("manuscript_fetch", [])),
        }
        if self._audit_path:
            self._append_records(self._audit_path, [record])

    def _serialize_step_payload(self, payload: StepExecutionPayload) -> dict[str, Any]:
        data = asdict(payload)
        data["started_at"] = payload.started_at.isoformat()
        data["completed_at"] = payload.completed_at.isoformat()
        return data

    def _serialize_fetch_log(self, log: ManuscriptFetchLog) -> dict[str, Any]:
        return asdict(log)

    def _serialize_dataclass(self, value: Any) -> dict[str, Any]:
        if hasattr(value, "__dataclass_fields__"):
            return asdict(value)
        if isinstance(value, dict):
            return value
        return {"value": str(value)}

    def _append_records(self, path: Path, payloads: Iterable[Any]) -> None:
        if not payloads:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            for payload in payloads:
                if hasattr(payload, "to_dict") and callable(payload.to_dict):
                    data = payload.to_dict()
                else:
                    data = payload
                json.dump(data, fh, ensure_ascii=False)
                fh.write("\n")

    def _write_json(self, path: Path, content: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(content, fh, ensure_ascii=False, indent=2)

    def _update_session_metadata(self, updates: dict[str, Any]) -> None:
        if self._session is None or self._session_payload is None:
            return
        self._session_payload.update(updates)
        self._write_json(self._session.session_path, self._session_payload)
        self._session = SessionContext(
            session_id=self._session.session_id,
            episode_number=self._session.episode_number,
            state_version=self._session_payload.get("state_version", self._session.state_version),
            session_path=self._session.session_path,
            lock_path=self._session.lock_path,
        )

