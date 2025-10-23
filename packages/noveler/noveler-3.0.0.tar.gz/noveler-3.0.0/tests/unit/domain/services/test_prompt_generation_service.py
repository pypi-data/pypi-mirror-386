#!/usr/bin/env python3
"""
プロンプト生成サービスのユニットテスト

SPEC-PROMPT-002: プロンプト生成ドメインサービス
DDD設計に基づくプロンプト生成サービスの動作を検証する。
"""

from unittest.mock import Mock

import pytest

from noveler.domain.entities.prompt_generation import (
    A24Stage,
    ContextElement,
    ContextElementType,
    PromptGenerationSession,
)
from noveler.domain.services.prompt_generation_service import (
    PromptGenerationService,
    PromptOptimizer,
)


class TestPromptGenerationService:
    """PromptGenerationService ドメインサービスのテスト"""

    @pytest.fixture
    def mock_a24_guide_repo(self) -> Mock:
        """A24ガイドリポジトリモック"""
        repo = Mock()
        repo.get_stage_instructions.return_value = ["ステップ1: 基本情報を記入", "ステップ2: 概要を作成"]
        repo.get_validation_criteria.return_value = ["必須項目入力済み", "YAML構文チェック済み"]
        repo.get_template_structure.return_value = {
            "episode_info": {"episode_number": "int", "title": "str"},
            "synopsis": "str",
        }
        return repo

    @pytest.fixture
    def mock_context_repo(self) -> Mock:
        """プロジェクトコンテキストリポジトリモック"""
        repo = Mock()

        # 伏線要素
        foreshadowing = ContextElement(
            element_type=ContextElementType.FORESHADOWING,
            content="重要な伏線要素",
            priority=0.8,
            integration_stage=A24Stage.TECH_INTEGRATION,
            source_file="伏線管理.yaml",
        )

        repo.extract_foreshadowing_elements.return_value = [foreshadowing]

        # 重要シーン
        important_scene = ContextElement(
            element_type=ContextElementType.IMPORTANT_SCENE,
            content="クライマックスシーン",
            priority=0.9,
            integration_stage=A24Stage.SCENE_DETAIL,
            source_file="重要シーン.yaml",
        )

        repo.extract_important_scenes.return_value = [important_scene]

        # 章間連携
        connection = ContextElement(
            element_type=ContextElementType.CHAPTER_CONNECTION,
            content="前話からの継続要素",
            priority=0.6,
            integration_stage=A24Stage.SKELETON,
            source_file="章別プロット.yaml",
        )

        repo.extract_chapter_connections.return_value = [connection]

        return repo

    @pytest.fixture
    def mock_optimizer(self) -> Mock:
        """プロンプト最適化器モック"""
        optimizer = Mock(spec=PromptOptimizer)
        optimizer.optimize_for_target.return_value = "最適化されたプロンプト"
        optimizer.estimate_token_count.return_value = 1500
        return optimizer

    @pytest.fixture
    def service(
        self, mock_a24_guide_repo: Mock, mock_context_repo: Mock, mock_optimizer: Mock
    ) -> PromptGenerationService:
        """プロンプト生成サービス"""
        return PromptGenerationService(mock_a24_guide_repo, mock_context_repo, mock_optimizer)

    @pytest.fixture
    def valid_session(self) -> PromptGenerationSession:
        """有効なセッション"""
        session = PromptGenerationSession()
        session.start_generation(12, "テストプロジェクト")
        session.context_level = "基本"
        session.include_foreshadowing = True
        session.include_important_scenes = True
        return session

    @pytest.mark.spec("SPEC-PROMPT-002-001")
    def test_generate_prompt_for_episode_success(
        self,
        service: PromptGenerationService,
        valid_session: PromptGenerationSession,
        mock_context_repo: Mock,
        mock_optimizer: Mock,
    ) -> None:
        """正常なプロンプト生成テスト"""
        service.generate_prompt_for_episode(valid_session)

        # セッション状態確認
        assert valid_session.is_success()
        assert valid_session.final_prompt == "最適化されたプロンプト"
        assert valid_session.token_estimate == 1500
        assert len(valid_session.integrated_context) > 0

        # リポジトリ呼び出し確認
        mock_context_repo.extract_foreshadowing_elements.assert_called_once_with(12)
        mock_context_repo.extract_important_scenes.assert_called_once_with(12)
        mock_context_repo.extract_chapter_connections.assert_called_once_with(12)

        # 最適化器呼び出し確認
        mock_optimizer.optimize_for_target.assert_called_once()
        mock_optimizer.estimate_token_count.assert_called_once()

    @pytest.mark.spec("SPEC-PROMPT-002-002")
    def test_generate_prompt_invalid_session(self, service: PromptGenerationService) -> None:
        """無効なセッションでのプロンプト生成テスト"""
        invalid_session = PromptGenerationSession()
        # episode_number と project_name を設定しない

        with pytest.raises(ValueError, match="エピソード番号とプロジェクト名は必須です"):
            service.generate_prompt_for_episode(invalid_session)

    @pytest.mark.spec("SPEC-PROMPT-002-003")
    def test_generate_prompt_context_repo_error(
        self, service: PromptGenerationService, valid_session: PromptGenerationSession, mock_context_repo: Mock
    ) -> None:
        """コンテキストリポジトリエラー時のテスト"""
        mock_context_repo.extract_foreshadowing_elements.side_effect = Exception("リポジトリエラー")

        # 実装では例外を警告として処理するため、正常に実行される
        service.generate_prompt_for_episode(valid_session)

        # 警告がセッションに記録されていることを確認
        assert len(valid_session.warnings) > 0
        assert "伏線要素の取得に失敗" in valid_session.warnings[0]

    @pytest.mark.spec("SPEC-PROMPT-002-004")
    def test_collect_context_elements_basic_level(
        self, service: PromptGenerationService, valid_session: PromptGenerationSession, mock_context_repo: Mock
    ) -> None:
        """基本レベルでのコンテキスト収集テスト"""
        valid_session.context_level = "基本"

        service._collect_context_elements(valid_session)

        # 高優先度要素のみフィルタリングされることを確認（priority >= 0.7）
        high_priority_elements = [e for e in valid_session.integrated_context if e.priority >= 0.7]
        assert len(high_priority_elements) == len(valid_session.integrated_context)

    @pytest.mark.spec("SPEC-PROMPT-002-005")
    def test_collect_context_elements_extended_level(
        self, service: PromptGenerationService, valid_session: PromptGenerationSession
    ) -> None:
        """拡張レベルでのコンテキスト収集テスト"""
        valid_session.context_level = "拡張"

        service._collect_context_elements(valid_session)

        # 中優先度以上の要素が含まれることを確認（priority >= 0.4）
        medium_priority_elements = [e for e in valid_session.integrated_context if e.priority >= 0.4]
        assert len(medium_priority_elements) == len(valid_session.integrated_context)

    @pytest.mark.spec("SPEC-PROMPT-002-006")
    def test_collect_context_elements_complete_level(
        self, service: PromptGenerationService, valid_session: PromptGenerationSession
    ) -> None:
        """完全レベルでのコンテキスト収集テスト"""
        valid_session.context_level = "完全"

        service._collect_context_elements(valid_session)

        # フィルタリングなしで全要素が含まれることを確認
        assert len(valid_session.integrated_context) == 3  # foreshadowing + scene + connection

    @pytest.mark.spec("SPEC-PROMPT-002-007")
    def test_collect_context_elements_disabled_foreshadowing(
        self, service: PromptGenerationService, valid_session: PromptGenerationSession, mock_context_repo: Mock
    ) -> None:
        """伏線収集無効時のテスト"""
        valid_session.include_foreshadowing = False

        service._collect_context_elements(valid_session)

        # 伏線要素抽出が呼ばれないことを確認
        mock_context_repo.extract_foreshadowing_elements.assert_not_called()

        # 伏線要素以外は含まれることを確認
        foreshadowing_elements = [
            e for e in valid_session.integrated_context if e.element_type == ContextElementType.FORESHADOWING
        ]
        assert len(foreshadowing_elements) == 0

    @pytest.mark.spec("SPEC-PROMPT-002-008")
    def test_collect_context_elements_disabled_important_scenes(
        self, service: PromptGenerationService, valid_session: PromptGenerationSession, mock_context_repo: Mock
    ) -> None:
        """重要シーン収集無効時のテスト"""
        valid_session.include_important_scenes = False

        service._collect_context_elements(valid_session)

        # 重要シーン抽出が呼ばれないことを確認
        mock_context_repo.extract_important_scenes.assert_not_called()

        # 重要シーン以外は含まれることを確認
        scene_elements = [
            e for e in valid_session.integrated_context if e.element_type == ContextElementType.IMPORTANT_SCENE
        ]
        assert len(scene_elements) == 0

    @pytest.mark.spec("SPEC-PROMPT-002-009")
    def test_collect_context_elements_with_warnings(
        self, service: PromptGenerationService, valid_session: PromptGenerationSession, mock_context_repo: Mock
    ) -> None:
        """コンテキスト収集時の警告テスト"""
        # 空の結果を返すように設定
        mock_context_repo.extract_foreshadowing_elements.return_value = []
        mock_context_repo.extract_important_scenes.return_value = []

        service._collect_context_elements(valid_session)

        # 警告が生成されることを確認
        warnings = [w for w in valid_session.warnings if "が見つかりませんでした" in w]
        assert len(warnings) >= 2  # 伏線 + 重要シーンの警告

    @pytest.mark.spec("SPEC-PROMPT-002-010")
    def test_generate_stage_prompts(
        self, service: PromptGenerationService, valid_session: PromptGenerationSession, mock_a24_guide_repo: Mock
    ) -> None:
        """段階別プロンプト生成テスト"""
        stage_prompts = service._generate_stage_prompts(valid_session)

        # 4段階すべてのプロンプトが生成されることを確認
        assert len(stage_prompts) == 4

        # 各段階でA24ガイドリポジトリが呼ばれることを確認
        assert mock_a24_guide_repo.get_stage_instructions.call_count == 4
        assert mock_a24_guide_repo.get_validation_criteria.call_count == 4

        # セッションの完了段階が更新されることを確認
        assert len(valid_session.completed_stages) == 4

    @pytest.mark.spec("SPEC-PROMPT-002-011")
    def test_generate_context_integration_points(
        self, service: PromptGenerationService, valid_session: PromptGenerationSession
    ) -> None:
        """コンテキスト統合ポイント生成テスト"""
        # テスト用要素を追加
        element = ContextElement(
            element_type=ContextElementType.FORESHADOWING,
            content="テスト伏線",
            priority=0.9,
            integration_stage=A24Stage.TECH_INTEGRATION,
        )

        valid_session.add_context_element(element)

        integration_points = service._generate_context_integration_points(A24Stage.TECH_INTEGRATION, valid_session)

        assert len(integration_points) > 0
        assert any("テスト伏線" in point for point in integration_points)

    @pytest.mark.spec("SPEC-PROMPT-002-012")
    def test_format_integration_point(self, service: PromptGenerationService) -> None:
        """統合ポイント整形テスト"""
        element = ContextElement(
            element_type=ContextElementType.IMPORTANT_SCENE,
            content="重要なシーン",
            priority=0.8,
            integration_stage=A24Stage.SCENE_DETAIL,
        )

        formatted = service._format_integration_point(element)

        assert "【重要シーン】" in formatted
        assert "重要なシーン" in formatted
        assert "★" in formatted  # 優先度インジケータ

    @pytest.mark.spec("SPEC-PROMPT-002-013")
    def test_determine_output_format(self, service: PromptGenerationService) -> None:
        """期待出力フォーマット決定テスト"""
        for stage in A24Stage:
            output_format = service._determine_output_format(stage)
            assert "YAML形式" in output_format
            assert len(output_format) > 0

    @pytest.mark.spec("SPEC-PROMPT-002-014")
    def test_integrate_prompts(
        self, service: PromptGenerationService, valid_session: PromptGenerationSession, mock_a24_guide_repo: Mock
    ) -> None:
        """プロンプト統合テスト"""
        stage_prompts = service._generate_stage_prompts(valid_session)

        integrated = service._integrate_prompts(stage_prompts, valid_session)

        # 統合プロンプトの基本構造確認
        assert f"第{valid_session.episode_number}話プロット作成ガイド" in integrated
        assert "Stage 1:" in integrated
        assert "Stage 4:" in integrated
        assert "YAML形式" in integrated
        assert valid_session.project_name in integrated

        # テンプレート構造取得が呼ばれることを確認
        mock_a24_guide_repo.get_template_structure.assert_called_once()

    @pytest.mark.spec("SPEC-PROMPT-002-015")
    def test_generate_prompt_header(
        self, service: PromptGenerationService, valid_session: PromptGenerationSession
    ) -> None:
        """プロンプトヘッダー生成テスト"""
        header = service._generate_prompt_header(valid_session)

        assert f"第{valid_session.episode_number}話プロット作成ガイド" in header
        assert valid_session.project_name in header
        assert "4段階プロセス" in header
        assert "骨格構築" in header
        assert "技術伏線統合" in header

    @pytest.mark.spec("SPEC-PROMPT-002-016")
    def test_generate_template_explanation(self, service: PromptGenerationService) -> None:
        """テンプレート構造説明生成テスト"""
        template_structure = {"episode_info": {}, "synopsis": ""}
        explanation = service._generate_template_explanation(template_structure)

        assert "使用テンプレート構造" in explanation
        assert "episode_info:" in explanation
        assert "synopsis:" in explanation
        assert "yaml" in explanation.lower()

    @pytest.mark.spec("SPEC-PROMPT-002-017")
    def test_generate_stage_section(self, service: PromptGenerationService, mock_a24_guide_repo: Mock) -> None:
        """段階セクション生成テスト"""
        from noveler.domain.entities.prompt_generation import A24StagePrompt

        stage_prompt = A24StagePrompt(
            stage=A24Stage.SKELETON,
            instructions=["指示1", "指示2"],
            validation_criteria=["チェック1", "チェック2"],
            expected_output_format="YAML形式",
            context_integration_points=["統合ポイント1"],
        )

        section = service._generate_stage_section(stage_prompt, 1)

        assert "Stage 1: 骨格構築" in section
        assert "指示1" in section
        assert "指示2" in section
        assert "チェック1" in section
        assert "統合ポイント1" in section
        assert "YAML形式" in section

    @pytest.mark.spec("SPEC-PROMPT-002-018")
    def test_generate_prompt_footer(
        self, service: PromptGenerationService, valid_session: PromptGenerationSession
    ) -> None:
        """プロンプトフッター生成テスト"""
        # コンテキスト要素追加
        element = ContextElement(
            element_type=ContextElementType.FORESHADOWING,
            content="伏線要素",
            priority=0.8,
            integration_stage=A24Stage.TECH_INTEGRATION,
        )

        valid_session.add_context_element(element)

        footer = service._generate_prompt_footer(valid_session)

        assert f"第{valid_session.episode_number}話" in footer
        assert valid_session.project_name in footer
        assert "伏線要素: 1個" in footer
        assert valid_session.optimization_target.value in footer
        assert valid_session.context_level in footer
