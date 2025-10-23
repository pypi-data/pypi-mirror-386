# File: tests/unit/mcp_servers/test_format_utils.py
# Purpose: Unit tests for shared formatting helpers used by MCP servers.
# Context: Ensures stable textual rendering for JSON conversion results and
#          simple mappings. Lightweight and side-effect free.

from mcp_servers.noveler.core.format_utils import format_json_result, format_dict


def test_format_dict_renders_key_value_lines() -> None:
    data = {"a": 1, "b": "x"}
    out = format_dict(data)
    assert "a: 1" in out
    assert "b: x" in out


def test_format_json_result_success_branch() -> None:
    result = {
        "success": True,
        "command": "write 1",
        "outputs": {"total_files": 2, "total_size_bytes": 1234},
    }
    out = format_json_result(result)
    assert "成功: True" in out
    assert "コマンド: write 1" in out
    assert "出力ファイル数: 2" in out
    assert "総サイズ: 1234 bytes" in out


def test_format_json_result_error_branch() -> None:
    result = {
        "success": False,
        "command": "check 1",
        "error": {"code": 500, "message": "oops"},
    }
    out = format_json_result(result)
    assert "成功: False" in out
    assert "コマンド: check 1" in out
    assert "エラーコード: 500" in out
    assert "エラーメッセージ: oops" in out

