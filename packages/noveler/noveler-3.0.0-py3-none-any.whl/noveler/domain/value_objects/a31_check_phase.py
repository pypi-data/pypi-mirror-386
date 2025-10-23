#!/usr/bin/env python3
"""品質チェックフェーズ バリューオブジェクト（旧称A31CheckPhase）

品質チェックの各フェーズを定義し、
フェーズ固有のビジネスロジックを提供するバリューオブジェクト。
"""

from enum import Enum


class QualityCheckPhase(Enum):
    """A31チェックフェーズ列挙型

    A31チェックリストの実行フェーズを定義し、
    各フェーズの特性と優先度を管理する。
    """

    # Phase 0: 自動執筆開始
    PHASE0_AUTO_START = "Phase0_自動執筆開始（推奨）"

    # Phase 1: 構造チェック
    PHASE1_STRUCTURE = "Phase1_構造チェック"
    STRUCTURE_CHECK = "structure_check"  # 汎用構造チェック

    # Phase 2: 執筆フェーズ
    PHASE2_WRITING = "Phase2_執筆"
    WRITING_PHASE = "writing_phase"

    # Phase 3: 校正・推敲
    PHASE3_REVISION = "Phase3_校正推敲"
    REVISION_PHASE = "revision_phase"

    # Stage 1: 基本品質チェック
    STAGE1_BASIC_QUALITY = "Stage1_基本品質"
    BASIC_QUALITY_CHECK = "basic_quality_check"

    # Stage 2: コンテンツ詳細チェック
    STAGE2_CONTENT = "Stage2_コンテンツ詳細"
    CONTENT_DETAIL_CHECK = "content_detail_check"

    # Stage 3: 最終仕上げ
    STAGE3_FINAL = "Stage3_最終仕上げ"
    FINAL_POLISH = "final_polish"

    # 品質チェック統合フェーズ
    QUALITY_INTEGRATION = "quality_integration"
    CLAUDE_ANALYSIS = "claude_analysis"

    def get_display_name(self) -> str:
        """フェーズ表示名取得

        Returns:
            str: 日本語での表示名
        """
        display_names = {
            self.PHASE0_AUTO_START: "自動執筆開始",
            self.PHASE1_STRUCTURE: "構造チェック",
            self.STRUCTURE_CHECK: "構造チェック",
            self.PHASE2_WRITING: "執筆フェーズ",
            self.WRITING_PHASE: "執筆フェーズ",
            self.PHASE3_REVISION: "校正・推敲",
            self.REVISION_PHASE: "校正・推敲",
            self.STAGE1_BASIC_QUALITY: "基本品質チェック",
            self.BASIC_QUALITY_CHECK: "基本品質チェック",
            self.STAGE2_CONTENT: "コンテンツ詳細チェック",
            self.CONTENT_DETAIL_CHECK: "コンテンツ詳細チェック",
            self.STAGE3_FINAL: "最終仕上げ",
            self.FINAL_POLISH: "最終仕上げ",
            self.QUALITY_INTEGRATION: "品質統合",
            self.CLAUDE_ANALYSIS: "Claude分析",
        }
        return display_names.get(self, self.value)

    def get_priority_weight(self) -> float:
        """フェーズ優先度重み取得

        Returns:
            float: フェーズの優先度重み（0.0-1.0）
        """
        weights = {
            self.PHASE0_AUTO_START: 0.3,
            self.PHASE1_STRUCTURE: 0.7,
            self.STRUCTURE_CHECK: 0.7,
            self.PHASE2_WRITING: 0.9,
            self.WRITING_PHASE: 0.9,
            self.PHASE3_REVISION: 0.8,
            self.REVISION_PHASE: 0.8,
            self.STAGE1_BASIC_QUALITY: 0.6,
            self.BASIC_QUALITY_CHECK: 0.6,
            self.STAGE2_CONTENT: 0.8,
            self.CONTENT_DETAIL_CHECK: 0.8,
            self.STAGE3_FINAL: 0.9,
            self.FINAL_POLISH: 0.9,
            self.QUALITY_INTEGRATION: 0.7,
            self.CLAUDE_ANALYSIS: 0.8,
        }
        return weights.get(self, 0.5)

    def is_analysis_phase(self) -> bool:
        """分析フェーズ判定

        Returns:
            bool: Claude分析に適したフェーズの場合True
        """
        analysis_phases = {
            self.PHASE2_WRITING,
            self.PHASE3_REVISION,
            self.STAGE2_CONTENT,
            self.STAGE3_FINAL,
            self.CLAUDE_ANALYSIS,
            self.QUALITY_INTEGRATION,
        }
        return self in analysis_phases

    def get_typical_check_count(self) -> int:
        """標準チェック項目数取得

        Returns:
            int: このフェーズの標準的なチェック項目数
        """
        typical_counts = {
            self.PHASE0_AUTO_START: 5,
            self.PHASE1_STRUCTURE: 10,
            self.STRUCTURE_CHECK: 10,
            self.PHASE2_WRITING: 15,
            self.WRITING_PHASE: 15,
            self.PHASE3_REVISION: 12,
            self.REVISION_PHASE: 12,
            self.STAGE1_BASIC_QUALITY: 8,
            self.BASIC_QUALITY_CHECK: 8,
            self.STAGE2_CONTENT: 18,
            self.CONTENT_DETAIL_CHECK: 18,
            self.STAGE3_FINAL: 10,
            self.FINAL_POLISH: 10,
            self.QUALITY_INTEGRATION: 6,
            self.CLAUDE_ANALYSIS: 8,
        }
        return typical_counts.get(self, 10)

    @classmethod
    def from_phase_name(cls, phase_name: str) -> "QualityCheckPhase":
        """フェーズ名からインスタンス作成

        Args:
            phase_name: フェーズ名文字列

        Returns:
            A31CheckPhase: 対応するフェーズインスタンス
        """
        # 完全一致を試行
        for phase in cls:
            if phase.value == phase_name:
                return phase

        # 部分一致を試行
        phase_name_lower = phase_name.lower()
        if "phase0" in phase_name_lower or "自動執筆" in phase_name_lower:
            return cls.PHASE0_AUTO_START
        if "phase1" in phase_name_lower or "構造" in phase_name_lower:
            return cls.PHASE1_STRUCTURE
        if "phase2" in phase_name_lower or "執筆" in phase_name_lower:
            return cls.PHASE2_WRITING
        if "phase3" in phase_name_lower or "校正" in phase_name_lower or "推敲" in phase_name_lower:
            return cls.PHASE3_REVISION
        if "stage1" in phase_name_lower or "基本品質" in phase_name_lower:
            return cls.STAGE1_BASIC_QUALITY
        if "stage2" in phase_name_lower or "コンテンツ詳細" in phase_name_lower:
            return cls.STAGE2_CONTENT
        if "stage3" in phase_name_lower or "最終仕上" in phase_name_lower:
            return cls.STAGE3_FINAL

        # デフォルトは構造チェック
        return cls.STRUCTURE_CHECK

    def __str__(self) -> str:
        """文字列表現"""
        return self.get_display_name()

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return f"QualityCheckPhase.{self.name}"

# Backward compatibility alias
A31CheckPhase = QualityCheckPhase
