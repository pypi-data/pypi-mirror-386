"""前話情報抽出×動的プロンプト生成統合テスト"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import pytest

from noveler.application.use_cases.previous_episode_analysis_use_case import (
    EnhancedPromptGenerationRequest,
    PreviousEpisodeAnalysisRequest,
    PreviousEpisodeAnalysisUseCase,
)
from noveler.domain.entities.chapter_plot import ChapterPlot
from noveler.domain.entities.previous_episode_context import (
    CharacterState,
    PreviousEpisodeContext,
    StoryProgressionState,
    TechnicalLearningState,
)
from noveler.domain.services.contextual_inference_engine import ContextualInferenceEngine
from noveler.domain.services.enhanced_staged_prompt_generation_service import EnhancedStagedPromptGenerationService
from noveler.domain.services.previous_episode_extraction_service import PreviousEpisodeExtractionService
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.presentation.shared.shared_utilities import get_common_path_service


@pytest.mark.spec("SPEC-ENHANCED-001")
class TestEnhancedPreviousEpisodeIntegration:
    """前話情報抽出と動的プロンプト生成の統合テスト"""

    def setup_method(self):
        """テスト前準備"""
        get_common_path_service()
        self.use_case = PreviousEpisodeAnalysisUseCase()
        self.temp_dir = TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

        # テスト用ディレクトリ構造作成
        self._setup_test_directory_structure()

    def teardown_method(self):
        """テスト後処理"""
        self.temp_dir.cleanup()

    def _setup_test_directory_structure(self) -> None:
        """テスト用ディレクトリ構造セットアップ"""
        # 原稿ディレクトリ作成
        path_service = get_common_path_service()
        manuscript_dir = self.project_root / str(path_service.get_manuscript_dir())
        manuscript_dir.mkdir(parents=True, exist_ok=True)

        # プロット関連ディレクトリ作成
        plot_dir = self.project_root / str(path_service.get_plots_dir()) / "章別プロット"
        plot_dir.mkdir(parents=True, exist_ok=True)

        # テスト用原稿ファイル作成
        self._create_test_manuscript(manuscript_dir)

    def _create_test_manuscript(self, manuscript_dir: Path) -> None:
        """テスト用原稿ファイル作成"""
        manuscript_content = """# 第006話 ペアプログラミング基礎

## 導入部
直人は朝から緊張していた。今日はあすかと一緒にペアプログラミングの練習をする日だった。

「おはよう、直人！」
あすかが教室に入ってきた。彼女はいつも通り元気だった。

## 展開部
実習室で、先生がペアプログラミングの基礎を説明し始めた。

「ペアプログラミングとは、2人で1つのプログラムを作成する手法です」

直人はメモを取りながら真面目に聞いていた。あすかは既に理解しているようで、時々頷いていた。

実際にペアプログラミングを始めてみると、思っていたより難しかった。

「ここはどうする？」
「こうしてみよう」

二人は協力して魔法のプログラムを作成した。シンクロ率が徐々に向上していく。

## クライマックス
複雑なアルゴリズムの実装で困難に直面した。

「うまくいかないな」
直人は困っていた。

「大丈夫、一緒に考えよう」
あすかが励ました。

二人で協力することで、ついに難しい問題を解決できた。

## 解決部
協調魔法の基礎を理解し、シンクロ率も大幅に向上した。

「今日は本当に勉強になった」
直人は満足していた。

「次回はもっと高度なことにチャレンジしよう」
あすかが提案した。

