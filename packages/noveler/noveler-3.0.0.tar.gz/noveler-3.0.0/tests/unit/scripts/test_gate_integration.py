#!/usr/bin/env python3
# File: tests/unit/scripts/test_gate_integration.py
# Purpose: Test Gate B and Gate C integration in quality check workflow
# Context: Validates proper metadata generation and exit code handling

"""Test quality gate integration (Gate B/C)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "ci"))


class TestGateBIntegration:
    """Test Gate B (core checks) integration."""

    @patch("run_quality_checks_ndjson._load_gate_defaults")
    def test_gate_b_metadata_generation(self, mock_load_defaults, tmp_path):
        """Test that Gate B metadata is properly generated.

        Args:
            tmp_path: pytest standard temporary directory fixture
        """
        from run_quality_checks_ndjson import main

        mock_load_defaults.return_value = {
            "gate_defaults": {
                "outputs": {"core_report": "test.ndjson"},
                "thresholds": {
                    "severity": "medium",
                    "gate_b": {"rhythm": 80, "readability": 80, "grammar": 90}
                },
                "episodes": {"default": 1}
            }
        }

        # Mock the RunQualityChecksTool response
        with patch("run_quality_checks_ndjson.RunQualityChecksTool") as MockTool:
            mock_tool = MockTool.return_value
            mock_tool.execute.return_value = MagicMock(
                success=True,
                score=85,
                metadata={
                    "gate_b_pass": True,
                    "gate_b_should_fail": False,
                    "gate_b_thresholds": {"rhythm": 80, "readability": 80, "grammar": 90},
                    "gate_b_evaluation": {
                        "rhythm": {"threshold": 80, "score": 85, "passed": True},
                        "readability": {"threshold": 80, "score": 90, "passed": True},
                        "grammar": {"threshold": 90, "score": 95, "passed": True}
                    },
                    "ndjson": '{"score": 85}\n'
                }
            )

            test_args = [
                "run_quality_checks_ndjson.py",
                "--out", str(tmp_path / "test.ndjson")
            ]
            with patch("sys.argv", test_args):
                exit_code = main()

            assert exit_code == 0  # Gate B passed

    @patch("run_quality_checks_ndjson._load_gate_defaults")
    def test_gate_b_failure(self, mock_load_defaults, tmp_path):
        """Test that Gate B failure returns correct exit code.

        Args:
            tmp_path: pytest standard temporary directory fixture
        """
        from run_quality_checks_ndjson import main

        mock_load_defaults.return_value = {
            "gate_defaults": {
                "outputs": {"core_report": "test.ndjson"},
                "thresholds": {
                    "gate_b": {"rhythm": 80, "readability": 80, "grammar": 90}
                }
            }
        }

        with patch("run_quality_checks_ndjson.RunQualityChecksTool") as MockTool:
            mock_tool = MockTool.return_value
            mock_tool.execute.return_value = MagicMock(
                success=True,
                score=75,  # Below threshold
                metadata={
                    "gate_b_pass": False,
                    "gate_b_should_fail": True,
                    "gate_b_evaluation": {
                        "rhythm": {"threshold": 80, "score": 75, "passed": False},
                        "readability": {"threshold": 80, "score": 85, "passed": True},
                        "grammar": {"threshold": 90, "score": 92, "passed": True}
                    },
                    "ndjson": '{"score": 75}\n'
                }
            )

            test_args = [
                "run_quality_checks_ndjson.py",
                "--out", str(tmp_path / "test.ndjson")
            ]
            with patch("sys.argv", test_args):
                exit_code = main()

            assert exit_code == 2  # Gate B failed

    @patch("run_quality_checks_ndjson._load_gate_defaults")
    def test_main_uses_gate_defaults_when_flags_missing(self, mock_load_defaults, tmp_path):
        """Ensure gate defaults populate request parameters by default.

        Args:
            tmp_path: pytest standard temporary directory fixture
        """
        from run_quality_checks_ndjson import main

        mock_load_defaults.return_value = {
            "gate_defaults": {
                "outputs": {"core_report": "reports/quality.ndjson"},
                "thresholds": {
                    "severity": "medium",
                    "gate_b": {"rhythm": 83, "readability": 87, "grammar": 92},
                },
                "episodes": {"default": 3},
                "editorial_checklist": {"require_all_pass": True},
            }
        }

        captured_request = None

        with patch("run_quality_checks_ndjson.RunQualityChecksTool") as MockTool:
            mock_tool = MockTool.return_value

            def _execute(req):
                nonlocal captured_request
                captured_request = req
                return MagicMock(
                    success=True,
                    score=95,
                    metadata={
                        "gate_b_pass": True,
                        "gate_b_should_fail": False,
                        "ndjson": '{"score": 95}\n'
                    },
                )

            mock_tool.execute.side_effect = _execute

            out_path = tmp_path / "quality.ndjson"
            test_args = [
                "run_quality_checks_ndjson.py",
                "--out", str(out_path),
            ]
            with patch("sys.argv", test_args):
                exit_code = main()

            assert exit_code == 0

        assert captured_request is not None
        params = captured_request.additional_params
        assert params["severity_threshold"] == "medium"
        assert params["gate_thresholds"] == {"rhythm": 83, "readability": 87, "grammar": 92}
        assert params["fail_on"]["score_below"] == 83.0
        assert captured_request.episode_number == 3


class TestGateCIntegration:
    """Test Gate C (editorial checklist) integration."""

    def test_gate_c_evaluation(self):
        """Test Gate C evaluation with mocked editorial checklist."""
        from run_quality_checks_ndjson import check_gate_c_status

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("""# Editorial 12-step checklist

## L12-01 - Opening

- Status: PASS
- Note: Good hook

## L12-02 - Dialogue

