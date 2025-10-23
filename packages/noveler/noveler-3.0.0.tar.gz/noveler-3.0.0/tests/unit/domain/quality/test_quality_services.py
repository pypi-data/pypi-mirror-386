"""品質管理ドメインサービスのテスト

TDD準拠テスト:
    - TextQualityChecker
- QualityReportGenerator
- QualityAdaptationService
"""

from unittest.mock import Mock

import pytest

from noveler.domain.quality.entities import (
    QualityAdaptationPolicy,
    QualityReport,
    QualityViolation,
)
from noveler.domain.quality.services import (
    QualityAdaptationService,
    QualityReportGenerator,
    TextQualityChecker,
)
from noveler.domain.quality.value_objects import (
    AdaptationStrength,
    ErrorContext,
    ErrorSeverity,
    LineNumber,
    QualityScore,
    RuleCategory,
)


class TestTextQualityChecker:
    """TextQualityCheckerのテストクラス"""

    @pytest.fixture
    def mock_proper_noun_repository(self) -> Mock:
        """固有名詞リポジトリのモック"""
        mock = Mock()
        mock.get_all_by_project.return_value = ["キャラクター名", "地名"]
        return mock

    @pytest.fixture
    def text_checker(self, mock_proper_noun_repository: Mock) -> TextQualityChecker:
        """テキスト品質チェッカーのインスタンス"""
        return TextQualityChecker(mock_proper_noun_repository)

    @pytest.mark.spec("SPEC-QUALITY-001")
    @pytest.mark.requirement("REQ-2.1.1")
    def test_check_basic_style_consecutive_punctuation(self, text_checker: TextQualityChecker) -> None:
        """連続句読点チェックテスト

        仕様書: specs/SPEC-QUALITY-001_quality_check_system.md
        要件: 連続する同一表現を検出
        """
        text_with_consecutive = "これは文です。。\nこちらも文です、、"

        violations = text_checker.check_basic_style(text_with_consecutive, "test_project")

        # 連続句読点が2箇所で検出される
        consecutive_violations = [v for v in violations if v.rule_name == "consecutive_punctuation"]
        assert len(consecutive_violations) == 2

        # 各違反の詳細チェック
        first_violation = consecutive_violations[0]
        assert first_violation.category == RuleCategory.BASIC_STYLE
        assert first_violation.severity == ErrorSeverity.WARNING
        assert first_violation.line_number.value == 1
        assert "連続した句読点があります" in first_violation.message

    @pytest.mark.spec("SPEC-QUALITY-001")
    @pytest.mark.requirement("REQ-2.1.3")
    def test_check_basic_style_missing_space_after_exclamation(self, text_checker: TextQualityChecker) -> None:
        """感嘆符・疑問符後のスペースチェックテスト

        仕様書: specs/SPEC-QUALITY-001_quality_check_system.md
        要件: 不適切な文末表現を検出
        """
        text_with_missing_space = "すごい!本当に?そうです"

        violations = text_checker.check_basic_style(text_with_missing_space, "test_project")

        # スペース不足が2箇所で検出される
        space_violations = [v for v in violations if v.rule_name == "missing_space_after_exclamation"]
        assert len(space_violations) == 2

        # 詳細チェック
        first_violation = space_violations[0]
        assert first_violation.severity == ErrorSeverity.WARNING
        assert "感嘆符・疑問符の後に全角スペースが必要です" in first_violation.message
        assert "全角スペースを追加" in first_violation.suggestion

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CHECK_BASIC_STYLE_IN")
    def test_check_basic_style_invalid_ellipsis(
        self, text_checker: TextQualityChecker, mock_proper_noun_repository: Mock
    ) -> None:
        """三点リーダーチェックテスト"""
        text_with_ellipsis = "彼は言った...「そうですね…」"
        mock_proper_noun_repository.get_all_by_project.return_value = []  # 固有名詞なし

        violations = text_checker.check_basic_style(text_with_ellipsis, "test_project")

        # 三点リーダー違反が検出される
        ellipsis_violations = [v for v in violations if v.rule_name == "invalid_ellipsis"]
        assert len(ellipsis_violations) >= 1

        # 詳細チェック
        violation = ellipsis_violations[0]
        assert violation.severity == ErrorSeverity.WARNING
        assert "三点リーダーは「……」を使用してください" in violation.message
        assert "……" in violation.suggestion

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CHECK_BASIC_STYLE_EL")
    def test_check_basic_style_ellipsis_with_proper_noun(
        self, text_checker: TextQualityChecker, mock_proper_noun_repository: Mock
    ) -> None:
        """固有名詞に含まれる三点リーダーは除外テスト"""
        text_with_proper_noun_ellipsis = "キャラ...の名前です"
        mock_proper_noun_repository.get_all_by_project.return_value = ["キャラ..."]

        violations = text_checker.check_basic_style(text_with_proper_noun_ellipsis, "test_project")

        # 固有名詞の三点リーダーは違反として検出されない
        ellipsis_violations = [v for v in violations if v.rule_name == "invalid_ellipsis"]
        assert len(ellipsis_violations) == 0

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CHECK_BASIC_STYLE_NO")
    def test_check_basic_style_no_violations(self, text_checker: TextQualityChecker) -> None:
        """違反なしテキストのテスト"""
        clean_text = "これは正しい文です。\n「こんにちは」と彼は言った。"

        violations = text_checker.check_basic_style(clean_text, "test_project")

        assert len(violations) == 0

    @pytest.mark.spec("SPEC-QUALITY-001")
    @pytest.mark.requirement("REQ-2.2.1")
    def test_check_composition_missing_indentation(self, text_checker: TextQualityChecker) -> None:
        """段落頭字下げチェックテスト

        仕様書: specs/SPEC-QUALITY-001_quality_check_system.md
        要件: 章の構成バランスを評価(SPEC-QUALITY-002の要件)
        """
        text_without_indentation = "これは字下げなしの段落です。\n これは正しい段落です。\n「会話文は字下げ不要です」\n# 見出しも字下げ不要\nまた字下げなしです。"

        violations = text_checker.check_composition(text_without_indentation)

        # 字下げなしが2箇所で検出される
        indentation_violations = [v for v in violations if v.rule_name == "missing_indentation"]
        assert len(indentation_violations) == 2

        # 詳細チェック
        first_violation = indentation_violations[0]
        assert first_violation.category == RuleCategory.COMPOSITION
        assert first_violation.severity == ErrorSeverity.INFO
        assert "段落頭に全角スペースがありません" in first_violation.message
        assert first_violation.suggestion.startswith(" ")

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CHECK_COMPOSITION_PR")
    def test_check_composition_proper_formatting(self, text_checker: TextQualityChecker) -> None:
        """正しい構成フォーマットのテスト"""
        properly_formatted = " これは正しい段落です。\n「会話文です」\n# 見出し\n もう一つの段落です。"

        violations = text_checker.check_composition(properly_formatted)

        assert len(violations) == 0

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CHECK_COMPOSITION_EM")
    def test_check_composition_empty_lines(self, text_checker: TextQualityChecker) -> None:
        """空行処理のテスト"""
        text_with_empty_lines = " 正しい段落。\n\n 次の段落。\n   \n 最後の段落。"

        violations = text_checker.check_composition(text_with_empty_lines)

        # 空行は違反として検出されない
        assert len(violations) == 0

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CALCULATE_READABILIT")
    def test_calculate_readability_score_short_sentences(self, text_checker: TextQualityChecker) -> None:
        """短文での読みやすさスコア計算テスト"""
        short_text = "短い。文です。読みやすい。"

        score = text_checker.calculate_readability_score(short_text)

        # 短文なので高スコア
        assert score.value == 90.0

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CALCULATE_READABILIT")
    def test_calculate_readability_score_medium_sentences(self, text_checker: TextQualityChecker) -> None:
        """中程度文での読みやすさスコア計算テスト"""
        medium_text = "これは中程度の長さの文章で、ある程度の長さを持っています。もう一つの文も同様の長さです。"

        score = text_checker.calculate_readability_score(medium_text)

        # 中程度の長さなので中程度のスコア
        assert score.value in [70.0, 80.0]  # 計算結果によって変動

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CALCULATE_READABILIT")
    def test_calculate_readability_score_long_sentences(self, text_checker: TextQualityChecker) -> None:
        """長文での読みやすさスコア計算テスト"""
        long_text = "これは非常に長い文章で、複数の節を含み、読者にとって理解が困難になる可能性があり、さらに詳細な説明を加えることで文章の長さが増し、最終的に読みにくくなってしまう可能性があります。"

        score = text_checker.calculate_readability_score(long_text)

        # 長文なので低スコア
        assert score.value == 60.0

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CALCULATE_READABILIT")
    def test_calculate_readability_score_no_periods(self, text_checker: TextQualityChecker) -> None:
        """句点なしテキストの読みやすさスコア計算テスト"""
        no_period_text = "句点がないテキストです"

        score = text_checker.calculate_readability_score(no_period_text)

        # 句点がない場合でも計算される(ゼロ除算回避)
        assert isinstance(score, QualityScore)
        assert 0 <= score.value <= 100


