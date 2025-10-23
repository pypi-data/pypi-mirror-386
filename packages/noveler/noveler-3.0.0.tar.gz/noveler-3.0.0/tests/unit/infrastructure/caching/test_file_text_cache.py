#!/usr/bin/env python3
# File: tests/unit/infrastructure/caching/test_file_text_cache.py
# Purpose: Verify the behaviour of the lightweight file text cache (read_text_cached).
# Context: Ensures cached reads return quickly and invalidate on file changes.

from __future__ import annotations

import time
from pathlib import Path

from noveler.infrastructure.caching.file_cache_service import read_text_cached, invalidate_text_cache


def test_read_text_cached_returns_content_and_updates_on_change(tmp_path: Path) -> None:
    target = tmp_path / "sample.txt"
    target.write_text("alpha", encoding="utf-8")

    # First read populates cache
    c1 = read_text_cached(target)
    assert c1 == "alpha"

    # Second read hits cache (content identical)
    c2 = read_text_cached(target)
    assert c2 == "alpha"

    # Modify file (ensure mtime_ns changes)
    time.sleep(0.001)  # ns precision guard on some FS
    target.write_text("beta", encoding="utf-8")

    c3 = read_text_cached(target)
    assert c3 == "beta"

    # Invalidate specific path and ensure fresh read still returns current content
    invalidate_text_cache(target)
    c4 = read_text_cached(target)
    assert c4 == "beta"
