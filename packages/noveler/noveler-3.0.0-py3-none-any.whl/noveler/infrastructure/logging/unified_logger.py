#!/usr/bin/env python3
# File: src/noveler/infrastructure/logging/unified_logger.py
# Purpose: Unified logging system for all modules with Rich/JSON/Plain formatters
# Context: Singleton logger with environment presets (dev/prod/mcp), CLI integration

"""Unified logging system providing consistent logging across the project.

Purpose:
    Supply a configurable logging facade that standardises formatting,
    handlers, and environment presets for every Noveler component.
Context:
    Imported by application services, infrastructure adapters, and command
    line entry points that require consistent logging behaviour.
Preconditions:
    Assumes the standard library ``logging`` module and Rich are available and
    that the process has permission to create the ``logs/`` directory.
Side Effects:
    Creates log directories, writes rotating log files, and mutates the
    process-global logging configuration when the module is initialised.
"""

import json
import logging.handlers
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.logging import RichHandler

# Removed self-import: get_logger is defined below


def _env_truthy(*names: str) -> bool:
    """Evaluate whether any named environment variable is truthy.

    Purpose:
        Check a collection of environment variables and report whether at
        least one is configured to a truthy value.
    Args:
        names (str): Environment variable names to inspect.
    Returns:
        bool: ``True`` when any referenced variable is set to a recognised
        truthy value.
    Preconditions:
        None beyond standard access to ``os.environ``.
    Side Effects:
        Reads environment variables from the current process.
    """
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value.lower() in {"1", "true", "on"}
    return False


# B30 compliance: Use unified Console from shared_utilities (avoid circular import)
def _get_logging_console() -> Console:
    """Create a Rich console dedicated to logging output.

    Purpose:
        Provide a logging console without importing helper utilities that
        would introduce circular dependencies.
    Returns:
        Console: Rich console configured to emit to ``stderr``.
    Preconditions:
        Requires Rich to be installed and importable.
    Side Effects:
        Instantiates a ``Console`` object targeting ``sys.stderr``.
    """
    # For STDIO safety, console logs go to stderr
    # (avoids polluting MCP server JSON-RPC communication)
    return Console(file=sys.stderr)


class LogFormat(Enum):
    """Enumerate supported console/file log output formats.

    Purpose:
        Provide symbolic names for selecting console and file formatter
        behaviour throughout the logging configuration.
    Preconditions:
        None; enumeration values are consumed by configuration helpers.
    Side Effects:
        None.
    """

    RICH = "rich"  # Rich format (human-readable)
    JSON = "json"  # JSON format (machine-readable)
    PLAIN = "plain"  # Plain text


class LogLevel(Enum):
    """Enumerate supported log levels used across configuration.

    Purpose:
        Offer readable constants that map to ``logging`` level integers.
    Preconditions:
        None.
    Side Effects:
        None.
    """

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class LogConfig:
    """Capture mutable logging configuration defaults.

    Purpose:
        Bundle together log destinations, formatting preferences, and
        environmental toggles consumed by :class:`UnifiedLogger`.
    Preconditions:
        None; values are plain dataclass fields with sensible defaults.
    Side Effects:
        None.
    """

    log_dir: Path = Path("logs")
    log_file: str = "novel_system.log"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_format: LogFormat = LogFormat.RICH
    file_format: LogFormat = LogFormat.JSON
    console_level: LogLevel = LogLevel.INFO
    file_level: LogLevel = LogLevel.DEBUG
    verbose: int = 0  # -v count (0: normal, 1: INFO, 2: DEBUG)
    quiet: bool = False  # -q flag enabled
    enable_console: bool = True
    environment: str = "development"
    schema_version: str = "1.0"
    fallback_log_dir: Optional[Path] = None
    fallback_retention_days: int = 14


