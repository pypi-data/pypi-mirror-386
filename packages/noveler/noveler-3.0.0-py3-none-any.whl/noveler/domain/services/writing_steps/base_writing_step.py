"""Domain.services.writing_steps.base_writing_step
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""基底執筆ステップクラス

A38執筆プロンプトガイドの15ステップ体系の基底クラス。
すべてのステップサービスが継承する共通インターフェース。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class WritingStepResponse:
    """執筆ステップレスポンス基底クラス"""

    success: bool
    step_number: int
    step_name: str
    execution_time_ms: float = 0.0
    error_message: str | None = None


class BaseWritingStep(ABC):
    """執筆ステップ基底クラス

    A38執筆プロンプトガイドの各ステップが実装すべき共通インターフェース
    """

    def __init__(self, step_number: int, step_name: str, **kwargs: Any) -> None:
        """基底クラス初期化

        Args:
            step_number: ステップ番号（0-15）
            step_name: ステップ名
            **kwargs: 追加引数
        """
        self.step_number = step_number
        self.step_name = step_name

    @abstractmethod
    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None = None
    ) -> WritingStepResponse:
        """ステップ実行

        Args:
            episode_number: エピソード番号
            previous_results: 前ステップの実行結果

        Returns:
            WritingStepResponse: ステップ実行結果
        """

    def validate_previous_results(
        self,
        previous_results: dict[int, Any] | None,
        required_steps: list[int]
    ) -> tuple[bool, list[str]]:
        """前ステップ結果の検証

        Args:
            previous_results: 前ステップ結果
            required_steps: 必須前ステップリスト

        Returns:
            tuple[bool, list[str]]: (検証成功, エラーメッセージリスト)
        """
        if not previous_results:
            if required_steps:
                return False, [f"必須前ステップが不足: {required_steps}"]
            return True, []

        missing_steps = []
        for step_num in required_steps:
            if step_num not in previous_results:
                missing_steps.append(step_num)
            elif not self._is_step_successful(previous_results[step_num]):
                missing_steps.append(f"{step_num}(失敗)")

        if missing_steps:
            return False, [f"必須前ステップエラー: {missing_steps}"]

        return True, []

    def _is_step_successful(self, step_result: Any) -> bool:
        """ステップ結果の成功判定

        Args:
            step_result: ステップ結果

        Returns:
            bool: 成功したかどうか
        """
        if hasattr(step_result, "success"):
            return step_result.success
        if isinstance(step_result, dict):
            return step_result.get("success", False)
        return bool(step_result)

    def extract_data_from_previous_step(
        self,
        previous_results: dict[int, Any] | None,
        step_number: int,
        data_key: str
    ) -> Any:
        """前ステップからのデータ抽出

        Args:
            previous_results: 前ステップ結果
            step_number: 対象ステップ番号
            data_key: データキー

        Returns:
            Any: 抽出されたデータ（なければNone）
        """
        if not previous_results or step_number not in previous_results:
            return None

        step_result = previous_results[step_number]

        if hasattr(step_result, data_key):
            return getattr(step_result, data_key)
        if isinstance(step_result, dict):
            return step_result.get(data_key)

        return None
