#!/usr/bin/env python3
"""レスポンスモデル"""

from typing import Any

from pydantic import Field, field_validator

from noveler.infrastructure.json.models.base_models import BaseJSONModel, TimestampMixin
from noveler.infrastructure.json.models.file_reference_models import FileReferenceCollection


class StandardResponseModel(BaseJSONModel, TimestampMixin):
    """標準レスポンスモデル"""

    success: bool = Field(..., description="実行成功フラグ")

    command: str = Field(..., description="実行されたコマンド", min_length=1, max_length=200)

    execution_time_ms: float = Field(..., description="実行時間（ミリ秒）", ge=0.0)

    outputs: FileReferenceCollection = Field(
        default_factory=FileReferenceCollection, description="出力ファイル参照コレクション"
    )

    metadata: dict[str, Any] = Field(default_factory=dict, description="追加メタデータ")

    @field_validator("command")
    @classmethod
    def validate_command_format(cls, v: str) -> str:
        """コマンド形式検証"""
        # 許可されたコマンドプレフィックス
        allowed_prefixes = ["novel", "check", "plot", "quality"]
        if not any(v.startswith(prefix) for prefix in allowed_prefixes):
            msg = f"許可されていないコマンド: {v}"
            raise ValueError(msg)
        return v


class ErrorDetailModel(BaseJSONModel):
    """エラー詳細モデル"""

    code: str = Field(..., description="エラーコード")

    message: str = Field(..., description="エラーメッセージ（日本語）", min_length=1, max_length=500)

    hint: str = Field(..., description="解決方法ヒント（日本語）", min_length=1, max_length=1000)

    details: dict[str, Any] | None = Field(default=None, description="詳細情報")

    stack_trace: str | None = Field(default=None, description="スタックトレース（開発時のみ）")


class ErrorResponseModel(BaseJSONModel, TimestampMixin):
    """エラーレスポンスモデル"""

    success: bool = Field(False, description="実行成功フラグ（常にFalse）")

    error: ErrorDetailModel = Field(..., description="エラー詳細")

    command: str = Field(..., description="実行されたコマンド")
