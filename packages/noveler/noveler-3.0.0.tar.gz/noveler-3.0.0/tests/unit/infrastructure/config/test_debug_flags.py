#!/usr/bin/env python3
import os
from contextlib import contextmanager

from noveler.infrastructure.config.debug_flags import is_debug_enabled


@contextmanager
def env(**kwargs):
    prev = {k: os.environ.get(k) for k in kwargs}
    try:
        for k, v in kwargs.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = str(v)
        yield
    finally:
        for k, v in prev.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_is_debug_enabled_precedence_mcp_safety_first():
    with env(MCP_STDIO_SAFE="1", MCP_STRICT_STDOUT=None, NOVELER_DEBUG="1", DEBUG_MCP="1"):
        assert is_debug_enabled("mcp") is False

    with env(MCP_STDIO_SAFE=None, MCP_STRICT_STDOUT="1", NOVELER_DEBUG="1", DEBUG_MCP="1"):
        assert is_debug_enabled("mcp") is False


def test_is_debug_enabled_explicit_then_legacy():
    with env(MCP_STDIO_SAFE=None, MCP_STRICT_STDOUT=None, NOVELER_DEBUG="1", DEBUG_MCP=None):
        assert is_debug_enabled("mcp") is True

    with env(MCP_STDIO_SAFE=None, MCP_STRICT_STDOUT=None, NOVELER_DEBUG=None, DEBUG_MCP="1"):
        assert is_debug_enabled("mcp") is True

    with env(MCP_STDIO_SAFE=None, MCP_STRICT_STDOUT=None, NOVELER_DEBUG=None, DEBUG_MCP=None):
        assert is_debug_enabled("mcp") is False

