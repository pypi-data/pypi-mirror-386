"""Tests.tests.unit.presentation.cli.test_cli_adapter
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

import types
import asyncio
import builtins
import sys

import pytest


def _install_stub_mcp_module(funcs: dict[str, object]) -> None:
    """Install a stub for mcp_servers.noveler.main into sys.modules.

    The stub prevents importing the real, heavy MCP module during unit tests.
    """
    pkg = types.ModuleType("mcp_servers")
    subpkg = types.ModuleType("mcp_servers.noveler")
    mod = types.ModuleType("mcp_servers.noveler.main")

    for name, obj in funcs.items():
        setattr(mod, name, obj)

    # Link modules
    setattr(subpkg, "main", mod)
    setattr(pkg, "noveler", subpkg)

    sys.modules["mcp_servers"] = pkg
    sys.modules["mcp_servers.noveler"] = subpkg
    sys.modules["mcp_servers.noveler.main"] = mod


@pytest.mark.unit
def test_mcp_call_unknown_tool_returns_2(monkeypatch: pytest.MonkeyPatch) -> None:
    from noveler.presentation.cli import cli_adapter

    async def dummy_exec(args):  # noqa: ANN001
        return {"success": True}

    # Install module without the requested tool (e.g., no execute_foo)
    _install_stub_mcp_module({"execute_run_quality_checks": dummy_exec})

    # Unknown tool
    rc = cli_adapter.run(["mcp", "call", "unknown_tool", "{}"])
    assert rc == 2


@pytest.mark.unit
def test_mcp_call_run_quality_checks_success(monkeypatch: pytest.MonkeyPatch) -> None:
    from noveler.presentation.cli import cli_adapter

    async def exec_rqc(args):  # noqa: ANN001
        return {"success": True, "score": 85}

    _install_stub_mcp_module({"execute_run_quality_checks": exec_rqc})

    rc = cli_adapter.run(["mcp", "call", "run_quality_checks", "{}"])
    assert rc == 0


@pytest.mark.unit
def test_check_command_success_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    from noveler.presentation.cli import cli_adapter

    async def exec_rqc(args):  # noqa: ANN001
        # Return a score above threshold so exit code is 0
        return {"success": True, "score": 82.5}

    async def exec_fix(args):  # noqa: ANN001
        return {"success": True, "metadata": {"applied": 3}}

    _install_stub_mcp_module(
        {
            "execute_run_quality_checks": exec_rqc,
            "execute_fix_quality_issues": exec_fix,
        }
    )

    rc = cli_adapter.run(["check", "1"])  # no --auto-fix path
    assert rc == 0
