#!/usr/bin/env python3
"""パスサービスインターフェース

CommonPathServiceとPathServiceAdapterの統合基盤として、
共通のパス操作インターフェースを定義。

DDD準拠設計:
- Domain層でのインターフェース定義
- Infrastructure層での実装
- Presentation層からの依存削減
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class IPathService(ABC):
    """パスサービス共通インターフェース

    CommonPathServiceとPathServiceAdapterの統合により、
    レイヤー間依存の適正化とコード重複削減を実現。
    """

    # === 基本プロパティ ===
    @property
    @abstractmethod
    def project_root(self) -> Path:
        """プロジェクトルートパスを取得"""

    # === 基本ディレクトリアクセス ===
    @abstractmethod
    def get_manuscript_dir(self) -> Path:
        """原稿ディレクトリパスを取得"""

    @abstractmethod
    def get_management_dir(self) -> Path:
        """管理資料ディレクトリパスを取得"""

    @abstractmethod
    def get_plots_dir(self) -> Path:
        """プロットディレクトリパスを取得"""

    @abstractmethod
    def get_backup_dir(self) -> Path:
        """バックアップディレクトリパスを取得"""

    @abstractmethod
    def get_prompts_dir(self) -> Path:
        """プロンプトディレクトリパスを取得"""

    @abstractmethod
    def get_settings_dir(self) -> Path:
        """設定集ディレクトリパスを取得"""

    @abstractmethod
    def get_quality_dir(self) -> Path:
        """品質チェックディレクトリパスを取得"""

    @abstractmethod
    def get_reports_dir(self) -> Path:
        """レポートディレクトリパスを取得"""

    # === サブディレクトリアクセス ===
    @abstractmethod
    def get_chapter_plots_dir(self) -> Path:
        """章別プロットディレクトリパスを取得"""

    @abstractmethod
    def get_episode_plots_dir(self) -> Path:
        """話別プロットディレクトリパスを取得"""

    @abstractmethod
    def get_quality_records_dir(self) -> Path:
        """品質記録ディレクトリパスを取得"""

    @abstractmethod
    def get_analysis_results_dir(self) -> Path:
        """全話分析結果ディレクトリパスを取得"""

    # === ファイルパス生成 ===
    @abstractmethod
    def get_episode_file_path(self, episode_number: int, episode_title: str) -> Path:
        """エピソードファイルパスを取得"""

    @abstractmethod
    def get_checklist_file_path(self, episode_number: int, episode_title: str) -> Path:
        """チェックリストファイルパスを取得"""

    @abstractmethod
    def get_project_config_file(self) -> Path:
        """プロジェクト設定ファイルパスを取得"""

    @abstractmethod
    def get_proposal_file(self) -> Path:
        """企画書ファイルパスを取得"""

    @abstractmethod
    def get_reader_analysis_file(self) -> Path:
        """読者分析ファイルパスを取得"""

    # === 管理ファイルアクセス ===
    @abstractmethod
    def get_episode_management_file(self) -> Path:
        """話数管理ファイルパスを取得"""

    @abstractmethod
    def get_quality_config_file(self) -> Path:
        """品質チェック設定ファイルパスを取得"""

    @abstractmethod
    def get_quality_record_file(self) -> Path:
        """品質記録ファイルパスを取得"""

    @abstractmethod
    def get_writing_logs_dir(self) -> Path:
        """原稿執筆ログディレクトリパスを取得"""

    # === ディレクトリ管理 ===
    @abstractmethod
    def ensure_directories_exist(self) -> None:
        """必要なディレクトリの存在確認・作成"""

    @abstractmethod
    def ensure_directory_exists(self, directory: Path) -> None:
        """指定ディレクトリの存在確認・作成"""

    # === ディレクトリ判定 ===
    @abstractmethod
    def is_project_directory(self, path: Path) -> bool:
        """プロジェクトディレクトリかどうかを判定"""

    @abstractmethod
    def is_manuscript_file(self, file_path: Path) -> bool:
        """原稿ファイルかどうかを判定"""

    # === ユーティリティ ===
    @abstractmethod
    def get_required_directories(self) -> list[str]:
        """必須ディレクトリリストを取得"""

    @abstractmethod
    def get_all_directories(self) -> list[str]:
        """推奨される全ディレクトリリストを取得"""

    # === エピソード関連ユーティリティ（B20: 共有基盤集約） ===
    @abstractmethod
    def get_episode_title(self, episode_number: int) -> str | None:
        """エピソードタイトルを取得（章/話プロットや設定から推定）

        Returns:
            タイトル文字列（取得不可時はNone）
        """

    @abstractmethod
    def get_manuscript_filename(self, episode_number: int) -> str:
        """原稿ファイル名を取得（第NNN話_{title}.md 規約、titleが無ければ『無題』）"""

    @abstractmethod
    def get_manuscript_path(self, episode_number: int) -> Path:
        """原稿ファイルの絶対パスを取得（ディレクトリ自動生成含む）"""

    # === プロット関連ユーティリティ ===
    @abstractmethod
    def get_episode_plot_path(self, episode_number: int) -> Path | None:
        """話別プロットファイルのパスを取得（存在しない場合はNone）"""
