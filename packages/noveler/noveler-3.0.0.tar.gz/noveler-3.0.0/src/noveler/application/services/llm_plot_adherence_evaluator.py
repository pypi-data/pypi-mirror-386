#!/usr/bin/env python3
"""LLM-powered evaluator for assessing plot adherence (B20 compliant).

Invoked by ``ValidatePlotAdherenceUseCase`` to run a ``UniversalLLMUseCase``
and return JSON metadata describing adherence to A31 plot viewpoints.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from noveler.application.use_cases.universal_llm_use_case import UniversalLLMUseCase
from noveler.domain.value_objects.universal_prompt_execution import (
    ProjectContext,
    PromptType,
    UniversalPromptRequest,
)
from noveler.infrastructure.integrations.universal_claude_code_service import UniversalClaudeCodeService


@dataclass
class LLMAdherenceConfig:
    """Configuration values controlling evaluation mode and sampling temperature."""

    mode: str = "gated"  # fast/gated/strict（ここでは使用しないが将来拡張に備え保持）
    temperature: float = 0.1


class LLMPlotAdherenceEvaluator:
    """Facade that orchestrates LLM-based plot adherence evaluation."""

    def __init__(self, config: LLMAdherenceConfig | None = None) -> None:
        self._config = config or LLMAdherenceConfig()
        self._use_case = UniversalLLMUseCase(UniversalClaudeCodeService())

    async def evaluate(
        self,
        episode_number: int,
        manuscript_content: str,
        project_root: Path,
        project_name: str,
    ) -> dict[str, Any]:
        """Evaluate a manuscript and return adherence metrics.

        Args:
            episode_number: Episode identifier to inject into the request.
            manuscript_content: Text that should be assessed for plot adherence.
            project_root: Root directory of the project for context.
            project_name: Human-readable project name for logging/context.

        Returns:
            dict[str, Any]: Parsed JSON payload with scores and evidence.
        """
        prompt = self._build_prompt(manuscript_content)
        project_context = ProjectContext(project_name=project_name, project_root=project_root)

        req = UniversalPromptRequest(
            prompt_type=PromptType.QUALITY_CHECK,
            prompt_content=prompt,
            project_context=project_context,
            output_format="json",
            max_turns=1,
            type_specific_config={
                "episode_number": episode_number,
                "task_name": "plot_adherence_check",
                "temperature": self._config.temperature,
            },
        )

        resp = await self._use_case.execute_with_fallback(req, fallback_enabled=True)

        data: dict[str, Any] = {}
        # 1) extracted_data 優先
        if getattr(resp, "extracted_data", None):
            data = dict(resp.extracted_data)
        # 2) response_content のJSONパース
        if not data:
            try:
                data = json.loads(getattr(resp, "response_content", "") or "")
            except Exception:
                data = {}

        # 標準キーを整える（欠落時は既定値）
        # scores_by_element はオプショナル（未対応モデルもあるため）
        raw_scores_by_element = data.get("scores_by_element") or {}
        scores_by_element: dict[str, float] = {}
        if isinstance(raw_scores_by_element, dict):
            for k, v in raw_scores_by_element.items():
                fv = _coerce_float(v, default=None)
                if fv is not None:
                    scores_by_element[str(k)] = fv

        return {
            "score": _coerce_float(data.get("score"), default=None),
            "scores_by_element": scores_by_element,
            "missing_elements": data.get("missing_elements") or [],
            "evidence": data.get("evidence") or [],
            "suggestions": data.get("suggestions") or [],
            "notes": data.get("notes") or "",
        }

    def _build_prompt(self, manuscript: str) -> str:
        """Construct the evaluation prompt supplied to the LLM."""
        return f"""
あなたは熟練編集者です。以下の本文のプロット準拠（A31代表観点）を評価してください。
- 代表観点: 重要イベント・キャラクター成長・世界観・伏線
- 提供テキストの範囲のみを根拠に判断すること
- 出力は必ずJSONオブジェクトのみ
- 欠落要素があれば missing_elements に日本語で列挙
- 見つけた要素の根拠は evidence 配列で必ず提示（要素名 element, 引用 quote, 文字位置 start/end）
- score は 0–100 の数値
 - さらに scores_by_element を出力し、各代表観点ごとのスコア（0–100）を提示すること

本文:
---
{manuscript}
---

出力JSONスキーマ:
{{
  "score": number,
  "scores_by_element": {{"重要イベント": number, "キャラクター成長": number, "世界観": number, "伏線": number}},
  "missing_elements": string[],
  "evidence": [{{"element": string, "quote": string, "start": number, "end": number}}],
  "suggestions": string[],
  "notes": string
}}
"""


def _coerce_float(val: object, default: float | None = None) -> float | None:
    try:
        if val is None:
            return default
        return float(val)
    except Exception:
        return default
