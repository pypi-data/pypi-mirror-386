"""品質サービスインターフェース

品質チェック、品質ゲート管理、品質改善提案の標準インターフェースを定義します。
"""

from abc import ABC, abstractmethod
from typing import Any

from noveler.domain.value_objects.quality_check_result import QualityCheckResult


class IQualityService(ABC):
    """品質サービスインターフェース

    品質チェック機能の統一インターフェースを提供します。
    """

    @abstractmethod
    async def execute_quality_gate(
        self,
        episode: int,
        step: int,
        content: str,
        context: dict[str, Any] | None = None
    ) -> QualityCheckResult:
        """品質ゲートチェックを実行

        Args:
            episode: エピソード番号
            step: ステップ番号
            content: チェック対象コンテンツ
            context: 追加コンテキスト情報

        Returns:
            品質チェック結果
        """

    @abstractmethod
    async def get_improvement_suggestions(
        self,
        episode: int,
        quality_result: QualityCheckResult
    ) -> list[str]:
        """品質改善提案を取得

        Args:
            episode: エピソード番号
            quality_result: 品質チェック結果

        Returns:
            改善提案リスト
        """

    @abstractmethod
    async def validate_step_requirements(
        self,
        step: int,
        content: str
    ) -> bool:
        """ステップ要件の検証

        Args:
            step: ステップ番号
            content: 検証対象コンテンツ

        Returns:
            要件を満たしているかのブール値
        """
