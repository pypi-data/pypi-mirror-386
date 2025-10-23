#!/usr/bin/env python3
# File: tests/unit/infrastructure/logging/test_unified_logger_preset.py
# Purpose: Verify unified logger presets and stderr-only console behaviour for MCP.
# Context: Ensures MCP preset disables console and prevents stdout pollution.

from __future__ import annotations

import sys

from noveler.infrastructure.logging.unified_logger import (
    _unified_logger,
    configure_logging,
    LogFormat,
)


def test_unified_logger_mcp_preset_disables_console_and_uses_stderr() -> None:
    # Switch to MCP preset
    configure_logging(preset="mcp")

    root = _unified_logger.root_logger

    # MCPプリセットではコンソール出力が無効化される
    assert not _unified_logger.config.enable_console

    # コンソールハンドラー(StreamHandler)が存在しないことを確認
    import logging
    has_console_handler = False
    for h in root.handlers:
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler):
            has_console_handler = True
            # もしStreamHandlerが存在する場合、それはstderrであるべき
            if hasattr(h, "stream"):
                assert h.stream is sys.stderr, "Stream must be stderr, not stdout"

    # MCPプリセットではコンソールハンドラーが無いはず
    assert not has_console_handler, "MCP preset should not have console handlers"

    # Switch back to development style (avoid side effects for other tests)
    configure_logging(preset="development", console_format=LogFormat.RICH)
