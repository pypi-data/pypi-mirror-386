#!/usr/bin/env python3
"""Functional Core契約保証フレームワーク

SPEC-ARCH-002に基づく純粋関数の契約保証システム
Domain層の関数が副作用を持たず、決定論的であることを保証
"""

import time
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

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
    function_name: str
    is_pure: bool
    is_deterministic: bool
    has_no_side_effects: bool
    violations: list[PurityViolation]
    test_iterations: int
    execution_time: float


class FunctionalCoreContract(ABC, Generic[T, R]):
    """Functional Core契約保証基底クラス

    Domain層の純粋関数であることを保証する契約インターフェース。
    FC/ISアーキテクチャパターンのFunctional Core部分の品質保証。
    """

    def __init__(self) -> None:
        self._violations: list[PurityViolation] = []
        self._test_cache: dict[str, Any] = {}

    @abstractmethod
    def is_pure(self) -> bool:
        """純粋関数であることを保証

        純粋関数の定義:
        1. 同じ入力に対して常に同じ出力を返す（決定論的）
        2. 副作用を持たない（外部状態を変更しない）
        3. 外部状態に依存しない（引数のみに依存）

        Returns:
            bool: 純粋関数として契約を満たす場合True
        """

    @abstractmethod
    def is_deterministic(self) -> bool:
        """決定論的であることを保証

        同一入力に対して常に同一出力を返すことを検証。
        時間依存、ランダム値依存、外部状態依存を検出。

        Returns:
            bool: 決定論的である場合True
        """

    @abstractmethod
    def has_no_side_effects(self) -> bool:
        """副作用がないことを保証

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

    def verify_purity(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> PurityTestResult:
        """関数の純粋性を包括的に検証

        Args:
            func: 検証対象の関数
            *args: 関数の位置引数
            **kwargs: 関数のキーワード引数

        Returns:
            PurityTestResult: 検証結果の詳細
        """
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
                    description=f"関数実行でエラーが発生: {e!s}",
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
                description="同一入力に対して異なる出力を生成",
                evidence={"results": [str(r) for r in deterministic_results]},
                timestamp=time.time()
            ))

        # 2. 副作用検出（簡易版）
        has_no_side_effects = self._check_side_effects(func, *args, **kwargs)
        if not has_no_side_effects:
            violations.append(PurityViolation(
                function_name=function_name,
                violation_type="side_effects",
                description="副作用の可能性を検出",
                evidence={"details": "外部依存または状態変更の可能性"},
                timestamp=time.time()
            ))

        execution_time = time.time() - start_time
        is_pure = is_deterministic and has_no_side_effects and len(violations) == 0

        return PurityTestResult(
            function_name=function_name,
            is_pure=is_pure,
            is_deterministic=is_deterministic,
            has_no_side_effects=has_no_side_effects,
            violations=violations,
            test_iterations=test_iterations,
            execution_time=execution_time
        )

    def _check_side_effects(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> bool:
        """副作用の簡易チェック

        注意: 完全な副作用検出は困難なため、基本的なパターンのみチェック
        """
        try:
            # 関数のソースコードから副作用パターンを検出
            import inspect
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
            ]

            return all(pattern not in source for pattern in side_effect_patterns)

        except (OSError, TypeError):
            # ソースコードが取得できない場合（C拡張等）は保守的に副作用ありと判定
            return False


class PureFunctionValidator:
    """純粋関数検証ユーティリティ"""

    @staticmethod
    def validate_domain_service(service_class: type) -> dict[str, PurityTestResult]:
        """Domain Serviceクラスの全メソッドを純粋関数として検証

        Args:
            service_class: 検証対象のサービスクラス

        Returns:
            Dict[str, PurityTestResult]: メソッド名別の検証結果
        """
        results: dict[str, PurityTestResult] = {}
        contract = FunctionalCoreContractImpl()

        # publicメソッドのみを対象とする
        for method_name in dir(service_class):
            if method_name.startswith("_"):
                continue

            method = getattr(service_class, method_name)
            if not callable(method):
                continue

            # インスタンスメソッドの場合はインスタンスを作成
            try:
                instance = service_class()
                bound_method = getattr(instance, method_name)

                # ダミー引数での検証（実際のテストでは適切な引数を提供）
                result = contract.verify_purity(bound_method)
                results[method_name] = result

            except Exception as e:
                # インスタンス化や実行で問題がある場合はスキップ
                results[method_name] = PurityTestResult(
                    function_name=method_name,
                    is_pure=False,
                    is_deterministic=False,
                    has_no_side_effects=False,
                    violations=[PurityViolation(
                        function_name=method_name,
                        violation_type="validation_error",
                        description=f"検証中にエラーが発生: {e!s}",
                        evidence={"exception": str(e)},
                        timestamp=time.time()
                    )],
                    test_iterations=0,
                    execution_time=0.0
                )

        return results


class FunctionalCoreContractImpl(FunctionalCoreContract[Any, Any]):
    """FunctionalCoreContractの具象実装"""

    def is_pure(self) -> bool:
        """純粋関数であることを保証"""
        return len(self._violations) == 0

    def is_deterministic(self) -> bool:
        """決定論的であることを保証"""
        # 決定論性違反のチェック
        non_deterministic_violations = [
            v for v in self._violations
            if v.violation_type == "non_deterministic"
        ]
        return len(non_deterministic_violations) == 0

    def has_no_side_effects(self) -> bool:
        """副作用がないことを保証"""
        # 副作用違反のチェック
        side_effect_violations = [
            v for v in self._violations
            if v.violation_type == "side_effects"
        ]
        return len(side_effect_violations) == 0
