#!/usr/bin/env python3
# File: tests/unit/mcp_servers/tools/test_run_quality_checks_gate_thresholds.py
# Purpose: Ensure RunQualityChecksTool emits gate threshold metadata and respects pass/fail evaluation.
# Context: Covers the new gate_b and gate_c metadata introduced for quality gate automation.

from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_servers.noveler.domain.entities.mcp_tool_base import ToolRequest
from mcp_servers.noveler.tools.run_quality_checks_tool import RunQualityChecksTool


def _write_text(tmp_path: Path, content: str = "") -> Path:
    fp = tmp_path / "manuscript.md"
    fp.write_text(content, encoding="utf-8")
    return fp


def test_gate_threshold_metadata_pass(tmp_path: Path) -> None:
    fp = _write_text(tmp_path, "")
    req = ToolRequest(
        episode_number=1,
        additional_params={
            "file_path": str(fp),
            "gate_thresholds": {"readability": 80, "grammar": 70},
        },
    )
    tool = RunQualityChecksTool()
    res = tool.execute(req)
    meta = res.metadata or {}
    assert meta.get("gate_b_pass") is True
    evaluation = meta.get("gate_b_evaluation", {})
    assert evaluation["readability"]["required"] == 80
    assert evaluation["readability"]["pass"] is True
    assert evaluation["grammar"]["pass"] is True
    assert meta.get("gate_b_should_fail") is False
    assert meta.get("should_fail") is False


def test_gate_threshold_metadata_fail(tmp_path: Path) -> None:
    fp = _write_text(tmp_path, "")
    req = ToolRequest(
        episode_number=1,
        additional_params={
            "file_path": str(fp),
            "gate_thresholds": {"readability": 120},
        },
    )
    tool = RunQualityChecksTool()
    res = tool.execute(req)
    meta = res.metadata or {}
    assert meta.get("gate_b_pass") is False
    evaluation = meta.get("gate_b_evaluation", {})
    assert evaluation["readability"]["required"] == 120
    assert evaluation["readability"]["pass"] is False
    assert meta.get("gate_b_should_fail") is True
    assert meta.get("should_fail") is True


def test_gate_c_metadata_pass(tmp_path: Path) -> None:
    """Test Gate C metadata when editorial checklist passes."""
    fp = _write_text(tmp_path, "")
    checklist_path = tmp_path / "editorial_checklist.md"

    # Mock _check_gate_c_status to return pass
    gate_c_result = {
        "gate_c_pass": True,
        "gate_c_should_fail": False,
        "gate_c_counts": {
            "total": 12,
            "pass": 12,
            "note": 0,
            "todo": 0,
            "unknown": 0,
            "checked": 12,
            "unchecked": 0,
        },
        "gate_c_counts_by_status": {"PASS": 12, "NOTE": 0, "TODO": 0, "UNKNOWN": 0},
        "gate_c_require_all_pass": True,
    }

    with patch.object(RunQualityChecksTool, "_check_gate_c_status", return_value=gate_c_result):
        req = ToolRequest(
            episode_number=1,
            additional_params={
                "file_path": str(fp),
                "enable_gate_c": True,
                "editorial_report": str(checklist_path),
            },
        )
        tool = RunQualityChecksTool()
        res = tool.execute(req)
        meta = res.metadata or {}

        assert meta.get("gate_c_pass") is True
        assert meta.get("gate_c_should_fail") is False
        assert meta.get("gate_c_counts") == {
            "total": 12,
            "pass": 12,
            "note": 0,
            "todo": 0,
            "unknown": 0,
            "checked": 12,
            "unchecked": 0,
        }
        assert meta.get("gate_c_counts_by_status") == {"PASS": 12, "NOTE": 0, "TODO": 0, "UNKNOWN": 0}
        assert meta.get("should_fail") is False


