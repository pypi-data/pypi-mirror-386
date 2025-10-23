"""Domain.value_objects.prompt_save_result
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""プロンプト保存結果バリューオブジェクト

DDD準拠: Domain層のvalue object
プロンプト保存操作の結果データの不変性を保証
"""


from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class PromptSaveResult:
    """プロンプト保存結果バリューオブジェクト"""

    success: bool  # 保存成功フラグ
    file_path: Path | None = None  # 保存先ファイルパス
    error_message: str | None = None  # エラーメッセージ
    file_size_bytes: int = 0  # ファイルサイズ（バイト）

    def __post_init__(self) -> None:
        """後初期化バリデーション"""
        if self.file_size_bytes < 0:
            msg = "file_size_bytes must be non-negative"
            raise ValueError(msg)

        if self.success and self.file_path is None:
            msg = "file_path is required when success is True"
            raise ValueError(msg)

        if not self.success and self.error_message is None:
            msg = "error_message is required when success is False"
            raise ValueError(msg)

    def is_large_file(self, threshold_kb: int = 100) -> bool:
        """大きなファイル判定

        Args:
            threshold_kb: 閾値（KB）

        Returns:
            bool: 指定サイズを超える場合True
        """
        return self.file_size_bytes > threshold_kb * 1024

    def get_file_size_kb(self) -> float:
        """ファイルサイズをKB単位で取得

        Returns:
            float: ファイルサイズ（KB）
        """
        return self.file_size_bytes / 1024.0

    def get_file_size_mb(self) -> float:
        """ファイルサイズをMB単位で取得

        Returns:
            float: ファイルサイズ（MB）
        """
        return self.file_size_bytes / (1024.0 * 1024.0)

    @classmethod
    def create_success(cls, file_path: Path, file_size_bytes: int = 0) -> PromptSaveResult:
        """成功結果作成ファクトリ

        Args:
            file_path: 保存先ファイルパス
            file_size_bytes: ファイルサイズ

        Returns:
            PromptSaveResult: 成功結果
        """
        return cls(success=True, file_path=file_path, file_size_bytes=file_size_bytes)

    @classmethod
    def create_failure(cls, error_message: str) -> PromptSaveResult:
        """失敗結果作成ファクトリ

        Args:
            error_message: エラーメッセージ

        Returns:
            PromptSaveResult: 失敗結果
        """
        return cls(success=False, error_message=error_message)
