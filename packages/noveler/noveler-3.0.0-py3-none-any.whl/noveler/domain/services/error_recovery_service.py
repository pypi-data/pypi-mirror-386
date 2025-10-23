"""
Error Recovery Service - Pure Domain Service

Responsible for business logic around error recovery strategies.
Contains domain rules for determining recovery approaches.
"""

from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

from noveler.domain.services.error_classification_service import ErrorCategory, ErrorSeverity
from noveler.domain.services.error_reporting_service import ErrorContext

T = TypeVar("T")


class RecoveryStrategy(Enum):
    """Domain-defined recovery strategies"""

    NONE = "none"
    RETRY = "retry"
    FALLBACK = "fallback"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    USER_INTERVENTION = "user_intervention"
    SYSTEM_RESTART = "system_restart"


class RecoveryPlan:
    """Domain entity representing recovery plan"""

    def __init__(
        self,
        strategy: RecoveryStrategy,
        max_attempts: int = 1,
        delay_seconds: float = 0,
        fallback_data: Any | None = None,
        requires_user_action: bool = False,
        escalation_required: bool = False,
    ) -> None:
        self.strategy = strategy
        self.max_attempts = max_attempts
        self.delay_seconds = delay_seconds
        self.fallback_data = fallback_data
        self.requires_user_action = requires_user_action
        self.escalation_required = escalation_required


class RecoveryResult:
    """Domain entity representing recovery attempt result"""

    def __init__(
        self,
        success: bool,
        data: Any | None = None,
        attempts_made: int = 0,
        strategy_used: RecoveryStrategy | None = None,
        fallback_used: bool = False,
        error_message: str | None = None,
    ) -> None:
        self.success = success
        self.data = data
        self.attempts_made = attempts_made
        self.strategy_used = strategy_used
        self.fallback_used = fallback_used
        self.error_message = error_message


