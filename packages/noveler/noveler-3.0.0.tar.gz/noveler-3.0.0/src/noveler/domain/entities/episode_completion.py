#!/usr/bin/env python3

"""Domain.entities.episode_completion
Where: Domain entity describing episode completion status.
What: Tracks completion milestones and quality metrics.
Why: Supports reporting on episode readiness.
"""

from __future__ import annotations

"""執筆完了ドメインエンティティ
ビジネスロジックとルールの実装
"""


from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from noveler.domain.exceptions import EpisodeCompletionError
from noveler.domain.value_objects.episode_completion import (
    CharacterGrowthEvent,
    ForeshadowingStatus,
    GrowthType,
    ImportantScene,
    SceneType,
)
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

if TYPE_CHECKING:
    from noveler.domain.entities.scene_entity import Scene
    from noveler.domain.value_objects.episode_completion import EpisodeCompletionEvent

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass
class CharacterGrowthRecord:
    """キャラクター成長記録エンティティ"""

    character_name: str
    episode_number: int
    growth_type: GrowthType
    description: str
    importance: str
    auto_detected: bool
    recorded_at: datetime

    @classmethod
    def from_event(cls, episode_number: int, event: dict) -> CharacterGrowthRecord:
        """イベントから記録を作成"""
        return cls(
            character_name=event.character_name,
            episode_number=episode_number,
            growth_type=event.growth_type,
            description=event.description,
            importance=event.importance,
            auto_detected=event.auto_detected,
            recorded_at=project_now().datetime,
        )

    def to_persistence_dict(self) -> dict[str, Any]:
        """永続化用辞書変換"""
        return {
            "character": self.character_name,
            "episode": f"第{self.episode_number}話",
            "growth_type": self.growth_type.value,
            "description": self.description,
            "importance": self.importance,
            "auto_detected": self.auto_detected,
            "recorded_at": _to_naive_iso(self.recorded_at),
        }


@dataclass
class ImportantSceneRecord:
    """重要シーン記録エンティティ"""

    episode_number: int
    scene_id: str
    scene_type: SceneType
    description: str
    emotion_level: str
    tags: list[str]
    recorded_at: datetime

    @classmethod
    def from_scene(cls, episode_number: int, scene: Scene) -> ImportantSceneRecord:
        """シーンから記録を作成"""
        return cls(
            episode_number=episode_number,
            scene_id=scene.scene_id,
            scene_type=scene.scene_type,
            description=scene.description,
            emotion_level=scene.emotion_level,
            tags=list(scene.tags),
            recorded_at=project_now().datetime,
        )

    def calculate_importance(self) -> str:
        """シーンの重要度を計算"""
        score = 0

        # 感情レベルによるスコア
        if self.emotion_level == "high":
            score += 3
        elif self.emotion_level == "medium":
            score += 2
        else:
            score += 1

        # シーンタイプによるスコア
        if self.scene_type in [SceneType.TURNING_POINT, SceneType.CLIMAX]:
            score += 3
        elif self.scene_type in [SceneType.REVELATION, SceneType.CHARACTER_MOMENT]:
            score += 2
        else:
            score += 1

        # スコアを重要度に変換
        if score >= 6:
            return "critical"
        if score >= 3:
            return "high"
        return "medium"

    def to_persistence_dict(self) -> dict[str, Any]:
        """永続化用辞書変換"""
        return {
            "episode": f"第{self.episode_number}話",
            "scene_id": self.scene_id,
            "scene_type": self.scene_type.value,
            "description": self.description,
            "emotion_level": self.emotion_level,
            "importance": self.calculate_importance(),
            "tags": self.tags,
            "recorded_at": _to_naive_iso(self.recorded_at),
        }


