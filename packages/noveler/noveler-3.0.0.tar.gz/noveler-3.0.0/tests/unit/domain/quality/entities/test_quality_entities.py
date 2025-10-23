"""品質管理ドメインエンティティのテスト

TDD準拠テスト:
    - QualityViolation
- AdaptiveQualityEvaluator
- QualityAdaptationPolicy
- QualityReport


仕様書: SPEC-UNIT-TEST
"""

from datetime import datetime

import pytest
pytestmark = pytest.mark.quality_domain


from noveler.domain.quality.entities import (
    AdaptiveQualityEvaluator,
    QualityAdaptationPolicy,
    QualityReport,
    QualityViolation,
)
from noveler.domain.quality.value_objects import (
    AdaptationStrength,
    ErrorContext,
    ErrorSeverity,
    EvaluationContext,
    LineNumber,
    QualityScore,
    RuleCategory,
)


class TestQualityViolation:
    """QualityViolationのテストクラス"""

    @pytest.fixture
    def basic_violation(self) -> QualityViolation:
        """基本的な品質違反"""
        return QualityViolation(
            rule_name="test_rule",
            category=RuleCategory.BASIC_STYLE,
            severity=ErrorSeverity.WARNING,
            line_number=LineNumber(5),
            message="テスト違反です",
            context=ErrorContext("テストテキスト", 0, 4),
            suggestion="修正してください",
        )

    @pytest.fixture
    def critical_violation(self) -> QualityViolation:
        """重大な品質違反"""
        return QualityViolation(
            rule_name="critical_rule",
            category=RuleCategory.CONSISTENCY,
            severity=ErrorSeverity.ERROR,
            line_number=LineNumber(10),
            message="重大なエラーです",
            context=ErrorContext("エラーテキスト"),
        )

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-VIOLATION_CREATION_W")
    def test_violation_creation_with_defaults(self) -> None:
        """デフォルト値での違反作成テスト"""
        violation = QualityViolation()

        assert violation.id is not None
        assert violation.rule_name == ""
        assert violation.category == RuleCategory.BASIC_STYLE
        assert violation.severity == ErrorSeverity.WARNING
        assert violation.line_number is None
        assert violation.message == ""
        assert violation.context is None
        assert violation.suggestion is None

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-VIOLATION_CREATION_W")
    def test_violation_creation_with_values(self, basic_violation: QualityViolation) -> None:
        """値指定での違反作成テスト"""
        assert basic_violation.rule_name == "test_rule"
        assert basic_violation.category == RuleCategory.BASIC_STYLE
        assert basic_violation.severity == ErrorSeverity.WARNING
        assert basic_violation.line_number.value == 5
        assert basic_violation.message == "テスト違反です"
        assert basic_violation.suggestion == "修正してください"

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-IS_CRITICAL_TRUE")
    def test_is_critical_true(self, critical_violation: QualityViolation) -> None:
        """重大違反判定(True)テスト"""
        assert critical_violation.is_critical() is True

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-IS_CRITICAL_FALSE")
    def test_is_critical_false(self, basic_violation: QualityViolation) -> None:
        """重大違反判定(False)テスト"""
        assert basic_violation.is_critical() is False

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-IS_AUTO_FIXABLE_TRUE")
    def test_is_auto_fixable_true(self, basic_violation: QualityViolation) -> None:
        """自動修正可能判定(True)テスト"""
        assert basic_violation.is_auto_fixable() is True

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-IS_AUTO_FIXABLE_FALS")
    def test_is_auto_fixable_false(self, critical_violation: QualityViolation) -> None:
        """自動修正可能判定(False)テスト"""
        assert critical_violation.is_auto_fixable() is False

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_DISPLAY_MESSAGE_")
    def test_get_display_message_full(self, basic_violation: QualityViolation) -> None:
        """完全な表示メッセージ生成テスト"""
        display_message = basic_violation.get_display_message()

        assert "[warning] テスト違反です" in display_message
        assert "5行目" in display_message
        assert "問題箇所:" in display_message
        assert "修正案:" in display_message

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_DISPLAY_MESSAGE_")
    def test_get_display_message_minimal(self) -> None:
        """最小限の表示メッセージ生成テスト"""
        minimal_violation = QualityViolation(rule_name="minimal", message="最小限のメッセージ")

        display_message = minimal_violation.get_display_message()

        assert "[warning] 最小限のメッセージ" in display_message
        assert "問題箇所:" not in display_message
        assert "修正案:" not in display_message

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_DISPLAY_MESSAGE_")
    def test_get_display_message_with_highlighted_context(self) -> None:
        """ハイライト付きコンテキストの表示メッセージテスト"""
        violation_with_highlight = QualityViolation(
            rule_name="highlight_test",
            message="ハイライトテスト",
            context=ErrorContext("これは【エラー】テキストです", 3, 6),
        )

        display_message = violation_with_highlight.get_display_message()

        assert "問題箇所: これは【エラー】テキストです" in display_message