class ErrorRecoveryService:
    """
    Domain service for error recovery business logic

    Responsibilities:
    - Determine appropriate recovery strategies based on business rules
    - Execute recovery plans with domain-specific logic
    - Manage recovery attempt limits and business constraints
    """

    def __init__(self) -> None:
        self._recovery_strategies: dict[ErrorCategory, RecoveryStrategy] = {
            ErrorCategory.VALIDATION: RecoveryStrategy.USER_INTERVENTION,
            ErrorCategory.BUSINESS_LOGIC: RecoveryStrategy.USER_INTERVENTION,
            ErrorCategory.INFRASTRUCTURE: RecoveryStrategy.RETRY,
            ErrorCategory.EXTERNAL_SERVICE: RecoveryStrategy.RETRY,
            ErrorCategory.SYSTEM: RecoveryStrategy.SYSTEM_RESTART,
        }

        self._max_retry_attempts: dict[ErrorCategory, int] = {
            ErrorCategory.INFRASTRUCTURE: 3,
            ErrorCategory.EXTERNAL_SERVICE: 5,
            ErrorCategory.SYSTEM: 1,
        }

    def create_recovery_plan(
        self, exception: Exception, category: ErrorCategory, severity: ErrorSeverity, context: ErrorContext
    ) -> RecoveryPlan:
        """Create recovery plan based on business rules

        Args:
            exception: Exception that occurred
            category: Error category
            severity: Error severity
            context: Error context

        Returns:
            RecoveryPlan: Business-defined recovery plan
        """
        strategy = self._determine_recovery_strategy(exception, category, severity)

        # Business rules for recovery parameters
        max_attempts = self._get_max_attempts(category, severity)
        delay = self._get_retry_delay(category, severity)
        requires_user = self._requires_user_intervention(category, severity)
        needs_escalation = self._needs_escalation(severity)

        return RecoveryPlan(
            strategy=strategy,
            max_attempts=max_attempts,
            delay_seconds=delay,
            requires_user_action=requires_user,
            escalation_required=needs_escalation,
            fallback_data=self._get_fallback_data(exception, context),
        )

    def execute_recovery_plan(
        self, plan: RecoveryPlan, original_operation: Callable[[], T], fallback_operation: Callable[[], T] | None = None
    ) -> RecoveryResult:
        """Execute recovery plan with business constraints

        Args:
            plan: Recovery plan to execute
            original_operation: Original operation to retry
            fallback_operation: Fallback operation if available

        Returns:
            RecoveryResult: Result of recovery attempt
        """
        if plan.strategy == RecoveryStrategy.NONE:
            return RecoveryResult(success=False, strategy_used=RecoveryStrategy.NONE)

        if plan.strategy == RecoveryStrategy.USER_INTERVENTION:
            return self._handle_user_intervention_recovery(plan)

        if plan.strategy == RecoveryStrategy.RETRY:
            return self._execute_retry_recovery(plan, original_operation)

        if plan.strategy == RecoveryStrategy.FALLBACK:
            return self._execute_fallback_recovery(plan, fallback_operation)

        if plan.strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            return self._execute_degradation_recovery(plan)

        return RecoveryResult(success=False, strategy_used=plan.strategy)

    def can_recover_from_error(self, exception: Exception, category: ErrorCategory, severity: ErrorSeverity) -> bool:
        """Determine if error is recoverable based on business rules

        Args:
            exception: Exception to assess
            category: Error category
            severity: Error severity

        Returns:
            bool: True if recovery is possible
        """
        # Critical system failures are typically not recoverable
        if severity == ErrorSeverity.CRITICAL:
            return isinstance(exception, ConnectionError | FileNotFoundError)

        # Business rules for recoverability by category
        recoverable_categories = {
            ErrorCategory.VALIDATION,  # User can fix input
            ErrorCategory.INFRASTRUCTURE,  # Resources may become available
            ErrorCategory.EXTERNAL_SERVICE,  # Services may recover
        }

        return category in recoverable_categories

    def _determine_recovery_strategy(
        self, exception: Exception, category: ErrorCategory, severity: ErrorSeverity
    ) -> RecoveryStrategy:
        """Determine appropriate recovery strategy based on business rules"""

        # Critical errors may need system restart
        if severity == ErrorSeverity.CRITICAL:
            if isinstance(exception, KeyboardInterrupt | SystemExit):
                return RecoveryStrategy.NONE
            return RecoveryStrategy.SYSTEM_RESTART

        # Specific exception handling
        if isinstance(exception, FileNotFoundError):
            return RecoveryStrategy.FALLBACK

        if isinstance(exception, ConnectionError):
            return RecoveryStrategy.RETRY

        # Default category-based strategy
        return self._recovery_strategies.get(category, RecoveryStrategy.USER_INTERVENTION)

    def _get_max_attempts(self, category: ErrorCategory, severity: ErrorSeverity) -> int:
        """Get maximum recovery attempts based on business rules"""
        if severity == ErrorSeverity.CRITICAL:
            return 1  # Don't retry critical failures extensively

        return self._max_retry_attempts.get(category, 1)

    def _get_retry_delay(self, category: ErrorCategory, severity: ErrorSeverity) -> float:
        """Get retry delay based on business impact"""
        if category == ErrorCategory.EXTERNAL_SERVICE:
            return 2.0  # Give external services time to recover

        if severity == ErrorSeverity.HIGH:
            return 1.0  # Shorter delay for high impact errors

        return 0.5  # Default delay

    def _requires_user_intervention(self, category: ErrorCategory, severity: ErrorSeverity) -> bool:
        """Determine if user intervention is required"""
        user_intervention_categories = {ErrorCategory.VALIDATION, ErrorCategory.BUSINESS_LOGIC}

        return category in user_intervention_categories

    def _needs_escalation(self, severity: ErrorSeverity) -> bool:
        """Determine if error needs escalation"""
        return severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]

    def _get_fallback_data(self, exception: Exception, context: ErrorContext) -> Any | None:
        """Get fallback data based on business rules"""
        # Provide safe defaults for certain error types
        if isinstance(exception, FileNotFoundError):
            return {"status": "file_not_found", "use_default": True}

        if isinstance(exception, ConnectionError):
            return {"status": "offline_mode", "cached_data": True}

        return None

    def _handle_user_intervention_recovery(self, plan: RecoveryPlan) -> RecoveryResult:
        """Handle recovery requiring user intervention"""
        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.USER_INTERVENTION,
            error_message="User intervention required to resolve this error",
        )

    def _execute_retry_recovery(self, plan: RecoveryPlan, operation: Callable[[], T] | None) -> RecoveryResult:
        """Execute retry recovery strategy"""
        if not operation:
            return RecoveryResult(
                success=False, strategy_used=RecoveryStrategy.RETRY, error_message="No operation provided for retry"
            )

        for attempt in range(plan.max_attempts):
            try:
                if attempt > 0 and plan.delay_seconds > 0:
                    # In real implementation, would use time.sleep
                    # Here we just simulate the delay
                    pass

                result = operation()
                return RecoveryResult(
                    success=True, data=result, attempts_made=attempt + 1, strategy_used=RecoveryStrategy.RETRY
                )

            except Exception:
                if attempt == plan.max_attempts - 1:
                    # Last attempt failed
                    return RecoveryResult(
                        success=False,
                        attempts_made=attempt + 1,
                        strategy_used=RecoveryStrategy.RETRY,
                        error_message=f"Retry failed after {plan.max_attempts} attempts",
                    )

        return RecoveryResult(success=False, strategy_used=RecoveryStrategy.RETRY)

    def _execute_fallback_recovery(
        self, plan: RecoveryPlan, fallback_operation: Callable[[], T] | None
    ) -> RecoveryResult:
        """Execute fallback recovery strategy"""
        if fallback_operation:
            try:
                result = fallback_operation()
                return RecoveryResult(
                    success=True, data=result, strategy_used=RecoveryStrategy.FALLBACK, fallback_used=True
                )

            except Exception as e:
                return RecoveryResult(
                    success=False,
                    strategy_used=RecoveryStrategy.FALLBACK,
                    error_message=f"Fallback operation failed: {e!s}",
                )

        # Use fallback data if available
        if plan.fallback_data:
            return RecoveryResult(
                success=True, data=plan.fallback_data, strategy_used=RecoveryStrategy.FALLBACK, fallback_used=True
            )

        return RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.FALLBACK,
            error_message="No fallback operation or data available",
        )

    def _execute_degradation_recovery(self, plan: RecoveryPlan) -> RecoveryResult:
        """Execute graceful degradation recovery"""
        # Provide minimal functionality
        degraded_data: dict[str, Any] = {
            "status": "degraded_mode",
            "functionality": "limited",
            "message": "Operating with reduced functionality",
        }

        return RecoveryResult(success=True, data=degraded_data, strategy_used=RecoveryStrategy.GRACEFUL_DEGRADATION)
