#!/usr/bin/env python3
"""
プロジェクトコンテキスト YAMLリポジトリ

YAML形式のプロジェクトファイルからコンテキスト要素を抽出する
インフラストラクチャ層の実装。
"""

import re
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.entities.prompt_generation import (
    A24Stage,
    ContextElement,
    ContextElementType,
)
from noveler.domain.services.prompt_generation_service import ProjectContextRepository
from noveler.presentation.shared.shared_utilities import get_common_path_service


class YamlProjectContextRepository(ProjectContextRepository):
    """プロジェクトコンテキスト YAMLリポジトリ実装

    伏線管理.yaml、重要シーン.yaml、章別プロット等のYAMLファイルから
    エピソード関連のコンテキスト要素を抽出する。
    """

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root
        self._foreshadowing_file = project_root / "50_管理資料" / "伏線管理.yaml"
        self._important_scenes_file = project_root / "50_管理資料" / "重要シーン.yaml"
        self._plot_dir = get_common_path_service(project_root).get_plot_dir() / "章別プロット"

    def extract_foreshadowing_elements(self, episode_number: int) -> list[ContextElement]:
        """伏線要素抽出 - 複数のYAML形式に対応"""
        if not self._foreshadowing_file.exists():
            return []

        try:
            with self._foreshadowing_file.Path("r").open(encoding="utf-8") as f:
                foreshadowing_data: dict[str, Any] = yaml.safe_load(f)

            elements = []

            # 形式1: シンプルな伏線リスト形式 (テストファイル用)
            if isinstance(foreshadowing_data, dict) and "伏線リスト" in foreshadowing_data:
                for foreshadowing in foreshadowing_data["伏線リスト"]:
                    if self._is_relevant_to_episode(foreshadowing, episode_number):
                        element = self._create_foreshadowing_element(foreshadowing, episode_number)
                        if element:
                            elements.append(element)

            # 形式2: 複雑な階層構造形式 (実プロジェクトファイル用)
            elif isinstance(foreshadowing_data, dict):
                # major_foreshadowing セクションから抽出
                if "major_foreshadowing" in foreshadowing_data:
                    major_foreshadowing = foreshadowing_data["major_foreshadowing"]
                    for key, foreshadowing in major_foreshadowing.items():
                        if self._is_major_foreshadowing_relevant(foreshadowing, episode_number):
                            element = self._create_major_foreshadowing_element(foreshadowing, episode_number, key)
                            if element:
                                elements.append(element)

                # episode_foreshadowing_checklist セクションから抽出
                if "episode_foreshadowing_checklist" in foreshadowing_data:
                    checklist = foreshadowing_data["episode_foreshadowing_checklist"]
                    episode_key = f"第{episode_number:03d}話"
                    if episode_key in checklist:
                        episode_data: dict[str, Any] = checklist[episode_key]

                        # 仕込む伏線 (planted_foreshadowing)
                        if "planted_foreshadowing" in episode_data:
                            for planted in episode_data["planted_foreshadowing"]:
                                element = ContextElement(
                                    element_type=ContextElementType.FORESHADOWING,
                                    content=f"仕込み伏線: {planted}",
                                    priority=0.8,
                                    integration_stage=A24Stage.TECH_INTEGRATION,
                                    source_file="伏線管理.yaml",
                                    metadata={"type": "planted", "episode": episode_number},
                                )

                                elements.append(element)

                        # 回収する伏線 (recovered_foreshadowing)
                        if "recovered_foreshadowing" in episode_data:
                            for recovered in episode_data["recovered_foreshadowing"]:
                                element = ContextElement(
                                    element_type=ContextElementType.FORESHADOWING,
                                    content=f"回収伏線: {recovered}",
                                    priority=0.9,
                                    integration_stage=A24Stage.TECH_INTEGRATION,
                                    source_file="伏線管理.yaml",
                                    metadata={"type": "recovered", "episode": episode_number},
                                )

                                elements.append(element)

            return elements

        except Exception as e:
            # YAML読み込みエラーの場合、デバッグ情報を含めて空リスト返却

            self.logger_service.warning("伏線管理ファイル読み込みエラー: %s", e)
            return []

    def extract_important_scenes(self, episode_number: int) -> list[ContextElement]:
        """重要シーン抽出"""
        if not self._important_scenes_file.exists():
            return []

        try:
            with self._important_scenes_file.Path("r").open(encoding="utf-8") as f:
                scenes_data: dict[str, Any] = yaml.safe_load(f)

            elements = []
            if isinstance(scenes_data, dict) and "重要シーン" in scenes_data:
                for scene in scenes_data["重要シーン"]:
                    if self._is_scene_relevant_to_episode(scene, episode_number):
                        element = self._create_scene_element(scene, episode_number)
                        if element:
                            elements.append(element)

            return elements

        except Exception:
            # YAML読み込みエラーは空リスト返却
            return []

    def extract_chapter_connections(self, episode_number: int) -> list[ContextElement]:
        """章間連携抽出"""
        elements = []

        # エピソード番号から章を推定（10話単位と仮定）
        chapter_number = ((episode_number - 1) // 10) + 1

        # 現在章、前章、次章のプロットファイルをチェック
        for chapter_offset in [-1, 0, 1]:
            target_chapter = chapter_number + chapter_offset
            if target_chapter <= 0:
                continue

            chapter_file = self._plot_dir / f"第{target_chapter:03d}章.yaml"
            if not chapter_file.exists():
                continue

            try:
                f_content = chapter_file.read_text(encoding="utf-8")
                chapter_data: dict[str, Any] = yaml.safe_load(f_content)

                connection_elements = self._extract_chapter_connections_from_data(
                    chapter_data, episode_number, target_chapter
                )

                elements.extend(connection_elements)

            except Exception:
                # YAML読み込みエラーはスキップ
                continue

        return elements

    def _is_relevant_to_episode(self, foreshadowing: dict[str, Any], episode_number: int) -> bool:
        """伏線要素がエピソードに関連するかチェック"""
        # 伏線データの構造に応じて実装
        # 例: "発生話数"、"回収話数"、"関連エピソード"等のフィールドをチェック

        if "発生話数" in foreshadowing:
            trigger_episode = foreshadowing["発生話数"]
            if isinstance(trigger_episode, int) and trigger_episode == episode_number:
                return True

        if "回収話数" in foreshadowing:
            resolution_episode = foreshadowing["回収話数"]
            if isinstance(resolution_episode, int) and resolution_episode == episode_number:
                return True

        if "関連エピソード" in foreshadowing:
            related_episodes = foreshadowing["関連エピソード"]
            if isinstance(related_episodes, list) and episode_number in related_episodes:
                return True

        return False

    def _create_foreshadowing_element(
        self, foreshadowing: dict[str, Any], episode_number: int
    ) -> ContextElement | None:
        """伏線要素作成"""
        title = foreshadowing.get("タイトル", "")
        description = foreshadowing.get("詳細", "")

        if not title and not description:
            return None

        content = f"{title}: {description}" if title and description else (title or description)

        # 優先度計算（重要度、複雑度等から）
        priority = self._calculate_foreshadowing_priority(foreshadowing)

        # 統合段階決定（伏線は通常Stage 4で統合）
        integration_stage = A24Stage.TECH_INTEGRATION

        return ContextElement(
            element_type=ContextElementType.FORESHADOWING,
            content=content,
            priority=priority,
            integration_stage=integration_stage,
            source_file="伏線管理.yaml",
            metadata=foreshadowing,
        )

    def _is_major_foreshadowing_relevant(self, foreshadowing: dict[str, Any], episode_number: int) -> bool:
        """major_foreshadowing形式の伏線が当該エピソードに関連するかチェック"""
        if not isinstance(foreshadowing, dict):
            return False

        # first_appearance、planned_revelation等をチェック
        if "first_appearance" in foreshadowing:
            first_app = foreshadowing["first_appearance"]
            if isinstance(first_app, str):
                # "第4話" -> 4 に変換

                match = re.search(r"第(\d+)話", first_app)
                if match and int(match.group(1)) == episode_number:
                    return True

        if "planned_revelation" in foreshadowing:
            planned_rev = foreshadowing["planned_revelation"]
            if isinstance(planned_rev, str):

                match = re.search(r"第(\d+)話", planned_rev)
                if match and int(match.group(1)) == episode_number:
                    return True

        # hints配列内のエピソード番号をチェック
        if "hints" in foreshadowing and isinstance(foreshadowing["hints"], list):
            for hint in foreshadowing["hints"]:
                if isinstance(hint, dict) and "episode" in hint:
                    hint_episode = hint["episode"]
                    if isinstance(hint_episode, str):

                        match = re.search(r"第(\d+)話", hint_episode)
                        if match and int(match.group(1)) == episode_number:
                            return True

        # revelation_timeline をチェック
        if "revelation_timeline" in foreshadowing and isinstance(foreshadowing["revelation_timeline"], list):
            for revelation in foreshadowing["revelation_timeline"]:
                if isinstance(revelation, dict) and "episode" in revelation:
                    rev_episode = revelation["episode"]
                    if isinstance(rev_episode, str):

                        match = re.search(r"第(\d+)話", rev_episode)
                        if match and int(match.group(1)) == episode_number:
                            return True

        return False

    def _create_major_foreshadowing_element(
        self, foreshadowing: dict[str, Any], episode_number: int, foreshadowing_key: str
    ) -> ContextElement | None:
        """major_foreshadowing形式の伏線要素作成"""
        title = foreshadowing.get("title", foreshadowing_key)
        setup = foreshadowing.get("setup", "")

        # 当該エピソードに関連するhintを探す
        episode_hint = ""
        if "hints" in foreshadowing and isinstance(foreshadowing["hints"], list):
            for hint in foreshadowing["hints"]:
                if isinstance(hint, dict) and "episode" in hint:
                    hint_episode = hint["episode"]

                    match = re.search(r"第(\d+)話", hint_episode) if isinstance(hint_episode, str) else None
                    if match and int(match.group(1)) == episode_number:
                        episode_hint = hint.get("content", "")
                        break

        # コンテンツ作成
        content_parts = []
        if title:
            content_parts.append(f"伏線: {title}")
        if setup:
            content_parts.append(f"設定: {setup}")
        if episode_hint:
            content_parts.append(f"第{episode_number}話での展開: {episode_hint}")

        content = " | ".join(content_parts)

        if not content:
            return None

        # 優先度計算（カテゴリーベース）
        priority = 0.8
        category = foreshadowing.get("category", "")
        if category == "world_system":
            priority = 0.9
        elif category == "character_growth":
            priority = 0.7
        elif category == "technical_evolution":
            priority = 0.85

        return ContextElement(
            element_type=ContextElementType.FORESHADOWING,
            content=content,
            priority=priority,
            integration_stage=A24Stage.TECH_INTEGRATION,
            source_file="伏線管理.yaml",
            metadata={
                "foreshadowing_key": foreshadowing_key,
                "category": category,
                "episode": episode_number,
                **foreshadowing,
            },
        )

    def _is_scene_relevant_to_episode(self, scene: dict[str, Any], episode_number: int) -> bool:
        """重要シーンがエピソードに関連するかチェック"""
        if "エピソード番号" in scene:
            scene_episode = scene["エピソード番号"]
            if isinstance(scene_episode, int) and scene_episode == episode_number:
                return True

        if "出現話数" in scene:
            appearance_episode = scene["出現話数"]
            if isinstance(appearance_episode, int) and appearance_episode == episode_number:
                return True

        return False

    def _create_scene_element(self, scene: dict[str, Any], episode_number: int) -> ContextElement | None:
        """重要シーン要素作成"""
        title = scene.get("シーン名", "")
        description = scene.get("概要", "")

        if not title and not description:
            return None

        content = f"{title}: {description}" if title and description else (title or description)

        # 優先度計算
        priority = self._calculate_scene_priority(scene)

        # 統合段階決定（重要シーンは通常Stage 3で統合）
        integration_stage = A24Stage.SCENE_DETAIL

        return ContextElement(
            element_type=ContextElementType.IMPORTANT_SCENE,
            content=content,
            priority=priority,
            integration_stage=integration_stage,
            source_file="重要シーン.yaml",
            metadata=scene,
        )

    def _extract_chapter_connections_from_data(
        self, chapter_data: dict[str, Any], episode_number: int, chapter_number: int
    ) -> list[ContextElement]:
        """章データから連携要素抽出"""
        elements = []

        # 章の概要やテーマ等から連携要素を抽出
        if "概要" in chapter_data:
            overview = chapter_data["概要"]
            if isinstance(overview, str) and overview.strip():
                element = ContextElement(
                    element_type=ContextElementType.CHAPTER_CONNECTION,
                    content=f"第{chapter_number}章概要: {overview}",
                    priority=0.6,
                    integration_stage=A24Stage.SKELETON,
                    source_file=f"第{chapter_number:03d}章.yaml",
                    metadata={"chapter_number": chapter_number, "type": "overview"},
                )

                elements.append(element)

        # エピソード一覧から前後エピソードの情報抽出
        if "エピソード一覧" in chapter_data:
            episodes = chapter_data["エピソード一覧"]
            if isinstance(episodes, list):
                for ep_data in episodes:
                    if isinstance(ep_data, dict) and "話数" in ep_data:
                        ep_num = ep_data["話数"]
                        # 前後エピソードの情報を連携要素として追加
                        if abs(ep_num - episode_number) <= 2 and ep_num != episode_number:
                            title = ep_data.get("タイトル", f"第{ep_num}話")
                            element = ContextElement(
                                element_type=ContextElementType.CHAPTER_CONNECTION,
                                content=f"関連エピソード: {title}",
                                priority=0.5,
                                integration_stage=A24Stage.SKELETON,
                                source_file=f"第{chapter_number:03d}章.yaml",
                                metadata={"related_episode": ep_num, "type": "related_episode"},
                            )

                            elements.append(element)

        return elements

    def _calculate_foreshadowing_priority(self, foreshadowing: dict[str, Any]) -> float:
        """伏線優先度計算"""
        priority = 0.7  # ベース優先度

        # 重要度による調整
        if "重要度" in foreshadowing:
            importance = foreshadowing["重要度"]
            if isinstance(importance, str):
                if importance == "高":
                    priority += 0.2
                elif importance == "中":
                    priority += 0.1
                elif importance == "低":
                    priority -= 0.1

        # 複雑度による調整
        if "複雑度" in foreshadowing:
            complexity = foreshadowing["複雑度"]
            if isinstance(complexity, str):
                if complexity == "複雑":
                    priority += 0.1
                elif complexity == "単純":
                    priority -= 0.05

        return min(1.0, max(0.0, priority))

    def _calculate_scene_priority(self, scene: dict[str, Any]) -> float:
        """重要シーン優先度計算"""
        priority = 0.8  # ベース優先度（伏線より高め）

        # インパクトによる調整
        if "インパクト" in scene:
            impact = scene["インパクト"]
            if isinstance(impact, str):
                if impact == "高":
                    priority += 0.15
                elif impact == "中":
                    priority += 0.05
                elif impact == "低":
                    priority -= 0.1

        # シーンタイプによる調整
        if "タイプ" in scene:
            scene_type = scene["タイプ"]
            if isinstance(scene_type, str):
                if scene_type in ["クライマックス", "転換点"]:
                    priority += 0.1
                elif scene_type in ["日常", "説明"]:
                    priority -= 0.05

        return min(1.0, max(0.0, priority))
