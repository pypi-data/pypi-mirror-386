#!/usr/bin/env python3
"""Integration-style smoke tests for the CLI MCP wrapper."""

from __future__ import annotations

import json

import pytest

from noveler.presentation.cli import cli_adapter


class StubClient:
    def __init__(self, responses: list[dict]):
        self.responses = responses
        self.calls: list[tuple[str, dict]] = []

    def _pop(self) -> dict:
        if self.responses:
            return self.responses.pop(0)
        return {"success": True}

    def call_tool(self, name: str, payload: dict) -> dict:
        self.calls.append((name, json.loads(json.dumps(payload))))
        return self._pop()

    async def call_tool_async(self, name: str, payload: dict) -> dict:
        self.calls.append((name, json.loads(json.dumps(payload))))
        return self._pop()


class DummyConsole:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def _store(self, *args, **_kwargs):
        self.messages.append(" ".join(str(a) for a in args))

    print = _store
    print_info = _store
    print_success = _store
    print_warning = _store
    print_error = _store


def _run_cli(args: list[str]) -> int:
    return cli_adapter.run(args)


@pytest.fixture(autouse=True)
def patch_client(monkeypatch):
    stub = StubClient([])
    monkeypatch.setattr(cli_adapter, "_CLIENT", stub, raising=True)
    return stub


@pytest.fixture(autouse=True)
def patch_console(monkeypatch):
    dummy = DummyConsole()
    monkeypatch.setattr(cli_adapter, "get_console", lambda: dummy, raising=False)
    return dummy


def test_quality_check_smoke(patch_client: StubClient, patch_console: DummyConsole):
    patch_client.responses = [{"score": 82.5}]
    exit_code = _run_cli(["check", "1"])
    assert exit_code == 0
    assert any("82.5点" in msg for msg in patch_console.messages)
    name, payload = patch_client.calls[0]
    assert name == "run_quality_checks"
    assert payload["episode_number"] == 1


def test_quality_check_with_autofix(patch_client: StubClient, patch_console: DummyConsole):
    patch_client.responses = [
        {"score": 60},  # initial run
        {"score": 85},  # improve
        {"score": 86},  # rerun
    ]
    exit_code = _run_cli(["check", "2", "--auto-fix"])
    assert exit_code == 0
    assert any("自動改善" in msg for msg in patch_console.messages)
    names = [name for name, _payload in patch_client.calls]
    assert names == ["run_quality_checks", "improve_quality_until", "run_quality_checks"]


def test_write_smoke(patch_client: StubClient, patch_console: DummyConsole):
    patch_client.responses = [{"result": {"success": True}}]
    exit_code = _run_cli(["write", "3", "--dry-run"])
    assert exit_code == 0
    name, payload = patch_client.calls[0]
    assert name == "noveler"
    assert payload["options"]["dry_run"] is True


def test_polish_via_mcp_call(patch_client: StubClient, patch_console: DummyConsole):
    patch_client.responses = [{"success": True}]
    exit_code = _run_cli(["mcp", "call", "polish_manuscript", "{\"episode_number\":1}"])
    assert exit_code == 0
    name, payload = patch_client.calls[0]
    assert name == "polish_manuscript"
    assert payload["episode_number"] == 1


def test_artifacts_list_via_mcp_call(patch_client: StubClient, patch_console: DummyConsole):
    patch_client.responses = [{"artifacts": []}]
    exit_code = _run_cli(["mcp", "call", "list_artifacts", "{\"episode_number\":1}"])
    assert exit_code == 0
    name, payload = patch_client.calls[0]
    assert name == "list_artifacts"
    assert payload["episode_number"] == 1


def test_direct_mcp_call_smoke(patch_client: StubClient, patch_console: DummyConsole):
    patch_client.responses = [{"success": True, "tool": "run_quality_checks"}]
    exit_code = _run_cli(["mcp", "call", "run_quality_checks", "{\"episode_number\":1}"])
    assert exit_code == 0
    assert any("run_quality_checks" in msg for msg in patch_console.messages)
    assert patch_client.calls[0][0] == "run_quality_checks"
