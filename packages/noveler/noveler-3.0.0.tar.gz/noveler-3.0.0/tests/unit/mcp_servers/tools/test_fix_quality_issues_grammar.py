# File: tests/unit/mcp_servers/tools/test_fix_quality_issues_grammar.py
# Purpose: Validate grammar punctuation auto fixes handled by FixQualityIssuesTool.
# Context: Ensures GRAMMAR_PUNCTUATION adjustments remain safe without Janome or dialogue regressions.

"""Unit tests for GRAMMAR_PUNCTUATION auto-fix behaviour in FixQualityIssuesTool."""

from __future__ import annotations

import pytest

from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolIssue
from mcp_servers.noveler.tools import fix_quality_issues_tool as tool_mod
from mcp_servers.noveler.tools.fix_quality_issues_tool import FixQualityIssuesTool


def _apply_grammar_fix(
    lines: list[str],
    issues: list[ToolIssue],
    *,
    max_sentence_length: int = 45,
    short_sentence_length: int = 10,
    max_commas_per_sentence: int = 3,
    enable_sentence_split: bool = True,
    enable_sentence_merge: bool = True,
    max_merges_per_line: int = 2,
    max_splits_per_line: int = 2,
    skip_dialogue_lines: bool = True,
    cfg: dict | None = None,
) -> tool_mod.FixResult:
    """Helper to invoke the internal fixer without running the full pipeline."""

    tool = FixQualityIssuesTool()
    cfg = cfg if cfg is not None else {"stage1": {"indent": {"enable": False}}}
    return tool._apply_fixes(  # noqa: SLF001 - direct access for focused unit tests
        list(lines),
        issues,
        max_sentence_length=max_sentence_length,
        short_sentence_length=short_sentence_length,
        max_commas_per_sentence=max_commas_per_sentence,
        enable_sentence_split=enable_sentence_split,
        enable_sentence_merge=enable_sentence_merge,
        max_merges_per_line=max_merges_per_line,
        max_splits_per_line=max_splits_per_line,
        skip_dialogue_lines=skip_dialogue_lines,
        cfg=cfg,
    )


def test_fix_quality_issues_removes_duplicate_punctuation() -> None:
    """Grammar auto fix should condense duplicate punctuation into a single mark."""

    line = "これはテストです。。。。"
    issue = ToolIssue(
        type="grammar",
        severity="medium",
        message="duplicate punctuation",
        line_number=1,
        reason_code="GRAMMAR_PUNCTUATION",
    )

    result = _apply_grammar_fix([line], [issue])
    sanitized_lines = [entry.strip() for entry in result.fixed_text.splitlines() if entry.strip()]

    assert sanitized_lines[0] == "これはテストです。"
    assert result.applied >= 1


def test_fix_quality_issues_splits_long_sentence_without_punctuation() -> None:
    """Grammar auto fix should insert safe punctuation for very long sentences."""

    long_line = (
        "これは句読点がなくて読みづらい文章が延々と続きますそして読者は少し疲れてしまいます"
        "もしこの文章に適切な句読点があればもっと読みやすくなります"
    )
    issue = ToolIssue(
        type="grammar",
        severity="medium",
        message="long sentence without punctuation",
        line_number=1,
        reason_code="GRAMMAR_PUNCTUATION",
    )

    result = _apply_grammar_fix([long_line], [issue])
    sanitized_lines = [entry.strip() for entry in result.fixed_text.splitlines() if entry.strip()]

    assert sanitized_lines[0] != long_line
    assert "ます。そして" in sanitized_lines[0]
    assert result.applied >= 1


def test_fix_quality_issues_fallback_split_inserts_punctuation(monkeypatch: pytest.MonkeyPatch) -> None:
    """When morphology is unavailable, fallback heuristics should still insert punctuation."""

    monkeypatch.setattr(tool_mod, "_MORPH_AVAILABLE", False, raising=False)
    monkeypatch.setattr(tool_mod, "_create_analyzer", lambda: None, raising=False)

    long_line = (
        "これは句読点がなくて読みづらい文章が延々と続きますそして読者は少し疲れてしまいます"
        "もしこの文章に適切な句読点があればもっと読みやすくなります"
    )
    issue = ToolIssue(
        type="grammar",
        severity="medium",
        message="long sentence without punctuation",
        line_number=1,
        reason_code="GRAMMAR_PUNCTUATION",
    )

    result = _apply_grammar_fix([long_line], [issue])
    sanitized_lines = [entry.strip() for entry in result.fixed_text.splitlines() if entry.strip()]

    assert "。" in sanitized_lines[0]
    assert "文章に。適切" not in sanitized_lines[0]
    assert result.applied >= 1


def test_fix_quality_issues_respects_dialogue_skip() -> None:
    """Grammar auto fix must not touch dialogue lines even if punctuation repeats."""

    dialogue_line = "「感嘆している。。。。」"
    issue = ToolIssue(
        type="grammar",
        severity="medium",
        message="duplicate punctuation",
        line_number=1,
        reason_code="GRAMMAR_PUNCTUATION",
    )

    result = _apply_grammar_fix([dialogue_line], [issue])
    sanitized_lines = [entry.strip() for entry in result.fixed_text.splitlines() if entry.strip()]

    assert sanitized_lines[0].count("。") == dialogue_line.count("。")
    assert result.applied == 0


def test_fix_quality_issues_leaves_short_sentence_unchanged() -> None:
    """Lines without reported issues must remain untouched to avoid false positives."""

    short_line = "見出し用テキスト"
    result = _apply_grammar_fix([short_line], [])
    sanitized_lines = [entry.strip() for entry in result.fixed_text.splitlines() if entry.strip()]

    assert sanitized_lines[0] == short_line
    assert result.applied == 0
