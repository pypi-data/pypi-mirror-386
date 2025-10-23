#!/usr/bin/env python3
"""Top-level pytest configuration."""

from __future__ import annotations
import os
import pytest
from pathlib import Path

from noveler.infrastructure.logging.unified_logger import get_logger as _get_unified_logger

def pytest_ignore_collect(collection_path=None, path=None, config=None) -> bool:
    """Tell pytest to ignore certain directories during collection."""
    p_obj = collection_path or path
    if p_obj is None:
        return False
    p = str(p_obj)
    blocked = (
        "/archive/" in p or "\\archive\\" in p or
        "/backups/" in p or "\\backups\\" in p
    )
    return bool(blocked)

def pytest_runtest_setup(item: pytest.Item) -> None:
    """Conditionally skip SPEC-gated tests."""
    try:
        if (
            "test_spec_901_async_mcp_integration.py" in str(item.fspath)
            and os.environ.get("ENABLE_SPEC_901_TESTS", "0") not in {"1", "true", "TRUE"}
        ):
            pytest.skip("SPEC-901 tests are gated by ENABLE_SPEC_901_TESTS=1")

        for mark in item.iter_markers(name="spec"):
            args = getattr(mark, "args", ())
            if not args:
                continue
            spec_name = args[0]
            if (
                isinstance(spec_name, str)
                and spec_name.strip().upper() == "SPEC-901-DDD-REFACTORING"
                and os.environ.get("ENABLE_SPEC_901_TESTS", "0") not in {"1", "true", "TRUE"}
            ):
                pytest.skip("SPEC-901 tests are gated by ENABLE_SPEC_901_TESTS=1")
    except Exception:
        return None


def pytest_sessionstart(session: pytest.Session) -> None:
    """Initialise the unified logger early so pytest env overrides apply."""

    try:
        _get_unified_logger(__name__)
    except Exception:
        return None


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register project-level CLI flags."""
    parser.addoption(
        "--llm-report",
        action="store_true",
        default=False,
        help="Enable LLM-oriented test reporting output.",
    )
