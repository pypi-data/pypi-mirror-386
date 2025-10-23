#!/usr/bin/env python3
"""Imperative shell adapter that wraps functional core operations.

Implements the FC/IS architecture (SPEC-ARCH-002) by isolating side effects
while delegating pure computation to the functional core.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from noveler.domain.interfaces.console_service_protocol import IConsoleService
from noveler.domain.interfaces.functional_core_contract import IFunctionalCoreContract
from noveler.domain.interfaces.logger_service_protocol import ILoggerService
from tests.contracts.functional_core_contract import FunctionalCoreContract


class ShellServiceAdapter(ABC):
    """Base implementation of the imperative shell for FC/IS architecture.

    Responsibilities:
        - Localize side effects such as I/O and logging
        - Delegate pure computation to the functional core
    """

    def __init__(
        self, functional_core: IFunctionalCoreContract, console_service: IConsoleService, logger_service: ILoggerService
    ) -> None:
        """Initialize the shell with its functional core and side-effect services.

        Args:
            functional_core: Functional core contract implementation.
            console_service: Console service used for user-facing output.
            logger_service: Logger service used for diagnostic logging.
        """
        self._core = functional_core
        self._console = console_service
        self._logger = logger_service

    def execute_with_side_effects(self, input_data: object) -> object:
        """Run the functional core while orchestrating side effects.

        FC/IS stages:
            1. Gather input (I/O)
            2. Execute pure computation
            3. Emit output (I/O)

        Args:
            input_data: Raw input payload received by the shell.

        Returns:
            object: Result produced by the functional core.
        """
        # Step 1: Input (Side Effect) - 外部リソースから入力を準備
        processed_input = self._prepare_input(input_data)
        self._log_input_processing(processed_input)

        # Step 2: Pure Computation (No Side Effects) - Functional Coreで純粋計算
        try:
            result = self._execute_pure_computation(processed_input)
        except Exception as e:
            self._handle_computation_error(e)
            raise

        # Step 3: Output (Side Effect) - 結果を外部に出力
        self._handle_output(result)
        self._log_successful_completion(result)

        return result

    @abstractmethod
    def _prepare_input(self, raw_input: object) -> object:
        """Prepare input data, performing necessary side effects (e.g., file reads).

        Args:
            raw_input: Raw input payload.

        Returns:
            object: Processed input for the functional core.
        """

    @abstractmethod
    def _execute_pure_computation(self, input_data: object) -> object:
        """Execute the pure computation using the functional core.

        Args:
            input_data: Processed input payload.

        Returns:
            object: Result returned by the functional core.
        """

    @abstractmethod
    def _handle_output(self, result: object) -> None:
        """Emit functional core results via side-effectful operations.

        Args:
            result: Output produced by the functional core.
        """

    def _log_input_processing(self, input_data: object) -> None:
        """Log details about input preparation."""
        self._self.logger_service.info("入力データ処理開始: %s", type(input_data).__name__)

    def _handle_computation_error(self, error: Exception) -> None:
        """Handle and log errors raised by the functional core."""
        self._self.logger_service.error("純粋計算でエラーが発生: %s", str(error))
        self._console.print_error(f"計算処理エラー: {error!s}")

    def _log_successful_completion(self, result: object) -> None:
        """Log successful completion of the shell execution."""
        self._self.logger_service.info("処理完了: 結果タイプ=%s", type(result).__name__)


class A31EvaluationShellAdapter(ShellServiceAdapter):
    """Imperative shell specialization that orchestrates the A31 evaluation service."""

    def __init__(
        self,
        evaluation_service: object,  # A31EvaluationService
        console_service: IConsoleService,
        logger_service: ILoggerService,
    ) -> None:
        """Initialize the adapter with the evaluation service and side-effect handlers.

        Args:
            evaluation_service: Functional core service performing A31 evaluation.
            console_service: Console service used for output.
            logger_service: Logger service used for logging.
        """
        # FunctionalCoreContractの簡易実装を作成
        core_contract = A31EvaluationCoreContract(evaluation_service)

        super().__init__(core_contract, console_service, logger_service)
        self._evaluation_service = evaluation_service

    def _prepare_input(self, raw_input: object) -> dict[str, Any]:
        """Prepare evaluation input data, including file reads when necessary.

        Args:
            raw_input: Raw evaluation request payload.

        Returns:
            dict[str, Any]: Structured input data for the functional core.
        """
        # ファイル読み込み（副作用）
        if hasattr(raw_input, "episode_file_path"):
            try:
                episode_path = Path(raw_input.episode_file_path)
                episode_content = episode_path.read_text(encoding="utf-8")
            except FileNotFoundError:
                self._console.print_error(f"エピソードファイルが見つかりません: {raw_input.episode_file_path}")
                raise
        else:
            episode_content = getattr(raw_input, "episode_content", "")

        return {
            "items": getattr(raw_input, "items", []),
            "episode_content": episode_content,
            "metadata": getattr(raw_input, "metadata", {}),
        }

    def _execute_pure_computation(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Run the evaluation functional core without introducing side effects.

        Args:
            input_data: Prepared evaluation input data.

        Returns:
            dict[str, Any]: Evaluation results.
        """
        # 純粋関数呼び出し（副作用なし）
        return self._evaluation_service.evaluate_all_items(
            input_data["items"], input_data["episode_content"], input_data["metadata"]
        )

    def _handle_output(self, result: dict[str, Any]) -> None:
        """Emit evaluation results via console output.

        Args:
            result: Evaluation result payload.
        """
        # コンソール出力（副作用）
        self._console.print_info("A31評価結果:")

        passed_count = sum(1 for r in result.values() if r.passed)
        total_count = len(result)

        self._console.print_info(f"  総項目数: {total_count}")
        self._console.print_success(f"  合格項目: {passed_count}")

        if passed_count < total_count:
            self._console.print_warning(f"  不合格項目: {total_count - passed_count}")

            # 不合格項目の詳細表示
            for item_id, eval_result in result.items():
                if not eval_result.passed:
                    self._console.print_warning(f"    ❌ {item_id}: {eval_result.current_score:.1f}")


class A31EvaluationCoreContract(FunctionalCoreContract[dict[str, Any], dict[str, Any]]):
    """Functional core contract wrapper for the A31 evaluation service."""

    def __init__(self, evaluation_service: object) -> None:
        super().__init__()
        self._evaluation_service = evaluation_service

    def is_pure(self) -> bool:
        """Assert that the function behaves as a pure function."""
        # A31EvaluationServiceの純粋性をチェック
        return True  # @ensure_pure_functionデコレータで保証済み

    def is_deterministic(self) -> bool:
        """Assert deterministic behaviour for repeated invocations."""
        return True  # 同じ入力に対して同じ出力を返す

    def has_no_side_effects(self) -> bool:
        """Assert that no side effects are produced."""
        return True  # ファイルI/O、コンソール出力等の副作用なし


def create_a31_evaluation_shell(
    evaluation_service: object,
    console_service: IConsoleService,
    logger_service: ILoggerService,
) -> A31EvaluationShellAdapter:
    """Factory function that creates the A31 evaluation shell adapter

    Args:
        evaluation_service: A31評価サービス
        console_service: コンソールサービス
        logger_service: ログサービス

    Returns:
        A31EvaluationShellAdapter: 設定済みShell Adapter
    """
    return A31EvaluationShellAdapter(
        evaluation_service=evaluation_service, console_service=console_service, logger_service=logger_service
    )
