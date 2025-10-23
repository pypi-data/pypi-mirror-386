"""Domain.value_objects.backup_strategy
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

from __future__ import annotations

"""バックアップ戦略値オブジェクト

B20準拠実装 - Value Object Pattern
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from noveler.noveler.domain.value_objects.backup_type import BackupType

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, kw_only=True)
class BackupStrategy:
    """バックアップ戦略値オブジェクト

    B20準拠 Value Object:
    - 不変性（frozen=True）
    - 値の同一性による比較
    - ビジネスルール封じ込め
    """

    backup_type: BackupType
    target_paths: list[Path]
    exclude_patterns: list[str]
    compression_enabled: bool
    purpose: str
    retention_days: int

    def __post_init__(self) -> None:
        """初期化後検証 - ビジネスルール適用"""
        if not self.target_paths:
            msg = "バックアップ対象パスが必要です"
            raise ValueError(msg)

        if self.retention_days <= 0:
            msg = "保持日数は1日以上である必要があります"
            raise ValueError(msg)

        if not self.purpose.strip():
            msg = "バックアップ目的が必要です"
            raise ValueError(msg)

    def get_backup_name(self) -> str:
        """バックアップ名生成 - Functional Core（純粋関数）"""
        return f"{self.backup_type.value}_{self.purpose.replace(' ', '_').replace('　', '_')}"

    def should_exclude(self, path: Path) -> bool:
        """除外判定 - Functional Core（純粋関数）

        Args:
            path: 判定対象パス

        Returns:
            bool: True=除外、False=含める
        """
        path_str = str(path)

        return any(pattern in path_str for pattern in self.exclude_patterns)

    def calculate_estimated_size_mb(self, base_size_mb: float) -> float:
        """推定サイズ計算 - Functional Core（純粋関数）

        Args:
            base_size_mb: ベースサイズ（MB）

        Returns:
            float: 推定サイズ（MB）
        """
        # 除外パターンによる削減率推定
        reduction_rate = len(self.exclude_patterns) * 0.1  # 10%ずつ削減
        reduced_size = base_size_mb * (1 - min(reduction_rate, 0.8))  # 最大80%削減

        # 圧縮による削減
        if self.compression_enabled:
            return reduced_size * 0.6  # 圧縮で40%削減

        return reduced_size
