"""Domain.quality.services
Where: Domain services implementing quality evaluation logic.
What: Check manuscripts, aggregate violations, and compute scores.
Why: Centralise quality-check behaviour for reuse by application layers.
"""

from __future__ import annotations

from typing import Any

"""品質管理ドメインのドメインサービス"""


import re

from noveler.domain.quality.entities import QualityAdaptationPolicy, QualityReport, QualityViolation
from noveler.domain.quality.value_objects import (
    AdaptationStrength,
    ErrorContext,
    ErrorSeverity,
    LineNumber,
    QualityScore,
    RuleCategory,
)


class TextQualityChecker:
    """テキスト品質チェッカー(ドメインサービス)"""

    def __init__(self, proper_noun_repository: object) -> None:
        self.proper_noun_repository = proper_noun_repository

    def check_basic_style(self, text: str, project_id: str) -> list[QualityViolation]:
        """基本文体をチェック"""
        violations: list[Any] = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines, 1):
            # 連続句読点チェック
            for match in re.finditer(r"[。、]{2,}", line):
                violations.append(
                    QualityViolation(
                        rule_name="consecutive_punctuation",
                        category=RuleCategory.BASIC_STYLE,
                        severity=ErrorSeverity.WARNING,
                        line_number=LineNumber(line_num),
                        message="連続した句読点があります",
                        context=ErrorContext(
                            text=line,
                            start_pos=match.start(),
                            end_pos=match.end(),
                        ),
                        suggestion="句読点を1つにしてください",
                    ),
                )

            # 感嘆符・疑問符後のスペースチェック
            for match in re.finditer(r"[!?](?![\s　\n」』)])", line):
                violations.append(
                    QualityViolation(
                        rule_name="missing_space_after_exclamation",
                        category=RuleCategory.BASIC_STYLE,
                        severity=ErrorSeverity.WARNING,
                        line_number=LineNumber(line_num),
                        message="感嘆符・疑問符の後に全角スペースが必要です",
                        context=ErrorContext(
                            text=line,
                            start_pos=match.start(),
                            end_pos=match.end(),
                        ),
                        suggestion="感嘆符・疑問符の後に全角スペースを追加",
                    ),
                )

            # 三点リーダーチェック
            if "..." in line or "…" in line:
                # 固有名詞チェック
                proper_nouns = self.proper_noun_repository.get_all_by_project(project_id)
                if not any(noun in line for noun in proper_nouns if "..." in noun or "…" in noun):
                    violations.append(
                        QualityViolation(
                            rule_name="invalid_ellipsis",
                            category=RuleCategory.BASIC_STYLE,
                            severity=ErrorSeverity.WARNING,
                            line_number=LineNumber(line_num),
                            message="三点リーダーは「……」を使用してください",
                            context=ErrorContext(text=line),
                            suggestion=line.replace("...", "……").replace("…", "……"),
                        ),
                    )

        return violations

    def check_composition(self, text: str) -> list[QualityViolation]:
        """構成をチェック"""
        violations: list[Any] = []
        lines = text.split("\n")

        # 段落頭の字下げチェック
        for line_num, line in enumerate(lines, 1):
            if line and not line.startswith(" ") and not line.startswith("「") and not line.startswith("#"):
                violations.append(
                    QualityViolation(
                        rule_name="missing_indentation",
                        category=RuleCategory.COMPOSITION,
                        severity=ErrorSeverity.INFO,
                        line_number=LineNumber(line_num),
                        message="段落頭に全角スペースがありません",
                        context=ErrorContext(text=line),
                        suggestion=" " + line,
                    ),
                )

        return violations

    def calculate_readability_score(self, text: str) -> QualityScore:
        """読みやすさスコアを計算"""
        sentences = [s for s in re.split(r"[。！？!?]", text) if s.strip()]
        sentence_count = max(1, len(sentences))
        avg_sentence_length = len(text) / sentence_count

        if avg_sentence_length <= 12:
            score = 90.0
        elif avg_sentence_length <= 35:
            score = 80.0
        elif avg_sentence_length <= 60:
            score = 70.0
        else:
            score = 60.0

        return QualityScore(score)


class QualityReportGenerator:
    """品質レポート生成サービス"""

    def generate_report(self, episode_id: str, violations: list[QualityViolation]) -> QualityReport:
        """品質レポートを生成"""
        report = QualityReport(episode_id=episode_id)

        for violation in violations:
            report.add_violation(violation)

        return report

    def merge_reports(self, reports: list[QualityReport]) -> QualityReport:
        """複数のレポートをマージ"""
        if not reports:
            msg = "マージするレポートがありません"
            raise ValueError(msg)

        merged = QualityReport(episode_id=reports[0].episode_id)

        for report in reports:
            for violation in report.violations:
                merged.add_violation(violation)

        return merged


class QualityAdaptationService:
    """品質適応ドメインサービス"""

    def generate_project_adaptation(
        self, learned_evaluator: object, episode_count: int, genre: str
    ) -> QualityAdaptationPolicy:
        """プロジェクト固有の適応ポリシーを生成"""

        policy = QualityAdaptationPolicy(
            policy_id=f"{learned_evaluator.project_id}_adaptation_{episode_count}",
        )

        # エピソード数に基づく信頼度設定
        if episode_count >= 30:
            policy.confidence_threshold = 0.8
        elif episode_count >= 15:
            policy.confidence_threshold = 0.7
        else:
            policy.confidence_threshold = 0.6

        # ジャンル特化適応
        if genre == "body_swap_fantasy":
            policy.add_adaptation("character_consistency", AdaptationStrength.STRONG)
            policy.add_adaptation("viewpoint_clarity", AdaptationStrength.STRONG)
            policy.add_adaptation("dialogue_ratio", AdaptationStrength.MODERATE)
        elif genre == "sf_romance":
            policy.add_adaptation("technical_accuracy", AdaptationStrength.STRONG)
            policy.add_adaptation("emotional_depth", AdaptationStrength.MODERATE)
        else:
            # 汎用適応
            policy.add_adaptation("readability", AdaptationStrength.MODERATE)
            policy.add_adaptation("dialogue_ratio", AdaptationStrength.WEAK)

        return policy

    def calculate_adaptation_strength(self, metric: str, learning_data: dict) -> AdaptationStrength:
        """学習データから適応強度を計算"""

        # 分散の取得
        variance = learning_data.get(f"{metric}_variance", 0.0)

        # 相関の取得
        correlation = learning_data.get("reader_satisfaction_correlation", 0.0)

        # エピソード数
        episode_count = learning_data.get("episode_count", 0)

        # 強度判定ロジック
        if variance >= 0.2 and correlation >= 0.7 and episode_count >= 20:
            return AdaptationStrength.STRONG
        if variance >= 0.1 and correlation >= 0.5 and episode_count >= 10:
            return AdaptationStrength.MODERATE
        return AdaptationStrength.WEAK
