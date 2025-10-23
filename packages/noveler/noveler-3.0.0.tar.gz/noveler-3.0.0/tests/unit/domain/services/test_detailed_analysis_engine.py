#!/usr/bin/env python3
"""DetailedAnalysisEngine ドメインサービス単体テスト

TDD Red フェーズ: 詳細分析エンジンの失敗テスト
手動Claude Code分析と同等の精度を実現する核心ロジック
"""

from unittest.mock import Mock

import pytest

from noveler.domain.entities.a31_checklist_item import A31ChecklistItem
from noveler.domain.entities.detailed_evaluation_session import DetailedEvaluationSession
from noveler.domain.services.detailed_analysis_engine import (
    AnalysisContext,
    DetailedAnalysisEngine,
    DetailedAnalysisResult,
)
from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.line_specific_feedback import IssueSeverity, IssueType


@pytest.mark.spec("SPEC-A31-DET-001")
class TestDetailedAnalysisEngine:
    """DetailedAnalysisEngine ドメインサービステスト"""

    def setup_method(self) -> None:
        """テストセットアップ"""
        self.engine = DetailedAnalysisEngine()

        # テスト用エピソード内容
        self.sample_episode = """# 第001話 始まりの物語

「やっと見つけた！」

彼女の声が森に響いた。だった。だった。

俺は振り返る。彼女の顔には安堵の表情が浮かんでいる。

「どこにいたんだ？ずっと探していたぞ」

俺の問いかけに、彼女は苦笑いを浮かべた。

「迷子になっちゃった。でも、面白いものを見つけたの」

彼女が指差す方向を見ると、古い石碑が立っている。"""

    @pytest.mark.spec("SPEC-DETAILED_ANALYSIS_ENGINE-ANALYZE_EPISODE_WITH")
    def test_analyze_episode_with_comprehensive_evaluation(self) -> None:
        """エピソードの包括的分析を実行"""
        # Given
        session = DetailedEvaluationSession.create(
            project_name="テストプロジェクト", episode_number=EpisodeNumber(1), episode_content=self.sample_episode
        )

        # A31チェックリスト項目（モック）
        checklist_items = [
            self._create_mock_checklist_item("A31-021", A31EvaluationCategory.FORMAT_CHECK),
            self._create_mock_checklist_item("A31-022", A31EvaluationCategory.CONTENT_BALANCE),
            self._create_mock_checklist_item("A31-023", A31EvaluationCategory.STYLE_CONSISTENCY),
        ]

        context = AnalysisContext.create(
            project_name="テストプロジェクト",
            episode_number=1,
            target_categories=[
                A31EvaluationCategory.FORMAT_CHECK,
                A31EvaluationCategory.CONTENT_BALANCE,
                A31EvaluationCategory.STYLE_CONSISTENCY,
            ],
        )

        # When
        result = self.engine.analyze_episode_detailed(session=session, checklist_items=checklist_items, context=context)

        # Then
        assert isinstance(result, DetailedAnalysisResult)
        assert result.overall_score > 0
        assert len(result.category_results) == 3
        assert len(result.line_feedbacks) > 0  # 問題行が検出される
        assert result.session_id == session.session_id

    @pytest.mark.spec("SPEC-DETAILED_ANALYSIS_ENGINE-DETECT_STYLE_MONOTON")
    def test_detect_style_monotony_issues(self) -> None:
        """文体単調問題を検出"""
        # Given - 「だった」の連続使用
        monotonous_content = "彼は走った。だった。だった。だった。"

        DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content=monotonous_content
        )

        context = AnalysisContext.create(
            project_name="テスト", episode_number=1, target_categories=[A31EvaluationCategory.STYLE_CONSISTENCY]
        )

        # When
        result = self.engine._analyze_style_consistency(content=monotonous_content, context=context)

        # Then
        assert result.score < 80.0  # 低スコア
        assert len(result.issues_found) > 0
        assert "文末単調" in " ".join(result.issues_found)
        assert len(result.suggestions) > 0

    @pytest.mark.spec("SPEC-DETAILED_ANALYSIS_ENGINE-ANALYZE_CONTENT_BALA")
    def test_analyze_content_balance_dialogue_vs_narrative(self) -> None:
        """会話と地の文のバランス分析"""
        # Given - 会話偏重コンテンツ
        dialogue_heavy_content = """
「こんにちは」
「元気？」
「うん、元気だよ」
「それは良かった」
「ありがとう」
"""

        DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content=dialogue_heavy_content
        )

        context = AnalysisContext.create(
            project_name="テスト", episode_number=1, target_categories=[A31EvaluationCategory.CONTENT_BALANCE]
        )

        # When
        result = self.engine._analyze_content_balance(content=dialogue_heavy_content, context=context)

        # Then
        assert result.score < 75.0  # バランス不良による低スコア
        assert any("バランス" in issue for issue in result.issues_found)
        assert any("地の文" in suggestion for suggestion in result.suggestions)

    @pytest.mark.spec("SPEC-DETAILED_ANALYSIS_ENGINE-GENERATE_LINE_SPECIF")
    def test_generate_line_specific_feedback_with_context(self) -> None:
        """行別フィードバックをコンテキスト付きで生成"""
        # Given
        lines = self.sample_episode.split("\n")
        problematic_line_index = 4  # "だった。だった。だった。"

        # When
        feedback = self.engine._generate_line_feedback(
            line_content=lines[problematic_line_index],
            line_number=problematic_line_index + 1,
            context_lines=lines[max(0, problematic_line_index - 2) : problematic_line_index + 3],
            issue_context={"category": A31EvaluationCategory.STYLE_CONSISTENCY},
        )

        # Then
        assert feedback.line_number == problematic_line_index + 1
        assert feedback.issue_type == IssueType.STYLE_MONOTONY
        assert feedback.severity in [IssueSeverity.MAJOR, IssueSeverity.MINOR]
        assert "だった" in feedback.original_text
        assert len(feedback.context_lines) > 0

    @pytest.mark.spec("SPEC-DETAILED_ANALYSIS_ENGINE-CALCULATE_CONFIDENCE")
    def test_calculate_confidence_based_on_analysis_depth(self) -> None:
        """分析深度に基づく信頼度計算"""
        # Given
        session = DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content=self.sample_episode
        )

        # 複数カテゴリでの詳細分析
        comprehensive_context = AnalysisContext.create(
            project_name="テスト",
            episode_number=1,
            target_categories=list(A31EvaluationCategory),  # 全カテゴリ
        )

        checklist_items = [
            self._create_mock_checklist_item(f"A31-{i:03d}", category)
            for i, category in enumerate(A31EvaluationCategory, 1)
        ]

        # When
        result = self.engine.analyze_episode_detailed(
            session=session, checklist_items=checklist_items, context=comprehensive_context
        )

        # Then
        assert result.confidence_score > 0.7  # 包括的分析による高信頼度
        assert all(cr.confidence_score is not None for cr in result.category_results)

    @pytest.mark.spec("SPEC-DETAILED_ANALYSIS_ENGINE-PRIORITIZE_ISSUES_BY")
    def test_prioritize_issues_by_severity_and_impact(self) -> None:
        """重要度と影響度による問題優先順位付け"""
        # Given
        mixed_issues_content = """
# 第001話 テスト

だった。だった。だった。だった。だった。

「こんにちは」「元気？」「うん」「そう」「うん」

彼は走った。彼は歩いた。彼は止まった。
"""

        DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content=mixed_issues_content
        )

        context = AnalysisContext.create(
            project_name="テスト", episode_number=1, target_categories=[A31EvaluationCategory.STYLE_CONSISTENCY]
        )

        # When
        result = self.engine._analyze_style_consistency(content=mixed_issues_content, context=context)

        priority_issues = result.get_priority_issues()

        # Then
        assert len(priority_issues) > 0
        # 重要度が高い問題が最初に来る
        first_issue = priority_issues[0]
        assert any(keyword in first_issue for keyword in ["だった", "単調", "反復"])

    @pytest.mark.spec("SPEC-DETAILED_ANALYSIS_ENGINE-GENERATE_ACTIONABLE_")
    def test_generate_actionable_improvement_suggestions(self) -> None:
        """実行可能な改善提案を生成"""
        # Given
        DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content="だった。だった。だった。"
        )

        context = AnalysisContext.create(
            project_name="テスト", episode_number=1, target_categories=[A31EvaluationCategory.STYLE_CONSISTENCY]
        )

        # When
        result = self.engine._analyze_style_consistency(content="だった。だった。だった。", context=context)

        # Then
        assert result.has_actionable_suggestions()
        suggestions = result.suggestions
        assert len(suggestions) > 0
        # 具体的な修正案が含まれる
        assert any("バリエーション" in s or "変化" in s for s in suggestions)

    @pytest.mark.spec("SPEC-DETAILED_ANALYSIS_ENGINE-HANDLE_EMPTY_OR_MINI")
    def test_handle_empty_or_minimal_content_gracefully(self) -> None:
        """空または最小限のコンテンツを適切に処理"""
        # Given
        minimal_content = "短い。"

        session = DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content=minimal_content
        )

        context = AnalysisContext.create(
            project_name="テスト", episode_number=1, target_categories=[A31EvaluationCategory.CONTENT_BALANCE]
        )

        checklist_items = [self._create_mock_checklist_item("A31-001", A31EvaluationCategory.CONTENT_BALANCE)]

        # When
        result = self.engine.analyze_episode_detailed(session=session, checklist_items=checklist_items, context=context)

        # Then
        assert result is not None
        assert result.overall_score >= 0
        assert len(result.category_results) > 0
        # 最小コンテンツに対する適切なフィードバック
        balance_result = result.category_results[0]
        assert "短い" in " ".join(balance_result.issues_found) or "不足" in " ".join(balance_result.issues_found)

    @pytest.mark.spec("SPEC-DETAILED_ANALYSIS_ENGINE-INTEGRATION_WITH_EXI")
    def test_integration_with_existing_a31_evaluation_format(self) -> None:
        """既存A31評価フォーマットとの統合"""
        # Given
        session = DetailedEvaluationSession.create(
            project_name="テスト", episode_number=EpisodeNumber(1), episode_content=self.sample_episode
        )

        # 既存A31チェックリストアイテムと互換性確認
        a31_items = [
            self._create_mock_checklist_item("A31-021", A31EvaluationCategory.FORMAT_CHECK),
            self._create_mock_checklist_item("A31-025", A31EvaluationCategory.STYLE_CONSISTENCY),
        ]

        context = AnalysisContext.create(
            project_name="テスト",
            episode_number=1,
            target_categories=[A31EvaluationCategory.FORMAT_CHECK, A31EvaluationCategory.STYLE_CONSISTENCY],
        )

        # When
        result = self.engine.analyze_episode_detailed(session=session, checklist_items=a31_items, context=context)

        # Then
        assert result.is_compatible_with_a31_format()
        summary = result.to_a31_compatible_summary()
        assert "A31-021" in summary["evaluated_items"]
        assert "A31-025" in summary["evaluated_items"]
        assert all(score >= 0 for score in summary["category_scores"].values())

    def _create_mock_checklist_item(self, item_id: str, category: A31EvaluationCategory) -> A31ChecklistItem:
        """モックA31チェックリストアイテムを作成"""
        mock_item = Mock(spec=A31ChecklistItem)
        mock_item.item_id = item_id
        mock_item.category = category
        mock_item.title = f"Test Item {item_id}"
        mock_item.required = True
        mock_item.threshold = Mock()
        mock_item.threshold.value = 80.0
        return mock_item
