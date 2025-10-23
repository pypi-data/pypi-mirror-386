#!/usr/bin/env python3
# File: tests/unit/domain/services/test_dialogue_detection_service.py
# Purpose: Verify dialogue line detection for Japanese quotes.
# Context: Ensures one-sided brackets and multi-line continuations are handled.

from noveler.domain.services.dialogue_detection_service import detect_dialogue_flags, is_dialogue_line

def test_detect_dialogue_flags_balanced_single_line():
    lines=["「こんにちは」これは挨拶です。", "地の文です"]
    flags=detect_dialogue_flags(lines)
    assert flags == [True, False]

def test_detect_dialogue_flags_unbalanced_multiline():
    lines=["「片側のみで開始", "継続行", "ここで終了」", "地の文"]
    flags=detect_dialogue_flags(lines)
    assert flags == [True, True, True, False]

def test_is_dialogue_line_with_previous_balance():
    prev_open=1
    assert is_dialogue_line("継続行（括弧なし）", prev_open) is True
    assert is_dialogue_line("地の文", 0) is False
