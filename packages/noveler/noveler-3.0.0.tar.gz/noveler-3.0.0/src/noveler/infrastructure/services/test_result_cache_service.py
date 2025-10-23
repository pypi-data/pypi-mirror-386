# File: src/noveler/infrastructure/services/test_result_cache_service.py
# Purpose: Persist and retrieve cached MCP test-result analysis payloads so
#          delta analysis can operate without explicit caller-provided history.
# Context: Used by ResultAnalysisTool to store the most recent pytest JSON
#          artefacts under the project management directory while enforcing
#          lightweight retention and basic size monitoring.

"""Test result cache service for MCP analysis tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from noveler.domain.interfaces.i_path_service import IPathService
from noveler.infrastructure.logging.unified_logger import get_logger


class TestResultCacheService:
    """Provide persistence for recent test result analysis payloads."""

    _CACHE_DIR_NAME = "tool_cache/test_result_analysis"
    _CACHE_FILE_NAME = "latest.json"
    _MAX_HISTORY = 5

    def __init__(self, path_service: IPathService) -> None:
        self._path_service = path_service
        self._logger = get_logger(__name__)

    def load_latest(self) -> dict[str, Any] | None:
        """Return the latest cached payload if present."""

        cache_file = self._resolve_cache_dir() / self._CACHE_FILE_NAME
        try:
            if not cache_file.exists():
                return None
            with cache_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
                return payload if isinstance(payload, dict) else None
        except (json.JSONDecodeError, OSError) as exc:  # pragma: no cover - defensive guard
            self._logger.warning("テスト結果キャッシュの読み込みに失敗: %s", exc)
            return None

    def store_latest(self, payload: dict[str, Any], *, max_history: int | None = None) -> None:
        """Persist the provided payload and maintain light history."""

        cache_dir = self._resolve_cache_dir()
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / self._CACHE_FILE_NAME

        try:
            serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            cache_file.write_text(serialized, encoding="utf-8")
            self._logger.debug("テスト結果キャッシュを更新: %s", cache_file)
            history_limit = max_history if max_history is not None else self._MAX_HISTORY
            self._rotate_history(cache_dir, serialized, history_limit)
        except OSError as exc:  # pragma: no cover - ファイル書き込み失敗は警告のみ
            self._logger.warning("テスト結果キャッシュの書き込みに失敗: %s", exc)
            return

        size_kb = cache_file.stat().st_size / 1024
        if size_kb > 1024:  # 1MB超は通知
            self._logger.warning(
                "テスト結果キャッシュが大きすぎます (%.1f KB)。保存内容を間引くことを検討してください。",
                size_kb,
            )

    def _rotate_history(self, cache_dir: Path, serialized: str, max_history: int) -> None:
        """Append a timestamped snapshot and prune old entries."""

        import time

        snapshot_path = cache_dir / f"history_{time.time_ns()}.json"
        try:
            snapshot_path.write_text(serialized, encoding="utf-8")
        except OSError:
            return  # 履歴保存に失敗しても致命的ではない

        history_files = sorted(cache_dir.glob("history_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
        for old_file in history_files[max_history:]:
            try:
                old_file.unlink(missing_ok=True)
            except OSError:
                continue

    def _resolve_cache_dir(self) -> Path:
        management_dir = self._path_service.get_management_dir()
        return management_dir / self._CACHE_DIR_NAME
