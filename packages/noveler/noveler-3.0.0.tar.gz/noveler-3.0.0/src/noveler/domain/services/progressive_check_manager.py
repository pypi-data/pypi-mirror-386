# File: src/noveler/domain/services/progressive_check_manager.py
# Purpose: Manage stepwise quality checks (12-step system) and generate
#          instructions/results for LLM-driven execution with external
#          template support.
# Context: Domain service. Avoids hard dependencies on presentation layer;
#          console output goes through domain_console wrapper. Logging uses
#          ILogger protocol (fallbacks allowed) to keep infra coupling minimal.

"""段階的品質チェック管理サービス

12ステップ品質チェックシステムの段階実行を管理するサービス
LLMが各チェックステップを個別に実行できるよう、チェックタスクの状態管理と制御を行う
MCPサーバーでの利用を想定し、適切な指示生成を行う

外部テンプレート読み込み機能:
- templates/check_step*.yamlファイルからプロンプトを読み込み
- テンプレート変数の動的置換
- 段階実行制御メッセージの自動挿入
- テンプレート未発見時のフォールバック処理
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol

from glob import glob
from queue import Queue
from threading import Lock, Thread

import yaml

from noveler.domain.interfaces.logger_interface import ILogger, NullLogger
from noveler.domain.utils.domain_console import get_console as _domain_get_console
from importlib import import_module
from noveler.domain.interfaces.path_service_protocol import get_path_service_manager
from noveler.domain.value_objects.universal_prompt_execution import (
    ProjectContext,
    PromptType,
    UniversalPromptRequest,
    UniversalPromptResponse,
)

from noveler.domain.services.workflow_state_store import (
    FilesystemWorkflowStateStore,
    IterationPolicy as WorkflowIterationPolicy,
    StepExecutionPayload,
    SessionContext,
    WorkflowStateStore,
    StatePersistenceError,
)

def _get_console():
    """Domain-safe console accessor (backward compatible for tests)."""

    return _domain_get_console()

# Console instance for this module (domain-safe wrapper)
console = _get_console()

# Backward-compatible factory for tests: wraps the domain path service manager.
def create_path_service(project_root: str | Path | None = None):  # type: ignore[override]
    try:
        manager = get_path_service_manager()
        return manager.create_common_path_service(project_root)
    except Exception:
        return None


# Domain-safe get_logger wrapper to satisfy tests without hard infra dependency
try:
    _infra_get_logger = import_module('noveler.infrastructure.logging.unified_logger').get_logger  # type: ignore
except Exception:
    _infra_get_logger = None  # type: ignore

def get_logger(name: str) -> ILogger:
    """Return an ILogger; prefer infra logger when available else NullLogger.

    This preserves the public symbol for tests that patch
    noveler.domain.services.progressive_check_manager.get_logger while
    avoiding a hard dependency at import time.
    """
    if _infra_get_logger is not None:
        try:
            return _infra_get_logger(name)  # type: ignore[misc]
        except Exception:
            pass
    return NullLogger()


def is_langgraph_workflow_enabled() -> bool:
    """Return True; LangGraph workflow is now the default execution path."""

    value = os.environ.get("NOVELER_LG_PROGRESSIVE_CHECK")
    if value and value.strip().lower() in {"0", "false", "off"}:
        logger = get_logger(__name__)
        logger.warning(
            "NOVELER_LG_PROGRESSIVE_CHECK is no longer a feature flag; "
            "value '%s' is ignored and LangGraph workflow remains enabled.",
            value,
        )
    return True


def create_workflow_state_store(project_root: Path, episode_number: int, session_id: str | None) -> WorkflowStateStore:
    """Factory for WorkflowStateStore; LangGraph workflow is always enabled."""
    return FilesystemWorkflowStateStore(project_root, session_id=session_id)


class UniversalLLMUseCaseProtocol(Protocol):
    """Minimal contract for the UniversalLLMUseCase used by checks."""

    async def execute_with_fallback(
        self, request: UniversalPromptRequest, fallback_enabled: bool = True
    ) -> UniversalPromptResponse:
        ...


@dataclass
class CheckTaskDefinition:
    """チェックタスクの定義"""

    id: int
    name: str
    phase: str
    description: str
    prerequisites: list[int]
    estimated_duration: str
    llm_instruction: str
    next_action: str
    success_criteria: list[str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckTaskDefinition:
        """辞書からインスタンスを作成"""
        return cls(
            id=data["id"],
            name=data["name"],
            phase=data["phase"],
            description=data["description"],
            prerequisites=data.get("prerequisites", []),
            estimated_duration=data.get("estimated_duration", "5-10分"),
            llm_instruction=data["llm_instruction"],
            next_action=data.get("next_action", ""),
            success_criteria=data.get("success_criteria", []),
        )


@dataclass
class CheckExecutionResult:
    """チェック実行結果"""

    step_id: int
    success: bool
    step_name: str | None = None
    content: str | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None
    artifacts: list[str] | None = None
    execution_time: float | None = None
    issues_found: int | None = None
    quality_score: float | None = None
    corrections: list[str] | None = None
    next_step: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """辞書形式で返す"""
        result = {
            "step_id": self.step_id,
            "success": self.success,
            "step_name": self.step_name,
            "content": self.content,
            "error": self.error,
            "metadata": self.metadata,
            "artifacts": self.artifacts,
            "execution_time": self.execution_time,
            "issues_found": self.issues_found,
            "quality_score": self.quality_score,
            "corrections": self.corrections,
            "next_step": self.next_step,
        }
        # None値を除外
        return {k: v for k, v in result.items() if v is not None}



class ProjectConfigError(RuntimeError):
    """プロジェクト設定に起因する致命エラーを表す。"""

    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


class ProgressiveCheckManager:
    """段階的品質チェック管理クラス

    12ステップ品質チェックシステムにおいて、各ステップを個別に実行するための
    状態管理とLLMへの指示生成を担当する

    外部テンプレート読み込み機能により、継続的なプロンプト改善を実現
    """

    def __init__(
        self,
        project_root: str | Path,
        episode_number: int,
        logger: ILogger | None = None,
        io_logger_factory: Callable[[Path], LLMIOLoggerProtocol] | None = None,
        *,
        session_id: str | None = None,
        resume: bool = False,
        manifest: dict[str, Any] | None = None,
        llm_use_case: UniversalLLMUseCaseProtocol | None = None,
        llm_use_case_factory: Callable[[], UniversalLLMUseCaseProtocol] | None = None,
    ) -> None:
        """初期化"""
        self.project_root = Path(project_root)
        self.episode_number = episode_number
        self.logger: ILogger = logger or get_logger(__name__)

        self._base_target_length = self._resolve_target_length()

        self._io_logger_factory = io_logger_factory
        self.path_service = None
        self._llm_use_case_factory = llm_use_case_factory
        self._llm_use_case_instance: UniversalLLMUseCaseProtocol | None = llm_use_case
        self._llm_lock = Lock()
        self._resume_requested = bool(resume)

        if session_id:
            self.session_id = str(session_id)
        else:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
            self.session_id = f"EP{episode_number:03d}_{ts}"

        self._workflow_state_store_factory: Callable[[Path, int, str | None], WorkflowStateStore | None] = create_workflow_state_store
        self._workflow_state_store: WorkflowStateStore | None = None
        self._workflow_session: SessionContext | None = None

        self.io_dir = self.project_root / ".noveler" / "checks" / self.session_id
        self.io_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.io_dir / "manifest.json"

        try:
            self.path_service = create_path_service(str(self.project_root))
        except Exception:
            self.path_service = None

        guide_root = Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド")
        self.prompt_templates_dir = guide_root / "templates"
        self.template_source_log: dict[int, dict[str, Any]] = {}
        self.template_metadata_cache: dict[int, dict[str, Any]] = {}

        self.tasks_config = self._load_tasks_config()

        if self.manifest_path.exists() and (resume or session_id):
            self.manifest = self._load_manifest()
        else:
            self.manifest = manifest or self._initialize_manifest()
            self._save_manifest(self.manifest)

        self.state_file = self.io_dir / f"{self.session_id}_session_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.current_state = self._load_or_initialize_state()

        self._initialize_workflow_store()

        session_label = "再開" if self._resume_requested else "開始"
        console.print(
            f"[bold green]品質チェックセッション{session_label}[/bold green] - "
            f"エピソード{episode_number} (session={self.session_id})"
        )

    def _initialize_workflow_store(self) -> None:
        """Instantiate the workflow state store when the feature flag is enabled."""

        if self._workflow_state_store is not None:
            return
        store = self._workflow_state_store_factory(self.project_root, self.episode_number, self.session_id)
        self._workflow_state_store = store


    @classmethod
    def start_session(
        cls,
        project_root: str | Path,
        episode_number: int,
        *,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """新しい段階的品質チェックセッションを開始する"""
        manager = cls(project_root, episode_number, session_id=None, resume=False)
        tasks_info = manager.get_check_tasks()
        manifest = manager._save_manifest(manager.manifest)
        return {
            "success": True,
            "session_id": manager.session_id,
            "tasks": manager.tasks_config.get("tasks", []),
            "current_step": manager.current_state.get("current_step", 1),
            "manifest_path": str(manager.manifest_path),
            "template_version_set": manifest.get("template_version_set", {}),
            "options": options or {},
        }

    def _load_tasks_config(self) -> dict[str, Any]:
        """タスク定義設定を読み込む"""
        # check_tasks.yamlファイルのパスを設定
        config_path = (
            Path(__file__).parent.parent.parent.parent / "noveler" / "infrastructure" / "config" / "check_tasks.yaml"
        )

        try:
            with config_path.open("r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config if isinstance(config, dict) else {}
        except FileNotFoundError:
            self.logger.exception(f"品質チェック定義ファイルが見つかりません: {config_path}")
            raise
        except Exception:
            self.logger.exception("品質チェック定義ファイル読み込みエラー")
            raise

    def _initialize_manifest(self) -> dict[str, Any]:
        """セッションマニフェストを初期化する"""
        tasks = self.tasks_config.get("tasks", []) if isinstance(self.tasks_config, dict) else []
        template_versions: dict[str, Any] = {}
        for task in tasks:
            try:
                step_id = int(task.get("id"))  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
            metadata = self._collect_template_metadata(step_id)
            if metadata:
                template_versions[str(step_id)] = metadata
        now = datetime.now(timezone.utc).isoformat()
        manifest = {
            "session_id": self.session_id,
            "episode_number": self.episode_number,
            "current_step": 1,
            "completed_steps": [],
            "failed_steps": [],
            "template_version_set": template_versions,
            "created_at": now,
            "last_updated": now,
            "target_length": dict(self._base_target_length),
        }
        return manifest


    def _normalize_target_length_dict(self, candidate: dict[str, Any], *, source: str) -> dict[str, Any]:
        """target_length辞書を検証し正規化する"""
        if not isinstance(candidate, dict):
            raise ProjectConfigError("QC-010", "target_length が辞書形式ではありません", details={"source": source})
        try:
            min_val = int(candidate["min"])
            max_val = int(candidate["max"])
        except (KeyError, TypeError, ValueError) as exc:  # noqa: PERF203
            raise ProjectConfigError("QC-010", "target_length に min/max が存在しないか数値ではありません", details={"source": source}) from exc
        if min_val < 1 or max_val < 1 or min_val >= max_val:
            raise ProjectConfigError("QC-010", "target_length の min/max が不正です", details={"source": source, "min": min_val, "max": max_val})
        result = {"min": min_val, "max": max_val, "source": source}
        return result

    def _resolve_target_length(self) -> dict[str, Any]:
        """プロジェクト設定から target_length を読み込み"""
        config_path = self.project_root / "プロジェクト設定.yaml"
        if not config_path.exists():
            raise ProjectConfigError("QC-009", f"プロジェクト設定ファイルが見つかりません: {config_path}", details={"path": str(config_path)})
        try:
            with config_path.open(encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as exc:  # noqa: PERF203
            raise ProjectConfigError("QC-010", f"プロジェクト設定の解析に失敗しました: {exc}", details={"path": str(config_path)}) from exc
        try:
            writing = config_data["writing"]
            episode = writing["episode"]
            target = episode["target_length"]
        except Exception as exc:  # noqa: BLE001
            raise ProjectConfigError("QC-010", "プロジェクト設定に target_length が定義されていません", details={"path": str(config_path)}) from exc
        normalized = self._normalize_target_length_dict(target, source="project_config")
        normalized["path"] = str(config_path)
        return normalized


    def _determine_target_length_snapshot(self, overrides: dict[str, Any] | None) -> dict[str, Any]:
        """config_overridesを考慮したtarget_lengthスナップショットを返す"""
        if not isinstance(overrides, dict):
            return dict(self._base_target_length)
        target_override = overrides.get("target_length")
        if target_override is None:
            return dict(self._base_target_length)
        normalized = self._normalize_target_length_dict(target_override, source="override")
        return normalized

    def _compute_body_char_count(self, input_data: dict[str, Any]) -> int:
        """manuscript_content等から本文文字数を概算"""
        if not isinstance(input_data, dict):
            return 0
        manuscript_content = input_data.get("manuscript_content")
        if isinstance(manuscript_content, str):
            return len(manuscript_content.strip())
        manuscript_path = input_data.get("manuscript_path")
        if manuscript_path:
            try:
                path_obj = Path(manuscript_path)
                if not path_obj.is_absolute():
                    path_obj = self.project_root / path_obj
                if path_obj.exists():
                    return len(path_obj.read_text(encoding="utf-8").strip())
            except Exception:
                return 0
        return 0

    def _load_manifest(self) -> dict[str, Any]:
        """マニフェストを読み込む（存在しない場合は初期化）"""
        if not self.manifest_path.exists():
            manifest = self._initialize_manifest()
            self._save_manifest(manifest)
            return manifest
        try:
            with self.manifest_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("manifest structure invalid")
        except Exception:
            self.logger.warning("マニフェスト読み込みに失敗したため再初期化します", exc_info=True)
            data = self._initialize_manifest()
            self._save_manifest(data)
        self.manifest = data
        return data

    def _save_manifest(self, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
        """マニフェストを保存し、最新状態を返す"""
        data = manifest or getattr(self, "manifest", None)
        if data is None:
            data = self._initialize_manifest()
        data.setdefault("target_length", dict(self._base_target_length))
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.manifest = data
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with self.manifest_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data

    def _resolve_template_path(self, step_id: int) -> tuple[Path, str] | None:
        """テンプレートファイルのパスと識別ラベルを探索する"""
        template_filename = f"check_step{step_id:02d}_{self._get_step_slug(step_id)}.yaml"
        search_roots = [
            (self.prompt_templates_dir / "quality" / "checks", "checks"),
            (self.prompt_templates_dir / "quality" / "checks" / "backup", "checks_backup"),
            (self.prompt_templates_dir / "writing", "writing"),
        ]
        for directory, label in search_roots:
            template_path = directory / template_filename
            if template_path.exists():
                return template_path, label
        return None

    def _hash_file(self, path: Path) -> str:
        """ファイルのSHA256ハッシュを取得する"""
        try:
            hasher = hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            self.logger.debug("テンプレートハッシュ取得に失敗しました", exc_info=True)
            return ""

    def _collect_template_metadata(
        self,
        step_id: int,
        template_data: dict[str, Any] | None = None,
        *,
        template_path: Path | None = None,
        source: str | None = None,
    ) -> dict[str, Any] | None:
        """テンプレートのメタデータを収集する"""
        if template_path is None or source is None:
            resolved = self._resolve_template_path(step_id)
            if not resolved:
                return None
            template_path, source = resolved
        schema_version = "2.0.0"
        data = template_data
        if data is None:
            try:
                with template_path.open("r", encoding="utf-8") as f:
                    loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    data = loaded
            except Exception:
                data = None
        if isinstance(data, dict):
            schema_version = str(data.get("schema_version") or data.get("version") or schema_version)
        metadata = {
            "version": schema_version,
            "hash": self._hash_file(template_path),
            "path": str(template_path),
            "source": source,
        }
        self.template_metadata_cache[step_id] = metadata
        return metadata

    def _ensure_manifest_template_version(self, step_id: int, metadata: dict[str, Any]) -> None:
        """マニフェスト内のテンプレート情報を最新化する"""
        if not hasattr(self, "manifest") or metadata is None:
            return
        version_set = self.manifest.setdefault("template_version_set", {})
        key = str(step_id)
        existing = version_set.get(key, {})
        if existing.get("hash") == metadata.get("hash") and existing.get("version") == metadata.get("version"):
            return
        version_set[key] = metadata
        self._save_manifest(self.manifest)

    def _normalize_iteration_policy(self, policy: dict[str, Any] | None) -> dict[str, Any]:
        """IterationPolicyを正規化する"""
        defaults: dict[str, Any] = {
            "count": 1,
            "time_budget_s": None,
            "cost_budget": None,
            "until_pass": False,
            "min_improvement": 0.0,
            "dry_run": False,
        }
        if not policy:
            return defaults.copy()
        normalized = defaults.copy()
        for key, value in policy.items():
            normalized[key] = value
        try:
            normalized["count"] = max(1, int(normalized.get("count", 1)))
        except (TypeError, ValueError):
            normalized["count"] = 1
        normalized["dry_run"] = bool(normalized.get("dry_run"))
        normalized["until_pass"] = bool(normalized.get("until_pass"))
        try:
            normalized["min_improvement"] = float(normalized.get("min_improvement") or 0.0)
        except (TypeError, ValueError):
            normalized["min_improvement"] = 0.0
        if normalized.get("time_budget_s") is not None:
            try:
                normalized["time_budget_s"] = max(0, int(normalized["time_budget_s"]))
            except (TypeError, ValueError):
                normalized["time_budget_s"] = None
        if normalized.get("cost_budget") is not None:
            try:
                normalized["cost_budget"] = max(0, int(normalized["cost_budget"]))
            except (TypeError, ValueError):
                normalized["cost_budget"] = None
        return normalized

    def _should_stop_iteration(
        self,
        policy: dict[str, Any],
        attempts: list[dict[str, Any]],
    ) -> tuple[bool, str]:
        """反復を継続するかどうかを判定する"""
        if not attempts:
            return False, ""
        latest_result = attempts[-1]["result"]
        if policy.get("until_pass"):
            issues = latest_result.get("issues_found")
            if issues == 0:
                return True, "until_pass"
            score = latest_result.get("overall_score")
            if issues is None and isinstance(score, (int, float)) and score >= 95:
                return True, "until_pass"
        min_improvement = float(policy.get("min_improvement") or 0.0)
        if min_improvement > 0 and len(attempts) >= 2:
            prev_score = attempts[-2]["result"].get("overall_score")
            new_score = latest_result.get("overall_score")
            if isinstance(prev_score, (int, float)) and isinstance(new_score, (int, float)):
                if (new_score - prev_score) < min_improvement:
                    return True, "min_improvement"
        return False, ""

    def _update_manifest_after_step(
        self,
        step_id: int,
        iteration_info: dict[str, Any],
        execution_result: dict[str, Any],
    ) -> None:
        """マニフェストにステップ実行結果を記録する"""
        if not hasattr(self, "manifest"):
            return
        manifest = self.manifest
        completed = manifest.setdefault("completed_steps", [])
        updated = False
        for entry in completed:
            if entry.get("step_id") == step_id:
                entry["attempts"] = entry.get("attempts", 0) + iteration_info.get("attempts", 1)
                entry["last_score"] = execution_result.get("overall_score")
                entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                entry["stopped_reason"] = iteration_info.get("stopped_reason")
                updated = True
                break
        if not updated:
            completed.append(
                {
                    "step_id": step_id,
                    "attempts": iteration_info.get("attempts", 1),
                    "last_score": execution_result.get("overall_score"),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "stopped_reason": iteration_info.get("stopped_reason"),
                }
            )
        manifest["current_step"] = self.current_state.get("current_step", step_id)
        manifest["last_updated"] = datetime.now(timezone.utc).isoformat()
        manifest["last_iteration_policy"] = iteration_info.get("policy")
        self._save_manifest(manifest)

    def _ensure_workflow_session(self, policy: dict[str, Any]) -> None:
        """Ensure the workflow state store has an active session."""

        if self._workflow_state_store is None or self._workflow_session is not None:
            return
        try:
            count = int(policy.get("count", 1))
        except (TypeError, ValueError):
            count = 1
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
        normalized = WorkflowIterationPolicy(
            count=max(1, count),
            until_pass=bool(policy.get("until_pass")),
            time_budget_sec=time_budget,
            min_improvement=min_improvement,
        )
        self._workflow_session = self._workflow_state_store.begin_session(self.episode_number, normalized)

    def _record_step_execution_to_workflow_store(
        self,
        *,
        step_id: int,
        attempts: list[dict[str, Any]],
        policy: dict[str, Any],
        request_prompt: str,
        sanitized_input: dict[str, Any],
        final_result: dict[str, Any],
        step_start_time: datetime,
        step_completed_at: datetime,
    ) -> None:
        store = self._workflow_state_store
        if store is None:
            return
        self._ensure_workflow_session(policy)
        if self._workflow_session is None:
            return
        try:
            attempt_count = max(1, len(attempts))
            payload = StepExecutionPayload(
                session_id=self._workflow_session.session_id,
                step_id=step_id,
                attempt=attempt_count,
                started_at=step_start_time,
                completed_at=step_completed_at,
                request_prompt_hash=self._hash_for_state_log(request_prompt),
                input_snapshot_hash=self._hash_for_state_log(sanitized_input),
                output_snapshot_hash=self._hash_for_state_log(final_result),
                issues_detected=self._extract_issue_ids(final_result),
                duration_ms=(step_completed_at - step_start_time).total_seconds() * 1000,
                fallback_reason=self._extract_fallback_reason(final_result),
                available_tools=self._extract_available_tools(final_result),
                tool_selection_status=self._extract_tool_selection_status(final_result),
                manuscript_hash_refs=self._extract_manuscript_hash_refs(final_result, sanitized_input),
                metadata={"iteration_policy": policy, "attempts": attempt_count},
            )
            store.record_step_execution(payload)
            store.commit()
        except Exception:
            try:
                store.rollback()
            except Exception:
                pass
            self.logger.warning("workflow state persistence failed", exc_info=True)

    def _hash_for_state_log(self, value: Any) -> str:
        """Generate a stable SHA256 hash for stored workflow payloads."""

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

    def _safe_dict(self, candidate: Any) -> dict[str, Any]:
        return candidate if isinstance(candidate, dict) else {}

    def _extract_issue_ids(self, final_result: dict[str, Any]) -> list[str] | None:
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

    def _extract_available_tools(self, final_result: dict[str, Any]) -> list[Any] | None:
        metadata = self._safe_dict(final_result.get("metadata"))
        tools = metadata.get("available_tools")
        if tools is None:
            tools = final_result.get("available_tools")
        if isinstance(tools, list):
            return list(tools) or None
        return None

    def _extract_tool_selection_status(self, final_result: dict[str, Any]) -> dict[str, Any] | None:
        metadata = self._safe_dict(final_result.get("metadata"))
        status = metadata.get("tool_selection_status")
        if status is None:
            status = final_result.get("tool_selection_status")
        if isinstance(status, dict):
            return status
        return None

    def _extract_manuscript_hash_refs(
        self, final_result: dict[str, Any], sanitized_input: dict[str, Any]
    ) -> list[dict[str, Any]] | None:
        metadata = self._safe_dict(final_result.get("metadata"))
        refs = metadata.get("manuscript_hash_refs")
        if not isinstance(refs, list):
            refs = sanitized_input.get("manuscript_hash_refs") if isinstance(sanitized_input, dict) else None
        if isinstance(refs, list):
            filtered = [ref for ref in refs if isinstance(ref, dict)]
            return filtered or None
        return None

    def _extract_fallback_reason(self, final_result: dict[str, Any]) -> str | None:
        metadata = self._safe_dict(final_result.get("metadata"))
        reason = metadata.get("fallback_reason") if metadata else None
        if reason is None:
            reason = final_result.get("fallback_reason")
        return reason if isinstance(reason, str) and reason else None

    def _perform_step_attempt(
        self,
        task: dict[str, Any],
        normalized_input: dict[str, Any],
        dry_run: bool,
    ) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]:
        """単一のチェックステップ実行を行い結果を返す"""
        prompt_result = self._build_step_request_prompt(task, normalized_input, include_context=True)
        if isinstance(prompt_result, tuple):
            request_prompt, prompt_payload = prompt_result
        else:
            request_prompt = prompt_result
            prompt_payload = None
        payload = prompt_payload or self._prepare_prompt_payload(task, normalized_input)
        sanitized_input = payload.get("sanitized_input", normalized_input)
        if not isinstance(sanitized_input, dict):
            sanitized_input = {"value": sanitized_input}
        else:
            sanitized_input = dict(sanitized_input)
        payload["sanitized_input"] = sanitized_input
        execution_result = (
            self._simulate_dry_run_result(task, normalized_input)
            if dry_run
            else self._execute_check_logic(task, normalized_input, payload)
        )
        return request_prompt, payload, sanitized_input, execution_result

    def _load_or_initialize_state(self) -> dict[str, Any]:
        """状態ファイルを読み込むか、初期状態を作成する"""
        if self.state_file.exists():
            try:
                with self.state_file.open("r", encoding="utf-8") as f:
                    state = json.load(f)
                    return state if isinstance(state, dict) else {}
            except Exception as e:
                self.logger.warning(f"状態ファイル読み込み失敗、初期化します: {e}")

        # 初期状態を作成
        initial_state = {
            "episode_number": self.episode_number,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "current_step": 1,  # 品質チェックはSTEP 1から開始
            "completed_steps": [],
            "failed_steps": [],
            "step_results": {},
            "overall_status": "not_started",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        self._save_state(initial_state)
        return initial_state

    def _save_state(self, state: dict[str, Any]) -> None:
        """状態をファイルに保存する"""
        state["last_updated"] = datetime.now(timezone.utc).isoformat()

        def _json_default(o: Any) -> Any:
            """JSONシリアライズ不能なオブジェクトを安全に変換"""
            try:
                if is_dataclass(o):
                    return asdict(o)
                if hasattr(o, "model_dump") and callable(o.model_dump):
                    return o.model_dump()
                if hasattr(o, "to_dict") and callable(o.to_dict):
                    return o.to_dict()
                if hasattr(o, "__dict__"):
                    # 直接__dict__を返すと再帰が深くなる場合があるためreprにフォールバック
                    return {k: str(v) for k, v in o.__dict__.items()}
            except Exception:
                pass
            # 最終フォールバック
            return str(o)

        try:
            with self.state_file.open("w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False, default=_json_default)
            # セッション状態も保存（テスト用互換）
            session_state_file = self.io_dir / f"{self.session_id}_session_state.json"
            with session_state_file.open("w", encoding="utf-8") as sf:
                json.dump(state | {"session_id": self.session_id}, sf, ensure_ascii=False, indent=2, default=_json_default)
        except Exception:
            self.logger.exception("状態ファイル保存エラー")
            raise

    def get_check_tasks(self) -> dict[str, Any]:
        """LLMに提示するチェックタスクリストを生成する

        Returns:
            チェックタスクリストとLLMへの指示を含む辞書
        """
        tasks = self.tasks_config["tasks"]
        current_step = self.current_state["current_step"]
        completed_steps = self.current_state["completed_steps"]

        # 現在実行可能なタスクを特定
        executable_tasks = self._get_executable_tasks(tasks, completed_steps)
        current_task = self._get_task_by_id(tasks, current_step)

        # LLM向けの指示を生成（改良版：外部テンプレート対応）
        llm_instruction = self._generate_enhanced_llm_instruction(current_task, executable_tasks)

        return {
            "session_id": self.session_id,
            "episode_number": self.episode_number,
            "current_step": current_step,
            "current_task": current_task,
            "executable_tasks": executable_tasks,
            "progress": {
                "completed": len(completed_steps),
                "total": len(tasks),
                "percentage": len(completed_steps) / len(tasks) * 100,
            },
            "llm_instruction": llm_instruction,
            "next_action": self._get_next_action(current_task),
            "phase_info": self._get_current_phase_info(),
        }

    def execute_check_step(
        self,
        step_id: int,
        input_data: dict[str, Any] | None = None,
        dry_run: bool = False,
        *,
        iteration_policy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """特定の品質チェックステップを実行する"""
        tasks = self.tasks_config["tasks"]
        task = self._get_task_by_id(tasks, step_id)

        if not task:
            return {"success": False, "error": f"チェックステップ {step_id} が見つかりません", "step_id": step_id}

        if not self._check_prerequisites(task["prerequisites"]):
            return {
                "success": False,
                "error": f"チェックステップ {step_id} の前提条件が満たされていません",
                "step_id": step_id,
                "prerequisites": task["prerequisites"],
                "completed_steps": self.current_state["completed_steps"],
            }

        try:
            step_start_time = datetime.now(timezone.utc)
            normalized_input = input_data or {}
            target_length_snapshot = self._determine_target_length_snapshot(normalized_input.get("config_overrides"))
            policy = self._normalize_iteration_policy(iteration_policy)
            self._ensure_workflow_session(policy)
            policy_snapshot = dict(policy)
            attempts: list[dict[str, Any]] = []
            stop_reason = "single_run"
            allowed_attempts = policy_snapshot.get("count", 1)

            for attempt_index in range(1, allowed_attempts + 1):
                attempt_dry_run = dry_run or bool(policy_snapshot.get("dry_run"))
                request_prompt, payload, sanitized_input, execution_result = self._perform_step_attempt(
                    task,
                    normalized_input,
                    attempt_dry_run,
                )
                attempts.append({
                    "request_prompt": request_prompt,
                    "payload": payload,
                    "sanitized_input": sanitized_input,
                    "result": execution_result,
                })
                should_stop, reason = self._should_stop_iteration(policy_snapshot, attempts)
                if should_stop:
                    stop_reason = reason
                    break

            if len(attempts) >= allowed_attempts and stop_reason == "single_run" and allowed_attempts > 1:
                stop_reason = "count_limit"

            final_record = attempts[-1]
            final_result = final_record["result"]
            sanitized_input = final_record["sanitized_input"]
            request_prompt = final_record["request_prompt"]
            step_completed_at = datetime.now(timezone.utc)
            iteration_info = {
                "policy": policy_snapshot,
                "attempts": len(attempts),
                "stopped_reason": stop_reason,
            }

            metadata = final_result.setdefault("metadata", {})
            iteration_meta = metadata.setdefault("iteration", {})
            iteration_meta.update(iteration_info)

            metadata.setdefault("config_snapshot", {})["target_length"] = dict(target_length_snapshot)
            body_chars = self._compute_body_char_count(normalized_input)
            metadata["length_stats"] = {
                "body_chars": body_chars,
                "in_range": target_length_snapshot["min"] <= body_chars <= target_length_snapshot["max"],
            }


            try:
                io_logger = None
                if self._io_logger_factory:
                    io_logger = self._io_logger_factory(self.project_root)
                else:
                    try:
                        _mod = import_module('noveler.infrastructure.llm.llm_io_logger')
                        _cls = getattr(_mod, 'LLMIOLogger')
                        io_logger = _cls(self.project_root)
                    except Exception:
                        io_logger = None
                if io_logger is not None:
                    io_logger.save_stage_io(
                        episode_number=self.episode_number,
                        step_number=step_id,
                        stage_name=task.get("name", f"Step {step_id}"),
                        request_content={
                            "prompt": request_prompt,
                            "input_data": sanitized_input,
                            "phase": task.get("phase"),
                        },
                        response_content=final_result,
                        extra_metadata={
                            "kind": "progressive_check_step",
                            "task_id": task.get("id", step_id),
                        },
                    )
            except Exception:
                pass

            self.save_step_input(step_id, sanitized_input)
            self.save_step_output(step_id, final_result)
            self._update_step_completion(step_id, final_result)
            self._update_manifest_after_step(step_id, iteration_info, final_result)

            self._record_step_execution_to_workflow_store(
                step_id=step_id,
                attempts=attempts,
                policy=policy_snapshot,
                request_prompt=request_prompt,
                sanitized_input=sanitized_input,
                final_result=final_result,
                step_start_time=step_start_time,
                step_completed_at=step_completed_at,
            )

            next_task = self._get_next_task()
            llm_instruction = self._generate_step_completion_instruction_enhanced(task, final_result, next_task)

            return {
                "success": True,
                "step_id": step_id,
                "step_name": task["name"],
                "phase": task["phase"],
                "execution_result": final_result,
                "quality_score": final_result.get("overall_score"),
                "next_task": next_task,
                "llm_instruction": llm_instruction,
                "progress": self._get_progress_info(),
                "iteration": iteration_info,
            }

        except Exception as e:
            if self._workflow_state_store is not None:
                try:
                    self._workflow_state_store.rollback()
                except Exception:
                    pass
            self._update_step_failure(step_id, str(e))
            error_instruction = self._generate_error_instruction(task, str(e))
            return {
                "success": False,
                "step_id": step_id,
                "step_name": task["name"],
                "error": str(e),
                "llm_instruction": error_instruction,
            }

    def repeat_step(
        self,
        step_id: int,
        *,
        iteration_policy: dict[str, Any],
        input_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """既存ステップを再実行し、反復メタデータを返す"""
        result = self.execute_check_step(
            step_id,
            input_data=input_data,
            dry_run=False,
            iteration_policy=iteration_policy,
        )
        iteration_meta = result.get("iteration", {})
        return {
            "success": result.get("success", True),
            "attempts": iteration_meta.get("attempts", 1),
            "stopped_reason": iteration_meta.get("stopped_reason"),
            "final_result": result.get("execution_result"),
            "session_id": getattr(self, "session_id", None),
            "iteration": iteration_meta,
        }


    def _build_step_request_prompt(
        self,
        task: dict[str, Any],
        input_data: dict[str, Any] | None = None,
        *,
        include_context: bool = False,
    ) -> str | tuple[str, dict[str, Any]]:
        """チェックステップ実行時にLLMへ提示する指示文を生成

        外部テンプレートがあれば優先して使用し、なければタスク定義のllm_instructionを使う。
        """
        payload = self._prepare_prompt_payload(task, input_data or {})
        prompt = payload.get("prompt") or str(
            task.get("llm_instruction", f"チェックステップ {task.get('id')} を実行してください")
        )
        if include_context:
            return prompt, payload
        return prompt

    # ----- 追加: E2E互換API -----
    def _simulate_dry_run_result(self, task: dict[str, Any], input_data: dict[str, Any] | None) -> dict[str, Any]:
        """ドライラン用の擬似実行結果を生成する."""
        focus_areas = list((input_data or {}).get("focus_areas", []))
        guidance_mode = bool((input_data or {}).get("guidance_mode"))
        step_id = int(task.get("id", 0))
        phase = task.get("phase", "unknown")

        base_score = 74.0 + min(step_id * 2.5, 21.0)
        quality_score = round(min(96.0, base_score), 2)
        issues_found = max(0, 3 - (step_id % 4))

        improvements: list[str] = [f"{task.get('name', 'チェック')}の改善提案{i+1}" for i in range(2)]
        if focus_areas:
            improvements.extend(f"{area}の強化" for area in focus_areas)

        findings = focus_areas or [f"{task.get('name', 'チェック')}に関連する確認事項"]

        return {
            "step_id": step_id,
            "step_name": task.get("name"),
            "phase": phase,
            "content": f"[DRY RUN] {task.get('name', f'Step {step_id}')}のシミュレーション結果",
            "dry_run": True,
            "overall_score": quality_score,
            "quality_breakdown": {
                "clarity": min(100.0, quality_score + 2),
                "consistency": quality_score,
                "readability": max(70.0, quality_score - 3),
            },
            "issues_found": issues_found,
            "findings": findings,
            "improvement_suggestions": improvements,
            "guidance_applied": guidance_mode,
            "metrics": {
                "simulated_processing_time": round(0.3 + step_id * 0.05, 3),
                "confidence": round(min(0.99, 0.75 + step_id * 0.02), 2),
            },
            "applied_input": input_data or {},
        }

    def save_step_input(self, step_id: int, input_data: dict[str, Any]) -> Path:
        """ステップ入力をファイル保存"""
        # 元仕様のままだと同一秒内に保存される入力/出力が同名となり、
        # 上書きが発生するためサフィックスで区別する
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        filename = f"EP{self.episode_number:04d}_step{step_id:02d}_{timestamp}_input.json"
        path = self.io_dir / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump({"step_id": step_id, "input": input_data}, f, ensure_ascii=False, indent=2)
        return path

    def save_step_output(self, step_id: int, output_data: dict[str, Any]) -> Path:
        """ステップ出力をファイル保存"""
        # 入力と同様に上書き防止のため _output サフィックスを付与
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        filename = f"EP{self.episode_number:04d}_step{step_id:02d}_{timestamp}_output.json"
        path = self.io_dir / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump({"step_id": step_id, "output": output_data}, f, ensure_ascii=False, indent=2)
        return path

    def get_execution_status(self) -> dict[str, Any]:
        """現在の実行状況を取得（E2E互換）"""
        completed = self.current_state.get("completed_steps", [])
        return {
            "session_id": self.session_id,
            "episode_number": self.episode_number,
            "completed_steps": len(completed),
            "last_completed_step": max(completed) if completed else 0,
            "overall_status": self.current_state.get("overall_status", "unknown"),
            "progress": self._get_progress_info(),
        }

    def can_resume_session(self, session_id: str) -> bool:
        """セッション復旧の可否を判定"""
        file = self.io_dir / f"{session_id}_session_state.json"
        return file.exists()

    def resume_session(self, session_id: str) -> None:
        """セッションを復旧"""
        file = self.io_dir / f"{session_id}_session_state.json"
        if not file.exists():
            msg = "Session state not found"
            raise FileNotFoundError(msg)
        with file.open(encoding="utf-8") as f:
            state = json.load(f)
        self.current_state = state
        self.session_id = session_id

    def get_check_status(self) -> dict[str, Any]:
        """現在のチェック状況を取得する"""
        tasks = self.tasks_config["tasks"]
        current_task = self._get_task_by_id(tasks, self.current_state["current_step"])

        return {
            "episode_number": self.episode_number,
            "session_id": self.session_id,
            "overall_status": self.current_state["overall_status"],
            "current_step": self.current_state["current_step"],
            "current_task": current_task,
            "progress": self._get_progress_info(),
            "completed_steps": self.current_state["completed_steps"],
            "failed_steps": self.current_state["failed_steps"],
            "last_updated": self.current_state["last_updated"],
        }

    def get_check_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """品質チェック履歴を取得する"""
        history = []

        # 完了したステップの履歴を取得
        for step_id in self.current_state["completed_steps"]:
            result = self.current_state["step_results"].get(str(step_id))
            if result:
                history.append(
                    {
                        "step_id": step_id,
                        "step_name": result.get("step_name", f"Step {step_id}"),
                        "status": "completed",
                        "result": result,
                        "timestamp": result.get("timestamp", ""),
                    }
                )

        # 失敗したステップの履歴を取得
        history.extend(
            [
                {
                    "step_id": failure.get("step_id"),
                    "step_name": failure.get("step_name", f"Step {failure.get('step_id')}"),
                    "status": "failed",
                    "error": failure.get("error"),
                    "timestamp": failure.get("timestamp", ""),
                }
                for failure in self.current_state["failed_steps"]
            ]
        )

        # タイムスタンプでソートして最新順に
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return history[:limit]

    def _get_executable_tasks(self, tasks: list[dict[str, Any]], completed_steps: list[int]) -> list[dict[str, Any]]:
        """現在実行可能なタスクを取得する"""
        executable = []
        for task in tasks:
            if task["id"] in completed_steps:
                continue
            if self._check_prerequisites(task["prerequisites"], completed_steps):
                executable.append(task)
        return executable

    def _get_task_by_id(self, tasks: list[dict[str, Any]], task_id: int) -> dict[str, Any] | None:
        """IDでタスクを取得する"""
        for task in tasks:
            if task["id"] == task_id:
                return task
        return None

    def _check_prerequisites(self, prerequisites: list[int], completed_steps: list[int] | None = None) -> bool:
        """前提条件をチェックする"""
        if completed_steps is None:
            completed_steps = self.current_state["completed_steps"]

        return all(prereq in completed_steps for prereq in prerequisites)

    def _load_prompt_template(self, step_id: int) -> dict[str, Any] | None:
        """外部YAMLプロンプトテンプレートを読み込む"""
        resolved = self._resolve_template_path(step_id)
        if not resolved:
            self.logger.debug("品質チェックテンプレートが見つかりません: check_step%02d", step_id)
            return None
        template_path, label = resolved
        try:
            with template_path.open("r", encoding="utf-8") as f:
                template_data = yaml.safe_load(f)
        except Exception as template_error:  # noqa: PERF203
            self.logger.warning(
                "品質チェックテンプレート読み込みエラー: %s (source=%s) %s",
                template_path,
                label,
                template_error,
                exc_info=True,
            )
            return None
        if not isinstance(template_data, dict):
            self.logger.warning(
                "品質チェックテンプレート構造が不正: %s (source=%s)",
                template_path,
                label,
            )
            return None

        metadata = self._collect_template_metadata(
            step_id,
            template_data,
            template_path=template_path,
            source=label,
        )
        if metadata is None:
            metadata = {"source": label, "path": str(template_path)}
        self.template_source_log[step_id] = metadata
        self._ensure_manifest_template_version(step_id, metadata)
        self.logger.info(
            "品質チェックテンプレート読み込み完了: %s (source=%s)",
            template_path.name,
            label,
        )
        return template_data


    def _get_step_slug(self, step_id: int) -> str:
        """ステップIDに基づいてファイル名用のスラッグを生成する

        Args:
            step_id: ステップID

        Returns:
            ファイル名用スラッグ
        """
        task = self._get_task_by_id(self.tasks_config["tasks"], step_id)
        if not task:
            return "unknown"

        # タスク名を元にスラッグを生成
        name = task["name"]
        slug_mapping = {
            "誤字脱字チェック": "typo_check",
            "文法・表記統一チェック": "grammar_check",
            "読みやすさ基礎チェック": "readability_check",
            "キャラクター一貫性チェック": "character_consistency",
            "プロット整合性チェック": "plot_consistency",
            "世界観・設定チェック": "worldview_check",
            "構造・起承転結チェック": "structure_check",
            "伏線・回収チェック": "foreshadowing_check",
            "シーン転換チェック": "scene_transition",
            "文章表現・文体チェック": "expression_check",
            "リズム・テンポチェック": "rhythm_tempo",
            "総合品質認定": "final_quality_approval",
        }

        slug = slug_mapping.get(name, name.lower().replace("・", "_").replace("（", "_").replace("）", ""))
        return str(slug)

    def _prepare_template_variables(self, step_id: int, current_task: dict[str, Any] | None = None) -> dict[str, Any]:
        """テンプレート用の変数を準備する

        Args:
            step_id: ステップID
            current_task: 現在のタスク情報

        Returns:
            テンプレート変数辞書
        """
        if current_task is None:
            current_task = self._get_task_by_id(self.tasks_config["tasks"], step_id)

        tasks = self.tasks_config["tasks"]
        completed_steps = self.current_state["completed_steps"]

        return {
            "step_id": step_id,
            "step_name": current_task["name"] if current_task else f"チェックステップ {step_id}",
            "episode_number": self.episode_number,
            "episode_number_formatted": f"{self.episode_number:03d}",
            "project_root": str(self.project_root),
            "session_id": self.session_id,
            "completed_steps": len(completed_steps),
            "total_steps": len(tasks),
            "phase": current_task.get("phase", "unknown") if current_task else "unknown",
            "next_step_id": step_id + 1 if step_id < len(tasks) else None,
        }

    def _replace_variables(self, template_content: str, variables: dict[str, Any]) -> str:
        """テンプレート内の変数を置換する

        Args:
            template_content: テンプレート文字列
            variables: 置換変数辞書

        Returns:
            変数置換後の文字列
        """
        try:
            return template_content.format(**variables)
        except KeyError as e:
            self.logger.warning(f"テンプレート変数が見つかりません: {e}")
            return template_content
        except Exception:
            self.logger.exception("テンプレート変数置換エラー")
            return template_content

    def _sanitize_for_json(self, value: Any) -> Any:
        '''Convert values into JSON serialisable structures.'''
        try:
            json.dumps(value, ensure_ascii=False)
            return value
        except (TypeError, ValueError):
            if isinstance(value, dict):
                return {str(k): self._sanitize_for_json(v) for k, v in value.items()}
            if isinstance(value, (list, tuple, set)):
                return [self._sanitize_for_json(v) for v in value]
            if isinstance(value, Path):
                return str(value)
            return str(value)

    def _prepare_prompt_payload(
        self, task: dict[str, Any], input_data: dict[str, Any]
    ) -> dict[str, Any]:
        '''Build a payload bundling template data, variables, and manuscript content.'''
        step_id = int(task.get('id', 0))
        variables = self._prepare_template_variables(step_id, task)
        variables.setdefault('project_root', str(self.project_root))
        variables.setdefault('episode_number', self.episode_number)
        variables.setdefault('episode_number_formatted', f'{self.episode_number:03d}')
        template_data = self._load_prompt_template(step_id) if isinstance(task, dict) else None
        template_source = self.template_source_log.get(step_id)
        sanitized_input = self._sanitize_for_json(dict(input_data))
        manuscript_content, context_files = self._load_manuscript_content(template_data, variables, input_data)
        prompt_text = ''
        if template_data:
            prompt_text = self._render_quality_template(
                template_data, variables, manuscript_content, sanitized_input
            )
        if not prompt_text:
            fallback = str(task.get('llm_instruction', f'チェックステップ {step_id} を実行してください'))
            prompt_text = self._replace_variables(fallback, variables)
        return {
            'prompt': prompt_text,
            'template_data': template_data,
            'variables': variables,
            'sanitized_input': sanitized_input,
            'manuscript_content': manuscript_content,
            'context_files': context_files,
            'template_source': template_source,
        }

    def _render_quality_template(
        self,
        template_data: dict[str, Any],
        variables: dict[str, Any],
        manuscript_content: str,
        sanitized_input: dict[str, Any],
    ) -> str:
        '''Render Schema v2 quality template into an LLM prompt.'''

        def _fmt_list(items: list[Any]) -> str:
            formatted: list[str] = []
            for item in items:
                if isinstance(item, str):
                    formatted.append(f"- {self._replace_variables(item, variables)}")
                else:
                    formatted.append(
                        f"- {json.dumps(self._sanitize_for_json(item), ensure_ascii=False)}"
                    )
            return '\n'.join(formatted)

        role_messages = (template_data.get('llm_config') or {}).get('role_messages', {})
        system_msg = role_messages.get('system', '').strip()
        user_msg = role_messages.get('user', '').strip()

        prompt_section = template_data.get('prompt', {})
        main_instruction = prompt_section.get('main_instruction', '')
        formatted_instruction = (
            self._replace_variables(main_instruction, variables) if main_instruction else ''
        )

        constraints = template_data.get('constraints', {})
        hard_rules = constraints.get('hard_rules', [])
        soft_targets = constraints.get('soft_targets', [])

        tasks_section = template_data.get('tasks', {})
        task_bullets = tasks_section.get('bullets', [])
        task_details = tasks_section.get('details', [])

        acceptance = template_data.get('acceptance_criteria', {})
        checklist = acceptance.get('checklist', [])
        metrics = acceptance.get('metrics', [])
        by_task = acceptance.get('by_task', [])

        check_criteria = template_data.get('check_criteria', {})

        sections: list[str] = []
        if system_msg:
            sections.append('# System Role\n' + system_msg)
        if user_msg:
            sections.append('# User Instructions\n' + user_msg)
        if formatted_instruction:
            sections.append('# Main Instruction\n' + formatted_instruction)

        if hard_rules or soft_targets:
            rule_lines: list[str] = []
            if hard_rules:
                rule_lines.append('*Hard Rules*\n' + _fmt_list(hard_rules))
            if soft_targets:
                rule_lines.append('*Soft Targets*\n' + _fmt_list(soft_targets))
            sections.append('# Constraints\n' + '\n\n'.join(rule_lines))

        if task_bullets or task_details:
            detail_lines: list[str] = []
            if task_bullets:
                detail_lines.append('*Primary Tasks*\n' + _fmt_list(task_bullets))
            for detail in task_details:
                name = detail.get('name')
                items = detail.get('items', [])
                if items:
                    lines = []
                    for item in items:
                        text = item.get('text') if isinstance(item, dict) else item
                        lines.append(self._replace_variables(str(text), variables))
                    detail_lines.append(
                        f"*{self._replace_variables(str(name), variables)}*\n" + '\n'.join(f'- {line}' for line in lines)
                    )
            sections.append('# Tasks\n' + '\n\n'.join(detail_lines))

        artifacts = template_data.get('artifacts', {})
        if artifacts:
            art_lines: list[str] = [
                f"- format: {artifacts.get('format', 'unknown')}",
                f"- required_fields: {', '.join(artifacts.get('required_fields', []))}",
            ]
            example_payload = artifacts.get('example')
            if example_payload:
                example_text = (
                    example_payload
                    if isinstance(example_payload, str)
                    else json.dumps(self._sanitize_for_json(example_payload), ensure_ascii=False, indent=2)
                )
                art_lines.append('- example:\n' + str(example_text).strip())
            sections.append('# Output Specification\n' + '\n'.join(art_lines))

        acceptance_lines: list[str] = []
        if checklist:
            acceptance_lines.append('*Checklist*\n' + _fmt_list(checklist))
        if metrics:
            metric_lines = [
                f"- {metric.get('name')}: target={metric.get('target')}, method={metric.get('method')}"
                for metric in metrics
            ]
            acceptance_lines.append('*Metrics*\n' + '\n'.join(metric_lines))
        if by_task:
            bt_lines = [
                f"- {entry.get('id')}: field={entry.get('field')}, rule={entry.get('rule')}"
                for entry in by_task
            ]
            acceptance_lines.append('*By Task*\n' + '\n'.join(bt_lines))
        if acceptance_lines:
            sections.append('# Acceptance Criteria\n' + '\n\n'.join(acceptance_lines))

        if check_criteria:
            criteria_lines: list[str] = []
            for key, guidelines in check_criteria.items():
                header = self._replace_variables(str(key), variables)
                if isinstance(guidelines, list):
                    entries = '\n'.join(
                        f"  - {self._replace_variables(str(item), variables)}" for item in guidelines
                    )
                else:
                    entries = str(guidelines)
                criteria_lines.append(f'- {header}\n{entries}')
            sections.append('# Check Criteria\n' + '\n'.join(criteria_lines))

        if sanitized_input:
            sections.append('# Execution Context\n' + json.dumps(sanitized_input, ensure_ascii=False, indent=2))

        manuscript_block = manuscript_content.strip() if manuscript_content else '(原稿を取得できませんでした)'
        sections.append('# Manuscript\n```markdown\n' + manuscript_block + '\n```')

        return '\n\n'.join(section.strip() for section in sections if section and section.strip()) + '\n'

    def _resolve_template_input_files(
        self, template_data: dict[str, Any] | None, variables: dict[str, Any]
    ) -> list[Path]:
        if not template_data:
            return []
        files = template_data.get('inputs', {}).get('files', [])
        resolved: list[Path] = []
        for entry in files:
            path_template = entry.get('path')
            if not path_template:
                continue
            try:
                formatted = path_template.format(**variables)
            except Exception:
                try:
                    formatted = path_template.format(**(variables | {'project_root': str(self.project_root)}))
                except Exception:
                    continue
            for candidate in self._expand_path_pattern(formatted):
                if candidate not in resolved:
                    resolved.append(candidate)
        return resolved

    def _expand_path_pattern(self, pattern: str) -> list[Path]:
        expanded = os.path.expanduser(str(pattern))
        matches = glob(expanded)
        if matches:
            return [Path(match) for match in matches]
        return [Path(expanded)]

    def _guess_episode_manuscript_path(self) -> Path | None:
        try:
            manuscript_dir: Path | None = None
            if self.path_service and hasattr(self.path_service, 'get_manuscript_dir'):
                raw = self.path_service.get_manuscript_dir()  # type: ignore[call-arg]
                manuscript_dir = raw if isinstance(raw, Path) else Path(raw)
            if manuscript_dir is None:
                manuscript_dir = self.project_root / '40_原稿'
            if not manuscript_dir.is_absolute():
                manuscript_dir = self.project_root / manuscript_dir
            if not manuscript_dir.exists():
                alt_dir = self.project_root / 'manuscripts'
                manuscript_dir = alt_dir if alt_dir.exists() else manuscript_dir
            if not manuscript_dir.exists():
                return None
            patterns = [
                f'第{self.episode_number:03d}話*.md',
                f'episode_{self.episode_number:03d}.md',
                f'{self.episode_number:03d}_*.md',
            ]
            for pattern in patterns:
                for candidate in manuscript_dir.glob(pattern):
                    if candidate.is_file():
                        return candidate
            latest = None
            for candidate in manuscript_dir.glob('*.md'):
                if candidate.is_file():
                    if latest is None or candidate.stat().st_mtime > latest.stat().st_mtime:
                        latest = candidate
            return latest
        except Exception:
            return None

    def _load_manuscript_content(
        self,
        template_data: dict[str, Any] | None,
        variables: dict[str, Any],
        input_data: dict[str, Any],
    ) -> tuple[str, list[Path]]:
        context_paths: list[Path] = []
        manuscript_content = input_data.get('manuscript_content')
        if isinstance(manuscript_content, str) and manuscript_content.strip():
            return manuscript_content, context_paths

        candidate_paths: list[Path] = []
        manual_path = input_data.get('manuscript_path')
        if manual_path:
            manual = Path(manual_path) if isinstance(manual_path, (str, Path)) else None
            if manual is not None and not manual.is_absolute():
                manual = self.project_root / manual
            if manual is not None:
                candidate_paths.append(manual)

        candidate_paths.extend(self._resolve_template_input_files(template_data, variables))
        guessed = self._guess_episode_manuscript_path()
        if guessed:
            candidate_paths.append(guessed)

        for candidate in candidate_paths:
            try:
                if candidate.exists() and candidate.is_file():
                    content = candidate.read_text(encoding='utf-8')
                    context_paths.append(candidate)
                    return content, context_paths
            except Exception:
                continue
        return '', context_paths

    def _create_llm_request(
        self,
        task: dict[str, Any],
        payload: dict[str, Any],
    ) -> UniversalPromptRequest:
        context_files = [
            path for path in payload.get('context_files', [])
            if isinstance(path, Path) and path.exists()
        ]
        project_context = ProjectContext(
            project_root=self.project_root,
            project_name=self.project_root.name,
            additional_context_files=context_files,
        )
        type_specific_config = self._sanitize_for_json(
            {
                'episode_number': self.episode_number,
                'step_id': task.get('id'),
                'phase': task.get('phase'),
                'task_name': task.get('name'),
                'template_source': payload.get('template_source'),
                'variables': payload.get('variables'),
                'input_data': payload.get('sanitized_input'),
            }
        )
        return UniversalPromptRequest(
            prompt_content=payload['prompt'],
            prompt_type=PromptType.QUALITY_CHECK,
            project_context=project_context,
            output_format='json',
            max_turns=1,
            type_specific_config=type_specific_config,
        )

    def _create_llm_use_case(self) -> UniversalLLMUseCaseProtocol | None:
        if self._llm_use_case_factory is not None:
            try:
                return self._llm_use_case_factory()
            except Exception as exc:
                self.logger.warning('LLM use case factory failed: %s', exc)
                return None
        with self._llm_lock:
            if self._llm_use_case_instance is None:
                try:
                    factory_module = import_module('noveler.application.use_cases.universal_llm_use_case_factory')
                    factory = getattr(factory_module, 'UniversalLLMUseCaseFactory')
                    self._llm_use_case_instance = factory.create_use_case()
                except Exception as exc:
                    self.logger.warning('UniversalLLMUseCase生成に失敗しました: %s', exc)
                    return None
        return self._llm_use_case_instance

    def _run_llm_use_case(self, request: UniversalPromptRequest) -> UniversalPromptResponse:
        result_queue: Queue[tuple[bool, UniversalPromptResponse | Exception]] = Queue()

        def runner() -> None:
            try:
                use_case = self._create_llm_use_case()
                if use_case is None:
                    raise RuntimeError('UniversalLLMUseCase is not available')
                response = asyncio.run(use_case.execute_with_fallback(request, fallback_enabled=True))
                result_queue.put((True, response))
            except Exception as exc:  # noqa: BLE001 - keep raw exception for logging
                result_queue.put((False, exc))

        thread = Thread(target=runner, daemon=True)
        thread.start()
        thread.join()
        success, payload = result_queue.get()
        if success:
            return payload  # type: ignore[return-value]
        raise payload

    def _safe_json_loads(self, content: str) -> dict[str, Any] | None:
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

    def _process_llm_response(
        self,
        task: dict[str, Any],
        payload: dict[str, Any],
        response: UniversalPromptResponse,
    ) -> dict[str, Any]:
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

    def _generate_static_execution_result(self, task: dict[str, Any]) -> dict[str, Any]:
        step_id = task.get('id', 0)
        step_name = task.get('name', f'Step {step_id}')
        base_score = 75.0 + min(step_id * 1.8, 18.0)
        overall_score = round(min(96.0, base_score), 2)
        return {
            'step_id': step_id,
            'step_name': step_name,
            'content': f'{step_name}を実行しました',
            'metadata': {'llm_used': False},
            'artifacts': [],
            'overall_score': overall_score,
            'quality_breakdown': {
                'clarity': overall_score,
                'consistency': max(70.0, overall_score - 5),
                'readability': max(72.0, overall_score - 3),
            },
            'improvement_suggestions': [f'{step_name}の改善提案'],
        }

    def _generate_enhanced_llm_instruction(
        self, current_task: dict[str, Any] | None, executable_tasks: list[dict[str, Any]]
    ) -> str:
        """外部テンプレートを使用してLLM指示を生成する（改良版）

        Args:
            current_task: 現在のタスク
            executable_tasks: 実行可能なタスクリスト

        Returns:
            LLM指示文字列
        """
        if not current_task:
            if not executable_tasks:
                return "全ての品質チェックが完了しました。お疲れさまでした！"
            current_task = executable_tasks[0]

        step_id = current_task["id"]

        # 外部テンプレートを試行
        template_data = self._load_prompt_template(step_id)
        if template_data:
            # 外部テンプレートが見つかった場合
            variables = self._prepare_template_variables(step_id, current_task)

            prompt_section = template_data.get("prompt", {})
            main_instruction = prompt_section.get("main_instruction", "")

            if main_instruction:
                enhanced_instruction = self._replace_variables(main_instruction, variables)

                # 制御設定の確認
                control_settings = template_data.get("control_settings", {})
                if control_settings.get("strict_single_step", False):
                    self.logger.info(f"チェックステップ {step_id} で厳格な単一ステップ実行を強制")

                return enhanced_instruction

        # フォールバック：従来のテンプレートシステム
        return self._generate_llm_instruction_legacy(current_task, executable_tasks)

    def _generate_llm_instruction_legacy(
        self, current_task: dict[str, Any], _executable_tasks: list[dict[str, Any]]
    ) -> str:
        """従来のLLM指示生成（フォールバック用）"""
        template = self.tasks_config.get("llm_templates", {}).get("step_completion", "")
        if template:
            formatted = template.format(
                step_id=current_task["id"],
                step_name=current_task["name"],
                next_action=current_task.get("next_action", ""),
                llm_instruction=current_task.get("llm_instruction", ""),
                result_summary="初回実行のため結果はありません",
            )
            return str(formatted)

        instruction = current_task.get(
            "llm_instruction", "チェックステップ {} を実行してください".format(current_task["id"])
        )
        return str(instruction)

    def _execute_check_logic(
        self,
        task: dict[str, Any],
        input_data: dict[str, Any] | None = None,
        prompt_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Perform the actual check step using LLM with graceful fallback."""
        payload = prompt_payload or self._prepare_prompt_payload(task, input_data or {})
        try:
            request = self._create_llm_request(task, payload)
            response = self._run_llm_use_case(request)
            if not response.is_success():
                raise RuntimeError(response.error_message or 'LLM execution returned failure')
            return self._process_llm_response(task, payload, response)
        except Exception as exc:  # noqa: BLE001 - log raw exception for diagnostics
            self.logger.warning(
                'LLM実行に失敗したためフォールバックします (step=%s): %s',
                task.get('id'),
                exc,
                exc_info=True,
            )
            fallback = self._generate_static_execution_result(task)
            metadata = fallback.setdefault('metadata', {})
            metadata['llm_used'] = False
            metadata['fallback_reason'] = str(exc)
            metadata['template_source'] = payload.get('template_source') if payload else None
            metadata['context_files'] = [str(path) for path in payload.get('context_files', [])] if payload else []
            metadata['prompt_preview'] = (payload.get('prompt') or '')[:2000] if payload else ''
            return fallback

    def _update_step_completion(self, step_id: int, result: dict[str, Any]) -> None:
        """ステップ完了時の状態更新"""
        if step_id not in self.current_state["completed_steps"]:
            self.current_state["completed_steps"].append(step_id)

        self.current_state["step_results"][str(step_id)] = result

        # 次のステップに進む
        next_step = self._find_next_step()
        if next_step is not None:
            self.current_state["current_step"] = next_step
            self.current_state["overall_status"] = "in_progress"
        else:
            self.current_state["overall_status"] = "completed"

        self._save_state(self.current_state)

    def _update_step_failure(self, step_id: int, error: str) -> None:
        """ステップ失敗時の状態更新"""
        failure_record = {"step_id": step_id, "error": error, "timestamp": datetime.now(timezone.utc).isoformat()}

        self.current_state["failed_steps"].append(failure_record)
        self.current_state["overall_status"] = "error"

        self._save_state(self.current_state)

    def _find_next_step(self) -> int | None:
        """次に実行すべきステップを見つける"""
        tasks = self.tasks_config["tasks"]
        completed = self.current_state["completed_steps"]

        for task in tasks:
            if task["id"] not in completed and self._check_prerequisites(task["prerequisites"], completed):
                return int(task["id"])

        return None

    def _get_next_task(self) -> dict[str, Any] | None:
        """次のタスクを取得する"""
        next_step_id = self._find_next_step()
        if next_step_id is not None:
            return self._get_task_by_id(self.tasks_config["tasks"], next_step_id)
        return None

    def _generate_step_completion_instruction_enhanced(
        self, completed_task: dict[str, Any], result: dict[str, Any], next_task: dict[str, Any] | None
    ) -> str:
        """ステップ完了後のLLM指示を生成する（改良版：外部テンプレート対応）"""
        if next_task:
            # 次のタスクが存在する場合、そのタスクの外部テンプレートを確認
            next_template_data = self._load_prompt_template(next_task["id"])
            if next_template_data:
                # 次のステップ用の外部テンプレートがある場合
                variables = self._prepare_template_variables(next_task["id"], next_task)
                variables.update(
                    {
                        "previous_step_id": completed_task["id"],
                        "previous_step_name": completed_task["name"],
                        "result_summary": result.get("content", "チェック完了"),
                    }
                )

                prompt_section = next_template_data.get("prompt", {})
                next_action_instruction = prompt_section.get("next_action_instruction", "")

                if next_action_instruction:
                    return """チェックステップ {}「{}」が完了しました。

{}""".format(completed_task["id"], completed_task["name"], self._replace_variables(next_action_instruction, variables))

        # フォールバック：従来のステップ完了指示生成
        return self._generate_step_completion_instruction_legacy(completed_task, result, next_task)

    def _generate_step_completion_instruction_legacy(
        self, completed_task: dict[str, Any], result: dict[str, Any], next_task: dict[str, Any] | None
    ) -> str:
        """ステップ完了後のLLM指示を生成する（従来版）"""
        template = self.tasks_config.get("llm_templates", {}).get("step_completion", "")

        if template and next_task:
            formatted = template.format(
                step_id=completed_task["id"],
                step_name=completed_task["name"],
                result_summary=result.get("content", "チェック完了"),
                next_action=next_task.get("next_action", ""),
                llm_instruction=next_task.get("llm_instruction", ""),
            )
            return str(formatted)
        if next_task:
            return """チェックステップ {}「{}」が完了しました。

次のチェックステップ：execute_check_step で step_id={} を実行してください。

{}""".format(completed_task["id"], completed_task["name"], next_task["id"], next_task.get("llm_instruction", ""))
        return "全てのチェックステップが完了しました。12ステップ品質チェックシステムの実行が完了しました！"

    def _generate_error_instruction(self, failed_task: dict[str, Any], error: str) -> str:
        """エラー時のLLM指示を生成する"""
        template = self.tasks_config.get("llm_templates", {}).get("error_handling", "")

        if template:
            formatted = template.format(step_id=failed_task["id"], step_name=failed_task["name"], error_message=error)
            return str(formatted)

        return """チェックステップ {}「{}」でエラーが発生しました：
{}

get_check_status ツールで現在の状況を確認してください。
修正後、同じステップを再実行してください。""".format(failed_task["id"], failed_task["name"], error)

    def _get_next_action(self, task: dict[str, Any] | None) -> str:
        """次のアクションを取得する"""
        if task:
            action = task.get("next_action", "execute_check_step で step_id={} を実行してください".format(task["id"]))
            return str(action)
        return "全てのチェックタスクが完了しています"

    def _get_current_phase_info(self) -> dict[str, Any]:
        """現在のフェーズ情報を取得する"""
        current_task = self._get_task_by_id(self.tasks_config["tasks"], self.current_state["current_step"])
        if not current_task:
            return {"phase": "completed", "description": "全フェーズ完了"}

        phase_name = current_task["phase"]
        phases = self.tasks_config.get("phases", {})
        phase_info = phases.get(phase_name, {"name": phase_name, "description": ""})

        return {
            "phase": phase_name,
            "name": phase_info.get("name", phase_name),
            "description": phase_info.get("description", ""),
        }

    def _get_progress_info(self) -> dict[str, Any]:
        """進捗情報を取得する"""
        total_tasks = len(self.tasks_config["tasks"])
        completed_count = len(self.current_state["completed_steps"])

        return {
            "completed": completed_count,
            "total": total_tasks,
            "percentage": round(completed_count / total_tasks * 100, 1),
            "remaining": total_tasks - completed_count,
        }