- Status: TODO
- Note: Needs work
""")
            checklist_path = f.name

        # Mock the subprocess call to editorial_checklist_evaluator
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=2,  # Gate C failed (TODO items present) - see editorial_checklist_evaluator.py L131
                stdout=json.dumps({
                    "total_items": 2,
                    "counts": {"PASS": 1, "TODO": 1, "NOTE": 0, "UNKNOWN": 0},
                    "pass": False,
                    "require_all_pass": True
                })
            )

            result = check_gate_c_status(checklist_path)

            assert result["gate_c_pass"] is False
            assert result["gate_c_should_fail"] is True
            assert result["gate_c_counts"]["todo"] == 1
            assert result["gate_c_counts"] == {
                "total": 2,
                "pass": 1,
                "note": 0,
                "todo": 1,
                "unknown": 0,
                "checked": 2,
                "unchecked": 0,
            }
            assert result["gate_c_counts_by_status"] == {"PASS": 1, "TODO": 1, "NOTE": 0, "UNKNOWN": 0}

        Path(checklist_path).unlink()

    @patch("run_quality_checks_ndjson._load_gate_defaults")
    @patch("run_quality_checks_ndjson.check_gate_c_status")
    def test_gate_c_integration_in_main(self, mock_check_gate_c, mock_load_defaults, tmp_path):
        """Test Gate C integration in main workflow.

        Args:
            tmp_path: pytest standard temporary directory fixture
        """
        from run_quality_checks_ndjson import main

        mock_load_defaults.return_value = {
            "gate_defaults": {
                "outputs": {
                    "core_report": "test.ndjson",
                    "editorial_checklist_report": "editorial.md"
                }
            }
        }

        # Mock Gate B passes
        with patch("run_quality_checks_ndjson.RunQualityChecksTool") as MockTool:
            mock_tool = MockTool.return_value
            mock_tool.execute.return_value = MagicMock(
                success=True,
                score=85,
                metadata={
                    "gate_b_pass": True,
                    "gate_b_should_fail": False,
                    "ndjson": '{"score": 85}\n'
                }
            )

            # Mock Gate C fails
            mock_check_gate_c.return_value = {
                "gate_c_pass": False,
                "gate_c_should_fail": True,
                "gate_c_counts": {
                    "total": 12,
                    "pass": 10,
                    "note": 0,
                    "todo": 2,
                    "unknown": 0,
                    "checked": 12,
                    "unchecked": 0,
                },
                "gate_c_counts_by_status": {"PASS": 10, "NOTE": 0, "TODO": 2, "UNKNOWN": 0},
            }

            test_args = [
                "run_quality_checks_ndjson.py",
                "--out", str(tmp_path / "test.ndjson"),
                "--enable-gate-c"
            ]
            with patch("sys.argv", test_args):
                exit_code = main()

                assert exit_code == 2  # Gate C failed despite Gate B passing
                mock_check_gate_c.assert_called_once()
                args, _ = mock_check_gate_c.call_args
                assert args[0] == "editorial.md"

    @patch("run_quality_checks_ndjson._load_gate_defaults")
    @patch("run_quality_checks_ndjson.check_gate_c_status")
    def test_gate_c_integration_respects_explicit_report(self, mock_check_gate_c, mock_load_defaults, tmp_path):
        """Explicit --editorial-report should override defaults.

        Args:
            tmp_path: pytest standard temporary directory fixture
        """
        from run_quality_checks_ndjson import main

        mock_load_defaults.return_value = {
            "gate_defaults": {
                "outputs": {
                    "core_report": "test.ndjson",
                    "editorial_checklist_report": "default_editorial.md"
                }
            }
        }

        with patch("run_quality_checks_ndjson.RunQualityChecksTool") as MockTool:
            mock_tool = MockTool.return_value
            mock_tool.execute.return_value = MagicMock(
                success=True,
                score=85,
                metadata={
                    "gate_b_pass": True,
                    "gate_b_should_fail": False,
                    "ndjson": '{"score": 85}\n'
                }
            )

            mock_check_gate_c.return_value = {
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
            }

            test_args = [
                "run_quality_checks_ndjson.py",
                "--out", str(tmp_path / "test.ndjson"),
                "--enable-gate-c",
                "--editorial-report", "custom_editorial.md",
            ]
            with patch("sys.argv", test_args):
                exit_code = main()

            assert exit_code == 0
            mock_check_gate_c.assert_called_once()
            args, _ = mock_check_gate_c.call_args
            assert args[0] == "custom_editorial.md"


class TestBothGatesIntegration:
    """Test combined Gate B and C behavior."""

    @patch("run_quality_checks_ndjson._load_gate_defaults")
    @patch("run_quality_checks_ndjson.check_gate_c_status")
    def test_both_gates_pass(self, mock_check_gate_c, mock_load_defaults, tmp_path):
        """Test that both gates passing returns success.

        Args:
            tmp_path: pytest standard temporary directory fixture
        """
        from run_quality_checks_ndjson import main

        mock_load_defaults.return_value = {
            "gate_defaults": {
                "outputs": {"core_report": "test.ndjson"}
            }
        }

        with patch("run_quality_checks_ndjson.RunQualityChecksTool") as MockTool:
            mock_tool = MockTool.return_value
            mock_tool.execute.return_value = MagicMock(
                success=True,
                metadata={
                    "gate_b_pass": True,
                    "gate_b_should_fail": False,
                    "ndjson": '{"score": 90}\n'
                }
            )

            mock_check_gate_c.return_value = {
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
            }

            test_args = [
                "run_quality_checks_ndjson.py",
                "--out", str(tmp_path / "test.ndjson"),
                "--enable-gate-c"
            ]
            with patch("sys.argv", test_args):
                exit_code = main()

            assert exit_code == 0  # Both gates passed
