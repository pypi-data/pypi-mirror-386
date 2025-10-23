# File: tests/meta/test_llm_report_option.py
# Purpose: Sanity-check that the project exposes the --llm-report option so
#          LLM-oriented summaries are available even when pytest is invoked
#          directly (without make).
# Context: Uses pytest's built-in pytester fixture to run a help check in an
#          isolated temp environment.

import subprocess
from pathlib import Path


def test_llm_report_option_is_available() -> None:
    """Ensure --llm-report flag is listed in pytest --help output."""

    repo_root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        ["pytest", "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert "--llm-report" in completed.stdout
