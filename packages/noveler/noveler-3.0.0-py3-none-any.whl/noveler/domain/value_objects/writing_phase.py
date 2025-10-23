"""Domain.value_objects.writing_phase
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""執筆フェーズ値オブジェクト

SPEC-A30-STEPWISE-001に基づく執筆フェーズの値オブジェクト実装
"""


from enum import Enum


class WritingPhase(Enum):
    """執筆フェーズ列挙型

    段階的A30ガイド読み込み機能で使用する執筆フェーズを定義
    """

    DRAFT = "draft"
    REFINEMENT = "refinement"
    TROUBLESHOOTING = "troubleshooting"

    @classmethod
    def from_string(cls, value: str) -> WritingPhase:
        """文字列から執筆フェーズオブジェクトを生成

        Args:
            value: フェーズを表す文字列

        Returns:
            WritingPhase: 対応する執筆フェーズ

        Raises:
            ValueError: 不正なフェーズ文字列の場合
        """
        for phase in cls:
            if phase.value == value:
                return phase
        msg = f"Unknown writing phase: {value}"
        raise ValueError(msg)

    def is_lightweight(self) -> bool:
        """軽量処理フェーズかどうかを判定

        Returns:
            bool: 軽量処理が必要な場合True
        """
        return self == WritingPhase.DRAFT

    def requires_detailed_rules(self) -> bool:
        """詳細ルールが必要かどうかを判定

        Returns:
            bool: 詳細ルールが必要な場合True
        """
        return self in [WritingPhase.REFINEMENT]

    def requires_quality_checklist(self) -> bool:
        """品質チェックリストが必要かどうかを判定

        Returns:
            bool: 品質チェックリストが必要な場合True
        """
        return self in [WritingPhase.REFINEMENT]

    def requires_troubleshooting_guide(self) -> bool:
        """トラブルシューティングガイドが必要かどうかを判定

        Returns:
            bool: トラブルシューティングガイドが必要な場合True
        """
        return self == WritingPhase.TROUBLESHOOTING
        return self == WritingPhase.TROUBLESHOOTING

    def get_description(self) -> str:
        """フェーズの説明を取得

        Returns:
            str: フェーズの日本語説明
        """
        descriptions = {
            WritingPhase.DRAFT: "初稿フェーズ（軽量・高速処理）",
            WritingPhase.REFINEMENT: "仕上げフェーズ（詳細ルール・品質重視）",
            WritingPhase.TROUBLESHOOTING: "トラブルシューティングフェーズ（問題解決特化）",
        }
        return descriptions.get(self, "未定義フェーズ")

    def get_performance_target_improvement(self) -> float:
        """フェーズ別性能目標改善率を取得

        Returns:
            float: 期待される性能改善率（％）
        """
        targets = {
            WritingPhase.DRAFT: 50.0,  # 50%改善目標
            WritingPhase.REFINEMENT: 10.0,  # 10%改善目標（品質重視）
            WritingPhase.TROUBLESHOOTING: 25.0,  # 25%改善目標
        }
        return targets.get(self, 0.0)

    def get_expected_file_patterns(self) -> list[str]:
        """フェーズに応じた期待ファイルパターンを取得

        Returns:
            list[str]: 期待されるファイル名パターンのリスト
        """
        base_patterns = ["A30_執筆ガイド.yaml"]

        if self.requires_detailed_rules():
            base_patterns.append("A30_執筆ガイド（詳細ルール集）.yaml")

        if self.requires_quality_checklist():
            base_patterns.append("A30_執筆ガイド（ステージ別詳細チェック項目）.yaml")

        if self.requires_troubleshooting_guide():
            base_patterns.append("A30_執筆ガイド（シューティング事例集）.yaml")

        return base_patterns
