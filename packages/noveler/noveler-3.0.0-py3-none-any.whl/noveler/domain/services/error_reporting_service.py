"""
Error Reporting Service - Pure Domain Service

Responsible for generating business-focused error reports and recovery suggestions.
"""

from datetime import datetime
from typing import Any

from noveler.domain.services.error_classification_service import ErrorCategory, ErrorSeverity
from noveler.domain.value_objects.project_time import project_now


class ErrorContext:
    """Domain entity representing error context"""

    def __init__(
        self,
        operation: str,
        parameters: dict[str, Any],
        timestamp: datetime | None = None,
        system_context: dict[str, Any] | None = None,
    ) -> None:
        self.operation = operation
        self.parameters = parameters
        self.timestamp = timestamp or project_now().datetime
        self.system_context = system_context or {}


class ErrorResult:
    """Domain entity representing error handling result"""

    def __init__(
        self,
        success: bool,
        data: Any = None,
        error_message: str | None = None,
        error_code: str | None = None,
        severity: ErrorSeverity | None = None,
        category: ErrorCategory | None = None,
        context: ErrorContext | None = None,
        recovery_suggestions: list[str] | None = None,
    ) -> None:
        self.success = success
        self.data = data
        self.error_message = error_message
        self.error_code = error_code
        self.severity = severity
        self.category = category
        self.context = context
        self.recovery_suggestions = recovery_suggestions or []


class BusinessErrorResult:
    """Business error result for application layer"""

    def __init__(
        self, user_message: str, technical_details: str, recovery_suggestions: list[str], error_code: str
    ) -> None:
        self.user_message = user_message
        self.technical_details = technical_details
        self.recovery_suggestions = recovery_suggestions
        self.error_code = error_code


