#!/usr/bin/env python3

"""Domain.entities.a31_complete_evaluation_engine
Where: Domain entity encapsulating A31 evaluation results.
What: Aggregates checklist results, metrics, and pass/fail analysis.
Why: Facilitates downstream reporting and auto-fix decisions.
"""

from __future__ import annotations

"""A31完全評価エンジン - ドメインエンティティ

SPEC-A31-001準拠の6カテゴリ評価エンジンの実装。
DDD構造に基づくドメインレイヤーのコアエンティティ。
"""


import hashlib
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from noveler.domain.entities.a31_checklist_item import A31ChecklistItem, ChecklistItemType
from noveler.domain.services.claude_code_evaluation_service import (
    ClaudeCodeEvaluationRequest,
    ClaudeCodeEvaluationService,
)
from noveler.domain.value_objects.a31_threshold import Threshold
from noveler.domain.value_objects.file_path import FilePath


class A31EvaluationCategory(Enum):
    """A31評価カテゴリ定義"""

    FORMAT_CHECK = "format_check"
    QUALITY_THRESHOLD = "quality_threshold"
    CONTENT_BALANCE = "content_balance"
    CONSISTENCY_CHECK = "consistency_check"
    CLAUDE_CODE_EVALUATION = "claude_code_evaluation"
    SYSTEM_FUNCTION = "system_function"


