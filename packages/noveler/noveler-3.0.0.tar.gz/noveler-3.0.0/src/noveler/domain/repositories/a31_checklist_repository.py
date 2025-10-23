#!/usr/bin/env python3
"""A31チェックリストリポジトリインターフェース

SPEC-QUALITY-001に基づくA31チェックリスト管理の抽象化
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from noveler.domain.entities.a31_checklist_item import A31ChecklistItem
from noveler.domain.entities.auto_fix_session import AutoFixSession


class A31ChecklistRepository(ABC):
    """A31チェックリストリポジトリインターフェース"""

    @abstractmethod
    def load_template(self) -> dict[str, Any]:
        """テンプレートYAMLの読み込み

        Returns:
            Dict[str, Any]: テンプレートデータ
        """

    @abstractmethod
    def create_episode_checklist(self, episode_number: int, episode_title: str, project_root: Path) -> Path:
        """エピソード用チェックリストファイルの作成

        Args:
            episode_number: エピソード番号
            episode_title: エピソードタイトル
            project_root: プロジェクトルートディレクトリ

        Returns:
            Path: 作成されたチェックリストファイルのパス
        """

    @abstractmethod
    def save_results(self, session: AutoFixSession, results_path: Path) -> None:
        """修正結果をエピソード用チェックリストに保存

        Args:
            session: 自動修正セッション
            results_path: 結果保存先パス
        """

    @abstractmethod
    def get_checklist_items(self, project_name: str, item_ids: list[str]) -> list[A31ChecklistItem]:
        """チェックリスト項目を取得

        Args:
            project_name: プロジェクト名
            item_ids: 取得する項目IDのリスト

        Returns:
            list[A31ChecklistItem]: チェックリスト項目のリスト
        """

    @abstractmethod
    def get_all_checklist_items(self, project_name: str) -> list[A31ChecklistItem]:
        """全チェックリスト項目を取得

        Args:
            project_name: プロジェクト名

        Returns:
            list[A31ChecklistItem]: 全チェックリスト項目
        """

    @abstractmethod
    def get_all_items(self) -> list[A31ChecklistItem]:
        """全チェックリスト項目を取得(プロジェクト非依存)

        Returns:
            list[A31ChecklistItem]: 全チェックリスト項目
        """

    @abstractmethod
    def get_auto_fixable_items(self, fix_level: str) -> list[A31ChecklistItem]:
        """自動修正可能な項目を取得

        Args:
            fix_level: 修正レベル(safe/standard/interactive)

        Returns:
            list[A31ChecklistItem]: 自動修正可能な項目のリスト
        """

    @abstractmethod
    def save_evaluation_results(
        self,
        project_name: str,
        episode_number: int,
        evaluation_batch: Any,  # A31EvaluationBatch
    ) -> Path:
        """評価結果をYAML形式で保存

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            evaluation_batch: 評価バッチ結果

        Returns:
            Path: 保存されたファイルのパス
        """

    @abstractmethod
    def validate_checklist_structure(self, checklist_path: Path) -> bool:
        """チェックリスト構造の検証

        Args:
            checklist_path: チェックリストファイルパス

        Returns:
            bool: 構造が正しい場合True
        """

    @abstractmethod
    def backup_checklist(self, checklist_path: Path) -> Path:
        """チェックリストのバックアップ作成

        Args:
            checklist_path: チェックリストファイルパス

        Returns:
            Path: バックアップファイルのパス
        """

    @abstractmethod
    def restore_checklist(self, backup_path: Path, target_path: Path) -> bool:
        """チェックリストをバックアップから復元

        Args:
            backup_path: バックアップファイルパス
            target_path: 復元先パス

        Returns:
            bool: 復元成功時True
        """
