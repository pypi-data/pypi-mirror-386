#!/usr/bin/env python3
"""YAMLプロジェクト設定リポジトリ

プロジェクト設定.yamlファイルの読み込みを担当
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.project_config_repository import ProjectConfigRepository
from noveler.infrastructure.repositories.base_yaml_repository import BaseYamlRepository


class YamlProjectConfigRepository(BaseYamlRepository, ProjectConfigRepository):
    """YAMLプロジェクト設定リポジトリ

    プロジェクト設定.yamlファイルの読み込み機能を提供
    """

    def __init__(self, project_root: Path) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートディレクトリ
        """
        self.project_root = Path(project_root)
        self.config_filename = self._get_config_filename()

    def _get_config_filename(self) -> str:
        """設定ファイル名を取得（FileTemplateServiceベース）"""
        try:
            from noveler.infrastructure.factories.configuration_service_factory import get_configuration_manager

            config_manager = get_configuration_manager()
            return config_manager.get_file_template("project_config")
        except Exception:
            # フォールバック: デフォルトファイル名
            return "プロジェクト設定.yaml"

    def load_config(self, project_path: Path) -> dict[str, Any]:
        """プロジェクト設定を読み込み

        Args:
            project_path: プロジェクトパス(Noneの場合は自動検出)

        Returns:
            プロジェクト設定辞書

        Raises:
            FileNotFoundError: 設定ファイルが見つからない
            yaml.YAMLError: YAML解析エラー
            OSError: その他のファイル読み込みエラー
        """
        config_path = self._find_config_file() if project_path is None else Path(project_path) / self.config_filename
        return self._load_yaml_file(config_path)

    def exists(self, project_path: Path) -> bool:
        """プロジェクト設定ファイルが存在するか

        Args:
            project_path: プロジェクトパス(Noneの場合は自動検出)

        Returns:
            存在するかどうか
        """
        try:
            if project_path is None:
                config_path = self._find_config_file()
            else:
                config_path = Path(project_path) / self.config_filename

            return config_path.exists()
        except FileNotFoundError:
            return False

    def get_genre_info(self, project_path: Path) -> dict[str, Any]:
        """ジャンル情報のみを取得

        Args:
            project_path: プロジェクトパス(Noneの場合は自動検出)

        Returns:
            ジャンル情報辞書
        """
        config = self.load_config(project_path)
        return config.get("ジャンル", {})

    def get_project_metadata(self, project_path: Path) -> dict[str, Any]:
        """プロジェクトメタデータを取得

        Args:
            project_path: プロジェクトパス(Noneの場合は自動検出)

        Returns:
            プロジェクトメタデータ
        """
        config = self.load_config(project_path)

        return {
            "project_name": config.get("プロジェクト名", ""),
            "author": config.get("作者", ""),
            "target_audience": config.get("ターゲット読者", ""),
            "publication_goal": config.get("出版目標", ""),
            "creation_date": config.get("作成日", ""),
            "last_updated": config.get("最終更新", ""),
        }

    def validate_config(self, project_path: Path) -> dict[str, Any]:
        """設定ファイルの妥当性を検証

        Args:
            project_path: プロジェクトパス(Noneの場合は自動検出)

        Returns:
            検証結果
        """
        try:
            config = self.load_config(project_path)

            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
            }

            # 必須フィールドの検証
            required_fields = ["プロジェクト名", "ジャンル"]
            for field in required_fields:
                if field not in config or not config[field]:
                    validation_result["errors"].append(f"必須フィールド '{field}' が見つかりません")
                    validation_result["valid"] = False

            # ジャンル情報の検証
            genre_info = config.get("ジャンル", {})
            if genre_info:
                if "メイン" not in genre_info:
                    validation_result["errors"].append("メインジャンルが設定されていません")
                    validation_result["valid"] = False

                if "サブ" not in genre_info or not genre_info["サブ"]:
                    validation_result["warnings"].append("サブジャンルが設定されていません")

                if "ターゲット" not in genre_info:
                    validation_result["warnings"].append("ターゲットフォーマットが設定されていません")

            # 推奨フィールドの検証
            recommended_fields = ["作者", "ターゲット読者"]
            for field in recommended_fields:
                if field not in config or not config[field]:
                    validation_result["warnings"].append(f"推奨フィールド '{field}' が設定されていません")

            return validation_result

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"設定ファイル読み込みエラー: {e}"],
                "warnings": [],
            }

    def get_path_config(self, project_path: Path | None = None) -> dict[str, str]:
        """プロジェクトのパス設定を取得

        Args:
            project_path: プロジェクトパス(Noneの場合は自動検出)

        Returns:
            パス設定辞書（キー：ディレクトリタイプ、値：相対パス）
        """
        try:
            config = self.load_config(project_path)

            # directory_structureセクションからパス設定を読み込み
            directory_structure = config.get("directory_structure", {})
            path_config = {}

            # directory_structureの設定をPathConfigurationのフィールドに対応させる
            if "manuscript_dir" in directory_structure:
                path_config["manuscripts"] = directory_structure["manuscript_dir"]
            if "plot_dir" in directory_structure:
                path_config["plots"] = directory_structure["plot_dir"]
            if "management_dir" in directory_structure:
                path_config["management"] = directory_structure["management_dir"]
            if "settings_dir" in directory_structure:
                path_config["settings"] = directory_structure["settings_dir"]

            # 旧形式（pathsセクション）にも対応
            old_path_config = config.get("paths", {})
            path_config.update(old_path_config)

            # デフォルト値を設定
            default_paths = {
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
            for key, default_value in default_paths.items():
                if key not in path_config:
                    path_config[key] = default_value

            return path_config

        except (FileNotFoundError, yaml.YAMLError):
            # 設定ファイルが見つからない場合はデフォルト値を返す
            return {
                "manuscripts": "40_原稿",
                "plots": "20_プロット",
                "management": "50_管理資料",
                "settings": "30_設定集",
                "backup": "60_バックアップ",
                "prompts": "60_プロンプト",
                "quality": "50_管理資料/品質記録",
                "reports": "50_管理資料/レポート",
            }

    def _find_config_file(self) -> Path:
        """設定ファイルを検索"""
        current_dir = Path.cwd()

        # 現在のディレクトリから上位へ向かって検索
        while current_dir != current_dir.parent:
            config_path = current_dir / self.config_filename
            if config_path.exists():
                return config_path
            current_dir = current_dir.parent

        # プロジェクトルートでも検索
        config_path = self.project_root / self.config_filename
        if config_path.exists():
            return config_path

        msg = f"プロジェクト設定ファイルが見つかりません: {self.config_filename}"
        raise FileNotFoundError(msg)

    def get_config_path(self, project_path: Path) -> Path:
        """設定ファイルパスを取得

        Args:
            project_path: プロジェクトパス(Noneの場合は自動検出)

        Returns:
            設定ファイルパス
        """
        if project_path is None:
            return self._find_config_file()
        return Path(project_path) / self.config_filename
