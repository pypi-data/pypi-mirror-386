"""Infrastructure adapter that records errors and collects diagnostics."""

from noveler.presentation.shared.shared_utilities import console

import os
import shutil

try:  # pragma: no cover
    import psutil as _psutil
except Exception:  # pragma: no cover
    _psutil = None
import platform
import traceback
from datetime import datetime, timezone
from typing import Any

from noveler.domain.services.error_classification_service import ErrorCategory, ErrorSeverity
from noveler.domain.services.error_reporting_service import ErrorContext
from noveler.infrastructure.logging.unified_logger import get_logger


class SystemContext:
    """Capture diagnostic data about the host environment.

    Attributes:
        platform: Platform identifier reported by the OS.
        python_version: Python runtime version string.
        working_directory: Current working directory path.
        environment_variables: Subset of environment variables captured for debugging.
        memory_usage: Human readable memory usage description.
        disk_space: Human readable disk usage description.
    """

    def __init__(self, context_data: dict[str, Any]) -> None:
        self.platform = context_data.get("platform", "unknown")
        self.python_version = context_data.get("python_version", "unknown")
        self.working_directory = context_data.get("working_directory", "unknown")
        self.environment_variables = context_data.get("environment_variables", {})
        self.memory_usage = context_data.get("memory_usage", "unknown")
        self.disk_space = context_data.get("disk_space", "unknown")


class ErrorInfo:
    """Describe a captured error along with contextual metadata.

    Attributes:
        exception: Original exception instance.
        exception_type: Type name of the exception.
        exception_message: String representation of the exception.
        category: Categorization supplied by the error classification service.
        severity: Severity level for the error.
        context: Domain-level error context information.
        system_context: Optional system context captured alongside the error.
        traceback: Formatted traceback string.
        timestamp: UTC timestamp when the error was observed.
    """

    def __init__(
        self,
        exception: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: ErrorContext,
        system_context: SystemContext | None = None,
    ) -> None:
        self.exception = exception
        self.exception_type = type(exception).__name__
        self.exception_message = str(exception)
        self.category = category
        self.severity = severity
        self.context = context
        self.system_context = system_context
        self.traceback = traceback.format_exc()
        self.timestamp = datetime.now(timezone.utc)


