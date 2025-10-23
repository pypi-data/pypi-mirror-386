# File: tests/unit/reporting/test_fail_only_ndjson_xdist.py
# Purpose: Verify fail-only NDJSON streaming merges per-worker files and writes session summary under xdist.
# Context: Runs a child pytest session via the unified runner to isolate report directory and ensure no cross-run bleed.

import json
import os
import sys
import textwrap
import importlib.util as _util
from pathlib import Path
import subprocess
import pytest


def _have_xdist() -> bool:
    return _util.find_spec("xdist") is not None


@pytest.mark.skipif(not _have_xdist(), reason="pytest-xdist not available")
def test_fail_only_ndjson_merges_workers_and_writes_summary(tmp_path: Path):
    # Arrange: create a small failing test file in a temp directory.
    sample = tmp_path / "sample_fail_test.py"
    sample.write_text(
        textwrap.dedent(
            '''\
            import pytest
            def test_pass():
                assert True
            def test_fail():
                assert False, "intentional failure"
            '''
        ),
        encoding="utf-8",
    )

    # Use a dedicated report dir to avoid bleed with outer session.
    report_dir = tmp_path / "reports"
    env = os.environ.copy()
    env["LLM_REPORT_DIR"] = str(report_dir)
    env["LLM_REPORT_STREAM_FAIL"] = "1"

    # Act: run the unified runner with -n 2 to force multi-worker execution.
    cmd = [sys.executable, "scripts/run_pytest.py", "-q", str(sample), "-n", "2"]
    cp = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[3], env=env)

    # Assert: exit code must be non-zero due to failing test.
    assert cp.returncode != 0

    # Per-worker files (at least 2 when -n 2)
    stream_dir = report_dir / "stream"
    worker_files = sorted(stream_dir.glob("llm_fail_*.ndjson"))
    assert len(worker_files) >= 2, f"expected >=2 worker files, got {len(worker_files)} in {stream_dir}"

    # Merged file with session_summary at the end
    merged = report_dir / "llm_fail.ndjson"
    assert merged.exists(), "merged NDJSON not found"
    lines = [ln for ln in merged.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert lines, "merged NDJSON is empty"
    last = json.loads(lines[-1])
    assert last.get("event") in ("session_summary", "summary", "session_end"), last
    # Should contain at least one failing test_phase record
    has_phase = any((json.loads(ln).get("event") == "test_phase") for ln in lines)
    assert has_phase, "expected at least one test_phase record in merged NDJSON"


@pytest.mark.skipif(not _have_xdist(), reason="pytest-xdist not available")
def test_fail_only_ndjson_no_failures_writes_summary_only(tmp_path: Path):
    # Arrange: create a passing-only test file.
    sample = tmp_path / "sample_pass_test.py"
    sample.write_text(
        textwrap.dedent(
            '''\
            def test_pass_one():
                assert True
            def test_pass_two():
                assert 1 + 1 == 2
            '''
        ),
        encoding="utf-8",
    )

    report_dir = tmp_path / "reports"
    env = os.environ.copy()
    env["LLM_REPORT_DIR"] = str(report_dir)
    env["LLM_REPORT_STREAM_FAIL"] = "1"

    cmd = [sys.executable, "scripts/run_pytest.py", "-q", str(sample), "-n", "2"]
    cp = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[3], env=env)

    # All tests pass => exit code 0
    assert cp.returncode == 0

    merged = report_dir / "llm_fail.ndjson"
    assert merged.exists(), "merged NDJSON not found"
    lines = [ln for ln in merged.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert lines, "merged NDJSON is empty"
    # No test_phase events expected when everything passes (fail-only)
    has_phase = any((json.loads(ln).get("event") == "test_phase") for ln in lines)
    assert not has_phase, f"unexpected test_phase records in fail-only mode: {merged}"
    # Last line should be a session-level summary
    last = json.loads(lines[-1])
    assert last.get("event") in ("session_summary", "summary", "session_end"), last
