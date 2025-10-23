#!/usr/bin/env python3
"""プロジェクトパス情報バリューオブジェクト

プロジェクト内の各フォルダパス情報を管理する不変オブジェクト。
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """プロジェクトパス情報

    プロジェクト内の標準的なフォルダ構成を表現する不変オブジェクト。
    プロジェクト設定.yamlから読み取られたパス情報をもとに構築される。
    """

    project_root: Path
    """プロジェクトルートディレクトリ"""

    manunoveler: Path
    """原稿フォルダ（デフォルト: 40_原稿）"""

    management: Path
    """管理資料フォルダ（デフォルト: 50_管理資料）"""

    plots: Path
    """プロットフォルダ（デフォルト: 20_プロット）"""

    settings: Path
    """設定集フォルダ（デフォルト: 30_設定集）"""

    backup: Path
    """バックアップフォルダ（デフォルト: 90_バックアップ）"""

    def get_manuscript_path(self, episode_number: int, title: str = "") -> Path:
        """指定されたエピソードの原稿ファイルパスを取得

        Args:
            episode_number: エピソード番号
            title: エピソードタイトル（省略可）

        Returns:
            Path: 原稿ファイルパス
        """
        filename = f"第{episode_number:03d}話_{title}.md" if title else f"第{episode_number:03d}話.md"

        return self.manuscripts / filename

    def get_quality_record_path(self, episode_number: int) -> Path:
        """指定されたエピソードの品質記録ファイルパスを取得

        Args:
            episode_number: エピソード番号

        Returns:
            Path: 品質記録ファイルパス
        """
        quality_dir = self.management / "品質記録"
        return quality_dir / f"第{episode_number:03d}話_品質記録.yaml"

    def get_a31_checklist_path(self, episode_number: int, title: str = "") -> Path:
        """指定されたエピソードのA31チェックリストファイルパスを取得

        Args:
            episode_number: エピソード番号
            title: エピソードタイトル（省略可）

        Returns:
            Path: A31チェックリストファイルパス
        """
        a31_dir = self.management / "A31_チェックリスト"
        if title:
            filename = f"A31_チェックリスト_第{episode_number:03d}話_{title}.yaml"
        else:
            filename = f"A31_チェックリスト_第{episode_number:03d}話.yaml"

        return a31_dir / filename

    def get_episode_management_path(self) -> Path:
        """話数管理ファイルのパスを取得

        Returns:
            Path: 話数管理ファイルパス
        """
        return self.management / "話数管理.yaml"

    def get_plot_chapter_path(self, chapter_number: int) -> Path:
        """指定された章のプロットファイルパスを取得

        Args:
            chapter_number: 章番号

        Returns:
            Path: 章別プロットファイルパス
        """
        chapter_plots_dir = self.plots / "章別プロット"
        return chapter_plots_dir / f"第{chapter_number:02d}章_プロット.yaml"

    def get_character_settings_path(self) -> Path:
        """キャラクター設定ファイルのパスを取得

        Returns:
            Path: キャラクター設定ファイルパス
        """
        return self.settings / "キャラクター.yaml"

    def get_terminology_path(self) -> Path:
        """用語集ファイルのパスを取得

        Returns:
            Path: 用語集ファイルパス
        """
        return self.settings / "用語集.yaml"

    def ensure_directories_exist(self) -> None:
        """必要なディレクトリが存在することを確認し、なければ作成

        プロジェクト運用に必要な基本的なディレクトリ構造を作成する。
        """
        directories_to_create = [
            self.manuscripts,
            self.management,
            self.management / "品質記録",
            self.management / "A31_チェックリスト",
            self.plots,
            self.plots / "章別プロット",
            self.settings,
        ]

        for directory in directories_to_create:
            directory.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict:
        """辞書形式に変換（デバッグ・ログ用）

        Returns:
            dict: パス情報の辞書表現
        """
        return {
            "project_root": str(self.project_root),
            "manuscripts": str(self.manuscripts),
            "management": str(self.management),
            "plots": str(self.plots),
            "settings": str(self.settings),
            "backup": str(self.backup),
        }
