#!/usr/bin/env python3
"""品質記録拡張リポジトリインターフェース
品質記録活用システムのドメイン層
"""

from abc import ABC, abstractmethod
from typing import Any

from noveler.domain.entities.learning_session import LearningSession
from noveler.domain.entities.quality_record_enhancement import QualityRecordEnhancement


class QualityRecordEnhancementRepository(ABC):
    """品質記録拡張リポジトリインターフェース

    品質記録の永続化を担当するリポジトリインターフェース
    """

    @abstractmethod
    def save(self, quality_record: QualityRecordEnhancement) -> None:
        """品質記録を保存"""

    @abstractmethod
    def find_by_project_name(self, project_name: str) -> QualityRecordEnhancement | None:
        """プロジェクト名で品質記録を検索"""

    @abstractmethod
    def find_by_project_and_episode(self, project_name: str, episode_number: int) -> dict[str, Any] | None:
        """プロジェクト名とエピソード番号で品質記録を検索"""

    @abstractmethod
    def find_learning_history(self, project_name: str, period: int) -> list[dict[str, Any]]:
        """学習履歴を検索"""

    @abstractmethod
    def get_trend_analysis_data(self, project_name: str, episode_range: tuple[int, int]) -> list[dict[str, Any]]:
        """トレンド分析データを取得"""

    @abstractmethod
    def exists(self, project_name: str) -> bool:
        """品質記録の存在確認"""

    @abstractmethod
    def delete(self, project_name: str) -> bool:
        """品質記録を削除"""

    @abstractmethod
    def get_all_projects(self) -> list[str]:
        """全てのプロジェクト名を取得"""

    @abstractmethod
    def save_learning_session(self, session: LearningSession) -> None:
        """学習セッションを保存"""

    @abstractmethod
    def find_learning_session(self, project_name: str, episode_number: int) -> LearningSession | None:
        """学習セッションを検索"""

    @abstractmethod
    def get_quality_statistics(self, project_name: str) -> dict[str, Any]:
        """品質統計を取得"""
