"""品質管理ドメインのリポジトリインターフェース"""

from abc import ABC, abstractmethod

from noveler.domain.quality.entities import QualityReport


class ProperNounRepository(ABC):
    """固有名詞リポジトリインターフェース"""

    @abstractmethod
    def get_all_by_project(self, project_id: str) -> set[str]:
        """プロジェクトの全固有名詞を取得"""

    @abstractmethod
    def exists(self, project_id: str, proper_noun: str) -> bool:
        """固有名詞が存在するか確認"""


class QualityRuleRepository(ABC):
    """品質ルールリポジトリインターフェース"""

    @abstractmethod
    def get_active_rules(self, project_id: str) -> list[str]:
        """有効なルールのリストを取得"""

    @abstractmethod
    def get_rule_config(self, project_id: str, rule_name: str) -> dict:
        """ルールの設定を取得"""


class QualityReportRepository(ABC):
    """品質レポートリポジトリインターフェース"""

    @abstractmethod
    def save(self, report: QualityReport) -> None:
        """レポートを保存"""

    @abstractmethod
    def find_by_episode_id(self, episode_id: str) -> QualityReport | None:
        """エピソードIDでレポートを検索"""

    @abstractmethod
    def find_latest_by_episode_id(self, episode_id: str) -> QualityReport | None:
        """エピソードの最新レポートを取得"""

    @abstractmethod
    def find_all_by_project(self, project_id: str) -> list[QualityReport]:
        """プロジェクトの全レポートを取得"""
