"""差分更新エンティティ

RFC6902 JSON Patch形式とUnified Diff形式を組み合わせた
差分管理システムのコアエンティティ。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import jsonpatch


class UpdateType(Enum):
    """更新タイプの定義"""

    REVISION = "revision"  # 改稿
    CORRECTION = "correction"  # 誤字修正
    ENHANCEMENT = "enhancement"  # 品質向上
    STRUCTURAL = "structural"  # 構造変更


@dataclass
class DifferentialUpdate:
    """差分更新を表現するドメインモデル

    RFC6902準拠のJSON Patch形式で差分を管理し、
    Unified Diff形式で人間可読な表示を提供する。
    トークン効率を最大化しつつ、完全な変更追跡を実現。

    Attributes:
        update_id: 一意の更新識別子
        timestamp: 更新タイムスタンプ
        update_type: 更新の種類（改稿、誤字修正、品質向上、構造変更）
        target_step: 対象ステップ番号
        json_patch: RFC6902形式の差分操作リスト
        unified_diff: Unified Diff形式の表示用差分
        quality_delta: 品質メトリクス変化（オプション）
        token_saved: 節約されたトークン数（オプション）
        compression_ratio: 圧縮率（オプション）
        metadata: 追加メタデータ
    """

    update_id: str
    timestamp: datetime
    update_type: UpdateType
    target_step: int
    json_patch: list[dict[str, Any]]
    unified_diff: str
    quality_delta: dict[str, float] | None = None
    token_saved: int | None = None
    compression_ratio: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def apply_to(self, target: dict[str, Any]) -> dict[str, Any]:
        """差分を対象データに適用

        Args:
            target: 適用対象のデータ辞書

        Returns:
            差分適用後のデータ辞書

        Raises:
            ValueError: パッチ適用に失敗した場合
        """
        try:
            patch = jsonpatch.JsonPatch(self.json_patch)
            return patch.apply(target)
        except jsonpatch.JsonPatchException as e:
            error_message = f"パッチ適用エラー: {e}"
            raise ValueError(error_message) from e

    def generate_preview(self) -> str:
        """人間可読な差分プレビューを生成

        Returns:
            Unified Diff形式の差分文字列
        """
        return self.unified_diff

    def calculate_efficiency(self) -> dict[str, Any]:
        """更新の効率性メトリクスを計算

        Returns:
            効率性指標の辞書
        """
        return {
            "update_id": self.update_id,
            "token_saved": self.token_saved,
            "compression_ratio": self.compression_ratio,
            "operations_count": len(self.json_patch),
            "update_type": self.update_type.value,
            "timestamp": self.timestamp.isoformat(),
        }

    def validate(self) -> bool:
        """差分更新の妥当性を検証

        Returns:
            検証結果（True: 妥当、False: 不正）
        """
        # 必須フィールドの存在確認
        if not self.update_id or not self.json_patch:
            return False

        # JSON Patch操作の妥当性確認
        valid_ops = {"add", "remove", "replace", "move", "copy", "test"}
        for operation in self.json_patch:
            if "op" not in operation or operation["op"] not in valid_ops:
                return False
            if "path" not in operation:
                return False

        return True

    def __str__(self) -> str:
        """文字列表現"""
        return (
            f"DifferentialUpdate("
            f"id={self.update_id}, "
            f"type={self.update_type.value}, "
            f"step={self.target_step}, "
            f"ops={len(self.json_patch)}, "
            f"saved={self.token_saved or 0})"
        )

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換

        Returns:
            エンティティの辞書表現
        """
        return {
            "update_id": self.update_id,
            "timestamp": self.timestamp.isoformat(),
            "update_type": self.update_type.value,
            "target_step": self.target_step,
            "json_patch": self.json_patch,
            "unified_diff": self.unified_diff,
            "quality_delta": self.quality_delta,
            "token_saved": self.token_saved,
            "compression_ratio": self.compression_ratio,
            "metadata": self.metadata,
        }
