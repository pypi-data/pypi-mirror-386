"""
SPEC-STAGED-002: StagedPromptエンティティのテスト

段階的プロンプト生成のメインエンティティの
状態管理、段階移行、ビジネスルール機能をテストする。
"""

from datetime import datetime
from pathlib import Path

import pytest
pytestmark = pytest.mark.project

from noveler.domain.entities.staged_prompt import StagedPrompt, StageTransitionError
from noveler.domain.value_objects.prompt_stage import PromptStage


class TestStagedPromptCreation:
    """StagedPrompt作成のテスト"""

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_valid_staged_prompt_creation(self):
        """正常なStagedPrompt作成テスト"""
        staged_prompt = StagedPrompt(
            episode_number=5, project_name="テストプロジェクト", project_root=Path("/test/path")
        )

        assert staged_prompt.episode_number == 5
        assert staged_prompt.project_name == "テストプロジェクト"
        assert staged_prompt.project_root == Path("/test/path")
        assert staged_prompt.current_stage == PromptStage.STAGE_1
        assert len(staged_prompt.completed_stages) == 0
        assert isinstance(staged_prompt.created_at, datetime)
        assert isinstance(staged_prompt.updated_at, datetime)

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_invalid_episode_number_raises_error(self):
        """無効なエピソード番号でのエラーテスト"""
        with pytest.raises(ValueError, match="Episode number must be positive"):
            StagedPrompt(episode_number=0, project_name="テストプロジェクト")

        with pytest.raises(ValueError, match="Episode number must be positive"):
            StagedPrompt(episode_number=-1, project_name="テストプロジェクト")

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_empty_project_name_raises_error(self):
        """空のプロジェクト名でのエラーテスト"""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            StagedPrompt(episode_number=1, project_name="")

        with pytest.raises(ValueError, match="Project name cannot be empty"):
            StagedPrompt(episode_number=1, project_name="   ")

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_project_name_is_stripped(self):
        """プロジェクト名の空白除去テスト"""
        staged_prompt = StagedPrompt(episode_number=1, project_name="  テストプロジェクト  ")

        assert staged_prompt.project_name == "テストプロジェクト"


class TestStagedPromptStageManagement:
    """段階管理機能のテスト"""

    def setup_method(self):
        """テスト準備"""
        self.staged_prompt = StagedPrompt(episode_number=1, project_name="テストプロジェクト")

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_initial_stage_state(self):
        """初期段階状態のテスト"""
        assert self.staged_prompt.current_stage == PromptStage.STAGE_1
        assert not self.staged_prompt.is_fully_completed()
        assert self.staged_prompt.get_completion_percentage() == 0.0
        assert self.staged_prompt.get_average_quality_score() == 0.0

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_stage_completion(self):
        """段階完了機能テスト"""
        stage_result = {"test_key": "test_value"}
        quality_score = 85.0
        execution_time = 15

        success = self.staged_prompt.complete_current_stage(
            stage_result=stage_result, quality_score=quality_score, execution_time_minutes=execution_time
        )

        assert success
        assert PromptStage.STAGE_1 in self.staged_prompt.completed_stages
        assert self.staged_prompt.get_stage_result(PromptStage.STAGE_1) == stage_result
        assert self.staged_prompt.get_stage_quality_score(PromptStage.STAGE_1) == quality_score
        assert self.staged_prompt.get_stage_execution_time(PromptStage.STAGE_1) == execution_time
        assert self.staged_prompt.get_completion_percentage() == 0.2  # 1/5
        assert self.staged_prompt.get_average_quality_score() == 85.0

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_complete_stage_invalid_quality_score(self):
        """無効な品質スコアでの段階完了エラーテスト"""
        with pytest.raises(ValueError, match="Quality score must be between 0 and 100"):
            self.staged_prompt.complete_current_stage(stage_result={}, quality_score=101.0, execution_time_minutes=15)

        with pytest.raises(ValueError, match="Quality score must be between 0 and 100"):
            self.staged_prompt.complete_current_stage(stage_result={}, quality_score=-1.0, execution_time_minutes=15)

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_complete_stage_invalid_execution_time(self):
        """無効な実行時間での段階完了エラーテスト"""
        with pytest.raises(ValueError, match="Execution time must be non-negative"):
            self.staged_prompt.complete_current_stage(stage_result={}, quality_score=80.0, execution_time_minutes=-1)


