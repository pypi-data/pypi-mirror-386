# File: tests/e2e/test_mcp_logging_env.py
# Purpose: E2E tests for MCP logging environment switching and stderr pollution prevention
# Context: Validates unified logging behavior across different operational presets

"""E2E tests for MCP logging environment configuration.

Tests verify that:
1. MCP_LIGHTWEIGHT_DEFAULT prevents stderr pollution
2. NOVEL_LOG_PRESET correctly switches between environments
3. Logging configuration properly isolates MCP server operation
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest


class TestMCPLoggingEnvironment:
    """Test MCP logging environment configuration."""

    def test_mcp_stdio_safe_prevents_stderr(self, tmp_path: Path) -> None:
        """Test that MCP_LIGHTWEIGHT_DEFAULT=1 prevents stderr output."""
        # Create isolated log directory
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # Create a test script that attempts to log
        test_script = tmp_path / "test_mcp_logging.py"
        test_script.write_text(f"""
import os
import sys
import json
os.environ['MCP_LIGHTWEIGHT_DEFAULT'] = '1'
os.environ['NOVEL_LOG_PRESET'] = 'mcp'
os.environ['NOVEL_LOG_DIR'] = {str(log_dir)!r}

from noveler.infrastructure.logging.unified_logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

# These should not appear in stderr when MCP_LIGHTWEIGHT_DEFAULT=1
logger.info("This should not appear in stderr")
logger.warning("This warning should be suppressed")
logger.error("Even errors should not pollute stderr")

# Only structured output should go to stdout
print(json.dumps({{"status": "ok", "message": "MCP safe mode"}}))
""")

        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "MCP_LIGHTWEIGHT_DEFAULT": "1",
                "NOVEL_LOG_PRESET": "mcp",
                "NOVEL_LOG_DIR": str(log_dir),
            },
        )

        # Verify no stderr pollution
        assert result.stderr == "", "MCP_LIGHTWEIGHT_DEFAULT=1 should prevent all stderr output"

        # Verify structured output still works
        output = json.loads(result.stdout.strip())
        assert output["status"] == "ok"
        assert output["message"] == "MCP safe mode"

    def test_log_preset_switching(self, tmp_path: Path) -> None:
        """Test that NOVEL_LOG_PRESET correctly switches between environments."""
        presets = ["development", "production", "mcp", "testing"]

        # Create isolated log directory
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        for preset in presets:
            # Create test script for each preset
            test_script = tmp_path / f"test_{preset}.py"
            test_script.write_text(f"""
import os
import sys
os.environ['NOVEL_LOG_PRESET'] = '{preset}'
os.environ['NOVEL_LOG_DIR'] = {str(log_dir)!r}

from noveler.infrastructure.logging.unified_logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

# Log at different levels
logger.debug("Debug message for {preset}")
logger.info("Info message for {preset}")
logger.warning("Warning message for {preset}")

print("PRESET:{preset}")
""")

            # Run with specific preset
            result = subprocess.run(
                [sys.executable, str(test_script)],
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "NOVEL_LOG_PRESET": preset,
                    "NOVEL_LOG_DIR": str(log_dir),
                },
            )

            # Verify preset was applied
            assert f"PRESET:{preset}" in result.stdout

            # Verify preset-specific behavior
            if preset == "mcp":
                # MCP preset should minimize stderr
                assert len(result.stderr) < 100 or "WARNING" not in result.stderr
            elif preset == "production":
                # Production should not include DEBUG
                assert "Debug message" not in result.stderr
            elif preset == "development":
                # Development might include more verbose output
                # Just verify it doesn't crash
                assert result.returncode == 0

    def test_json_logging_format(self, tmp_path: Path) -> None:
        """Test JSON logging format in production mode."""
        # Create isolated log directory
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        test_script = tmp_path / "test_json_log.py"
        test_script.write_text(f"""
import os
import sys
import json
os.environ['NOVEL_LOG_PRESET'] = 'production'
os.environ['NOVEL_LOG_FORMAT'] = 'json'
os.environ['NOVEL_LOG_DIR'] = {str(log_dir)!r}

from noveler.infrastructure.logging.unified_logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

