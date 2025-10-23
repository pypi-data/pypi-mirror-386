# infrastructure/repositories/narrative_depth_repositories.py
"""内面描写深度評価リポジトリの実装"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

sys.path.append(str(Path(__file__).parent.parent.parent))

from noveler.domain.repositories.narrative_repositories import (
    EpisodeTextRepository,
    EvaluationResultRepository,
    PlotDataRepository,
)

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


class YamlPlotDataRepository(PlotDataRepository):
    """YAMLファイルベースのプロット情報リポジトリ"""

    def __init__(self, plot_directory: str | Path, logger_service=None, console_service=None) -> None:
        self.plot_directory = Path(plot_directory)

        self.logger_service = logger_service
        self.console_service = console_service
    def get_viewpoint_info(self, episode_number: int) -> dict[str, Any] | None:
        """エピソードの視点情報を取得"""
        try:
            # 章別プロットファイルを探す
            plot_files = list(self.plot_directory.glob("第*.yaml"))

            for plot_file in plot_files:
                with Path(plot_file).open(encoding="utf-8") as f:
                    plot_data: dict[str, Any] = yaml.safe_load(f)

                if not plot_data:
                    continue

                # episode_breakdownから情報を検索
                episode_breakdown = plot_data.get("episode_breakdown", {})
                # 両方のフォーマットを試す
                ep_key = f"ep{episode_number}"
                ep_key_padded = f"ep{episode_number:03d}"

                episode_info = None
                if ep_key in episode_breakdown:
                    episode_info = episode_breakdown[ep_key]
                elif ep_key_padded in episode_breakdown:
                    episode_info = episode_breakdown[ep_key_padded]

                if episode_info:
                    viewpoint_details = episode_info.get("viewpoint_details", {})

                    return {
                        "視点タイプ": episode_info.get("viewpoint_label", "標準"),
                        "複雑度": plot_data.get("chapter_info", {})
                        .get("viewpoint_management", {})
                        .get("complexity_level", "中"),
                        "キャラクター": viewpoint_details.get("consciousness", "不明"),
                        "シーン構成": episode_info.get("key_scenes", []),
                    }

                # 章情報から全体の視点情報を取得
                chapter_info = plot_data.get("chapter_info", {})
                if chapter_info is None:
                    chapter_info = {}

                viewpoint_mgmt = chapter_info.get("viewpoint_management", {})
                if viewpoint_mgmt is None:
                    viewpoint_mgmt = {}

                episodes_range = chapter_info.get("episodes", "")

                # エピソード範囲をチェック(例:第005-008話)
                if self._is_episode_in_range(episode_number, episodes_range):
                    return {
                        "視点タイプ": viewpoint_mgmt.get("narrative_technique", "標準"),
                        "複雑度": viewpoint_mgmt.get("complexity_level", "中"),
                        "キャラクター": viewpoint_mgmt.get("primary_pov_character", "不明"),
                        "シーン構成": [],
                    }

            return None

        except Exception as e:
            self.console_service.print(f"視点情報取得エラー: {e}")
            return None

    def _is_episode_in_range(self, episode_number: int, episodes_range: str) -> bool:
        """エピソードが章の範囲内かチェック"""
        try:
            if not episodes_range:
                return False

            # 例:「第1-4話」「第005-008話」
            if "第" in episodes_range and "-" in episodes_range:
                range_part = episodes_range.replace("第", "").replace("話", "")
                start_str, end_str = range_part.split("-")
                start = int(start_str)
                end = int(end_str)
                return start <= episode_number <= end

            # 例:「第001話」
            return bool(f"第{episode_number}話" in range_part)
        except Exception:
            return False

    def _extract_from_chapter3(self, file_path: Path, episode_number: int) -> dict[str, Any] | None:
        """第3章ファイルから視点情報を抽出"""
        try:
            with Path(file_path).open(encoding="utf-8") as f:
                yaml.safe_load(f)

            # 第001話の特別処理
            if episode_number == 1:
                return {
                    "視点タイプ": "単一視点・内省型",
                    "複雑度": "中",
                    "キャラクター": "カノン",
                    "シーン構成": ["朝の配信準備", "内面描写中心"],
                }

            return None

        except Exception:
            return None

    def get_complexity_level(self, episode_number: int) -> str:
        """エピソードの複雑度レベルを取得"""
        viewpoint_info = self.get_viewpoint_info(episode_number)
        if viewpoint_info:
            return viewpoint_info.get("複雑度", "中")
        return "中"


class MarkdownEpisodeTextRepository(EpisodeTextRepository):
    """Markdownファイルベースのエピソードテキストリポジトリ"""

    def __init__(self, manuscript_directory: str | Path, logger_service=None, console_service=None) -> None:
        self.manuscript_directory = Path(manuscript_directory)

        self.logger_service = logger_service
        self.console_service = console_service
    def get_episode_text(self, episode_number: int) -> str:
        """エピソードのテキストを取得"""
        try:
            # ファイル名パターンを試行
            patterns = [
                f"第{episode_number:03d}話*.md",
                f"第{episode_number}話*.md",
            ]

            for pattern in patterns:
                files = list(self.manuscript_directory.glob(pattern))
                if files:
                    with Path(files[0]).open(encoding="utf-8") as f:
                        return f.read()

            return ""

        except Exception as e:
            self.console_service.print(f"エピソードテキスト取得エラー: {e}")
            return ""

    def get_episode_metadata(self, episode_number: int) -> dict[str, Any]:
        """エピソードのメタデータを取得"""
        try:
            patterns = [
                f"第{episode_number:03d}話*.md",
                f"第{episode_number}話*.md",
            ]

            for pattern in patterns:
                files = list(self.manuscript_directory.glob(pattern))
                if files:
                    file_path = files[0]
                    stat = file_path.stat()
                    return {
                        "file_path": str(file_path),
                        "file_size": stat.st_size,
                        "modified_time": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                        "title": file_path.stem,
                    }

            return {}

        except Exception as e:
            self.console_service.print(f"メタデータ取得エラー: {e}")
            return {}


class JsonEvaluationResultRepository(EvaluationResultRepository):
    """JSONファイルベースの評価結果リポジトリ"""

    def __init__(self, results_directory: str | Path, logger_service=None, console_service=None) -> None:
        self.results_directory = Path(results_directory)
        self.results_directory.mkdir(parents=True, exist_ok=True)

        self.logger_service = logger_service
        self.console_service = console_service
    def save_evaluation_result(self, episode_number: int, result: dict[str, Any]) -> None:
        """評価結果を保存"""
        try:
            file_path = self.results_directory / f"narrative_depth_episode_{episode_number:03d}.json"

            # タイムスタンプを追加
            result["saved_at"] = project_now().datetime.isoformat()

            with Path(file_path).open("w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.console_service.print(f"評価結果保存エラー: {e}")

    def get_evaluation_history(self, episode_number: int) -> list[dict[str, Any]]:
        """評価履歴を取得"""
        try:
            file_path = self.results_directory / f"narrative_depth_episode_{episode_number:03d}.json"

            if not file_path.exists():
                return []

            with Path(file_path).open(encoding="utf-8") as f:
                result = json.load(f)
                return [result]  # 現在は単一結果のみ

        except Exception as e:
            self.console_service.print(f"評価履歴取得エラー: {e}")
            return []


class NarrativeDepthRepositoryFactory:
    """リポジトリファクトリ"""

    @staticmethod
    def create_repositories(
        project_root: str | Path,
    ) -> tuple[YamlPlotDataRepository, MarkdownEpisodeTextRepository, JsonEvaluationResultRepository]:
        """プロジェクトルートからリポジトリを作成"""
        project_path = Path(project_root)

        from noveler.infrastructure.adapters.path_service_adapter import create_path_service

        path_service = create_path_service(project_path)

        plot_repo = YamlPlotDataRepository(
            str(path_service.get_plot_dir() / "章別プロット"),
        )
        text_repo = MarkdownEpisodeTextRepository(
            str(path_service.get_manuscript_dir()),
        )

        result_repo = JsonEvaluationResultRepository(
            str(project_path / "logs" / "narrative_depth_evaluations"),
        )

        return plot_repo, text_repo, result_repo
