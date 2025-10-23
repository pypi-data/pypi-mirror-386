#!/usr/bin/env python3
"""JSON変換基底モデル"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ContentType(str, Enum):
    """サポートするコンテンツタイプ"""

    MARKDOWN = "text/markdown"
    YAML = "text/yaml"
    JSON = "application/json"
    PLAIN_TEXT = "text/plain"


class BaseJSONModel(BaseModel):
    """JSON変換用基底モデル（Pydantic v2対応）"""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    @model_validator(mode="after")
    def validate_model_consistency(self) -> "BaseJSONModel":
        """モデル整合性検証"""
        return self

    def to_json(self) -> str:
        """JSON文字列生成（カスタムエンコーダー付き）"""
        return self.model_dump_json(exclude_none=True, serialize_as_any=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseJSONModel":
        """辞書からモデル生成"""
        return cls(**data)


class TimestampMixin(BaseModel):
    """タイムスタンプミックスイン"""

    created_at: datetime = Field(default_factory=datetime.now, description="作成日時（ISO 8601）")

    updated_at: datetime | None = Field(default=None, description="更新日時（ISO 8601）")

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def validate_timestamp(cls, v):
        """タイムスタンプ形式検証"""
        if v is None:
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v
