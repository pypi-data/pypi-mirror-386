# File: src/noveler/domain/value_objects/execution_policy.py
# Purpose: Define execution policies and supporting value objects for infrastructure services.
# Context: Extracted from legacy aggregate to enforce cohesive rules.

"""Execution policy value objects for infrastructure service orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from noveler.domain.exceptions import DomainException


class ExecutionBackoffStrategy(Enum):
    """Backoff strategy for retries."""

    NONE = "none"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"


@dataclass(frozen=True)
class CachePolicy:
    """Cache policy controlling cache interaction."""

    enabled: bool
    ttl_seconds: int
    max_entries: int

    @classmethod
    def disabled(cls) -> "CachePolicy":
        """Create a disabled cache policy."""
        return cls(enabled=False, ttl_seconds=0, max_entries=0)

    def validate(self) -> None:
        """Ensure cache configuration adheres to invariants."""
        if self.enabled:
            if self.ttl_seconds <= 0:
                msg = "TTL must be positive when cache is enabled"
                raise DomainException(msg)
            if self.max_entries <= 0:
                msg = "Max entries must be positive when cache is enabled"
                raise DomainException(msg)


@dataclass(frozen=True)
class FallbackPolicy:
    """Policy describing fallback behaviour."""

    enabled: bool
    fallback_service: str | None
    reuse_original_context: bool = True

    def allows_fallback(self) -> bool:
        """Return True if fallback is configured."""
        return self.enabled and bool(self.fallback_service)


@dataclass(frozen=True)
class ExecutionPolicy:
    """Execution policy describing retry and cache behaviour."""

    timeout_seconds: float
    retry_limit: int
    backoff_strategy: ExecutionBackoffStrategy
    cache_policy: CachePolicy
    fallback_policy: FallbackPolicy
    health_error_threshold: float

    @classmethod
    def default(cls) -> "ExecutionPolicy":
        """Default policy mirroring legacy aggregate behaviour."""
        return cls(
            timeout_seconds=60.0,
            retry_limit=0,
            backoff_strategy=ExecutionBackoffStrategy.NONE,
            cache_policy=CachePolicy.disabled(),
            fallback_policy=FallbackPolicy(enabled=False, fallback_service=None),
            health_error_threshold=10.0,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExecutionPolicy":
        """Build policy from mapping."""
        cache_config = data.get("cache", {})
        cache_policy = CachePolicy(
            enabled=cache_config.get("enabled", False),
            ttl_seconds=cache_config.get("ttl_seconds", 0),
            max_entries=cache_config.get("max_entries", 0),
        )
        fallback_config = data.get("fallback", {})
        fallback_policy = FallbackPolicy(
            enabled=fallback_config.get("enabled", False),
            fallback_service=fallback_config.get("service"),
            reuse_original_context=fallback_config.get("reuse_context", True),
        )
        return cls(
            timeout_seconds=float(data.get("timeout_seconds", 60.0)),
            retry_limit=int(data.get("retry_limit", 0)),
            backoff_strategy=ExecutionBackoffStrategy(data.get("backoff_strategy", "none")),
            cache_policy=cache_policy,
            fallback_policy=fallback_policy,
            health_error_threshold=float(data.get("health_error_threshold", 10.0)),
        )

    def should_retry(self, attempt_count: int) -> bool:
        """Return True when another retry is allowed."""
        return attempt_count <= self.retry_limit

    def validate(self) -> None:
        """Validate policy invariants."""
        if self.timeout_seconds <= 0:
            msg = "Timeout must be greater than zero"
            raise DomainException(msg)
        if self.retry_limit < 0:
            msg = "Retry limit cannot be negative"
            raise DomainException(msg)
        if not 0.0 <= self.health_error_threshold <= 100.0:
            msg = "Health error threshold must be between 0 and 100"
            raise DomainException(msg)
        self.cache_policy.validate()