@dataclass
class ForeshadowingRecord:
    """伏線記録エンティティ"""

    foreshadowing_id: str
    description: str
    status: ForeshadowingStatus
    planted_episode: int | None = None
    resolved_episode: int | None = None
    updated_at: datetime = field(default_factory=datetime.now)

    def plant(self, episode_number: int) -> None:
        """伏線を仕込む"""
        if self.status != ForeshadowingStatus.PLANNED:
            msg = f"Foreshadowing {self.foreshadowing_id} is already {self.status.value}"
            raise EpisodeCompletionError(episode_number, msg)

        self.status = ForeshadowingStatus.PLANTED
        self.planted_episode = episode_number
        self.updated_at = project_now().datetime

    def resolve(self, episode_number: int) -> None:
        """伏線を回収"""
        if self.status != ForeshadowingStatus.PLANTED:
            msg = f"Cannot resolve unplanted foreshadowing {self.foreshadowing_id}"
            raise EpisodeCompletionError(episode_number, msg)

        self.status = ForeshadowingStatus.RESOLVED
        self.resolved_episode = episode_number
        self.updated_at = project_now().datetime

    def abandon(self) -> None:
        """伏線を放棄"""
        self.status = ForeshadowingStatus.ABANDONED
        self.updated_at = project_now().datetime

    def to_persistence_dict(self) -> dict[str, Any]:
        """永続化用辞書変換"""
        episodes = []
        if self.planted_episode:
            episodes.append(self.planted_episode)
        if self.resolved_episode:
            episodes.append(self.resolved_episode)

        return {
            "id": self.foreshadowing_id,
            "description": self.description,
            "status": self.status.value,
            "planted_episode": self.planted_episode,
            "resolved_episode": self.resolved_episode,
            "episodes": episodes,
            "updated_at": _to_naive_iso(self.updated_at),
        }


