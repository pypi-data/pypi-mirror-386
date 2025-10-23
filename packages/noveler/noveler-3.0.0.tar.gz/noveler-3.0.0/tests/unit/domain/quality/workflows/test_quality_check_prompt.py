"""
品質チェックプロンプトエンティティのテスト

SPEC-STAGE5-SEPARATION対応
TDD実装: 品質チェックプロンプト生成機能のテストケース
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
pytestmark = pytest.mark.quality_domain


from noveler.domain.entities.quality_check_prompt import (
    PlotValidationResult,
    QualityCheckPrompt,
    QualityCheckPromptGenerator,
    QualityCheckPromptId,
    QualityCheckResult,
)
from noveler.domain.value_objects.quality_check_level import (
    QualityCheckLevel,
    QualityCheckRequest,
    get_standard_quality_criteria,
)


@pytest.mark.spec("SPEC-STAGE5-SEPARATION")
class TestQualityCheckPromptId:
    """品質チェックプロンプトIDのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-DEFAULT_UUID_GENERAT")
    def test_default_uuid_generation(self):
        """デフォルトUUID生成テスト"""
        prompt_id = QualityCheckPromptId()

        assert prompt_id.value is not None
        assert len(prompt_id.value) > 0
        assert isinstance(prompt_id.value, str)

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-CUSTOM_ID_CREATION")
    def test_custom_id_creation(self):
        """カスタムID作成テスト"""
        custom_id = "test-prompt-001"
        prompt_id = QualityCheckPromptId(custom_id)

        assert prompt_id.value == custom_id
        assert str(prompt_id) == custom_id

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-EMPTY_ID_VALIDATION")
    def test_empty_id_validation(self):
        """空ID検証テスト"""
        with pytest.raises(ValueError, match="Quality check prompt ID cannot be empty"):
            QualityCheckPromptId("")

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-EQUALITY_COMPARISON")
    def test_equality_comparison(self):
        """等価性比較テスト"""
        id1 = QualityCheckPromptId("test-id")
        id2 = QualityCheckPromptId("test-id")
        id3 = QualityCheckPromptId("different-id")

        assert id1 == id2
        assert id1 != id3
        assert id1 != "test-id"  # 型が異なる場合

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-HASH_CONSISTENCY")
    def test_hash_consistency(self):
        """ハッシュ一貫性テスト"""
        id1 = QualityCheckPromptId("test-id")
        id2 = QualityCheckPromptId("test-id")

        assert hash(id1) == hash(id2)
        assert {id1, id2} == {id1}  # セット操作での一意性確認


