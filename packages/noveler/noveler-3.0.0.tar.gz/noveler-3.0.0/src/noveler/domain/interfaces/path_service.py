#!/usr/bin/env python3
"""パスサービスインターフェース

DDD準拠: ドメイン層のインターフェース定義
アプリケーション層はこのインターフェース経由でパス操作を行う
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path


class IPathService(Protocol):
    """パスサービスインターフェース

    ドメイン層で定義し、インフラ層で実装する。
    これによりアプリケーション層がプレゼンテーション層に依存することを防ぐ。
    """

    @property
    def project_root(self) -> Path:
        """プロジェクトルートパスを取得

        Returns:
            プロジェクトルートパス
        """
        ...

    def get_manuscript_dir(self) -> Path:
        """原稿ディレクトリパスを取得

        Returns:
            原稿ディレクトリパス
        """
        ...

    def get_checklist_file_path(self, episode_number: int, episode_title: str) -> Path:
        """チェックリストファイルパスを取得

        Args:
            episode_number: エピソード番号
            episode_title: エピソードタイトル

        Returns:
            チェックリストファイルパス
        """
        ...

    def get_episode_file_path(self, episode_number: int, episode_title: str) -> Path:
        """エピソードファイルパスを取得

        Args:
            episode_number: エピソード番号
            episode_title: エピソードタイトル

        Returns:
            エピソードファイルパス
        """
        ...

    def get_backup_dir(self) -> Path:
        """バックアップディレクトリパスを取得

        Returns:
            バックアップディレクトリパス
        """
        ...

    def get_plots_dir(self) -> Path:
        """プロットディレクトリパスを取得

        Returns:
            プロットディレクトリパス
        """
        ...

    def get_prompts_dir(self) -> Path:
        """プロンプトディレクトリパスを取得

        Returns:
            プロンプトディレクトリパス
        """
        ...

    def get_settings_dir(self) -> Path:
        """設定集ディレクトリパスを取得"""
        ...

    def get_quality_dir(self) -> Path:
        """品質チェックディレクトリパスを取得

        Returns:
            品質チェックディレクトリパス
        """
        ...

    def get_reports_dir(self) -> Path:
        """レポートディレクトリパスを取得

        Returns:
            レポートディレクトリパス
        """
        ...

    def get_spec_path(self) -> Path:
        """仕様書ディレクトリパスを取得

        Returns:
            仕様書ディレクトリパス
        """
        ...

    def ensure_directory_exists(self, directory: Path) -> None:
        """ディレクトリの存在を保証

        Args:
            directory: 確認/作成するディレクトリパス
        """
        ...

    def get_required_directories(self) -> list[str]:
        """必須ディレクトリ名の一覧を取得"""
        ...

    def get_all_directories(self) -> list[str]:
        """プロジェクト構造として推奨される全ディレクトリ名の一覧を取得"""
        ...

    # === B20: エピソード名・パス解決（共有基盤） ===
    def get_episode_title(self, episode_number: int) -> str | None:
        """エピソードタイトルを取得（章/話プロットや設定から推定）"""
        ...

    def get_manuscript_filename(self, episode_number: int) -> str:
        """原稿ファイル名を取得（第NNN話_{title}.md 規約、titleが無ければ『無題』）"""
        ...

    def get_manuscript_path(self, episode_number: int) -> Path:
        """原稿ファイルの絶対パスを取得（ディレクトリ自動生成含む）"""
        ...

    def get_episode_plot_path(self, episode_number: int) -> Path | None:
        """話別プロットファイルのパスを取得（存在しない場合はNone）"""
        ...
