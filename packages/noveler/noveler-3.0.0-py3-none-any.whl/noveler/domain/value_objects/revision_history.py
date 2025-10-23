"""改稿履歴管理エンティティ

差分更新の履歴を管理し、ロールバック機能を提供する
ドメインエンティティ。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from noveler.domain.value_objects.differential_update import DifferentialUpdate


@dataclass
class RevisionHistory:
    """改稿履歴を管理するドメインエンティティ

    差分更新の履歴を保持し、任意の時点へのロールバックや
    変更履歴の分析機能を提供する。

    Attributes:
        history_id: 履歴の一意識別子
        step_number: 対象ステップ番号
        base_version: ベースとなるバージョンデータ
        updates: 適用された差分更新のリスト
        current_version: 現在のバージョンデータ
        created_at: 履歴作成日時
        metadata: 追加メタデータ
    """

    history_id: str
    step_number: int
    base_version: dict[str, Any]
    updates: list[DifferentialUpdate] = field(default_factory=list)
    current_version: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """初期化後処理"""
        if self.current_version is None:
            self.current_version = self.base_version.copy()

    def apply_update(self, update: DifferentialUpdate) -> dict[str, Any]:
        """差分更新を適用

        Args:
            update: 適用する差分更新

        Returns:
            更新後のバージョンデータ

        Raises:
            ValueError: 更新の適用に失敗した場合
        """
        if not update.validate():
            error_message = "無効な差分更新です"
            raise ValueError(error_message)

        if update.target_step != self.step_number:
            error_msg = f"ステップ番号が一致しません: 期待={self.step_number}, 実際={update.target_step}"
            raise ValueError(error_msg)

        # 現在のバージョンに差分を適用
        new_version = update.apply_to(self.current_version)

        # 履歴に追加
        self.updates.append(update)
        self.current_version = new_version

        return new_version

    def rollback(self, steps: int = 1) -> dict[str, Any]:
        """指定ステップ数だけロールバック

        Args:
            steps: ロールバックするステップ数

        Returns:
            ロールバック後のバージョンデータ

        Raises:
            ValueError: ロールバックが不可能な場合
        """
        if steps < 0:
            error_message = "ロールバックステップ数は0以上である必要があります"
            raise ValueError(error_message)

        if steps > len(self.updates):
            error_msg = f"ロールバック可能なステップ数を超えています: 最大={len(self.updates)}, 要求={steps}"
            raise ValueError(error_msg)

        if steps == 0:
            return self.current_version

        # ベースバージョンから再構築
        rebuilt_version = self.base_version.copy()

        # 指定位置までの更新を再適用
        updates_to_apply = self.updates[:-steps]
        for update in updates_to_apply:
            rebuilt_version = update.apply_to(rebuilt_version)

        # 履歴を更新
        self.updates = updates_to_apply
        self.current_version = rebuilt_version

        return rebuilt_version

    def get_update_at_index(self, index: int) -> DifferentialUpdate | None:
        """指定インデックスの更新を取得

        Args:
            index: 更新のインデックス

        Returns:
            差分更新オブジェクト、存在しない場合はNone
        """
        if 0 <= index < len(self.updates):
            return self.updates[index]
        return None

    def get_version_at_index(self, index: int) -> dict[str, Any]:
        """指定インデックス時点でのバージョンを取得

        Args:
            index: バージョンのインデックス（-1はベースバージョン）

        Returns:
            指定時点のバージョンデータ

        Raises:
            ValueError: 無効なインデックスの場合
        """
        if index < -1 or index >= len(self.updates):
            error_message = f"無効なインデックス: {index}"
            raise ValueError(error_message)

        if index == -1:
            return self.base_version.copy()

        # ベースから指定位置まで再構築
        version = self.base_version.copy()
        for i in range(index + 1):
            version = self.updates[i].apply_to(version)

        return version

    def get_total_token_saved(self) -> int:
        """総トークン節約量を計算

        Returns:
            全更新での総トークン節約量
        """
        total = 0
        for update in self.updates:
            if update.token_saved:
                total += update.token_saved
        return total

    def get_average_compression_ratio(self) -> float:
        """平均圧縮率を計算

        Returns:
            全更新の平均圧縮率
        """
        if not self.updates:
            return 0.0

        ratios = [update.compression_ratio for update in self.updates if update.compression_ratio is not None]

        if not ratios:
            return 0.0

        return sum(ratios) / len(ratios)

    def get_change_summary(self) -> str:
        """変更履歴のサマリーを生成

        Returns:
            フォーマットされた変更履歴サマリー
        """
        if not self.updates:
            return "変更履歴はありません"

        summary_lines = [
            "=== 改稿履歴サマリー ===",
            f"ステップ番号: {self.step_number}",
            f"総更新回数: {len(self.updates)}",
            f"総トークン節約: {self.get_total_token_saved()}",
            f"平均圧縮率: {self.get_average_compression_ratio():.2%}",
            "",
            "=== 更新履歴 ===",
        ]

        for i, update in enumerate(self.updates):
            summary_lines.append(
                f"{i + 1}. [{update.timestamp.strftime('%Y-%m-%d %H:%M')}] "
                f"{update.update_type.value} - "
                f"操作数: {len(update.json_patch)}, "
                f"節約: {update.token_saved or 0}トークン"
            )

        return "\n".join(summary_lines)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換

        Returns:
            履歴データの辞書表現
        """
        return {
            "history_id": self.history_id,
            "step_number": self.step_number,
            "base_version": self.base_version,
            "current_version": self.current_version,
            "updates": [update.to_dict() for update in self.updates],
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "statistics": {
                "total_updates": len(self.updates),
                "total_token_saved": self.get_total_token_saved(),
                "average_compression_ratio": self.get_average_compression_ratio(),
            },
        }
