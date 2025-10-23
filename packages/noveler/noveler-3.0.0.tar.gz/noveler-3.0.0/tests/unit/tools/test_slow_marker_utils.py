# File: tests/unit/tools/test_slow_marker_utils.py
# Purpose: Validate helper utilities that normalise test names for slow markers.
# Context: Ensures pytest collection hooks rely on predictable tokenisation.
"""Unit tests for the slow marker helper functions."""

from tests._utils.slow_marker_utils import extract_slow_marker_tokens


def test_extract_tokens_splits_underscores() -> None:
    """アンダースコア区切りのテスト名を分割できること"""
    tokens = extract_slow_marker_tokens("test_performance_metrics")
    assert {"test", "performance", "metrics"}.issubset(tokens)
    assert "test_performance_metrics" in tokens


def test_extract_tokens_handles_mixed_separators() -> None:
    """ハイフンやスペースを含むテスト名でもトークン化できること"""
    tokens = extract_slow_marker_tokens("test-heavy benchmark case")
    assert {"test", "heavy", "benchmark", "case"}.issubset(tokens)


def test_extract_tokens_returns_empty_set_for_blank_input() -> None:
    """空文字入力では空集合を返すこと"""
    assert extract_slow_marker_tokens("") == set()
