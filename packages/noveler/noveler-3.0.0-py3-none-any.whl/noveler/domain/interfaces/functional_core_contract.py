#!/usr/bin/env python3
"""Functional Core契約保証インターフェース

DDD Domain層インターフェース定義
Domain層の関数が副作用を持たず、決定論的であることを保証する契約
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., Any])


@dataclass(frozen=True)
class PurityViolation:
    """純粋性違反の記録"""
    function_name: str
    violation_type: str
    description: str
    evidence: dict[str, Any]
    timestamp: float


@dataclass(frozen=True)
class PurityTestResult:
    """純粋性テスト結果"""
    is_pure: bool
    violations: list[PurityViolation]
    execution_time_ms: float
    determinism_verified: bool
    side_effects_detected: list[str]


class IFunctionalCoreContract(ABC):
    """Functional Core契約インターフェース

    DDD Domain層で定義し、Infrastructure層で実装する。
    純粋関数の契約を保証し、副作用を検出する責務を持つ。
    """

    @abstractmethod
    def is_side_effect_free(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
        """関数が副作用を持たないことを検証

        以下の副作用を検出:
        - ファイルI/O操作
        - ネットワーク通信
        - データベース操作
        - グローバル変数の変更
        - 標準出力・標準エラー出力
        - 外部システムの状態変更

        Returns:
            bool: 副作用がない場合True
        """

    @abstractmethod
    def verify_purity(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> PurityTestResult:
        """関数の純粋性を包括的に検証

        Args:
            func: 検証対象の関数
            *args: 関数の位置引数
            **kwargs: 関数のキーワード引数

        Returns:
            PurityTestResult: 検証結果
        """

    @abstractmethod
    def enforce_determinism(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
        """決定論的実行を保証

        同じ入力に対して常に同じ出力を返すことを検証

        Args:
            func: 検証対象の関数
            *args: 関数の位置引数
            **kwargs: 関数のキーワード引数

        Returns:
            bool: 決定論的である場合True
        """


class NullFunctionalCoreContract:
    """Null Object Pattern実装

    テストや開発時に使用するダミー実装
    """

    def is_side_effect_free(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
        """常にTrueを返す（契約チェックを無効化）"""
        return True

    def verify_purity(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> PurityTestResult:
        """純粋であると仮定した結果を返す"""
        return PurityTestResult(
            is_pure=True,
            violations=[],
            execution_time_ms=0.0,
            determinism_verified=True,
            side_effects_detected=[]
        )

    def enforce_determinism(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
        """常にTrueを返す（決定論性チェックを無効化）"""
        return True
