"""ベースステップ処理器

全ステップ処理器の基底クラス
"""

from abc import ABC, abstractmethod
from typing import Any

from noveler.domain.entities.interactive_writing_session import InteractiveWritingSession, StepExecutionResult


class BaseStepProcessor(ABC):
    """ステップ処理器基底クラス"""

    def __init__(self, step_number: int) -> None:
        self.step_number = step_number

    @abstractmethod
    async def execute(
        self,
        session: InteractiveWritingSession,
        context: dict[str, Any] | None = None
        ) -> StepExecutionResult:
        """ステップ実行

        Args:
            session: インタラクティブ執筆セッション
            context: 実行コンテキスト

        Returns:
            ステップ実行結果
        """

    @abstractmethod
    def validate_prerequisites(self, session: InteractiveWritingSession) -> bool:
        """前提条件の検証

        Args:
            session: インタラクティブ執筆セッション

        Returns:
            前提条件を満たしているかのブール値
        """

    def get_step_name(self) -> str:
        """ステップ名取得"""
        step_names = {
            1: "プロットデータ準備",
            2: "構造分析",
            3: "感情設計",
            4: "ユーモア要素設計",
            5: "キャラクター対話設計",
            6: "場面演出設計",
            7: "論理整合性調整",
            8: "原稿執筆",
            9: "品質改善",
            10: "最終調整"
        }
        return step_names.get(self.step_number, f"ステップ{self.step_number}")
