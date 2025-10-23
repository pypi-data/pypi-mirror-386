#!/usr/bin/env python3
"""Adapter that implements the functional core contract in the infrastructure layer."""

import inspect
import time
import traceback
from collections.abc import Callable
from typing import Any

from noveler.domain.interfaces.functional_core_contract import (
    PurityTestResult,
    PurityViolation,
)


class FunctionalCoreContractAdapter:
    """Provide purity verification and side-effect checks for functional cores."""

    def is_side_effect_free(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
        """Return ``True`` if no obvious side effects are detected."""
        return self._check_side_effects(func, *args, **kwargs)

    def verify_purity(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> PurityTestResult:
        """Run deterministic and side-effect checks to assess purity."""
        start_time = time.time()
        violations: list[PurityViolation] = []
        test_iterations = 5  # 決定論性確認のための反復回数

        function_name = func.__name__

        # 1. 決定論性テスト
        deterministic_results = []
        for _i in range(test_iterations):
            try:
                result = func(*args, **kwargs)
                deterministic_results.append(result)
            except Exception as e:
                violations.append(PurityViolation(
                    function_name=function_name,
                    violation_type="execution_error",
                    description=f"Function execution raised an error: {e!s}",
                    evidence={"exception": str(e), "traceback": traceback.format_exc()},
                    timestamp=time.time()
                ))
                break

        # 決定論性チェック
        is_deterministic = len({str(r) for r in deterministic_results}) <= 1 if deterministic_results else False
        if not is_deterministic and deterministic_results:
            violations.append(PurityViolation(
                function_name=function_name,
                violation_type="non_deterministic",
                description="Detected non-deterministic output for identical input",
                evidence={"results": [str(r) for r in deterministic_results]},
                timestamp=time.time()
            ))

        # 2. 副作用検出
        has_no_side_effects = self._check_side_effects(func, *args, **kwargs)
        if not has_no_side_effects:
            violations.append(PurityViolation(
                function_name=function_name,
                violation_type="side_effects",
                description="Potential side effects detected",
                evidence={"details": "外部依存または状態変更の可能性"},
                timestamp=time.time()
            ))

        execution_time_ms = (time.time() - start_time) * 1000
        is_pure = is_deterministic and has_no_side_effects and len(violations) == 0

        return PurityTestResult(
            is_pure=is_pure,
            violations=violations,
            execution_time_ms=execution_time_ms,
            determinism_verified=is_deterministic,
            side_effects_detected=[] if has_no_side_effects else ["potential_side_effects"]
        )

    def enforce_determinism(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
        """Return ``True`` if repeated executions yield identical results."""
        test_iterations = 3
        results = []

        for _ in range(test_iterations):
            try:
                result = func(*args, **kwargs)
                results.append(str(result))
            except Exception:
                return False

        # 全ての結果が同一であることを確認
        return len(set(results)) <= 1

    def _check_side_effects(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
        """Perform a best-effort static analysis for side-effect patterns."""
        try:
            # 関数のソースコードから副作用パターンを検出
            source = inspect.getsource(func)

            # 副作用を示すパターン
            side_effect_patterns = [
                "print(",
                "open(",
                "write(",
                "requests.",
                "urllib.",
                "sqlite3.",
                "os.system",
                "subprocess.",
                "time.sleep",
                "random.",
                "console.print",
                "logging.",
                "global ",
                "nonlocal ",
            ]

            return all(pattern not in source for pattern in side_effect_patterns)

        except (OSError, TypeError):
            # ソースコードが取得できない場合（C拡張等）は保守的に副作用ありと判定
            return False


class PureFunctionValidator:
    """Utility wrapper that exposes common purity validation helpers."""

    def __init__(self) -> None:
        self._contract = FunctionalCoreContractAdapter()

    def validate(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> PurityTestResult:
        """Return the detailed purity test result for the function."""
        return self._contract.verify_purity(func, *args, **kwargs)

    def is_pure(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
        """Return ``True`` when the function passes purity checks."""
        result = self._contract.verify_purity(func, *args, **kwargs)
        return result.is_pure

    def enforce_purity(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator that enforces purity before executing the function."""
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not self.is_pure(func, *args, **kwargs):
                msg = f"Function {func.__name__} is not pure"
                raise RuntimeError(msg)
            return func(*args, **kwargs)
        return wrapper


# Factory function for easy instantiation
def create_functional_core_contract() -> FunctionalCoreContractAdapter:
    """Factory helper that returns a functional core contract adapter."""
    return FunctionalCoreContractAdapter()
