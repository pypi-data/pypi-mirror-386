#!/usr/bin/env python3

"""Tests.tests.unit.domain.entities.test_a31_complete_evaluation_engine
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

"""A31完全評価エンジンのテストケース(TDD実装)

SPEC-A31-001準拠の6カテゴリ評価エンジンのテスト定義。
DDD構造に基づくドメインレイヤーの単体テスト。
"""


import pytest
pytestmark = pytest.mark.a31_evaluation

from noveler.domain.entities.a31_checklist_item import A31ChecklistItem, ChecklistItemType
from noveler.domain.entities.a31_complete_evaluation_engine import (
    A31CompleteEvaluationEngine,
    A31EvaluationBatch,
    A31EvaluationCategory,
    A31EvaluationResult,
)
from noveler.domain.value_objects.a31_auto_fix_strategy import AutoFixStrategy
from noveler.domain.value_objects.a31_threshold import Threshold, ThresholdType


@pytest.mark.spec("SPEC-A31-001")
class TestA31CompleteEvaluationEngine:
    """A31完全評価エンジンのテストクラス"""

    @pytest.fixture
    def sample_episode_content(self) -> str:
        """サンプルエピソード内容"""
        return """# 第001話 テストエピソード

 普通の人間には見えない赤い文字が、視界いっぱいに踊り狂っていた。

「これはテストです」と彼は言った。

 風が頬を撫で、甘い香りが鼻をくすぐった。鳥のさえずりが耳に心地よく響く。

 彼は手を握りしめた。温かく、力強い感触だった。
