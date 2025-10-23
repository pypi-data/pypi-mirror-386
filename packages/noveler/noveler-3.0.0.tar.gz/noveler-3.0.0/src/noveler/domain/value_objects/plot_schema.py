"""Domain.value_objects.plot_schema
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""プロットファイルのスキーマを定義する値オブジェクト

各種プロットファイルの必須項目と推奨項目を定義
"""


from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldDefinition:
    """フィールド定義"""

    name: str
    required: bool = True
    field_type: type = str
    description: str = ""
    default: object = None
    children: dict[str, FieldDefinition] = field(default_factory=dict)


@dataclass(frozen=True)
class PlotSchema:
    """プロットファイルのスキーマ"""

    schema_name: str
    fields: dict[str, FieldDefinition]
    description: str = ""

    def get_required_fields(self) -> list[str]:
        """必須フィールドのリストを取得"""
        return [name for name, field_def in self.fields.items() if field_def.required]

    def get_optional_fields(self) -> list[str]:
        """オプションフィールドのリストを取得"""
        return [name for name, field_def in self.fields.items() if not field_def.required]


# 全体構成のスキーマ定義
MASTER_PLOT_SCHEMA = PlotSchema(
    schema_name="master_plot",
    description="全体構成(マスタープロット)のスキーマ",
    fields={
        "title": FieldDefinition(
            name="title",
            required=True,
            field_type=str,
            description="作品タイトル",
        ),
        "genre": FieldDefinition(
            name="genre",
            required=True,
            field_type=str,
            description="ジャンル",
        ),
        "target_readers": FieldDefinition(
            name="target_readers",
            required=True,
            field_type=dict,
            description="ターゲット読者層",
        ),
        "story_concept": FieldDefinition(
            name="story_concept",
            required=True,
            field_type=dict,
            description="物語のコンセプト",
        ),
        "chapters": FieldDefinition(
            name="chapters",
            required=True,
            field_type=list,
            description="章構成",
        ),
        "themes": FieldDefinition(
            name="themes",
            required=False,
            field_type=dict,
            description="テーマ",
        ),
        "world_building": FieldDefinition(
            name="world_building",
            required=False,
            field_type=dict,
            description="世界観設定の概要",
        ),
    },
)


# 章別プロットのスキーマ定義
CHAPTER_PLOT_SCHEMA = PlotSchema(
    schema_name="chapter_plot",
    description="章別プロットのスキーマ",
    fields={
        "chapter_number": FieldDefinition(
            name="chapter_number",
            required=True,
            field_type=int,
            description="章番号",
        ),
        "title": FieldDefinition(
            name="title",
            required=True,
            field_type=str,
            description="章タイトル",
        ),
        "summary": FieldDefinition(
            name="summary",
            required=True,
            field_type=str,
            description="章の概要",
        ),
        "key_events": FieldDefinition(
            name="key_events",
            required=True,
            field_type=list,
            description="主要イベント",
        ),
        "episodes": FieldDefinition(
            name="episodes",
            required=True,
            field_type=list,
            description="話数構成",
        ),
        "character_arcs": FieldDefinition(
            name="character_arcs",
            required=False,
            field_type=dict,
            description="キャラクターアーク",
        ),
        "foreshadowing": FieldDefinition(
            name="foreshadowing",
            required=False,
            field_type=list,
            description="伏線",
        ),
    },
)


# 話数別プロットのスキーマ定義
EPISODE_PLOT_SCHEMA = PlotSchema(
    schema_name="episode_plot",
    description="話数別プロットのスキーマ",
    fields={
        "episode_number": FieldDefinition(
            name="episode_number",
            required=True,
            field_type=int,
            description="話数",
        ),
        "title": FieldDefinition(
            name="title",
            required=True,
            field_type=str,
            description="エピソードタイトル",
        ),
        "summary": FieldDefinition(
            name="summary",
            required=True,
            field_type=str,
            description="あらすじ",
        ),
        "scenes": FieldDefinition(
            name="scenes",
            required=True,
            field_type=list,
            description="シーン構成",
        ),
        "key_points": FieldDefinition(
            name="key_points",
            required=False,
            field_type=list,
            description="重要ポイント",
        ),
        "character_emotions": FieldDefinition(
            name="character_emotions",
            required=False,
            field_type=dict,
            description="キャラクターの感情変化",
        ),
    },
)


# スキーママッピング
PLOT_SCHEMAS = {
    "master_plot": MASTER_PLOT_SCHEMA,
    "chapter_plot": CHAPTER_PLOT_SCHEMA,
    "episode_plot": EPISODE_PLOT_SCHEMA,
}
