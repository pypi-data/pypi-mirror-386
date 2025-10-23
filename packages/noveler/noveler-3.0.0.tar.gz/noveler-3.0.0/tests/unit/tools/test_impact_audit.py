# File: tests/unit/tools/test_impact_audit.py
# Purpose: Validate the impact audit automation workflow for B20影響調査.
# Context: Ensures the CLI helper reports matches and exit codes for pattern scans.

"""Unit tests for the impact audit tooling.

The tests confirm that the scanner aggregates matches correctly and that the CLI
behaves as expected when no matches are present. They are written against the
public functions to keep the tool callable from both humans and automation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from scripts.tools import impact_audit


def _setup_project(tmp_path: Path) -> Path:
    """Create a minimal project structure for testing purposes."""

    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    sample_file = src_dir / "sample_module.py"
    sample_file.write_text(
        """
CONFIG_PATH = "schemas/episode_config.yaml"
DOC_PATH = "docs/reference_guide.yaml"
""".strip()
    )

    return src_dir


def test_run_audit_collects_matches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The audit should record every matching line with relative paths."""

    _setup_project(tmp_path)

    monkeypatch.setattr(impact_audit, "find_guide_root", lambda: tmp_path)

    config = impact_audit.parse_args(["--pattern", r"\.yaml", "--paths", "src", "--output", "-"])

    result = impact_audit.run_audit(config)

    assert result.total_matches == 2
    grouped = result.matches_by_file()
    assert len(grouped) == 1
    (path, matches), = grouped.items()
    assert path.as_posix().endswith("src/sample_module.py")
    assert {m.line_number for m in matches} == {1, 2}


def test_main_respects_fail_on_zero(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The CLI should exit with code 1 when no matches exist and --fail-on-zero is set."""

    _setup_project(tmp_path)

    monkeypatch.setattr(impact_audit, "find_guide_root", lambda: tmp_path)

    exit_code = impact_audit.main(
        ["--pattern", r"DOES_NOT_EXIST", "--paths", "src", "--fail-on-zero", "--output", "-"]
    )

    assert exit_code == 1