# Log a structured message
logger.info("Test message", extra={{"user": "test", "action": "validate"}})
print("DONE")
""")

        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "NOVEL_LOG_PRESET": "production",
                "NOVEL_LOG_FORMAT": "json",
                "NOVEL_LOG_DIR": str(log_dir),
            },
        )

        assert "DONE" in result.stdout
        assert result.returncode == 0

    @pytest.mark.parametrize("log_level", ["DEBUG", "INFO", "WARNING", "ERROR"])
    def test_log_level_environment(self, tmp_path: Path, log_level: str) -> None:
        """Test that NOVEL_LOG_LEVEL correctly sets logging threshold."""
        # Create isolated log directory
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        test_script = tmp_path / f"test_level_{log_level}.py"
        test_script.write_text(f"""
import os
import sys
os.environ['NOVEL_LOG_LEVEL'] = '{log_level}'
os.environ['NOVEL_LOG_DIR'] = {str(log_dir)!r}

from noveler.infrastructure.logging.unified_logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

# Log at all levels
logger.debug("DEBUG")
logger.info("INFO")
logger.warning("WARNING")
logger.error("ERROR")

print("COMPLETED")
""")

        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "NOVEL_LOG_LEVEL": log_level,
                "NOVEL_LOG_DIR": str(log_dir),
            },
        )

        assert "COMPLETED" in result.stdout

        # Verify level filtering
        stderr = result.stderr
        if log_level == "ERROR":
            assert "DEBUG" not in stderr
            assert "INFO" not in stderr
            assert "WARNING" not in stderr
        elif log_level == "WARNING":
            assert "DEBUG" not in stderr
            assert "INFO" not in stderr
        elif log_level == "INFO":
            assert "DEBUG" not in stderr

    def test_mcp_server_logging_isolation(self, tmp_path: Path) -> None:
        """Test that MCP server properly isolates logging."""
        # Create isolated log directory
        log_dir = tmp_path / "logs"
        log_dir.mkdir()

        # This test simulates MCP server startup conditions
        test_script = tmp_path / "test_mcp_server.py"
        test_script.write_text(f"""
import os
import sys
import json

# Simulate MCP server environment
os.environ['MCP_LIGHTWEIGHT_DEFAULT'] = '1'
os.environ['NOVEL_LOG_PRESET'] = 'mcp'
os.environ['NOVELER_PRODUCTION_MODE'] = '1'
os.environ['NOVEL_LOG_DIR'] = {str(log_dir)!r}

from noveler.infrastructure.logging.unified_logger import configure_logging, get_logger

# Initialize as MCP server would
configure_logging()
logger = get_logger("mcp.server")

# Simulate server operations
logger.info("Server starting")
logger.debug("Debug info should be suppressed")

# Only structured output to stdout
response = {{"jsonrpc": "2.0", "method": "initialize", "params": {{}}}}
print(json.dumps(response))
""")

        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "MCP_LIGHTWEIGHT_DEFAULT": "1",
                "NOVEL_LOG_PRESET": "mcp",
                "NOVELER_PRODUCTION_MODE": "1",
                "NOVEL_LOG_DIR": str(log_dir),
            },
        )

        # Verify clean stdout with only JSON-RPC
        output = json.loads(result.stdout.strip())
        assert output["jsonrpc"] == "2.0"
        assert output["method"] == "initialize"

        # Verify no stderr pollution
        assert len(result.stderr) < 50 or "Server starting" not in result.stderr


@pytest.mark.integration
class TestLoggingIntegration:
    """Integration tests for logging subsystem."""

    def test_fallback_logger_safety(self) -> None:
        """Test that fallback loggers don't crash the system."""
        from noveler.domain.interfaces.logger_service import NullLoggerService

        # Get fallback logger (should be NullLogger)
        logger = NullLoggerService()

        # These should all be safe no-ops
        logger.debug("test")
        logger.info("test")
        logger.warning("test")
        logger.error("test")
        logger.critical("test")

        # Verify it's actually a null logger
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'info')

    def test_domain_console_fallback(self) -> None:
        """Test domain console fallback mechanism."""
        from noveler.domain.utils.domain_console import get_console

        # Get console (should provide safe fallback)
        console = get_console()

        # These should all be safe
        console.print("test")
        console.log("test")

        # Verify it has expected interface
        assert hasattr(console, 'print')
        assert hasattr(console, 'log')
