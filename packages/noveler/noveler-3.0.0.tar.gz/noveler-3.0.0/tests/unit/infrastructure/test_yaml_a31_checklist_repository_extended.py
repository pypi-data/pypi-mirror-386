#!/usr/bin/env python3

"""Tests.tests.unit.infrastructure.test_yaml_a31_checklist_repository_extended
Where: Automated test module.
What: Contains test cases verifying project behaviour.
Why: Ensures regressions are caught and documented.
"""

from __future__ import annotations

"""YamlA31ChecklistRepository拡張機能のテスト

A31CompleteEvaluationEngine連携に関するテストケース。
SPEC-A31-001準拠のリポジトリ拡張機能をテスト。
"""


import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from noveler.domain.entities.a31_complete_evaluation_engine import (
    A31EvaluationBatch,
    A31EvaluationCategory,
    A31EvaluationResult,
)
from noveler.infrastructure.repositories.yaml_a31_checklist_repository import YamlA31ChecklistRepository


@pytest.mark.spec("SPEC-A31-001")
class TestYamlA31ChecklistRepositoryExtended:
    """YamlA31ChecklistRepository拡張機能のテストクラス"""

    @pytest.fixture
    def temp_guide_root(self) -> Path:
        """一時ガイドルートディレクトリ"""
        with tempfile.TemporaryDirectory() as tmpdir:
            guide_root = Path(tmpdir)

            # テンプレートディレクトリとファイルを作成
            template_dir = guide_root / "templates"
            template_dir.mkdir(parents=True)

            template_content = {
                "metadata": {"version": "1.0", "template_type": "A31_checklist", "created_date": "2025-01-01T00:00:00"},
                "checklist_items": {
                    "format_check": [
                        {
                            "id": "A31-045",
                            "item": "段落頭は全角スペースで字下げ",
                            "type": "format_check",
                            "required": True,
                            "auto_fix_supported": True,
                            "auto_fix_level": "safe",
                        }
                    ],
                    "content_balance": [
                        {
                            "id": "A31-022",
                            "item": "会話と地の文のバランス(30%-40%)",
                            "type": "content_balance",
                            "required": True,
                            "auto_fix_supported": False,
                            "auto_fix_level": "none",
                        }
                    ],
                },
                "validation_summary": {"total_items": 2},
            }

            import yaml

            template_path = template_dir / "A31_原稿執筆チェックリストテンプレート.yaml"
            with template_path.Path("w").open(encoding="utf-8") as f:
                yaml.dump(template_content, f, allow_unicode=True, default_flow_style=False)

            yield guide_root

    @pytest.fixture
    def repository(self, temp_guide_root: Path) -> YamlA31ChecklistRepository:
        """テスト対象のリポジトリ"""
        return YamlA31ChecklistRepository(temp_guide_root)

    @pytest.fixture
    def sample_evaluation_batch(self) -> A31EvaluationBatch:
        """サンプル評価バッチ"""
        results = {
            "A31-045": A31EvaluationResult(
                item_id="A31-045",
                category=A31EvaluationCategory.FORMAT_CHECK,
                score=95.0,
                passed=True,
                details="段落字下げ適正",
                execution_time_ms=50.0,
                confidence=0.95,
                auto_fixable=True,
                fix_suggestions=["全角スペースで統一"],
            ),
            "A31-022": A31EvaluationResult(
                item_id="A31-022",
                category=A31EvaluationCategory.CONTENT_BALANCE,
                score=25.0,
                passed=False,
                details="会話比率不足",
                execution_time_ms=30.0,
                confidence=0.85,
                auto_fixable=False,
                fix_suggestions=["会話を追加してください"],
            ),
        }

        return A31EvaluationBatch(results=results, total_items=2, evaluated_items=2, execution_time_ms=80.0)

    def test_repository_initialization(self, temp_guide_root: Path) -> None:
        """リポジトリの初期化テスト"""
        repository = YamlA31ChecklistRepository(temp_guide_root)

        assert repository.guide_root == temp_guide_root
        assert repository.template_path == temp_guide_root / "templates" / "A31_原稿執筆チェックリストテンプレート.yaml"

    def test_load_template_success(self, repository: YamlA31ChecklistRepository) -> None:
        """テンプレート読み込み成功テスト"""
        template = repository.load_template()

        assert template is not None
        assert "metadata" in template
        assert "checklist_items" in template
        assert "validation_summary" in template
        assert template["validation_summary"]["total_items"] == 2

    def test_get_all_checklist_items_success(self, repository: YamlA31ChecklistRepository) -> None:
        """全チェックリスト項目取得成功テスト"""
        items = repository.get_all_checklist_items("テストプロジェクト")

        assert len(items) == 2
        assert any(item.item_id == "A31-045" for item in items)
        assert any(item.item_id == "A31-022" for item in items)

        # A31-045項目の詳細確認
        item_045 = next(item for item in items if item.item_id == "A31-045")
        assert item_045.title == "段落頭は全角スペースで字下げ"
        assert item_045.is_auto_fixable() is True
        assert item_045.auto_fix_strategy.fix_level == "safe"

    @patch("noveler.domain.value_objects.project_time.project_now")
    def test_save_evaluation_results_success(
        self,
        mock_project_now: Mock,
        repository: YamlA31ChecklistRepository,
        sample_evaluation_batch: A31EvaluationBatch,
    ) -> None:
        """評価結果保存成功テスト"""
        # project_nowのモック設定
        mock_time = Mock()
        mock_time.format_timestamp.return_value = "20250101_120000"
        mock_time.isoformat.return_value = "2025-01-01T12:00:00"
        mock_project_now.return_value = mock_time

        # Execute
        result_path = repository.save_evaluation_results("テストプロジェクト", 1, sample_evaluation_batch)

        # Assert
        assert result_path.exists()
        assert result_path.name == "A31_evaluation_テストプロジェクト_episode_001_20250101_120000.yaml"

        # ファイル内容の検証
        import yaml

        with result_path.Path("r").open(encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        assert saved_data["metadata"]["project_name"] == "テストプロジェクト"
        assert saved_data["metadata"]["episode_number"] == 1
        assert saved_data["metadata"]["total_items"] == 2
        assert saved_data["metadata"]["evaluated_items"] == 2

        # 評価結果の検証
        eval_results = saved_data["evaluation_results"]
        assert eval_results["average_score"] == 60.0  # (95.0 + 25.0) / 2
        assert eval_results["pass_rate"] == 0.5  # 1/2

        # 項目結果の検証
        item_results = eval_results["item_results"]
        assert "A31-045" in item_results
        assert "A31-022" in item_results

        item_045_result = item_results["A31-045"]
        assert item_045_result["item_id"] == "A31-045"
        assert item_045_result["score"] == 95.0
        assert item_045_result["passed"] is True
        assert item_045_result["auto_fixable"] is True
        assert "全角スペースで統一" in item_045_result["fix_suggestions"]

    def test_serialize_category_stats(self, repository: YamlA31ChecklistRepository) -> None:
        """カテゴリ統計シリアライズテスト"""
        category_stats = {
            A31EvaluationCategory.FORMAT_CHECK: {"count": 1, "pass_rate": 1.0, "average_score": 95.0},
            A31EvaluationCategory.CONTENT_BALANCE: {"count": 1, "pass_rate": 0.0, "average_score": 25.0},
        }

        serialized = repository._serialize_category_stats(category_stats)

        assert "format_check" in serialized
        assert "content_balance" in serialized
        assert serialized["format_check"]["count"] == 1
        assert serialized["format_check"]["pass_rate"] == 1.0
        assert serialized["content_balance"]["average_score"] == 25.0

    def test_serialize_evaluation_results(
        self, repository: YamlA31ChecklistRepository, sample_evaluation_batch: A31EvaluationBatch
    ) -> None:
        """評価結果シリアライズテスト"""
        serialized = repository._serialize_evaluation_results(sample_evaluation_batch.results)

        assert "A31-045" in serialized
        assert "A31-022" in serialized

        # A31-045結果の検証
        result_045 = serialized["A31-045"]
        assert result_045["item_id"] == "A31-045"
        assert result_045["category"] == "format_check"
        assert result_045["score"] == 95.0
        assert result_045["passed"] is True
        assert result_045["confidence"] == 0.95

        # A31-022結果の検証
        result_022 = serialized["A31-022"]
        assert result_022["item_id"] == "A31-022"
        assert result_022["category"] == "content_balance"
        assert result_022["score"] == 25.0
        assert result_022["passed"] is False
        assert len(result_022["fix_suggestions"]) == 1

    def test_get_auto_fixable_items_safe_level(self, repository: YamlA31ChecklistRepository) -> None:
        """自動修正可能項目取得テスト(safeレベル)"""
        auto_fixable_items = repository.get_auto_fixable_items("safe")

        # A31-045のみが自動修正可能でsafeレベル
        assert len(auto_fixable_items) == 1
        assert auto_fixable_items[0].item_id == "A31-045"
        assert auto_fixable_items[0].auto_fix_strategy.fix_level == "safe"

    def test_get_auto_fixable_items_none_level(self, repository: YamlA31ChecklistRepository) -> None:
        """自動修正可能項目取得テスト(レベル制限なし)"""
        auto_fixable_items = repository.get_auto_fixable_items("interactive")

        # interactiveレベルではsafeレベルの項目も含む
        assert len(auto_fixable_items) == 1
        assert auto_fixable_items[0].item_id == "A31-045"

    def test_create_checklist_item_from_dict(self, repository: YamlA31ChecklistRepository) -> None:
        """辞書からチェックリスト項目作成テスト"""
        item_data = {
            "id": "A31-045",
            "item": "段落頭は全角スペースで字下げ",
            "type": "format_check",
            "required": True,
            "auto_fix_supported": True,
            "auto_fix_level": "safe",
        }

        item = repository._create_checklist_item_from_dict(item_data)

        assert item.item_id == "A31-045"
        assert item.title == "段落頭は全角スペースで字下げ"
        assert item.required is True
        assert item.is_auto_fixable() is True
        assert item.auto_fix_strategy.fix_level == "safe"
        assert item.auto_fix_strategy.priority == 1  # 高優先度

    def test_determine_item_type_mapping(self, repository: YamlA31ChecklistRepository) -> None:
        """項目タイプ決定のマッピングテスト"""
        from noveler.domain.entities.a31_checklist_item import ChecklistItemType

        assert repository._determine_item_type("format_check") == ChecklistItemType.FORMAT_CHECK
        assert repository._determine_item_type("content_balance") == ChecklistItemType.CONTENT_BALANCE
        assert repository._determine_item_type("quality_threshold") == ChecklistItemType.QUALITY_THRESHOLD
        assert repository._determine_item_type("unknown_type") == ChecklistItemType.CONTENT_REVIEW  # デフォルト

    def test_create_threshold_from_item_specific_ids(self, repository: YamlA31ChecklistRepository) -> None:
        """特定項目IDに対する閾値作成テスト"""
        from noveler.domain.value_objects.a31_threshold import ThresholdType

        # A31-045: 段落字下げ(100%)
        threshold_045 = repository._create_threshold_from_item({"id": "A31-045"})
        assert threshold_045.threshold_type == ThresholdType.PERCENTAGE
        assert threshold_045.value == 100.0

        # A31-042: 品質スコア(70点)
        threshold_042 = repository._create_threshold_from_item({"id": "A31-042"})
        assert threshold_042.threshold_type == ThresholdType.SCORE
        assert threshold_042.value == 70.0

        # A31-022: 会話バランス(範囲30-40%)
        threshold_022 = repository._create_threshold_from_item({"id": "A31-022"})
        assert threshold_022.threshold_type == ThresholdType.RANGE

        # 未知のID: デフォルト(Boolean)
        threshold_default = repository._create_threshold_from_item({"id": "A31-999"})
        assert threshold_default.threshold_type == ThresholdType.BOOLEAN
        assert threshold_default.value == 1.0

    def test_get_fix_priority_mapping(self, repository: YamlA31ChecklistRepository) -> None:
        """修正優先度取得のマッピングテスト"""
        assert repository._get_fix_priority("A31-045") == 1  # 高優先度
        assert repository._get_fix_priority("A31-035") == 1  # 高優先度
        assert repository._get_fix_priority("A31-031") == 2  # 中優先度
        assert repository._get_fix_priority("A31-042") == 3  # 中優先度
        assert repository._get_fix_priority("A31-022") == 4  # 低優先度
        assert repository._get_fix_priority("A31-999") == 5  # デフォルト

    def test_is_compatible_fix_level(self, repository: YamlA31ChecklistRepository) -> None:
        """修正レベル互換性チェックテスト"""
        # safe ≤ safe
        assert repository._is_compatible_fix_level("safe", "safe") is True

        # safe ≤ standard
        assert repository._is_compatible_fix_level("safe", "standard") is True

        # safe ≤ interactive
        assert repository._is_compatible_fix_level("safe", "interactive") is True

        # standard > safe
        assert repository._is_compatible_fix_level("standard", "safe") is False

        # standard ≤ interactive
        assert repository._is_compatible_fix_level("standard", "interactive") is True

        # interactive > standard
        assert repository._is_compatible_fix_level("interactive", "standard") is False

    @patch("noveler.domain.value_objects.project_time.project_now")
    def test_save_evaluation_results_error_handling(self, mock_project_now: Mock, temp_guide_root: Path) -> None:
        """評価結果保存エラーハンドリングテスト"""
        # 書き込み権限のないディレクトリでリポジトリを作成
        repository = YamlA31ChecklistRepository(Path("/invalid/path"))

        # project_nowのモック設定
        mock_time = Mock()
        mock_time.format_timestamp.return_value = "20250101_120000"
        mock_time.isoformat.return_value = "2025-01-01T12:00:00"
        mock_project_now.return_value = mock_time

        # サンプル評価バッチ
        sample_batch = A31EvaluationBatch({}, 0, 0, 0.0)

        # Execute & Assert
        with pytest.raises(OSError, match="評価結果の保存に失敗しました"):
            repository.save_evaluation_results("テストプロジェクト", 1, sample_batch)


@pytest.mark.spec("SPEC-A31-001")
class TestYamlA31ChecklistRepositoryIntegration:
    """YamlA31ChecklistRepository統合テストクラス"""

    @pytest.fixture
    def temp_guide_root(self) -> Path:
        """統合テスト用の一時ガイドルート"""
        with tempfile.TemporaryDirectory() as tmpdir:
            guide_root = Path(tmpdir)

            # より完全なテンプレートを作成
            template_dir = guide_root / "templates"
            template_dir.mkdir(parents=True)

            template_content = {
                "metadata": {"version": "1.0", "template_type": "A31_checklist", "created_date": "2025-01-01T00:00:00"},
                "checklist_items": {
                    "format_check": [
                        {
                            "id": "A31-045",
                            "item": "段落頭は全角スペースで字下げ",
                            "type": "format_check",
                            "required": True,
                            "auto_fix_supported": True,
                            "auto_fix_level": "safe",
                        },
                        {
                            "id": "A31-035",
                            "item": "記号統一(「」など)",
                            "type": "format_check",
                            "required": True,
                            "auto_fix_supported": True,
                            "auto_fix_level": "safe",
                        },
                    ],
                    "quality_threshold": [
                        {
                            "id": "A31-042",
                            "item": "品質スコア70点以上",
                            "type": "quality_threshold",
                            "required": True,
                            "auto_fix_supported": False,
                            "auto_fix_level": "none",
                        }
                    ],
                    "content_balance": [
                        {
                            "id": "A31-022",
                            "item": "会話と地の文のバランス(30%-40%)",
                            "type": "content_balance",
                            "required": True,
                            "auto_fix_supported": False,
                            "auto_fix_level": "none",
                        }
                    ],
                },
                "validation_summary": {"total_items": 4},
            }

            import yaml

            template_path = template_dir / "A31_原稿執筆チェックリストテンプレート.yaml"
            with template_path.Path("w").open(encoding="utf-8") as f:
                yaml.dump(template_content, f, allow_unicode=True, default_flow_style=False)

            yield guide_root

    @patch("noveler.domain.value_objects.project_time.project_now")
    def test_complete_workflow_with_evaluation_batch(self, mock_project_now: Mock, temp_guide_root: Path) -> None:
        """評価バッチを使った完全なワークフローテスト"""
        # project_nowのモック設定
        mock_time = Mock()
        mock_time.format_timestamp.return_value = "20250101_120000"
        mock_time.isoformat.return_value = "2025-01-01T12:00:00"
        mock_project_now.return_value = mock_time

        # リポジトリ作成
        repository = YamlA31ChecklistRepository(temp_guide_root)

        # 1. 全チェックリスト項目を取得
        all_items = repository.get_all_checklist_items("統合テストプロジェクト")
        assert len(all_items) == 4

        # 2. 自動修正可能項目を取得
        auto_fixable_items = repository.get_auto_fixable_items("safe")
        assert len(auto_fixable_items) == 2  # A31-045, A31-035

        # 3. 評価結果を作成
        evaluation_results = {}
        for item in all_items:
            if item.item_id == "A31-045":
                result = A31EvaluationResult(
                    item_id=item.item_id,
                    category=A31EvaluationCategory.FORMAT_CHECK,
                    score=100.0,
                    passed=True,
                    details="段落字下げ完璧",
                    execution_time_ms=25.0,
                    auto_fixable=True,
                )

            elif item.item_id == "A31-035":
                result = A31EvaluationResult(
                    item_id=item.item_id,
                    category=A31EvaluationCategory.FORMAT_CHECK,
                    score=95.0,
                    passed=True,
                    details="記号統一適正",
                    execution_time_ms=20.0,
                    auto_fixable=True,
                )

            elif item.item_id == "A31-042":
                result = A31EvaluationResult(
                    item_id=item.item_id,
                    category=A31EvaluationCategory.QUALITY_THRESHOLD,
                    score=75.0,
                    passed=True,
                    details="品質基準クリア",
                    execution_time_ms=15.0,
                    auto_fixable=False,
                )

            else:  # A31-022
                result = A31EvaluationResult(
                    item_id=item.item_id,
                    category=A31EvaluationCategory.CONTENT_BALANCE,
                    score=20.0,
                    passed=False,
                    details="会話比率不足",
                    execution_time_ms=30.0,
                    auto_fixable=False,
                )

            evaluation_results[item.item_id] = result

        # 4. 評価バッチを作成
        evaluation_batch = A31EvaluationBatch(
            results=evaluation_results, total_items=4, evaluated_items=4, execution_time_ms=90.0
        )

        # 5. 評価結果を保存
        saved_path = repository.save_evaluation_results("統合テストプロジェクト", 1, evaluation_batch)

        # 6. 保存されたファイルを検証
        assert saved_path.exists()

        import yaml

        with saved_path.Path("r").open(encoding="utf-8") as f:
            saved_data = yaml.safe_load(f)

        # メタデータ検証
        metadata = saved_data["metadata"]
        assert metadata["project_name"] == "統合テストプロジェクト"
        assert metadata["episode_number"] == 1
        assert metadata["total_items"] == 4
        assert metadata["evaluated_items"] == 4

        # 評価結果検証
        eval_results = saved_data["evaluation_results"]
        assert eval_results["average_score"] == 72.5  # (100+95+75+20)/4
        assert eval_results["pass_rate"] == 0.75  # 3/4

        # カテゴリ統計検証
        category_stats = eval_results["category_statistics"]
        assert "format_check" in category_stats
        assert "quality_threshold" in category_stats
        assert "content_balance" in category_stats

        format_stats = category_stats["format_check"]
        assert format_stats["count"] == 2
        assert format_stats["pass_rate"] == 1.0  # A31-045, A31-035ともに合格
        assert format_stats["average_score"] == 97.5  # (100+95)/2

        content_stats = category_stats["content_balance"]
        assert content_stats["count"] == 1
        assert content_stats["pass_rate"] == 0.0  # A31-022が不合格
        assert content_stats["average_score"] == 20.0

        # 項目別結果検証
        item_results = eval_results["item_results"]
        assert len(item_results) == 4

        # A31-045の詳細確認
        item_045 = item_results["A31-045"]
        assert item_045["score"] == 100.0
        assert item_045["passed"] is True
        assert item_045["auto_fixable"] is True

        # A31-022の詳細確認
        item_022 = item_results["A31-022"]
        assert item_022["score"] == 20.0
        assert item_022["passed"] is False
        assert item_022["auto_fixable"] is False