class TestAdaptiveQualityEvaluator:
    """AdaptiveQualityEvaluatorのテストクラス"""

    @pytest.fixture
    def basic_evaluator(self) -> AdaptiveQualityEvaluator:
        """基本的な適応的評価器"""
        return AdaptiveQualityEvaluator(
            project_id="test_project", learning_model_path="/path/to/model", is_trained=True
        )

    @pytest.fixture
    def untrained_evaluator(self) -> AdaptiveQualityEvaluator:
        """未訓練の評価器"""
        return AdaptiveQualityEvaluator(project_id="untrained_project")

    @pytest.fixture
    def evaluation_context(self) -> EvaluationContext:
        """評価コンテキスト"""
        return EvaluationContext(episode_number=1, chapter_number=1, genre="fantasy", viewpoint_type="first_person")

    @pytest.fixture
    def standard_scores(self) -> dict[str, QualityScore]:
        """標準スコア"""
        return {
            "readability": QualityScore(80.0),
            "dialogue_ratio": QualityScore(70.0),
            "narrative_depth": QualityScore(75.0),
        }

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-EVALUATOR_CREATION_D")
    def test_evaluator_creation_defaults(self) -> None:
        """デフォルト値での評価器作成テスト"""
        evaluator = AdaptiveQualityEvaluator()

        assert evaluator.evaluator_id is not None
        assert evaluator.project_id == ""
        assert evaluator.learning_model_path is None
        assert evaluator.current_policy is None
        assert evaluator.is_trained is False
        assert isinstance(evaluator.created_at, datetime)

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-EVALUATOR_CREATION_W")
    def test_evaluator_creation_with_values(self, basic_evaluator: AdaptiveQualityEvaluator) -> None:
        """値指定での評価器作成テスト"""
        assert basic_evaluator.project_id == "test_project"
        assert basic_evaluator.learning_model_path == "/path/to/model"
        assert basic_evaluator.is_trained is True

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-HAS_LEARNING_MODEL_T")
    def test_has_learning_model_true(self, basic_evaluator: AdaptiveQualityEvaluator) -> None:
        """学習モデル有無判定(True)テスト"""
        assert basic_evaluator.has_learning_model() is True

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-HAS_LEARNING_MODEL_F")
    def test_has_learning_model_false_no_path(self, untrained_evaluator: AdaptiveQualityEvaluator) -> None:
        """学習モデル有無判定(False・パスなし)テスト"""
        assert untrained_evaluator.has_learning_model() is False

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-HAS_LEARNING_MODEL_F")
    def test_has_learning_model_false_not_trained(self) -> None:
        """学習モデル有無判定(False・未訓練)テスト"""
        evaluator_not_trained = AdaptiveQualityEvaluator(
            project_id="test", learning_model_path="/path/to/model", is_trained=False
        )

        assert evaluator_not_trained.has_learning_model() is False

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-IS_READY_FOR_ADAPTIV")
    def test_is_ready_for_adaptive_evaluation_true(self, basic_evaluator: AdaptiveQualityEvaluator) -> None:
        """適応的評価準備完了判定(True)テスト"""
        assert basic_evaluator.is_ready_for_adaptive_evaluation() is True

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-IS_READY_FOR_ADAPTIV")
    def test_is_ready_for_adaptive_evaluation_false(self, untrained_evaluator: AdaptiveQualityEvaluator) -> None:
        """適応的評価準備完了判定(False)テスト"""
        assert untrained_evaluator.is_ready_for_adaptive_evaluation() is False

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-EVALUATE_ADAPTIVELY_")
    def test_evaluate_adaptively_not_ready(
        self,
        untrained_evaluator: AdaptiveQualityEvaluator,
        standard_scores: dict[str, QualityScore],
        evaluation_context: EvaluationContext,
    ) -> None:
        """適応的評価(準備未完了)テスト"""
        result = untrained_evaluator.evaluate_adaptively(standard_scores, evaluation_context)

        # 準備未完了なので標準スコアをそのまま返す
        assert result == standard_scores

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-EVALUATE_ADAPTIVELY_")
    def test_evaluate_adaptively_ready(
        self,
        basic_evaluator: AdaptiveQualityEvaluator,
        standard_scores: dict[str, QualityScore],
        evaluation_context: EvaluationContext,
    ) -> None:
        """適応的評価(準備完了)テスト"""
        # 適応ポリシーを設定
        policy = QualityAdaptationPolicy()
        policy.add_adaptation("readability", AdaptationStrength.STRONG)
        basic_evaluator.apply_adaptation_policy(policy)

        result = basic_evaluator.evaluate_adaptively(standard_scores, evaluation_context)

        # 適応的評価固有の情報が追加される
        assert "adaptation_confidence" in result
        assert "learning_source" in result
        assert result["learning_source"] == "project_specific_model"

        # スコアが調整される(強い適応で1.25倍)
        expected_readability = min(100.0, 80.0 * 1.25)
        assert result["readability"].value == expected_readability

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-APPLY_ADAPTATION_POL")
    def test_apply_adaptation_policy(self, basic_evaluator: AdaptiveQualityEvaluator) -> None:
        """適応ポリシー適用テスト"""
        policy = QualityAdaptationPolicy()

        basic_evaluator.apply_adaptation_policy(policy)

        assert basic_evaluator.current_policy == policy

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-HAS_ADAPTATION_POLIC")
    def test_has_adaptation_policy_true(self, basic_evaluator: AdaptiveQualityEvaluator) -> None:
        """適応ポリシー有無判定(True)テスト"""
        policy = QualityAdaptationPolicy()
        basic_evaluator.apply_adaptation_policy(policy)

        assert basic_evaluator.has_adaptation_policy() is True

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-HAS_ADAPTATION_POLIC")
    def test_has_adaptation_policy_false(self, basic_evaluator: AdaptiveQualityEvaluator) -> None:
        """適応ポリシー有無判定(False)テスト"""
        assert basic_evaluator.has_adaptation_policy() is False

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_ADAPTATION_STREN")
    def test_get_adaptation_strength_with_policy(self, basic_evaluator: AdaptiveQualityEvaluator) -> None:
        """ポリシー有りでの適応強度取得テスト"""
        policy = QualityAdaptationPolicy()
        policy.add_adaptation(
            "readability",
            AdaptationStrength.STRONG,
        )

        basic_evaluator.apply_adaptation_policy(policy)

        strength = basic_evaluator.get_adaptation_strength("readability")

        assert strength == AdaptationStrength.STRONG

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_ADAPTATION_STREN")
    def test_get_adaptation_strength_without_policy(self, basic_evaluator: AdaptiveQualityEvaluator) -> None:
        """ポリシーなしでの適応強度取得テスト"""
        strength = basic_evaluator.get_adaptation_strength("any_metric")

        assert strength == AdaptationStrength.WEAK

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-APPLY_ADAPTATION_SCO")
    def test_apply_adaptation_score_adjustment(
        self, basic_evaluator: AdaptiveQualityEvaluator, evaluation_context: EvaluationContext
    ) -> None:
        """適応強度によるスコア調整テスト"""
        test_cases = [
            (AdaptationStrength.WEAK, 80.0, 84.0),  # 1.05倍
            (AdaptationStrength.MODERATE, 80.0, 92.0),  # 1.15倍
            (AdaptationStrength.STRONG, 80.0, 100.0),  # 1.25倍(上限100)
        ]

        for strength, input_score, expected_score in test_cases:
            adjusted_score = basic_evaluator._apply_adaptation(input_score, strength, evaluation_context)
            assert adjusted_score == expected_score

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-APPLY_ADAPTATION_GEN")
    def test_apply_adaptation_genre_specific(self, basic_evaluator: AdaptiveQualityEvaluator) -> None:
        """ジャンル特化適応テスト"""
        context = EvaluationContext(
            episode_number=1, chapter_number=1, genre="body_swap_fantasy", viewpoint_type="character_consistency"
        )

        # body_swap_fantasy + character_consistency で追加の1.1倍
        adjusted_score = basic_evaluator._apply_adaptation(80.0, AdaptationStrength.STRONG, context)

        # 1.25 * 1.1 = 1.375倍
        expected_score = min(100.0, 80.0 * 1.25 * 1.1)
        assert adjusted_score == expected_score


