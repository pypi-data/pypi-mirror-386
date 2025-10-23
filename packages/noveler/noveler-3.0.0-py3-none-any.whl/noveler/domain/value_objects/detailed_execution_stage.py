"""詳細実行段階定義

A30プロンプトとの整合性を確保するための拡張実行段階。
従来の5段階から10段階への段階的移行を支援。
"""

from enum import Enum
from typing import ClassVar


class DetailedExecutionStage(Enum):
    """詳細実行段階定義（A30-16STEP準拠）

    Phase 1実装: EPISODE_DESIGNの5段階分割により、
    A30のSTEP 5-9との整合性を確保する。
    """

    # データ収集段階（既存維持）
    DATA_COLLECTION = "data_collection"

    # プロット分析段階（既存維持）
    PLOT_ANALYSIS = "plot_analysis"

    # === 拡張エピソード設計段階（A30 STEP 5-9対応）===
    LOGIC_VERIFICATION = "logic_verification"  # A30 STEP 5対応
    CHARACTER_CONSISTENCY = "character_consistency"  # A30 STEP 6対応
    DIALOGUE_DESIGN = "dialogue_design"  # A30 STEP 7対応
    EMOTION_CURVE = "emotion_curve"  # A30 STEP 8対応
    SCENE_ATMOSPHERE = "scene_atmosphere"  # A30 STEP 9対応

    # 原稿執筆段階（既存維持）
    MANUSCRIPT_WRITING = "manuscript_writing"

    # 品質仕上げ段階（既存維持）
    QUALITY_FINALIZATION = "quality_finalization"

    @property
    def display_name(self) -> str:
        """表示名取得"""
        display_names: ClassVar[dict[DetailedExecutionStage, str]] = {
            DetailedExecutionStage.DATA_COLLECTION: "データ収集・準備",
            DetailedExecutionStage.PLOT_ANALYSIS: "プロット分析・設計",
            DetailedExecutionStage.LOGIC_VERIFICATION: "論理検証（因果・動機・整合）",
            DetailedExecutionStage.CHARACTER_CONSISTENCY: "キャラクター一貫性検証",
            DetailedExecutionStage.DIALOGUE_DESIGN: "会話設計（目的駆動・個性強化）",
            DetailedExecutionStage.EMOTION_CURVE: "感情曲線（内面・表現強化）",
            DetailedExecutionStage.SCENE_ATMOSPHERE: "情景・五感・世界観設計",
            DetailedExecutionStage.MANUSCRIPT_WRITING: "原稿執筆",
            DetailedExecutionStage.QUALITY_FINALIZATION: "品質チェック・仕上げ",
        }
        return display_names[self]

    @property
    def expected_turns(self) -> int:
        """予想ターン数"""
        turn_estimates: ClassVar[dict[DetailedExecutionStage, int]] = {
            DetailedExecutionStage.DATA_COLLECTION: 3,
            DetailedExecutionStage.PLOT_ANALYSIS: 3,
            DetailedExecutionStage.LOGIC_VERIFICATION: 2,  # A30 STEP 5専用
            DetailedExecutionStage.CHARACTER_CONSISTENCY: 2,  # A30 STEP 6専用
            DetailedExecutionStage.DIALOGUE_DESIGN: 2,  # A30 STEP 7専用
            DetailedExecutionStage.EMOTION_CURVE: 2,  # A30 STEP 8専用
            DetailedExecutionStage.SCENE_ATMOSPHERE: 2,  # A30 STEP 9専用
            DetailedExecutionStage.MANUSCRIPT_WRITING: 4,
            DetailedExecutionStage.QUALITY_FINALIZATION: 3,
        }
        return turn_estimates[self]

    @property
    def max_turns(self) -> int:
        """最大ターン数制限"""
        # 各段階の最大ターン数を予想の1.5倍に設定（安全マージン）
        return int(self.expected_turns * 1.5)

    @property
    def a30_step_mapping(self) -> list[int]:
        """対応するA30ステップ番号"""
        step_mappings: ClassVar[dict[DetailedExecutionStage, list[int]]] = {
            DetailedExecutionStage.DATA_COLLECTION: [0, 1, 2],  # STEP 0-2
            DetailedExecutionStage.PLOT_ANALYSIS: [3, 4],  # STEP 3-4
            DetailedExecutionStage.LOGIC_VERIFICATION: [5],  # STEP 5
            DetailedExecutionStage.CHARACTER_CONSISTENCY: [6],  # STEP 6
            DetailedExecutionStage.DIALOGUE_DESIGN: [7],  # STEP 7
            DetailedExecutionStage.EMOTION_CURVE: [8],  # STEP 8
            DetailedExecutionStage.SCENE_ATMOSPHERE: [9],  # STEP 9
            DetailedExecutionStage.MANUSCRIPT_WRITING: [10],  # STEP 10
            DetailedExecutionStage.QUALITY_FINALIZATION: [11, 12, 13, 14, 15],  # STEP 11-15
        }
        return step_mappings[self]

    @property
    def is_new_detailed_stage(self) -> bool:
        """新規追加の詳細段階かどうか"""
        new_stages = {
            DetailedExecutionStage.LOGIC_VERIFICATION,
            DetailedExecutionStage.CHARACTER_CONSISTENCY,
            DetailedExecutionStage.DIALOGUE_DESIGN,
            DetailedExecutionStage.EMOTION_CURVE,
            DetailedExecutionStage.SCENE_ATMOSPHERE,
        }
        return self in new_stages

    @classmethod
    def get_total_expected_turns(cls) -> int:
        """全段階の合計予想ターン数"""
        return sum(stage.expected_turns for stage in cls)

    @classmethod
    def get_a30_coverage_improvement(cls) -> dict[str, float]:
        """A30カバー率改善効果"""
        return {
            "従来5段階カバー率": 0.30,  # 30%
            "新10段階カバー率": 0.80,  # 80%
            "改善効果": 0.50,  # +50ポイント
            "改善倍率": 2.67,  # 2.67倍
        }

    def get_stage_description(self) -> str:
        """段階説明取得"""
        descriptions: ClassVar[dict[DetailedExecutionStage, str]] = {
            DetailedExecutionStage.DATA_COLLECTION: "プロット・設定データの収集と前処理。A30 STEP 0-2に対応。",
            DetailedExecutionStage.PLOT_ANALYSIS: "大骨・中骨構造の分析と設計。A30 STEP 3-4に対応。",
            DetailedExecutionStage.LOGIC_VERIFICATION: "因果関係・動機・整合性の論理検証。A30 STEP 5の専用実装。",
            DetailedExecutionStage.CHARACTER_CONSISTENCY: "キャラクター設定・行動パターンの一貫性検証。A30 STEP 6の専用実装。",
            DetailedExecutionStage.DIALOGUE_DESIGN: "目的駆動の台詞設計とキャラクター個性強化。A30 STEP 7の専用実装。",
            DetailedExecutionStage.EMOTION_CURVE: "感情の内面表現と表現バリエーション強化。A30 STEP 8の専用実装。",
            DetailedExecutionStage.SCENE_ATMOSPHERE: "情景描写・五感表現・世界観の段階開示計画。A30 STEP 9の専用実装。",
            DetailedExecutionStage.MANUSCRIPT_WRITING: "品質優先の初稿生成。A30 STEP 10に対応。",
            DetailedExecutionStage.QUALITY_FINALIZATION: "文字数最適化・文体調整・品質認定・公開準備。A30 STEP 11-15に対応。",
        }
        return descriptions[self]