def test_gate_c_metadata_fail(tmp_path: Path) -> None:
    """Test Gate C metadata when editorial checklist fails."""
    fp = _write_text(tmp_path, "")
    checklist_path = tmp_path / "editorial_checklist.md"

    # Mock _check_gate_c_status to return fail
    gate_c_result = {
        "gate_c_pass": False,
        "gate_c_should_fail": True,
        "gate_c_counts": {
            "total": 12,
            "pass": 8,
            "note": 2,
            "todo": 2,
            "unknown": 0,
            "checked": 12,
            "unchecked": 0,
        },
        "gate_c_counts_by_status": {"PASS": 8, "NOTE": 2, "TODO": 2, "UNKNOWN": 0},
        "gate_c_require_all_pass": True,
    }

    with patch.object(RunQualityChecksTool, "_check_gate_c_status", return_value=gate_c_result):
        req = ToolRequest(
            episode_number=1,
            additional_params={
                "file_path": str(fp),
                "enable_gate_c": True,
                "editorial_report": str(checklist_path),
            },
        )
        tool = RunQualityChecksTool()
        res = tool.execute(req)
        meta = res.metadata or {}

        assert meta.get("gate_c_pass") is False
        assert meta.get("gate_c_should_fail") is True
        assert meta.get("gate_c_counts") == {
            "total": 12,
            "pass": 8,
            "note": 2,
            "todo": 2,
            "unknown": 0,
            "checked": 12,
            "unchecked": 0,
        }
        assert meta.get("gate_c_counts_by_status") == {"PASS": 8, "NOTE": 2, "TODO": 2, "UNKNOWN": 0}
        assert meta.get("should_fail") is True


def test_gate_c_metadata_with_error(tmp_path: Path) -> None:
    """Test Gate C metadata when evaluation encounters an error."""
    fp = _write_text(tmp_path, "")
    checklist_path = tmp_path / "nonexistent_checklist.md"

    # Mock _check_gate_c_status to return error
    gate_c_result = {
        "gate_c_pass": None,
        "gate_c_should_fail": False,
        "gate_c_error": "Editorial checklist not found",
    }

    with patch.object(RunQualityChecksTool, "_check_gate_c_status", return_value=gate_c_result):
        req = ToolRequest(
            episode_number=1,
            additional_params={
                "file_path": str(fp),
                "enable_gate_c": True,
                "editorial_report": str(checklist_path),
            },
        )
        tool = RunQualityChecksTool()
        res = tool.execute(req)
        meta = res.metadata or {}

        assert meta.get("gate_c_pass") is None
        assert meta.get("gate_c_should_fail") is False
        assert meta.get("gate_c_error") == "Editorial checklist not found"
        assert meta.get("should_fail") is False


def test_gate_b_and_c_combined_fail(tmp_path: Path) -> None:
    """Test combined Gate B and Gate C evaluation when both fail."""
    fp = _write_text(tmp_path, "")
    checklist_path = tmp_path / "editorial_checklist.md"

    # Mock _check_gate_c_status to return fail
    gate_c_result = {
        "gate_c_pass": False,
        "gate_c_should_fail": True,
        "gate_c_counts": {
            "total": 12,
            "pass": 6,
            "note": 3,
            "todo": 3,
            "unknown": 0,
            "checked": 12,
            "unchecked": 0,
        },
        "gate_c_counts_by_status": {"PASS": 6, "NOTE": 3, "TODO": 3, "UNKNOWN": 0},
        "gate_c_require_all_pass": True,
    }

    with patch.object(RunQualityChecksTool, "_check_gate_c_status", return_value=gate_c_result):
        req = ToolRequest(
            episode_number=1,
            additional_params={
                "file_path": str(fp),
                "gate_thresholds": {"readability": 120},  # Gate B fail
                "enable_gate_c": True,
                "editorial_report": str(checklist_path),
            },
        )
        tool = RunQualityChecksTool()
        res = tool.execute(req)
        meta = res.metadata or {}

        # Both gates should fail
        assert meta.get("gate_b_pass") is False
        assert meta.get("gate_b_should_fail") is True
        assert meta.get("gate_c_pass") is False
        assert meta.get("gate_c_should_fail") is True

        # should_fail should be True because both failed
        assert meta.get("should_fail") is True