class CompletedEpisode:
    """完了エピソードエンティティ(集約ルート)"""

    def __init__(self, episode_number: int, completion_event: EpisodeCompletionEvent) -> None:
        self.episode_number = episode_number
        self.status = "completed"
        self.completed_at = completion_event.completed_at
        self.quality_score = completion_event.quality_score
        self.word_count = completion_event.word_count
        self.plot_data = completion_event.plot_data or {}

        # 関連エンティティ
        self.character_growth_records: list[CharacterGrowthRecord] = []
        self.important_scenes: list[ImportantSceneRecord] = []
        self.foreshadowing_records: list[ForeshadowingRecord] = []

        # ドメインイベント
        self._domain_events: list[dict[str, Any]] = []
        self._warnings: list[str] = []

        # 初期イベント発行
        self._add_domain_event(
            {
                "type": "EpisodeCompleted",
                "episode_number": self.episode_number,
                "quality_score": float(self.quality_score),
                "word_count": self.word_count,
                "timestamp": project_now().datetime,
            }
        )

        # 品質チェック
        self._check_quality()

    @classmethod
    def create_from_event(cls, event: EpisodeCompletionEvent) -> CompletedEpisode:
        """イベントから作成"""
        return cls(event.episode_number, event)

    def add_character_growth(self, event: CharacterGrowthEvent) -> None:
        """キャラクター成長を追加"""
        record = CharacterGrowthRecord.from_event(self.episode_number, event)
        self.character_growth_records.append(record)

        self._add_domain_event(
            {
                "type": "CharacterGrowthAdded",
                "episode_number": self.episode_number,
                "character": event.character_name,
                "growth_type": event.growth_type.name.lower(),
            }
        )

    def add_important_scene(self, scene: Scene) -> None:
        """重要シーンを追加"""
        record = ImportantSceneRecord.from_scene(self.episode_number, scene)
        self.important_scenes.append(record)

        self._add_domain_event(
            {
                "type": "ImportantSceneAdded",
                "episode_number": self.episode_number,
                "scene_id": scene.scene_id,
                "scene_type": scene.scene_type.name.lower(),
            }
        )

    def plant_foreshadowing(self, foreshadowing_id: str, description: str) -> None:
        """伏線を仕込む"""
        # 既存の伏線をチェック
        existing = self._find_foreshadowing(foreshadowing_id)

        if existing:
            existing.plant(self.episode_number)
        else:
            record = ForeshadowingRecord(
                foreshadowing_id=foreshadowing_id,
                description=description,
                status=ForeshadowingStatus.PLANTED,
                planted_episode=self.episode_number,
            )

            self.foreshadowing_records.append(record)

        self._add_domain_event(
            {
                "type": "ForeshadowingPlanted",
                "episode_number": self.episode_number,
                "foreshadowing_id": foreshadowing_id,
            }
        )

    def resolve_foreshadowing(self, foreshadowing_id: str) -> None:
        """伏線を回収"""
        record = self._find_foreshadowing(foreshadowing_id)

        if not record:
            # 新規作成(他の話で仕込まれた伏線の回収)
            record = ForeshadowingRecord(
                foreshadowing_id=foreshadowing_id,
                description="",  # 後で更新される想定
                status=ForeshadowingStatus.PLANTED,
            )

            self.foreshadowing_records.append(record)

        record.resolve(self.episode_number)

        self._add_domain_event(
            {
                "type": "ForeshadowingResolved",
                "episode_number": self.episode_number,
                "foreshadowing_id": foreshadowing_id,
            }
        )

    def extract_from_plot_data(self) -> None:
        """プロットデータから情報を抽出"""
        if not self.plot_data:
            return

        # キャラクター成長
        for growth_data in self.plot_data.get("character_growth", []):
            growth_type = GrowthType[growth_data["type"].upper()]
            event = CharacterGrowthEvent(
                character_name=growth_data["character"],
                growth_type=growth_type,
                description=growth_data["description"],
                importance=growth_data.get("importance", "medium"),
            )

            self.add_character_growth(event)

        # 重要シーン
        for scene_data in self.plot_data.get("important_scenes", []):
            scene_type = SceneType[scene_data["type"].upper()]
            scene = ImportantScene(
                scene_id=scene_data["scene_id"],
                scene_type=scene_type,
                description=scene_data["description"],
                emotion_level=scene_data.get("emotion_level", "medium"),
                tags=scene_data.get("tags", []),
            )

            self.add_important_scene(scene)

        # 伏線
        foreshadowing_data: dict[str, Any] = self.plot_data.get("foreshadowing", {})
        for foreshadowing_id in foreshadowing_data.get("planted", []):
            self.plant_foreshadowing(foreshadowing_id, "")

        for foreshadowing_id in foreshadowing_data.get("resolved", []):
            self.resolve_foreshadowing(foreshadowing_id)

    def has_quality_warning(self) -> bool:
        """品質警告の有無"""
        return len(self._warnings) > 0

    def get_warnings(self) -> list[str]:
        """警告リストを取得"""
        return list(self._warnings)

    def get_domain_events(self) -> list[dict[str, Any]]:
        """ドメインイベントを取得"""
        return list(self._domain_events)

    def clear_domain_events(self) -> None:
        """ドメインイベントをクリア"""
        self._domain_events.clear()

    def _find_foreshadowing(self, foreshadowing_id: str) -> ForeshadowingRecord | None:
        """伏線レコードを検索"""
        for record in self.foreshadowing_records:
            if record.foreshadowing_id == foreshadowing_id:
                return record
        return None

    def _add_domain_event(self, event: dict[str, Any]) -> None:
        """ドメインイベントを追加"""
        self._domain_events.append(event)

    def _check_quality(self) -> None:
        """品質チェック"""
        if self.quality_score < Decimal("80"):
            self._warnings.append("low_quality")

        if self.word_count < 3000:
            self._warnings.append("low_word_count")
        elif self.word_count > 8000:
            self._warnings.append("high_word_count")

    def to_persistence_dict(self) -> dict[str, Any]:
        """永続化用辞書変換"""
        return {
            "episode_number": self.episode_number,
            "status": self.status,
            "completed_at": _to_naive_iso(self.completed_at),
            "quality_score": float(self.quality_score),
            "word_count": self.word_count,
            "character_growth": [r.to_persistence_dict() for r in self.character_growth_records],
            "important_scenes": [s.to_persistence_dict() for s in self.important_scenes],
            "foreshadowing": [f.to_persistence_dict() for f in self.foreshadowing_records],
            "warnings": self._warnings,
        }


def _to_naive_iso(value: datetime) -> str:
    """タイムゾーン情報を取り除いたISO文字列を返す"""
    dt = value
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt.isoformat()
