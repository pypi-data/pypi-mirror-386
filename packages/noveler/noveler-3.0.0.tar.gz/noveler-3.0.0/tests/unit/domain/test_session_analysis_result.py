#!/usr/bin/env python3
"""SessionAnalysisResult エンティティ単体テスト

Claude Codeセッション内分析結果エンティティの
ビジネスロジックと状態管理の正確性を検証する。
"""

import pytest

from noveler.domain.entities.a31_priority_item import A31PriorityItem
from noveler.domain.entities.session_analysis_result import (
    AnalysisConfidence,
    AnalysisImprovement,
    AnalysisStatus,
    ItemAnalysisResult,
    SessionAnalysisId,
    SessionAnalysisResult,
)
from noveler.domain.value_objects.a31_check_phase import A31CheckPhase
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory
from noveler.domain.value_objects.priority_item_id import PriorityItemId


class TestSessionAnalysisResult:
    """SessionAnalysisResult エンティティテスト"""

    @pytest.mark.spec("SPEC-A31-SESSION-001")
    def test_create_new_session_result(self):
        """新規セッション分析結果作成テスト"""
        # Act
        result = SessionAnalysisResult.create_new(
            project_name="テストプロジェクト",
            episode_number=4,
            manuscript_path="test_manuscript.md",
            total_priority_items=15,
        )

        # Assert
        assert result.project_name == "テストプロジェクト"
        assert result.episode_number == 4
        assert result.overall_status == AnalysisStatus.PENDING
        assert result.get_completion_rate() == 0.0
        assert len(result.item_results) == 0
        assert isinstance(result.analysis_id, SessionAnalysisId)

    @pytest.mark.spec("SPEC-A31-SESSION-001")
    def test_start_analysis_state_transition(self):
        """分析開始状態遷移テスト"""
        # Arrange
        result = SessionAnalysisResult.create_new("プロジェクト", 1, "manuscript.md", 10)

        # Act
        result.start_analysis()

        # Assert
        assert result.overall_status == AnalysisStatus.IN_PROGRESS
        assert result._started_at is not None

        # 二重開始エラーテスト
        with pytest.raises(ValueError, match="分析は既に開始されています"):
            result.start_analysis()

    @pytest.mark.spec("SPEC-A31-SESSION-001")
    def test_add_item_analysis_result(self):
        """項目分析結果追加テスト"""
        # Arrange
        session_result = SessionAnalysisResult.create_new("プロジェクト", 1, "manuscript.md", 5)

        session_result.start_analysis()

        priority_item = self._create_mock_priority_item("A31-001")
        item_result = ItemAnalysisResult(
            priority_item=priority_item,
            analysis_score=8.5,
            status=AnalysisStatus.COMPLETED,
            confidence=AnalysisConfidence.HIGH,
            improvements=[],
            issues_found=["テスト問題"],
            execution_time=2.5,
        )

        # Act
        session_result.add_item_analysis_result(item_result)

        # Assert
        assert len(session_result.item_results) == 1
        assert "A31-001" in session_result.item_results
        assert session_result._total_execution_time == 2.5
        assert session_result._successful_analyses == 1

    @pytest.mark.spec("SPEC-A31-SESSION-001")
    def test_complete_analysis_status_determination(self):
        """分析完了ステータス決定テスト"""
        # Arrange
        session_result = SessionAnalysisResult.create_new("プロジェクト", 1, "manuscript.md", 3)

        session_result.start_analysis()

        # 成功結果追加
        successful_item = self._create_mock_item_result("A31-001", True, 8.0)
        failed_item = self._create_mock_item_result("A31-002", False, 0.0)

        session_result.add_item_analysis_result(successful_item)
        session_result.add_item_analysis_result(failed_item)

        # Act
        session_result.complete_analysis()

        # Assert
        assert session_result.overall_status == AnalysisStatus.PARTIAL
        assert session_result._completed_at is not None
        assert session_result.get_success_rate() == 0.5

    @pytest.mark.spec("SPEC-A31-SESSION-001")
    def test_completion_rate_calculation(self):
        """完了率計算精度テスト"""
        # Arrange
        session_result = SessionAnalysisResult.create_new("プロジェクト", 1, "manuscript.md", 10)

        session_result.start_analysis()

        # 3件の結果追加
        for i in range(3):
            item_result = self._create_mock_item_result(f"A31-00{i + 1}", True, 7.0)
            session_result.add_item_analysis_result(item_result)

        # Act & Assert
        assert session_result.get_completion_rate() == 0.3  # 3/10

        # 2件追加して再計算
        for i in range(2):
            item_result = self._create_mock_item_result(f"A31-00{i + 4}", True, 8.0)
            session_result.add_item_analysis_result(item_result)

        assert session_result.get_completion_rate() == 0.5  # 5/10

    @pytest.mark.spec("SPEC-A31-SESSION-001")
    def test_high_confidence_improvements_filtering(self):
        """高信頼度改善提案フィルタリングテスト"""
        # Arrange
        session_result = SessionAnalysisResult.create_new("プロジェクト", 1, "manuscript.md", 3)

        session_result.start_analysis()

        # 高信頼度改善提案を含む結果
        high_conf_improvement = AnalysisImprovement(
            original_text="改善前",
            improved_text="改善後",
            improvement_type="test_improvement",
            confidence=AnalysisConfidence.HIGH,
            reasoning="高信頼度テスト",
        )

        low_conf_improvement = AnalysisImprovement(
            original_text="改善前2",
            improved_text="改善後2",
            improvement_type="test_improvement_2",
            confidence=AnalysisConfidence.LOW,
            reasoning="低信頼度テスト",
        )

        priority_item = self._create_mock_priority_item("A31-001")
        item_result = ItemAnalysisResult(
            priority_item=priority_item,
            analysis_score=8.0,
            status=AnalysisStatus.COMPLETED,
            confidence=AnalysisConfidence.HIGH,
            improvements=[high_conf_improvement, low_conf_improvement],
            issues_found=[],
            execution_time=1.0,
        )

        session_result.add_item_analysis_result(item_result)

        # Act
        high_conf_improvements = session_result.get_high_confidence_improvements()

        # Assert
        assert len(high_conf_improvements) == 1
        assert high_conf_improvements[0][1].confidence == AnalysisConfidence.HIGH
        assert high_conf_improvements[0][1].original_text == "改善前"

    @pytest.mark.spec("SPEC-A31-SESSION-001")
    def test_average_analysis_score_calculation(self):
        """平均分析スコア計算テスト"""
        # Arrange
        session_result = SessionAnalysisResult.create_new("プロジェクト", 1, "manuscript.md", 5)

        session_result.start_analysis()

        # 成功結果（スコア: 8.0, 6.0, 9.0）
        scores = [8.0, 6.0, 9.0]
        for i, score in enumerate(scores):
            item_result = self._create_mock_item_result(f"A31-00{i + 1}", True, score)
            session_result.add_item_analysis_result(item_result)

        # 失敗結果（スコア計算対象外）
        failed_result = self._create_mock_item_result("A31-004", False, 0.0)
        session_result.add_item_analysis_result(failed_result)

        # Act
        average_score = session_result.get_average_analysis_score()

        # Assert
        expected_average = sum(scores) / len(scores)  # (8+6+9)/3 = 7.67
        assert abs(average_score - expected_average) < 0.01

    @pytest.mark.spec("SPEC-A31-SESSION-001")
    def test_generate_analysis_summary(self):
        """分析サマリー生成テスト"""
        # Arrange
        session_result = SessionAnalysisResult.create_new("テストプロジェクト", 4, "test_manuscript.md", 10)

        session_result.start_analysis()

        # 結果追加
        item_result = self._create_mock_item_result("A31-001", True, 8.5)
        session_result.add_item_analysis_result(item_result)
        session_result.complete_analysis()

        # Act
        summary = session_result.generate_analysis_summary()

        # Assert
        assert summary["project_name"] == "テストプロジェクト"
        assert summary["episode_number"] == 4
        assert summary["overall_status"] == "completed"
        assert summary["completion_rate"] == 0.1  # 1/10
        assert summary["success_rate"] == 1.0
        assert summary["average_score"] == 8.5
        assert "analysis_id" in summary
        assert "created_at" in summary

    @pytest.mark.spec("SPEC-A31-SESSION-001")
    def test_entity_equality_and_hash(self):
        """エンティティ同値性とハッシュテスト"""
        # Arrange
        result1 = SessionAnalysisResult.create_new("プロジェクト", 1, "manuscript.md", 5)

        result2 = SessionAnalysisResult.create_new("プロジェクト", 1, "manuscript.md", 5)

        # Act & Assert
        # 異なるIDを持つエンティティは等しくない
        assert result1 != result2
        assert hash(result1) != hash(result2)

        # 同じインスタンスは等しい
        assert result1 == result1
        assert hash(result1) == hash(result1)

    def _create_mock_priority_item(self, item_id: str) -> A31PriorityItem:
        """モック重点項目作成ヘルパー"""
        return A31PriorityItem(
            item_id=PriorityItemId(item_id),
            content="テスト項目内容",
            phase=A31CheckPhase.STRUCTURE_CHECK,
            category=A31EvaluationCategory.CONTENT_BALANCE,
            priority_score=0.8,
        )

    def _create_mock_item_result(self, item_id: str, is_successful: bool, score: float) -> ItemAnalysisResult:
        """モック項目分析結果作成ヘルパー"""
        priority_item = self._create_mock_priority_item(item_id)

        return ItemAnalysisResult(
            priority_item=priority_item,
            analysis_score=score,
            status=AnalysisStatus.COMPLETED if is_successful else AnalysisStatus.FAILED,
            confidence=AnalysisConfidence.HIGH if is_successful else AnalysisConfidence.LOW,
            improvements=[],
            issues_found=[] if is_successful else ["テストエラー"],
            execution_time=1.0,
            error_message=None if is_successful else "テストエラー",
        )
