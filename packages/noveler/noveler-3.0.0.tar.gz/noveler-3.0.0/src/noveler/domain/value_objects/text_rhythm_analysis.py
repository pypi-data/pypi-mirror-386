"""Domain.value_objects.text_rhythm_analysis
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""文章リズム分析用値オブジェクト

文字数分析、リズムパターン検出、読みやすさ評価のための
データ構造を定義
"""


from dataclasses import dataclass
from enum import Enum
from typing import Any


class RhythmIssueType(Enum):
    """リズム問題のタイプ"""

    CONSECUTIVE_LONG = "consecutive_long"  # 連続長文
    CONSECUTIVE_SHORT = "consecutive_short"  # 連続短文
    IRREGULAR_PATTERN = "irregular_pattern"  # 不規則パターン
    MONOTONOUS_LENGTH = "monotonous_length"  # 単調な長さ


class RhythmSeverity(Enum):
    """問題の深刻度"""

    LOW = "low"  # 軽微な問題
    MEDIUM = "medium"  # 改善推奨
    HIGH = "high"  # 要修正
    CRITICAL = "critical"  # 緊急修正


@dataclass(frozen=True)
class SentenceAnalysis:
    """個別文の分析結果"""

    index: int  # 文番号（0から開始）
    content: str  # 文の内容
    character_count: int  # 文字数
    is_dialogue: bool  # 会話文かどうか
    sentence_type: str  # 文種別（平叙・疑問・感嘆・命令）
    ending_pattern: str  # 文末パターン

    def is_long_sentence(self, threshold: int = 60) -> bool:
        """長文判定"""
        return self.character_count >= threshold

    def is_short_sentence(self, threshold: int = 20) -> bool:
        """短文判定"""
        return self.character_count <= threshold

    def get_length_category(self) -> str:
        """文字数カテゴリの取得"""
        if self.character_count <= 15:
            return "very_short"
        if self.character_count <= 25:
            return "short"
        if self.character_count <= 40:
            return "medium"
        if self.character_count <= 60:
            return "long"
        return "very_long"


@dataclass(frozen=True)
class RhythmIssue:
    """リズム問題の詳細"""

    issue_type: RhythmIssueType  # 問題タイプ
    severity: RhythmSeverity  # 深刻度
    start_index: int  # 問題開始位置
    end_index: int  # 問題終了位置
    description: str  # 問題の説明
    suggestion: str  # 改善提案
    affected_sentences: list[SentenceAnalysis]  # 影響を受ける文

    @property
    def sentence_count(self) -> int:
        """影響を受ける文の数"""
        return len(self.affected_sentences)

    def get_character_range(self) -> tuple[int, int]:
        """問題箇所の文字数範囲"""
        if not self.affected_sentences:
            return 0, 0

        min_chars = min(s.character_count for s in self.affected_sentences)
        max_chars = max(s.character_count for s in self.affected_sentences)
        return min_chars, max_chars


@dataclass(frozen=True)
class RhythmStatistics:
    """文章リズムの統計情報"""

    total_sentences: int  # 総文数
    average_length: float  # 平均文字数
    median_length: float  # 中央値
    std_deviation: float  # 標準偏差
    min_length: int  # 最短文字数
    max_length: int  # 最長文字数

    # 文字数分布
    very_short_count: int  # 15文字以下
    short_count: int  # 16-25文字
    medium_count: int  # 26-40文字
    long_count: int  # 41-60文字
    very_long_count: int  # 61文字以上

    # バランス指標
    length_variance: float  # 長さのバラエティ
    rhythm_score: float  # リズムスコア（0-100）

    def get_distribution_percentages(self) -> dict[str, float]:
        """文字数分布の割合を取得"""
        if self.total_sentences == 0:
            return dict.fromkeys(["very_short", "short", "medium", "long", "very_long"], 0.0)

        return {
            "very_short": (self.very_short_count / self.total_sentences) * 100,
            "short": (self.short_count / self.total_sentences) * 100,
            "medium": (self.medium_count / self.total_sentences) * 100,
            "long": (self.long_count / self.total_sentences) * 100,
            "very_long": (self.very_long_count / self.total_sentences) * 100,
        }

    def is_balanced_distribution(self) -> bool:
        """バランスの取れた分布かどうか"""
        percentages = self.get_distribution_percentages()
        # 極端な偏りがないかチェック（70%を超える単一カテゴリがないか）
        return all(p <= 70.0 for p in percentages.values())


@dataclass(frozen=True)
class TextRhythmReport:
    """文章リズム分析の総合レポート"""

    sentences: list[SentenceAnalysis]  # 全文の分析結果
    statistics: RhythmStatistics  # 統計情報
    issues: list[RhythmIssue]  # 発見された問題
    overall_score: float  # 総合スコア（0-100）
    readability_grade: str  # 読みやすさランク

    def get_issue_summary(self) -> dict[RhythmIssueType, int]:
        """問題タイプ別の集計"""
        summary = dict.fromkeys(RhythmIssueType, 0)
        for issue in self.issues:
            summary[issue.issue_type] += 1
        return summary

    def get_severity_summary(self) -> dict[RhythmSeverity, int]:
        """深刻度別の集計"""
        summary = dict.fromkeys(RhythmSeverity, 0)
        for issue in self.issues:
            summary[issue.severity] += 1
        return summary

    def has_critical_issues(self) -> bool:
        """重大な問題があるかどうか"""
        return any(issue.severity == RhythmSeverity.CRITICAL for issue in self.issues)

    def get_improvement_priority(self) -> list[RhythmIssue]:
        """改善優先度順の問題リスト"""
        severity_order = {
            RhythmSeverity.CRITICAL: 0,
            RhythmSeverity.HIGH: 1,
            RhythmSeverity.MEDIUM: 2,
            RhythmSeverity.LOW: 3,
        }
        return sorted(self.issues, key=lambda x: (severity_order[x.severity], x.start_index))

    def to_dict(self) -> dict[str, Any]:
        """辞書形式への変換"""
        return {
            "sentence_count": len(self.sentences),
            "statistics": {
                "total_sentences": self.statistics.total_sentences,
                "average_length": self.statistics.average_length,
                "median_length": self.statistics.median_length,
                "std_deviation": self.statistics.std_deviation,
                "min_length": self.statistics.min_length,
                "max_length": self.statistics.max_length,
                "length_variance": self.statistics.length_variance,
                "rhythm_score": self.statistics.rhythm_score,
                "distribution": self.statistics.get_distribution_percentages(),
            },
            "issues": [
                {
                    "type": issue.issue_type.value,
                    "severity": issue.severity.value,
                    "start_index": issue.start_index,
                    "end_index": issue.end_index,
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                    "sentence_count": issue.sentence_count,
                }
                for issue in self.issues
            ],
            "overall_score": self.overall_score,
            "readability_grade": self.readability_grade,
            "issue_summary": {k.value: v for k, v in self.get_issue_summary().items()},
            "severity_summary": {k.value: v for k, v in self.get_severity_summary().items()},
        }
