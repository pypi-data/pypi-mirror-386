"""パスサービスProtocol定義

循環依存回避のための純粋なProtocol定義。
Pathに関わる依存はtypingで型ヒントのみ提供。
"""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path


class IPathServiceProtocol(Protocol):
    """パスサービスProtocol

    ドメイン層で定義し、インフラ層で実装する。
    これによりアプリケーション層がプレゼンテーション層に依存することを防ぐ。
    """

    @property
    def project_root(self) -> "Path":
        """プロジェクトルートパスを取得

        Returns:
            プロジェクトルートパス
        """
        ...

    # === 基本ディレクトリアクセス ===
    def get_manuscript_dir(self) -> "Path":
        """原稿ディレクトリパスを取得

        Returns:
            原稿ディレクトリパス
        """
        ...

    def get_management_dir(self) -> "Path":
        """管理資料ディレクトリパスを取得

        Returns:
            管理資料ディレクトリパス
        """
        ...

    def get_plots_dir(self) -> "Path":
        """プロットディレクトリパスを取得

        Returns:
            プロットディレクトリパス
        """
        ...

    def get_backup_dir(self) -> "Path":
        """バックアップディレクトリパスを取得

        Returns:
            バックアップディレクトリパス
        """
        ...

    def get_prompts_dir(self) -> "Path":
        """プロンプトディレクトリパスを取得

        Returns:
            プロンプトディレクトリパス
        """
        ...

    def get_settings_dir(self) -> "Path":
        """設定集ディレクトリパスを取得"""
        ...

    def get_quality_dir(self) -> "Path":
        """品質チェックディレクトリパスを取得

        Returns:
            品質チェックディレクトリパス
        """
        ...

    def get_reports_dir(self) -> "Path":
        """レポートディレクトリパスを取得

        Returns:
            レポートディレクトリパス
        """
        ...

    # === サブディレクトリアクセス ===
    def get_chapter_plots_dir(self) -> "Path":
        """章別プロットディレクトリパスを取得

        Returns:
            章別プロットディレクトリパス
        """
        ...

    def get_episode_plots_dir(self) -> "Path":
        """話別プロットディレクトリパスを取得

        Returns:
            話別プロットディレクトリパス
        """
        ...

    def get_quality_records_dir(self) -> "Path":
        """品質記録ディレクトリパスを取得

        Returns:
            品質記録ディレクトリパス
        """
        ...

    def get_analysis_results_dir(self) -> "Path":
        """全話分析結果ディレクトリパスを取得

        Returns:
            全話分析結果ディレクトリパス
        """
        ...

    def get_writing_logs_dir(self) -> "Path":
        """原稿執筆ログディレクトリパスを取得

        Returns:
            原稿執筆ログディレクトリパス
        """
        ...

    # === ファイルパス生成 ===
    def get_episode_file_path(self, episode_number: int, episode_title: str) -> "Path":
        """エピソードファイルパスを取得

        Args:
            episode_number: エピソード番号
            episode_title: エピソードタイトル

        Returns:
            エピソードファイルパス
        """
        ...

    def get_checklist_file_path(self, episode_number: int, episode_title: str) -> "Path":
        """チェックリストファイルパスを取得

        Args:
            episode_number: エピソード番号
            episode_title: エピソードタイトル

        Returns:
            チェックリストファイルパス
        """
        ...

    def get_project_config_file(self) -> "Path":
        """プロジェクト設定ファイルパスを取得

        Returns:
            プロジェクト設定ファイルパス
        """
        ...

    def get_proposal_file(self) -> "Path":
        """企画書ファイルパスを取得

        Returns:
            企画書ファイルパス
        """
        ...

    def get_reader_analysis_file(self) -> "Path":
        """読者分析ファイルパスを取得

        Returns:
            読者分析ファイルパス
        """
        ...

    # === 管理ファイルアクセス ===
    def get_episode_management_file(self) -> "Path":
        """話数管理ファイルパスを取得

        Returns:
            話数管理ファイルパス
        """
        ...

    def get_quality_config_file(self) -> "Path":
        """品質チェック設定ファイルパスを取得

        Returns:
            品質チェック設定ファイルパス
        """
        ...

    def get_quality_record_file(self) -> "Path":
        """品質記録ファイルパスを取得

        Returns:
            品質記録ファイルパス
        """
        ...

    # === ディレクトリ管理 ===
    def ensure_directories_exist(self) -> None:
        """必要なディレクトリの存在確認・作成"""
        ...

    def ensure_directory_exists(self, directory: "Path") -> None:
        """指定ディレクトリの存在確認・作成

        Args:
            directory: 確認/作成するディレクトリパス
        """
        ...

    # === ディレクトリ判定 ===
    def is_project_directory(self, path: "Path") -> bool:
        """プロジェクトディレクトリかどうかを判定

        Args:
            path: 判定対象パス

        Returns:
            プロジェクトディレクトリの場合True
        """
        ...

    def is_manuscript_file(self, file_path: "Path") -> bool:
        """原稿ファイルかどうかを判定

        Args:
            file_path: 判定対象ファイルパス

        Returns:
            原稿ファイルの場合True
        """
        ...

    # === ユーティリティ ===
    def get_required_directories(self) -> list[str]:
        """必須ディレクトリリストを取得

        Returns:
            必須ディレクトリリスト
        """
        ...

    def get_all_directories(self) -> list[str]:
        """推奨される全ディレクトリリストを取得"""
        ...
