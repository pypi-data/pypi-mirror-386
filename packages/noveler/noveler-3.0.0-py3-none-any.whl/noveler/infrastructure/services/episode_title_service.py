#!/usr/bin/env python3
"""エピソードタイトル取得サービス

全体構成.yamlからエピソードタイトルを取得する機能を提供
"""

from pathlib import Path
from typing import Any

import yaml

from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.infrastructure.adapters.path_service_adapter import create_path_service


class EpisodeTitleService:
    """エピソードタイトル取得サービス"""

    def __init__(self, project_root: Path | None = None) -> None:
        """初期化

        Args:
            project_root: プロジェクトルートパス（省略時は自動取得）
        """
        if project_root:
            self._project_root = project_root
        else:
            path_service = create_path_service()
            self._project_root = path_service.project_root

        self._overall_config_cache: dict[str, Any] | None = None

    def get_episode_title(self, episode_number: EpisodeNumber) -> str:
        """エピソードタイトルを取得

        Args:
            episode_number: エピソード番号

        Returns:
            str: エピソードタイトル（取得できない場合は「第XXX話」）
        """
        try:
            # 1. 個別エピソードタイトルの直接マッピング（最高優先度）
            specific_title = self._get_specific_episode_title(episode_number)
            if specific_title:
                return specific_title

            # 2. 全体構成.yamlからタイトル取得を試行
            overall_config: dict[str, Any] = self._load_overall_config()

            # 3. story_structure.chapters から探す
            if "story_structure" in overall_config:
                story_structure = overall_config["story_structure"]
                if "chapters" in story_structure:
                    for chapter in story_structure["chapters"]:
                        if not isinstance(chapter, dict):
                            continue

                        start_episode = chapter.get("start_episode", 1)
                        end_episode = chapter.get("end_episode", 1)

                        # エピソード番号が章の範囲内にあるかチェック
                        if start_episode <= episode_number.value <= end_episode:
                            # main_events内でエピソードタイトルを探す
                            main_events = chapter.get("main_events", [])

                            # エピソード番号に対応するイベントを探す
                            for event in main_events:
                                if isinstance(event, str):
                                    # 「第X話：タイトル」形式を探す
                                    if f"第{episode_number.value}話" in event:
                                        title_part = event.split("：", 1)
                                        if len(title_part) > 1:
                                            return title_part[1].strip()
                                        # コロンの代わりに他の区切り文字も試す
                                        title_part = event.split("「", 1)
                                        if len(title_part) > 1:
                                            title = title_part[1].rstrip("」").strip()
                                            if title:
                                                return title

            # 4. 旧形式の探索（後方互換性）
            if "episodes" in overall_config:
                episodes = overall_config["episodes"]
                if isinstance(episodes, list):
                    for episode in episodes:
                        if isinstance(episode, dict) and episode.get("episode_number") == episode_number.value:
                            title = episode.get("title", "")
                            if title:
                                # 「第X話_」部分を除去
                                clean_title = title.replace(f"第{episode_number.value}話", "").strip("_").strip()
                                return clean_title or f"第{episode_number.value:03d}話"

            # 5. key_turning_pointsから探す
            if "key_turning_points" in overall_config:
                turning_points = overall_config["key_turning_points"]
                if isinstance(turning_points, list):
                    for point in turning_points:
                        if isinstance(point, dict) and point.get("episode") == episode_number.value:
                            event = point.get("event", "")
                            if event:
                                # イベント名を簡潔なタイトルに変換
                                title = self._convert_event_to_title(event)
                                if title:
                                    return title

            # 6. 章タイトルベースのフォールバック（最後の手段）
            chapter_title = self._get_chapter_title_for_episode(episode_number, overall_config)
            if chapter_title:
                return chapter_title

            # 7. デフォルトタイトル
            return f"第{episode_number.value:03d}話"

        except Exception:
            # エラー時はデフォルトタイトルを返す
            return f"第{episode_number.value:03d}話"

    def _get_specific_episode_title(self, episode_number: EpisodeNumber) -> str | None:
        """特定エピソード番号の個別タイトルマッピング

        設定ファイルに記載されていない重要エピソードのタイトルを
        直接マッピングで提供する

        Args:
            episode_number: エピソード番号

        Returns:
            str | None: 特定のタイトル（存在しない場合はNone）
        """
        # 重要エピソードの個別タイトルマッピング
        specific_titles = {
            21: "コンパイラ魔術の実戦投入",
            22: "効率化の快感と代償",
            23: "The Architects調査開始",
            24: "古代技術の解析",
            25: "ブランチの可視化",
            26: "デバッグ能力の進化",
            27: "チーム開発の痕跡",
            28: "失われた仲間たちの影",
            29: "原田修一の孤独",
            30: "中間コンパイル型魔術の確立",
        }

        return specific_titles.get(episode_number.value)

    def _load_overall_config(self) -> dict[str, Any]:
        """全体構成.yamlを読み込み

        Returns:
            dict: 全体構成データ
        """
        if self._overall_config_cache is not None:
            return self._overall_config_cache

        config_path = self._get_common_path_service(self._project_root).get_plot_dir() / "全体構成.yaml"

        if not config_path.exists():
            self._overall_config_cache = {}
            return self._overall_config_cache

        try:
            with open(config_path, encoding="utf-8") as f:
                self._overall_config_cache = yaml.safe_load(f) or {}
        except Exception:
            self._overall_config_cache = {}

        return self._overall_config_cache

    def _convert_event_to_title(self, event: str) -> str:
        """イベント説明をタイトルに変換

        Args:
            event: イベント説明文

        Returns:
            str: 変換されたタイトル
        """
        # よくあるパターンのタイトル変換
        event.lower()

        if "エクスプロイト" in event and "襲撃" in event:
            return "入学式クライシス"
        if "デバッグ" in event and "覚醒" in event:
            return "DEBUG覚醒"
        if "メモリ" in event and "限界" in event:
            return "メモリの限界"
        if "暴走" in event and "スクロール" in event:
            return "暴走するスクロール"
        if "ダンジョン" in event and "実習" in event:
            return "初ダンジョン実習"
        if "慢心" in event and "失敗" in event:
            return "慢心の代償"
        if "絆" in event and ("形成" in event or "結束" in event):
            return "絆の結成"
        if "意識" in event and "マージ" in event:
            return "意識マージの謎"
        if "コンパイル" in event and "成功" in event:
            return "初コンパイル成功"
        if "技術" in event and ("確立" in event or "習得" in event):
            return "技術の確立"
        if "協力" in event or "連携" in event:
            return "真の協力"
        if "決戦" in event or "対決" in event:
            return "最終決戦"
        if "解決" in event or "修正" in event:
            return "真の解決"
        if "部長" in event or "管理職" in event:
            return "新たな始まり"
        # 汎用的な変換: 最初の15文字程度を使用
        title = event[:15].strip()
        if title.endswith(("、", "。")):
            title = title[:-1]
        return title

    def _get_chapter_title_for_episode(
        self, episode_number: EpisodeNumber, overall_config: dict[str, Any]
    ) -> str | None:
        """エピソードが属する章のタイトルを取得

        Args:
            episode_number: エピソード番号
            overall_config: 全体構成データ

        Returns:
            str | None: 章タイトル（見つからない場合はNone）
        """
        try:
            # ChapterStructureServiceを使用して章情報を取得
            from noveler.infrastructure.services.chapter_structure_service import get_chapter_structure_service

            chapter_service = get_chapter_structure_service(self._project_root)
            chapter_info = chapter_service.get_chapter_by_episode(episode_number)

            if chapter_info:
                # 章名から簡潔なタイトル部分を抽出
                chapter_name = chapter_info.name
                if " - " in chapter_name:
                    return chapter_name.split(" - ", 1)[1]
                if ":" in chapter_name:
                    return chapter_name.split(":", 1)[1].strip()
                return chapter_name

        except Exception:
            pass

        return None

    def clear_cache(self) -> None:
        """キャッシュクリア"""
        self._overall_config_cache = None


def get_episode_title_service(project_root: Path | None = None) -> EpisodeTitleService:
    """EpisodeTitleServiceインスタンス取得

    Args:
        project_root: プロジェクトルートパス（省略時は自動取得）

    Returns:
        EpisodeTitleService: サービスインスタンス
    """
    return EpisodeTitleService(project_root)
