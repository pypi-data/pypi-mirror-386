"""
マージ戦略値オブジェクト

プロットファイルのマージ戦略を表現する値オブジェクト
"""

from enum import Enum


class MergeStrategy(Enum):
    """マージ戦略の種類"""

    MERGE = "merge"  # 既存内容と新規内容をマージ(デフォルト)
    REPLACE = "replace"  # 既存内容を完全に置き換え
    APPEND = "append"  # 既存内容の後に追加

    @property
    def is_safe(self) -> bool:
        """安全な戦略かどうか(既存データを保持するか)"""
        return self != MergeStrategy.REPLACE

    @property
    def requires_confirmation(self) -> bool:
        """ユーザー確認が必要かどうか"""
        return self == MergeStrategy.REPLACE
