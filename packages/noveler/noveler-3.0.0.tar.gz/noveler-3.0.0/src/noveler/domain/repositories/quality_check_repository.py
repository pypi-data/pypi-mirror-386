#!/usr/bin/env python3
"""品質チェックリポジトリ(ドメイン層インターフェース)

品質チェックに関する永続化のインターフェース定義。
DDD原則に従い、ドメイン層で定義してインフラ層で実装する。
"""

from abc import ABC, abstractmethod

from noveler.domain.entities.quality_check_aggregate import QualityCheckConfiguration, QualityCheckResult, QualityRule
from noveler.domain.value_objects.completion_status import QualityCheckResult as CompletionQualityCheckResult
from noveler.domain.value_objects.quality_threshold import QualityThreshold


class QualityCheckRepository(ABC):
    """品質チェックリポジトリのインターフェース

    品質チェックに関する永続化操作を抽象化。
    実装はインフラ層で行う。
    """

    @abstractmethod
    def get_default_rules(self) -> list[QualityRule]:
        """デフォルトの品質ルールを取得

        Returns:
            品質ルールのリスト
        """

    @abstractmethod
    def get_rules_by_category(self, category: str) -> list[QualityRule]:
        """カテゴリ別の品質ルールを取得

        Args:
            category: ルールカテゴリ

        Returns:
            指定カテゴリの品質ルールのリスト
        """

    @abstractmethod
    def get_quality_threshold(self) -> QualityThreshold:
        """品質閾値を取得

        Returns:
            品質閾値
        """

    @abstractmethod
    def save_result(self, result: QualityCheckResult) -> None:
        """品質チェック結果を保存

        Args:
            result: 品質チェック結果
        """

    @abstractmethod
    def find_result_by_id(self, check_id: str) -> QualityCheckResult | None:
        """IDで品質チェック結果を検索

        Args:
            check_id: チェックID

        Returns:
            品質チェック結果(見つからない場合はNone)
        """

    @abstractmethod
    def find_results_by_episode(self, episode_id: str) -> list[QualityCheckResult]:
        """エピソードIDで品質チェック結果を検索

        Args:
            episode_id: エピソードID

        Returns:
            品質チェック結果のリスト
        """

    @abstractmethod
    def get_configuration(self) -> QualityCheckConfiguration:
        """品質チェック設定を取得

        Returns:
            品質チェック設定
        """

    @abstractmethod
    def save_configuration(self, config: QualityCheckConfiguration) -> None:
        """品質チェック設定を保存

        Args:
            config: 品質チェック設定
        """

    @abstractmethod
    def delete_result(self, check_id: str) -> bool:
        """品質チェック結果を削除

        Args:
            check_id: チェックID

        Returns:
            削除が成功したかどうか
        """

    def check_quality(self, project_name: str, episode_number: int) -> CompletionQualityCheckResult:
        """エピソードの品質をチェック

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            content: エピソード内容

        Returns:
            品質チェック結果
        """
        raise NotImplementedError('check_quality is not implemented')

    def auto_fix_content(self, content: str, issues: list[str]) -> tuple[str, CompletionQualityCheckResult]:
        """コンテンツを自動修正

        Args:
            content: 元の内容
            issues: 修正対象の問題リスト

        Returns:
            (修正後の内容, 修正後の品質チェック結果)
        """
        raise NotImplementedError('auto_fix_content is not implemented')