"""

    @pytest.fixture
    def format_check_item(self) -> A31ChecklistItem:
        """フォーマット系チェック項目(段落字下げ)"""
        return A31ChecklistItem(
            item_id="A31-045",
            title="段落頭の字下げを確認",
            required=True,
            item_type=ChecklistItemType.FORMAT_CHECK,
            threshold=Threshold(ThresholdType.PERCENTAGE, 95.0),
            auto_fix_strategy=AutoFixStrategy(supported=True, fix_level="safe", priority=1),
        )

    @pytest.fixture
    def content_balance_item(self) -> A31ChecklistItem:
        """内容バランス系チェック項目(会話比率)"""
        return A31ChecklistItem(
            item_id="A31-022",
            title="会話と地の文のバランスを確認(3:7~4:6)",
            required=True,
            item_type=ChecklistItemType.CONTENT_BALANCE,
            threshold=Threshold.create_range(30.0, 40.0),
            auto_fix_strategy=AutoFixStrategy(supported=False, fix_level="none", priority=0),
        )

    @pytest.fixture
    def engine(self) -> A31CompleteEvaluationEngine:
        """評価エンジンインスタンス"""
        return A31CompleteEvaluationEngine()

    @pytest.mark.spec("SPEC-A31_COMPLETE_EVALUATION_ENGINE-ENGINE_INITIALIZATIO")
    def test_engine_initialization(self, engine: A31CompleteEvaluationEngine) -> None:
        """評価エンジンの初期化テスト"""
        assert engine is not None
        assert len(engine.evaluators) == 6  # 6カテゴリの評価器
        assert A31EvaluationCategory.FORMAT_CHECK in engine.evaluators
        assert A31EvaluationCategory.QUALITY_THRESHOLD in engine.evaluators
        assert A31EvaluationCategory.CONTENT_BALANCE in engine.evaluators
        assert A31EvaluationCategory.CONSISTENCY_CHECK in engine.evaluators
        assert A31EvaluationCategory.CLAUDE_CODE_EVALUATION in engine.evaluators
        assert A31EvaluationCategory.SYSTEM_FUNCTION in engine.evaluators

    @pytest.mark.spec("SPEC-A31_COMPLETE_EVALUATION_ENGINE-FORMAT_CHECK_EVALUAT")
    def test_format_check_evaluation_paragraph_indentation(
        self, engine: A31CompleteEvaluationEngine, format_check_item: A31ChecklistItem, sample_episode_content: str
    ) -> None:
        """フォーマット系評価:段落字下げのテスト"""
        result = engine.evaluate_single_item(content=sample_episode_content, item=format_check_item, context={})

        assert isinstance(result, A31EvaluationResult)
        assert result.item_id == "A31-045"
        assert result.category == A31EvaluationCategory.FORMAT_CHECK
        assert result.passed is True  # サンプルは全段落字下げ済み
        assert result.score >= 95.0  # 閾値以上
        assert "段落字下げ" in result.details

    @pytest.mark.spec("SPEC-A31_COMPLETE_EVALUATION_ENGINE-CONTENT_BALANCE_EVAL")
    def test_content_balance_evaluation_dialogue_ratio(
        self, engine: A31CompleteEvaluationEngine, content_balance_item: A31ChecklistItem, sample_episode_content: str
    ) -> None:
        """内容バランス系評価:会話比率のテスト"""
        result = engine.evaluate_single_item(content=sample_episode_content, item=content_balance_item, context={})

        assert isinstance(result, A31EvaluationResult)
        assert result.item_id == "A31-022"
        assert result.category == A31EvaluationCategory.CONTENT_BALANCE
        # サンプルは会話が少ないので範囲外の可能性が高い
        assert 0.0 <= result.score <= 100.0
        assert "会話比率" in result.details or "dialogue_ratio" in result.details

    @pytest.mark.spec("SPEC-A31_COMPLETE_EVALUATION_ENGINE-EVALUATE_ALL_ITEMS_B")
    def test_evaluate_all_items_batch_processing(
        self,
        engine: A31CompleteEvaluationEngine,
        format_check_item: A31ChecklistItem,
        content_balance_item: A31ChecklistItem,
        sample_episode_content: str,
    ) -> None:
        """全項目一括評価のバッチ処理テスト"""
        items = [format_check_item, content_balance_item]

        batch_result = engine.evaluate_all_items(content=sample_episode_content, items=items, context={})

        assert isinstance(batch_result, A31EvaluationBatch)
        assert len(batch_result.results) == 2
        assert "A31-045" in batch_result.results
        assert "A31-022" in batch_result.results

        # 実行時間とメタデータの確認
        assert batch_result.execution_time_ms > 0
        assert batch_result.total_items == 2
        assert batch_result.evaluated_items == 2

    @pytest.mark.spec("SPEC-A31_COMPLETE_EVALUATION_ENGINE-CATEGORY_FILTERING")
    def test_category_filtering(
        self,
        engine: A31CompleteEvaluationEngine,
        format_check_item: A31ChecklistItem,
        content_balance_item: A31ChecklistItem,
    ) -> None:
        """カテゴリフィルタリング機能のテスト"""
        items = [format_check_item, content_balance_item]

        # フォーマット系のみフィルタ
        format_items = engine.filter_items_by_category(items, A31EvaluationCategory.FORMAT_CHECK)

        assert len(format_items) == 1
        assert format_items[0].item_id == "A31-045"

        # 内容バランス系のみフィルタ
        balance_items = engine.filter_items_by_category(items, A31EvaluationCategory.CONTENT_BALANCE)

        assert len(balance_items) == 1
        assert balance_items[0].item_id == "A31-022"

    @pytest.mark.spec("SPEC-A31_COMPLETE_EVALUATION_ENGINE-ERROR_HANDLING_INVAL")
    def test_error_handling_invalid_content(
        self, engine: A31CompleteEvaluationEngine, format_check_item: A31ChecklistItem
    ) -> None:
        """不正コンテンツに対するエラーハンドリングテスト"""
        # 空のコンテンツ
        result = engine.evaluate_single_item(content="", item=format_check_item, context={})

        assert isinstance(result, A31EvaluationResult)
        assert result.passed is False
        assert result.score == 0.0
        assert "error" in result.details.lower() or "empty" in result.details.lower()

    @pytest.mark.spec("SPEC-A31_COMPLETE_EVALUATION_ENGINE-EVALUATION_RESULT_SE")
    def test_evaluation_result_serialization(
        self, engine: A31CompleteEvaluationEngine, format_check_item: A31ChecklistItem, sample_episode_content: str
    ) -> None:
        """評価結果のシリアライゼーションテスト"""
        result = engine.evaluate_single_item(content=sample_episode_content, item=format_check_item, context={})

        # 辞書への変換
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["item_id"] == "A31-045"
        assert "score" in result_dict
        assert "passed" in result_dict
        assert "category" in result_dict

        # 辞書からの復元
        restored_result = A31EvaluationResult.from_dict(result_dict)
        assert restored_result.item_id == result.item_id
        assert restored_result.score == result.score
        assert restored_result.passed == result.passed

    @pytest.mark.spec("SPEC-A31_COMPLETE_EVALUATION_ENGINE-PERFORMANCE_REQUIREM")
    def test_performance_requirements(
        self, engine: A31CompleteEvaluationEngine, format_check_item: A31ChecklistItem, sample_episode_content: str
    ) -> None:
        """パフォーマンス要件のテスト"""
        import time

        start_time = time.time()

        # 単一項目評価は100ms以下であること
        result = engine.evaluate_single_item(content=sample_episode_content, item=format_check_item, context={})

        execution_time = (time.time() - start_time) * 1000  # ms
        assert execution_time < 100.0  # 100ms未満
        assert isinstance(result, A31EvaluationResult)

    @pytest.mark.spec("SPEC-A31_COMPLETE_EVALUATION_ENGINE-THREAD_SAFETY")
    def test_thread_safety(
        self, engine: A31CompleteEvaluationEngine, format_check_item: A31ChecklistItem, sample_episode_content: str
    ) -> None:
        """スレッドセーフティのテスト"""
        import concurrent.futures

        results = []

        def evaluate_item() -> A31EvaluationResult:
            return engine.evaluate_single_item(content=sample_episode_content, item=format_check_item, context={})

        # 3つの並列実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(evaluate_item) for _ in range(3)]
            results = [future.result() for future in futures]

        # 全ての結果が同じであること
        assert len(results) == 3
        for result in results:
            assert isinstance(result, A31EvaluationResult)
            assert result.item_id == "A31-045"
            # 全て同じスコアであること
            assert result.score == results[0].score


@pytest.mark.spec("SPEC-A31-001")
class TestA31EvaluationBatch:
    """A31評価バッチのテストクラス"""

    @pytest.mark.spec("SPEC-A31_COMPLETE_EVALUATION_ENGINE-BATCH_AGGREGATION")
    def test_batch_aggregation(self) -> None:
        """バッチ集計機能のテスト"""
        # テスト用の評価結果を作成
        results = {
            "A31-045": A31EvaluationResult(
                item_id="A31-045",
                category=A31EvaluationCategory.FORMAT_CHECK,
                score=95.0,
                passed=True,
                details="段落字下げ適正",
                execution_time_ms=50.0,
            ),
            "A31-022": A31EvaluationResult(
                item_id="A31-022",
                category=A31EvaluationCategory.CONTENT_BALANCE,
                score=25.0,
                passed=False,
                details="会話比率不足",
                execution_time_ms=30.0,
            ),
        }

        batch = A31EvaluationBatch(results=results, total_items=2, evaluated_items=2, execution_time_ms=80.0)

        # 集計結果の確認
        assert batch.get_average_score() == 60.0  # (95 + 25) / 2
        assert batch.get_pass_rate() == 0.5  # 1/2
        assert batch.get_total_execution_time() == 80.0

        # カテゴリ別集計
        category_stats = batch.get_category_statistics()
        assert A31EvaluationCategory.FORMAT_CHECK in category_stats
        assert A31EvaluationCategory.CONTENT_BALANCE in category_stats
        assert category_stats[A31EvaluationCategory.FORMAT_CHECK]["pass_rate"] == 1.0
        assert category_stats[A31EvaluationCategory.CONTENT_BALANCE]["pass_rate"] == 0.0

    @pytest.mark.spec("SPEC-A31_COMPLETE_EVALUATION_ENGINE-BATCH_FILTERING")
    def test_batch_filtering(self) -> None:
        """バッチフィルタリング機能のテスト"""
        results = {
            "A31-045": A31EvaluationResult(
                item_id="A31-045",
                category=A31EvaluationCategory.FORMAT_CHECK,
                score=95.0,
                passed=True,
                details="段落字下げ適正",
                execution_time_ms=50.0,
            ),
            "A31-022": A31EvaluationResult(
                item_id="A31-022",
                category=A31EvaluationCategory.CONTENT_BALANCE,
                score=25.0,
                passed=False,
                details="会話比率不足",
                execution_time_ms=30.0,
            ),
        }

        batch = A31EvaluationBatch(results=results, total_items=2, evaluated_items=2, execution_time_ms=80.0)

        # 合格項目のみフィルタ
        passed_results = batch.filter_passed_items()
        assert len(passed_results) == 1
        assert "A31-045" in passed_results

        # 不合格項目のみフィルタ
        failed_results = batch.filter_failed_items()
        assert len(failed_results) == 1
        assert "A31-022" in failed_results

        # カテゴリ別フィルタ
        format_results = batch.filter_by_category(A31EvaluationCategory.FORMAT_CHECK)
        assert len(format_results) == 1
        assert "A31-045" in format_results