@pytest.mark.spec("SPEC-STAGE5-SEPARATION")
class TestQualityCheckResult:
    """品質チェック結果のテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-VALID_RESULT_CREATIO")
    def test_valid_result_creation(self):
        """有効な結果作成テスト"""
        result = QualityCheckResult(
            overall_score=85.5,
            criterion_scores={"QC001": 90.0, "QC002": 80.0},
            passed_criteria=["QC001"],
            failed_criteria=["QC002"],
            recommendations=["Improve character consistency"],
        )

        assert result.overall_score == 85.5
        assert result.criterion_scores["QC001"] == 90.0
        assert "QC001" in result.passed_criteria
        assert "QC002" in result.failed_criteria
        assert len(result.recommendations) == 1

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-SCORE_VALIDATION")
    def test_score_validation(self):
        """スコア検証テスト"""
        # 正常範囲
        result = QualityCheckResult(
            overall_score=0.0, criterion_scores={}, passed_criteria=[], failed_criteria=[], recommendations=[]
        )

        assert result.overall_score == 0.0

        result = QualityCheckResult(
            overall_score=100.0, criterion_scores={}, passed_criteria=[], failed_criteria=[], recommendations=[]
        )

        assert result.overall_score == 100.0

        # 範囲外エラー
        with pytest.raises(ValueError, match="Overall score must be between 0 and 100"):
            QualityCheckResult(
                overall_score=-1.0, criterion_scores={}, passed_criteria=[], failed_criteria=[], recommendations=[]
            )

        with pytest.raises(ValueError, match="Overall score must be between 0 and 100"):
            QualityCheckResult(
                overall_score=101.0, criterion_scores={}, passed_criteria=[], failed_criteria=[], recommendations=[]
            )

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-PASSING_GRADE_JUDGME")
    def test_passing_grade_judgment(self):
        """合格判定テスト"""
        passing_result = QualityCheckResult(
            overall_score=85.0, criterion_scores={}, passed_criteria=[], failed_criteria=[], recommendations=[]
        )

        failing_result = QualityCheckResult(
            overall_score=75.0, criterion_scores={}, passed_criteria=[], failed_criteria=[], recommendations=[]
        )

        assert passing_result.is_passing_grade()  # デフォルト80.0以上
        assert not failing_result.is_passing_grade()

        # カスタム閾値
        assert failing_result.is_passing_grade(threshold=70.0)

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-IMPROVEMENT_PRIORITY")
    def test_improvement_priority(self):
        """改善優先度テスト"""
        result = QualityCheckResult(
            overall_score=70.0,
            criterion_scores={
                "QC001": 90.0,  # 合格
                "QC002": 60.0,  # 失格（低優先）
                "QC003": 40.0,  # 失格（高優先）
            },
            passed_criteria=["QC001"],
            failed_criteria=["QC002", "QC003"],
            recommendations=[],
        )

        priority = result.get_improvement_priority()
        assert priority == ["QC003", "QC002"]  # スコア低い順


@pytest.mark.spec("SPEC-STAGE5-SEPARATION")
class TestQualityCheckPrompt:
    """品質チェックプロンプトエンティティのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-DEFAULT_CREATION")
    def test_default_creation(self):
        """デフォルト作成テスト"""
        prompt = QualityCheckPrompt()

        assert prompt.prompt_id is not None
        assert prompt.request is None
        assert prompt.episode_plot is None
        assert len(prompt.check_criteria) == 0
        assert prompt.generated_prompt is None
        assert prompt.check_result is None
        assert prompt.creation_timestamp <= datetime.now(timezone.utc)

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-REQUEST_SETTING")
    def test_request_setting(self):
        """要求設定テスト"""
        prompt = QualityCheckPrompt()
        request = QualityCheckRequest(
            episode_number=1,
            project_name="Test Project",
            plot_file_path="test.yaml",
            check_level=QualityCheckLevel.STANDARD,
        )

        prompt.set_request(request)

        assert prompt.request == request
        assert "request_set" in prompt.get_domain_events()

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-DUPLICATE_REQUEST_SE")
    def test_duplicate_request_setting(self):
        """重複要求設定テスト"""
        prompt = QualityCheckPrompt()
        request = QualityCheckRequest(
            episode_number=1,
            project_name="Test Project",
            plot_file_path="test.yaml",
            check_level=QualityCheckLevel.STANDARD,
        )

        prompt.set_request(request)

        with pytest.raises(ValueError, match="Request already set for this prompt"):
            prompt.set_request(request)

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-CRITERIA_SETTING")
    def test_criteria_setting(self):
        """基準設定テスト"""
        prompt = QualityCheckPrompt()
        criteria = get_standard_quality_criteria()[:3]  # 最初の3項目

        prompt.set_check_criteria(criteria)

        assert len(prompt.check_criteria) == 3
        assert prompt.check_criteria == criteria
        assert "criteria_set" in prompt.get_domain_events()

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-EMPTY_CRITERIA_VALID")
    def test_empty_criteria_validation(self):
        """空基準検証テスト"""
        prompt = QualityCheckPrompt()

        with pytest.raises(ValueError, match="Check criteria cannot be empty"):
            prompt.set_check_criteria([])

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-READY_FOR_GENERATION")
    def test_ready_for_generation_check(self):
        """生成準備完了チェック"""
        prompt = QualityCheckPrompt()
        assert not prompt.is_ready_for_generation()

        # 要求設定
        request = QualityCheckRequest(
            episode_number=1,
            project_name="Test Project",
            plot_file_path="test.yaml",
            check_level=QualityCheckLevel.STANDARD,
        )

        prompt.set_request(request)
        assert not prompt.is_ready_for_generation()

        # プロット設定（Mockを使用）
        mock_plot = Mock()
        prompt.set_episode_plot(mock_plot)
        assert not prompt.is_ready_for_generation()

        # 基準設定
        criteria = get_standard_quality_criteria()[:3]
        prompt.set_check_criteria(criteria)
        assert prompt.is_ready_for_generation()

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-PROMPT_GENERATION_WI")
    def test_prompt_generation_without_prerequisites(self):
        """前提条件なしプロンプト生成テスト"""
        prompt = QualityCheckPrompt()
        template = "Test template: {episode_number}"

        with pytest.raises(ValueError, match="Request must be set before generating prompt"):
            prompt.generate_prompt(template)

    @patch("noveler.domain.entities.quality_check_prompt.QualityCheckPrompt._build_quality_check_prompt")
    def test_prompt_generation_success(self, mock_build):
        """プロンプト生成成功テスト"""
        mock_build.return_value = "Generated prompt content"

        prompt = QualityCheckPrompt()

        # 必要な設定を完了
        request = QualityCheckRequest(
            episode_number=1,
            project_name="Test Project",
            plot_file_path="test.yaml",
            check_level=QualityCheckLevel.STANDARD,
        )

        prompt.set_request(request)

        mock_plot = Mock()
        prompt.set_episode_plot(mock_plot)

        criteria = get_standard_quality_criteria()[:3]
        prompt.set_check_criteria(criteria)

        # プロンプト生成実行
        template = "Test template"
        result = prompt.generate_prompt(template)

        assert result == "Generated prompt content"
        assert prompt.generated_prompt == "Generated prompt content"
        assert "prompt_generated" in prompt.get_domain_events()
        mock_build.assert_called_once_with(template)

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-DOMAIN_EVENTS_MANAGE")
    def test_domain_events_management(self):
        """ドメインイベント管理テスト"""
        prompt = QualityCheckPrompt()

        # 初期状態
        assert len(prompt.get_domain_events()) == 0

        # イベント発生
        request = QualityCheckRequest(
            episode_number=1,
            project_name="Test Project",
            plot_file_path="test.yaml",
            check_level=QualityCheckLevel.STANDARD,
        )

        prompt.set_request(request)

        events = prompt.get_domain_events()
        assert "request_set" in events

        # イベントクリア
        prompt.clear_domain_events()
        assert len(prompt.get_domain_events()) == 0

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-TO_DICT_CONVERSION")
    def test_to_dict_conversion(self):
        """辞書変換テスト"""
        prompt = QualityCheckPrompt()
        request = QualityCheckRequest(
            episode_number=1,
            project_name="Test Project",
            plot_file_path="test.yaml",
            check_level=QualityCheckLevel.STANDARD,
        )

        prompt.set_request(request)

        dict_data = prompt.to_dict()

        assert "prompt_id" in dict_data
        assert dict_data["request"]["episode_number"] == 1
        assert dict_data["request"]["project_name"] == "Test Project"
        assert dict_data["criteria_count"] == 0
        assert dict_data["has_result"] is False


@pytest.mark.spec("SPEC-STAGE5-SEPARATION")
class TestQualityCheckPromptGenerator:
    """品質チェックプロンプトジェネレーターのテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-GENERATOR_INITIALIZA")
    def test_generator_initialization(self):
        """ジェネレーター初期化テスト"""
        generator = QualityCheckPromptGenerator()

        assert generator._default_template is not None
        assert len(generator._default_template) > 0

    @patch("noveler.domain.entities.quality_check_prompt.EnhancedEpisodePlot")
    def test_plot_completeness_validation_success(self, mock_plot_class):
        """プロット完成度検証成功テスト"""
        generator = QualityCheckPromptGenerator()

        # 有効なプロットのMock作成
        mock_plot = Mock()
        mock_plot.episode_info.title = "Test Episode"
        mock_plot.episode_info.theme = "Test Theme"
        mock_plot.story_structure = Mock()
        mock_plot.foreshadowing_integration = "test"
        mock_plot.technical_elements = "test"
        mock_plot.thematic_elements = "test"

        result = generator.validate_plot_completeness(mock_plot)

        assert result.is_valid
        assert result.error_message is None

    @patch("noveler.domain.entities.quality_check_prompt.EnhancedEpisodePlot")
    def test_plot_completeness_validation_failure(self, mock_plot_class):
        """プロット完成度検証失敗テスト"""
        generator = QualityCheckPromptGenerator()

        # 不完全なプロットのMock作成
        mock_plot = Mock()
        mock_plot.episode_info = None  # 基本情報なし
        mock_plot.story_structure = None  # 構造なし

        result = generator.validate_plot_completeness(mock_plot)

        assert not result.is_valid
        assert "Episode info is missing" in result.error_message
        assert "Story structure is missing" in result.error_message

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-CRITERIA_SELECTION_B")
    def test_criteria_selection_by_level(self):
        """レベル別基準選択テスト"""
        generator = QualityCheckPromptGenerator()

        # 基本レベル
        basic_criteria = generator._select_criteria_by_level(QualityCheckLevel.BASIC)
        assert len(basic_criteria) == 5

        # 標準レベル
        standard_criteria = generator._select_criteria_by_level(QualityCheckLevel.STANDARD)
        assert len(standard_criteria) == 8

        # Claude最適化レベル
        claude_criteria = generator._select_criteria_by_level(QualityCheckLevel.CLAUDE_OPTIMIZED)
        assert len(claude_criteria) > 8  # 標準基準 + Claude特化基準

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-TEMPLATE_SELECTION_B")
    def test_template_selection_by_level(self):
        """レベル別テンプレート選択テスト"""
        generator = QualityCheckPromptGenerator()

        basic_template = generator._get_template_by_level(QualityCheckLevel.BASIC)
        standard_template = generator._get_template_by_level(QualityCheckLevel.STANDARD)
        comprehensive_template = generator._get_template_by_level(QualityCheckLevel.COMPREHENSIVE)
        claude_template = generator._get_template_by_level(QualityCheckLevel.CLAUDE_OPTIMIZED)

        assert "基本品質チェック" in basic_template
        assert "標準品質チェック" in standard_template
        assert "包括的品質チェック" in comprehensive_template
        assert "Claude Code最適化品質チェック" in claude_template

        # 各テンプレートが異なることを確認
        templates = [basic_template, standard_template, comprehensive_template, claude_template]
        assert len(set(templates)) == 4


@pytest.mark.spec("SPEC-STAGE5-SEPARATION")
class TestPlotValidationResult:
    """プロット検証結果のテスト"""

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-VALID_RESULT")
    def test_valid_result(self):
        """有効結果テスト"""
        result = PlotValidationResult(is_valid=True)

        assert result.is_valid
        assert result.error_message is None
        assert not result.has_warnings()

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-INVALID_RESULT_WITH_")
    def test_invalid_result_with_error(self):
        """エラー付き無効結果テスト"""
        result = PlotValidationResult(is_valid=False, error_message="Plot validation failed")

        assert not result.is_valid
        assert result.error_message == "Plot validation failed"

    @pytest.mark.spec("SPEC-QUALITY_CHECK_PROMPT-WARNING_MANAGEMENT")
    def test_warning_management(self):
        """警告管理テスト"""
        result = PlotValidationResult(is_valid=True)

        # 初期状態
        assert not result.has_warnings()
        assert len(result.warnings) == 0

        # 警告追加
        result.add_warning("Minor inconsistency detected")
        assert result.has_warnings()
        assert len(result.warnings) == 1
        assert "Minor inconsistency detected" in result.warnings

        # 複数警告
        result.add_warning("Another warning")
        assert len(result.warnings) == 2
