"""Domain.value_objects.langsmith_artifacts
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


@dataclass(slots=True)
class LangSmithRun:
    """LangSmithのRun情報を表現する値オブジェクト"""

    run_id: str
    name: str
    status: str
    error: str | None = None
    trace_url: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_failure(self) -> bool:
        """エラーかどうかを判定"""
        return self.status.lower() not in {"success", "completed"}

    def to_dataset_entry(self, expected_behavior: str | None = None) -> dict[str, Any]:
        """データセット行へ変換"""
        return {
            "run_id": self.run_id,
            "name": self.name,
            "status": self.status,
            "trace_url": self.trace_url,
            "inputs": self.inputs,
            "observed_output": self.outputs,
            "expected_behavior": expected_behavior,
            "error": self.error,
            "captured_at": self.captured_at.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata,
        }

    def headline(self) -> str:
        """サマリの見出しテキストを取得"""
        status_icon = "❌" if self.is_failure else "✅"
        return f"{status_icon} LangSmith Run {self.run_id} ({self.name})"


@dataclass(slots=True)
class LangSmithBugfixArtifacts:
    """生成された成果物のメタ情報"""

    run: LangSmithRun
    summary_path: Path
    prompt_path: Path
    dataset_entry_path: Path | None = None


@dataclass(slots=True)
class PatchResult:
    """パッチ適用結果"""

    applied: bool
    stdout: str
    stderr: str
    command: Sequence[str]


@dataclass(slots=True)
class VerificationResult:
    """検証コマンドの実行結果"""

    returncode: int
    stdout: str
    stderr: str
    command: Sequence[str]

    @property
    def succeeded(self) -> bool:
        """成功判定"""
        return self.returncode == 0
