"""Infrastructure.llm.llm_io_logger
Where: Infrastructure module logging LLM input/output interactions.
What: Provides utilities to capture and persist prompts, responses, and metadata.
Why: Supports traceability and debugging for LLM-based workflows.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""LLM I/O ロガー（B20準拠: Imperative Shell でファイルI/O集約）

目的:
- LLMへのリクエストとレスポンスを .noveler に保存し、トレーサビリティを確保
- 命名規則: `/noveler write` 相当は EP{episode:04d}_{yyyyMMddHHMMSS}.json（stepなし）
- それ以外は LLM_{type}_{yyyyMMddHHMMSS}.json に保存
"""

import json
import os
import random
from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.universal_prompt_execution import (
    PromptType,
    UniversalPromptRequest,
    UniversalPromptResponse,
)
from noveler.infrastructure.factories.path_service_factory import create_path_service
from noveler.domain.value_objects.project_time import project_now

if TYPE_CHECKING:
    from pathlib import Path


class LLMIOLogger:
    """LLM I/O保存ロガー"""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root
        self._path_service = create_path_service(project_root)

    # ===== 内部ユーティリティ（環境制御・整形） =====
    def _now_second(self) -> str:
        # JSTベースの現在時刻（プロジェクト標準）
        return project_now().datetime.strftime("%Y%m%d%H%M%S")

    def _is_enabled(self) -> bool:
        val = os.getenv("NOVELER_LLM_IO_LOGGING", "1").strip().lower()
        return val not in ("0", "false", "off", "no")

    def _sampling(self) -> float:
        try:
            return max(0.0, min(1.0, float(os.getenv("NOVELER_LLM_IO_SAMPLING", "1.0"))))
        except Exception:
            return 1.0

    def _maxlen(self) -> int | None:
        val = os.getenv("NOVELER_LLM_IO_MAXLEN", "").strip()
        if not val:
            return None
        try:
            n = int(val)
            return n if n > 0 else None
        except Exception:
            return None

    def _redact(self, text: str) -> str:
        patterns = os.getenv("NOVELER_LLM_IO_REDACT", "").strip()
        if not patterns:
            return text
        redacted = text
        for token in [p for p in patterns.split(",") if p.strip()]:
            try:
                redacted = redacted.replace(token, "[REDACTED]")
            except Exception:
                continue
        return redacted

    def _maybe_truncate(self, text: str) -> str:
        limit = self._maxlen()
        if limit is None:
            return text
        if len(text) <= limit:
            return text
        return text[:limit] + "..."  # indicate truncation

    def _ensure_unique(self, path: Path) -> Path:
        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        idx = 2
        while True:
            candidate = parent / f"{stem}_{idx}{suffix}"
            if not candidate.exists():
                return candidate
            idx += 1

    # ===== 既存: 汎用ユースケースI/O保存 =====
    def _get_output_path(self, request: UniversalPromptRequest) -> Path:
        ts = self._now_second()
        # episode推定（type_specific_configにあれば使用）
        episode = None
        try:
            episode = int(request.type_specific_config.get("episode_number")) if request.type_specific_config else None
        except Exception:
            episode = None

        # writing + episode指定あり → EP{04d}_{yyyyMMddHHMMSS}.json
        if request.prompt_type == PromptType.WRITING and episode:
            try:
                return self._path_service.get_write_command_file_path(episode, ts)
            except Exception:
                # フォールバック
                return (self._path_service.get_noveler_output_dir() / "writes" / f"EP{episode:04d}_{ts}.json")

        # それ以外は汎用名
        name = f"LLM_{request.prompt_type.value}_{ts}.json"
        # 非writing系は checks へ、writing系は writes へ
        base_dir = "writes" if request.prompt_type == PromptType.WRITING else "checks"
        return self._path_service.get_noveler_output_dir() / base_dir / name

    def save_request_response(self, request: UniversalPromptRequest, response: UniversalPromptResponse) -> Path:
        """リクエスト・レスポンスを1ファイルに保存"""
        # 環境制御（無効・サンプリング）
        if not self._is_enabled():
            return self._path_service.get_noveler_output_dir() / "checks" / "logging_disabled.json"
        if random.random() > self._sampling():
            return self._path_service.get_noveler_output_dir() / "checks" / "logging_sampled_out.json"

        output_path = self._ensure_unique(self._get_output_path(request))
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 追加情報の抽出
        context_files = []
        try:
            context_files = [str(p) for p in (request.get_context_files() or [])]
        except Exception:
            context_files = []

        # 敏感情報のマスキングと長さ制御
        prompt_content = self._maybe_truncate(self._redact(request.prompt_content))
        response_content = self._maybe_truncate(self._redact(getattr(response, "response_content", "")))

        data: dict[str, Any] = {
            "kind": "universal_prompt",
            "prompt_type": request.prompt_type.value,
            "timestamp": project_now().datetime.isoformat(),
            "request": {
                "project_root": str(request.project_context.project_root),
                "project_name": request.project_context.project_name,
                "prompt_content": prompt_content,
                "type_specific_config": request.type_specific_config or {},
                "max_turns": request.max_turns,
                "output_format": request.output_format,
                "context_files": context_files,
            },
            "response": {
                "success": response.success,
                "execution_time_ms": getattr(response, "execution_time_ms", None),
                "error_message": getattr(response, "error_message", None),
                "response_content": response_content,
                "extracted_data": getattr(response, "extracted_data", {}),
                "metadata": getattr(response, "metadata", {}),
            },
        }

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return output_path

    # ===== 追加: /noveler write 各ステージ向けI/O保存 =====
    def save_stage_io(
        self,
        episode_number: int,
        step_number: int,
        stage_name: str,
        request_content: str | dict[str, Any],
        response_content: str | dict[str, Any],
        extra_metadata: dict[str, Any] | None = None,
    ) -> Path:
        """/noveler write ステージ用のI/O保存

        命名: EP{episode:04d}_step{step:02d}_{yyyyMMddHHMMSS}.json
        """
        # 環境制御（無効・サンプリング）
        if not self._is_enabled():
            return self._path_service.get_noveler_output_dir() / "logging_disabled.json"
        if random.random() > self._sampling():
            return self._path_service.get_noveler_output_dir() / "logging_sampled_out.json"

        ts = self._now_second()
        # write系ステージ名かどうかで保存先を分ける
        stage_lower = (stage_name or "").lower()
        is_write_stage = ("write" in stage_lower)
        try:
            if is_write_stage:
                path = self._path_service.get_write_step_output_file_path(episode_number, step_number, ts)
            else:
                path = self._path_service.get_step_output_file_path(episode_number, step_number, ts)
        except Exception:
            # フォールバック
            sub = "writes" if is_write_stage else "checks"
            path = (
                self._path_service.get_noveler_output_dir()
                / sub
                / f"EP{episode_number:04d}_step{step_number:02d}_{ts}.json"
            )

        path = self._ensure_unique(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # 文字列化と整形（マスク・長さ制限）
        def to_text(obj: str | dict[str, Any]) -> str:
            if isinstance(obj, str):
                return obj
            try:
                return json.dumps(obj, ensure_ascii=False)
            except Exception:
                return str(obj)

        req_text = self._maybe_truncate(self._redact(to_text(request_content)))
        res_text = self._maybe_truncate(self._redact(to_text(response_content)))

        payload = {
            "kind": "ten_stage_step_io",
            "episode_number": episode_number,
            "step_number": step_number,
            "stage_name": stage_name,
            "timestamp": project_now().datetime.isoformat(),
            "request": {"content": req_text},
            "response": {"content": res_text},
            "metadata": extra_metadata or {},
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return path
