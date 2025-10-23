#!/usr/bin/env python3
"""品質チェックプロンプトリポジトリインターフェース

DDD準拠: Domain層の抽象インターフェース
実装はInfrastructure層に配置
"""

from abc import ABC, abstractmethod

from noveler.domain.entities.quality_check_prompt import QualityCheckPrompt, QualityCheckPromptId
from noveler.domain.value_objects.quality_check_level import QualityCriterion


class QualityCheckPromptRepository(ABC):
    """品質チェックプロンプトリポジトリインターフェース

    Domain層の抽象インターフェース。
    Infrastructure層で具体実装を提供。
    """

    @abstractmethod
    def save(self, prompt: QualityCheckPrompt) -> None:
        """プロンプトを保存

        Args:
            prompt: 保存するプロンプト
        """

    @abstractmethod
    def find_by_id(self, prompt_id: QualityCheckPromptId) -> QualityCheckPrompt | None:
        """ID検索

        Args:
            prompt_id: プロンプトID

        Returns:
            QualityCheckPrompt | None: 見つかったプロンプト、存在しない場合はNone
        """

    @abstractmethod
    def find_by_episode(self, project_name: str, episode_number: int) -> list[QualityCheckPrompt]:
        """エピソード検索

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号

        Returns:
            list[QualityCheckPrompt]: 該当するプロンプト一覧
        """

    @abstractmethod
    def find_by_criteria(self, criteria: QualityCriterion) -> list[QualityCheckPrompt]:
        """基準検索

        Args:
            criteria: 検索基準

        Returns:
            list[QualityCheckPrompt]: 該当するプロンプト一覧
        """

    @abstractmethod
    def delete(self, prompt_id: QualityCheckPromptId) -> bool:
        """プロンプト削除

        Args:
            prompt_id: 削除するプロンプトID

        Returns:
            bool: 削除成功時True
        """

    @abstractmethod
    def list_all(self, project_name: str | None = None) -> list[QualityCheckPrompt]:
        """プロンプト一覧取得

        Args:
            project_name: プロジェクト名でフィルタ（Noneの場合は全て）

        Returns:
            list[QualityCheckPrompt]: プロンプト一覧
        """
