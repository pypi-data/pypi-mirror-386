#!/usr/bin/env python3
"""A31自動修正戦略値オブジェクト

SPEC-QUALITY-001に基づく自動修正戦略の表現。
修正レベル、優先度、対応可否を管理。
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AutoFixStrategy:
    """自動修正戦略値オブジェクト

    A31チェックリスト項目の自動修正アプローチを定義。
    安全性レベルと優先度を組み合わせた戦略を提供。
    """

    supported: bool
    fix_level: str  # "safe", "standard", "interactive", "none"
    priority: int  # 1が最高優先度、0は修正なし

    def __post_init__(self) -> None:
        """初期化後の検証"""
        self._validate_strategy()

    def _validate_strategy(self) -> None:
        """戦略の妥当性検証"""
        valid_levels = {"safe", "standard", "interactive", "none"}
        if self.fix_level not in valid_levels:
            msg = f"fix_level '{self.fix_level}' は {valid_levels} のいずれかである必要があります"
            raise ValueError(msg)

        if self.priority < 0:
            msg = f"priority は0以上である必要があります: {self.priority}"
            raise ValueError(msg)

        # 整合性チェック
        if not self.supported and self.fix_level != "none":
            msg = "supported=False の場合、fix_level は 'none' である必要があります"
            raise ValueError(msg)

        if not self.supported and self.priority != 0:
            msg = "supported=False の場合、priority は 0 である必要があります"
            raise ValueError(msg)

    def is_safe_fix(self) -> bool:
        """安全な修正かの判定

        Returns:
            bool: 安全な修正レベルの場合True
        """
        return self.supported and self.fix_level == "safe"

    def requires_confirmation(self) -> bool:
        """確認が必要な修正かの判定

        Returns:
            bool: 対話的確認が必要な場合True
        """
        return self.supported and self.fix_level == "interactive"

    def is_pattern_based(self) -> bool:
        """パターンベース修正かの判定

        Returns:
            bool: パターンベース修正の場合True
        """
        return self.supported and self.fix_level == "standard"

    def get_risk_level(self) -> str:
        """リスクレベルの取得

        Returns:
            str: リスクレベル("low", "medium", "high", "none")
        """
        if not self.supported:
            return "none"

        risk_map = {"safe": "low", "standard": "medium", "interactive": "high"}
        return risk_map.get(self.fix_level, "none")

    def to_dict(self) -> dict[str, Any]:
        """辞書形式への変換

        Returns:
            Dict[str, Any]: 戦略データの辞書表現
        """
        return {"supported": self.supported, "fix_level": self.fix_level, "priority": self.priority}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AutoFixStrategy":
        """辞書からの復元

        Args:
            data: 戦略データの辞書

        Returns:
            AutoFixStrategy: 復元された戦略インスタンス
        """
        return cls(supported=data["supported"], fix_level=data["fix_level"], priority=data["priority"])

    @classmethod
    def create_safe_strategy(cls, priority: int = 1) -> "AutoFixStrategy":
        """安全な修正戦略の作成

        Args:
            priority: 優先度

        Returns:
            AutoFixStrategy: 安全な修正戦略
        """
        return cls(supported=True, fix_level="safe", priority=priority)

    @classmethod
    def create_standard_strategy(cls, priority: int = 2) -> "AutoFixStrategy":
        """標準修正戦略の作成

        Args:
            priority: 優先度

        Returns:
            AutoFixStrategy: 標準修正戦略
        """
        return cls(supported=True, fix_level="standard", priority=priority)

    @classmethod
    def create_interactive_strategy(cls, priority: int = 3) -> "AutoFixStrategy":
        """対話的修正戦略の作成

        Args:
            priority: 優先度

        Returns:
            AutoFixStrategy: 対話的修正戦略
        """
        return cls(supported=True, fix_level="interactive", priority=priority)

    @classmethod
    def create_manual_strategy(cls) -> "AutoFixStrategy":
        """手動チェック戦略の作成

        Returns:
            AutoFixStrategy: 手動チェック戦略
        """
        return cls(supported=False, fix_level="none", priority=0)