class TestStagedPromptStageTransition:
    """段階移行機能のテスト"""

    def setup_method(self):
        """テスト準備"""
        self.staged_prompt = StagedPrompt(episode_number=1, project_name="テストプロジェクト")

        # Stage 1を完了
        self.staged_prompt.complete_current_stage(
            stage_result={"stage1": "completed"}, quality_score=80.0, execution_time_minutes=15
        )

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_can_advance_to_next_stage(self):
        """次段階への進行可能性テスト"""
        assert self.staged_prompt.can_advance_to_stage(PromptStage.STAGE_2)
        assert not self.staged_prompt.can_advance_to_stage(PromptStage.STAGE_3)
        assert not self.staged_prompt.can_advance_to_stage(PromptStage.STAGE_1)

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_successful_stage_advance(self):
        """成功する段階進行テスト"""
        success = self.staged_prompt.advance_to_stage(PromptStage.STAGE_2)

        assert success
        assert self.staged_prompt.current_stage == PromptStage.STAGE_2

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_invalid_stage_advance_raises_error(self):
        """無効な段階進行でのエラーテスト"""
        with pytest.raises(StageTransitionError):
            self.staged_prompt.advance_to_stage(PromptStage.STAGE_3)

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_get_next_stage(self):
        """次段階取得テスト"""
        next_stage = self.staged_prompt.get_next_stage()
        assert next_stage == PromptStage.STAGE_2

        # Stage 5まで進めてテスト
        self.staged_prompt.advance_to_stage(PromptStage.STAGE_2)
        self.staged_prompt.complete_current_stage({}, 80.0, 15)
        self.staged_prompt.advance_to_stage(PromptStage.STAGE_3)
        self.staged_prompt.complete_current_stage({}, 80.0, 15)
        self.staged_prompt.advance_to_stage(PromptStage.STAGE_4)
        self.staged_prompt.complete_current_stage({}, 80.0, 15)
        self.staged_prompt.advance_to_stage(PromptStage.STAGE_5)

        next_stage = self.staged_prompt.get_next_stage()
        assert next_stage is None


class TestStagedPromptStageRollback:
    """段階戻り機能のテスト"""

    def setup_method(self):
        """テスト準備 - Stage 3まで完了"""
        self.staged_prompt = StagedPrompt(episode_number=1, project_name="テストプロジェクト")

        # Stage 1-3まで完了
        for stage_num in range(1, 4):
            self.staged_prompt.complete_current_stage(
                stage_result={f"stage{stage_num}": "completed"},
                quality_score=80.0 + stage_num,
                execution_time_minutes=15,
            )

            if stage_num < 3:
                next_stage = PromptStage.STAGE_2 if stage_num == 1 else PromptStage.STAGE_3
                self.staged_prompt.advance_to_stage(next_stage)

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_can_rollback_to_previous_stage(self):
        """前段階への戻り可能性テスト"""
        assert self.staged_prompt.can_rollback_to_stage(PromptStage.STAGE_2)
        assert self.staged_prompt.can_rollback_to_stage(PromptStage.STAGE_1)
        assert not self.staged_prompt.can_rollback_to_stage(PromptStage.STAGE_3)
        assert not self.staged_prompt.can_rollback_to_stage(PromptStage.STAGE_4)

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_successful_stage_rollback(self):
        """成功する段階戻りテスト"""
        original_completion_count = len(self.staged_prompt.completed_stages)

        success = self.staged_prompt.rollback_to_stage(PromptStage.STAGE_2)

        assert success
        assert self.staged_prompt.current_stage == PromptStage.STAGE_2
        assert len(self.staged_prompt.completed_stages) < original_completion_count
        assert PromptStage.STAGE_3 not in self.staged_prompt.completed_stages
        assert self.staged_prompt.get_stage_result(PromptStage.STAGE_3) is None

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_invalid_stage_rollback_raises_error(self):
        """無効な段階戻りでのエラーテスト"""
        with pytest.raises(StageTransitionError):
            self.staged_prompt.rollback_to_stage(PromptStage.STAGE_4)


