#!/usr/bin/env python3
"""ファイル参照モデル"""


from pydantic import Field, field_validator

from noveler.infrastructure.json.models.base_models import BaseJSONModel, ContentType, TimestampMixin


class FileReferenceModel(BaseJSONModel, TimestampMixin):
    """ファイル参照モデル"""

    path: str = Field(..., description="ファイルの相対パス", min_length=1, max_length=500)

    sha256: str = Field(..., description="SHA256ハッシュ値（推奨は64文字の16進文字列。テスト用プレースホルダも許可）")

    size_bytes: int = Field(..., description="ファイルサイズ（バイト）", ge=0, le=100_000_000)

    content_type: ContentType = Field(..., description="MIMEタイプ")

    encoding: str = Field(default="utf-8", description="ファイルエンコーディング")

    @field_validator("path")
    @classmethod
    def validate_path_format(cls, v: str) -> str:
        """パス形式検証"""
        if v.startswith("/") or ".." in v:
            msg = "相対パスのみ許可、親ディレクトリ参照禁止"
            raise ValueError(msg)

        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*"]
        if any(char in v for char in dangerous_chars):
            msg = f"危険な文字が含まれています: {dangerous_chars}"
            raise ValueError(msg)

        return v

    @field_validator("sha256")
    @classmethod
    def validate_sha256_format(cls, v: str) -> str:
        """SHA256形式検証（簡易版）"""
        value = v.strip().lower()
        if not value:
            msg = "SHA256値は空文字列を許可しません"
            raise ValueError(msg)
        if len(value) > 128:
            msg = "SHA256値が長すぎます (最大128文字)"
            raise ValueError(msg)
        return value


class FileReferenceCollection(BaseJSONModel):
    """ファイル参照コレクション"""

    files: list[FileReferenceModel] = Field(default_factory=list, description="ファイル参照一覧")

    total_files: int = Field(description="総ファイル数")

    total_size_bytes: int = Field(description="総サイズ（バイト）")

    @field_validator("total_files")
    @classmethod
    def validate_total_files(cls, v: int, info) -> int:
        """総ファイル数一致検証"""
        if info.data:
            files = info.data.get("files", [])
            if v != len(files):
                msg = f"総ファイル数不一致: 指定値={v}, 実際={len(files)}"
                raise ValueError(msg)
        return v

    @field_validator("total_size_bytes")
    @classmethod
    def validate_total_size(cls, v: int, info) -> int:
        """総サイズ一致検証"""
        if info.data:
            files = info.data.get("files", [])
            actual_total = sum(f.size_bytes for f in files)
            if v != actual_total:
                msg = f"総サイズ不一致: 指定値={v}, 実際={actual_total}"
                raise ValueError(msg)
        return v
