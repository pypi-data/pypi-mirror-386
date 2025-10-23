#!/usr/bin/env python3
"""Unit tests for CLI ↔ MCP bridge."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from noveler.presentation.cli import cli_adapter


class DummyClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def _next(self):
        if not self.responses:
            return {"success": True}
        return self.responses.pop(0)

    def call_tool(self, name, payload):
        self.calls.append((name, json.loads(json.dumps(payload))))
        return self._next()

    async def call_tool_async(self, name, payload):
        self.calls.append((name, json.loads(json.dumps(payload))))
        return self._next()


@pytest.fixture(autouse=True)
def patch_client(monkeypatch):
    dummy = DummyClient([])
    monkeypatch.setattr(cli_adapter, "_CLIENT", dummy)
    return dummy


def test_help_includes_mapping(monkeypatch, capsys):
    monkeypatch.setattr(cli_adapter, "iter_mappings", lambda: [SimpleNamespace(cli_command="noveler foo", mcp_tool="bar", description="baz")])
    help_text = cli_adapter._render_help()
    assert "noveler foo" in help_text
    assert "bar" in help_text


def test_mcp_call_invokes_client(patch_client):
    patch_client.responses = [{"success": True}]
    exit_code = cli_adapter.run(["mcp", "call", "run_quality_checks", "{}"])
    assert exit_code == 0
    assert patch_client.calls == [("run_quality_checks", {})]


def test_check_with_auto_fix(patch_client):
    patch_client.responses = [
        {"score": 60},
        {"score": 85},
        {"score": 85},
    ]
    exit_code = cli_adapter.run(["check", "1", "--auto-fix"])
    assert exit_code == 0
    called_tools = [name for name, _ in patch_client.calls]
    assert called_tools == ["run_quality_checks", "improve_quality_until", "run_quality_checks"]


def test_write_delegates_to_noveler_tool(patch_client):
    patch_client.responses = [{"result": {"success": True}}]
    exit_code = cli_adapter.run(["write", "2", "--dry-run"])
    assert exit_code == 0
    assert patch_client.calls[0][0] == "noveler"