class ErrorLoggingAdapter:
    """Implement technical error logging concerns for infrastructure.

    Responsibilities:
        - Persist detailed error information
        - Gather system diagnostics
        - Track performance metrics
        - Coordinate console and logger output
    """

    def __init__(self, logger_name: str = __name__, log_file: str | None = None) -> None:
        """Configure the adapter and prepare diagnostics containers.

        Args:
            logger_name: Identifier passed to the unified logger factory.
            log_file: Optional path if file-based logging is required.
        """
        self.logger = get_logger(logger_name)
        self._setup_logger(log_file)
        self._error_count = 0
        self._performance_metrics = {}

    def log_error(self, error_info: ErrorInfo) -> None:
        """Persist a detailed error record and update metrics.

        Args:
            error_info: Aggregated error details to record.
        """
        self._error_count += 1
        log_data: dict[str, Any] = {
            "error_id": f"ERR_{int(error_info.timestamp.timestamp())}_{self._error_count}",
            "operation": error_info.context.operation,
            "exception_type": error_info.exception_type,
            "exception_message": error_info.exception_message,
            "category": error_info.category.value,
            "severity": error_info.severity.value,
            "timestamp": error_info.timestamp.isoformat(),
            "parameters": error_info.context.parameters,
            "traceback": error_info.traceback,
        }
        if error_info.system_context:
            log_data["system_context"] = {
                "platform": error_info.system_context.platform,
                "python_version": error_info.system_context.python_version,
                "working_directory": error_info.system_context.working_directory,
                "memory_usage": error_info.system_context.memory_usage,
            }
        log_message = f"Error in {error_info.context.operation}: {error_info.exception_message}"
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra=log_data)
        elif error_info.severity in (ErrorSeverity.HIGH, ErrorSeverity.MEDIUM):
            console.print(log_message)
        else:
            console.print(log_message)
        self._update_error_metrics(error_info.category, error_info.severity)

    def get_system_context(self) -> SystemContext:
        """Collect diagnostic data about the current runtime environment.

        Returns:
            SystemContext: Snapshot of relevant host details.
        """
        try:
            context_data: dict[str, Any] = {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "working_directory": os.getcwd(),
                "environment_variables": self._get_relevant_env_vars(),
                "memory_usage": self._get_memory_usage(),
                "disk_space": self._get_disk_space(),
            }
            return SystemContext(context_data)
        except Exception as e:
            console.print(f"Failed to gather system context: {e}")
            return SystemContext(
                {"platform": "unknown", "python_version": "unknown", "error": f"Context gathering failed: {e}"}
            )

    def log_performance_metric(self, operation: str, duration_seconds: float) -> None:
        """Record basic timing information for an operation.

        Args:
            operation: Name of the monitored operation.
            duration_seconds: Duration measured in seconds.
        """
        if operation not in self._performance_metrics:
            self._performance_metrics[operation] = []
        self._performance_metrics[operation].append(duration_seconds)
        if duration_seconds > 5.0:
            console.print(f"Slow operation detected: {operation} took {duration_seconds:.2f}s")

    def get_error_statistics(self) -> dict[str, Any]:
        """Return aggregated error and performance statistics.

        Returns:
            dict[str, Any]: Summary of counts and performance metrics.
        """
        return {
            "total_errors": self._error_count,
            "error_by_category": getattr(self, "_category_counts", {}),
            "error_by_severity": getattr(self, "_severity_counts", {}),
            "performance_metrics": {
                operation: {
                    "count": len(durations),
                    "avg_duration": sum(durations) / len(durations),
                    "max_duration": max(durations),
                    "min_duration": min(durations),
                }
                for (operation, durations) in self._performance_metrics.items()
            },
        }

    def _setup_logger(self, log_file: str | None = None) -> None:
        """Ensure the unified logger is initialized for this adapter."""
        # Doppelgänger handlers are not added here; configuration is delegated to the unified logger.
        return

    def _get_relevant_env_vars(self) -> dict[str, str]:
        """Collect a subset of environment variables useful for debugging."""
        relevant_prefixes = ["NOVEL_", "PROJECT_", "PYTHON", "PATH"]
        return {
            key: value
            for (key, value) in os.environ.items()
            if any(key.startswith(prefix) for prefix in relevant_prefixes)
        }

    def _get_memory_usage(self) -> str:
        """Return a human readable description of process memory usage."""
        try:
            if _psutil is None:
                raise ImportError
            process = _psutil.Process()
            memory_info = process.memory_info()
            return f"{memory_info.rss / 1024 / 1024:.1f} MB"
        except ImportError:
            return "psutil not available"
        except Exception as e:
            return f"memory check failed: {e}"

    def _get_disk_space(self) -> str:
        """Return a human readable description of disk space."""
        try:
            (total, used, free) = shutil.disk_usage(".")
            return f"Free: {free / 1024 / 1024 / 1024:.1f} GB"
        except Exception as e:
            return f"disk check failed: {e}"

    def _update_error_metrics(self, category: ErrorCategory, severity: ErrorSeverity) -> None:
        """Update internal error metrics"""
        if not hasattr(self, "_category_counts"):
            self._category_counts = {}
        if not hasattr(self, "_severity_counts"):
            self._severity_counts = {}
        category_name = category.value
        severity_name = severity.value
        self._category_counts[category_name] = self._category_counts.get(category_name, 0) + 1
        self._severity_counts[severity_name] = self._severity_counts.get(severity_name, 0) + 1

    def create_error_info(
        self, exception: Exception, category: ErrorCategory, severity: ErrorSeverity, context: ErrorContext
    ) -> ErrorInfo:
        """Create ErrorInfo with system context

        Args:
            exception: Exception that occurred
            category: Error category
            severity: Error severity
            context: Error context

        Returns:
            ErrorInfo: Complete error information with system context
        """
        system_context = self.get_system_context()
        return ErrorInfo(
            exception=exception, category=category, severity=severity, context=context, system_context=system_context
        )
