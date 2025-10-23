#!/usr/bin/env python3
"""YAML ベースのプロジェクト情報リポジトリ実装.

ProjectInfoRepository インターフェースの具体実装。
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.project_info_repository import ProjectInfoRepository


class YamlProjectInfoRepository(ProjectInfoRepository):
    """YAML ファイルベースのプロジェクト情報リポジトリ

    小説プロジェクトの標準ディレクトリ構造から各種YAMLファイルを読み込み、
    プロジェクト情報を提供する
    """

    def __init__(self, logger_service=None, console_service=None) -> None:
        """リポジトリを初期化"""
        # ファイルパスマッピング（後方互換用デフォルト）
        self._file_mapping = {
            "project_settings": "プロジェクト設定.yaml",
            "character_settings": "30_設定集/キャラクター.yaml",
            "plot_settings": "20_プロット/全体構成.yaml",
            "episode_management": "50_管理資料/話数管理.yaml",
        }

        self.logger_service = logger_service
        self.console_service = console_service
    def _relative_to_root(self, path: Path, project_root: Path) -> Path:
        try:
            return path.relative_to(project_root)
        except ValueError:
            return path

    def _resolve_file_mapping(self, project_root_path: Path) -> dict[str, list[Path]]:
        """動的なファイルマッピングを生成"""
        mapping: dict[str, list[Path]] = {
            "project_settings": [Path(self._file_mapping["project_settings"])],
        }

        try:
            from noveler.infrastructure.adapters.path_service_adapter import create_path_service

            path_service = create_path_service(project_root_path)

            settings_dir = path_service.get_settings_dir()
            management_dir = path_service.get_management_dir()
            plots_dir = path_service.get_plots_dir()

            character_candidates = [
                self._relative_to_root(settings_dir / "キャラクター.yaml", project_root_path)
            ]

            management_candidate = self._relative_to_root(
                management_dir / "キャラクター.yaml",
                project_root_path,
            )
            if management_candidate not in character_candidates:
                character_candidates.append(management_candidate)

            mapping["character_settings"] = character_candidates
            mapping["plot_settings"] = [
                self._relative_to_root(plots_dir / "全体構成.yaml", project_root_path)
            ]
            mapping["episode_management"] = [
                self._relative_to_root(management_dir / "話数管理.yaml", project_root_path)
            ]
        except Exception:
            # フォールバック: 既定マッピングを使用
            for key, relative in self._file_mapping.items():
                mapping.setdefault(key, [Path(relative)])

        return mapping

    def load_project_files(self, project_root: str | None = None) -> dict[str, Any]:
        """プロジェクトファイルを読み込み

        Args:
            project_root: プロジェクトルートパス(省略時は現在位置から検索)

        Returns:
            Dict[str, Any]: 読み込まれたプロジェクトファイルデータ

        Raises:
            FileNotFoundError: プロジェクトルートが見つからない場合
            PermissionError: ファイル読み込み権限がない場合
            ValueError: ファイル形式が不正な場合
        """
        # プロジェクトルートを特定
        project_root_str = self.get_project_root() if project_root is None else project_root

        project_root_path = Path(project_root_str)

        if not project_root_path.exists():
            not_found_error = f"プロジェクトルートが見つかりません: {project_root_path}"
            raise FileNotFoundError(not_found_error)

        result = {}

        file_mapping = self._resolve_file_mapping(project_root_path)

        for file_type, candidate_paths in file_mapping.items():
            for relative_path in candidate_paths:
                file_path = (
                    relative_path if relative_path.is_absolute() else project_root_path / relative_path
                )

                try:
                    if file_path.exists():
                        content = self._load_yaml_file(file_path)
                        if content:
                            result[file_type] = content
                            break
                except (FileNotFoundError, PermissionError, ValueError) as e:
                    warning_msg = f"Warning: {file_path} の読み込みに失敗しました: {e}"
                    if hasattr(self.console_service, "print"):
                        self.console_service.print(warning_msg)  # type: ignore[call-arg]
                    else:
                        print(warning_msg)
                    break

        return result

    def _load_yaml_file(self, file_path: Path) -> dict[str, Any] | None:
        """YAML ファイルを読み込み

        Args:
            file_path: YAMLファイルパス

        Returns:
            Dict[str, Any]: 読み込まれたデータ(読み込み失敗時はNone)

        Raises:
            PermissionError: ファイル読み込み権限がない場合
            ValueError: YAML形式が不正な場合
        """
        try:
            with Path(file_path).open(encoding="utf-8") as f:
                content = yaml.safe_load(f)

            # 空ファイルや無効な内容をチェック
            if content is None:
                return None

            return self._validate_yaml_content(content, file_path)

        except PermissionError:
            permission_error = f"ファイル読み込み権限がありません: {file_path}"
            raise PermissionError(permission_error) from None
        except yaml.YAMLError as e:
            yaml_error = f"YAML形式が不正です: {file_path}, エラー: {e}"
            raise ValueError(yaml_error) from e
        except Exception as e:
            file_error = f"ファイル読み込みエラー: {file_path}, エラー: {e}"
            raise ValueError(file_error) from e

    def _validate_yaml_content(self, content: object, file_path: Path) -> dict[str, Any]:
        """YAML コンテンツの形式を検証"""
        if not isinstance(content, dict):
            dict_format_error = f"YAMLファイルは辞書形式である必要があります: {file_path}"
            raise TypeError(dict_format_error)
        return content

    def get_project_root(self, start_path: str | None = None) -> str:
        """プロジェクトルートパスを取得

        Args:
            start_path: 検索開始パス(省略時は現在ディレクトリ)

        Returns:
            str: プロジェクトルートパス

        Raises:
            FileNotFoundError: プロジェクトルートが見つからない場合
        """
        if start_path is None:
            start_path = str(Path.cwd())

        current_path = Path(start_path).absolute()

        # プロジェクトマーカーファイル
        project_markers = [
            "プロジェクト設定.yaml",
            "CLAUDE.md",  # 技術ガイドプロジェクトの場合
        ]

        # 上位ディレクトリに向かって検索
        for path in [current_path, *list(current_path.parents)]:
            for marker in project_markers:
                if (path / marker).exists():
                    return str(path)

        # 見つからない場合は現在のディレクトリをプロジェクトルートとして扱う
        # (開発時や特殊なケースに対応)
        return str(current_path)

    def file_exists(self, file_path: str | Path) -> bool:
        """ファイルの存在確認

        Args:
            file_path: 確認するファイルパス

        Returns:
            bool: ファイルが存在する場合True
        """
        return Path(file_path).exists()

    def get_file_path(self, project_root: str, file_type: str) -> str:
        """ファイルタイプから実際のファイルパスを取得

        Args:
            project_root: プロジェクトルートパス
            file_type: ファイルタイプ(project_settings, character_settings等)

        Returns:
            str: 実際のファイルパス
        """
        if file_type not in self._file_mapping:
            unknown_type_error = f"未知のファイルタイプ: {file_type}"
            raise ValueError(unknown_type_error)

        project_root_path = Path(project_root)
        mapping = self._resolve_file_mapping(project_root_path)
        for relative_path in mapping[file_type]:
            file_path = relative_path if relative_path.is_absolute() else project_root_path / relative_path
            if file_path.exists():
                return str(file_path)

        fallback = mapping[file_type][0]
        file_path = fallback if fallback.is_absolute() else project_root_path / fallback
        return str(file_path)

    def validate_project_structure(self, project_root: str) -> dict[str, Any]:
        """プロジェクト構造の検証

        Args:
            project_root: プロジェクトルートパス

        Returns:
            Dict[str, Any]: 検証結果
            {
                "is_valid": bool,
                "missing_directories": list[str],
                "missing_files": list[str],
                "recommendations": list[str]
            }
        """
        project_path = Path(project_root)
        result: dict[str, Any] = {
            "is_valid": True,
            "missing_directories": [],
            "missing_files": [],
            "recommendations": [],
        }

        # 必須ディレクトリ
        from noveler.presentation.shared.shared_utilities import get_common_path_service

        # 共通パスサービスはターゲットプロジェクト毎に再初期化することで
        # テスト用の一時ディレクトリでも副作用なく利用できる
        path_service = get_common_path_service(target_project_root=project_path)
        required_dirs = list(path_service.get_required_directories())

        # 推奨ディレクトリ
        recommended_dirs = ["90_アーカイブ"]

        # 必須ディレクトリの確認
        for dir_name in required_dirs:
            dir_path = project_path / dir_name
            if not dir_path.exists():
                result["missing_directories"].append(dir_name)
                result["is_valid"] = False

        # 推奨ディレクトリの確認
        for dir_name in recommended_dirs:
            dir_path = project_path / dir_name
            if not dir_path.exists():
                result["recommendations"].append(f"ディレクトリ '{dir_name}' の作成をお勧めします")

        # 必須ファイルの確認
        if not (project_path / "プロジェクト設定.yaml").exists():
            result["missing_files"].append("プロジェクト設定.yaml")
            result["is_valid"] = False

        # 推奨ファイルの確認
        recommended_files = [
            ("30_設定集/キャラクター.yaml", "キャラクター設定"),
            ("20_プロット/全体構成.yaml", "プロット設定"),
            ("50_管理資料/話数管理.yaml", "話数管理"),
        ]

        for file_path, description in recommended_files:
            if not (project_path / file_path).exists():
                result["recommendations"].append(f"{description}ファイル '{file_path}' の作成をお勧めします")

        return result

    def create_project_structure(self, project_root: str, project_name: str) -> None:
        """プロジェクト構造を作成

        Args:
            project_root: プロジェクトルートパス
            project_name: プロジェクト名
        """
        project_path = Path(project_root)
        project_path.mkdir(parents=True, exist_ok=True)

        # ディレクトリ作成
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service
        from noveler.presentation.shared.shared_utilities import get_common_path_service

        path_service = create_path_service(project_path)
        directories = path_service.get_all_directories()

        for dir_name in directories:
            (project_path / dir_name).mkdir(exist_ok=True)

        # 共通パスサービスを新規プロジェクトに合わせて再初期化
        try:
            get_common_path_service(target_project_root=Path(project_path))
        except Exception:
            pass

        # 基本ファイル作成
        self._create_basic_project_settings(project_path, project_name)

    def _create_basic_project_settings(self, project_path: Path, project_name: str) -> None:
        """基本的なプロジェクト設定ファイルを作成"""
        settings_file = project_path / "プロジェクト設定.yaml"

        if not settings_file.exists():
            basic_settings = {
                "title": project_name,
                "genre": "",
                "protagonist": "",
                "target_audience": "",
                "quality_threshold": 80,
                "created_at": "",
                "description": "プロジェクトの基本設定です。各項目を適切に設定してください。",
            }

            with Path(settings_file).open("w", encoding="utf-8") as f:
                yaml.dump(basic_settings, f, allow_unicode=True, default_flow_style=False)

    def get_supported_file_types(self) -> list[str]:
        """サポートされているファイルタイプ一覧を取得

        Returns:
            list[str]: ファイルタイプ一覧
        """
        return list(self._file_mapping.keys())

    def get_file_type_description(self, file_type: str) -> str:
        """ファイルタイプの説明を取得

        Args:
            file_type: ファイルタイプ

        Returns:
            str: ファイルタイプの説明
        """
        descriptions = {
            "project_settings": "プロジェクトの基本設定(タイトル、ジャンル、主人公等)",
            "character_settings": "キャラクター設定(主要キャラクター、関係性等)",
            "plot_settings": "プロット設定(全体構成、幕構造、転回点等)",
            "episode_management": "話数管理(各話の状態、品質記録等)",
        }

        return descriptions.get(file_type, f"未知のファイルタイプ: {file_type}")
