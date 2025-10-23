"""Domain-level error definitions for the Noveler project."""

from datetime import datetime, timezone


class BaseError(Exception):
    """Base exception that provides structured error payloads."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict | None = None,
        recoverable: bool = True,
        recovery_actions: list[str] | None = None,
        error_level: str = "ERROR",
        context: dict | None = None
    ) -> None:
        """Initialise the base error with structured metadata."""
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.recoverable = recoverable
        self.recovery_actions = recovery_actions or []
        self.error_level = error_level
        self.context = context or {}
        self.timestamp = self._get_current_timestamp()

    def _get_current_timestamp(self) -> str:
        """Return the current timestamp as an ISO 8601 string."""
        return datetime.now(tz=timezone.utc).isoformat()

    def to_dict(self) -> dict:
        """Return a JSON-serialisable representation of the error."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
            "recoverable": self.recoverable,
            "recovery_actions": self.recovery_actions,
            "error_level": self.error_level,
            "context": self.context,
            "timestamp": self.timestamp
        }

    def get_user_friendly_message(self) -> str:
        """Return a user-facing error message that suggests recovery steps."""
        base_msg = f"Error: {self.message}"

        if self.recoverable and self.recovery_actions:
            actions = "\n".join([f"  - {action}" for action in self.recovery_actions])
            base_msg += f"\n\n対処方法:\n{actions}"
        elif not self.recoverable:
            base_msg += "\n\nこのエラーは自動復旧できません。システム管理者にお問い合わせください。"

        return base_msg


class DomainError(BaseError):
    """Errors raised by the domain layer when business rules are violated."""

    def __init__(self, message: str, **kwargs) -> None:
        kwargs.setdefault("error_level", "ERROR")
        kwargs.setdefault("recoverable", True)
        super().__init__(message, **kwargs)


class ApplicationError(BaseError):
    """Errors raised by the application layer during use case execution."""

    def __init__(self, message: str, **kwargs) -> None:
        kwargs.setdefault("error_level", "ERROR")
        kwargs.setdefault("recoverable", True)
        super().__init__(message, **kwargs)


class InfrastructureError(BaseError):
    """Errors raised by the infrastructure layer (I/O, network, persistence)."""

    def __init__(self, message: str, **kwargs) -> None:
        kwargs.setdefault("error_level", "ERROR")
        kwargs.setdefault("recoverable", False)  # インフラエラーは基本的に回復困難
        super().__init__(message, **kwargs)


class ValidationError(DomainError):
    """Raised when validation of domain data fails."""


class BusinessRuleViolationError(DomainError):
    """Raised when a domain business rule is violated."""


class NotFoundError(ApplicationError):
    """Raised when a requested resource cannot be found."""


class ConflictError(ApplicationError):
    """Raised when conflicting data prevents completion."""


class ExternalServiceError(InfrastructureError):
    """Raised when an external service interaction fails."""


class PartialFailureError(ApplicationError):
    """Raised when multi-step operations partially succeed and require recovery."""

    def __init__(
        self,
        message: str,
        failed_steps: list[int | str] | None = None,
        completed_steps: list[int | str] | None = None,
        recovery_point: int | str | None = None,
        **kwargs
    ) -> None:
        self.failed_steps = failed_steps or []
        self.completed_steps = completed_steps or []
        self.recovery_point = recovery_point

        kwargs.setdefault("recoverable", True)
        kwargs.setdefault("recovery_actions", [
            "中断されたステップから再実行してください",
            f"復旧ポイント: {recovery_point}" if recovery_point else None,
            "完了済みステップは自動的にスキップされます"
        ])
        kwargs["recovery_actions"] = [action for action in kwargs["recovery_actions"] if action]

        kwargs.setdefault("details", {}).update({
            "failed_steps": self.failed_steps,
            "completed_steps": self.completed_steps,
            "recovery_point": self.recovery_point
        })

        super().__init__(message, **kwargs)


