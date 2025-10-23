"""Domain.repositories.test_repository
Where: Domain repository interface for test result data.
What: Defines operations to persist and retrieve test diagnostics and histories.
Why: Supports testing workflows with consistent data access patterns.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""テストリポジトリインターフェース

DDD原則に基づくドメイン層のテスト管理リポジトリ抽象化
"""


from abc import ABC, abstractmethod
from typing import Any


class TestRepository(ABC):
    """テストリポジトリインターフェース"""

    @abstractmethod
    def save_test_result(self, test_id: str, result: dict[str, Any]) -> bool:
        """テスト結果を保存

        Args:
            test_id: テストID
            result: テスト結果

        Returns:
            保存成功時True
        """

    @abstractmethod
    def load_test_result(self, test_id: str) -> dict[str, Any] | None:
        """テスト結果を読み込み

        Args:
            test_id: テストID

        Returns:
            テスト結果、存在しない場合None
        """

    @abstractmethod
    def list_test_results(self, project_id: str | None = None) -> list[str]:
        """テスト結果IDのリストを取得

        Args:
            project_id: プロジェクトID(オプション)

        Returns:
            テスト結果IDのリスト
        """

    @abstractmethod
    def delete_test_result(self, test_id: str) -> bool:
        """テスト結果を削除

        Args:
            test_id: テストID

        Returns:
            削除成功時True
        """

    @abstractmethod
    def save_test_coverage(self, project_id: str, coverage_data: dict[str, Any]) -> bool:
        """テストカバレッジを保存

        Args:
            project_id: プロジェクトID
            coverage_data: カバレッジデータ

        Returns:
            保存成功時True
        """

    @abstractmethod
    def load_test_coverage(self, project_id: str) -> dict[str, Any] | None:
        """テストカバレッジを読み込み

        Args:
            project_id: プロジェクトID

        Returns:
            カバレッジデータ、存在しない場合None
        """

    @abstractmethod
    def save_test_configuration(self, project_id: str, config: dict[str, Any]) -> bool:
        """テスト設定を保存

        Args:
            project_id: プロジェクトID
            config: テスト設定

        Returns:
            保存成功時True
        """

    @abstractmethod
    def load_test_configuration(self, project_id: str) -> dict[str, Any] | None:
        """テスト設定を読み込み

        Args:
            project_id: プロジェクトID

        Returns:
            テスト設定、存在しない場合None
        """

    @abstractmethod
    def get_test_history(self, project_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """テスト履歴を取得

        Args:
            project_id: プロジェクトID
            limit: 取得件数の上限

        Returns:
            テスト履歴のリスト
        """

    @abstractmethod
    def archive_old_results(self, project_id: str, days_threshold: int = 30) -> int:
        """古いテスト結果をアーカイブ

        Args:
            project_id: プロジェクトID
            days_threshold: アーカイブ対象とする日数

        Returns:
            アーカイブされた件数
        """
