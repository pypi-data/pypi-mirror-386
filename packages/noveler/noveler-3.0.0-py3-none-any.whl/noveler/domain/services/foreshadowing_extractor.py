"""Domain.services.foreshadowing_extractor
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""
伏線抽出ドメインサービス
全体構成から伏線を識別・抽出するビジネスロジックを実装
"""


from typing import Any, ClassVar

from noveler.domain.value_objects.foreshadowing import (
    Foreshadowing,
    ForeshadowingCategory,
    ForeshadowingId,
    ForeshadowingStatus,
    PlantingInfo,
    ReaderReaction,
    ResolutionInfo,
    SubtletyLevel,
)


class ForeshadowingExtractor:
    """全体構成から伏線を抽出するドメインサービス"""

    # 伏線を示唆するキーワード
    FORESHADOWING_KEYWORDS: ClassVar[dict[str, list[str]]] = {
        "mystery": ["謎", "秘密", "正体", "真相", "隠された", "記憶", "過去"],
        "revelation": ["明かされる", "判明", "真実", "正体", "暴露", "告白"],
        "hidden": ["裏", "陰", "黒幕", "操る", "仕組まれた", "企み"],
        "identity": ["本当の", "実は", "素性", "出自", "血統"],
        "transformation": ["覚醒", "変化", "成長", "変貌", "力の解放"],
    }

    def __init__(self) -> None:
        self._foreshadowing_counter = 0

    def extract_from_master_plot(self, master_plot_data: dict[str, Any]) -> list[Foreshadowing]:
        """
        全体構成データから伏線を抽出

        Args:
            master_plot_data: 全体構成.yamlのデータ

        Returns:
            抽出された伏線のリスト
        """
        foreshadowings = []

        # 1. ストーリー構造から伏線を抽出
        if "story_structure" in master_plot_data:
            foreshadowings.extend(self._extract_from_story_structure(master_plot_data["story_structure"]))

        # 2. 章別概要から伏線を抽出
        if "chapter_outlines" in master_plot_data:
            foreshadowings.extend(self._extract_from_chapter_outlines(master_plot_data["chapter_outlines"]))

        # 3. キャラクター設定から伏線を抽出
        if "characters" in master_plot_data:
            foreshadowings.extend(self._extract_from_characters(master_plot_data["characters"]))

        # 4. テーマから伏線を抽出
        if "themes" in master_plot_data:
            foreshadowings.extend(self._extract_from_themes(master_plot_data["themes"]))

        return foreshadowings

    def _extract_from_story_structure(self, story_structure: dict[str, Any]) -> list[Foreshadowing]:
        """ストーリー構造から伏線を抽出"""
        foreshadowings = []

        # 開始部分の謎を抽出
        opening_foreshadowings = self._extract_opening_mysteries(story_structure)
        foreshadowings.extend(opening_foreshadowings)

        # 展開部分の伏線を抽出
        development_foreshadowings = self._extract_development_foreshadowings(story_structure)
        foreshadowings.extend(development_foreshadowings)

        return foreshadowings

    def _extract_opening_mysteries(self, story_structure: dict[str, Any]) -> list[Foreshadowing]:
        """開始部分の謎を抽出"""
        foreshadowings = []

        if "opening" in story_structure:
            opening = story_structure["opening"]
            if self._contains_mystery_keywords(str(opening)):
                foreshadowing = self._create_mystery_foreshadowing(
                    title="物語の開始時の謎",
                    description=self._extract_description(opening),
                    planting_chapter=1,
                    resolution_chapter=3,
                )

                if foreshadowing:
                    foreshadowings.append(foreshadowing)

        return foreshadowings

    def _extract_development_foreshadowings(self, story_structure: dict[str, Any]) -> list[Foreshadowing]:
        """展開部分の伏線を抽出"""
        foreshadowings = []

        if "development" not in story_structure:
            return foreshadowings

        development = story_structure["development"]

        # 主要な啓示
        if "major_revelations" in development:
            for i, revelation in enumerate(development["major_revelations"]):
                foreshadowing = self._create_revelation_foreshadowing(
                    revelation=revelation, index=i, total_chapters=story_structure.get("total_chapters", 3)
                )
                if foreshadowing:
                    foreshadowings.append(foreshadowing)

        # 転換点
        if "turning_points" in development:
            for i, turning_point in enumerate(development["turning_points"]):
                foreshadowing = self._create_turning_point_foreshadowing(turning_point=turning_point, index=i)
                if foreshadowing:
                    foreshadowings.append(foreshadowing)

        return foreshadowings

    def _extract_from_chapter_outlines(self, chapter_outlines: list[dict[str, Any]]) -> list[Foreshadowing]:
        """章別概要から伏線を抽出"""
        foreshadowings = []

        for chapter in chapter_outlines:
            chapter_num = chapter.get("chapter_number", 1)

            # 各章の重要な要素から伏線を探す
            if "key_events" in chapter:
                for event in chapter["key_events"]:
                    if self._is_foreshadowing_event(event):
                        foreshadowing = self._create_event_foreshadowing(event=event, chapter_num=chapter_num)
                        if foreshadowing:
                            foreshadowings.append(foreshadowing)

        return foreshadowings

    def _extract_from_characters(self, characters: dict[str, Any]) -> list[Foreshadowing]:
        """キャラクター設定から伏線を抽出"""
        foreshadowings = []

        for char_name, char_data in characters.items():
            # 隠された設定
            if "hidden_aspects" in char_data:
                for aspect in char_data["hidden_aspects"]:
                    foreshadowing = self._create_character_foreshadowing(character_name=char_name, hidden_aspect=aspect)
                    if foreshadowing:
                        foreshadowings.append(foreshadowing)

            # 秘密
            if "secrets" in char_data:
                for secret in char_data["secrets"]:
                    foreshadowing = self._create_secret_foreshadowing(character_name=char_name, secret=secret)
                    if foreshadowing:
                        foreshadowings.append(foreshadowing)

        return foreshadowings

    def _extract_from_themes(self, themes: dict[str, Any]) -> list[Foreshadowing]:
        """テーマから伏線を抽出"""
        foreshadowings = []

        # メインテーマに関連する伏線
        if "main" in themes and isinstance(themes["main"], str):
            if "真実" in themes["main"] or "正体" in themes["main"]:
                foreshadowing = self._create_thematic_foreshadowing(theme=themes["main"], _theme_type="main")
                if foreshadowing:
                    foreshadowings.append(foreshadowing)

        return foreshadowings

    def _create_mystery_foreshadowing(
        self, title: str, description: str, planting_chapter: int = 1, resolution_chapter: int = 3
    ) -> Foreshadowing | None:
        """謎系の伏線を作成"""
        self._foreshadowing_counter += 1
        foreshadowing_id = ForeshadowingId(f"F{self._foreshadowing_counter:03d}")

        # エピソード番号を推定
        planting_episode = f"第{planting_chapter:03d}話"
        resolution_episode = f"第{(resolution_chapter - 1) * 10 + 5:03d}話"  # 章の中盤と仮定

        return Foreshadowing(
            id=foreshadowing_id,
            title=title,
            category=ForeshadowingCategory.MYSTERY,
            description=description,
            importance=5,  # 謎は基本的に重要
            planting=PlantingInfo(
                episode=planting_episode,
                chapter=planting_chapter,
                method="物語の自然な流れの中で提示",
                content=description,
                subtlety_level=SubtletyLevel.HIGH,
            ),
            resolution=ResolutionInfo(
                episode=resolution_episode,
                chapter=resolution_chapter,
                method="衝撃的な真実の開示",
                impact="読者の予想を覆す展開",
            ),
            status=ForeshadowingStatus.PLANNED,
            expected_reader_reaction=ReaderReaction(
                on_planting="自然に受け入れる",
                on_hints="何か重要な意味があるのでは?",
                on_resolution="なるほど、そういうことだったのか!",
            ),
        )

    def _create_revelation_foreshadowing(
        self, revelation: object, index: int, total_chapters: int = 3
    ) -> Foreshadowing | None:
        """啓示・真相系の伏線を作成"""
        self._foreshadowing_counter += 1
        foreshadowing_id = ForeshadowingId(f"F{self._foreshadowing_counter:03d}")

        # 伏線のタイトルを生成
        title = self._extract_foreshadowing_title(revelation)

        # 章の配置を計算
        planting_chapter = 1  # 基本的に序盤で仕込む
        resolution_chapter = min(index + 2, total_chapters)  # 段階的に明かす

        return Foreshadowing(
            id=foreshadowing_id,
            title=title,
            category=ForeshadowingCategory.MAIN,
            description=revelation,
            importance=4,
            planting=PlantingInfo(
                episode=f"第{(index + 1) * 3:03d}話",
                chapter=planting_chapter,
                method="さりげない描写や台詞",
                content=f"{revelation}への布石",
                subtlety_level=SubtletyLevel.MEDIUM,
            ),
            resolution=ResolutionInfo(
                episode=f"第{resolution_chapter * 10:03d}話",
                chapter=resolution_chapter,
                method="段階的な真相開示",
                impact=revelation,
            ),
            status=ForeshadowingStatus.PLANNED,
        )

    def _create_character_foreshadowing(self, character_name: str, hidden_aspect: object) -> Foreshadowing | None:
        """キャラクター関連の伏線を作成"""
        self._foreshadowing_counter += 1
        foreshadowing_id = ForeshadowingId(f"F{self._foreshadowing_counter:03d}")

        return Foreshadowing(
            id=foreshadowing_id,
            title=f"{character_name}の隠された一面",
            category=ForeshadowingCategory.CHARACTER,
            description=hidden_aspect,
            importance=3,
            planting=PlantingInfo(
                episode="第002話",
                chapter=1,
                method="キャラクターの何気ない仕草や反応",
                content=f"{character_name}の不自然な振る舞い",
                subtlety_level=SubtletyLevel.HIGH,
            ),
            resolution=ResolutionInfo(
                episode="第015話",
                chapter=2,
                method="過去の回想や告白",
                impact=f"{character_name}の本当の姿が明らかになる",
            ),
            status=ForeshadowingStatus.PLANNED,
        )

    def _contains_mystery_keywords(self, text: str) -> bool:
        """テキストに謎を示唆するキーワードが含まれているか"""
        for keywords in self.FORESHADOWING_KEYWORDS.values():
            for keyword in keywords:
                if keyword in text:
                    return True
        return False

    def _is_foreshadowing_event(self, event: str) -> bool:
        """イベントが伏線として扱うべきか判定"""
        return self._contains_mystery_keywords(event) or "伏線" in event

    def _extract_description(self, data: object) -> str:
        """データから説明文を抽出"""
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            return data.get("description", "") or data.get("content", "") or str(data)
        return str(data)

    def _extract_foreshadowing_title(self, text: str) -> str:
        """テキストから伏線のタイトルを生成"""
        # 最初の20文字程度を使用
        title = text[:30] if len(text) > 30 else text
        # 改行を除去
        return title.replace("\n", " ").strip()

    def _create_event_foreshadowing(self, event: str, chapter_num: int) -> Foreshadowing | None:
        """イベントベースの伏線を作成"""
        self._foreshadowing_counter += 1
        foreshadowing_id = ForeshadowingId(f"F{self._foreshadowing_counter:03d}")

        return Foreshadowing(
            id=foreshadowing_id,
            title=self._extract_foreshadowing_title(event),
            category=ForeshadowingCategory.MAIN,
            description=event,
            importance=3,
            planting=PlantingInfo(
                episode=f"第{chapter_num * 5:03d}話",
                chapter=chapter_num,
                method="イベントの描写",
                content=event,
                subtlety_level=SubtletyLevel.MEDIUM,
            ),
            resolution=ResolutionInfo(
                episode=f"第{(chapter_num + 1) * 10:03d}話",
                chapter=chapter_num + 1,
                method="伏線の回収",
                impact="物語の理解が深まる",
            ),
            status=ForeshadowingStatus.PLANNED,
        )

    def _create_secret_foreshadowing(self, character_name: str, secret: object) -> Foreshadowing | None:
        """秘密に関する伏線を作成"""
        self._foreshadowing_counter += 1
        foreshadowing_id = ForeshadowingId(f"F{self._foreshadowing_counter:03d}")

        return Foreshadowing(
            id=foreshadowing_id,
            title=f"{character_name}の秘密",
            category=ForeshadowingCategory.CHARACTER,
            description=secret,
            importance=4,
            planting=PlantingInfo(
                episode="第003話",
                chapter=1,
                method="意味深な台詞や行動",
                content=f"{character_name}が何かを隠している様子",
                subtlety_level=SubtletyLevel.MEDIUM,
            ),
            resolution=ResolutionInfo(
                episode="第020話", chapter=2, method="秘密の暴露", impact=f"{character_name}の行動の真意が明らかになる"
            ),
            status=ForeshadowingStatus.PLANNED,
        )

    def _create_thematic_foreshadowing(self, theme: str, _theme_type: str) -> Foreshadowing | None:
        """テーマに関する伏線を作成"""
        self._foreshadowing_counter += 1
        foreshadowing_id = ForeshadowingId(f"F{self._foreshadowing_counter:03d}")

        return Foreshadowing(
            id=foreshadowing_id,
            title=f"テーマ「{theme}」の体現",
            category=ForeshadowingCategory.THEMATIC,
            description=f"物語全体を通じて{theme}というテーマを探求",
            importance=5,
            planting=PlantingInfo(
                episode="第001話",
                chapter=1,
                method="象徴的な描写やメタファー",
                content=f"{theme}を暗示する要素",
                subtlety_level=SubtletyLevel.HIGH,
            ),
            resolution=ResolutionInfo(
                episode="第030話", chapter=3, method="テーマの集大成", impact=f"{theme}という答えに到達"
            ),
            status=ForeshadowingStatus.PLANNED,
        )

    def _create_turning_point_foreshadowing(self, turning_point: str, index: int) -> Foreshadowing | None:
        """転換点に関する伏線を作成"""
        self._foreshadowing_counter += 1
        foreshadowing_id = ForeshadowingId(f"F{self._foreshadowing_counter:03d}")

        return Foreshadowing(
            id=foreshadowing_id,
            title=f"転換点: {turning_point}",
            category=ForeshadowingCategory.MAIN,
            description=turning_point,
            importance=4,
            planting=PlantingInfo(
                episode=f"第{(index + 1) * 2:03d}話",
                chapter=1,
                method="前兆となる出来事",
                content=f"{turning_point}への布石",
                subtlety_level=SubtletyLevel.MEDIUM,
            ),
            resolution=ResolutionInfo(
                episode=f"第{(index + 2) * 5:03d}話", chapter=2, method="転換点の到来", impact=turning_point
            ),
            status=ForeshadowingStatus.PLANNED,
        )

    def extract_from_chapter_plot(self, chapter_plot_data: dict[str, Any]) -> list[Foreshadowing]:
        """
        章別プロットデータから細かな伏線を抽出

        Args:
            chapter_plot_data: 章別プロット.yamlのデータ

        Returns:
            抽出された伏線のリスト
        """
        foreshadowings = []
        chapter_num = chapter_plot_data.get("metadata", {}).get("chapter_number", 1)

        # エピソードから伏線を抽出
        episode_foreshadowings = self._extract_episode_foreshadowings(chapter_plot_data, chapter_num)
        foreshadowings.extend(episode_foreshadowings)

        # 章の重要イベントから伏線を抽出
        event_foreshadowings = self._extract_event_foreshadowings(chapter_plot_data, chapter_num)
        foreshadowings.extend(event_foreshadowings)

        return foreshadowings

    def _extract_episode_foreshadowings(
        self, chapter_plot_data: dict[str, Any], chapter_num: int
    ) -> list[Foreshadowing]:
        """エピソードから伏線を抽出"""
        foreshadowings = []

        if "episodes" not in chapter_plot_data:
            return foreshadowings

        for episode in chapter_plot_data["episodes"]:
            episode_num = episode.get("number", 1)

            # エピソードタイトルから伏線を探す
            if "title" in episode and self._contains_mystery_keywords(episode["title"]):
                foreshadowing = self._create_episode_foreshadowing(
                    episode_title=episode["title"], episode_num=episode_num, chapter_num=chapter_num
                )
                if foreshadowing:
                    foreshadowings.append(foreshadowing)

            # シーンから伏線を探す
            scene_foreshadowings = self._extract_scene_foreshadowings(episode, episode_num, chapter_num)
            foreshadowings.extend(scene_foreshadowings)

        return foreshadowings

    def _extract_scene_foreshadowings(
        self, episode: dict[str, Any], episode_num: int, chapter_num: int
    ) -> list[Foreshadowing]:
        """シーンから伏線を抽出"""
        foreshadowings = []

        if "scenes" not in episode:
            return foreshadowings

        for scene in episode["scenes"]:
            if isinstance(scene, str) and self._contains_mystery_keywords(scene):
                foreshadowing = self._create_scene_foreshadowing(
                    scene_description=scene, episode_num=episode_num, chapter_num=chapter_num
                )
                if foreshadowing:
                    foreshadowings.append(foreshadowing)

        return foreshadowings

    def _extract_event_foreshadowings(self, chapter_plot_data: dict[str, Any], chapter_num: int) -> list[Foreshadowing]:
        """章の重要イベントから伏線を抽出"""
        foreshadowings = []

        if "key_events" not in chapter_plot_data:
            return foreshadowings

        for event in chapter_plot_data["key_events"]:
            if self._is_foreshadowing_event(event):
                foreshadowing = self._create_event_foreshadowing(event=event, chapter_num=chapter_num)
                if foreshadowing:
                    foreshadowings.append(foreshadowing)

        return foreshadowings

    def _create_episode_foreshadowing(
        self, episode_title: str, episode_num: int, chapter_num: int = 1
    ) -> Foreshadowing | None:
        """エピソードベースの伏線を作成"""
        self._foreshadowing_counter += 1
        foreshadowing_id = ForeshadowingId(f"F{self._foreshadowing_counter:03d}")

        return Foreshadowing(
            id=foreshadowing_id,
            title=f"第{episode_num}話: {episode_title}",
            category=ForeshadowingCategory.MAIN,
            description=episode_title,
            importance=2,  # 細かな伏線なので重要度は低め
            planting=PlantingInfo(
                episode=f"第{episode_num:03d}話",
                chapter=chapter_num,
                method="エピソードの展開",
                content=episode_title,
                subtlety_level=SubtletyLevel.LOW,
            ),
            resolution=ResolutionInfo(
                episode=f"第{episode_num + 10:03d}話",
                chapter=chapter_num + 1,
                method="後の展開で意味が明らかになる",
                impact="細部の繋がりが見える",
            ),
            status=ForeshadowingStatus.PLANNED,
        )

    def _create_scene_foreshadowing(
        self, scene_description: str, episode_num: int, chapter_num: int = 1
    ) -> Foreshadowing | None:
        """シーンベースの伏線を作成"""
        self._foreshadowing_counter += 1
        foreshadowing_id = ForeshadowingId(f"F{self._foreshadowing_counter:03d}")

        return Foreshadowing(
            id=foreshadowing_id,
            title=f"シーン: {scene_description}",
            category=ForeshadowingCategory.MAIN,
            description=scene_description,
            importance=1,  # 最も細かな伏線
            planting=PlantingInfo(
                episode=f"第{episode_num:03d}話",
                chapter=chapter_num,
                method="シーンの描写",
                content=scene_description,
                subtlety_level=SubtletyLevel.LOW,
            ),
            resolution=ResolutionInfo(
                episode=f"第{episode_num + 5:03d}話",
                chapter=chapter_num,
                method="関連シーンでの回収",
                impact="細かな演出の意図が分かる",
            ),
            status=ForeshadowingStatus.PLANNED,
        )
