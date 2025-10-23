"""
Error Classification Service - Pure Domain Service

Responsible for classifying exceptions based on business rules.
Follows DDD principles with no external dependencies.
"""

from enum import Enum


class ErrorCategory(Enum):
    """Business-focused error categories"""

    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    INFRASTRUCTURE = "infrastructure"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"


class ErrorSeverity(Enum):
    """Business impact severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorClassificationService:
    """
    Pure domain service for exception classification

    Follows DDD principles:
    - No external dependencies
    - Only business logic
    - Single responsibility: error classification

    This service replaces the classification logic from UnifiedErrorHandlingService
    """

    def classify_error(self, exception: Exception) -> ErrorCategory:
        """Classify exception into business category

        Args:
            exception: Exception to classify

        Returns:
            ErrorCategory: Business classification of the error
        """
        exception_type = type(exception)

        # Validation errors - user input issues
        if exception_type.__name__ in ["ValueError", "ValidationError", "AssertionError"]:
            return ErrorCategory.VALIDATION

        # Infrastructure errors - system resource issues
        if exception_type.__name__ in ["FileNotFoundError", "PermissionError", "OSError"]:
            return ErrorCategory.INFRASTRUCTURE

        # External service errors - third-party dependency issues
        if exception_type.__name__ in ["ConnectionError", "TimeoutError", "HTTPException"]:
            return ErrorCategory.EXTERNAL_SERVICE

        # Business logic errors - domain rule violations
        if hasattr(exception, "__module__") and "domain" in exception.__module__:
            return ErrorCategory.BUSINESS_LOGIC

        # System errors - unexpected technical issues
        return ErrorCategory.SYSTEM

    def determine_severity(self, exception: Exception, context: dict | None = None) -> ErrorSeverity:
        """Determine business impact severity

        Args:
            exception: Exception to assess
            context: Optional context information about the operation

        Returns:
            ErrorSeverity: Business impact level
        """
        # Get the category first
        category = self.classify_error(exception)

        # Base severity mapping by business category
        base_severity_map = {
            ErrorCategory.VALIDATION: ErrorSeverity.MEDIUM,  # User can fix
            ErrorCategory.BUSINESS_LOGIC: ErrorSeverity.HIGH,  # Business rule violation
            ErrorCategory.INFRASTRUCTURE: ErrorSeverity.HIGH,  # System resource issue
            ErrorCategory.EXTERNAL_SERVICE: ErrorSeverity.MEDIUM,  # Temporary service issue
            ErrorCategory.SYSTEM: ErrorSeverity.CRITICAL,  # Unexpected system failure
        }

        severity = base_severity_map.get(category, ErrorSeverity.MEDIUM)

        # Critical system exceptions override category rules
        if isinstance(exception, KeyboardInterrupt | SystemExit):
            return ErrorSeverity.CRITICAL

        # High impact file system and import errors
        if isinstance(exception, FileNotFoundError | ImportError):
            return ErrorSeverity.HIGH

        return severity

    def is_recoverable_error(self, severity: ErrorSeverity) -> bool:
        """Determine if error severity level is potentially recoverable

        Args:
            severity: Error severity level to assess

        Returns:
            bool: True if error might be recoverable
        """
        # Critical errors are never recoverable automatically
        if severity == ErrorSeverity.CRITICAL:
            return False

        # High severity errors may be recoverable with retry strategies
        if severity == ErrorSeverity.HIGH:
            return True

        # Medium and low severity errors are generally recoverable
        return True

    def get_business_context(self, exception: Exception, category: ErrorCategory) -> dict[str, str]:
        """Get business context information for the error

        Args:
            exception: Exception that occurred
            category: Business category

        Returns:
            dict: Business context information
        """
        context = {
            "exception_type": type(exception).__name__,
            "category": category.value,
            "business_impact": self._get_business_impact_description(category),
        }

        # Add specific context for certain error types
        if isinstance(exception, FileNotFoundError):
            context["resource_type"] = "file_system"
            context["user_action_required"] = "verify_file_path"

        if isinstance(exception, ImportError):
            context["resource_type"] = "python_module"
            context["user_action_required"] = "install_dependencies"

        return context

    def _get_business_impact_description(self, category: ErrorCategory) -> str:
        """Get human-readable business impact description

        Args:
            category: Error category

        Returns:
            str: Business impact description
        """
        impact_descriptions = {
            ErrorCategory.VALIDATION: "User input correction needed",
            ErrorCategory.BUSINESS_LOGIC: "Business rule violation detected",
            ErrorCategory.INFRASTRUCTURE: "System resource unavailable",
            ErrorCategory.EXTERNAL_SERVICE: "Third-party service disruption",
            ErrorCategory.SYSTEM: "Critical system failure",
        }

        return impact_descriptions.get(category, "Unknown business impact")