class TestQualityReportGenerator:
    """QualityReportGeneratorのテストクラス"""

    @pytest.fixture
    def report_generator(self) -> QualityReportGenerator:
        """品質レポート生成器のインスタンス"""
        return QualityReportGenerator()

    @pytest.fixture
    def sample_violations(self) -> list[QualityViolation]:
        """サンプル違反リスト"""
        return [
            QualityViolation(
                rule_name="test_rule_1",
                category=RuleCategory.BASIC_STYLE,
                severity=ErrorSeverity.ERROR,
                line_number=LineNumber(1),
                message="エラーテスト",
                context=ErrorContext("テストテキスト"),
                suggestion="修正案",
            ),
            QualityViolation(
                rule_name="test_rule_2",
                category=RuleCategory.COMPOSITION,
                severity=ErrorSeverity.WARNING,
                line_number=LineNumber(2),
                message="警告テスト",
                context=ErrorContext("テストテキスト2"),
            ),
        ]

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-GENERATE_REPORT_BASI")
    def test_generate_report_basic(
        self, report_generator: QualityReportGenerator, sample_violations: list[QualityViolation]
    ) -> None:
        """基本的なレポート生成テスト"""
        episode_id = "test_episode_001"

        report = report_generator.generate_report(episode_id, sample_violations)

        assert isinstance(report, QualityReport)
        assert report.episode_id == episode_id
        assert len(report.violations) == len(sample_violations)
        assert report.violations == sample_violations

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-GENERATE_REPORT_EMPT")
    def test_generate_report_empty_violations(self, report_generator: QualityReportGenerator) -> None:
        """違反なしでのレポート生成テスト"""
        episode_id = "test_episode_002"

        report = report_generator.generate_report(episode_id, [])

        assert report.episode_id == episode_id
        assert len(report.violations) == 0

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-MERGE_REPORTS_MULTIP")
    def test_merge_reports_multiple(
        self, report_generator: QualityReportGenerator, sample_violations: list[QualityViolation]
    ) -> None:
        """複数レポートのマージテスト"""
        episode_id = "test_episode_003"

        # 複数のレポートを作成
        report1 = report_generator.generate_report(episode_id, [sample_violations[0]])
        report2 = report_generator.generate_report(episode_id, [sample_violations[1]])

        merged_report = report_generator.merge_reports([report1, report2])

        assert merged_report.episode_id == episode_id
        assert len(merged_report.violations) == 2
        # 両方の違反が含まれている
        rule_names = [v.rule_name for v in merged_report.violations]
        assert "test_rule_1" in rule_names
        assert "test_rule_2" in rule_names

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-MERGE_REPORTS_SINGLE")
    def test_merge_reports_single(
        self, report_generator: QualityReportGenerator, sample_violations: list[QualityViolation]
    ) -> None:
        """単一レポートのマージテスト"""
        episode_id = "test_episode_004"
        report = report_generator.generate_report(episode_id, sample_violations)

        merged_report = report_generator.merge_reports([report])

        assert merged_report.episode_id == episode_id
        assert len(merged_report.violations) == len(sample_violations)

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-MERGE_REPORTS_EMPTY_")
    def test_merge_reports_empty_list(self, report_generator: QualityReportGenerator) -> None:
        """空リストでのマージテスト"""
        with pytest.raises(ValueError, match="マージするレポートがありません"):
            report_generator.merge_reports([])

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-MERGE_REPORTS_DIFFER")
    def test_merge_reports_different_episodes(
        self, report_generator: QualityReportGenerator, sample_violations: list[QualityViolation]
    ) -> None:
        """異なるエピソードIDのレポートマージテスト"""
        report1 = report_generator.generate_report("episode_1", [sample_violations[0]])
        report2 = report_generator.generate_report("episode_2", [sample_violations[1]])

        # 最初のレポートのIDが使用される
        merged_report = report_generator.merge_reports([report1, report2])

        assert merged_report.episode_id == "episode_1"
        assert len(merged_report.violations) == 2


