#!/usr/bin/env python3
"""行特定フィードバック バリューオブジェクト

エピソードの特定行に対する詳細なフィードバック情報を表現する。
手動Claude Code分析の行番号付きフィードバックと同等の詳細度を提供。
"""

from enum import Enum
from typing import Any

from noveler.domain.value_objects.improvement_suggestion import ImprovementSuggestion


class IssueSeverity(Enum):
    """問題重要度"""

    CRITICAL = "critical"  # 致命的問題
    MAJOR = "major"  # 重要問題
    MINOR = "minor"  # 軽微問題
    INFO = "info"  # 情報提供


class IssueType(Enum):
    """問題種別"""

    FORMAT_STRUCTURE = "format_structure"  # 構造・形式問題
    CONTENT_BALANCE = "content_balance"  # 内容バランス問題
    STYLE_MONOTONY = "style_monotony"  # 文体単調問題
    CHARACTER_CONSISTENCY = "character_consistency"  # キャラクター一貫性問題
    READABILITY = "readability"  # 読みやすさ問題
    SENSORY_DESCRIPTION = "sensory_description"  # 五感描写問題

    # 高度分析用新規問題タイプ
    STRUCTURE_COMPLEXITY = "structure_complexity"  # 構造複雑性問題
    PUNCTUATION_OVERUSE = "punctuation_overuse"  # 読点過多問題
    SENSORY_LACK = "sensory_lack"  # 五感描写不足問題
    RHYTHM_VARIATION = "rhythm_variation"  # リズム変化不足問題
    BREATHING_POINTS = "breathing_points"  # 呼吸点不足問題  # 五感描写問題


class LineSpecificFeedback:
    """行特定フィードバック バリューオブジェクト

    エピソードの特定行に対する詳細な分析結果と改善提案。
    不変オブジェクトとして実装。
    """

    def __init__(
        self,
        line_number: int,
        original_text: str,
        issue_type: IssueType,
        severity: IssueSeverity,
        suggestion: ImprovementSuggestion,
        confidence: float = 1.0,
        auto_fixable: bool = False,
        context_lines: list[str] | None = None,
    ) -> None:
        """行特定フィードバック初期化

        Args:
            line_number: 行番号（1から開始）
            original_text: 元のテキスト
            issue_type: 問題種別
            severity: 重要度
            suggestion: 改善提案
            confidence: 判定信頼度（0.0-1.0）
            auto_fixable: 自動修正可能フラグ
            context_lines: 前後の文脈行

        Raises:
            ValueError: 無効なパラメータの場合
        """
        if line_number < 1:
            msg = "行番号は1以上である必要があります"
            raise ValueError(msg)

        if not original_text:
            msg = "元のテキストは空にできません"
            raise ValueError(msg)

        if not 0.0 <= confidence <= 1.0:
            msg = "信頼度は0.0から1.0の範囲である必要があります"
            raise ValueError(msg)

        self._line_number = line_number
        self._original_text = original_text
        self._issue_type = issue_type
        self._severity = severity
        self._suggestion = suggestion
        self._confidence = confidence
        self._auto_fixable = auto_fixable
        self._context_lines = context_lines or []

    @classmethod
    def create(
        cls,
        line_number: int,
        original_text: str,
        issue_type: str,
        severity: str,
        suggestion: str,
        confidence: float = 1.0,
        auto_fixable: bool = False,
        context_lines: list[str] | None = None,
    ) -> "LineSpecificFeedback":
        """ファクトリーメソッド（文字列パラメータ版）

        Args:
            line_number: 行番号
            original_text: 元のテキスト
            issue_type: 問題種別文字列
            severity: 重要度文字列
            suggestion: 改善提案文字列
            confidence: 判定信頼度
            auto_fixable: 自動修正可能フラグ
            context_lines: 前後の文脈行

        Returns:
            LineSpecificFeedback: 行特定フィードバック
        """
        # 文字列から列挙型に変換
        issue_type_enum = IssueType(issue_type)
        severity_enum = IssueSeverity(severity)

        # 改善提案オブジェクト作成
        suggestion_obj = ImprovementSuggestion.create(
            content=suggestion, suggestion_type="enhancement", confidence=confidence
        )

        return cls(
            line_number=line_number,
            original_text=original_text,
            issue_type=issue_type_enum,
            severity=severity_enum,
            suggestion=suggestion_obj,
            confidence=confidence,
            auto_fixable=auto_fixable,
            context_lines=context_lines,
        )

    def has_issues(self) -> bool:
        """問題が存在するかチェック

        Returns:
            bool: 問題が存在する場合True
        """
        return self._severity != IssueSeverity.INFO

    def is_critical(self) -> bool:
        """致命的問題かチェック

        Returns:
            bool: 致命的問題の場合True
        """
        return self._severity == IssueSeverity.CRITICAL

    def is_high_confidence(self) -> bool:
        """高信頼度判定かチェック

        Returns:
            bool: 信頼度が0.8以上の場合True
        """
        return self._confidence >= 0.8

    def get_display_text(self) -> str:
        """表示用テキストを生成

        Returns:
            str: 表示用のフォーマット済みテキスト
        """
        severity_markers = {
            IssueSeverity.CRITICAL: "🔴",
            IssueSeverity.MAJOR: "🟡",
            IssueSeverity.MINOR: "🟢",
            IssueSeverity.INFO: "ℹ️",
        }

        marker = severity_markers.get(self._severity, "")

        return f"{marker} 行{self._line_number}: {self._issue_type.value} - {self._suggestion.content}"

    def to_dict(self) -> dict[str, Any]:
        """辞書形式で出力

        Returns:
            dict[str, Any]: フィードバック情報辞書
        """
        return {
            "line_number": self._line_number,
            "original_text": self._original_text,
            "issue_type": self._issue_type.value,
            "severity": self._severity.value,
            "suggestion": self._suggestion.to_dict(),
            "confidence": self._confidence,
            "auto_fixable": self._auto_fixable,
            "context_lines": self._context_lines,
        }

    # プロパティ
    @property
    def line_number(self) -> int:
        """行番号"""
        return self._line_number

    @property
    def original_text(self) -> str:
        """元のテキスト"""
        return self._original_text

    @property
    def issue_type(self) -> IssueType:
        """問題種別"""
        return self._issue_type

    @property
    def severity(self) -> IssueSeverity:
        """重要度"""
        return self._severity

    @property
    def suggestion(self) -> ImprovementSuggestion:
        """改善提案"""
        return self._suggestion

    @property
    def confidence(self) -> float:
        """判定信頼度"""
        return self._confidence

    @property
    def auto_fixable(self) -> bool:
        """自動修正可能フラグ"""
        return self._auto_fixable

    @property
    def context_lines(self) -> list[str]:
        """前後の文脈行"""
        return self._context_lines.copy()

    def __eq__(self, other: Any) -> bool:
        """等価性比較"""
        if not isinstance(other, LineSpecificFeedback):
            return False

        return (
            self._line_number == other._line_number
            and self._original_text == other._original_text
            and self._issue_type == other._issue_type
            and self._severity == other._severity
            and self._suggestion == other._suggestion
        )

    def __hash__(self) -> int:
        """ハッシュ値計算"""
        return hash((self._line_number, self._original_text, self._issue_type, self._severity, self._suggestion))

    def __str__(self) -> str:
        """文字列表現"""
        return self.get_display_text()

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return (
            f"LineSpecificFeedback("
            f"line={self._line_number}, "
            f"type={self._issue_type.value}, "
            f"severity={self._severity.value})"
        )
