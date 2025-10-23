#!/usr/bin/env python3
"""シーン管理エンティティ群

シーン管理に関するデータクラス・Enum・バリューオブジェクトの定義。
DDD原則に基づくドメインエンティティの分離。
"""

from dataclasses import dataclass, field
from enum import Enum


class SceneCategory(Enum):
    """シーンカテゴリー"""

    OPENING = "opening"  # 冒頭
    TURNING_POINT = "turning_point"  # 転換点
    CLIMAX = "climax"  # クライマックス
    EMOTIONAL = "emotional"  # 感動シーン
    ACTION = "action"  # アクションシーン
    MYSTERY = "mystery"  # 謎・伏線
    ENDING = "ending"  # エンディング
    FORESHADOWING = "foreshadowing"  # 伏線
    NORMAL = "normal"  # 通常シーン


@dataclass
class SceneInfo:
    """シーン情報"""

    scene_id: str
    category: SceneCategory
    title: str
    description: str
    episodes: list[int] = field(default_factory=list)
    sensory_details: dict[str, str] = field(default_factory=dict)
    emotional_arc: str | None = None
    key_dialogues: list[str] = field(default_factory=list)
    completion_status: str | None = None


@dataclass
class ValidationIssue:
    """検証エラー情報"""

    severity: str  # error, warning, info
    category: str
    scene_id: str | None = None
    message: str = ""
