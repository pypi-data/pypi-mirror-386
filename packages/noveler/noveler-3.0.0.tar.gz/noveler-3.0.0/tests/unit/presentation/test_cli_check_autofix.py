"""CLI adapter: noveler check --auto-fix should use improve_quality_until.
"""
from __future__ import annotations

import types
from typing import Any

from noveler.presentation.cli import cli_adapter


class DummyConsole:
    def print(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        # no-op
        pass


async def _async_return(data: dict[str, Any]) -> dict[str, Any]:
    return data


def test_cli_check_uses_improve_quality_until(monkeypatch):
    # Patch console
    monkeypatch.setattr(cli_adapter, "get_console", lambda: DummyConsole())

    # Patch mcp main functions
    from mcp_servers.noveler import main as mcp_mod

    async def fake_check(args: dict[str, Any]) -> dict[str, Any]:
        return {"success": True, "score": 60.0}

    async def fake_improve(args: dict[str, Any]) -> dict[str, Any]:
        # Ensure target/max_iterations are passed through
        ap = args.get("additional_params") or {}
        assert ap.get("target_score") == 80
        assert ap.get("max_iterations") == 3
        return {"success": True, "score": 82.0, "metadata": {"target_score": 80}}

    monkeypatch.setattr(mcp_mod, "execute_run_quality_checks", fake_check)
    monkeypatch.setattr(mcp_mod, "execute_improve_quality_until", fake_improve)

    # Execute CLI
    rc = cli_adapter.run(["check", "1", "--auto-fix"])
    assert rc == 0  # score >= 80 after improvements