class TestQualityAdaptationService:
    """QualityAdaptationServiceのテストクラス"""

    @pytest.fixture
    def adaptation_service(self) -> QualityAdaptationService:
        """品質適応サービスのインスタンス"""
        return QualityAdaptationService()

    @pytest.fixture
    def mock_learned_evaluator(self) -> Mock:
        """学習済み評価器のモック"""
        mock = Mock()
        mock.project_id = "test_project_123"
        return mock

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-GENERATE_PROJECT_ADA")
    def test_generate_project_adaptation_high_episode_count(
        self, adaptation_service: QualityAdaptationService, mock_learned_evaluator: Mock
    ) -> None:
        """高エピソード数でのプロジェクト適応生成テスト"""
        episode_count = 35
        genre = "fantasy"

        policy = adaptation_service.generate_project_adaptation(mock_learned_evaluator, episode_count, genre)

        assert isinstance(policy, QualityAdaptationPolicy)
        assert policy.policy_id.startswith("test_project_123_adaptation_35")
        # 高エピソード数なので高い信頼度しきい値
        assert policy.confidence_threshold == 0.8

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-GENERATE_PROJECT_ADA")
    def test_generate_project_adaptation_medium_episode_count(
        self, adaptation_service: QualityAdaptationService, mock_learned_evaluator: Mock
    ) -> None:
        """中程度エピソード数での適応生成テスト"""
        episode_count = 20
        genre = "romance"

        policy = adaptation_service.generate_project_adaptation(mock_learned_evaluator, episode_count, genre)

        # 中程度エピソード数なので中間の信頼度しきい値
        assert policy.confidence_threshold == 0.7

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-GENERATE_PROJECT_ADA")
    def test_generate_project_adaptation_low_episode_count(
        self, adaptation_service: QualityAdaptationService, mock_learned_evaluator: Mock
    ) -> None:
        """低エピソード数での適応生成テスト"""
        episode_count = 5
        genre = "mystery"

        policy = adaptation_service.generate_project_adaptation(mock_learned_evaluator, episode_count, genre)

        # 低エピソード数なので低い信頼度しきい値
        assert policy.confidence_threshold == 0.6

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-GENERATE_PROJECT_ADA")
    def test_generate_project_adaptation_body_swap_fantasy_genre(
        self, adaptation_service: QualityAdaptationService, mock_learned_evaluator: Mock
    ) -> None:
        """入れ替わりファンタジージャンルでの適応生成テスト"""
        episode_count = 25
        genre = "body_swap_fantasy"

        policy = adaptation_service.generate_project_adaptation(mock_learned_evaluator, episode_count, genre)

        # ジャンル特化適応が設定される
        assert policy.get_adaptation_strength("character_consistency") == AdaptationStrength.STRONG
        assert policy.get_adaptation_strength("viewpoint_clarity") == AdaptationStrength.STRONG
        assert policy.get_adaptation_strength("dialogue_ratio") == AdaptationStrength.MODERATE

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-GENERATE_PROJECT_ADA")
    def test_generate_project_adaptation_sf_romance_genre(
        self, adaptation_service: QualityAdaptationService, mock_learned_evaluator: Mock
    ) -> None:
        """SFロマンスジャンルでの適応生成テスト"""
        episode_count = 15
        genre = "sf_romance"

        policy = adaptation_service.generate_project_adaptation(mock_learned_evaluator, episode_count, genre)

        # SF ロマンス特化適応が設定される
        assert policy.get_adaptation_strength("technical_accuracy") == AdaptationStrength.STRONG
        assert policy.get_adaptation_strength("emotional_depth") == AdaptationStrength.MODERATE

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-GENERATE_PROJECT_ADA")
    def test_generate_project_adaptation_generic_genre(
        self, adaptation_service: QualityAdaptationService, mock_learned_evaluator: Mock
    ) -> None:
        """一般ジャンルでの適応生成テスト"""
        episode_count = 20
        genre = "slice_of_life"

        policy = adaptation_service.generate_project_adaptation(mock_learned_evaluator, episode_count, genre)

        # 汎用適応が設定される
        assert policy.get_adaptation_strength("readability") == AdaptationStrength.MODERATE
        assert policy.get_adaptation_strength("dialogue_ratio") == AdaptationStrength.WEAK

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CALCULATE_ADAPTATION")
    def test_calculate_adaptation_strength_strong_conditions(
        self, adaptation_service: QualityAdaptationService
    ) -> None:
        """強い適応条件での強度計算テスト"""
        learning_data = {"readability_variance": 0.3, "reader_satisfaction_correlation": 0.8, "episode_count": 25}

        strength = adaptation_service.calculate_adaptation_strength("readability", learning_data)

        assert strength == AdaptationStrength.STRONG

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CALCULATE_ADAPTATION")
    def test_calculate_adaptation_strength_moderate_conditions(
        self, adaptation_service: QualityAdaptationService
    ) -> None:
        """中程度適応条件での強度計算テスト"""
        learning_data = {"dialogue_ratio_variance": 0.15, "reader_satisfaction_correlation": 0.6, "episode_count": 12}

        strength = adaptation_service.calculate_adaptation_strength("dialogue_ratio", learning_data)

        assert strength == AdaptationStrength.MODERATE

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CALCULATE_ADAPTATION")
    def test_calculate_adaptation_strength_weak_conditions(self, adaptation_service: QualityAdaptationService) -> None:
        """弱い適応条件での強度計算テスト"""
        learning_data = {"narrative_depth_variance": 0.05, "reader_satisfaction_correlation": 0.3, "episode_count": 5}

        strength = adaptation_service.calculate_adaptation_strength("narrative_depth", learning_data)

        assert strength == AdaptationStrength.WEAK

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CALCULATE_ADAPTATION")
    def test_calculate_adaptation_strength_insufficient_data(
        self, adaptation_service: QualityAdaptationService
    ) -> None:
        """データ不足での強度計算テスト"""
        learning_data = {
            "episode_count": 2  # 他のデータが不足
        }

        strength = adaptation_service.calculate_adaptation_strength("any_metric", learning_data)

        assert strength == AdaptationStrength.WEAK

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CALCULATE_ADAPTATION")
    def test_calculate_adaptation_strength_mixed_conditions(self, adaptation_service: QualityAdaptationService) -> None:
        """混合条件での強度計算テスト"""
        learning_data = {
            "emotional_intensity_variance": 0.25,  # 強い条件
            "reader_satisfaction_correlation": 0.4,  # 弱い条件
            "episode_count": 30,  # 強い条件
        }

        strength = adaptation_service.calculate_adaptation_strength("emotional_intensity", learning_data)

        # 一つでも条件を満たさないと弱くなる
        assert strength == AdaptationStrength.WEAK

    @pytest.mark.spec("SPEC-QUALITY_SERVICES-CALCULATE_ADAPTATION")
    def test_calculate_adaptation_strength_edge_case_values(self, adaptation_service: QualityAdaptationService) -> None:
        """境界値での強度計算テスト"""
        # 中程度の境界値
        learning_data = {
            "test_metric_variance": 0.1,  # 境界値
            "reader_satisfaction_correlation": 0.5,  # 境界値
            "episode_count": 10,  # 境界値
        }

        strength = adaptation_service.calculate_adaptation_strength("test_metric", learning_data)

        assert strength == AdaptationStrength.MODERATE
