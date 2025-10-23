#!/usr/bin/env python3
"""ファイルシステムベースプロジェクトファイルリポジトリ実装

ProjectFileRepositoryインターフェースの実装
実際のファイルシステムを使用してプロジェクトファイルを操作
"""

import sys
from pathlib import Path
from typing import Any

import yaml

# スクリプトのルートディレクトリをパスに追加
current_dir = Path(__file__).resolve().parent
scripts_root = current_dir.parent.parent
sys.path.insert(0, str(scripts_root))

from noveler.domain.repositories.project_file_repository import ProjectFileRepository



class FileSystemProjectFileRepository(ProjectFileRepository):
    """ファイルシステムベースプロジェクトファイルリポジトリ実装"""

    def __init__(self, project_root: str | Path) -> None:
        """Args:
        project_root: プロジェクトルートディレクトリ
        """
        self.project_root = Path(project_root)

    def exists(self, file_path: str | Path) -> bool:
        """ファイルが存在するかチェック

        Args:
            file_path: ファイルパス(プロジェクトルートからの相対パス)

        Returns:
            bool: 存在する場合True
        """
        full_path = self.project_root / file_path
        return full_path.exists()

    def save_file(self, file_path: str | Path, content: dict[str, Any]) -> None:
        """ファイルを保存

        Args:
            file_path: 保存先ファイルパス(絶対パス)
            content: 保存内容

        Raises:
            IOError: 保存に失敗した場合
        """
        try:
            # パス文字列をPathオブジェクトに変換
            file_path = Path(file_path)
            # ディレクトリを作成
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # YAML形式で保存
            if isinstance(content, dict):
                with Path(file_path).open("w", encoding="utf-8") as f:
                    yaml.dump(content, f, allow_unicode=True, default_flow_style=False)
            else:
                # テキスト形式で保存
                # バッチ書き込みを使用
                Path(file_path).write_text(str(content), encoding="utf-8")

        except (OSError, yaml.YAMLError) as e:
            msg = f"ファイル保存エラー: {e}"
            raise OSError(msg) from e

    def load_project_config(self) -> dict[str, Any]:
        """プロジェクト設定を読み込み

        Returns:
            Dict[str, Any]: プロジェクト設定
        """
        config_file = self.project_root / "プロジェクト設定.yaml"

        if not config_file.exists():
            return {}

        try:
            with Path(config_file).open(encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config or {}
        except (OSError, yaml.YAMLError):
            return {}

    def create_directory(self, dir_path: str | Path) -> None:
        """ディレクトリを作成

        Args:
            dir_path: 作成するディレクトリパス(絶対パス)
        """
        try:
            # パス文字列をPathオブジェクトに変換
            dir_path = Path(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            msg = f"ディレクトリ作成エラー: {e}"
            raise OSError(msg) from e

    def get_file_content(self, file_path: str | Path) -> dict[str, Any]:
        """ファイル内容を読み込み(YAML)

        Args:
            file_path: ファイルパス(プロジェクトルートからの相対パス)

        Returns:
            Dict[str, Any]: ファイル内容
        """
        full_path = self.project_root / file_path

        if not full_path.exists():
            return {}

        try:
            with Path(full_path).open(encoding="utf-8") as f:
                content = yaml.safe_load(f)
                return content or {}
        except (OSError, yaml.YAMLError):
            return {}

    def load_file(self, file_path: str | Path) -> dict[str, Any]:
        """ファイルを読み込む(絶対パス版)

        Args:
            file_path: ファイルパス(絶対パス)

        Returns:
            Dict[str, Any]: ファイル内容

        Raises:
            IOError: 読み込みに失敗した場合
        """
        file_path = Path(file_path)

        if not file_path.exists():
            msg = f"ファイルが見つかりません: {file_path}"
            raise FileNotFoundError(msg)

        try:
            with Path(file_path).open(encoding="utf-8") as f:
                content = yaml.safe_load(f)
                return content or {}
        except yaml.YAMLError as e:
            msg = f"YAMLパースエラー: {e}"
            raise OSError(msg) from e
        except OSError as e:
            msg = f"ファイル読み込みエラー: {e}"
            raise OSError(msg) from e
