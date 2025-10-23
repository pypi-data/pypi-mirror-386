# File: tests/unit/domain/services/test_range_adjustment_service.py
# Purpose: Validate range adjustment strategies used during LangGraph quality workflow.
# Context: Ensures SPEC-QUALITY-120 range_adjustment_strategy requirements are met.

from __future__ import annotations

import math

import pytest

from noveler.domain.services.range_adjustment_service import (
    ManualAlignmentRequired,
    RangeAdjustmentResult,
    RangeAdjustmentService,
)


@pytest.fixture()
def service() -> RangeAdjustmentService:
    return RangeAdjustmentService()


def test_exact_match_returns_same_span(service: RangeAdjustmentService) -> None:
    original_document = "この文章は品質チェック用です。"
    current = "冒頭に追記。" + original_document

    result = service.adjust(
        original_text=original_document,
        current_text=current,
        original_start=0,
        original_end=len(original_document),
    )

    expected_start = current.index(original_document)
    expected_end = expected_start + len(original_document)
    assert result.method == "exact_match"
    assert result.start_char == expected_start
    assert result.end_char == expected_end
    assert math.isclose(result.confidence, 1.0)
    assert result.adjustment_attempts[0]["strategy"] == "exact_match"
    assert result.adjustment_attempts[0]["result"] == "success"


def test_diff3_adjusts_offset(service: RangeAdjustmentService) -> None:
    original = "品質チェックでは文脈を重視する。"
    current = "品質チェックでは必ず文脈を重視するべきだ。"
    original_start = 0
    original_end = len(original)

    result = service.adjust(
        original_text=original,
        current_text=current,
        original_start=original_start,
        original_end=original_end,
    )

    assert result.method == "diff3"
    assert result.start_char == 0
    assert result.end_char == len(current)
    assert result.confidence >= 0.75
    diff_attempt = next(a for a in result.adjustment_attempts if a["strategy"] == "diff3")
    assert diff_attempt["result"] == "success"


def test_semantic_search_requires_manual_alignment(service: RangeAdjustmentService) -> None:
    original = "英雄が村を救った"
    current = "旅人は静かに森を抜けた"

    with pytest.raises(ManualAlignmentRequired) as exc_info:
        service.adjust(
            original_text=original,
            current_text=current,
            original_start=0,
            original_end=len(original),
        )

    err = exc_info.value
    assert err.code == "QC-013"
    attempts = err.details.get("attempts")
    assert attempts is not None
    assert attempts[-1]["strategy"] == "semantic_search"
    assert attempts[-1]["result"] == "low_confidence"
