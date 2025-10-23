#!/usr/bin/env python3
"""
Error handling workflow orchestrator

This application layer orchestrator coordinates error handling workflows
between domain services and infrastructure adapters, implementing comprehensive
error management for the novel writing system.

Follows DDD principles:
    - Application layer responsibilities only
- Workflow coordination for error handling processes
- Business process management for error recovery
"""

import contextlib
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol

from noveler.domain.services.error_classification_service import (
    ErrorCategory,
    ErrorClassificationService,
    ErrorSeverity,
)
from noveler.domain.services.error_recovery_service import ErrorRecoveryService, RecoveryPlan, RecoveryResult
from noveler.domain.services.error_reporting_service import BusinessErrorResult, ErrorReportingService
from noveler.domain.value_objects.execution_result import ExecutionResult

# DDD準拠: インフラストラクチャ層への直接依存を削除
# ErrorLoggingAdapterプロトコル定義でアーキテクチャ層分離を保持


class ErrorLoggingProtocol(Protocol):
    """エラーログ記録プロトコル（インフラ層依存解消）"""

    def log_error(self, exception: Exception, context: dict[str, Any], operation_name: str) -> None:
        """エラーログ記録"""
        ...

    def is_available(self) -> bool:
        """ロギング機能利用可能性チェック"""
        ...


class ErrorHandlingStrategy(Enum):
    """Error handling strategy options"""

    IMMEDIATE_RECOVERY = "immediate_recovery"
    LOGGING_ONLY = "logging_only"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    COMPREHENSIVE = "comprehensive"


@dataclass
class ErrorHandlingRequest:
    """Request for error handling workflow"""

    exception: Exception
    context: dict[str, Any]
    operation_name: str
    strategy: ErrorHandlingStrategy = ErrorHandlingStrategy.COMPREHENSIVE
    retry_attempts: int = 3
    enable_recovery: bool = True
    enable_reporting: bool = True


@dataclass
class ErrorHandlingResult:
    """Result of error handling workflow"""

    success: bool
    error_category: ErrorCategory | None = None
    error_severity: ErrorSeverity | None = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_plan: RecoveryPlan | None = None
    recovery_result: RecoveryResult | None = None
    business_error_result: BusinessErrorResult | None = None
    logged: bool = False
    processing_time_ms: int | None = None
    error_message: str | None = None


