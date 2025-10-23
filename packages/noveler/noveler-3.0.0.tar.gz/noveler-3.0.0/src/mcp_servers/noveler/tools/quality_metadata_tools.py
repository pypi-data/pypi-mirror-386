"""品質メタデータ系ツール

list_quality_presets / get_quality_schema を提供
"""
from __future__ import annotations

from typing import Any

from mcp_servers.noveler.domain.entities.mcp_tool_base import (
    MCPToolBase,
    ToolIssue,
    ToolRequest,
    ToolResponse,
)


_NAROU_THRESHOLDS = {
    "preset": "narou",
    "long_sentence_length": 45,
    "long_run_threshold": 3,
    "short_sentence_length": 10,
    "short_run_threshold": 5,
    "dialogue_ratio_min": 0.4,
    "dialogue_ratio_max": 0.75,
    "comma_avg_min": 0.6,
    "comma_avg_max": 1.6,
    "comma_per_sentence_max": 3,
    "ending_repeat_threshold": 4,
}


class ListQualityPresetsTool(MCPToolBase):
    def __init__(self) -> None:
        super().__init__(
            tool_name="list_quality_presets",
            tool_description="品質プリセット一覧を返す",
        )

    def get_input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, request: ToolRequest) -> ToolResponse:
        import time

        presets = {
            "narou": _NAROU_THRESHOLDS,
        }
        issues = [
            ToolIssue(
                type="quality_presets",
                severity="low",
                message="プリセット一覧",
                details=presets,
            )
        ]
        return self._create_response(True, 100.0, issues, time.time())


class GetQualitySchemaTool(MCPToolBase):
    def __init__(self) -> None:
        super().__init__(
            tool_name="get_quality_schema",
            tool_description="品質チェックのスキーマ（aspects/reason_codes）",
        )

    def get_input_schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, request: ToolRequest) -> ToolResponse:
        import time

        aspects = [
            "long_short_runs",
            "dialogue_ratio",
            "ending_repetition",
            "punctuation_style",
            "comma_density",
            "readability",
            "grammar",
            "style",
        ]
        reason_codes = [
            # rhythm
            "CONSECUTIVE_LONG_SENTENCES",
            "CONSECUTIVE_SHORT_SENTENCES",
            "DIALOGUE_RATIO_OUT_OF_RANGE",
            "ENDING_REPETITION",
            "ELLIPSIS_STYLE",
            "ELLIPSIS_ODD_COUNT",
            "DASH_STYLE",
            "COMMA_AVG_OUT_OF_RANGE",
            "COMMA_OVERUSE",
            # readability
            "LONG_SENTENCE",
            "COMPLEX_VOCABULARY",
            "HIGH_AVG_SENTENCE_LENGTH",
            # grammar
            "TYPO",
            "PARTICLE_ERROR",
            "NOTATION_INCONSISTENCY",
            "GRAMMAR_PUNCTUATION",
            # style
            "TRAILING_SPACES",
            "DOUBLE_SPACES",
            "TAB_FOUND",
            "FULLWIDTH_SPACE",
            "EMPTY_LINE_RUNS",
            "BRACKETS_MISMATCH",
        ]
        payload = {"aspects": aspects, "reason_codes": reason_codes}
        issues = [
            ToolIssue(
                type="quality_schema",
                severity="low",
                message="品質スキーマ",
                details=payload,
            )
        ]
        return self._create_response(True, 100.0, issues, time.time())