class JsonFormatter(logging.Formatter):
    """Formatter that serialises log records into structured JSON.

    Purpose:
        Emit log entries with machine-readable metadata for downstream tools
        such as log aggregators and test harnesses.
    Preconditions:
        Requires standard ``logging`` infrastructure and valid configuration
        values for the environment and schema version.
    Side Effects:
        None beyond allocating formatter state.
    """

    def __init__(self, *, environment: str, schema_version: str, **kwargs: Any) -> None:
        """Initialise the formatter with environment metadata.

        Purpose:
            Record contextual fields that are injected into each JSON payload.
        Args:
            environment (str): Logical environment name (development, prod, etc.).
            schema_version (str): Version identifier for the log schema.
            **kwargs (Any): Additional keyword arguments forwarded to ``logging.Formatter``.
        Preconditions:
            Caller must provide non-empty ``environment`` and ``schema_version`` strings.
        Side Effects:
            Stores configuration for later formatting.
        """
        super().__init__(**kwargs)
        self._environment = environment
        self._schema_version = schema_version

    def format(self, record: logging.LogRecord) -> str:
        """Convert a ``logging.LogRecord`` into a JSON string.

        Purpose:
            Serialise standard log metadata together with environment
            information for storage or transport.
        Args:
            record (logging.LogRecord): Event to serialise.
        Returns:
            str: JSON string containing the record data.
        Preconditions:
            ``record`` must be a valid ``logging.LogRecord`` instance.
        Side Effects:
            Reads from ``os.getpid`` and may access ``record.exc_info``.
        """
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "pid": os.getpid(),
            "environment": self._environment,
            "schema_version": self._schema_version,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


class SafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Rotating handler that degrades gracefully when rotation fails."""

    def __init__(
        self,
        *args: Any,
        fallback_dir: Path | None = None,
        fallback_retention_days: int = 0,
        **kwargs: Any,
    ) -> None:
        self._fallback_dir = fallback_dir
        self._rotation_disabled = False
        self._fallback_retention_days = fallback_retention_days
        self._permission_warning_emitted = False
        super().__init__(*args, **kwargs)

    def shouldRollover(self, record: logging.LogRecord) -> bool:  # noqa: N802 - signature inherited
        if self._rotation_disabled:
            return False
        return super().shouldRollover(record)

    def doRollover(self) -> None:
        if self._rotation_disabled:
            return

        try:
            super().doRollover()
        except PermissionError as exc:
            self._handle_rotation_failure(exc)

    def _handle_rotation_failure(self, exc: PermissionError) -> None:
        """Disable rotation and optionally redirect logs when rename fails."""
        should_emit_warning = not self._permission_warning_emitted
        message_parts: list[str] = []
        if should_emit_warning:
            message_parts.extend(
                [
                    "SafeRotatingFileHandler: PermissionError during rotation",
                    f"path={self.baseFilename}",
                    f"reason={exc}",
                ]
            )

        fallback_path: Path | None = None
        if self._fallback_dir is not None:
            try:
                fallback_dir = Path(self._fallback_dir)
                fallback_dir.mkdir(parents=True, exist_ok=True)
                fallback_path = fallback_dir / Path(self.baseFilename).name
                if should_emit_warning:
                    message_parts.append(f"fallback={fallback_path}")
            except Exception as fallback_exc:  # pragma: no cover - best effort logging
                if should_emit_warning:
                    message_parts.append(f"fallback_error={fallback_exc}")
                fallback_path = None

        if getattr(self, "stream", None):
            try:
                self.stream.close()
            except Exception:  # pragma: no cover - best effort cleanup
                pass
            finally:
                self.stream = None

        if fallback_path is not None:
            self.baseFilename = str(fallback_path)

        if fallback_path is not None:
            self._rotation_disabled = False
            if should_emit_warning:
                message_parts.append("rotation=continue_on_fallback")
            self._cleanup_fallback_files(Path(self.baseFilename).parent)
        else:
            self._rotation_disabled = True
            self.maxBytes = 0
            self.backupCount = 0
            if should_emit_warning:
                message_parts.append("rotation=disabled")

        if should_emit_warning:
            sys.stderr.write(" | ".join(message_parts) + "\n")
            self._permission_warning_emitted = True

    def _cleanup_fallback_files(self, directory: Path) -> None:
        """Remove aged fallback log files beyond the retention window."""
        retention_days = max(self._fallback_retention_days, 0)
        if retention_days == 0:
            return

        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        for candidate in directory.glob("novel_system.log*"):
            try:
                stat = candidate.stat()
            except FileNotFoundError:
                continue
            modified_time = datetime.fromtimestamp(stat.st_mtime, timezone.utc)
            if modified_time < cutoff:
                try:
                    candidate.unlink()
                except Exception:
                    # Best effort cleanup; ignore failures to avoid noisy stderr.
                    pass


class UnifiedLogger:
    """Manage project-wide logging through a singleton facade.

    Purpose:
        Centralise configuration of handlers, formatters, and presets so that
        every component emits logs consistently.
    Preconditions:
        Requires write access to the configured log directory and standard
        library logging functionality.
    Side Effects:
        Mutates global logging handlers and levels when initialised.
    """

    _instance: Optional["UnifiedLogger"] = None
    _initialized: bool = False

    def __new__(cls) -> "UnifiedLogger":
        """Return the singleton instance for the logger manager.

        Purpose:
            Guarantee that only one :class:`UnifiedLogger` exists during the
            process lifetime.
        Returns:
            UnifiedLogger: Shared singleton instance.
        Preconditions:
            None.
        Side Effects:
            Allocates the singleton on first call.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: LogConfig | None = None) -> None:
        """Initialise the logging system on first instantiation.

        Purpose:
            Store configuration, apply environment overrides, and install
            logging handlers for the entire process.
        Args:
            config (LogConfig | None): Optional configuration override; when
                omitted, defaults are used.
        Preconditions:
            None; repeated constructions are ignored after first initialisation.
        Side Effects:
            Configures filesystem handlers, console handlers, and module-level
            logging settings.
        """
        if self._initialized:
            return

        self.config = config or LogConfig()
        self._apply_environment_overrides()
        self._setup_logging()
        self._initialized = True

    def _apply_environment_overrides(self) -> None:
        """Adjust configuration using environment variables.

        Purpose:
            Apply presets and overrides derived from environment variables
            prior to constructing logging handlers.
        Preconditions:
            None.
        Side Effects:
            Mutates ``self.config`` fields based on environment state.
        """

        if preset := os.getenv("NOVEL_LOG_PRESET"):
            self._apply_preset(preset.lower())

        if _env_truthy("NOVELER_PRODUCTION_MODE"):
            self._apply_preset("production")

        if _env_truthy("MCP_LIGHTWEIGHT_DEFAULT"):
            self._apply_preset("mcp")
            self.config.enable_console = False

        if log_dir := os.getenv("NOVEL_LOG_DIR"):
            self.config.log_dir = Path(log_dir)

        if fallback_dir := os.getenv("NOVEL_LOG_FALLBACK_DIR"):
            self.config.fallback_log_dir = Path(fallback_dir)

        if retention := os.getenv("NOVEL_LOG_FALLBACK_RETENTION_DAYS"):
            try:
                self.config.fallback_retention_days = max(int(retention), 0)
            except ValueError:
                logger.warning(
                    "Invalid NOVEL_LOG_FALLBACK_RETENTION_DAYS value '%s'; using default %s",
                    retention,
                    self.config.fallback_retention_days,
                )

        if log_file := os.getenv("NOVEL_LOG_FILE"):
            self.config.log_file = log_file

        if schema_version := os.getenv("NOVEL_LOG_SCHEMA_VERSION"):
            self.config.schema_version = schema_version

        if env_name := os.getenv("NOVEL_LOG_ENVIRONMENT"):
            self.config.environment = env_name

        if worker_id := os.getenv("PYTEST_XDIST_WORKER"):
            base, ext = os.path.splitext(self.config.log_file)
            if not ext:
                ext = ".log"
            self.config.log_file = f"{base}_{worker_id}{ext}"

    def _setup_logging(self) -> None:
        """Configure root logger handlers based on current settings.

        Purpose:
            Install file and console handlers that honour the stored
            configuration.
        Preconditions:
            ``self.config`` must already contain desired values.
        Side Effects:
            Mutates the root logger, creates log directories, and attaches handlers.
        """
        # Configure root logger
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.DEBUG)

        # Clear existing handlers
        self.root_logger.handlers.clear()

        # Create log directory
        self.config.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up file handler
        self._setup_file_handler()

        # Set up console handler
        self._setup_console_handler()

    def _apply_preset(self, preset: str) -> None:
        """Apply a named preset to the current configuration.

        Purpose:
            Switch logging behaviour to align with common runtime environments
            such as development, production, or MCP.
        Args:
            preset (str): Preset identifier (e.g., ``"production"``).
        Preconditions:
            ``preset`` should correspond to a recognised preset name.
        Side Effects:
            Mutates ``self.config`` fields.
        """

        preset = preset.lower()
        if preset in {"dev", "development"}:
            self.config.environment = "development"
            self.config.enable_console = True
            self.config.console_format = LogFormat.RICH
            self.config.console_level = LogLevel.INFO
            self.config.file_format = LogFormat.JSON
            self.config.file_level = LogLevel.DEBUG
            self.config.quiet = False
        elif preset in {"prod", "production"}:
            self.config.environment = "production"
            self.config.enable_console = True
            self.config.console_format = LogFormat.PLAIN
            self.config.console_level = LogLevel.WARNING
            self.config.file_format = LogFormat.JSON
            self.config.file_level = LogLevel.INFO
            self.config.quiet = True
        elif preset == "mcp":
            self.config.environment = "mcp"
            self.config.enable_console = False
            self.config.console_format = LogFormat.PLAIN
            self.config.file_format = LogFormat.JSON
            self.config.file_level = LogLevel.INFO
            self.config.quiet = True

    def _setup_file_handler(self) -> None:
        """Create and attach the file handler for persistent logging.

        Purpose:
            Ensure logs are written to a rotating file with the configured
            format and retention settings.
        Preconditions:
            ``self.config.log_dir`` must be a valid directory path.
        Side Effects:
            Opens log files and attaches a handler to the root logger.
        """
        log_path = self.config.log_dir / self.config.log_file
        fallback_dir = (
            self.config.fallback_log_dir
            if self.config.fallback_log_dir is not None
            else Path(tempfile.gettempdir()) / "noveler" / "logs"
        )

        file_handler = SafeRotatingFileHandler(
            log_path,
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count,
            encoding="utf-8",
            delay=True,
            fallback_dir=fallback_dir,
            fallback_retention_days=self.config.fallback_retention_days,
        )

        file_handler.setLevel(self.config.file_level.value)

        # Configure formatter
        if self.config.file_format == LogFormat.JSON:
            json_formatter = JsonFormatter(
                environment=self.config.environment,
                schema_version=self.config.schema_version,
            )
            file_handler.setFormatter(json_formatter)
        else:
            plain_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(plain_formatter)
        self.root_logger.addHandler(file_handler)

    def _setup_console_handler(self) -> None:
        """Create and attach the console handler when enabled.

        Purpose:
            Configure interactive logging output tailored to console
            preferences such as Rich, JSON, or plain formatting.
        Preconditions:
            ``self.config`` must be initialised; console logging must be enabled.
        Side Effects:
            Instantiates console handler instances and attaches them to the root logger.
        """
        if not self.config.enable_console:
            return

        # Process verbose and quiet flags
        if self.config.quiet:
            console_level = LogLevel.WARNING
        elif self.config.verbose >= 2:
            console_level = LogLevel.DEBUG
        elif self.config.verbose == 1:
            console_level = LogLevel.INFO
        else:
            console_level = self.config.console_level

        if self.config.console_format == LogFormat.RICH:
            # Rich format
            console_handler = RichHandler(
                console=_get_logging_console(),
                rich_tracebacks=True,
                show_time=True,
                show_path=False,
            )

        elif self.config.console_format == LogFormat.JSON:
            # JSON format
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(
                JsonFormatter(
                    environment=self.config.environment,
                    schema_version=self.config.schema_version,
                )
            )
        else:
            # Plain text
            console_handler = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter("%(levelname)s: %(message)s")
            console_handler.setFormatter(formatter)

        console_handler.setLevel(console_level.value)
        self.root_logger.addHandler(console_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Return a configured logger with the desired name.

        Purpose:
            Provide callers with a logger that inherits the unified
            configuration.
        Args:
            name (str): Logger namespace, typically ``__name__``.
        Returns:
            logging.Logger: Logger bound to the global configuration.
        Preconditions:
            ``UnifiedLogger`` must have been initialised.
        Side Effects:
            None beyond retrieving a logger from ``logging``.
        """
        return logging.getLogger(name)

    def update_config(self, **kwargs: object) -> None:
        """Update configuration fields and reinitialise handlers.

        Purpose:
            Apply runtime configuration changes such as toggling verbosity or
            switching formats.
        Args:
            **kwargs (object): Configuration overrides, including optional
                ``preset`` values.
        Preconditions:
            None.
        Side Effects:
            Rebuilds logging handlers and mutates ``self.config``.
        """
        preset = kwargs.pop("preset", None)
        if isinstance(preset, str):
            self._apply_preset(preset)

        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Reconfigure logging system
        self.root_logger.handlers.clear()
        self._setup_logging()

    @classmethod
    def configure_from_cli(cls, args: object) -> "UnifiedLogger":
        """Create and configure the logger from CLI arguments.

        Purpose:
            Translate command-line flags into a :class:`UnifiedLogger`
            instance with matching behaviour.
        Args:
            args (object): Namespace-style object exposing logging options.
        Returns:
            UnifiedLogger: Shared singleton configured with CLI values.
        Preconditions:
            ``args`` must expose attributes such as ``verbose`` or
            ``log_format`` when used.
        Side Effects:
            May read environment variables; initialises global logging state.
        """
        config = LogConfig()

        # Process verbose and quiet
        if hasattr(args, "verbose"):
            config.verbose = args.verbose or 0
        if hasattr(args, "quiet"):
            config.quiet = args.quiet or False

        # Process log-format
        if hasattr(args, "log_format"):
            format_map = {
                "rich": LogFormat.RICH,
                "json": LogFormat.JSON,
                "plain": LogFormat.PLAIN,
            }
            config.console_format = format_map.get(args.log_format, LogFormat.RICH)

        # Also read from environment variables
        if env_level := os.getenv("NOVEL_LOG_LEVEL"):
            level_map = {
                "DEBUG": LogLevel.DEBUG,
                "INFO": LogLevel.INFO,
                "WARNING": LogLevel.WARNING,
                "ERROR": LogLevel.ERROR,
                "CRITICAL": LogLevel.CRITICAL,
            }
            config.console_level = level_map.get(env_level, LogLevel.INFO)

        return cls(config)


# Global instance
_unified_logger = UnifiedLogger()


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured by the unified logging subsystem.

    Purpose:
        Provide a one-line helper for modules that prefer functional access
        instead of interacting with :class:`UnifiedLogger` directly.
    Args:
        name (str): Logger name to retrieve.
    Returns:
        logging.Logger: Configured logger instance.
    Preconditions:
        ``UnifiedLogger`` must have been initialised (occurs at import time).
    Side Effects:
        None.
    """
    return _unified_logger.get_logger(name)


def configure_logging(**kwargs: object) -> None:
    """Apply configuration overrides to the unified logger.

    Purpose:
        Offer a functional façade for updating logger settings from callers
        that cannot easily access the singleton instance.
    Args:
        **kwargs (object): Configuration overrides forwarded to
            :meth:`UnifiedLogger.update_config`.
    Preconditions:
        None.
    Side Effects:
        Reconfigures logging handlers and mutates logger settings.
    """
    _unified_logger.update_config(**kwargs)
