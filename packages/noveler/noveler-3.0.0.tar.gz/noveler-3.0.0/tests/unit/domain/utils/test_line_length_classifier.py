#!/usr/bin/env python3
# File: tests/unit/domain/utils/test_line_length_classifier.py
# Purpose: Verify boundary classification at 80/120 for line length.
# Context: Confirms warn/critical thresholds at edges (直上直下)。

from noveler.domain.utils.line_length_classifier import classify_length


def test_classify_boundaries_default():
    assert classify_length(79) == 'ok'
    assert classify_length(80) == 'warn'
    assert classify_length(81) == 'warn'
    assert classify_length(120) == 'warn'
    assert classify_length(121) == 'critical'
