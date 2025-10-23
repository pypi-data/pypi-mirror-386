#!/usr/bin/env python3
"""
プロンプト生成エンティティのユニットテスト

SPEC-PROMPT-001: A24プロンプト生成機能
DDD設計に基づくプロンプト生成エンティティの動作を検証する。
"""

from uuid import UUID

import pytest
pytestmark = pytest.mark.plot_episode

from noveler.domain.entities.prompt_generation import (
    A24Stage,
    A24StagePrompt,
    ContextElement,
    ContextElementType,
    OptimizationTarget,
    PromptGenerationSession,
)


class TestContextElement:
    """ContextElement バリューオブジェクトのテスト"""

    @pytest.mark.spec("SPEC-PROMPT-001-001")
    def test_context_element_creation_success(self) -> None:
        """正常なContextElement作成テスト"""
        element = ContextElement(
            element_type=ContextElementType.FORESHADOWING,
            content="重要な伏線要素",
            priority=0.8,
            integration_stage=A24Stage.TECH_INTEGRATION,
            source_file="伏線管理.yaml",
            metadata={"category": "main_plot"},
        )

        assert element.element_type == ContextElementType.FORESHADOWING
        assert element.content == "重要な伏線要素"
        assert element.priority == 0.8
        assert element.integration_stage == A24Stage.TECH_INTEGRATION
        assert element.source_file == "伏線管理.yaml"
        assert element.metadata["category"] == "main_plot"

    @pytest.mark.spec("SPEC-PROMPT-001-002")
    def test_context_element_invalid_priority(self) -> None:
        """無効な優先度でのContextElement作成テスト"""
        with pytest.raises(ValueError, match="優先度は0.0-1.0の範囲である必要があります"):
            ContextElement(
                element_type=ContextElementType.FORESHADOWING,
                content="テスト要素",
                priority=1.5,  # 無効な優先度
                integration_stage=A24Stage.SKELETON,
            )

    @pytest.mark.spec("SPEC-PROMPT-001-003")
    def test_context_element_empty_content(self) -> None:
        """空のコンテンツでのContextElement作成テスト"""
        with pytest.raises(ValueError, match="コンテンツは空にできません"):
            ContextElement(
                element_type=ContextElementType.IMPORTANT_SCENE,
                content="   ",  # 空白のみ
                priority=0.5,
                integration_stage=A24Stage.SCENE_DETAIL,
            )


class TestA24StagePrompt:
    """A24StagePrompt バリューオブジェクトのテスト"""

    @pytest.mark.spec("SPEC-PROMPT-001-004")
    def test_stage_prompt_creation_success(self) -> None:
        """正常なA24StagePrompt作成テスト"""
        stage_prompt = A24StagePrompt(
            stage=A24Stage.SKELETON,
            instructions=["基本情報を記入", "概要を作成"],
            validation_criteria=["必須項目入力済み", "YAML構文チェック済み"],
            expected_output_format="YAML形式の基本情報",
            context_integration_points=["【伏線】重要な要素"],
        )

        assert stage_prompt.stage == A24Stage.SKELETON
        assert len(stage_prompt.instructions) == 2
        assert "基本情報を記入" in stage_prompt.instructions
        assert len(stage_prompt.validation_criteria) == 2
        assert stage_prompt.expected_output_format == "YAML形式の基本情報"
        assert len(stage_prompt.context_integration_points) == 1

    @pytest.mark.spec("SPEC-PROMPT-001-005")
    def test_stage_prompt_empty_instructions(self) -> None:
        """空の指示リストでのA24StagePrompt作成テスト"""
        with pytest.raises(ValueError, match="指示リストは空にできません"):
            A24StagePrompt(
                stage=A24Stage.THREE_ACT,
                instructions=[],  # 空の指示リスト
                validation_criteria=["チェック項目"],
                expected_output_format="YAML形式",
            )

    @pytest.mark.spec("SPEC-PROMPT-001-006")
    def test_stage_prompt_empty_output_format(self) -> None:
        """空の期待出力フォーマットでのA24StagePrompt作成テスト"""
        with pytest.raises(ValueError, match="期待出力フォーマットは空にできません"):
            A24StagePrompt(
                stage=A24Stage.SCENE_DETAIL,
                instructions=["指示1"],
                validation_criteria=["チェック1"],
                expected_output_format="",  # 空の出力フォーマット
            )


