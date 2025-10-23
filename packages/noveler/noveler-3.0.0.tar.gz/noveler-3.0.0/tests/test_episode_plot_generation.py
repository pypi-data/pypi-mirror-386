#!/usr/bin/env python3

"""エピソード別プロット生成機能テスト

A28話別プロット拡張機能のテストスイート（旧a28_plot_enhancements）
SPEC-A28-001準拠の統合テストスイート
"""

import pytest
from dataclasses import dataclass
from unittest.mock import Mock, patch

from noveler.domain.services.plot_generation_functional_core import (
    PlotGenerationCore,
    PlotGenerationInput,
    PlotGenerationOutput,
    ForeshadowingElement,
    ForeshadowingStatus,
    SceneData,
    ImportanceRank,
    EmotionTechFusion,
    EnhancedPlotAnalysis,
)


class TestA28PlotEnhancements:
    """A28プロット拡張機能テストクラス

    7つの拡張機能の統合テスト
    - 伏線追跡システム
    - シーン粒度管理
    - 感情×技術融合
    - ステージ間連携強化
    - 文字数配分ガイドライン
    - 読者反応予測
    - 視点一貫性チェック
    """

    @pytest.fixture
    def sample_foreshadowing_elements(self):
        """サンプル伏線要素"""
        return [
            ForeshadowingElement(
                foreshadow_id="FS001",
                element="主人公の過去の傷跡についての言及",
                category="character_background",
                status=ForeshadowingStatus.PLANTED,
                planted_episode=1,
                resolution_episode=5,
                importance_level=4,
                dependency=[],
                placement_scene="scene_001",
                reader_clue_level="subtle",
            ),
            ForeshadowingElement(
                foreshadow_id="FS002",
                element="古い魔法書に記された禁術の予兆",
                category="world_building",
                status=ForeshadowingStatus.PLANNED,
                planted_episode=1,
                resolution_episode=8,
                importance_level=5,
                dependency=["FS001"],
                placement_scene="scene_002",
                reader_clue_level="moderate",
            ),
        ]

    @pytest.fixture
    def sample_scene_structure(self):
        """サンプルシーン構造"""
        return [
            SceneData(
                scene_id="scene_001",
                title="導入・状況設定",
                importance_rank=ImportanceRank.S,
                estimated_words=800,
                percentage=13.3,
                story_function="hook_and_setup",
                emotional_weight="medium",
                technical_complexity="low",
                reader_engagement_level="high",
            ),
            SceneData(
                scene_id="scene_002",
                title="問題発生・困難提示",
                importance_rank=ImportanceRank.A,
                estimated_words=900,
                percentage=15.0,
                story_function="plot_advancement",
                emotional_weight="high",
                technical_complexity="medium",
                reader_engagement_level="high",
            ),
            SceneData(
                scene_id="scene_003",
                title="技術的課題への挑戦",
                importance_rank=ImportanceRank.S,
                estimated_words=1200,
                percentage=20.0,
                story_function="character_development",
                emotional_weight="high",
                technical_complexity="high",
                reader_engagement_level="high",
            ),
        ]

    @pytest.fixture
    def sample_emotion_tech_fusions(self):
        """サンプル感情×技術融合"""
        return [
            EmotionTechFusion(
                timing="第二幕クライマックス",
                scene_reference="scene_003",
                emotion_type="絶望から希望へ",
                emotion_intensity="high",
                tech_concept="再帰アルゴリズムの理解",
                tech_complexity="intermediate",
                synergy_effect="技術的突破が感情的カタルシスと重なる",
                synergy_intensity="maximum",
            ),
        ]

    @pytest.fixture
    def sample_plot_input(self, sample_foreshadowing_elements, sample_scene_structure, sample_emotion_tech_fusions):
        """サンプルプロット入力"""
        return PlotGenerationInput(
            episode_number=1,
            chapter_info={
                "title": "第001話_デバッグ魔法師の覚醒",
                "summary": "主人公がデバッグ魔法を習得する重要なエピソード",
            },
            previous_episodes=[],
            quality_threshold=0.8,
            enable_enhancements=True,
            foreshadowing_elements=sample_foreshadowing_elements,
            scene_structure=sample_scene_structure,
            emotion_tech_fusions=sample_emotion_tech_fusions,
            target_word_count=6000,
            viewpoint_character="主人公",
        )

    def test_input_validation_success(self, sample_plot_input):
        """正常な入力データの検証テスト"""
        is_valid, error_msg = PlotGenerationCore.validate_input(sample_plot_input)

        assert is_valid is True
        assert error_msg is None

    def test_input_validation_duplicate_foreshadowing_ids(self, sample_plot_input):
        """伏線ID重複エラーテスト"""
        # 重複するIDを追加
        duplicate_element = ForeshadowingElement(
            foreshadow_id="FS001",  # 重複ID
            element="重複する伏線",
            category="plot_device",
            status=ForeshadowingStatus.PLANNED,
            planted_episode=1,
            resolution_episode=3,
            importance_level=2,
            dependency=[],
            placement_scene="scene_001",
            reader_clue_level="obvious",
        )
        sample_plot_input.foreshadowing_elements.append(duplicate_element)

        is_valid, error_msg = PlotGenerationCore.validate_input(sample_plot_input)

        assert is_valid is False
        assert "Duplicate foreshadowing IDs found" in error_msg

    def test_input_validation_invalid_foreshadowing_id_format(self, sample_plot_input):
        """伏線ID形式エラーテスト"""
        # 不正な形式のIDを設定
        sample_plot_input.foreshadowing_elements[0].foreshadow_id = "INVALID_ID"

        is_valid, error_msg = PlotGenerationCore.validate_input(sample_plot_input)

        assert is_valid is False
        assert "Invalid foreshadowing ID format" in error_msg

    def test_input_validation_three_act_ratios_sum_error(self, sample_plot_input):
        """三幕構成比率合計エラーテスト"""
        # 比率の合計が1.0でない場合
        sample_plot_input.three_act_ratios = (0.3, 0.5, 0.3)  # 合計1.1

        is_valid, error_msg = PlotGenerationCore.validate_input(sample_plot_input)

        assert is_valid is False
        assert "Three-act ratios must sum to 1.0" in error_msg

    def test_foreshadowing_consistency_analysis(self, sample_foreshadowing_elements):
        """伏線一貫性分析テスト"""
        score = PlotGenerationCore._analyze_foreshadowing_consistency(sample_foreshadowing_elements)

        # スコアが0.0-1.0の範囲内であることを確認
        assert 0.0 <= score <= 1.0

        # 循環依存がない場合、高いスコアが期待される
        assert score > 0.5

    def test_foreshadowing_consistency_with_circular_dependency(self):
        """循環依存がある伏線の一貫性分析テスト"""
        circular_elements = [
            ForeshadowingElement(
                foreshadow_id="FS001",
                element="要素1",
                category="plot_device",
                status=ForeshadowingStatus.PLANNED,
                planted_episode=1,
                resolution_episode=3,
                importance_level=3,
                dependency=["FS001"],  # 自己参照
                placement_scene="scene_001",
                reader_clue_level="moderate",
            ),
        ]

        score = PlotGenerationCore._analyze_foreshadowing_consistency(circular_elements)

        # 循環依存があるため、スコアが下がることを確認
        assert score < 0.9

    def test_scene_balance_analysis(self, sample_scene_structure):
        """シーンバランス分析テスト"""
        target_word_count = 6000
        score = PlotGenerationCore._analyze_scene_balance(sample_scene_structure, target_word_count)

        # スコアが0.0-1.0の範囲内であることを確認
        assert 0.0 <= score <= 1.0

    def test_emotion_tech_fusion_analysis(self, sample_emotion_tech_fusions):
        """感情×技術融合分析テスト"""
        score = PlotGenerationCore._analyze_emotion_tech_fusion(sample_emotion_tech_fusions)

        # スコアが0.0-1.0の範囲内であることを確認
        assert 0.0 <= score <= 1.0

        # maximum強度の融合があるため、高いスコアが期待される
        assert score >= 0.8

    def test_word_allocation_analysis(self):
        """文字数配分分析テスト"""
        three_act_ratios = (0.25, 0.50, 0.25)
        scene_structure = [
            SceneData(
                scene_id="scene_001",
                title="テストシーン",
                importance_rank=ImportanceRank.A,
                estimated_words=1500,
                percentage=25.0,
                story_function="setup",
                emotional_weight="medium",
                technical_complexity="low",
                reader_engagement_level="medium",
            ),
        ]

        score = PlotGenerationCore._analyze_word_allocation(three_act_ratios, scene_structure)

        # スコアが0.0-1.0の範囲内であることを確認
        assert 0.0 <= score <= 1.0

    def test_reader_engagement_prediction(self, sample_scene_structure, sample_emotion_tech_fusions):
        """読者エンゲージメント予測テスト"""
        score = PlotGenerationCore._predict_reader_engagement(sample_scene_structure, sample_emotion_tech_fusions)

        # スコアが0.0-1.0の範囲内であることを確認
        assert 0.0 <= score <= 1.0

        # 高エンゲージメントシーンが多いため、高いスコアが期待される
        assert score > 0.6

    def test_viewpoint_consistency_check(self):
        """視点一貫性チェックテスト"""
        # 視点キャラクターが設定されている場合
        score_with_character = PlotGenerationCore._check_viewpoint_consistency("主人公")
        assert score_with_character >= 0.8

        # 視点キャラクターが設定されていない場合
        score_without_character = PlotGenerationCore._check_viewpoint_consistency("")
        assert score_without_character < 0.8

    def test_word_allocation_calculation(self):
        """文字数配分計算テスト"""
        three_act_ratios = (0.25, 0.50, 0.25)
        target_word_count = 6000

        allocation = PlotGenerationCore._calculate_word_allocation(three_act_ratios, target_word_count)

        assert allocation["act_1"] == 1500
        assert allocation["act_2"] == 3000
        assert allocation["act_3"] == 1500
        assert sum(allocation.values()) == target_word_count

    def test_reader_predictions_generation(self, sample_scene_structure):
        """読者反応予測生成テスト"""
        predictions = PlotGenerationCore._generate_reader_predictions(sample_scene_structure)

        # すべてのシーンに予測が生成されることを確認
        assert len(predictions) == len(sample_scene_structure)

        # 高エンゲージメントシーンには適切な予測が含まれることを確認
        high_engagement_scenes = [s for s in sample_scene_structure if s.reader_engagement_level == "high"]
        for scene in high_engagement_scenes:
            assert scene.scene_id in predictions
            assert "高い関心" in predictions[scene.scene_id]

    def test_improvement_suggestions_generation(self):
        """改善提案生成テスト"""
        # 低スコアのテスト分析結果
        low_score_analysis = EnhancedPlotAnalysis(
            foreshadowing_consistency_score=0.6,
            scene_balance_score=0.5,
            emotion_tech_integration_score=0.4,
            stage_interconnection_score=0.8,
            word_allocation_score=0.6,
            reader_engagement_prediction=0.5,
            viewpoint_consistency_score=0.9,
            overall_enhancement_score=0.6,
        )

        suggestions = PlotGenerationCore._generate_improvement_suggestions(low_score_analysis)

        # 低スコア項目に対する提案が生成されることを確認
        assert len(suggestions) > 0
        assert any("伏線" in suggestion for suggestion in suggestions)
        assert any("シーン" in suggestion for suggestion in suggestions)
        assert any("感情" in suggestion for suggestion in suggestions)

    def test_process_enhancements_disabled(self, sample_plot_input):
        """拡張機能無効化テスト"""
        sample_plot_input.enable_enhancements = False

        analysis, processed_data = PlotGenerationCore.process_enhancements(sample_plot_input)

        # 拡張機能が無効の場合、すべてのスコアが0.0であることを確認
        assert analysis.overall_enhancement_score == 0.0
        assert analysis.foreshadowing_consistency_score == 0.0
        assert len(processed_data) == 0

    def test_process_enhancements_enabled(self, sample_plot_input):
        """拡張機能有効化テスト"""
        analysis, processed_data = PlotGenerationCore.process_enhancements(sample_plot_input)

        # 拡張機能が有効の場合、適切なスコアが計算されることを確認
        assert 0.0 <= analysis.overall_enhancement_score <= 1.0
        assert 0.0 <= analysis.foreshadowing_consistency_score <= 1.0
        assert 0.0 <= analysis.scene_balance_score <= 1.0
        assert 0.0 <= analysis.emotion_tech_integration_score <= 1.0

        # 処理済みデータが生成されることを確認
        assert "word_allocation" in processed_data
        assert "reader_predictions" in processed_data
        assert "improvement_suggestions" in processed_data

    def test_transform_plot_success(self, sample_plot_input):
        """プロット変換成功テスト"""
        result = PlotGenerationCore.transform_plot(sample_plot_input)

        assert result.success is True
        assert result.episode_number == sample_plot_input.episode_number
        assert result.quality_score >= sample_plot_input.quality_threshold
        assert result.enhancement_analysis is not None
        assert len(result.validated_foreshadowing) > 0
        assert len(result.optimized_scene_structure) > 0
        assert len(result.improvement_suggestions) >= 0

    def test_transform_plot_quality_threshold_failure(self, sample_plot_input):
        """品質閾値未達テスト"""
        sample_plot_input.quality_threshold = 0.95  # 非常に高い閾値

        result = PlotGenerationCore.transform_plot(sample_plot_input)

        # 品質閾値を満たさない場合、失敗が返される
        assert result.success is False
        assert "below threshold" in result.error_message

    def test_transform_plot_input_validation_failure(self, sample_plot_input):
        """入力検証失敗テスト"""
        sample_plot_input.episode_number = -1  # 不正な値

        result = PlotGenerationCore.transform_plot(sample_plot_input)

        assert result.success is False
        assert "Episode number must be positive" in result.error_message

    def test_key_events_extraction_with_foreshadowing(self, sample_foreshadowing_elements):
        """伏線要素を含むキーイベント抽出テスト"""
        plot_content = "この物語には重要な伏線とクライマックスが含まれています。"

        events = PlotGenerationCore.extract_key_events(plot_content, sample_foreshadowing_elements)

        # 基本的なキーイベントが抽出されることを確認
        assert "伏線の設置" in events

        # 伏線要素からのキーイベントが追加されることを確認
        foreshadowing_events = [event for event in events if "伏線設置" in event or "伏線回収" in event]
        assert len(foreshadowing_events) > 0

    @pytest.mark.spec("SPEC-A28-001")
    def test_spec_a28_001_compliance(self, sample_plot_input):
        """SPEC-A28-001仕様準拠テスト"""
        result = PlotGenerationCore.transform_plot(sample_plot_input)

        # 仕様書で定義された7つの拡張機能が実装されていることを確認
        assert result.enhancement_analysis is not None

        # FR-001: 伏線追跡システム
        assert hasattr(result.enhancement_analysis, 'foreshadowing_consistency_score')

        # FR-002: シーン粒度管理システム
        assert hasattr(result.enhancement_analysis, 'scene_balance_score')

        # FR-003: 感情×技術融合システム
        assert hasattr(result.enhancement_analysis, 'emotion_tech_integration_score')

        # FR-004: ステージ間連携強化
        assert hasattr(result.enhancement_analysis, 'stage_interconnection_score')

        # FR-005: 文字数配分ガイドライン
        assert hasattr(result.enhancement_analysis, 'word_allocation_score')

        # FR-006: 読者反応予測システム
        assert hasattr(result.enhancement_analysis, 'reader_engagement_prediction')

        # FR-007: 視点一貫性チェック
        assert hasattr(result.enhancement_analysis, 'viewpoint_consistency_score')

        # 総合品質スコア
        assert hasattr(result.enhancement_analysis, 'overall_enhancement_score')


