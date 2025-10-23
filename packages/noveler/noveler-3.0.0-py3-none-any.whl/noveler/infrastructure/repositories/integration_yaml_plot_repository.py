"""Infrastructure.repositories.integration_yaml_plot_repository
Where: Infrastructure repository storing YAML plot integrations.
What: Persists integration-specific plot data for downstream services.
Why: Keeps integration plot information organised and accessible.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""統合YAMLプロットリポジトリ(インフラ層実装)

YAMLファイルベースのプロットリポジトリ実装。
レガシーEpisodeManagerからの統合を含む。
"""


import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.repositories.plot_repository import PlotRepository


@dataclass
class PlotEpisodeInfo:
    """プロットエピソード情報"""

    episode_number: int
    title: str
    summary: str = ""
    status: str = "未執筆"
    target_words: int = 3000
    keywords: list[str] = None
    character_focus: list[str] = None
    scene_setting: str = ""

    def __post_init__(self) -> None:
        if self.keywords is None:
            self.keywords = []
        if self.character_focus is None:
            self.character_focus = []


# Phase 6修正: Infrastructure内循環依存解消のため、DI注入に変更
# from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class IntegrationYamlPlotRepository(PlotRepository):
    """統合YAMLプロットリポジトリ

    プロット情報をYAMLファイルで管理し、
    レガシーEpisodeManagerの機能を統合。
    """

    def __init__(self, project_root: Path | str | None = None, path_service: Any = None) -> None:
        """Phase 6修正: Adapter依存をDI注入に変更"""
        self.project_root = Path(project_root) if isinstance(project_root, str) else (project_root or Path.cwd())

        if path_service is None:
            # フォールバック: 基本的なパス構築
            self.plot_dir = self.project_root / "20_設定" / "章別プロット"
        else:
            self.plot_dir = path_service.get_plot_dir() / "章別プロット"

        # プロットディレクトリが存在しない場合は作成
        self.plot_dir.mkdir(parents=True, exist_ok=True)

    def find_episode_plot(self, _project_name: str, episode_number: int) -> dict[str, Any] | None:
        """エピソードのプロット情報を取得(レガシー互換)"""
        plot_files = list(self.plot_dir.glob("*.yaml"))

        for plot_file in plot_files:
            try:
                with Path(plot_file).open(encoding="utf-8") as f:
                    plot_data: dict[str, Any] = yaml.safe_load(f)

                if not plot_data or "episodes" not in plot_data:
                    continue

                episodes = plot_data["episodes"]
                if isinstance(episodes, list):
                    for episode in episodes:
                        if episode.get("episode_number") == episode_number:
                            return episode
                elif isinstance(episodes, dict):
                    episode_key = f"第{episode_number}話"
                    if episode_key in episodes:
                        return episodes[episode_key]

            except Exception:
                continue

        return None

    def find_chapter_plot(self, _project_name: str, chapter_number: int) -> dict[str, Any] | None:
        """章のプロット情報を取得"""
        chapter_file = self.plot_dir / f"ch{chapter_number:02d}.yaml"
        if not chapter_file.exists():
            chapter_file = self.plot_dir / f"第{chapter_number}章.yaml"

        if not chapter_file.exists():
            return None

        try:
            with Path(chapter_file).open(encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception:
            return None

    def save_episode_plot(self, _project_name: str, episode_number: int, plot_data: dict[str, Any]) -> None:
        """エピソードのプロット情報を保存"""
        # 該当する章ファイルを特定
        chapter_number = self._determine_chapter_number(episode_number)
        chapter_file = self.plot_dir / f"ch{chapter_number:02d}.yaml"
        if not chapter_file.exists():
            chapter_file = self.plot_dir / f"第{chapter_number}章.yaml"

        # 既存の章データを読み込み
        if chapter_file.exists():
            try:
                with Path(chapter_file).open(encoding="utf-8") as f:
                    chapter_data: dict[str, Any] = yaml.safe_load(f) or {}
            except Exception:
                chapter_data: dict[str, Any] = {}
        else:
            chapter_data: dict[str, Any] = {
                "chapter_number": chapter_number,
                "title": f"第{chapter_number}章",
                "episodes": {},
            }

        # エピソードデータを更新
        if "episodes" not in chapter_data:
            chapter_data["episodes"] = {}

        episode_key = f"第{episode_number}話"
        chapter_data["episodes"][episode_key] = plot_data

        # ファイルに保存
        with Path(chapter_file).open("w", encoding="utf-8") as f:
            yaml.dump(chapter_data, f, allow_unicode=True, default_flow_style=False)

    def exists(self, _project_name: str, episode_number: int) -> bool:
        """話プロットが存在するか確認"""
        return self.find_episode_plot(_project_name, episode_number) is not None

    def get_all_episode_plots(self, _project_name: str) -> list[dict[str, Any]]:
        """プロジェクトの全話プロットを取得"""
        all_episodes = []
        plot_files = list(self.plot_dir.glob("*.yaml"))

        for plot_file in plot_files:
            try:
                with Path(plot_file).open(encoding="utf-8") as f:
                    plot_data: dict[str, Any] = yaml.safe_load(f)

                if not plot_data or "episodes" not in plot_data:
                    continue

                episodes = plot_data["episodes"]
                if isinstance(episodes, list):
                    all_episodes.extend(episodes)
                elif isinstance(episodes, dict):
                    all_episodes.extend(
                        episode_data for episode_data in episodes.values() if isinstance(episode_data, dict)
                    )

            except Exception:
                continue

        return sorted(all_episodes, key=lambda x: x.get("episode_number", 999))

    def find_all_episodes(self) -> list[PlotEpisodeInfo]:
        """全エピソードのプロット情報を取得(統合用)"""
        all_episodes = []

        # レガシーEpisodeManagerのロジックを統合
        plot_data: dict[str, Any] = self._load_all_plot_data()

        for episode_dict in plot_data:
            try:
                episode_info = PlotEpisodeInfo(
                    episode_number=episode_dict.get("episode_number", 0),
                    title=episode_dict.get("title", ""),
                    summary=episode_dict.get("summary", ""),
                    status=episode_dict.get("status", "未執筆"),
                    target_words=episode_dict.get("target_words", 3000),
                    keywords=episode_dict.get("keywords", []),
                    character_focus=episode_dict.get("character_focus", []),
                    scene_setting=episode_dict.get("scene_setting", ""),
                )

                all_episodes.append(episode_info)
            except Exception:
                continue

        return sorted(all_episodes, key=lambda x: x.episode_number)

    def find_episode_plot_info(self, episode_number: int) -> PlotEpisodeInfo | None:
        """エピソード番号でプロット情報を取得(統合用)"""
        all_episodes = self.find_all_episodes()

        for episode in all_episodes:
            if episode.episode_number == episode_number:
                return episode

        return None

    def _load_all_plot_data(self) -> list[dict[str, Any]]:
        """全プロットデータを読み込み(レガシーEpisodeManager統合)

        レガシーEpisodeManagerのfind_next_unwritten_episodeメソッドのロジックを統合。
        """
        all_plot_data: dict[str, Any] = []

        try:
            plot_files = list(self.plot_dir.glob("*.yaml"))

            for plot_file in plot_files:
                try:
                    with Path(plot_file).open(encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                    if not data:
                        continue

                    # 章レベルのデータ処理
                    if "episodes" in data:
                        episodes = data["episodes"]

                        # リスト形式の場合
                        if isinstance(episodes, list):
                            all_plot_data.extend(episodes)

                        # 辞書形式の場合
                        elif isinstance(episodes, dict):
                            for episode_key, episode_data in episodes.items():
                                if isinstance(episode_data, dict):
                                    # エピソード番号を抽出または設定
                                    if "episode_number" not in episode_data:
                                        episode_number = self._extract_episode_number(episode_key)
                                        episode_data["episode_number"] = episode_number

                                    all_plot_data.append(episode_data)

                    # 直接エピソードデータの場合
                    elif "episode_number" in data:
                        all_plot_data.append(data)

                except Exception:
                    # ファイル読み込みエラーは無視して継続
                    continue

            return all_plot_data

        except Exception:
            return []

    def _extract_episode_number(self, episode_key: str) -> int:
        """エピソードキーから番号を抽出

        レガシーEpisodeManagerのextract_title_from_plotメソッドのロジックを統合。
        """

        # "第N話" パターンの抽出
        match = re.search(r"第(\d+)話", episode_key)
        if match:
            return int(match.group(1))

        # 数値のみのパターン
        match = re.search(r"(\d+)", episode_key)
        if match:
            return int(match.group(1))

        return 0

    def _determine_chapter_number(self, episode_number: int) -> int:
        """エピソード番号から章番号を決定

        通常は10話ごとに1章として計算。
        """
        return ((episode_number - 1) // 10) + 1