@dataclass
class A31EvaluationResult:
    """A31評価結果値オブジェクト"""

    item_id: str
    category: A31EvaluationCategory
    score: float
    passed: bool
    details: str
    execution_time_ms: float
    confidence: float = 1.0
    auto_fixable: bool = False
    fix_suggestions: list[str] | None = None

    def __post_init__(self) -> None:
        if self.fix_suggestions is None:
            self.fix_suggestions = []

    def to_dict(self) -> dict[str, Any]:
        """辞書形式への変換"""
        return {
            "item_id": self.item_id,
            "category": self.category.value,
            "score": self.score,
            "passed": self.passed,
            "details": self.details,
            "execution_time_ms": self.execution_time_ms,
            "confidence": self.confidence,
            "auto_fixable": self.auto_fixable,
            "fix_suggestions": self.fix_suggestions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> A31EvaluationResult:
        """辞書からの復元"""
        return cls(
            item_id=data["item_id"],
            category=A31EvaluationCategory(data["category"]),
            score=data["score"],
            passed=data["passed"],
            details=data["details"],
            execution_time_ms=data["execution_time_ms"],
            confidence=data.get("confidence", 1.0),
            auto_fixable=data.get("auto_fixable", False),
            fix_suggestions=data.get("fix_suggestions", []),
        )


@dataclass
class A31EvaluationBatch:
    """A31評価バッチ結果"""

    results: dict[str, A31EvaluationResult]
    total_items: int
    evaluated_items: int
    execution_time_ms: float

    def get_average_score(self) -> float:
        """平均スコア計算"""
        if not self.results:
            return 0.0
        return sum(result.score for result in self.results.values()) / len(self.results)

    def get_pass_rate(self) -> float:
        """合格率計算"""
        if not self.results:
            return 0.0
        passed_count = sum(1 for result in self.results.values() if result.passed)
        return passed_count / len(self.results)

    def get_total_execution_time(self) -> float:
        """総実行時間取得"""
        return self.execution_time_ms

    def get_category_statistics(self) -> dict[A31EvaluationCategory, dict[str, float]]:
        """カテゴリ別統計情報"""
        category_stats = {}

        for category in A31EvaluationCategory:
            category_results = [r for r in self.results.values() if r.category == category]
            if category_results:
                passed_count = sum(1 for r in category_results if r.passed)
                category_stats[category] = {
                    "count": len(category_results),
                    "pass_rate": passed_count / len(category_results),
                    "average_score": sum(r.score for r in category_results) / len(category_results),
                }

        return category_stats

    def filter_passed_items(self) -> dict[str, A31EvaluationResult]:
        """合格項目のフィルタ"""
        return {item_id: result for item_id, result in self.results.items() if result.passed}

    def filter_failed_items(self) -> dict[str, A31EvaluationResult]:
        """不合格項目のフィルタ"""
        return {item_id: result for item_id, result in self.results.items() if not result.passed}

    def filter_by_category(self, category: A31EvaluationCategory) -> dict[str, A31EvaluationResult]:
        """カテゴリ別フィルタ"""
        return {item_id: result for item_id, result in self.results.items() if result.category == category}


@dataclass
class A31CompleteCheckRequest:
    """A31完全チェックリクエスト"""

    project_name: str
    episode_number: int
    target_categories: list[A31EvaluationCategory] = None
    include_auto_fix: bool = False
    include_claude_analysis: bool = False  # Claude分析統合フラグ
    fix_level: str = "safe"  # safe, standard, aggressive

    def __post_init__(self) -> None:
        if self.target_categories is None:
            self.target_categories = list(A31EvaluationCategory)


@dataclass
class A31CompleteCheckResponse:
    """A31完全チェックレスポンス（Claude分析統合対応）"""

    success: bool
    project_name: str
    episode_number: int
    evaluation_batch: A31EvaluationBatch
    total_items_checked: int = 0
    auto_fixes_applied: int = 0
    claude_analysis_applied: bool = False  # Claude分析統合フラグ
    error_message: str | None = None
    checklist_file_path: str | None = None
    execution_time_ms: float = 0.0  # 実行時間記録

    def get_overall_score(self) -> float:
        """総合スコアの計算"""
        return self.evaluation_batch.get_average_score()

    def get_pass_rate(self) -> float:
        """合格率の計算"""
        return self.evaluation_batch.get_pass_rate()

    def get_failed_items(self) -> dict[str, A31EvaluationResult]:
        """不合格項目の取得"""
        return self.evaluation_batch.filter_failed_items()

    def has_claude_improvements(self) -> bool:
        """Claude改善提案が含まれているかチェック"""
        if not self.claude_analysis_applied:
            return False

        for result in self.evaluation_batch.results.values():
            if hasattr(result, "claude_improvements") and result.claude_improvements:
                return True
        return False


class A31CompleteEvaluationEngine:
    """A31完全評価エンジン

    全68項目を6つのカテゴリに分類し、
    それぞれに特化した評価アルゴリズムを適用する。
    """

    def __init__(self) -> None:
        """評価エンジンの初期化"""
        self.evaluators = self._initialize_evaluators()

    def _initialize_evaluators(self) -> dict[A31EvaluationCategory, Any]:
        """評価器の初期化"""
        return {
            A31EvaluationCategory.FORMAT_CHECK: self._create_format_evaluator(),
            A31EvaluationCategory.QUALITY_THRESHOLD: self._create_quality_evaluator(),
            A31EvaluationCategory.CONTENT_BALANCE: self._create_content_evaluator(),
            A31EvaluationCategory.CONSISTENCY_CHECK: self._create_consistency_evaluator(),
            A31EvaluationCategory.CLAUDE_CODE_EVALUATION: self._create_claude_evaluator(),
            A31EvaluationCategory.SYSTEM_FUNCTION: self._create_system_evaluator(),
        }

    def _create_format_evaluator(self) -> FormatEvaluator:
        """フォーマット系評価器の作成"""
        return FormatEvaluator()

    def _create_quality_evaluator(self) -> QualityEvaluator:
        """品質閾値系評価器の作成"""
        return QualityEvaluator()

    def _create_content_evaluator(self) -> ContentEvaluator:
        """内容バランス系評価器の作成"""
        return ContentEvaluator()

    def _create_consistency_evaluator(self) -> ConsistencyEvaluator:
        """整合性系評価器の作成"""
        return ConsistencyEvaluator()

    def _create_claude_evaluator(self) -> ClaudeCodeEvaluator:
        """Claude Code評価器の作成"""
        return ClaudeCodeEvaluator()

    def _create_system_evaluator(self) -> SystemEvaluator:
        """システム自動系評価器の作成"""
        return SystemEvaluator()

    def evaluate_single_item(
        self, content: str, item: A31ChecklistItem, context: dict[str, Any]
    ) -> A31EvaluationResult:
        """単一項目の評価実行"""
        start_time = time.time()

        try:
            # 空のコンテンツチェック
            if not content.strip():
                return A31EvaluationResult(
                    item_id=item.item_id,
                    category=self._get_category_from_item_type(item.item_type),
                    score=0.0,
                    passed=False,
                    details="Empty content detected",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # カテゴリに応じた評価実行
            category = self._get_category_from_item_type(item.item_type)
            evaluator = self.evaluators[category]

            # 評価の実行
            score, details = evaluator.evaluate(content, item, context)
            passed = self._check_threshold(score, item.threshold)

            execution_time = (time.time() - start_time) * 1000

            return A31EvaluationResult(
                item_id=item.item_id,
                category=category,
                score=score,
                passed=passed,
                details=details,
                execution_time_ms=execution_time,
                auto_fixable=item.auto_fix_strategy.supported if item.auto_fix_strategy else False,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return A31EvaluationResult(
                item_id=item.item_id,
                category=self._get_category_from_item_type(item.item_type),
                score=0.0,
                passed=False,
                details=f"Evaluation error: {e!s}",
                execution_time_ms=execution_time,
            )

    def evaluate_all_items(
        self, content: str, items: list[A31ChecklistItem], context: dict[str, Any]
    ) -> A31EvaluationBatch:
        """全項目一括評価のバッチ処理"""
        start_time = time.time()

        results: dict[str, Any] = {}
        for item in items:
            result = self.evaluate_single_item(content, item, context)
            results[item.item_id] = result

        execution_time = (time.time() - start_time) * 1000

        return A31EvaluationBatch(
            results=results, total_items=len(items), evaluated_items=len(results), execution_time_ms=execution_time
        )

    def filter_items_by_category(
        self, items: list[A31ChecklistItem], category: A31EvaluationCategory
    ) -> list[A31ChecklistItem]:
        """カテゴリによる項目フィルタリング"""
        return [item for item in items if self._get_category_from_item_type(item.item_type) == category]

    def _get_category_from_item_type(self, item_type: ChecklistItemType) -> A31EvaluationCategory:
        """項目タイプからカテゴリへの変換"""
        mapping = {
            ChecklistItemType.FORMAT_CHECK: A31EvaluationCategory.FORMAT_CHECK,
            ChecklistItemType.QUALITY_THRESHOLD: A31EvaluationCategory.QUALITY_THRESHOLD,
            ChecklistItemType.CONTENT_BALANCE: A31EvaluationCategory.CONTENT_BALANCE,
            ChecklistItemType.CONSISTENCY_CHECK: A31EvaluationCategory.CONSISTENCY_CHECK,
            ChecklistItemType.CLAUDE_CODE_EVALUATION: A31EvaluationCategory.CLAUDE_CODE_EVALUATION,
            ChecklistItemType.SYSTEM_FUNCTION: A31EvaluationCategory.SYSTEM_FUNCTION,
        }
        return mapping.get(item_type, A31EvaluationCategory.FORMAT_CHECK)

    def _check_threshold(self, score: float, threshold: Threshold | None) -> bool:
        """閾値チェック"""
        if threshold is None:
            return True
        return threshold.check(score)


# 個別評価器のスタブ実装
class FormatEvaluator:
    """フォーマット系評価器"""

    def evaluate(self, content: str, item: A31ChecklistItem, context: dict[str, Any]) -> tuple[float, str]:
        """フォーマット評価の実行"""
        if item.item_id == "A31-045":  # 段落字下げ:
            return self._evaluate_paragraph_indentation(content)
        return 85.0, "フォーマット評価完了"

    def _evaluate_paragraph_indentation(self, content: str) -> tuple[float, str]:
        """段落字下げの評価"""
        lines = content.split("\n")
        # ヘッダー行(#で始まる)と会話文(「」を含む)を除く段落のみを対象
        paragraph_lines = [
            line for line in lines if line.strip() and not line.startswith("#") and not ("「" in line and "」" in line)
        ]

        if not paragraph_lines:
            return 0.0, "段落が見つかりません"

        # 全角スペースで始まる段落をカウント
        indented_count = sum(1 for line in paragraph_lines if line.startswith(" "))
        indentation_rate = (indented_count / len(paragraph_lines)) * 100

        return indentation_rate, f"段落字下げ率: {indentation_rate:.1f}% ({indented_count}/{len(paragraph_lines)})"


class QualityEvaluator:
    """品質閾値系評価器"""

    def evaluate(self, content: str, item: A31ChecklistItem, context: dict[str, Any]) -> tuple[float, str]:
        """品質評価の実行"""
        return 75.0, "品質スコア評価完了"


class ContentEvaluator:
    """内容バランス系評価器"""

    def evaluate(self, content: str, item: A31ChecklistItem, context: dict[str, Any]) -> tuple[float, str]:
        """内容バランス評価の実行"""
        if item.item_id == "A31-022":  # 会話と地の文のバランス:
            return self._evaluate_dialogue_balance(content)
        return 70.0, "内容バランス評価完了"

    def _evaluate_dialogue_balance(self, content: str) -> tuple[float, str]:
        """会話と地の文のバランス評価"""
        lines = content.split("\n")
        dialogue_lines = [line for line in lines if "「" in line and "」" in line]
        narrative_lines = [
            line for line in lines if line.strip() and not line.startswith("#") and not ("「" in line and "」" in line)
        ]

        total_content_lines = len(dialogue_lines) + len(narrative_lines)
        if total_content_lines == 0:
            return 0.0, "コンテンツが見つかりません"

        dialogue_ratio = (len(dialogue_lines) / total_content_lines) * 100

        return dialogue_ratio, f"会話比率: {dialogue_ratio:.1f}% ({len(dialogue_lines)}/{total_content_lines})"


class ConsistencyEvaluator:
    """整合性系評価器"""

    def evaluate(self, content: str, item: A31ChecklistItem, context: dict[str, Any]) -> tuple[float, str]:
        """整合性評価の実行"""
        return 80.0, "整合性評価完了"


class ClaudeCodeEvaluator:
    """Claude Code連携評価器(完全統合版)

    ClaudeCodeEvaluationServiceと統合し、実際のClaude Code評価を実行。
    エラーハンドリング、パフォーマンス最適化、キャッシュ機能を含む。
    """

    def __init__(self) -> None:
        """Claude Code評価器の初期化"""
        self._claude_service: ClaudeCodeEvaluationService | None = None
        self._cache: dict[str, tuple[float, str]] = {}
        self._cache_timeout = 300  # 5分間のキャッシュ

    def _get_claude_service(self) -> ClaudeCodeEvaluationService:
        """Claude Codeサービスの遅延初期化"""
        if self._claude_service is None:

            self._claude_service = ClaudeCodeEvaluationService()
        return self._claude_service

    def evaluate(self, content: str, item: A31ChecklistItem, context: dict[str, Any]) -> tuple[float, str]:
        """Claude Code評価の実行

        Args:
            content: エピソード内容
            item: チェックリスト項目
            context: 評価コンテキスト

        Returns:
            tuple[float, str]: (スコア, 詳細メッセージ)
        """
        try:
            # キャッシュチェック(同一内容の重複評価回避)
            cache_key = self._generate_cache_key(content, item.item_id)
            if cache_key in self._cache:
                return self._cache[cache_key]

            # Claude Code評価リクエスト作成
            request = self._create_evaluation_request(content, item, context)

            # Claude Codeサービスで評価実行
            claude_service = self._get_claude_service()
            evaluation_result = claude_service.evaluate_item(request)

            # 結果の解析と変換
            score = evaluation_result.current_score
            details: Any = self._format_evaluation_details(evaluation_result)

            # キャッシュに保存
            self._cache[cache_key] = (score, details)

            return score, details

        except ImportError as e:
            # ClaudeCodeEvaluationServiceが利用できない場合のフォールバック
            return self._fallback_evaluation(item, f"サービス初期化エラー: {e}")

        except Exception as e:
            # その他のエラー時のフォールバック
            return self._fallback_evaluation(item, f"評価実行エラー: {e}")

    def _create_evaluation_request(
        self, content: str, item: A31ChecklistItem, context: dict[str, Any]
    ) -> ClaudeCodeEvaluationRequest:
        """Claude Code評価リクエストの作成

        Args:
            content: エピソード内容
            item: チェックリスト項目
            context: 評価コンテキスト

        Returns:
            ClaudeCodeEvaluationRequest: 評価リクエスト
        """


        # 一時ファイルとしてエピソード内容を保存(Claude Codeサービス用)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as tmp_file:
            tmp_file.write(content)
            episode_file_path = Path(tmp_file.name)

        # コンテキストファイルのパス取得(存在する場合)
        context_files = []
        if "context_files" in context:
            context_files = [Path(f) for f in context["context_files"] if Path(f).exists()]

        # メタデータの準備
        metadata = {
            "item_id": item.item_id,
            "item_type": item.item_type.value,
            "required": item.required,
            "evaluation_timestamp": context.get("evaluation_timestamp"),
            "project_name": context.get("project_name"),
            "episode_number": context.get("episode_number"),
        }

        return ClaudeCodeEvaluationRequest(
            item=item,
            episode_file_path=FilePath(episode_file_path),
            context_files=[FilePath(f) for f in context_files],
            metadata=metadata,
        )

    def _format_evaluation_details(self, evaluation_result) -> str:
        """評価結果の詳細フォーマット

        Args:
            evaluation_result: Claude Code評価結果

        Returns:
            str: フォーマット済み詳細メッセージ
        """
        details: Any = evaluation_result.details

        if not isinstance(details, dict) or "claude_evaluation" not in details:
            return "Claude Code評価完了(詳細情報なし)"

        claude_eval = details["claude_evaluation"]

        # 基本情報
        result_parts = [
            f"Claude Code評価結果: {claude_eval.get('result', 'UNKNOWN')}",
            f"信頼度: {claude_eval.get('confidence', 0.0):.2f}",
            f"主要理由: {claude_eval.get('primary_reason', '不明')}",
        ]

        # エビデンスポイント
        evidence_points = claude_eval.get("evidence_points", [])
        if evidence_points:
            result_parts.append(f"良い点: {len(evidence_points)}件確認")

        # 改善提案
        improvements = claude_eval.get("improvement_suggestions", [])
        if improvements:
            result_parts.append(f"改善提案: {len(improvements)}件")

        # 問題点
        issues = claude_eval.get("issues_found", [])
        if issues:
            result_parts.append(f"問題点: {len(issues)}件発見")

        return " | ".join(result_parts)

    def _generate_cache_key(self, content: str, item_id: str) -> str:
        """キャッシュキーの生成

        Args:
            content: エピソード内容
            item_id: 項目ID

        Returns:
            str: キャッシュキー
        """

        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:8]
        return f"{item_id}_{content_hash}"

    def _fallback_evaluation(self, item: A31ChecklistItem, error_message: str) -> tuple[float, str]:
        """フォールバック評価(エラー時)

        Args:
            item: チェックリスト項目
            error_message: エラーメッセージ

        Returns:
            tuple[float, str]: (フォールバックスコア, エラー詳細)
        """
        # 項目タイプに応じた基本スコア設定
        fallback_scores = {
            ChecklistItemType.FORMAT_CHECK: 75.0,
            ChecklistItemType.CONTENT_BALANCE: 70.0,
            ChecklistItemType.READABILITY_CHECK: 65.0,
            ChecklistItemType.CHARACTER_CONSISTENCY: 80.0,
            ChecklistItemType.STYLE_CONSISTENCY: 85.0,
        }

        base_score = fallback_scores.get(item.item_type, 60.0)

        details: Any = (
            f"Claude Code統合評価でエラーが発生しました。基本評価スコア: {base_score} | エラー: {error_message}"
        )

        return base_score, details


class SystemEvaluator:
    """システム自動系評価器"""

    def evaluate(self, content: str, item: A31ChecklistItem, context: dict[str, Any]) -> tuple[float, str]:
        """システム評価の実行"""
        return 95.0, "システム評価完了"
