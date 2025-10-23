"""ファイル名テンプレート管理サービス

設定ベースのファイル名管理を提供するドメインサービス
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from pathlib import Path


class FileTemplateRepository(ABC):
    """ファイル名テンプレート取得のインターフェース"""

    @abstractmethod
    def get_template(self, template_key: str) -> Optional[str]:
        """テンプレートキーからファイル名を取得"""
        pass

    @abstractmethod
    def get_all_templates(self) -> Dict[str, str]:
        """全テンプレートを取得"""
        pass


class FileTemplateService:
    """ファイル名テンプレート解決サービス（Domain Service）"""

    # デフォルトテンプレート定義
    DEFAULT_TEMPLATES = {
        "project_config": "プロジェクト設定.yaml",
        "episode_management": "話数管理.yaml",
        "quality_rules": "執筆品質ルール.yaml",
        "quality_record": "品質記録.yaml",
        "revision_history": "改訂履歴.yaml",
        "access_analysis": "アクセス分析.yaml",
        "quality_record_ai": "品質記録_AI学習用.yaml",
        "project_fallback": "project.yaml",
    }

    def __init__(self, repository: Optional[FileTemplateRepository] = None):
        """初期化

        Args:
            repository: ファイル名テンプレートリポジトリ（Noneの場合はデフォルト値使用）
        """
        self._repository = repository

    def get_filename(self, template_key: str) -> str:
        """テンプレートキーからファイル名を取得

        Args:
            template_key: テンプレートキー

        Returns:
            ファイル名（設定またはデフォルト値）
        """
        # リポジトリが設定されている場合は設定値を試行
        if self._repository:
            try:
                template_value = self._repository.get_template(template_key)
                if template_value:
                    return template_value
            except Exception:
                # 設定読み込み失敗時はデフォルト値にフォールバック
                pass

        # デフォルト値を返す
        return self.DEFAULT_TEMPLATES.get(template_key, f"{template_key}.yaml")

    def get_project_config_filename(self) -> str:
        """プロジェクト設定ファイル名を取得"""
        return self.get_filename("project_config")

    def get_episode_management_filename(self) -> str:
        """話数管理ファイル名を取得"""
        return self.get_filename("episode_management")

    def get_quality_rules_filename(self) -> str:
        """品質ルールファイル名を取得"""
        return self.get_filename("quality_rules")

    def get_project_fallback_filename(self) -> str:
        """代替プロジェクトファイル名を取得"""
        return self.get_filename("project_fallback")
