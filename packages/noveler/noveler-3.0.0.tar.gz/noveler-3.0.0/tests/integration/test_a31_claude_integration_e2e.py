#!/usr/bin/env python3
"""A31+Claude統合システム E2Eテスト

A31拡張型+方式Bの完全なエンドツーエンドテストを実装し、
SDD+DDD+TDD準拠システムの動作を検証する。
"""

import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml

from noveler.application.use_cases.claude_analysis_request_generation_use_case import (
    ClaudeAnalysisRequestGenerationUseCase,
    GenerateClaudeAnalysisRequest,
)
from noveler.domain.services.a31_priority_extractor_service import (
    A31ChecklistData,
    A31PriorityExtractorService,
    PriorityExtractionCriteria,
)


@pytest.mark.spec("SPEC-A31-EXT-001")
@pytest.mark.integration
class TestA31ClaudeIntegrationE2E:
    """A31Claude統合システム エンドツーエンドテスト"""

    @pytest.fixture
    def sample_a31_checklist_data(self) -> dict[str, Any]:
        """テスト用A31チェックリストデータ"""
        return {
            "checklist_items": {
                "Phase2_執筆段階": [
                    {
                        "id": "A31-021",
                        "item": "冒頭3行で読者を引き込む工夫",
                        "type": "hook_check",
                        "required": True,
                        "status": False,
                        "reference_guides": ["$GUIDE_ROOT/冒頭の技法.md"],
                    },
                    {
                        "id": "A31-022",
                        "item": "会話と地の文のバランスを確認（3:7～4:6）",
                        "type": "content_balance",
                        "required": True,
                        "status": False,
                    },
                    {
                        "id": "A31-023",
                        "item": "五感描写を適切に配置",
                        "type": "sensory_check",
                        "required": True,
                        "status": False,
                    },
                ],
                "Phase3_推敲段階": [
                    {
                        "id": "A31-032",
                        "item": "文章のリズムと読みやすさを確認",
                        "type": "readability_check",
                        "required": True,
                        "status": False,
                    },
                    {
                        "id": "A31-033",
                        "item": "キャラクターの口調一貫性を検証",
                        "type": "character_consistency",
                        "required": True,
                        "status": False,
                    },
                ],
            },
            "metadata": {
                "checklist_name": "A31_原稿執筆チェックリスト",
                "target_episode": 4,
                "target_title": "DEBUGログの副作用",
                "version": "2.1",
            },
        }

    @pytest.fixture
    def temp_checklist_file(self, sample_a31_checklist_data: dict) -> str:
        """一時的なA31チェックリストファイル作成"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", encoding="utf-8", delete=False) as f:
            yaml.dump(sample_a31_checklist_data, f, allow_unicode=True)
            return f.name

    @pytest.mark.spec("SPEC-A31_CLAUDE_INTEGRATION_E2E-COMPLETE_A31_TO_CLAU")
    def test_complete_a31_to_claude_workflow(self, temp_checklist_file: str, sample_a31_checklist_data: dict) -> None:
        """完全なA31→Claude変換ワークフローのテスト"""

        # Step 1: A31重点項目抽出サービス初期化
        extractor_service = A31PriorityExtractorService()

        # Step 2: チェックリストデータ読み込み
        with open(temp_checklist_file, encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

        checklist_data = A31ChecklistData(
            checklist_items=yaml_data["checklist_items"],
            metadata=yaml_data["metadata"],
            target_episode=4,
            target_title="DEBUGログの副作用",
        )

        # Step 3: 抽出基準設定
        criteria = PriorityExtractionCriteria(priority_threshold=0.7, max_items=10)

        # Step 4: 重点項目抽出実行
        priority_items = extractor_service.extract_priority_items(checklist_data, criteria)

        # Step 5: 抽出結果検証
        assert len(priority_items) > 0, "重点項目が抽出されませんでした"
        assert len(priority_items) <= 10, "最大項目数制限が機能していません"

        # 高優先度項目が含まれることを確認
        high_priority_items = [item for item in priority_items if item.is_high_priority()]
        assert len(high_priority_items) > 0, "高優先度項目が抽出されませんでした"

        # Claude適性項目が含まれることを確認
        claude_suitable_items = [item for item in priority_items if item.is_claude_suitable()]
        assert len(claude_suitable_items) > 0, "Claude適性項目が抽出されませんでした"

    @pytest.mark.spec("SPEC-A31_CLAUDE_INTEGRATION_E2E-CLAUDE_ANALYSIS_REQU")
    def test_claude_analysis_request_generation(self, temp_checklist_file: str) -> None:
        """Claude分析リクエスト生成のテスト"""

        # アプリケーション層ユースケース初期化
        extractor_service = A31PriorityExtractorService()
        use_case = ClaudeAnalysisRequestGenerationUseCase(extractor_service)

        # 一時出力ファイル
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as output_file:
            output_path = output_file.name

        # リクエスト作成
        request = GenerateClaudeAnalysisRequest(
            checklist_file_path=temp_checklist_file,
            episode_number=4,
            max_priority_items=15,
            extraction_strategy="hybrid",
            output_file_path=output_path,
        )

        # 実行
        response = use_case.execute(request)

        # 成功検証
        assert response.success, f"リクエスト生成失敗: {response.error_message}"
        assert response.claude_request is not None
        assert response.extracted_items_count > 0

        # Claude分析リクエスト構造検証
        claude_request = response.claude_request

        # 必須セクション存在確認
        assert claude_request.analysis_context is not None
        assert claude_request.analysis_focus is not None
        assert claude_request.source_content is not None
        assert claude_request.output_requirements is not None

        # 分析コンテキスト内容確認
        context = claude_request.analysis_context
        assert "work_info" in context
        assert context["work_info"]["episode"] == 4
        assert context["work_info"]["title"] == "DEBUGログの副作用"

        # 出力ファイル生成確認
        assert Path(output_path).exists()

        # 生成されたYAMLの妥当性確認
        with open(output_path, encoding="utf-8") as f:
            generated_yaml = yaml.safe_load(f)

        assert "claude_analysis_request" in generated_yaml
        assert "metadata" in generated_yaml

    @pytest.mark.spec("SPEC-A31_CLAUDE_INTEGRATION_E2E-PRIORITY_EXTRACTION_")
    def test_priority_extraction_with_different_strategies(self, temp_checklist_file: str) -> None:
        """異なる抽出戦略での重点項目抽出テスト"""

        extractor_service = A31PriorityExtractorService()
        use_case = ClaudeAnalysisRequestGenerationUseCase(extractor_service)

        strategies = ["manual", "auto", "hybrid"]
        results = {}

        for strategy in strategies:
            request = GenerateClaudeAnalysisRequest(
                checklist_file_path=temp_checklist_file,
                episode_number=4,
                extraction_strategy=strategy,
                max_priority_items=20,
            )

            response = use_case.execute(request)
            assert response.success, f"戦略 {strategy} で失敗"

            results[strategy] = response.extracted_items_count

        # 戦略別結果検証
        assert results["manual"] > 0, "手動キューション戦略で項目が抽出されませんでした"
        assert results["auto"] > 0, "自動スコアリング戦略で項目が抽出されませんでした"
        assert results["hybrid"] > 0, "ハイブリッド戦略で項目が抽出されませんでした"

        # ハイブリッドが最も効果的であることを確認（期待値）
        # 実際のプロジェクトではこの値は調整される
        assert results["hybrid"] >= max(results["manual"], results["auto"]) * 0.8

    @pytest.mark.spec("SPEC-A31_CLAUDE_INTEGRATION_E2E-FOCUS_CATEGORY_FILTE")
    def test_focus_category_filtering(self, temp_checklist_file: str) -> None:
        """フォーカスカテゴリフィルタリングのテスト"""

        extractor_service = A31PriorityExtractorService()
        use_case = ClaudeAnalysisRequestGenerationUseCase(extractor_service)

        # 特定カテゴリにフォーカス
        request = GenerateClaudeAnalysisRequest(
            checklist_file_path=temp_checklist_file,
            episode_number=4,
            focus_categories=["content_balance", "sensory_description"],
            max_priority_items=20,
        )

        response = use_case.execute(request)
        assert response.success, "フォーカスカテゴリフィルタリングに失敗"

        # フィルタリング効果確認（項目数が制限されることを期待）
        assert response.extracted_items_count <= 20

    @pytest.mark.spec("SPEC-A31_CLAUDE_INTEGRATION_E2E-ERROR_HANDLING_AND_V")
    def test_error_handling_and_validation(self) -> None:
        """エラーハンドリングとバリデーションのテスト"""

        extractor_service = A31PriorityExtractorService()
        use_case = ClaudeAnalysisRequestGenerationUseCase(extractor_service)

        # 存在しないファイルでのテスト
        request = GenerateClaudeAnalysisRequest(checklist_file_path="nonexistent_file.yaml", episode_number=4)

        response = use_case.execute(request)
        assert not response.success
        assert "見つかりません" in response.error_message

    @pytest.mark.spec("SPEC-A31_CLAUDE_INTEGRATION_E2E-STATISTICAL_INFORMAT")
    def test_statistical_information_accuracy(self, temp_checklist_file: str) -> None:
        """統計情報の正確性テスト"""

        extractor_service = A31PriorityExtractorService()
        use_case = ClaudeAnalysisRequestGenerationUseCase(extractor_service)

        request = GenerateClaudeAnalysisRequest(
            checklist_file_path=temp_checklist_file, episode_number=4, max_priority_items=10
        )

        response = use_case.execute(request)
        assert response.success

        # 統計情報存在確認
        assert response.statistics is not None
        stats = response.statistics

        # 必須統計項目確認
        required_stats = [
            "total_items",
            "high_priority_items",
            "average_priority_score",
            "phase_distribution",
            "suitability_distribution",
            "claude_suitable_count",
        ]

        for stat_key in required_stats:
            assert stat_key in stats, f"統計情報 {stat_key} が不足しています"

        # 論理的整合性確認
        assert stats["total_items"] == response.extracted_items_count
        assert stats["high_priority_items"] <= stats["total_items"]
        assert stats["claude_suitable_count"] <= stats["total_items"]
        assert 0.0 <= stats["average_priority_score"] <= 1.0

    @pytest.mark.performance
    def test_performance_requirements(self, temp_checklist_file: str) -> None:
        """パフォーマンス要件のテスト"""
        import time

        extractor_service = A31PriorityExtractorService()
        use_case = ClaudeAnalysisRequestGenerationUseCase(extractor_service)

        request = GenerateClaudeAnalysisRequest(
            checklist_file_path=temp_checklist_file, episode_number=4, max_priority_items=25
        )

        # パフォーマンス測定
        start_time = time.time()
        response = use_case.execute(request)
        execution_time = time.time() - start_time

        # 成功確認
        assert response.success

        # パフォーマンス要件確認（SDD仕様: ≤1秒）
        assert execution_time < 1.0, f"実行時間が要件を超過: {execution_time:.2f}秒"

    def teardown_method(self) -> None:
        """テスト後クリーンアップ"""
        # 一時ファイルの削除は pytest-tempdir で自動処理される


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
