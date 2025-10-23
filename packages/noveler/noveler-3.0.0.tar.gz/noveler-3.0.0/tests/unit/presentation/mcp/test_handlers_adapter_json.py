"""Tests.unit.presentation.mcp.test_handlers_adapter_json
Where: Automated test module.
What: Thin adapter tests for JSON conversion helpers.
Why: Guards behaviour as we extract adapters from main.py.
"""

from __future__ import annotations

from noveler.presentation.mcp.adapters.handlers import (
    convert_cli_to_json_adapter,
    validate_json_response_adapter,
)


def test_convert_cli_to_json_adapter_runs() -> None:
    cli_result = {
        "success": True,
        "command": "noveler check 1",
        "returncode": 0,
        "stdout": "ok\n" * 10,
        "stderr": "",
    }
    res = convert_cli_to_json_adapter(cli_result)
    assert isinstance(res, dict)
    assert "stdout_summary" in res and "success" in res


def test_validate_json_response_adapter_runs() -> None:
    json_data = {"success": True, "any": "thing"}
    res = validate_json_response_adapter(json_data)
    assert isinstance(res, dict)
    assert res.get("valid") in (True, False)

