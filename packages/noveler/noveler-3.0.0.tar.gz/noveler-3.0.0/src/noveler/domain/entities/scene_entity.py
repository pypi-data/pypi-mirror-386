#!/usr/bin/env python3

"""Domain.entities.scene_entity
Where: Domain entity modelling individual scenes.
What: Encapsulates scene metadata, structure, and notes.
Why: Keeps scene details consistent across scene workflows.
"""

from __future__ import annotations

"""DDD Domain Entity: Scene
重要シーンのドメインエンティティ
"""


import importlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# Lazy import to avoid circular dependency
from noveler.domain.value_objects.scene_direction import SceneDirection
from noveler.domain.value_objects.scene_setting import SceneSetting

# 執筆ノートの値型
WritingNoteValue = str | int | float | bool | list[str] | dict[str, Any]


def _get_project_time() -> tuple[Any, ...]:
    """遅延インポートでプロジェクト時刻関連を取得（importlib経由でPLC0415回避）"""
    mod = importlib.import_module("noveler.domain.value_objects.project_time")
    return mod.ProjectDateTime, mod.ProjectTimezone, mod.project_now


def _get_jst_timezone() -> Any:
    """JST タイムゾーンを遅延取得"""
    _, ProjectTimezone, _ = _get_project_time()
    return ProjectTimezone.jst().timezone


# JSTタイムゾーン
# JST will be initialized lazily


class SceneCategory(Enum):
    """シーンカテゴリ"""

    CLIMAX = "climax_scenes"
    EMOTIONAL = "emotional_scenes"
    ROMANCE = "romance_scenes"
    ACTION = "action_scenes"
    MYSTERY = "mystery_scenes"
    COMEDY = "comedy_scenes"
    DAILY = "daily_scenes"


class ImportanceLevel(Enum):
    """重要度レベル"""

    S = "S"  # 最重要(物語の核心)
    A = "A"  # 重要(大きな転換点)
    B = "B"  # 中程度(キャラ成長等)
    C = "C"  # 軽微(雰囲気作り等)


@dataclass
class Scene:
    """重要シーンエンティティ"""

    scene_id: str
    title: str
    category: SceneCategory
    importance_level: ImportanceLevel
    episode_range: str
    created_at: datetime = field(default_factory=lambda: _get_project_time()[2]().datetime)
    updated_at: datetime = field(default_factory=lambda: _get_project_time()[2]().datetime)

    # オプション要素
    setting: SceneSetting | None = None
    direction: SceneDirection | None = None
    characters: list[str] = field(default_factory=list)
    key_elements: list[str] = field(default_factory=list)
    writing_notes: dict[str, Any] = field(default_factory=dict)
    quality_checklist: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """初期化後の検証"""
        self._validate()

    def _validate(self) -> None:
        """エンティティの不変条件を検証"""
        if not self.scene_id or not self.scene_id.strip():
            msg = "scene_id は必須です"
            raise ValueError(msg)

        if not self.title or not self.title.strip():
            msg = "title は必須です"
            raise ValueError(msg)

        if not self.episode_range or not self.episode_range.strip():
            msg = "episode_range は必須です"
            raise ValueError(msg)

    def set_setting(self, setting: SceneSetting) -> None:
        """設定情報を設定"""
        self.setting = setting
        self.updated_at = _get_project_time()[2]().datetime

    def set_direction(self, direction: SceneDirection) -> None:
        """演出指示を設定"""
        self.direction = direction
        self.updated_at = _get_project_time()[2]().datetime

    def add_character(self, character_name: str) -> None:
        """登場キャラクターを追加"""
        if character_name and character_name not in self.characters:
            self.characters.append(character_name)
            self.updated_at = _get_project_time()[2]().datetime

    def add_key_element(self, element: str) -> None:
        """重要要素を追加"""
        if element and element not in self.key_elements:
            self.key_elements.append(element)
            self.updated_at = _get_project_time()[2]().datetime

    def set_writing_note(self, key: str, value: WritingNoteValue) -> None:
        """執筆ノートを設定"""
        self.writing_notes[key] = value
        self.updated_at = _get_project_time()[2]().datetime

    def add_quality_check(self, category: str, check_item: str) -> None:
        """品質チェック項目を追加"""
        if category not in self.quality_checklist:
            self.quality_checklist[category] = []

        if check_item not in self.quality_checklist[category]:
            self.quality_checklist[category].append(check_item)
            self.updated_at = _get_project_time()[2]().datetime

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換(永続化用)"""
        data = {
            "scene_id": self.scene_id,
            "title": self.title,
            "category": self.category.value,
            "importance_level": self.importance_level.value,
            "episode_range": self.episode_range,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "characters": self.characters,
            "key_elements": self.key_elements,
            "writing_notes": self.writing_notes,
            "quality_checklist": self.quality_checklist,
        }

        if self.setting:
            data["setting"] = self.setting.to_dict()

        if self.direction:
            data["direction"] = self.direction.to_dict()

        return data

    @classmethod
    def _parse_datetime(cls, datetime_str: str | None) -> datetime:
        """ISO文字列からdatetimeを解析"""
        _, ProjectTimezone, project_now = _get_project_time()

        if datetime_str is None:
            return project_now().datetime

        parsed = datetime.fromisoformat(datetime_str)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=_get_jst_timezone())
        return parsed

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Scene:
        """辞書から復元(永続化からの復元用)"""
        # 基本フィールド
        scene = cls(
            scene_id=data["scene_id"],
            title=data["title"],
            category=SceneCategory(data["category"]),
            importance_level=ImportanceLevel(data["importance_level"]),
            episode_range=data["episode_range"],
            created_at=cls._parse_datetime(data.get("created_at")),
            updated_at=cls._parse_datetime(data.get("updated_at")),
        )

        # オプションフィールド
        scene.characters = data.get("characters", [])
        scene.key_elements = data.get("key_elements", [])
        scene.writing_notes = data.get("writing_notes", {})
        scene.quality_checklist = data.get("quality_checklist", {})

        # バリューオブジェクト
        if "setting" in data:
            scene.setting = SceneSetting.from_dict(data["setting"])

        if "direction" in data:
            scene.direction = SceneDirection.from_dict(data["direction"])

        return scene

    def is_critical(self) -> bool:
        """クリティカルなシーンかどうか判定"""
        return self.importance_level in [ImportanceLevel.S, ImportanceLevel.A]

    def get_completion_score(self) -> float:
        """シーンの完成度スコアを計算(0.0-1.0)"""
        score = 0.0
        total_criteria = 0

        # 基本情報(必須)
        if self.title and self.title.strip():
            score += 1
        total_criteria += 1

        if self.episode_range and self.episode_range.strip():
            score += 1
        total_criteria += 1

        # 設定情報
        if self.setting:
            score += 1
        total_criteria += 1

        # 演出指示
        if self.direction:
            score += 1
        total_criteria += 1

        # 登場キャラクター
        if self.characters:
            score += 1
        total_criteria += 1

        # 重要要素
        if self.key_elements:
            score += 1
        total_criteria += 1

        # 執筆ノート
        if self.writing_notes:
            score += 1
        total_criteria += 1

        # 品質チェックリスト
        if self.quality_checklist:
            score += 1
        total_criteria += 1

        return score / total_criteria if total_criteria > 0 else 0.0