class TestPromptGenerationSession:
    """PromptGenerationSession エンティティのテスト"""

    @pytest.mark.spec("SPEC-PROMPT-001-007")
    def test_session_creation_success(self) -> None:
        """正常なPromptGenerationSession作成テスト"""
        session = PromptGenerationSession()

        assert isinstance(session.session_id, UUID)
        assert session.episode_number == 0
        assert session.project_name == ""
        assert session.context_level == "基本"
        assert session.optimization_target == OptimizationTarget.CLAUDE_CODE
        assert session.include_foreshadowing is True
        assert session.include_important_scenes is True
        assert session.current_stage is None
        assert len(session.completed_stages) == 0
        assert len(session.generated_content) == 0
        assert len(session.integrated_context) == 0
        assert session.final_prompt == ""
        assert session.token_estimate == 0
        assert session.generation_time_ms == 0
        assert len(session.errors) == 0
        assert len(session.warnings) == 0

    @pytest.mark.spec("SPEC-PROMPT-001-008")
    def test_session_start_generation(self) -> None:
        """プロンプト生成開始テスト"""
        session = PromptGenerationSession()
        session.start_generation(12, "テストプロジェクト")

        assert session.episode_number == 12
        assert session.project_name == "テストプロジェクト"
        assert session.current_stage == A24Stage.SKELETON
        assert session.created_at is not None

    @pytest.mark.spec("SPEC-PROMPT-001-009")
    def test_session_advance_to_stage(self) -> None:
        """段階進行テスト"""
        session = PromptGenerationSession()
        session.start_generation(1, "プロジェクト")

        # SKELETON → THREE_ACT
        session.advance_to_stage(A24Stage.THREE_ACT)

        assert session.current_stage == A24Stage.THREE_ACT
        assert A24Stage.SKELETON in session.completed_stages

    @pytest.mark.spec("SPEC-PROMPT-001-010")
    def test_session_complete_current_stage(self) -> None:
        """現在段階完了テスト"""
        session = PromptGenerationSession()
        session.start_generation(1, "プロジェクト")

        generated_content = "Stage 1 完了内容"
        session.complete_current_stage(generated_content)

        assert session.generated_content[A24Stage.SKELETON] == generated_content
        assert A24Stage.SKELETON in session.completed_stages

    @pytest.mark.spec("SPEC-PROMPT-001-011")
    def test_session_complete_stage_without_current(self) -> None:
        """アクティブ段階なしでの完了テスト"""
        session = PromptGenerationSession()

        with pytest.raises(ValueError, match="アクティブな段階がありません"):
            session.complete_current_stage("内容")

    @pytest.mark.spec("SPEC-PROMPT-001-012")
    def test_session_add_context_element(self) -> None:
        """コンテキスト要素追加テスト"""
        session = PromptGenerationSession()

        element = ContextElement(
            element_type=ContextElementType.FORESHADOWING,
            content="テスト伏線",
            priority=0.7,
            integration_stage=A24Stage.TECH_INTEGRATION,
        )

        session.add_context_element(element)

        assert len(session.integrated_context) == 1
        assert session.integrated_context[0] == element

    @pytest.mark.spec("SPEC-PROMPT-001-013")
    def test_session_finalize_prompt(self) -> None:
        """プロンプト生成完了テスト"""
        session = PromptGenerationSession()
        session.start_generation(1, "プロジェクト")

        # 全段階を完了状態にする
        for stage in A24Stage:
            session.completed_stages.append(stage)

        final_prompt = "完成されたプロンプト"
        token_estimate = 1500
        generation_time_ms = 2500

        session.finalize_prompt(final_prompt, token_estimate, generation_time_ms)

        assert session.final_prompt == final_prompt
        assert session.token_estimate == token_estimate
        assert session.generation_time_ms == generation_time_ms

    @pytest.mark.spec("SPEC-PROMPT-001-014")
    def test_session_finalize_with_missing_stages(self) -> None:
        """未完了段階があるプロンプト完了テスト"""
        session = PromptGenerationSession()
        session.start_generation(1, "プロジェクト")

        # 一部段階のみ完了
        session.completed_stages.append(A24Stage.SKELETON)
        session.completed_stages.append(A24Stage.THREE_ACT)

        session.finalize_prompt("プロンプト", 1000, 1000)

        assert len(session.warnings) > 0
        assert "未完了段階があります" in session.warnings[0]

    @pytest.mark.spec("SPEC-PROMPT-001-015")
    def test_session_add_error_and_warning(self) -> None:
        """エラーと警告追加テスト"""
        session = PromptGenerationSession()

        session.add_error("テストエラー")
        session.add_warning("テスト警告")

        assert len(session.errors) == 1
        assert "テストエラー" in session.errors[0]
        assert len(session.warnings) == 1
        assert "テスト警告" in session.warnings[0]

    @pytest.mark.spec("SPEC-PROMPT-001-016")
    def test_session_is_completed(self) -> None:
        """完了判定テスト"""
        session = PromptGenerationSession()

        # 初期状態：未完了
        assert session.is_completed() is False

        # プロンプト設定のみ：未完了（エラーがないことも必要）
        session.final_prompt = "プロンプト"
        assert session.is_completed() is True

        # エラーがある場合：未完了
        session.add_error("エラー")
        assert session.is_completed() is False

    @pytest.mark.spec("SPEC-PROMPT-001-017")
    def test_session_is_success(self) -> None:
        """成功判定テスト"""
        session = PromptGenerationSession()

        # 初期状態：失敗
        assert session.is_success() is False

        # プロンプト完了 + 3段階以上完了：成功
        session.final_prompt = "プロンプト"
        session.completed_stages = [A24Stage.SKELETON, A24Stage.THREE_ACT, A24Stage.SCENE_DETAIL]
        assert session.is_success() is True

        # 段階不足：失敗
        session.completed_stages = [A24Stage.SKELETON, A24Stage.THREE_ACT]
        assert session.is_success() is False

    @pytest.mark.spec("SPEC-PROMPT-001-018")
    def test_session_get_completion_rate(self) -> None:
        """完了率取得テスト"""
        session = PromptGenerationSession()

        # 初期状態：0%
        assert session.get_completion_rate() == 0.0

        # 2段階完了：50%
        session.completed_stages = [A24Stage.SKELETON, A24Stage.THREE_ACT]
        assert session.get_completion_rate() == 0.5

        # 全段階完了：100%
        session.completed_stages = list(A24Stage)
        assert session.get_completion_rate() == 1.0

    @pytest.mark.spec("SPEC-PROMPT-001-019")
    def test_session_get_context_summary(self) -> None:
        """コンテキストサマリ取得テスト"""
        session = PromptGenerationSession()

        # 初期状態
        summary = session.get_context_summary()
        assert all(count == 0 for count in summary.values())

        # 要素追加後
        foreshadowing = ContextElement(
            element_type=ContextElementType.FORESHADOWING,
            content="伏線1",
            priority=0.8,
            integration_stage=A24Stage.TECH_INTEGRATION,
        )

        scene = ContextElement(
            element_type=ContextElementType.IMPORTANT_SCENE,
            content="重要シーン1",
            priority=0.7,
            integration_stage=A24Stage.SCENE_DETAIL,
        )

        session.add_context_element(foreshadowing)
        session.add_context_element(scene)

        summary = session.get_context_summary()
        assert summary["伏線要素"] == 1
        assert summary["重要シーン"] == 1
        assert summary["章間連携"] == 0
        assert summary["技術要素"] == 0

    @pytest.mark.spec("SPEC-PROMPT-001-020")
    def test_session_get_statistics(self) -> None:
        """セッション統計取得テスト"""
        session = PromptGenerationSession()
        session.start_generation(12, "テストプロジェクト")
        session.token_estimate = 1500
        session.generation_time_ms = 2000
        session.add_error("テストエラー")
        session.add_warning("テスト警告")

        stats = session.get_session_statistics()

        assert stats["session_id"] == str(session.session_id)
        assert stats["episode_number"] == 12
        assert stats["project_name"] == "テストプロジェクト"
        assert stats["completion_rate"] == 0.0  # 段階未完了
        assert stats["token_estimate"] == 1500
        assert stats["generation_time_ms"] == 2000
        assert stats["error_count"] == 1
        assert stats["warning_count"] == 1
        assert stats["success"] is False

    @pytest.mark.spec("SPEC-PROMPT-001-021")
    def test_session_restart_completed(self) -> None:
        """完了済みセッションの再開始テスト"""
        session = PromptGenerationSession()
        session.start_generation(1, "プロジェクト")
        session.final_prompt = "完了済み"

        # 完了済みセッションでの再開始は失敗
        with pytest.raises(ValueError, match="既に完了したセッションです"):
            session.start_generation(2, "別プロジェクト")
