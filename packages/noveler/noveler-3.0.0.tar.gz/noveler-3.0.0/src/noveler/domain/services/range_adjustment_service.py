# File: src/noveler/domain/services/range_adjustment_service.py
# Purpose: Provide range re-mapping utilities for LangGraph quality workflow steps.
# Context: Domain service shared across ProgressiveCheckManager and LangGraph workflow state handling.

"""Range adjustment strategies for progressive quality checks.

Implements SPEC-QUALITY-120 range_adjustment_strategy order:
1. exact_match
2. diff3 (difflib-based approximation)
3. semantic_search (similarity heuristic)
4. manual_confirmation (raises ManualAlignmentRequired)
"""

from __future__ import annotations

import difflib
import math
from dataclasses import dataclass
from typing import Any, Iterable


class ManualAlignmentRequired(RuntimeError):
    """Raised when automatic range re-mapping fails and manual confirmation is required."""

    def __init__(self, message: str, *, attempts: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.code = "QC-013"
        self.details = {"attempts": attempts or []}


@dataclass(slots=True)
class RangeAdjustmentResult:
    """Outcome of a range adjustment attempt."""

    start_char: int
    end_char: int
    method: str
    confidence: float
    adjustment_attempts: list[dict[str, Any]]


class RangeAdjustmentService:
    """Coordinate range re-mapping using multiple fallback strategies."""

    def __init__(self, *, similarity_threshold: float = 0.8) -> None:
        self.similarity_threshold = similarity_threshold

    def adjust(
        self,
        *,
        original_text: str,
        current_text: str,
        original_start: int,
        original_end: int,
    ) -> RangeAdjustmentResult:
        if original_start < 0 or original_end < original_start:
            raise ValueError("Invalid original range")

        original_slice = original_text[original_start:original_end]
        attempts: list[dict[str, Any]] = []

        if not original_slice:
            raise ManualAlignmentRequired("Empty slice cannot be adjusted", attempts=attempts)

        exact = self._try_exact_match(original_slice, current_text)
        attempts.append(exact["attempt"])
        if exact["success"]:
            return RangeAdjustmentResult(
                start_char=exact["start"],
                end_char=exact["end"],
                method="exact_match",
                confidence=1.0,
                adjustment_attempts=attempts,
            )

        diff_result = self._try_diff3(
            original_text=original_text,
            current_text=current_text,
            original_start=original_start,
            original_end=original_end,
        )
        attempts.append(diff_result["attempt"])
        if diff_result["success"]:
            return RangeAdjustmentResult(
                start_char=diff_result["start"],
                end_char=diff_result["end"],
                method="diff3",
                confidence=diff_result["confidence"],
                adjustment_attempts=attempts,
            )

        semantic_result = self._try_semantic_search(original_slice, current_text)
        attempts.append(semantic_result["attempt"])
        if semantic_result["success"] and semantic_result["confidence"] >= self.similarity_threshold:
            return RangeAdjustmentResult(
                start_char=semantic_result["start"],
                end_char=semantic_result["end"],
                method="semantic_search",
                confidence=semantic_result["confidence"],
                adjustment_attempts=attempts,
            )

        attempts[-1]["result"] = "low_confidence"
        raise ManualAlignmentRequired("Manual alignment required", attempts=attempts)

    def _try_exact_match(self, slice_text: str, current_text: str) -> dict[str, Any]:
        index = current_text.find(slice_text)
        if index != -1:
            return {
                "success": True,
                "start": index,
                "end": index + len(slice_text),
                "attempt": {
                    "strategy": "exact_match",
                    "result": "success",
                    "confidence": 1.0,
                },
            }
        return {
            "success": False,
            "attempt": {
                "strategy": "exact_match",
                "result": "not_found",
                "confidence": 0.0,
            },
        }

    def _try_diff3(
        self,
        *,
        original_text: str,
        current_text: str,
        original_start: int,
        original_end: int,
    ) -> dict[str, Any]:
        matcher = difflib.SequenceMatcher(None, original_text, current_text, autojunk=False)
        # Map original indices to current positions.
        current_start, current_end = self._map_range_via_opcodes(
            matcher.get_opcodes(),
            original_start,
            original_end,
            current_text_length=len(current_text),
        )
        if current_start is not None and current_end is not None:
            overlap_ratio = matcher.ratio()
            if overlap_ratio < 0.6:
                return {
                    "success": False,
                    "attempt": {
                        "strategy": "diff3",
                        "result": "low_overlap",
                        "confidence": overlap_ratio,
                    },
                }
            confidence = max(0.75, overlap_ratio)
            return {
                "success": True,
                "start": current_start,
                "end": current_end,
                "confidence": confidence,
                "attempt": {
                    "strategy": "diff3",
                    "result": "success",
                    "confidence": confidence,
                },
            }
        return {
            "success": False,
            "attempt": {
                "strategy": "diff3",
                "result": "unmapped",
                "confidence": 0.0,
            },
        }

    def _map_range_via_opcodes(
        self,
        opcodes: Iterable[tuple[str, int, int, int, int]],
        original_start: int,
        original_end: int,
        *,
        current_text_length: int,
    ) -> tuple[int | None, int | None]:
        covered_ranges: list[tuple[int, int]] = []
        inside_original = False
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "insert" and inside_original:
                covered_ranges.append((j1, j2))
                continue
            if i2 <= original_start:
                continue
            if i1 >= original_end:
                if tag == "insert" and covered_ranges:
                    covered_ranges.append((j1, j2))
                break
            inside_original = True
            span_start = max(original_start, i1)
            span_end = min(original_end, i2)
            offset_start = span_start - i1
            offset_end = span_end - i1
            mapped_start = j1 + max(0, offset_start)
            mapped_end = j1 + max(0, offset_end)
            covered_ranges.append((mapped_start, mapped_end))
        if not covered_ranges:
            return None, None
        start = max(0, min(s for s, _ in covered_ranges))
        end = min(current_text_length, max(e for _, e in covered_ranges))
        if start >= end:
            return None, None
        return start, end

    def _try_semantic_search(self, slice_text: str, current_text: str) -> dict[str, Any]:
        slice_len = len(slice_text)
        if slice_len == 0:
            return {
                "success": False,
                "attempt": {
                    "strategy": "semantic_search",
                    "result": "empty_slice",
                    "confidence": 0.0,
                },
            }
        best_confidence = 0.0
        best_start = None
        best_end = None
        step = max(1, slice_len // 5)
        for start in range(0, max(1, len(current_text) - slice_len + 1), step):
            candidate = current_text[start : start + slice_len]
            ratio = difflib.SequenceMatcher(None, slice_text, candidate, autojunk=False).ratio()
            if ratio > best_confidence:
                best_confidence = ratio
                best_start = start
                best_end = start + slice_len
                if best_confidence >= 0.999:
                    break
        success = best_start is not None
        return {
            "success": success,
            "start": best_start if success else None,
            "end": best_end if success else None,
            "confidence": best_confidence,
            "attempt": {
                "strategy": "semantic_search",
                "result": "success" if success else "not_found",
                "confidence": best_confidence,
            },
        }
