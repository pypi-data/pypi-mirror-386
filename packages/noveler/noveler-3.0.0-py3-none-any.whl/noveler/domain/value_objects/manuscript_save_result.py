# File: src/noveler/domain/value_objects/manuscript_save_result.py
# Purpose: Value object representing the result of a manuscript save operation
# Context: Provides type-safe return values instead of dict[str, Any]

"""原稿保存結果 Value Object

保存操作の結果を型安全に表現する。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class ManuscriptSaveResult:
    """原稿保存結果 Value Object

    保存操作の結果を不変オブジェクトとして表現する。

    Attributes:
        status: 保存状態（success, skipped, failed）
        message: 人間可読なメッセージ
        path: 保存先パス（成功時のみ）
        error: エラーメッセージ（失敗時のみ）
    """

    status: Literal["success", "skipped", "failed"]
    message: str
    path: str | None = None
    error: str | None = None

    @classmethod
    def success(cls, path: str, message: str = "Manuscript saved successfully") -> ManuscriptSaveResult:
        """保存成功の結果を作成

        Args:
            path: 保存先パス
            message: 成功メッセージ

        Returns:
            ManuscriptSaveResult: 成功結果
        """
        return cls(status="success", message=message, path=path)

    @classmethod
    def skipped(cls, reason: str) -> ManuscriptSaveResult:
        """保存スキップの結果を作成

        Args:
            reason: スキップ理由

        Returns:
            ManuscriptSaveResult: スキップ結果
        """
        return cls(
            status="skipped",
            message=f"Manuscript save skipped: {reason}"
        )

    @classmethod
    def failed(cls, error: str, message: str = "Manuscript save failed") -> ManuscriptSaveResult:
        """保存失敗の結果を作成

        Args:
            error: エラーメッセージ
            message: 失敗メッセージ

        Returns:
            ManuscriptSaveResult: 失敗結果
        """
        return cls(status="failed", message=message, error=error)

    def is_success(self) -> bool:
        """保存が成功したか判定

        Returns:
            bool: 成功した場合True
        """
        return self.status == "success"

    def is_skipped(self) -> bool:
        """保存がスキップされたか判定

        Returns:
            bool: スキップされた場合True
        """
        return self.status == "skipped"

    def is_failed(self) -> bool:
        """保存が失敗したか判定

        Returns:
            bool: 失敗した場合True
        """
        return self.status == "failed"

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換（後方互換性のため）

        Returns:
            dict[str, Any]: 結果辞書
        """
        result = {
            "manuscript_saved": self.is_success(),
        }

        if self.is_skipped():
            result["manuscript_save_skipped"] = True

        if self.error:
            result["manuscript_save_error"] = self.error

        if self.path:
            result["manuscript_path"] = self.path

        return result

    def apply_to_result_dict(self, result: dict[str, Any]) -> None:
        """既存の結果辞書に適用（副作用あり）

        Args:
            result: 更新対象の辞書
        """
        result.update(self.to_dict())

    def __str__(self) -> str:
        """人間可読な文字列表現"""
        if self.is_success():
            return f"Success: {self.message} (path={self.path})"
        elif self.is_skipped():
            return f"Skipped: {self.message}"
        else:
            return f"Failed: {self.message} (error={self.error})"

    def __repr__(self) -> str:
        """開発用の文字列表現"""
        return (
            f"ManuscriptSaveResult(status={self.status!r}, "
            f"message={self.message!r}, path={self.path!r}, error={self.error!r})"
        )