class TestA28IntegrationWithUseCase:
    """A28拡張機能とユースケース統合テスト"""

    @patch('noveler.application.use_cases.generate_episode_plot_use_case.PlotGenerationCore')
    def test_use_case_integration_with_a28_enhancements(self, mock_core):
        """ユースケースとA28拡張機能の統合テスト"""
        from noveler.application.use_cases.generate_episode_plot_use_case import (
            GenerateEpisodePlotUseCase,
            GenerateEpisodePlotRequest,
        )
        from pathlib import Path

        # モックの設定
        mock_output = PlotGenerationOutput(
            episode_number=1,
            plot_content="テストプロット",
            quality_score=0.85,
            key_events=["テストイベント"],
            success=True,
            enhancement_analysis=EnhancedPlotAnalysis(
                foreshadowing_consistency_score=0.9,
                scene_balance_score=0.8,
                emotion_tech_integration_score=0.85,
                stage_interconnection_score=0.8,
                word_allocation_score=0.9,
                reader_engagement_prediction=0.8,
                viewpoint_consistency_score=0.9,
                overall_enhancement_score=0.85,
            ),
        )
        mock_core.transform_plot.return_value = mock_output

        # ユースケースの依存関係をモック
        mock_chapter_repo = Mock()
        mock_claude_service = Mock()
        mock_logger = Mock()

        mock_chapter_repo.find_by_episode_number.return_value = Mock()
        mock_claude_service.generate_episode_plot.return_value = Mock(
            episode_number=1,
            title="テストエピソード",
            to_yaml_dict=Mock(return_value={"test": "data"})
        )

        use_case = GenerateEpisodePlotUseCase(
            chapter_plot_repository=mock_chapter_repo,
            claude_service=mock_claude_service,
            logger_service=mock_logger,
        )

        # リクエスト作成（A28拡張機能有効）
        request = GenerateEpisodePlotRequest(
            episode_number=1,
            project_path=Path("/tmp/test"),
            enable_a28_enhancements=True,
            foreshadowing_elements=[{
                "foreshadow_id": "FS001",
                "element": "テスト伏線",
                "status": "planned",
            }],
        )

        # ファイル保存をモック
        with patch('builtins.open', create=True), \
             patch('yaml.dump'), \
             patch('pathlib.Path.mkdir'), \
             patch.object(use_case, '_get_output_file_path', return_value=Path("/tmp/output.yaml")):

            response = use_case.execute(request)

        # A28拡張機能が正しく適用されたことを確認
        assert response.success is True
        assert response.enhancement_used is True
        assert response.enhancement_quality_score > 0
        assert response.foreshadowing_consistency_score > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
