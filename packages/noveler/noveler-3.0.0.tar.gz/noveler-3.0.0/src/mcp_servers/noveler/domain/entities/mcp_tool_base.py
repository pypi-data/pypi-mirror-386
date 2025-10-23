# File: src/mcp_servers/noveler/domain/entities/mcp_tool_base.py
# Purpose: Define core request/response data structures and the abstract base
#          class for Noveler MCP tools, including shared helpers for
#          normalised responses and PathService fallback metadata.
# Context: Imported by individual MCP tool implementations under
#          src/mcp_servers/noveler/tools. Depends on noveler.infrastructure
#          (path service, cache) but performs no I/O at import time.
"""Core data structures and base classes for Noveler MCP tools."""
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from noveler.infrastructure.adapters.path_service_adapter import create_path_service
from noveler.infrastructure.caching.file_cache_service import get_file_cache_service


@dataclass(frozen=True)
class ToolIssue:
    """Describe a single issue detected during tool execution."""

    type: str  # 問題のタイプ（例：typo, long_sentence, etc.）
    severity: str  # 重要度：low, medium, high, critical
    message: str  # 問題の説明
    line_number: int | None = None  # 問題が発生した行番号
    suggestion: str | None = None  # 修正提案
    # 後続修正作業向けの識別子/付加情報（任意）
    end_line_number: int | None = None  # 連続範囲などの終了行
    file_path: str | None = None  # 対象ファイルパス
    line_hash: str | None = None  # 対象行のハッシュ（正規化行のSHA256など）
    block_hash: str | None = None  # 範囲ブロックのハッシュ
    reason_code: str | None = None  # 機械可読な理由コード（例: LINE_WIDTH_OVERFLOW）
    details: dict[str, Any] | None = None  # 測定値・閾値などの詳細
    issue_id: str | None = None  # 安定同定子（ファイルハッシュ/行/タイプに基づく）


@dataclass(frozen=True)
class ToolResponse:
    """Aggregate the result of a tool execution."""

    success: bool
    score: float  # 0-100の品質スコア
    issues: list[ToolIssue]
    execution_time_ms: float
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ToolRequest:
    """Describe the request payload forwarded to an MCP tool."""

    episode_number: int | None = None
    project_name: str | None = None
    additional_params: dict[str, Any] | None = None


class MCPToolBase(ABC):
    """Abstract base class for FastMCP tool implementations."""

    def __init__(self, tool_name: str, tool_description: str) -> None:
        self._tool_name = tool_name
        self._tool_description = tool_description
        self._version = "1.0.0"
        # PathServiceのフォールバックイベントを各ツールで一貫して扱うための共通バッファ
        self._fallback_events: list[dict] = []

    @property
    def tool_name(self) -> str:
        return self._tool_name

    @property
    def tool_description(self) -> str:
        return self._tool_description

    @property
    def version(self) -> str:
        return self._version

    @abstractmethod
    def get_input_schema(self) -> dict[str, Any]:
        """Return the JSON schema describing the tool input."""

    @abstractmethod
    def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute the tool logic and return a :class:`ToolResponse`."""

    def _create_response(
        self,
        success: bool,
        score: float,
        issues: list[ToolIssue],
        start_time: float,
        error_message: str | None = None
    ) -> ToolResponse:
        """Build a :class:`ToolResponse` with common metadata.

        Args:
            success (bool): Whether the tool completed successfully.
            score (float): Score assigned by the tool (0–100 scale).
            issues (list[ToolIssue]): Issues reported by the tool.
            start_time (float): Execution start timestamp (``time.time()``).
            error_message (str | None): Optional error message.

        Returns:
            ToolResponse: Normalised response object.
        """
        execution_time = (time.time() - start_time) * 1000  # ms

        metadata = {
            "tool_name": self._tool_name,
            "tool_version": self._version,
            "check_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        if error_message:
            metadata["error_message"] = error_message

        return ToolResponse(
            success=success,
            score=score,
            issues=issues,
            execution_time_ms=execution_time,
            metadata=metadata
        )

    # ---- PathService fallback helpers (共通ユーティリティ) ----
    def _ps_collect_fallback(self, *services: Any) -> None:
        """Collect fallback events emitted by path service instances."""
        for ps in services:
            try:
                if hasattr(ps, "get_and_clear_fallback_events"):
                    ev = ps.get_and_clear_fallback_events() or []
                    if ev:
                        self._fallback_events.extend(ev)
            except Exception:
                # 収集失敗はツールの挙動に影響させない
                pass

    def _apply_fallback_metadata(self, response: "ToolResponse") -> None:
        """Attach collected fallback events to the response metadata."""
        if getattr(self, "_fallback_events", None):
            response.metadata["path_fallback_used"] = True
            response.metadata["path_fallback_events"] = list(self._fallback_events)
            self._fallback_events.clear()

    def _validate_request(self, request: ToolRequest, *, require_episode_number: bool = True) -> None:
        """Perform basic validation on the tool request."""
        if require_episode_number:
            if request.episode_number is None or request.episode_number <= 0:
                msg = f"Invalid episode number: {request.episode_number}"
                raise ValueError(msg)

    def _get_common_input_schema(self) -> dict[str, Any]:
        """Return the common subset of the JSON input schema."""
        return {
            "type": "object",
            "properties": {
                "episode_number": {
                    "type": "integer",
                    "description": "対象エピソード番号",
                    "minimum": 1
                },
                "project_name": {
                    "type": "string",
                    "description": "プロジェクト名（省略時は環境変数から取得）"
                }
            },
            "required": ["episode_number"]
        }

    def _load_episode_content(self, episode_number: int, project_name: str | None) -> str:
        """Load manuscript content for the requested episode."""
        try:
            # DDD準拠: Infrastructure層のパスサービスとキャッシュサービスを使用
            # プロジェクト指定があれば使用、なければ現在のプロジェクト
            path_service = create_path_service(Path(project_name)) if project_name else create_path_service()

            # 高速化: ファイルキャッシュサービスを活用
            cache_service = get_file_cache_service()
            manuscript_dir = path_service.get_manuscript_dir()

            # キャッシュ最適化されたエピソードファイル取得
            episode_file = cache_service.get_episode_file_cached(manuscript_dir, episode_number)

            if not episode_file or not episode_file.exists():
                msg = f"Episode {episode_number} file not found"
                raise FileNotFoundError(msg)

            try:
                from noveler.infrastructure.caching.file_cache_service import read_text_cached
                return read_text_cached(episode_file)
            except Exception:
                return episode_file.read_text(encoding="utf-8")

        except FileNotFoundError:
            raise
        except Exception as e:
            msg = f"Failed to load episode {episode_number}: {e!s}"
            raise FileNotFoundError(msg) from e
