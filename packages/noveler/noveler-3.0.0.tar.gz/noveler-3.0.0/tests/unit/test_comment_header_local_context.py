# File: tests/unit/test_comment_header_local_context.py
# Purpose: Ensure MCP local_context server module meets header/docstring policy.
# Context: Executes the repository's comment header audit script against
#          src/mcp_servers/local_context/main.py to prevent regressions.

import subprocess
import sys
from pathlib import Path


def test_local_context_comment_header_audit_passes() -> None:
    """Run comment header audit for the local_context module.

    Purpose:
        Ensure the module complies with AGENTS.md header/docstring standards.

    Side Effects:
        Spawns a Python subprocess to run the audit script.
    """
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "comment_header_audit.py"
    target = repo_root / "src" / "mcp_servers" / "local_context" / "main.py"

    proc = subprocess.run(
        [sys.executable, str(script), "--paths", str(target)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr

