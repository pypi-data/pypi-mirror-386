"""Smart Auto-Enhancement Entity Unit Tests

SPEC-SAE-005: Smart Auto-Enhancement エンティティ単体テスト
- TDD原則に基づくテスト駆動開発
- ドメインロジックの完全なテストカバレッジ
- pytest + pytest.mark.spec によるSPEC仕様との連携
"""

import pytest
pytestmark = pytest.mark.quality_domain

from noveler.domain.entities.smart_auto_enhancement import (
    EnhancementMode,
    EnhancementRequest,
    EnhancementResult,
    EnhancementStage,
    SmartAutoEnhancement,
)
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.project_info import ProjectInfo
from noveler.domain.value_objects.quality_score import QualityScore


@pytest.mark.spec("SPEC-SAE-001")
class TestSmartAutoEnhancement:
    """Smart Auto-Enhancement エンティティのテストクラス"""

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-CREATE_SMART_AUTO_EN")
    def test_create_smart_auto_enhancement_with_valid_request(self):
        """有効なリクエストでSmart Auto-Enhancement エンティティを作成"""
        # Arrange
        request = EnhancementRequest(
            episode_number=EpisodeNumber(1),
            project_info=ProjectInfo(name="test_project"),
            mode=EnhancementMode.SMART_AUTO,
        )

        # Act
        enhancement = SmartAutoEnhancement(request)

        # Assert
        assert enhancement.request == request
        assert enhancement.current_stage == EnhancementStage.BASIC_CHECK
        assert enhancement.is_smart_auto_mode is True
        assert enhancement.is_completed() is False
        assert enhancement.is_success() is False

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-CREATE_ENHANCED_MODE")
    def test_create_enhanced_mode_forces_detailed_review(self):
        """Enhanced モードでは詳細レビューが強制される"""
        # Arrange & Act
        request = EnhancementRequest(
            episode_number=EpisodeNumber(1),
            project_info=ProjectInfo(name="test_project"),
            mode=EnhancementMode.ENHANCED,
            show_detailed_review=False,  # 意図的にFalseを指定
        )

        # Assert
        assert request.show_detailed_review is True  # 強制的にTrueになる

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-SMART_AUTO_MODE_PREV")
    def test_smart_auto_mode_prevents_all_stages_skip(self):
        """Smart Auto-Enhancement モードでは全段階スキップが無効"""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Smart Auto-Enhancement では全段階スキップは無効"):
            EnhancementRequest(
                episode_number=EpisodeNumber(1),
                project_info=ProjectInfo(name="test_project"),
                mode=EnhancementMode.SMART_AUTO,
                skip_basic=True,
                skip_a31=True,
                skip_claude=True,
            )

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-SHOULD_EXECUTE_STAGE")
    def test_should_execute_stage_in_smart_auto_mode(self):
        """Smart Auto-Enhancement モードでは全段階実行"""
        # Arrange
        request = EnhancementRequest(
            episode_number=EpisodeNumber(1),
            project_info=ProjectInfo(name="test_project"),
            mode=EnhancementMode.SMART_AUTO,
        )

        enhancement = SmartAutoEnhancement(request)

        # Act & Assert
        assert enhancement.should_execute_stage(EnhancementStage.BASIC_CHECK) is True
        assert enhancement.should_execute_stage(EnhancementStage.A31_EVALUATION) is True
        assert enhancement.should_execute_stage(EnhancementStage.CLAUDE_ANALYSIS) is True

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-SHOULD_EXECUTE_STAGE")
    def test_should_execute_stage_respects_skip_options_in_standard_mode(self):
        """標準モードではスキップオプションを考慮"""
        # Arrange
        request = EnhancementRequest(
            episode_number=EpisodeNumber(1),
            project_info=ProjectInfo(name="test_project"),
            mode=EnhancementMode.STANDARD,
            skip_basic=True,
            skip_a31=False,
            skip_claude=True,
        )

        enhancement = SmartAutoEnhancement(request)

        # Act & Assert
        assert enhancement.should_execute_stage(EnhancementStage.BASIC_CHECK) is False
        assert enhancement.should_execute_stage(EnhancementStage.A31_EVALUATION) is True
        assert enhancement.should_execute_stage(EnhancementStage.CLAUDE_ANALYSIS) is False

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-ADVANCE_TO_STAGE_SUC")
    def test_advance_to_stage_successfully(self):
        """段階を正常に進める"""
        # Arrange
        request = EnhancementRequest(
            episode_number=EpisodeNumber(1),
            project_info=ProjectInfo(name="test_project"),
            mode=EnhancementMode.SMART_AUTO,
        )

        enhancement = SmartAutoEnhancement(request)

        # Act
        enhancement.advance_to_stage(EnhancementStage.A31_EVALUATION)

        # Assert
        assert enhancement.current_stage == EnhancementStage.A31_EVALUATION

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-ADVANCE_TO_STAGE_PRE")
    def test_advance_to_stage_prevents_regression(self):
        """段階の後退を防ぐ"""
        # Arrange
        request = EnhancementRequest(
            episode_number=EpisodeNumber(1),
            project_info=ProjectInfo(name="test_project"),
            mode=EnhancementMode.SMART_AUTO,
        )

        enhancement = SmartAutoEnhancement(request)
        enhancement.advance_to_stage(EnhancementStage.A31_EVALUATION)

        # Act & Assert
        with pytest.raises(ValueError, match="段階を後退させることはできません"):
            enhancement.advance_to_stage(EnhancementStage.BASIC_CHECK)

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-ADD_STAGE_RESULT_SUC")
    def test_add_stage_result_successfully(self):
        """段階結果を正常に追加"""
        # Arrange
        request = EnhancementRequest(
            episode_number=EpisodeNumber(1),
            project_info=ProjectInfo(name="test_project"),
            mode=EnhancementMode.SMART_AUTO,
        )

        enhancement = SmartAutoEnhancement(request)

        result = EnhancementResult(
            stage=EnhancementStage.BASIC_CHECK,
            basic_score=QualityScore(75),
            a31_score=None,
            claude_score=None,
            execution_time_ms=100.0,
            improvements_count=5,
            error_message=None,
        )

        # Act
        enhancement.add_stage_result(EnhancementStage.BASIC_CHECK, result)

        # Assert
        assert enhancement.get_stage_result(EnhancementStage.BASIC_CHECK) == result

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-ADD_FAILED_RESULT_MO")
    def test_add_failed_result_moves_to_failed_stage(self):
        """失敗結果の追加で失敗状態に移行"""
        # Arrange
        request = EnhancementRequest(
            episode_number=EpisodeNumber(1),
            project_info=ProjectInfo(name="test_project"),
            mode=EnhancementMode.SMART_AUTO,
        )

        enhancement = SmartAutoEnhancement(request)

        failed_result = EnhancementResult(
            stage=EnhancementStage.BASIC_CHECK,
            basic_score=None,
            a31_score=None,
            claude_score=None,
            execution_time_ms=50.0,
            improvements_count=0,
            error_message="テストエラー",
        )

        # Act
        enhancement.add_stage_result(EnhancementStage.BASIC_CHECK, failed_result)

        # Assert
        assert enhancement.current_stage == EnhancementStage.FAILED
        assert enhancement.is_completed() is True
        assert enhancement.is_success() is False

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-GET_FINAL_RESULT_RET")
    def test_get_final_result_returns_claude_result_first(self):
        """最終結果としてClaude結果を優先"""
        # Arrange
        request = EnhancementRequest(
            episode_number=EpisodeNumber(1),
            project_info=ProjectInfo(name="test_project"),
            mode=EnhancementMode.SMART_AUTO,
        )

        enhancement = SmartAutoEnhancement(request)

        basic_result = EnhancementResult(
            stage=EnhancementStage.BASIC_CHECK,
            basic_score=QualityScore(70),
            a31_score=None,
            claude_score=None,
            execution_time_ms=100.0,
            improvements_count=3,
            error_message=None,
        )

        claude_result = EnhancementResult(
            stage=EnhancementStage.CLAUDE_ANALYSIS,
            basic_score=None,
            a31_score=None,
            claude_score=QualityScore(85),
            execution_time_ms=200.0,
            improvements_count=8,
            error_message=None,
        )

        enhancement.add_stage_result(EnhancementStage.BASIC_CHECK, basic_result)
        enhancement.add_stage_result(EnhancementStage.CLAUDE_ANALYSIS, claude_result)

        # Act
        final_result = enhancement.get_final_result()

        # Assert
        assert final_result == claude_result

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-GET_TOTAL_IMPROVEMEN")
    def test_get_total_improvements_count(self):
        """総改善提案数の計算"""
        # Arrange
        request = EnhancementRequest(
            episode_number=EpisodeNumber(1),
            project_info=ProjectInfo(name="test_project"),
            mode=EnhancementMode.SMART_AUTO,
        )

        enhancement = SmartAutoEnhancement(request)

        basic_result = EnhancementResult(
            stage=EnhancementStage.BASIC_CHECK,
            basic_score=QualityScore(70),
            a31_score=None,
            claude_score=None,
            execution_time_ms=100.0,
            improvements_count=3,
            error_message=None,
        )

        a31_result = EnhancementResult(
            stage=EnhancementStage.A31_EVALUATION,
            basic_score=None,
            a31_score=QualityScore(75),
            claude_score=None,
            execution_time_ms=150.0,
            improvements_count=7,
            error_message=None,
        )

        enhancement.add_stage_result(EnhancementStage.BASIC_CHECK, basic_result)
        enhancement.add_stage_result(EnhancementStage.A31_EVALUATION, a31_result)

        # Act
        total_count = enhancement.get_total_improvements_count()

        # Assert
        assert total_count == 10  # 3 + 7

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-DOMAIN_INVARIANTS_VA")
    def test_domain_invariants_validation(self):
        """ドメイン不変条件の検証"""
        # Invalid episode number
        with pytest.raises(ValueError, match="エピソード番号は1以上である必要があります"):
            request = EnhancementRequest(
                episode_number=EpisodeNumber(0),
                project_info=ProjectInfo(name="test_project"),
                mode=EnhancementMode.SMART_AUTO,
            )

            SmartAutoEnhancement(request)

        # Empty project name
        with pytest.raises(ValueError, match="プロジェクト名は必須です"):
            request = EnhancementRequest(
                episode_number=EpisodeNumber(1), project_info=ProjectInfo(name=""), mode=EnhancementMode.SMART_AUTO
            )

            SmartAutoEnhancement(request)