class TestQualityAdaptationPolicy:
    """QualityAdaptationPolicyのテストクラス"""

    @pytest.fixture
    def basic_policy(self) -> QualityAdaptationPolicy:
        """基本的な適応ポリシー"""
        return QualityAdaptationPolicy(confidence_threshold=0.8)

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-POLICY_CREATION_DEFA")
    def test_policy_creation_defaults(self) -> None:
        """デフォルト値でのポリシー作成テスト"""
        policy = QualityAdaptationPolicy()

        assert policy.policy_id is not None
        assert policy.adaptations == {}
        assert policy.confidence_threshold == 0.7
        assert isinstance(policy.created_at, datetime)

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-POLICY_CREATION_WITH")
    def test_policy_creation_with_values(self, basic_policy: QualityAdaptationPolicy) -> None:
        """値指定でのポリシー作成テスト"""
        assert basic_policy.confidence_threshold == 0.8

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-ADD_ADAPTATION")
    def test_add_adaptation(self, basic_policy: QualityAdaptationPolicy) -> None:
        """適応設定追加テスト"""
        basic_policy.add_adaptation("readability", AdaptationStrength.STRONG)
        basic_policy.add_adaptation("dialogue_ratio", AdaptationStrength.MODERATE)

        assert basic_policy.adaptations["readability"] == AdaptationStrength.STRONG
        assert basic_policy.adaptations["dialogue_ratio"] == AdaptationStrength.MODERATE

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_ADAPTATION_STREN")
    def test_get_adaptation_strength_existing(self, basic_policy: QualityAdaptationPolicy) -> None:
        """既存メトリックの適応強度取得テスト"""
        basic_policy.add_adaptation("readability", AdaptationStrength.STRONG)

        strength = basic_policy.get_adaptation_strength("readability")

        assert strength == AdaptationStrength.STRONG

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_ADAPTATION_STREN")
    def test_get_adaptation_strength_nonexistent(self, basic_policy: QualityAdaptationPolicy) -> None:
        """存在しないメトリックの適応強度取得テスト"""
        strength = basic_policy.get_adaptation_strength("nonexistent_metric")

        assert strength == AdaptationStrength.WEAK

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-IS_APPLICABLE_TRUE")
    def test_is_applicable_true(self, basic_policy: QualityAdaptationPolicy) -> None:
        """適用可能判定(True)テスト"""
        # confidence_threshold=0.8, 信頼度0.9
        assert basic_policy.is_applicable(0.9) is True

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-IS_APPLICABLE_FALSE")
    def test_is_applicable_false(self, basic_policy: QualityAdaptationPolicy) -> None:
        """適用可能判定(False)テスト"""
        # confidence_threshold=0.8, 信頼度0.7
        assert basic_policy.is_applicable(0.7) is False

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-IS_APPLICABLE_EQUAL_")
    def test_is_applicable_equal_threshold(self, basic_policy: QualityAdaptationPolicy) -> None:
        """適用可能判定(閾値と同値)テスト"""
        # confidence_threshold=0.8, 信頼度0.8
        assert basic_policy.is_applicable(0.8) is True

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_COVERAGE_METRICS")
    def test_get_coverage_metrics(self, basic_policy: QualityAdaptationPolicy) -> None:
        """カバーメトリック一覧取得テスト"""
        basic_policy.add_adaptation("readability", AdaptationStrength.STRONG)
        basic_policy.add_adaptation("dialogue_ratio", AdaptationStrength.MODERATE)
        basic_policy.add_adaptation("narrative_depth", AdaptationStrength.WEAK)

        coverage_metrics = basic_policy.get_coverage_metrics()

        expected_metrics = ["readability", "dialogue_ratio", "narrative_depth"]
        assert set(coverage_metrics) == set(expected_metrics)

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_COVERAGE_METRICS")
    def test_get_coverage_metrics_empty(self, basic_policy: QualityAdaptationPolicy) -> None:
        """空のカバーメトリック取得テスト"""
        coverage_metrics = basic_policy.get_coverage_metrics()

        assert coverage_metrics == []


