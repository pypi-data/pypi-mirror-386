#!/usr/bin/env python3
"""
CI check: ensure server stdout is MCP-only (Content-Length framed JSON),
and that the development guard blocks accidental stdout prints.

Runs two sub-tests:
  1) demo_server_ok.py: must emit only valid MCP frames and exit 0
  2) demo_server_bad.py (with MCP_STRICT_STDOUT=1): must fail on stdout print
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import List, Tuple


HEADER_SEP = b"\r\n\r\n"
CL_RE = re.compile(rb"^\s*Content-Length:\s*(\d+)\s*$", re.IGNORECASE)


class StreamError(Exception):
    pass


def parse_mcp_stream(data: bytes) -> Tuple[List[object], int]:
    """Parse a stream of MCP/LSP-like messages and return (messages, consumed_bytes).

    Requires headers to contain Content-Length and be separated by CRLFCRLF.
    Fails on any stray bytes or malformed frames.
    """

    i = 0
    messages: List[object] = []
    n = len(data)

    while i < n:
        # Find header/body separator
        sep = data.find(HEADER_SEP, i)
        if sep == -1:
            if i == 0 and n == 0:
                break  # empty stream
            raise StreamError("missing header terminator CRLFCRLF")

        header_blob = data[i:sep]
        header_lines = header_blob.split(b"\r\n") if header_blob else []

        content_length = None
        for line in header_lines:
            m = CL_RE.match(line)
            if m:
                content_length = int(m.group(1))
                break

        if content_length is None:
            raise StreamError("Content-Length header not found")

        body_start = sep + len(HEADER_SEP)
        body_end = body_start + content_length
        if body_end > n:
            raise StreamError("body truncated: claimed length exceeds available bytes")

        body = data[body_start:body_end]
        try:
            messages.append(json.loads(body.decode("utf-8")))
        except Exception as e:
            raise StreamError(f"invalid JSON body: {e}")

        i = body_end

        if i == n:
            break

    # No trailing noise permitted
    if i != n:
        raise StreamError(f"trailing bytes after last frame: {n - i} bytes")

    return messages, i


def run(cmd: list[str], env: dict[str, str], timeout: float = 5.0):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        out, err = p.communicate()
        return 124, out, err
    return p.returncode, out, err


def main() -> int:
    py = sys.executable

    base_env = os.environ.copy()
    base_env.setdefault("PYTHONUNBUFFERED", "1")

    # Test 1: OK server emits valid frames only
    env_ok = base_env.copy()
    # guard optional for ok; include to ensure no stray prints occur
    env_ok["MCP_STRICT_STDOUT"] = "1"
    code, out, err = run([py, "demo_server_ok.py"], env_ok)
    if code != 0:
        sys.stderr.write(f"[FAIL] demo_server_ok exit {code}\n")
        sys.stderr.write(err.decode(errors="ignore"))
        return 1

    try:
        msgs, consumed = parse_mcp_stream(out)
    except StreamError as e:
        sys.stderr.write(f"[FAIL] stdout not MCP-only: {e}\n")
        return 1

    if not msgs:
        sys.stderr.write("[FAIL] no MCP frames found on stdout\n")
        return 1

    # Test 2: Bad server should fail due to stdout print under guard
    env_bad = base_env.copy()
    env_bad["MCP_STRICT_STDOUT"] = "1"
    code2, out2, err2 = run([py, "demo_server_bad.py"], env_bad)
    if code2 == 0:
        sys.stderr.write("[FAIL] demo_server_bad unexpectedly succeeded (stdout print not blocked)\n")
        return 1

    # Success report
    sys.stdout.write("OK: stdout contains only valid MCP frames\n")
    sys.stdout.write("OK: guard blocks accidental stdout prints\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