次回の協力が楽しみになっていた。まだペアプログラミングの基礎段階だが、将来的にはより高度な協調開発を目指したい。
"""
        manuscript_file = manuscript_dir / "第006話_ペアプログラミング基礎.md"
        manuscript_file.write_text(manuscript_content, encoding="utf-8")

    @pytest.mark.asyncio
    async def test_previous_episode_analysis_comprehensive(self):
        """前話情報分析の包括的テスト"""
        # Given: 第7話の前話分析リクエスト
        request = PreviousEpisodeAnalysisRequest(
            episode_number=7,
            project_root=self.project_root,
            analysis_depth="comprehensive",
            include_inference_details=True,
        )

        # When: 前話情報分析実行
        response = await self.use_case.analyze_previous_episode(request)

        # Then: 分析成功と詳細情報取得確認
        assert response.success, f"Analysis failed: {response.error_message}"
        assert response.episode_number == 7
        assert response.previous_context is not None
        assert response.dynamic_context is not None

        # 前話コンテキストの詳細確認
        prev_context = response.previous_context
        assert prev_context.current_episode_number.value == 7
        assert prev_context.previous_episode_number.value == 6
        assert prev_context.has_sufficient_context()

        # キャラクター状態抽出確認
        assert len(prev_context.character_states) > 0
        assert "直人" in prev_context.character_states
        assert "あすか" in prev_context.character_states

        # 直人の状態確認
        naoto_state = prev_context.get_character_state("直人")
        assert naoto_state is not None
        assert naoto_state.emotional_state != "平静"  # 何らかの感情が抽出されているはず

        # あすかの状態確認
        asuka_state = prev_context.get_character_state("あすか")
        assert asuka_state is not None

        # ストーリー進行状況確認
        story_prog = prev_context.story_progression
        assert story_prog.story_momentum in ["low", "normal", "high", "climactic"]

        # 技術学習状況確認
        tech_learning = prev_context.technical_learning
        assert tech_learning.current_learning_focus != ""  # 学習フォーカス抽出確認

        # 動的コンテキストの確認
        dynamic_context = response.dynamic_context
        assert dynamic_context.story_phase in ["introduction", "development", "climax", "resolution"]
        assert dynamic_context.character_growth_stage in ["beginner", "learning", "practicing", "competent", "expert"]
        assert dynamic_context.technical_complexity_level in ["basic", "intermediate", "advanced", "expert"]

        # 推論結果確認
        assert len(dynamic_context.inferences) > 0
        high_confidence_inferences = dynamic_context.get_high_confidence_inferences()
        assert len(high_confidence_inferences) >= 0  # 0以上の高信頼度推論

        # 分析サマリー確認
        assert "前話情報分析結果" in response.analysis_summary
        assert "動的推論結果" in response.analysis_summary

        # 推論詳細確認（リクエストで要求されている）
        assert len(response.inference_insights) >= 0

        # 推奨事項確認
        assert len(response.recommendations) > 0

    @pytest.mark.asyncio
    async def test_enhanced_prompt_generation_with_previous_context(self):
        """前話コンテキストを活用した高度化プロンプト生成テスト"""
        # Given: 章別プロット情報準備
        chapter_plot = self._create_test_chapter_plot()

        # Given: 高度化プロンプト生成リクエスト
        request = EnhancedPromptGenerationRequest(
            episode_number=7,
            project_root=self.project_root,
            chapter_plot=chapter_plot,
            target_stage=3,  # シーン肉付け段階
            base_context={"project_name": "test_novel"},
        )

        # When: 高度化プロンプト生成実行
        response = await self.use_case.generate_enhanced_prompt(request)

        # Then: 生成成功と高度化機能確認
        assert response.success, f"Enhanced prompt generation failed: {response.error_message}"
        assert response.episode_number == 7
        assert response.target_stage == 3
        assert response.generated_prompt != ""
        assert response.quality_score > 0.0

        # 前話コンテキスト活用確認
        assert response.previous_context_used  # 前話情報が活用されている

        # 動的調整適用確認
        assert response.dynamic_adjustments_applied  # 動的調整が適用されている

        # 高度化詳細情報確認
        enhancement_details = response.enhancement_details
        assert "story_phase" in enhancement_details
        assert "character_growth_stage" in enhancement_details
        assert "technical_complexity_level" in enhancement_details
        assert enhancement_details["emotional_focus_count"] >= 0
        assert enhancement_details["adaptive_elements_count"] >= 0

        # 生成されたプロンプトの内容確認
        generated_prompt = response.generated_prompt
        assert "Stage 3" in generated_prompt  # 段階情報が含まれている

        # 適応的調整の確認（プロンプトに特定の指示が含まれているか）
        if response.enhancement_details.get("emotional_focus_count", 0) > 2:
            # 多数の感情フォーカス領域がある場合、感情描写に関する指示があるはず
            assert any(keyword in generated_prompt.lower() for keyword in ["感情", "emotional", "描写", "内面"])

    @pytest.mark.spec("SPEC-ENHANCED_PREVIOUS_EPISODE_INTEGRATION-PREVIOUS_EPISODE_EXT")
    def test_previous_episode_extraction_service_integration(self):
        """前話情報抽出サービスの統合テスト"""
        # Given: エピソード番号
        episode_number = EpisodeNumber(7)

        # Given: 前話情報抽出サービス
        extraction_service = PreviousEpisodeExtractionService()

        # When: 前話情報抽出実行
        context = extraction_service.extract_previous_episode_context(episode_number, self.project_root)

        # Then: 抽出結果確認
        assert context is not None
        assert context.current_episode_number.value == 7
        assert context.previous_episode_number.value == 6
        assert context.source_manuscript_path is not None
        assert context.source_manuscript_path.exists()

        # キャラクター抽出確認
        assert len(context.character_states) >= 2  # 直人とあすか

        # 技術要素抽出確認
        tech_learning = context.technical_learning
        assert tech_learning.current_learning_focus != ""

        # 感情の流れ抽出確認
        assert len(context.emotional_flow) >= 0

        # YAML変換確認
        yaml_dict = context.to_yaml_dict()
        assert "current_episode_number" in yaml_dict
        assert "character_states" in yaml_dict
        assert "story_progression" in yaml_dict
        assert "technical_learning" in yaml_dict

    @pytest.mark.spec("SPEC-ENHANCED_PREVIOUS_EPISODE_INTEGRATION-CONTEXTUAL_INFERENCE")
    def test_contextual_inference_engine_integration(self):
        """コンテキスト推論エンジンの統合テスト"""
        # Given: エピソード番号と前話コンテキスト
        episode_number = EpisodeNumber(7)

        # 前話コンテキストのモック作成
        previous_context = self._create_mock_previous_context(episode_number)

        # Given: 推論エンジン
        inference_engine = ContextualInferenceEngine()

        # When: 動的コンテキスト生成
        dynamic_context = inference_engine.generate_dynamic_context(
            episode_number,
            None,  # 章別プロット無し
            previous_context,
        )

        # Then: 推論結果確認
        assert dynamic_context is not None
        assert dynamic_context.episode_number.value == 7
        assert dynamic_context.story_phase in ["introduction", "development", "climax", "resolution"]
        assert dynamic_context.character_growth_stage in ["beginner", "learning", "practicing", "competent", "expert"]
        assert dynamic_context.technical_complexity_level in ["basic", "intermediate", "advanced", "expert"]

        # 推論詳細確認
        assert len(dynamic_context.inferences) >= 4  # 少なくとも4つの推論（フェーズ、成長、複雑度、感情、適応）

        # 高信頼度推論確認
        high_confidence = dynamic_context.get_high_confidence_inferences()
        assert len(high_confidence) >= 0

        # YAML変換確認
        yaml_dict = dynamic_context.to_yaml_dict()
        assert "episode_number" in yaml_dict
        assert "story_phase" in yaml_dict
        assert "character_growth_stage" in yaml_dict
        assert "inferences" in yaml_dict

    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """エラーハンドリング統合テスト"""
        # Given: 存在しないプロジェクトパス
        invalid_path = Path("/nonexistent/path")

        # When: 無効なパスでの前話分析
        request = PreviousEpisodeAnalysisRequest(episode_number=7, project_root=invalid_path)

        response = await self.use_case.analyze_previous_episode(request)

        # Then: 適切なエラーハンドリング確認
        assert not response.success
        assert response.error_message is not None

        # When: 無効なパスでの高度化プロンプト生成
        enhanced_request = EnhancedPromptGenerationRequest(episode_number=7, project_root=invalid_path)

        enhanced_response = await self.use_case.generate_enhanced_prompt(enhanced_request)

        # Then: 適切なエラーハンドリング確認
        assert not enhanced_response.success
        assert enhanced_response.error_message is not None

    @pytest.mark.asyncio
    async def test_first_episode_special_handling(self):
        """第1話特別処理テスト"""
        # Given: 第1話の分析リクエスト
        request = PreviousEpisodeAnalysisRequest(episode_number=1, project_root=self.project_root)

        # When: 第1話分析実行
        response = await self.use_case.analyze_previous_episode(request)

        # Then: 第1話特別処理確認
        assert response.success
        assert "第1話のため前話情報はありません" in response.analysis_summary
        assert len(response.recommendations) > 0
        assert any("導入" in rec or "世界観" in rec for rec in response.recommendations)

    def _create_test_chapter_plot(self) -> ChapterPlot:
        """テスト用章別プロット作成"""
        mock_plot = Mock(spec=ChapterPlot)
        mock_plot.get_episode_info.return_value = {
            "episode_number": 7,
            "title": "ペアプログラミング応用編",
            "summary": "より高度な協調開発に挑戦",
            "estimated_length": 6500,
            "key_themes": ["協力", "技術向上", "挑戦"],
            "character_focus": ["直人", "あすか"],
            "technical_elements": ["ペアプログラミング", "協調開発", "高度アルゴリズム"],
        }
        return mock_plot

    def _create_mock_previous_context(self, episode_number: EpisodeNumber) -> PreviousEpisodeContext:
        """モック前話コンテキスト作成"""
        context = PreviousEpisodeContext(episode_number)

        # キャラクター状態追加
        naoto_state = CharacterState(
            character_name="直人",
            emotional_state="成長の喜び",
            current_relationships={"あすか": "協力的"},
            character_development_stage="実践段階",
            key_attributes=["真面目", "協調性"],
        )

        context.add_character_state(naoto_state)

        asuka_state = CharacterState(
            character_name="あすか",
            emotional_state="満足",
            current_relationships={"直人": "友好的"},
            character_development_stage="指導段階",
            key_attributes=["積極的", "協調性"],
        )

        context.add_character_state(asuka_state)

        # ストーリー進行状況設定
        story_progression = StoryProgressionState(
            main_plot_developments=["ペアプログラミング基礎習得", "協調魔法実践"],
            subplot_progressions={"技術学習": "進展", "人間関係": "進展"},
            resolved_conflicts=["初期の緊張"],
            active_foreshadowing=["次回はより高度な挑戦"],
            story_momentum="normal",
        )

        context.update_story_progression(story_progression)

        # 技術学習状況設定
        tech_learning = TechnicalLearningState(
            mastered_concepts=["ペアプログラミング基礎", "協調魔法入門"],
            current_learning_focus="ペアプログラミング",
            difficulty_level="intermediate",
            practical_applications=["魔法プログラム作成", "シンクロ率向上"],
            next_learning_targets=["高度な協調開発"],
        )

        context.update_technical_learning(tech_learning)

        # 感情の流れ追加
        context.add_emotional_flow_element("緊張 → 理解")
        context.add_emotional_flow_element("困惑 → 協力")
        context.add_emotional_flow_element("達成感 → 満足")

        # 未解決要素追加
        context.add_unresolved_element("より高度なアルゴリズム習得")

        # シーン継続性追加
        context.add_scene_continuity_note("前話の主要場所: 実習室で")
        context.add_scene_continuity_note("継続要素: 次回協力予定")

        return context


@pytest.mark.spec("SPEC-ENHANCED-002")
class TestEnhancedStagedPromptGenerationService:
    """高度化段階的プロンプト生成サービステスト"""

    def setup_method(self):
        """テスト前準備"""
        self.temp_dir = TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def teardown_method(self):
        """テスト後処理"""
        self.temp_dir.cleanup()

    @pytest.mark.spec("SPEC-ENHANCED_PREVIOUS_EPISODE_INTEGRATION-ENHANCED_SERVICE_INI")
    def test_enhanced_service_initialization(self):
        """高度化サービス初期化テスト"""
        # Given: モックリポジトリとバリデータ
        mock_template_repo = Mock()
        mock_quality_validator = Mock()

        # When: 高度化サービス作成
        service = EnhancedStagedPromptGenerationService(mock_template_repo, mock_quality_validator, self.project_root)

        # Then: 正常初期化確認
        assert service is not None
        assert service._project_root == self.project_root
        assert service._previous_extractor is not None
        assert service._inference_engine is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
