"""Domain.value_objects.path_configuration
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""パス設定値オブジェクト

FC/IS パターンのFunctional Core実装：
- 不変オブジェクトによるパス設定管理
- 純粋関数によるパス計算（副作用なし）
- 決定論的で予測可能な動作
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PathConfiguration:
    """パス設定値オブジェクト（不変・純粋）

    FC/IS パターンのFunctional Core実装。
    全てのパス計算が純粋関数として実装される。

    Attributes:
        manuscripts: 原稿ディレクトリ名
        plots: プロットディレクトリ名
        management: 管理ディレクトリ名
        backup: バックアップディレクトリ名
        prompts: プロンプトディレクトリ名
        quality: 品質チェックディレクトリ名
        reports: レポートディレクトリ名
    """

    manuscripts: str = "40_原稿"
    plots: str = "20_プロット"
    management: str = "50_管理資料"
    settings: str = "30_設定集"
    backup: str = "60_バックアップ"
    prompts: str = "60_プロンプト"
    quality: str = "50_管理資料/品質記録"
    reports: str = "50_管理資料/レポート"

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> PathConfiguration:
        """辞書からPathConfigurationを生成

        Args:
            config_dict: パス設定辞書

        Returns:
            PathConfiguration: パス設定値オブジェクト
        """
        # デフォルト値でマージ
        defaults = {
            "manuscripts": "40_原稿",
            "plots": "20_プロット",
            "management": "50_管理資料",
            "settings": "30_設定集",
            "backup": "60_バックアップ",
            "prompts": "60_プロンプト",
            "quality": "50_管理資料/品質記録",
            "reports": "50_管理資料/レポート",
        }

        # 設定値でデフォルト値を上書き
        merged_config = {**defaults, **config_dict}

        # 値オブジェクトのフィールドのみ抽出
        valid_fields = {
            key: value for key, value in merged_config.items()
            if key in cls.__dataclass_fields__
        }

        return cls(**valid_fields)

    def get_manuscript_path(self, project_root: Path) -> Path:
        """原稿ディレクトリパスを取得（純粋関数）

        Args:
            project_root: プロジェクトルートパス

        Returns:
            原稿ディレクトリパス
        """
        return project_root / self.manuscripts

    def get_management_path(self, project_root: Path) -> Path:
        """管理ディレクトリパスを取得（純粋関数）

        Args:
            project_root: プロジェクトルートパス

        Returns:
            管理ディレクトリパス
        """
        return project_root / self.management

    def get_settings_path(self, project_root: Path) -> Path:
        """設定集ディレクトリパスを取得（純粋関数）"""
        return project_root / self.settings

    def get_backup_path(self, project_root: Path) -> Path:
        """バックアップディレクトリパスを取得（純粋関数）

        Args:
            project_root: プロジェクトルートパス

        Returns:
            バックアップディレクトリパス
        """
        return project_root / self.backup

    def get_plots_path(self, project_root: Path) -> Path:
        """プロットディレクトリパスを取得（純粋関数）

        Args:
            project_root: プロジェクトルートパス

        Returns:
            プロットディレクトリパス
        """
        return project_root / self.plots

    def get_prompts_path(self, project_root: Path) -> Path:
        """プロンプトディレクトリパスを取得（純粋関数）

        Args:
            project_root: プロジェクトルートパス

        Returns:
            プロンプトディレクトリパス
        """
        return project_root / self.prompts

    def get_quality_path(self, project_root: Path) -> Path:
        """品質チェックディレクトリパスを取得（純粋関数）

        Args:
            project_root: プロジェクトルートパス

        Returns:
            品質チェックディレクトリパス
        """
        return project_root / self.quality

    def get_reports_path(self, project_root: Path) -> Path:
        """レポートディレクトリパスを取得（純粋関数）

        Args:
            project_root: プロジェクトルートパス

        Returns:
            レポートディレクトリパス
        """
        return project_root / self.reports

    def get_checklist_file_path(self, project_root: Path, episode_number: int, episode_title: str) -> Path:
        """チェックリストファイルパスを取得（純粋関数）

        Args:
            project_root: プロジェクトルートパス
            episode_number: エピソード番号
            episode_title: エピソードタイトル

        Returns:
            チェックリストファイルパス

        Raises:
            ValueError: 無効なエピソード番号またはタイトル
        """
        if episode_number < 1:
            msg = f"エピソード番号は1以上である必要があります: {episode_number}"
            raise ValueError(msg)

        if not episode_title or not isinstance(episode_title, str):
            msg = f"エピソードタイトルは空でない文字列である必要があります: {episode_title}"
            raise ValueError(msg)

        quality_dir = self.get_quality_path(project_root)
        return quality_dir / f"a31_checklist_第{episode_number:03d}話_{episode_title}.yaml"

    def get_episode_file_path(self, project_root: Path, episode_number: int, episode_title: str) -> Path:
        """エピソードファイルパスを取得（純粋関数）

        Args:
            project_root: プロジェクトルートパス
            episode_number: エピソード番号
            episode_title: エピソードタイトル

        Returns:
            エピソードファイルパス

        Raises:
            ValueError: 無効なエピソード番号またはタイトル
        """
        if episode_number < 1:
            msg = f"エピソード番号は1以上である必要があります: {episode_number}"
            raise ValueError(msg)

        if not episode_title or not isinstance(episode_title, str):
            msg = f"エピソードタイトルは空でない文字列である必要があります: {episode_title}"
            raise ValueError(msg)

        manuscript_dir = self.get_manuscript_path(project_root)
        return manuscript_dir / f"第{episode_number:03d}話_{episode_title}.md"

    def to_dict(self) -> dict[str, str]:
        """辞書形式に変換

        Returns:
            パス設定辞書
        """
        return {
            "manuscripts": self.manuscripts,
            "plots": self.plots,
            "management": self.management,
            "backup": self.backup,
            "prompts": self.prompts,
            "quality": self.quality,
            "reports": self.reports
        }


DEFAULT_PATH_CONFIG = PathConfiguration()


def get_default_manuscript_dir(project_root: Path) -> Path:
    """Return the manuscript directory path using the default configuration."""
    return DEFAULT_PATH_CONFIG.get_manuscript_path(project_root)


def get_default_management_dir(project_root: Path) -> Path:
    """Return the management directory path using the default configuration."""
    return DEFAULT_PATH_CONFIG.get_management_path(project_root)


def get_default_plot_dir(project_root: Path) -> Path:
    """Return the plot directory path using the default configuration."""
    return project_root / DEFAULT_PATH_CONFIG.plots
