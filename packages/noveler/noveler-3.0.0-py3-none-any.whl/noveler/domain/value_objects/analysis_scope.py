#!/usr/bin/env python3
"""分析範囲値オブジェクト

統合コンテキスト分析での分析範囲を定義する値オブジェクト。
"""

from enum import Enum


class AnalysisScope(Enum):
    """分析範囲列挙型

    統合コンテキスト分析での分析の包括度を定義。
    """

    BASIC = "basic"
    """基本分析 - 主要項目のみ"""

    EXTENDED = "extended"
    """拡張分析 - 段階間関係を含む"""

    COMPREHENSIVE = "comprehensive"
    """包括的分析 - 全項目・全関係性を分析"""

    def get_item_limit(self) -> int:
        """分析項目数制限の取得

        Returns:
            int: 分析項目数上限（0は無制限）
        """
        limits = {
            AnalysisScope.BASIC: 20,
            AnalysisScope.EXTENDED: 40,
            AnalysisScope.COMPREHENSIVE: 0,  # 無制限
        }
        return limits[self]

    def includes_cross_phase_analysis(self) -> bool:
        """段階間分析の包含判定

        Returns:
            bool: 段階間分析を含むかどうか
        """
        return self in [AnalysisScope.EXTENDED, AnalysisScope.COMPREHENSIVE]

    def includes_context_preservation(self) -> bool:
        """コンテキスト保持の包含判定

        Returns:
            bool: 全文コンテキスト保持を行うかどうか
        """
        return self == AnalysisScope.COMPREHENSIVE

    def get_description(self) -> str:
        """分析範囲の説明取得

        Returns:
            str: 分析範囲の説明
        """
        descriptions = {
            AnalysisScope.BASIC: "基本的な項目別分析（高速）",
            AnalysisScope.EXTENDED: "段階間関係を含む拡張分析",
            AnalysisScope.COMPREHENSIVE: "全項目・全文コンテキスト統合分析（最高品質）",
        }
        return descriptions[self]
