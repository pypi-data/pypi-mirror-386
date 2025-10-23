#!/usr/bin/env python3
"""品質評価カテゴリ バリューオブジェクト（旧称A31EvaluationCategory）

小説品質チェックで使用される評価カテゴリを定義。
詳細評価システムでの分析分類に使用される。
"""

from enum import Enum


class QualityEvaluationCategory(Enum):
    """A31評価カテゴリ列挙型

    A31チェックシステムで使用される評価カテゴリ。
    各カテゴリは特定の品質観点を表す。
    """

    # 基本品質カテゴリ
    FORMAT_CHECK = "format_check"  # フォーマット・構造チェック
    CONTENT_BALANCE = "content_balance"  # 内容バランス分析
    STYLE_CONSISTENCY = "style_consistency"  # 文体一貫性チェック
    READABILITY_CHECK = "readability_check"  # 読みやすさ評価
    CHARACTER_CONSISTENCY = "character_consistency"  # キャラクター一貫性

    # 拡張品質カテゴリ
    SENSORY_DESCRIPTION = "sensory_description"  # 五感描写チェック
    BASIC_WRITING_STYLE = "basic_writing_style"  # 基本的な文体チェック
    QUALITY_THRESHOLD = "quality_threshold"  # 品質閾値評価
    CLAUDE_CODE_EVALUATION = "claude_code_evaluation"  # Claude Code分析
    SYSTEM_FUNCTION = "system_function"  # システム機能評価

    def get_display_name(self) -> str:
        """表示用名称を取得

        Returns:
            str: 日本語表示名
        """
        display_names = {
            self.FORMAT_CHECK: "フォーマット・構造",
            self.CONTENT_BALANCE: "内容バランス",
            self.STYLE_CONSISTENCY: "文体一貫性",
            self.READABILITY_CHECK: "読みやすさ",
            self.CHARACTER_CONSISTENCY: "キャラクター一貫性",
            self.SENSORY_DESCRIPTION: "五感描写",
            self.BASIC_WRITING_STYLE: "基本文体",
            self.QUALITY_THRESHOLD: "品質閾値",
            self.CLAUDE_CODE_EVALUATION: "Claude Code評価",
            self.SYSTEM_FUNCTION: "システム機能",
        }
        return display_names.get(self, self.value)

    def get_description(self) -> str:
        """カテゴリ説明を取得

        Returns:
            str: カテゴリの詳細説明
        """
        descriptions = {
            self.FORMAT_CHECK: "段落構成、見出し、冒頭の引き込み効果等の構造面を評価",
            self.CONTENT_BALANCE: "会話と地の文のバランス、五感描写、情報密度を分析",
            self.STYLE_CONSISTENCY: "文末表現の多様性、文体統一、語句反復等をチェック",
            self.READABILITY_CHECK: "文章長バランス、漢字・ひらがな比率、認知負荷を評価",
            self.CHARACTER_CONSISTENCY: "キャラクターの話し方、行動パターンの一貫性を確認",
            self.SENSORY_DESCRIPTION: "視覚、聴覚、嗅覚、味覚、触覚の五感描写の配置と品質を評価",
            self.BASIC_WRITING_STYLE: "基本的な文体、語彙選択、文章構成の品質を評価",
            self.QUALITY_THRESHOLD: "設定された品質基準との適合性を評価",
            self.CLAUDE_CODE_EVALUATION: "Claude Code分析による総合品質評価",
            self.SYSTEM_FUNCTION: "システム機能の動作確認と品質保証",
        }
        return descriptions.get(self, "評価カテゴリの説明")

    def is_core_category(self) -> bool:
        """基本カテゴリかどうか判定

        Returns:
            bool: 基本カテゴリの場合True
        """
        core_categories = {
            self.FORMAT_CHECK,
            self.CONTENT_BALANCE,
            self.STYLE_CONSISTENCY,
            self.READABILITY_CHECK,
            self.CHARACTER_CONSISTENCY,
        }
        return self in core_categories

    def get_priority_level(self) -> int:
        """優先度レベルを取得

        Returns:
            int: 優先度（1が最高、数値が大きいほど優先度低）
        """
        priority_levels = {
            self.FORMAT_CHECK: 1,  # 構造は最優先
            self.CONTENT_BALANCE: 2,  # 内容バランスは重要
            self.STYLE_CONSISTENCY: 2,  # 文体も重要
            self.READABILITY_CHECK: 3,  # 読みやすさ
            self.CHARACTER_CONSISTENCY: 3,  # キャラクター一貫性
            self.SENSORY_DESCRIPTION: 2,  # 五感描写は重要
            self.BASIC_WRITING_STYLE: 3,  # 基本文体
            self.QUALITY_THRESHOLD: 4,  # 品質閾値
            self.CLAUDE_CODE_EVALUATION: 4,  # Claude Code評価
            self.SYSTEM_FUNCTION: 5,  # システム機能は最低優先
        }
        return priority_levels.get(self, 5)

    @classmethod
    def get_all_core_categories(cls) -> list["QualityEvaluationCategory"]:
        """全ての基本カテゴリを取得

        Returns:
            list[A31EvaluationCategory]: 基本カテゴリのリスト
        """
        return [
            cls.FORMAT_CHECK,
            cls.CONTENT_BALANCE,
            cls.STYLE_CONSISTENCY,
            cls.READABILITY_CHECK,
            cls.CHARACTER_CONSISTENCY,
        ]

    @classmethod
    def get_categories_by_priority(cls) -> list["QualityEvaluationCategory"]:
        """優先度順でカテゴリを取得

        Returns:
            list[A31EvaluationCategory]: 優先度順カテゴリリスト
        """
        all_categories = list(cls)
        return sorted(all_categories, key=lambda cat: cat.get_priority_level())

    @classmethod
    def from_checklist_item_type(cls, item_type: str) -> "QualityEvaluationCategory":
        """A31ChecklistItemのitem_typeから評価カテゴリに変換

        Args:
            item_type: ChecklistItemTypeの値

        Returns:
            A31EvaluationCategory: 対応する評価カテゴリ

        Raises:
            ValueError: マッピングが見つからない場合
        """
        # ChecklistItemType → A31EvaluationCategory のマッピング
        type_mapping = {
            "format_check": cls.FORMAT_CHECK,
            "content_balance": cls.CONTENT_BALANCE,
            "style_consistency": cls.STYLE_CONSISTENCY,
            "readability_check": cls.READABILITY_CHECK,
            "character_consistency": cls.CHARACTER_CONSISTENCY,
            "quality_threshold": cls.QUALITY_THRESHOLD,
            "claude_code_evaluation": cls.CLAUDE_CODE_EVALUATION,
            "system_function": cls.SYSTEM_FUNCTION,
            # 追加のマッピング（既存のChecklistItemTypeとの互換性）
            "content_review": cls.CONTENT_BALANCE,
            "consistency_check": cls.CHARACTER_CONSISTENCY,
            "basic_proofread": cls.READABILITY_CHECK,
            "style_variety": cls.STYLE_CONSISTENCY,
            "sensory_check": cls.SENSORY_DESCRIPTION,
            "basic_writing_style": cls.BASIC_WRITING_STYLE,
        }

        if item_type in type_mapping:
            return type_mapping[item_type]

        # デフォルトはFORMAT_CHECKにフォールバック
        return cls.FORMAT_CHECK

    def __str__(self) -> str:
        """文字列表現"""
        return self.get_display_name()

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return f"QualityEvaluationCategory.{self.name}"

# Backward compatibility alias
A31EvaluationCategory = QualityEvaluationCategory