class InputValidationError(DomainError):
    """Raised when tool input validation fails (invalid or missing data)."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        expected_format: str | None = None,
        actual_value: str | None = None,
        validation_rules: list[str] | None = None,
        **kwargs
    ) -> None:
        self.field = field
        self.expected_format = expected_format
        self.actual_value = actual_value
        self.validation_rules = validation_rules or []

        # 具体的な修正提案を生成
        recovery_actions = []
        if field and expected_format:
            recovery_actions.append(f"{field}は{expected_format}の形式で入力してください")
        if validation_rules:
            recovery_actions.extend([f"検証ルール: {rule}" for rule in validation_rules])
        if not recovery_actions:
            recovery_actions = ["入力内容を確認し、正しい形式で再入力してください"]

        kwargs.setdefault("recoverable", True)
        kwargs.setdefault("recovery_actions", recovery_actions)
        kwargs.setdefault("details", {}).update({
            "field": self.field,
            "expected_format": self.expected_format,
            "actual_value": self.actual_value,
            "validation_rules": self.validation_rules
        })

        super().__init__(message, **kwargs)


class RecoveryError(ApplicationError):
    """Raised when automatic recovery fails and manual steps are required."""

    def __init__(
        self,
        message: str,
        original_error: BaseError | None = None,
        attempted_recoveries: list[str] | None = None,
        fallback_options: list[str] | None = None,
        **kwargs
    ) -> None:
        self.original_error = original_error
        self.attempted_recoveries = attempted_recoveries or []
        self.fallback_options = fallback_options or []

        recovery_actions = ["Automatic recovery failed. Manual intervention is required."]
        if self.fallback_options:
            recovery_actions.extend([f"Fallback option: {option}" for option in self.fallback_options])
        else:
            recovery_actions.append("Please contact the system administrator.")

        kwargs.setdefault("recoverable", False)
        kwargs.setdefault("recovery_actions", recovery_actions)
        kwargs.setdefault("details", {}).update({
            "original_error": original_error.to_dict() if original_error else None,
            "attempted_recoveries": self.attempted_recoveries,
            "fallback_options": self.fallback_options
        })

        super().__init__(message, **kwargs)


class SystemStateError(ApplicationError):
    """Raised when inconsistent system state transitions occur."""

    def __init__(
        self,
        message: str,
        current_state: str | None = None,
        expected_state: str | None = None,
        state_repair_actions: list[str] | None = None,
        **kwargs
    ) -> None:
        self.current_state = current_state
        self.expected_state = expected_state
        self.state_repair_actions = state_repair_actions or []

        recovery_actions = []
        if current_state and expected_state:
            recovery_actions.append(f"Current state: {current_state}")
            recovery_actions.append(f"Expected state: {expected_state}")
        if self.state_repair_actions:
            recovery_actions.extend(self.state_repair_actions)
        else:
            recovery_actions.append("Reset the system state and retry.")

        kwargs.setdefault("recoverable", True)
        kwargs.setdefault("recovery_actions", recovery_actions)
        kwargs.setdefault("details", {}).update({
            "current_state": self.current_state,
            "expected_state": self.expected_state,
            "state_repair_actions": self.state_repair_actions
        })

        super().__init__(message, **kwargs)


class PerformanceError(InfrastructureError):
    """Raised when performance thresholds are exceeded."""

    def __init__(
        self,
        message: str,
        metric_name: str | None = None,
        actual_value: float | None = None,
        threshold_value: float | None = None,
        optimization_suggestions: list[str] | None = None,
        **kwargs
    ) -> None:
        self.metric_name = metric_name
        self.actual_value = actual_value
        self.threshold_value = threshold_value
        self.optimization_suggestions = optimization_suggestions or []

        recovery_actions = []
        if metric_name and actual_value and threshold_value:
            recovery_actions.append(f"{metric_name}: {actual_value} (制限: {threshold_value})")
        if self.optimization_suggestions:
            recovery_actions.extend(self.optimization_suggestions)
        else:
            recovery_actions.extend([
                "処理データ量を削減してください",
                "システムリソースを確認してください"
            ])

        kwargs.setdefault("recoverable", True)
        kwargs.setdefault("recovery_actions", recovery_actions)
        kwargs.setdefault("details", {}).update({
            "metric_name": self.metric_name,
            "actual_value": self.actual_value,
            "threshold_value": self.threshold_value,
            "optimization_suggestions": self.optimization_suggestions
        })

        super().__init__(message, **kwargs)