class ErrorHandlingOrchestrator:
    """
    Application orchestrator for error handling workflow

    Responsibilities:
    - Coordinate error classification, recovery, and reporting
    - Implement error handling business workflows
    - Manage error handling strategies and policies
    - Integrate technical logging with business error management
    """

    def __init__(
        self,
        classification_service: ErrorClassificationService,
        recovery_service: ErrorRecoveryService,
        reporting_service: ErrorReportingService,
        logging_adapter: ErrorLoggingProtocol | None = None,
    ) -> None:
        """Initialize error handling orchestrator

        Args:
            classification_service: Domain service for error classification
            recovery_service: Domain service for error recovery
            reporting_service: Domain service for error reporting
            logging_adapter: Infrastructure adapter for technical logging
        """
        self._classification_service = classification_service
        self._recovery_service = recovery_service
        self._reporting_service = reporting_service
        self._logging_adapter = logging_adapter

    def handle_error(self, request: ErrorHandlingRequest) -> ErrorHandlingResult:
        """Execute comprehensive error handling workflow

        Args:
            request: Error handling request

        Returns:
            ErrorHandlingResult: Complete error handling result
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Phase 1: Error Classification
            error_category = self._classification_service.classify_error(request.exception)
            error_severity = self._classification_service.determine_severity(request.exception, request.context)

            # Phase 2: Technical Logging (Infrastructure)
            logged = self._log_error_technical(request, error_category, error_severity)

            # Phase 3: Recovery Attempt (if enabled and recoverable)
            recovery_attempted = False
            recovery_successful = False
            recovery_plan = None
            recovery_result = None

            if request.enable_recovery and self._should_attempt_recovery(error_severity, request.strategy):
                recovery_attempted = True
                recovery_plan = self._recovery_service.create_recovery_plan(
                    request.exception, error_category, request.context
                )

                if recovery_plan:
                    recovery_result = self._recovery_service.execute_recovery_plan(
                        recovery_plan, request.retry_attempts
                    )

                    recovery_successful = recovery_result.success if recovery_result else False

            # Phase 4: Business Error Reporting (if enabled)
            business_error_result = None
            if request.enable_reporting:
                business_error_result = self._reporting_service.create_business_error_result(
                    request.exception, error_category, error_severity, request.context, recovery_result
                )

            # Calculate processing time
            end_time = datetime.now(timezone.utc)
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)

            return ErrorHandlingResult(
                success=True,
                error_category=error_category,
                error_severity=error_severity,
                recovery_attempted=recovery_attempted,
                recovery_successful=recovery_successful,
                recovery_plan=recovery_plan,
                recovery_result=recovery_result,
                business_error_result=business_error_result,
                logged=logged,
                processing_time_ms=processing_time_ms,
            )

        except Exception as orchestrator_error:
            # Handle errors in the error handling process itself
            end_time = datetime.now(timezone.utc)
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Log the meta-error
            if self._logging_adapter:
                with contextlib.suppress(Exception):
                    self._logging_adapter.log_error(
                        orchestrator_error,
                        {"original_error": str(request.exception), "operation": "error_handling"},
                        "ERROR_ORCHESTRATOR",
                    )

            return ErrorHandlingResult(
                success=False,
                error_message=f"Error handling orchestration failed: {orchestrator_error!s}",
                processing_time_ms=processing_time_ms,
            )

    def handle_error_simple(
        self, exception: Exception, context: dict[str, Any], operation_name: str
    ) -> ErrorHandlingResult:
        """Simplified error handling with default strategy

        Args:
            exception: Exception to handle
            context: Error context
            operation_name: Name of the operation that failed

        Returns:
            ErrorHandlingResult: Error handling result
        """
        request = ErrorHandlingRequest(
            exception=exception,
            context=context,
            operation_name=operation_name,
            strategy=ErrorHandlingStrategy.COMPREHENSIVE,
        )

        return self.handle_error(request)

    def get_error_handling_capabilities(self) -> dict[str, Any]:
        """Get information about error handling capabilities

        Returns:
            dict: Error handling system capabilities
        """
        return {
            "strategies": [strategy.value for strategy in ErrorHandlingStrategy],
            "classification": {
                "categories": [category.value for category in ErrorCategory],
                "severities": [severity.value for severity in ErrorSeverity],
            },
            "recovery": {
                "enabled": True,
                "max_retry_attempts": 10,
                "supported_error_types": self._recovery_service.get_supported_error_types(),
            },
            "reporting": {"enabled": True, "business_error_tracking": True, "user_friendly_messages": True},
            "logging": {
                "technical_logging": self._logging_adapter.is_available() if self._logging_adapter else False,
                "structured_logging": True,
                "correlation_tracking": True,
            },
        }

    def validate_error_handling_context(self, context: dict[str, Any]) -> list[str]:
        """Validate error handling context data

        Args:
            context: Context data to validate

        Returns:
            list[str]: List of validation errors (empty if valid)
        """
        errors: list[Any] = []

        # Check for required context elements
        required_elements = ["operation_id", "user_context"]
        errors.extend([
            f"Missing required context element: {element}"
            for element in required_elements
            if element not in context
        ])

        # Validate user context structure
        if "user_context" in context:
            user_context = context["user_context"]
            if not isinstance(user_context, dict):
                errors.append("User context must be a dictionary")
            elif "operation_name" not in user_context:
                errors.append("User context must include operation_name")

        return errors

    def _log_error_technical(
        self, request: ErrorHandlingRequest, error_category: ErrorCategory, error_severity: ErrorSeverity
    ) -> bool:
        """Log error using technical logging adapter

        Args:
            request: Error handling request
            error_category: Classified error category
            error_severity: Determined error severity

        Returns:
            bool: True if logging was successful
        """
        try:
            # Enhance context with classification results
            enhanced_context = {
                **request.context,
                "error_category": error_category.value,
                "error_severity": error_severity.value,
                "operation_name": request.operation_name,
                "strategy": request.strategy.value,
            }

            if self._logging_adapter:
                self._logging_adapter.log_error(request.exception, enhanced_context, request.operation_name)

            return True

        except Exception:
            return False

    def _should_attempt_recovery(self, error_severity: ErrorSeverity, strategy: ErrorHandlingStrategy) -> bool:
        """Determine if recovery should be attempted

        Args:
            error_severity: Error severity level
            strategy: Error handling strategy

        Returns:
            bool: True if recovery should be attempted
        """
        if strategy == ErrorHandlingStrategy.LOGGING_ONLY:
            return False

        if strategy == ErrorHandlingStrategy.IMMEDIATE_RECOVERY:
            return True

        # For comprehensive and graceful degradation strategies
        return self._classification_service.is_recoverable_error(error_severity)

    def create_error_summary(self, result: ErrorHandlingResult) -> dict[str, Any]:
        """Create a summary of error handling results

        Args:
            result: Error handling result

        Returns:
            dict: Error handling summary
        """
        summary = {
            "handling_successful": result.success,
            "error_classified": result.error_category is not None,
            "recovery_attempted": result.recovery_attempted,
            "recovery_successful": result.recovery_successful,
            "logged": result.logged,
            "processing_time_ms": result.processing_time_ms,
        }

        if result.error_category:
            summary["error_category"] = result.error_category.value

        if result.error_severity:
            summary["error_severity"] = result.error_severity.value

        if result.business_error_result:
            summary["user_message"] = result.business_error_result.user_message
            summary["suggestions"] = result.business_error_result.recovery_suggestions

        if result.error_message:
            summary["error_message"] = result.error_message

        return summary

    def execute_with_error_handling(
        self,
        operation: str,
        func: callable,
        parameters: dict[str, Any],
        fallback_func: Callable | None = None,
        enable_recovery: bool = True,
        enable_reporting: bool = True,
    ) -> "ExecutionResult":
        """Execute a function with comprehensive error handling

        Args:
            operation: Name of the operation being executed
            func: Function to execute
            parameters: Parameters for the function
            fallback_func: Optional fallback function if main function fails
            enable_recovery: Whether to attempt error recovery
            enable_reporting: Whether to generate error reports

        Returns:
            ExecutionResult: Result of the execution with error handling
        """

        @dataclass
        class ExecutionResult:
            success: bool
            data: Any | None = None
            error_message: str | None = None
            context: dict[str, Any] | None = None
            suggestions: list[str] = None

            def __post_init__(self) -> None:
                if self.suggestions is None:
                    self.suggestions = []

        # Create execution context
        context = {
            "operation": operation,
            "parameters": parameters,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # Execute the main function
            result = func()
            return ExecutionResult(success=True, data=result, context=context)

        except Exception as e:
            # Handle the error using the orchestrator
            error_request = ErrorHandlingRequest(
                exception=e,
                context=context,
                operation_name=operation,
                enable_recovery=enable_recovery,
                enable_reporting=enable_reporting,
            )

            handling_result = self.handle_error(error_request)

            # Try fallback function if available and recovery didn't work
            if fallback_func and not handling_result.recovery_successful:
                with contextlib.suppress(Exception):
                    fallback_result = fallback_func()
                    return ExecutionResult(
                        success=True,
                        data=fallback_result,
                        context=context,
                        suggestions=["Used fallback function due to main function failure"],
                    )

            # Generate suggestions from business error result
            suggestions = []
            if handling_result.business_error_result:
                suggestions = handling_result.business_error_result.recovery_suggestions or []

            return ExecutionResult(
                success=handling_result.recovery_successful,
                data=handling_result.recovery_result.data if handling_result.recovery_result else None,
                error_message=str(e),
                context=context,
                suggestions=suggestions,
            )

    def handle_business_error(
        self, message: str, operation: str, parameters: dict[str, Any], suggestions: list[str] | None = None
    ) -> "ExecutionResult":
        """Handle a business error scenario

        Args:
            message: Error message
            operation: Operation name
            parameters: Operation parameters
            suggestions: Recovery suggestions

        Returns:
            ExecutionResult: Business error result
        """

        @dataclass
        class ExecutionResult:
            success: bool
            data: Any | None = None
            error_message: str | None = None
            context: dict[str, Any] | None = None
            suggestions: list[str] = None

            def __post_init__(self) -> None:
                if self.suggestions is None:
                    self.suggestions = []

        context = {
            "operation": operation,
            "parameters": parameters,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Log the business error
        if self._logging_adapter:
            with contextlib.suppress(Exception):
                self._logging_adapter.log_error(ValueError(message), context, operation)


        return ExecutionResult(success=False, error_message=message, context=context, suggestions=suggestions or [])

    def assess_error_recoverability(self, exception: Exception, operation_context: dict[str, Any]) -> dict[str, Any]:
        """Assess if an error is recoverable

        Args:
            exception: Exception to assess
            operation_context: Context of the operation

        Returns:
            dict: Recovery assessment
        """
        # Classify the error
        category = self._classification_service.classify_error(exception)
        severity = self._classification_service.determine_severity(exception, operation_context)

        # Determine recoverability
        is_recoverable = self._classification_service.is_recoverable_error(severity)

        # Generate recovery suggestions
        suggestions = []
        if hasattr(self._reporting_service, "generate_recovery_suggestions"):
            suggestions = self._reporting_service.generate_recovery_suggestions(exception, category)

        # Determine max attempts based on error type
        max_attempts = 3 if is_recoverable else 0
        if isinstance(exception, KeyboardInterrupt | SystemExit):
            max_attempts = 0
            is_recoverable = False

        # Determine if user action is required
        requires_user_action = isinstance(exception, KeyboardInterrupt | SystemExit) or severity.value == "critical"

        return {
            "is_recoverable": is_recoverable,
            "category": category.value,
            "severity": severity.value,
            "max_attempts": max_attempts,
            "suggestions": suggestions,
            "requires_user_action": requires_user_action,
        }

    def get_error_statistics(self) -> dict[str, Any]:
        """Get error handling statistics

        Returns:
            dict: Statistics about error handling
        """
        # Basic statistics - in a real implementation this would track actual metrics
        stats = {
            "operations_handled": getattr(self, "_operations_count", 0),
            "recovery_success_rate": 0.75,  # Example rate
            "orchestrator_info": {
                "classification_service": self._classification_service.__class__.__name__,
                "reporting_service": self._reporting_service.__class__.__name__,
                "recovery_service": self._recovery_service.__class__.__name__,
                "logging_adapter": self._logging_adapter.__class__.__name__ if self._logging_adapter else None,
            },
            "infrastructure_metrics": {
                "total_errors": getattr(self, "_total_errors", 0),
                "error_by_category": {},
                "error_by_severity": {},
            },
        }

        # Increment operation count for tracking
        self._operations_count = getattr(self, "_operations_count", 0) + 1

        return stats


class ErrorHandlingOrchestratorFactory:
    """Factory for creating ErrorHandlingOrchestrator instances

    Provides standard configurations for different environments:
    - Default: Full logging and error handling for production
    - Testing: Minimal logging for test environments
    """

    @staticmethod
    def create_default_orchestrator(
        enable_logging: bool = True, log_file: str | None = None
    ) -> ErrorHandlingOrchestrator:
        """Create orchestrator with default production configuration

        Args:
            enable_logging: Whether to enable file logging
            log_file: Optional custom log file path

        Returns:
            ErrorHandlingOrchestrator: Configured orchestrator instance
        """
        # Create domain services
        classification_service = ErrorClassificationService()
        recovery_service = ErrorRecoveryService()
        reporting_service = ErrorReportingService()

        # Create infrastructure adapter
        logging_adapter = None
        if enable_logging:
            # 軽量なファイルロギングアダプター（アプリケーション内蔵の簡易実装）
            from pathlib import Path as _Path  # noqa: PLC0415

            class _BasicFileLoggingAdapter:
                def __init__(self, path: str | None) -> None:
                    default_path = _Path.cwd() / "logs" / "error.log"
                    self._path = _Path(path) if path else default_path
                    try:
                        self._path.parent.mkdir(parents=True, exist_ok=True)
                    except Exception:
                        # フォールバック: /tmp配下
                        self._path = _Path(tempfile.gettempdir()) / "error.log"

                def log_error(self, exception: Exception, context: dict[str, Any], operation_name: str) -> None:
                    msg = f"[{operation_name}] {type(exception).__name__}: {exception!s} | context={context}\n"
                    with contextlib.suppress(Exception):
                        with self._path.open("a", encoding="utf-8") as file_handle:
                            file_handle.write(msg)

                def is_available(self) -> bool:  # noqa: D401
                    return True

            logging_adapter = _BasicFileLoggingAdapter(log_file)

        return ErrorHandlingOrchestrator(
            classification_service=classification_service,
            recovery_service=recovery_service,
            reporting_service=reporting_service,
            logging_adapter=logging_adapter,
        )

    @staticmethod
    def create_testing_orchestrator() -> ErrorHandlingOrchestrator:
        """Create orchestrator for testing with minimal logging

        Returns:
            ErrorHandlingOrchestrator: Test-configured orchestrator instance
        """
        return ErrorHandlingOrchestratorFactory.create_default_orchestrator(enable_logging=False)
