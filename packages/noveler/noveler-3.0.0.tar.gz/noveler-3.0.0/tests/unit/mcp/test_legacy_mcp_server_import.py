#!/usr/bin/env python3
# File: tests/unit/mcp/test_legacy_mcp_server_import.py
# Purpose: Guard the backwards compatibility layer for the noveler.mcp_server import.
# Context: Legacy integrations still import noveler.mcp_server; regressions here break
#          external automation that has not yet migrated to the new package layout.
"""Unit tests for the noveler.mcp_server compatibility facade."""

from __future__ import annotations

import importlib
import inspect

from mcp_servers.noveler import main as legacy_main


def test_polish_manuscript_apply_alias() -> None:
    """Compatibility module must expose the legacy polish_manuscript_apply symbol."""

    module = importlib.import_module("noveler.mcp_server")

    assert module.polish_manuscript_apply is legacy_main.execute_polish_manuscript_apply
    assert inspect.iscoroutinefunction(module.polish_manuscript_apply)


def test_attribute_delegation_matches_legacy_module() -> None:
    """All other attributes should delegate to the legacy main module."""

    module = importlib.import_module("noveler.mcp_server")

    assert module.execute_polish_manuscript_apply is legacy_main.execute_polish_manuscript_apply
    assert module.server is legacy_main.server
    assert "polish_manuscript_apply" in module.__all__