class TestStagedPromptStatusMethods:
    """状態確認メソッドのテスト"""

    def setup_method(self):
        """テスト準備"""
        self.staged_prompt = StagedPrompt(episode_number=5, project_name="テストプロジェクト")

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_is_stage_completed(self):
        """段階完了状態確認テスト"""
        assert not self.staged_prompt.is_stage_completed(PromptStage.STAGE_1)

        self.staged_prompt.complete_current_stage({}, 80.0, 15)
        assert self.staged_prompt.is_stage_completed(PromptStage.STAGE_1)
        assert not self.staged_prompt.is_stage_completed(PromptStage.STAGE_2)

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_is_fully_completed(self):
        """全段階完了状態確認テスト"""
        assert not self.staged_prompt.is_fully_completed()

        # 全段階完了
        for stage_num in range(1, 6):
            self.staged_prompt.complete_current_stage({}, 80.0, 15)
            if stage_num < 5:
                next_stage = (
                    PromptStage.STAGE_2
                    if stage_num == 1
                    else PromptStage.STAGE_3
                    if stage_num == 2
                    else PromptStage.STAGE_4
                    if stage_num == 3
                    else PromptStage.STAGE_5
                )
                self.staged_prompt.advance_to_stage(next_stage)

        assert self.staged_prompt.is_fully_completed()

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_get_status_summary(self):
        """状態サマリー取得テスト"""
        summary = self.staged_prompt.get_status_summary()

        assert summary["episode_number"] == 5
        assert summary["project_name"] == "テストプロジェクト"
        assert summary["current_stage"]["number"] == 1
        assert summary["completion_percentage"] == 0.0
        assert summary["completed_stages_count"] == 0
        assert summary["is_fully_completed"] is False
        assert "created_at" in summary
        assert "updated_at" in summary

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_get_total_execution_time(self):
        """総実行時間取得テスト"""
        assert self.staged_prompt.get_total_execution_time() == 0

        self.staged_prompt.complete_current_stage({}, 80.0, 15)
        self.staged_prompt.advance_to_stage(PromptStage.STAGE_2)
        self.staged_prompt.complete_current_stage({}, 85.0, 20)

        assert self.staged_prompt.get_total_execution_time() == 35


class TestStagedPromptValidation:
    """段階完了基準検証のテスト"""

    def setup_method(self):
        """テスト準備"""
        self.staged_prompt = StagedPrompt(episode_number=1, project_name="テストプロジェクト")

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_validate_stage_completion_criteria_stage1(self):
        """Stage 1完了基準検証テスト"""
        valid_content = {
            "episode_number": 1,
            "title": "テストタイトル",
            "chapter": 1,
            "theme": "テストテーマ",
            "purpose": "テスト目的",
            "synopsis": "これは十分に長いシノプシスです。" * 10,  # 100文字以上
        }

        errors = self.staged_prompt.validate_stage_completion_criteria(PromptStage.STAGE_1, valid_content)

        assert len(errors) == 0

        # 短いシノプシス
        invalid_content = valid_content.copy()
        invalid_content["synopsis"] = "短すぎる"

        errors = self.staged_prompt.validate_stage_completion_criteria(PromptStage.STAGE_1, invalid_content)

        assert len(errors) > 0
        assert "Synopsis too short" in errors[0]

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_validate_stage_completion_criteria_stage2(self):
        """Stage 2完了基準検証テスト"""
        valid_content = {
            "story_structure": {"setup": "導入部", "confrontation": "展開部", "resolution": "解決部"},
            "setup": "導入部詳細",
            "confrontation": "展開部詳細",
            "resolution": "解決部詳細",
        }

        errors = self.staged_prompt.validate_stage_completion_criteria(PromptStage.STAGE_2, valid_content)

        assert len(errors) == 0

        # 不完全な三幕構成
        invalid_content = {
            "story_structure": {
                "setup": "導入部"
                # act2, act3が不足
            },
            "setup": "導入部詳細",
            # act2, act3が不足
        }

        errors = self.staged_prompt.validate_stage_completion_criteria(PromptStage.STAGE_2, invalid_content)

        assert len(errors) > 0
        # 必須要素不足とthree-act structure incompleteの両方が報告される
        assert any("Required element missing" in error for error in errors)
        assert any("Three-act structure incomplete" in error for error in errors)

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_validate_stage_completion_criteria_missing_elements(self):
        """必須要素不足の検証テスト"""
        incomplete_content = {
            "episode_number": 1
            # 他の必須要素が不足
        }

        errors = self.staged_prompt.validate_stage_completion_criteria(PromptStage.STAGE_1, incomplete_content)

        # 不足している必須要素が報告される
        assert len(errors) > 0
        missing_elements = [error for error in errors if "Required element missing" in error]
        assert len(missing_elements) > 0


class TestStagedPromptEquality:
    """等価性のテスト"""

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_staged_prompt_equality(self):
        """StagedPrompt等価性テスト"""
        prompt1 = StagedPrompt(episode_number=1, project_name="テストプロジェクト")

        prompt2 = StagedPrompt(episode_number=1, project_name="テストプロジェクト")

        prompt3 = StagedPrompt(episode_number=2, project_name="テストプロジェクト")

        assert prompt1 == prompt2
        assert prompt1 != prompt3
        assert hash(prompt1) == hash(prompt2)
        assert hash(prompt1) != hash(prompt3)

    @pytest.mark.spec("SPEC-STAGED-002")
    def test_staged_prompt_representation(self):
        """文字列表現テスト"""
        prompt = StagedPrompt(episode_number=5, project_name="テストプロジェクト")

        repr_str = repr(prompt)
        assert "episode=5" in repr_str
        assert "project='テストプロジェクト'" in repr_str
        assert "current_stage=1" in repr_str
        assert "completed=0/5" in repr_str
