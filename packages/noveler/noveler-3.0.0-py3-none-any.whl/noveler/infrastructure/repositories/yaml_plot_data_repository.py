#!/usr/bin/env python3
"""YAMLプロットデータリポジトリ実装
Infrastructure層:技術的実装の詳細
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.plot_data_repository import (
    PlotDataRepository,
    PlotValidationDataRepository,
    ProjectDetectionRepository,
)
from noveler.infrastructure.factories.path_service_factory import create_path_service


class YamlPlotDataRepository(PlotDataRepository):
    """YAML形式のプロットデータリポジトリ実装"""

    def load_master_plot(self, project_path: str | Path) -> dict[str, Any]:
        """マスタープロットを読み込む"""
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        plot_file = path_service.get_plots_dir() / "全体構成.yaml"

        if not plot_file.exists():
            msg = f"マスタープロットファイルが見つかりません: {plot_file}"
            raise FileNotFoundError(msg)

        try:
            with plot_file.Path(encoding="utf-8").open() as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            msg = f"マスタープロットファイルの読み込みに失敗しました: {e}"
            raise OSError(msg) from e

    def save_master_plot(self, project_path: str | Path, plot_data: dict[str, Any]) -> None:
        """マスタープロットを保存する"""
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        plot_file = path_service.get_plots_dir() / "全体構成.yaml"
        plot_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with plot_file.Path("w").open(encoding="utf-8") as f:
                yaml.dump(plot_data, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            msg = f"マスタープロットファイルの保存に失敗しました: {e}"
            raise OSError(msg) from e

    def load_chapter_plot(self, project_path: str, chapter_number: int) -> dict[str, Any]:
        """章別プロットを読み込む"""
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        plot_dir = path_service.get_plots_dir() / "章別プロット"
        plot_file = plot_dir / f"ch{chapter_number:02d}.yaml"
        if not plot_file.exists():
            legacy = plot_dir / f"第{chapter_number}章.yaml"
            if legacy.exists():
                plot_file = legacy

        if not plot_file.exists():
            msg = f"第{chapter_number}章のプロットファイルが見つかりません: {plot_file}"
            raise FileNotFoundError(msg)

        try:
            with plot_file.Path(encoding="utf-8").open() as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            msg = f"章別プロットファイルの読み込みに失敗しました: {e}"
            raise OSError(msg) from e

    def save_chapter_plot(self, project_path: str | Path, chapter_number: int, plot_data: dict[str, Any]) -> None:
        """章別プロットを保存する"""
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        plot_dir = path_service.get_plots_dir() / "章別プロット"
        plot_file = plot_dir / f"ch{chapter_number:02d}.yaml"
        if not plot_file.exists():
            plot_file = plot_dir / f"第{chapter_number}章.yaml"
        plot_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with plot_file.Path("w").open(encoding="utf-8") as f:
                yaml.dump(plot_data, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            msg = f"章別プロットファイルの保存に失敗しました: {e}"
            raise OSError(msg) from e

    def list_chapter_plots(self, project_path: str | Path) -> list[int]:
        """存在する章番号のリストを取得"""
        # B20準拠: パス管理はPathServiceを使用
        path_service = create_path_service()
        plot_dir = path_service.get_plots_dir() / "章別プロット"

        if not plot_dir.exists():
            return []

        chapter_numbers = []
        for file_path in plot_dir.glob("第*章.yaml"):
            try:
                # ファイル名から番号を抽出
                number_part = file_path.stem[1:-1]  # "第1章" -> "1"
                chapter_numbers.append(int(number_part))
            except (ValueError, IndexError):
                continue

        return sorted(chapter_numbers)

    def get_plot_progress(self, project_path: str | Path) -> dict[str, Any]:
        """プロット作成進捗を取得"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(Path(project_path))
        progress_file = path_service.get_plot_progress_file()

        if not progress_file.exists():
            return {"master_plot": False, "chapters": {}, "last_updated": None}

        try:
            with progress_file.Path(encoding="utf-8").open() as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            msg = f"プロット進捗ファイルの読み込みに失敗しました: {e}"
            raise OSError(msg) from e

    def update_plot_progress(self, project_path: str | Path, progress_data: dict[str, Any]) -> None:
        """プロット作成進捗を更新"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(Path(project_path))
        progress_file = path_service.get_plot_progress_file()
        progress_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with progress_file.Path("w").open(encoding="utf-8") as f:
                yaml.dump(progress_data, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            msg = f"プロット進捗ファイルの保存に失敗しました: {e}"
            raise OSError(msg) from e


class YamlPlotValidationDataRepository(PlotValidationDataRepository):
    """YAML形式のプロット検証データリポジトリ実装"""

    def load_plot_validation_rules(self, project_path: str | Path) -> dict[str, Any]:
        """プロット検証ルールを読み込む"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(Path(project_path))
        rules_file = path_service.get_plot_validation_rules_file()

        if not rules_file.exists():
            # デフォルトルールを返す
            return {
                "required_elements": ["opening", "development", "climax", "resolution"],
                "minimum_chapters": 1,
                "maximum_chapters": 10,
                "character_consistency": True,
            }

        try:
            with rules_file.Path(encoding="utf-8").open() as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            msg = f"プロット検証ルールファイルの読み込みに失敗しました: {e}"
            raise OSError(msg) from e

    def save_plot_validation_results(self, project_path: str | Path, results: dict[str, Any]) -> None:
        """プロット検証結果を保存する"""
        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(Path(project_path))
        results_file = path_service.get_plot_validation_results_file()
        results_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with results_file.Path("w").open(encoding="utf-8") as f:
                yaml.dump(results, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            msg = f"プロット検証結果ファイルの保存に失敗しました: {e}"
            raise OSError(msg) from e


class FileSystemProjectDetectionRepository(ProjectDetectionRepository):
    """ファイルシステムベースのプロジェクト検出リポジトリ実装"""

    def scan_directory_structure(self, base_path: str | Path) -> dict[str, Any]:
        """ディレクトリ構造をスキャンする"""
        base_dir = Path(base_path)

        if not base_dir.exists():
            return {"exists": False, "directories": []}

        structure = {"exists": True, "directories": [], "files": []}

        try:
            for item in base_dir.iterdir():
                if item.is_dir():
                    structure["directories"].append(item.name)
                else:
                    structure["files"].append(item.name)
        except PermissionError:
            structure["error"] = "Permission denied"

        return structure

    def check_project_markers(self, project_path: str | Path) -> dict[str, bool]:
        """プロジェクトマーカーファイルの存在確認"""
        project_dir = Path(project_path)

        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_dir)

        return {
            "project_config": (project_dir / "プロジェクト設定.yaml").exists(),
            "manuscript_dir": path_service.get_manuscript_dir().exists(),
            "management_dir": path_service.get_management_dir().exists(),
            "plot_dir": path_service.get_plot_dir().exists(),
            "episode_management": path_service.get_episode_management_file().exists(),
        }

    def get_project_metadata(self, project_path: str | Path) -> dict[str, Any]:
        """プロジェクトメタデータを取得"""
        project_dir = Path(project_path)

        metadata = {
            "path": str(project_dir),
            "name": project_dir.name,
            "exists": project_dir.exists(),
            "is_valid_project": False,
        }

        if project_dir.exists():
            markers = self.check_project_markers(project_path)
            metadata["is_valid_project"] = markers.get("project_config", False)
            metadata["markers"] = markers

            # プロジェクト設定から追加メタデータを取得
            config_file = project_dir / "プロジェクト設定.yaml"
            if config_file.exists():
                try:
                    with config_file.Path(encoding="utf-8").open() as f:
                        config_data: dict[str, Any] = yaml.safe_load(f) or {}
                        metadata.update(
                            {
                                "title": config_data.get("title", project_dir.name),
                                "genre": config_data.get("genre", "未設定"),
                                "author": config_data.get("author", "未設定"),
                            }
                        )

                except Exception:
                    pass

        return metadata
