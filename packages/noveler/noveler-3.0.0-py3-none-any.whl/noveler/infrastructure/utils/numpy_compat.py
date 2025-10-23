# File: src/noveler/infrastructure/utils/numpy_compat.py
# Purpose: Provide a minimal NumPy-compatible facade when the binary cannot be imported.
# Context: Used by analytics and NLP adapters to avoid failing on environments without NumPy.
"""Lightweight NumPy compatibility layer.

This module exposes a subset of NumPy-like helpers so that modules depending on
`numpy` can continue to operate in environments where the native extension
cannot be loaded (e.g., sandboxed CI without manylinux wheels). When the real
NumPy package is available it will be returned, otherwise a pure Python fallback
is supplied with compatible behaviour for the limited API surface we rely on.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, pvariance, pstdev
from typing import Iterable, Sequence


@dataclass
class _CompatArray(list):
    """Simple list-backed array with NumPy-like repr."""

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"CompatArray({list(self)!r})"


class _NumpyCompat:
    """Subset of NumPy APIs required by the project."""

    ndarray = _CompatArray

    @staticmethod
    def array(values: Iterable) -> _CompatArray:
        """Create a compatible array from an iterable."""
        if isinstance(values, _CompatArray):
            return values
        if isinstance(values, list):
            return _CompatArray(values)
        return _CompatArray(list(values))

    @staticmethod
    def zeros(shape: Sequence[int]) -> list[_CompatArray]:
        """Return a zero-filled matrix described by ``shape``."""
        if isinstance(shape, int):  # pragma: no cover - defensive fallback
            return [_CompatArray([0.0 for _ in range(shape)])]
        if len(shape) != 2:
            raise ValueError("Only 2D shapes are supported in compat mode")
        rows, cols = shape
        return [_CompatArray([0.0 for _ in range(cols)]) for _ in range(rows)]

    @staticmethod
    def mean(data: Sequence[float]) -> float:
        """Population mean."""
        return fmean(data) if data else 0.0

    @staticmethod
    def std(data: Sequence[float]) -> float:
        """Population standard deviation."""
        return pstdev(data) if len(data) > 1 else 0.0

    @staticmethod
    def var(data: Sequence[float]) -> float:
        """Population variance."""
        return pvariance(data) if len(data) > 1 else 0.0

    @staticmethod
    def arange(stop: int) -> list[int]:
        """Return a range as a list for compatibility."""
        return list(range(stop))

    @staticmethod
    def polyfit(x: Sequence[float], y: Sequence[float], deg: int) -> tuple[float, float]:
        """Compute a first-degree polynomial fit and return (slope, intercept)."""
        if deg != 1:
            raise NotImplementedError("Compat polyfit only supports degree=1")
        if not x or not y:
            raise ValueError("polyfit requires non-empty x and y sequences")
        if len(x) != len(y):
            raise ValueError("x and y must be the same length")

        mean_x = fmean(x)
        mean_y = fmean(y)

        denominator = sum((xi - mean_x) ** 2 for xi in x)
        if denominator == 0:
            return 0.0, mean_y

        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        slope = numerator / denominator
        intercept = mean_y - slope * mean_x
        return slope, intercept


def get_numpy():
    """Return real NumPy if available, otherwise the compatibility shim."""
    try:
        import numpy as _np  # type: ignore[import-not-found]

        return _np
    except Exception:  # pragma: no cover - executed in constrained envs
        return _NumpyCompat()


__all__ = ["get_numpy", "_NumpyCompat"]