class TestQualityReport:
    """QualityReportのテストクラス"""

    @pytest.fixture
    def basic_report(self) -> QualityReport:
        """基本的な品質レポート"""
        return QualityReport(episode_id="episode_001")

    @pytest.fixture
    def sample_violations(self) -> list[QualityViolation]:
        """サンプル違反リスト"""
        return [
            QualityViolation(
                rule_name="error_rule",
                category=RuleCategory.BASIC_STYLE,
                severity=ErrorSeverity.ERROR,
                message="エラー違反",
            ),
            QualityViolation(
                rule_name="warning_rule",
                category=RuleCategory.COMPOSITION,
                severity=ErrorSeverity.WARNING,
                message="警告違反",
                suggestion="修正案",
            ),
            QualityViolation(
                rule_name="info_rule",
                category=RuleCategory.READABILITY,
                severity=ErrorSeverity.INFO,
                message="情報違反",
            ),
        ]

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-REPORT_CREATION_DEFA")
    def test_report_creation_defaults(self) -> None:
        """デフォルト値でのレポート作成テスト"""
        report = QualityReport()

        assert report.id is not None
        assert report.episode_id == ""
        assert isinstance(report.created_at, datetime)
        assert report.violations == []
        assert report.auto_fixed_count == 0

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-REPORT_CREATION_WITH")
    def test_report_creation_with_values(self, basic_report: QualityReport) -> None:
        """値指定でのレポート作成テスト"""
        assert basic_report.episode_id == "episode_001"

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-ADD_VIOLATION")
    def test_add_violation(self, basic_report: QualityReport, sample_violations: list[QualityViolation]) -> None:
        """違反追加テスト"""
        for violation in sample_violations:
            basic_report.add_violation(violation)

        assert len(basic_report.violations) == 3
        assert basic_report.violations == sample_violations

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_VIOLATIONS_BY_SE")
    def test_get_violations_by_severity(
        self, basic_report: QualityReport, sample_violations: list[QualityViolation]
    ) -> None:
        """重要度別違反取得テスト"""
        for violation in sample_violations:
            basic_report.add_violation(violation)

        error_violations = basic_report.get_violations_by_severity(ErrorSeverity.ERROR)
        warning_violations = basic_report.get_violations_by_severity(ErrorSeverity.WARNING)
        info_violations = basic_report.get_violations_by_severity(ErrorSeverity.INFO)

        assert len(error_violations) == 1
        assert error_violations[0].rule_name == "error_rule"

        assert len(warning_violations) == 1
        assert warning_violations[0].rule_name == "warning_rule"

        assert len(info_violations) == 1
        assert info_violations[0].rule_name == "info_rule"

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_VIOLATIONS_BY_CA")
    def test_get_violations_by_category(
        self, basic_report: QualityReport, sample_violations: list[QualityViolation]
    ) -> None:
        """カテゴリー別違反取得テスト"""
        for violation in sample_violations:
            basic_report.add_violation(violation)

        basic_style_violations = basic_report.get_violations_by_category(RuleCategory.BASIC_STYLE)
        composition_violations = basic_report.get_violations_by_category(RuleCategory.COMPOSITION)
        readability_violations = basic_report.get_violations_by_category(RuleCategory.READABILITY)

        assert len(basic_style_violations) == 1
        assert basic_style_violations[0].rule_name == "error_rule"

        assert len(composition_violations) == 1
        assert composition_violations[0].rule_name == "warning_rule"

        assert len(readability_violations) == 1
        assert readability_violations[0].rule_name == "info_rule"

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_CRITICAL_VIOLATI")
    def test_get_critical_violations(
        self, basic_report: QualityReport, sample_violations: list[QualityViolation]
    ) -> None:
        """重大違反取得テスト"""
        for violation in sample_violations:
            basic_report.add_violation(violation)

        critical_violations = basic_report.get_critical_violations()

        assert len(critical_violations) == 1
        assert critical_violations[0].rule_name == "error_rule"

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_AUTO_FIXABLE_VIO")
    def test_get_auto_fixable_violations(
        self, basic_report: QualityReport, sample_violations: list[QualityViolation]
    ) -> None:
        """自動修正可能違反取得テスト"""
        for violation in sample_violations:
            basic_report.add_violation(violation)

        auto_fixable_violations = basic_report.get_auto_fixable_violations()

        assert len(auto_fixable_violations) == 1
        assert auto_fixable_violations[0].rule_name == "warning_rule"

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-CALCULATE_SCORE_NO_V")
    def test_calculate_score_no_violations(self, basic_report: QualityReport) -> None:
        """違反なしでのスコア計算テスト"""
        score = basic_report.calculate_score()

        assert score.value == 100.0

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-CALCULATE_SCORE_WITH")
    def test_calculate_score_with_violations(
        self, basic_report: QualityReport, sample_violations: list[QualityViolation]
    ) -> None:
        """違反ありでのスコア計算テスト"""
        for violation in sample_violations:
            basic_report.add_violation(violation)

        score = basic_report.calculate_score()

        # ERROR: -10, WARNING: -3, INFO: -1 → 100 - 10 - 3 - 1 = 86
        assert score.value == 86.0

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-CALCULATE_SCORE_MINI")
    def test_calculate_score_minimum_zero(self, basic_report: QualityReport) -> None:
        """スコア下限ゼロのテスト"""
        # 大量のエラー違反を追加(100点を超える減点)
        for _ in range(15):
            error_violation = QualityViolation(rule_name=f"error_{_}", severity=ErrorSeverity.ERROR, message="エラー")
            basic_report.add_violation(error_violation)

        score = basic_report.calculate_score()

        # 15 * 10 = 150点減点だが、下限は0
        assert score.value == 0.0

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_SUMMARY")
    def test_get_summary(self, basic_report: QualityReport, sample_violations: list[QualityViolation]) -> None:
        """サマリー情報取得テスト"""
        for violation in sample_violations:
            basic_report.add_violation(violation)

        basic_report.auto_fixed_count = 2

        summary = basic_report.get_summary()

        assert summary["total_violations"] == 3
        assert summary["errors"] == 1
        assert summary["warnings"] == 1
        assert summary["info"] == 1
        assert summary["auto_fixable"] == 1
        assert summary["auto_fixed"] == 2

    @pytest.mark.spec("SPEC-QUALITY_ENTITIES-GET_SUMMARY_EMPTY_RE")
    def test_get_summary_empty_report(self, basic_report: QualityReport) -> None:
        """空レポートのサマリー取得テスト"""
        summary = basic_report.get_summary()

        assert summary["total_violations"] == 0
        assert summary["errors"] == 0
        assert summary["warnings"] == 0
        assert summary["info"] == 0
        assert summary["auto_fixable"] == 0
        assert summary["auto_fixed"] == 0