@pytest.mark.spec("SPEC-SAE-001")
class TestEnhancementResult:
    """Enhancement Result のテストクラス"""

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-GET_FINAL_SCORE_RETU")
    def test_get_final_score_returns_claude_first(self):
        """最終スコアとしてClaudeスコアを優先"""
        # Arrange
        result = EnhancementResult(
            stage=EnhancementStage.CLAUDE_ANALYSIS,
            basic_score=QualityScore(70),
            a31_score=QualityScore(75),
            claude_score=QualityScore(85),
            execution_time_ms=200.0,
            improvements_count=8,
            error_message=None,
        )

        # Act
        final_score = result.get_final_score()

        # Assert
        assert final_score.value == 85.0

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-GET_FINAL_SCORE_FALL")
    def test_get_final_score_fallback_to_a31(self):
        """Claudeスコアがない場合はA31スコアを使用"""
        # Arrange
        result = EnhancementResult(
            stage=EnhancementStage.A31_EVALUATION,
            basic_score=QualityScore(70),
            a31_score=QualityScore(75),
            claude_score=None,
            execution_time_ms=150.0,
            improvements_count=5,
            error_message=None,
        )

        # Act
        final_score = result.get_final_score()

        # Assert
        assert final_score.value == 75.0

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-IS_SUCCESS_WITH_COMP")
    def test_is_success_with_completed_stage_and_no_error(self):
        """完了段階でエラーなしの場合は成功"""
        # Arrange
        result = EnhancementResult(
            stage=EnhancementStage.COMPLETED,
            basic_score=QualityScore(80),
            a31_score=None,
            claude_score=None,
            execution_time_ms=100.0,
            improvements_count=3,
            error_message=None,
        )

        # Act & Assert
        assert result.is_success() is True

    @pytest.mark.spec("SPEC-SMART_AUTO_ENHANCEMENT-IS_SUCCESS_FAILS_WIT")
    def test_is_success_fails_with_error_message(self):
        """エラーメッセージがある場合は失敗"""
        # Arrange
        result = EnhancementResult(
            stage=EnhancementStage.COMPLETED,
            basic_score=QualityScore(80),
            a31_score=None,
            claude_score=None,
            execution_time_ms=100.0,
            improvements_count=3,
            error_message="テストエラー",
        )

        # Act & Assert
        assert result.is_success() is False
