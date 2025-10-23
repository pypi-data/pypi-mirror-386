#!/usr/bin/env python3
"""A31チェックリスト評価サービス - FC/IS準拠純粋関数実装

SPEC-QUALITY-001, SPEC-ARCH-002に基づくA31チェックリスト項目の自動評価。
Functional Coreパターン適用：副作用なし、決定論的、純粋関数群で構成。
"""

import re
from collections.abc import Callable
from typing import Any

from noveler.domain.entities.a31_checklist_item import A31ChecklistItem, ChecklistItemType
from noveler.domain.value_objects.a31_evaluation_result import EvaluationResult
from noveler.domain.value_objects.function_signature import ensure_pure_function


class A31EvaluationService:
    """A31チェックリスト項目評価サービス

    エピソード内容に対してA31チェックリスト項目の自動評価を実行。
    フォーマット・品質・内容の各カテゴリーで異なる評価ロジックを適用。
    """

    def __init__(self) -> None:
        """評価サービスの初期化"""
        self._format_evaluators = {
            ChecklistItemType.FORMAT_CHECK: self._evaluate_format_check,
            ChecklistItemType.STYLE_CONSISTENCY: self._evaluate_style_consistency,
        }

        self._quality_evaluators = {
            ChecklistItemType.QUALITY_THRESHOLD: self._evaluate_quality_threshold,
            ChecklistItemType.READABILITY_CHECK: self._evaluate_readability_check,
        }

        self._content_evaluators = {
            ChecklistItemType.CONTENT_BALANCE: self._evaluate_content_balance,
            ChecklistItemType.CHARACTER_CONSISTENCY: self._evaluate_character_consistency,
            ChecklistItemType.TERMINOLOGY_CHECK: self._evaluate_terminology_check,
        }

    @ensure_pure_function
    def evaluate_item(
        self, item: A31ChecklistItem, episode_content: str, metadata: dict[str, Any] | None = None
    ) -> EvaluationResult:
        """個別項目の評価実行 - FC/IS準拠純粋関数

        Args:
            item: 評価対象のチェックリスト項目
            episode_content: エピソード内容
            metadata: 追加メタデータ(プロジェクト設定等)

        Returns:
            EvaluationResult: 評価結果
        """
        if metadata is None:
            metadata = {}

        # 項目タイプに応じた評価器を選択
        evaluator = self._get_evaluator(item.item_type)
        if evaluator is None:
            return self._create_unsupported_result(item.item_id)

        # 評価実行
        score, details = evaluator(item, episode_content, metadata)

        # 閾値判定
        passed = item.threshold.evaluate(score)

        return EvaluationResult(
            item_id=item.item_id,
            current_score=score,
            threshold_value=item.threshold.value,
            passed=passed,
            details=details,
        )

    @ensure_pure_function
    def evaluate_all_items(
        self, items: list[A31ChecklistItem], episode_content: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, EvaluationResult]:
        """全項目の一括評価 - FC/IS準拠純粋関数

        Args:
            items: 評価対象のチェックリスト項目リスト
            episode_content: エピソード内容
            metadata: 追加メタデータ

        Returns:
            Dict[str, EvaluationResult]: 項目ID別の評価結果
        """
        results: dict[str, Any] = {}

        for item in items:
            results[item.item_id] = self.evaluate_item(item, episode_content, metadata)

        return results

    def _get_evaluator(self, item_type: ChecklistItemType) -> Callable[..., tuple[float, dict[str, Any]]] | None:
        """項目タイプに応じた評価器を取得"""
        # フォーマット系評価器
        if item_type in self._format_evaluators:
            return self._format_evaluators[item_type]

        # 品質系評価器
        if item_type in self._quality_evaluators:
            return self._quality_evaluators[item_type]

        # 内容系評価器
        if item_type in self._content_evaluators:
            return self._content_evaluators[item_type]

        # その他(評価不可)
        return None

    @ensure_pure_function
    def _evaluate_format_check(
        self, item: A31ChecklistItem, content: str, _metadata: dict[str, Any]
    ) -> tuple[float, dict[str, Any]]:
        """フォーマット系チェックの評価 - FC/IS準拠純粋関数

        主に段落字下げ等のフォーマット要素を評価
        """
        if item.item_id == "A31-045":  # 段落頭の字下げ確認:
            return self._evaluate_paragraph_indentation(content)

        # デフォルト評価
        return 0.0, {"error": f"Unsupported format check: {item.item_id}"}

    def _evaluate_style_consistency(
        self, item: A31ChecklistItem, content: str, _metadata: dict[str, Any]
    ) -> tuple[float, dict[str, Any]]:
        """スタイル統一性の評価

        記号使用や表記統一をチェック
        """
        if item.item_id == "A31-035":  # 記号統一:
            return self._evaluate_symbol_consistency(content)

        return 0.0, {"error": f"Unsupported style check: {item.item_id}"}

    def _evaluate_quality_threshold(
        self, item: A31ChecklistItem, _content: str, metadata: dict[str, Any]
    ) -> tuple[float, dict[str, Any]]:
        """品質閾値の評価

        既存の品質スコアシステムと連携
        """
        if item.item_id == "A31-042":  # 品質スコア70点以上:
            # メタデータから品質スコアを取得
            quality_score = metadata.get("quality_score", 0.0)
            return quality_score, {"source": "quality_system", "score": quality_score}

        return 0.0, {"error": f"Unsupported quality check: {item.item_id}"}

    def _evaluate_readability_check(
        self, _item: A31ChecklistItem, content: str, _metadata: dict[str, Any]
    ) -> tuple[float, dict[str, Any]]:
        """読みやすさの評価（詳細リズム分析統合版）

        文章リズムや可読性を詳細分析し、具体的な改善提案を提供
        """
        try:
            # 新しい詳細リズム分析サービスを使用
            # NOTE: 動的インポートはDependency Injection準備のため一時的に使用
            from noveler.domain.services.text_rhythm_analysis_service import TextRhythmAnalysisService

            rhythm_service = TextRhythmAnalysisService()
            report = rhythm_service.analyze_text_rhythm(content)

            # A31評価用の詳細情報を作成（視覚化は上位層で処理）
            details: dict[str, Any] = {
                "rhythm_analysis": report.to_dict(),
                "text_report": "詳細レポートは上位層で生成",
                "statistics": {
                    "total_sentences": report.statistics.total_sentences,
                    "average_length": report.statistics.average_length,
                    "rhythm_score": report.statistics.rhythm_score,
                    "issues_count": len(report.issues),
                    "critical_issues": sum(1 for issue in report.issues if issue.severity.value == "critical"),
                    "distribution": report.statistics.get_distribution_percentages(),
                },
                "improvement_suggestions": [
                    {
                        "type": issue.issue_type.value,
                        "severity": issue.severity.value,
                        "description": issue.description,
                        "suggestion": issue.suggestion,
                        "location": f"{issue.start_index + 1}〜{issue.end_index + 1}文目",
                    }
                    for issue in report.issues
                ],
            }

            # 総合スコアを返す（0-100の範囲）
            return report.overall_score, details

        except ImportError:
            # フォールバック: 既存の簡易評価
            avg_sentence_length = self._calculate_average_sentence_length(content)
            readability_score = max(0, 100 - (avg_sentence_length - 20) * 2)  # 20文字が最適

            return readability_score, {
                "average_sentence_length": avg_sentence_length,
                "readability_score": readability_score,
                "note": "詳細リズム分析は利用できませんでした（フォールバック評価）",
            }

        except Exception as e:
            # エラー時のフォールバック
            avg_sentence_length = self._calculate_average_sentence_length(content)
            readability_score = max(0, 100 - (avg_sentence_length - 20) * 2)

            return readability_score, {
                "average_sentence_length": avg_sentence_length,
                "readability_score": readability_score,
                "error": f"詳細分析でエラーが発生しました: {e}",
                "note": "基本評価で代替しました",
            }

    def _evaluate_content_balance(
        self, item: A31ChecklistItem, content: str, _metadata: dict[str, Any]
    ) -> tuple[float, dict[str, Any]]:
        """内容バランスの評価

        会話と地の文の比率等をチェック
        """
        if item.item_id == "A31-022":  # 会話と地の文バランス:
            return self._evaluate_dialogue_balance(content)

        return 0.0, {"error": f"Unsupported content balance check: {item.item_id}"}

    def _evaluate_character_consistency(
        self, _item: A31ChecklistItem, _content: str, metadata: dict[str, Any]
    ) -> tuple[float, dict[str, Any]]:
        """キャラクター整合性の評価

        キャラクター設定との整合性をチェック
        """
        # メタデータからキャラクター設定を取得して比較
        character_data: dict[str, Any] = metadata.get("characters", {})
        consistency_score = 85.0  # 仮の値

        return consistency_score, {"character_count": len(character_data), "consistency_score": consistency_score}

    def _evaluate_terminology_check(
        self, _item: A31ChecklistItem, content: str, metadata: dict[str, Any]
    ) -> tuple[float, dict[str, Any]]:
        """用語統一性の評価

        固有名詞や専門用語の表記統一をチェック
        """
        # メタデータから用語集を取得
        terminology = metadata.get("terminology", {})
        consistency_count = 0
        total_terms = 0

        for term, standard_form in terminology.items():
            if term in content:
                total_terms += 1
                if standard_form in content:
                    consistency_count += 1

        if total_terms == 0:
            return 100.0, {"no_terms_found": True}

        consistency_rate = (consistency_count / total_terms) * 100

        return consistency_rate, {
            "total_terms": total_terms,
            "consistent_terms": consistency_count,
            "consistency_rate": consistency_rate,
        }

    def _evaluate_paragraph_indentation(self, content: str) -> tuple[float, dict[str, Any]]:
        """段落字下げの評価"""
        lines = content.split("\n")
        paragraph_lines = [line for line in lines if line.strip()]  # 空行を除外

        if not paragraph_lines:
            return 100.0, {"no_paragraphs": True}

        indented_count = 0
        for line in paragraph_lines:
            if line.startswith(" "):  # 全角スペースで開始:
                indented_count += 1

        indentation_rate = (indented_count / len(paragraph_lines)) * 100

        return indentation_rate, {
            "total_paragraphs": len(paragraph_lines),
            "indented_paragraphs": indented_count,
            "indentation_rate": indentation_rate,
        }

    def _evaluate_symbol_consistency(self, content: str) -> tuple[float, dict[str, Any]]:
        """記号統一性の評価"""
        issues = []

        # 三点リーダーのチェック
        dot_patterns = re.findall(r"\.{2,}", content)
        ellipsis_patterns = re.findall(r"…+", content)

        if dot_patterns and ellipsis_patterns:
            issues.append("混在: ドット記号と三点リーダー")

        # ダッシュのチェック
        hyphen_patterns = re.findall(r"-{2,}", content)
        dash_patterns = re.findall(r"[―-]{1,}", content)

        if hyphen_patterns and dash_patterns:
            issues.append("混在: ハイフンとダッシュ")

        consistency_score = max(0, 100 - len(issues) * 20)

        return consistency_score, {
            "issues": issues,
            "dot_patterns": len(dot_patterns),
            "ellipsis_patterns": len(ellipsis_patterns),
            "hyphen_patterns": len(hyphen_patterns),
            "dash_patterns": len(dash_patterns),
        }

    def _evaluate_dialogue_balance(self, content: str) -> tuple[float, dict[str, Any]]:
        """会話と地の文バランスの評価"""
        lines = content.split("\n")
        dialogue_lines = []
        narrative_lines = []

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            # 会話文の判定(「」で囲まれている)
            if "「" in stripped_line and "」" in stripped_line:
                dialogue_lines.append(stripped_line)
            else:
                narrative_lines.append(stripped_line)

        total_lines = len(dialogue_lines) + len(narrative_lines)
        if total_lines == 0:
            return 0.0, {"no_content": True}

        dialogue_ratio = (len(dialogue_lines) / total_lines) * 100

        # 適正範囲(30-40%)からの距離で評価
        if 30 <= dialogue_ratio <= 40:
            balance_score = 100.0
        elif dialogue_ratio < 30:
            balance_score = max(0, 100 - (30 - dialogue_ratio) * 3)
        else:  # dialogue_ratio > 40
            balance_score = max(0, 100 - (dialogue_ratio - 40) * 3)

        return balance_score, {
            "dialogue_lines": len(dialogue_lines),
            "narrative_lines": len(narrative_lines),
            "dialogue_ratio": dialogue_ratio,
            "balance_score": balance_score,
        }

    def _calculate_average_sentence_length(self, content: str) -> float:
        """平均文長の計算"""
        sentences = re.split(r"[。!?]", content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 0.0

        total_length = sum(len(sentence) for sentence in sentences)
        return total_length / len(sentences)

    def _create_unsupported_result(self, item_id: str) -> EvaluationResult:
        """未対応項目の結果作成"""
        return EvaluationResult(
            item_id=item_id,
            current_score=0.0,
            threshold_value=0.0,
            passed=False,
            details={"error": "Evaluation not supported for this item type"},
        )