class ErrorReportingService:
    """
    Domain service for generating business-focused error reports

    Responsibilities:
    - Generate user-friendly recovery suggestions
    - Create business error results
    - Format error information for business context
    """

    def generate_recovery_suggestions(self, exception: Exception, category: ErrorCategory) -> list[str]:
        """Generate actionable recovery suggestions for users

        Args:
            exception: Exception that occurred
            category: Business category of the error

        Returns:
            list[str]: User-friendly recovery suggestions
        """
        suggestions = []

        # Category-specific guidance based on business impact
        category_guidance = {
            ErrorCategory.VALIDATION: [
                "Please check input parameters are valid",
                "Verify data format meets requirements",
                "Review validation constraints in documentation",
            ],
            ErrorCategory.INFRASTRUCTURE: [
                "Please verify file paths exist and are accessible",
                "Check system permissions and disk space",
                "Ensure required directories are created",
                "Verify system resources are available",
            ],
            ErrorCategory.EXTERNAL_SERVICE: [
                "Please check network connectivity",
                "Verify external service availability",
                "Consider retrying the operation after a brief delay",
                "Check service status pages for known issues",
            ],
            ErrorCategory.BUSINESS_LOGIC: [
                "Please review business rule constraints",
                "Verify data meets domain requirements",
                "Check for conflicting operations",
                "Ensure all prerequisite conditions are met",
            ],
            ErrorCategory.SYSTEM: [
                "Please contact system administrator",
                "Check system logs for additional details",
                "Consider restarting the application",
                "Report this issue with full context",
            ],
        }

        suggestions.extend(category_guidance.get(category, []))

        # Exception-specific actionable advice
        if isinstance(exception, FileNotFoundError):
            file_path = str(exception).split("'")[1] if "'" in str(exception) else "unknown"
            suggestions.append(f"Create missing file or verify path: {file_path}")

        if isinstance(exception, ImportError):
            suggestions.append("Install missing dependencies with pip install")
            suggestions.append("Check PYTHONPATH includes required modules")

        if isinstance(exception, PermissionError):
            suggestions.append("Check file/directory permissions")
            suggestions.append("Run with appropriate user privileges")

        if isinstance(exception, ConnectionError):
            suggestions.append("Verify network connectivity and firewall settings")
            suggestions.append("Check if target service is running")

        return suggestions

    def create_business_error_result(
        self,
        exception: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: dict[str, Any],
        recovery_result: Any | None = None,
    ) -> BusinessErrorResult:
        """Create business error result for application layer

        Args:
            exception: Exception that occurred
            category: Error category
            severity: Error severity
            context: Error context
            recovery_result: Optional recovery result

        Returns:
            BusinessErrorResult: Business error result
        """
        user_message = self._create_user_friendly_message(exception, category, severity)
        technical_details = f"{type(exception).__name__}: {exception!s}"
        recovery_suggestions = self.generate_recovery_suggestions(exception, category)
        error_code = f"{category.value.upper()}_{severity.value.upper()}"

        return BusinessErrorResult(
            user_message=user_message,
            technical_details=technical_details,
            recovery_suggestions=recovery_suggestions,
            error_code=error_code,
        )

    def create_business_error_result_legacy(
        self,
        message: str,
        operation: str,
        parameters: dict[str, Any],
        category: ErrorCategory = ErrorCategory.BUSINESS_LOGIC,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        suggestions: list[str] | None = None,
    ) -> ErrorResult:
        """Create structured business error result

        Args:
            message: Business-friendly error message
            operation: Operation that failed
            parameters: Operation parameters
            category: Error category
            severity: Business impact severity
            suggestions: Recovery suggestions

        Returns:
            ErrorResult: Structured error result for business layer
        """
        context = ErrorContext(operation=operation, parameters=parameters, timestamp=project_now().datetime)

        return ErrorResult(
            success=False,
            error_message=message,
            error_code=f"{category.value}_business_error",
            severity=severity,
            category=category,
            context=context,
            recovery_suggestions=suggestions or ["Please review business requirements"],
        )

    def create_success_result(self, data: Any, operation: str, parameters: dict[str, Any]) -> ErrorResult:
        """Create structured success result

        Args:
            data: Successful operation result
            operation: Operation that succeeded
            parameters: Operation parameters

        Returns:
            ErrorResult: Structured success result
        """
        context = ErrorContext(operation=operation, parameters=parameters, timestamp=project_now().datetime)

        return ErrorResult(success=True, data=data, context=context)

    def format_error_summary(self, error_result: ErrorResult) -> str:
        """Format error for business stakeholder communication

        Args:
            error_result: Error result to format

        Returns:
            str: Business-friendly error summary
        """
        if error_result.success:
            return f"Operation '{error_result.context.operation}' completed successfully"

        severity_label = error_result.severity.value.upper() if error_result.severity else "UNKNOWN"
        category_label = error_result.category.value.replace("_", " ").title() if error_result.category else "Unknown"

        summary = f"[{severity_label}] {category_label} Error in '{error_result.context.operation}'"
        summary += f"\nIssue: {error_result.error_message}"

        if error_result.recovery_suggestions:
            summary += "\nRecommended Actions:"
            for i, suggestion in enumerate(error_result.recovery_suggestions, 1):
                summary += f"\n  {i}. {suggestion}"

        return summary

    def create_error_report(
        self,
        exception: Exception,
        operation: str,
        parameters: dict[str, Any],
        category: ErrorCategory,
        severity: ErrorSeverity,
        recovery_suggestions: list[str],
    ) -> dict[str, Any]:
        """Create comprehensive error report for analysis

        Args:
            exception: Exception that occurred
            operation: Operation name
            parameters: Operation parameters
            category: Error category
            severity: Error severity
            recovery_suggestions: Recovery suggestions

        Returns:
            dict: Comprehensive error report
        """
        return {
            "error_id": f"{category.value}_{int(project_now().datetime.timestamp())}",
            "operation": operation,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "category": category.value,
            "severity": severity.value,
            "business_impact": self._get_business_impact_level(severity),
            "recovery_suggestions": recovery_suggestions,
            "parameters": parameters,
            "timestamp": project_now().datetime.isoformat(),
            "requires_immediate_attention": severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL],
        }

    def _get_business_impact_level(self, severity: ErrorSeverity) -> str:
        """Get business impact level description

        Args:
            severity: Error severity

        Returns:
            str: Business impact description
        """
        impact_levels = {
            ErrorSeverity.LOW: "Minor disruption, low priority fix",
            ErrorSeverity.MEDIUM: "Moderate impact, schedule fix within days",
            ErrorSeverity.HIGH: "Significant impact, requires urgent attention",
            ErrorSeverity.CRITICAL: "Critical failure, immediate intervention required",
        }

        return impact_levels.get(severity, "Unknown impact level")

    def _create_user_friendly_message(
        self, exception: Exception, category: ErrorCategory, severity: ErrorSeverity
    ) -> str:
        """Create user-friendly error message

        Args:
            exception: Exception that occurred
            category: Error category
            severity: Error severity

        Returns:
            str: User-friendly error message
        """
        # Ensure the message always contains 'Error:' for downstream checks/tests
        severity_prefix = "Error:"

        category_context = {
            ErrorCategory.VALIDATION: "Input validation failed",
            ErrorCategory.INFRASTRUCTURE: "System resource issue",
            ErrorCategory.EXTERNAL_SERVICE: "External service unavailable",
            ErrorCategory.BUSINESS_LOGIC: "Business rule violation",
            ErrorCategory.SYSTEM: "System error occurred",
        }.get(category, "An error occurred")

        return f"{severity_prefix} {category_context}. {exception!s}"
