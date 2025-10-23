"""品質評価サービスのテスト

DDD準拠テスト:
    - ビジネスロジックのテスト
- 重み付け計算の検証
- グレード判定の動作確認


仕様書: SPEC-DOMAIN-SERVICES
"""

import pytest

from noveler.domain.entities.quality_check_session import (
    CheckType,
    QualityCheckResult,
    QualityGrade,
    QualityIssue,
    QualityScore,
    Severity,
)
from noveler.domain.services.quality_evaluation_service import QualityEvaluationService


class TestQualityEvaluationService:
    """QualityEvaluationServiceのテスト"""

    @pytest.fixture
    def service(self):
        """サービスインスタンス"""
        return QualityEvaluationService()

    @pytest.fixture
    def service_with_custom_weights(self):
        """カスタム重み設定のサービス"""
        custom_weights = {
            CheckType.BASIC_STYLE: 0.4,
            CheckType.COMPOSITION: 0.3,
            CheckType.CHARACTER_CONSISTENCY: 0.2,
            CheckType.READABILITY: 0.1,
        }
        return QualityEvaluationService(custom_weights)

    @pytest.fixture
    def sample_check_results(self):
        """サンプルのチェック結果"""

        return [
            QualityCheckResult(
                check_type=CheckType.BASIC_STYLE,
                score=QualityScore(85.0),
                issues=[
                    QualityIssue(type="style", message="エラー1", severity=Severity.ERROR),
                    QualityIssue(type="style", message="エラー2", severity=Severity.ERROR),
                    QualityIssue(type="style", message="警告1", severity=Severity.WARNING),
                    QualityIssue(type="style", message="警告2", severity=Severity.WARNING),
                    QualityIssue(type="style", message="警告3", severity=Severity.WARNING),
                ],
            ),
            QualityCheckResult(
                check_type=CheckType.COMPOSITION,
                score=QualityScore(75.0),
                issues=[
                    QualityIssue(type="composition", message="構成エラー1", severity=Severity.ERROR),
                    QualityIssue(type="composition", message="構成エラー2", severity=Severity.ERROR),
                    QualityIssue(type="composition", message="構成エラー3", severity=Severity.ERROR),
                    QualityIssue(type="composition", message="構成エラー4", severity=Severity.ERROR),
                    QualityIssue(type="composition", message="構成エラー5", severity=Severity.ERROR),
                    QualityIssue(type="composition", message="構成警告1", severity=Severity.WARNING),
                ],
            ),
            QualityCheckResult(
                check_type=CheckType.CHARACTER_CONSISTENCY,
                score=QualityScore(90.0),
                issues=[
                    QualityIssue(type="character", message="キャラ警告1", severity=Severity.WARNING),
                    QualityIssue(type="character", message="キャラ警告2", severity=Severity.WARNING),
                ],
            ),
            QualityCheckResult(
                check_type=CheckType.READABILITY,
                score=QualityScore(70.0),
                issues=[
                    QualityIssue(type="readability", message="読みやすさエラー1", severity=Severity.ERROR),
                    QualityIssue(type="readability", message="読みやすさエラー2", severity=Severity.ERROR),
                    QualityIssue(type="readability", message="読みやすさエラー3", severity=Severity.ERROR),
                    QualityIssue(type="readability", message="読みやすさ警告1", severity=Severity.WARNING),
                    QualityIssue(type="readability", message="読みやすさ警告2", severity=Severity.WARNING),
                    QualityIssue(type="readability", message="読みやすさ警告3", severity=Severity.WARNING),
                    QualityIssue(type="readability", message="読みやすさ警告4", severity=Severity.WARNING),
                ],
            ),
        ]

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-INIT_DEFAULT_WEIGHTS")
    def test_init_default_weights(self, service: object) -> None:
        """デフォルト重みでの初期化テスト"""
        assert service.weights == QualityEvaluationService.DEFAULT_WEIGHTS
        assert sum(service.weights.values()) == pytest.approx(1.0, rel=1e-9)

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-INIT_CUSTOM_WEIGHTS")
    def test_init_custom_weights(self, service_with_custom_weights: object) -> None:
        """カスタム重みでの初期化テスト"""
        expected_weights = {
            CheckType.BASIC_STYLE: 0.4,
            CheckType.COMPOSITION: 0.3,
            CheckType.CHARACTER_CONSISTENCY: 0.2,
            CheckType.READABILITY: 0.1,
        }
        assert service_with_custom_weights.weights == expected_weights

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-CALCULATE_WEIGHTED_S")
    def test_calculate_weighted_score_normal(self, service: object, sample_check_results: object) -> None:
        """正常な重み付けスコア計算テスト"""
        score = service.calculate_weighted_score(sample_check_results)

        # 手動計算:
        # BASIC_STYLE: 85 * 0.25 = 21.25
        # COMPOSITION: 75 * 0.25 = 18.75
        # CHARACTER_CONSISTENCY: 90 * 0.20 = 18.0
        # READABILITY: 70 * 0.20 = 14.0
        # 合計: 72.0
        # 重みの合計: 0.25 + 0.25 + 0.20 + 0.20 = 0.90
        # 重み付け平均: 72.0 / 0.90 = 80.0
        expected = (85 * 0.25 + 75 * 0.25 + 90 * 0.20 + 70 * 0.20) / 0.90
        assert score.value == pytest.approx(expected, rel=1e-2)

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-CALCULATE_WEIGHTED_S")
    def test_calculate_weighted_score_empty_list(self, service: object) -> None:
        """空のチェック結果リストのテスト"""
        score = service.calculate_weighted_score([])
        assert score.value == 0.0

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-CALCULATE_WEIGHTED_S")
    def test_calculate_weighted_score_missing_weights(self, service: object) -> None:
        """重みが設定されていないチェックタイプのテスト"""
        # 存在しないチェックタイプ
        check_results = [
            QualityCheckResult(
                check_type=CheckType.BASIC_STYLE,
                score=QualityScore(80.0),
                issues=[],
            )
        ]

        # 重みを一旦クリア
        service.weights = {}
        score = service.calculate_weighted_score(check_results)

        # 重みがない場合は単純平均
        assert score.value == 80.0

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-DETERMINE_GRADE_S_GR")
    def test_determine_grade_s_grade(self, service: object) -> None:
        """Sグレード判定のテスト"""
        score = QualityScore(95.0)
        grade = service.determine_grade(score)
        assert grade == QualityGrade.S

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-DETERMINE_GRADE_A_GR")
    def test_determine_grade_a_grade(self, service: object) -> None:
        """Aグレード判定のテスト"""
        score = QualityScore(85.0)
        grade = service.determine_grade(score)
        assert grade == QualityGrade.A

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-DETERMINE_GRADE_B_GR")
    def test_determine_grade_b_grade(self, service: object) -> None:
        """Bグレード判定のテスト"""
        score = QualityScore(75.0)
        grade = service.determine_grade(score)
        assert grade == QualityGrade.B

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-DETERMINE_GRADE_C_GR")
    def test_determine_grade_c_grade(self, service: object) -> None:
        """Cグレード判定のテスト"""
        score = QualityScore(65.0)
        grade = service.determine_grade(score)
        assert grade == QualityGrade.C

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-DETERMINE_GRADE_D_GR")
    def test_determine_grade_d_grade(self, service: object) -> None:
        """Dグレード判定のテスト"""
        score = QualityScore(45.0)
        grade = service.determine_grade(score)
        assert grade == QualityGrade.D

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-DETERMINE_GRADE_BOUN")
    def test_determine_grade_boundary_values(self, service: object) -> None:
        """境界値でのグレード判定テスト"""
        # 境界値ちょうど
        assert service.determine_grade(QualityScore(90.0)) == QualityGrade.S
        assert service.determine_grade(QualityScore(80.0)) == QualityGrade.A
        assert service.determine_grade(QualityScore(70.0)) == QualityGrade.B
        assert service.determine_grade(QualityScore(60.0)) == QualityGrade.C

        # 境界値未満
        assert service.determine_grade(QualityScore(89.9)) == QualityGrade.A
        assert service.determine_grade(QualityScore(79.9)) == QualityGrade.B

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-IDENTIFY_WEAK_AREAS_")
    def test_identify_weak_areas_default_threshold(self, service: object, sample_check_results: object) -> None:
        """デフォルト閾値での弱点領域特定テスト"""
        weak_areas = service.identify_weak_areas(sample_check_results)

        # 70.0未満のスコア: READABILITY(70.0)は含まれない
        assert len(weak_areas) == 0  # 70.0は閾値と同じなので含まれない

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-IDENTIFY_WEAK_AREAS_")
    def test_identify_weak_areas_custom_threshold(self, service: object, sample_check_results: object) -> None:
        """カスタム閾値での弱点領域特定テスト"""
        weak_areas = service.identify_weak_areas(sample_check_results, threshold=80.0)

        # 80.0未満: COMPOSITION(75.0), READABILITY(70.0)
        assert len(weak_areas) == 2
        assert weak_areas[0] == (CheckType.READABILITY, 70.0)  # 最低スコア
        assert weak_areas[1] == (CheckType.COMPOSITION, 75.0)

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-IDENTIFY_WEAK_AREAS_")
    def test_identify_weak_areas_no_weak_areas(self, service: object) -> None:
        """弱点領域がない場合のテスト"""
        high_score_results = [
            QualityCheckResult(
                check_type=CheckType.BASIC_STYLE,
                score=QualityScore(95.0),
                issues=[],
            )
        ]

        weak_areas = service.identify_weak_areas(high_score_results, threshold=70.0)
        assert len(weak_areas) == 0

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-CALCULATE_IMPROVEMEN")
    def test_calculate_improvement_priority(self, service: object, sample_check_results: object) -> None:
        """改善優先度計算のテスト"""
        priorities = service.calculate_improvement_priority(sample_check_results)

        assert len(priorities) == 4
        assert all("check_type" in p for p in priorities)
        assert all("priority_score" in p for p in priorities)
        assert all("potential_improvement" in p for p in priorities)

        # 優先度スコアの降順になっている
        for i in range(len(priorities) - 1):
            assert priorities[i]["priority_score"] >= priorities[i + 1]["priority_score"]

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-CALCULATE_IMPROVEMEN")
    def test_calculate_improvement_priority_error_impact(self, service: object) -> None:
        """エラー数の改善優先度への影響テスト"""

        results_with_many_errors = [
            QualityCheckResult(
                check_type=CheckType.BASIC_STYLE,
                score=QualityScore(80.0),
                issues=[
                    QualityIssue(type="style", message=f"エラー{i}", severity=Severity.ERROR)
                    for i in range(10)  # 多くのエラー
                ],
            ),
            QualityCheckResult(
                check_type=CheckType.COMPOSITION,
                score=QualityScore(60.0),  # 低いスコア
                issues=[
                    QualityIssue(type="composition", message="エラー1", severity=Severity.ERROR),  # 少ないエラー
                ],
            ),
        ]

        priorities = service.calculate_improvement_priority(results_with_many_errors)

        # エラー数の多いものが優先度高くなるかチェック
        basic_style_priority = next(p for p in priorities if p["check_type"] == CheckType.BASIC_STYLE)
        composition_priority = next(p for p in priorities if p["check_type"] == CheckType.COMPOSITION)

        # エラー数の影響を確認(エラー1件 = 5ポイント)
        assert basic_style_priority["priority_score"] > composition_priority["priority_score"]

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-GENERATE_IMPROVEMENT")
    def test_generate_improvement_plan_already_achieved(self, service: object) -> None:
        """既に目標達成済みの改善計画テスト"""
        high_score_results = [
            QualityCheckResult(
                check_type=CheckType.BASIC_STYLE,
                score=QualityScore(90.0),
                issues=[],
            )
        ]

        plan = service.generate_improvement_plan(high_score_results, QualityGrade.B)

        assert plan["current_score"] >= plan["target_score"]
        assert "既に目標グレードを達成しています" in plan["message"]

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-GENERATE_IMPROVEMENT")
    def test_generate_improvement_plan_needs_improvement(self, service: object, sample_check_results: object) -> None:
        """改善が必要な場合の改善計画テスト"""
        # 現在のスコアを確認
        current_score = service.calculate_weighted_score(sample_check_results)
        print(f"Current score: {current_score.value}")

        plan = service.generate_improvement_plan(sample_check_results, QualityGrade.A)

        assert plan["target_grade"] == QualityGrade.A.value
        assert plan["target_score"] == 80

        # 現在のスコアが80.0だった場合、改善が必要ないと判断される
        if plan["current_score"] >= 80.0:
            assert "message" in plan
            assert plan["message"] == "既に目標グレードを達成しています"
        else:
            assert plan["score_gap"] > -0.1  # 誤差範囲内
            assert len(plan["improvement_steps"]) > 0

            # 改善ステップの内容確認
            step = plan["improvement_steps"][0]
            assert "check_type" in step
            assert "current_score" in step
            assert "target_score" in step
            assert "improvement_needed" in step
            assert "priority" in step

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-GENERATE_IMPROVEMENT")
    def test_generate_improvement_plan_custom_target(self, service: object, sample_check_results: object) -> None:
        """カスタム目標グレードでの改善計画テスト"""
        plan_s = service.generate_improvement_plan(sample_check_results, QualityGrade.S)
        plan_c = service.generate_improvement_plan(sample_check_results, QualityGrade.C)

        # Sグレードの方が大きなスコアギャップ
        assert plan_s["score_gap"] > plan_c["score_gap"]
        assert plan_s["target_score"] > plan_c["target_score"]

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-VALIDATE_WEIGHTS_VAL")
    def test_validate_weights_valid(self, service: object) -> None:
        """妥当な重み設定の検証テスト"""
        valid_weights = {
            CheckType.BASIC_STYLE: 0.3,
            CheckType.COMPOSITION: 0.3,
            CheckType.CHARACTER_CONSISTENCY: 0.2,
            CheckType.READABILITY: 0.2,
        }
        assert service.validate_weights(valid_weights) is True

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-VALIDATE_WEIGHTS_INV")
    def test_validate_weights_invalid_sum(self, service: object) -> None:
        """重みの合計が1.0でない場合のテスト"""
        invalid_weights = {
            CheckType.BASIC_STYLE: 0.5,
            CheckType.COMPOSITION: 0.5,  # 合計1.0超過
            CheckType.CHARACTER_CONSISTENCY: 0.2,
        }
        assert service.validate_weights(invalid_weights) is False

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-VALIDATE_WEIGHTS_TOL")
    def test_validate_weights_tolerance(self, service: object) -> None:
        """許容誤差内での重み検証テスト"""
        # 0.995(許容範囲内)
        nearly_valid_weights = {
            CheckType.BASIC_STYLE: 0.995,
        }
        assert service.validate_weights(nearly_valid_weights) is True

        # 1.005(許容範囲内)
        nearly_valid_weights2 = {
            CheckType.BASIC_STYLE: 1.005,
        }
        assert service.validate_weights(nearly_valid_weights2) is True

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-WEIGHTED_SCORE_CALCU")
    def test_weighted_score_calculation_edge_cases(self, service: object) -> None:
        """重み付けスコア計算のエッジケーステスト"""
        # 全て同じスコア
        uniform_results = [
            QualityCheckResult(
                check_type=CheckType.BASIC_STYLE,
                score=QualityScore(80.0),
                issues=[],
            ),
            QualityCheckResult(
                check_type=CheckType.COMPOSITION,
                score=QualityScore(80.0),
                issues=[],
            ),
        ]

        score = service.calculate_weighted_score(uniform_results)
        assert score.value == 80.0

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-IMPROVEMENT_PLAN_STE")
    def test_improvement_plan_step_priority_calculation(self, service: object) -> None:
        """改善計画ステップの優先度計算テスト"""

        results = [
            QualityCheckResult(
                check_type=CheckType.BASIC_STYLE,
                score=QualityScore(40.0),  # 低スコア、高い改善ポテンシャル
                issues=[
                    *[
                        QualityIssue(type="style", message=f"エラー{i}", severity=Severity.ERROR) for i in range(15)
                    ],  # 多くのエラー
                    *[QualityIssue(type="style", message=f"警告{i}", severity=Severity.WARNING) for i in range(5)],
                ],
            ),
            QualityCheckResult(
                check_type=CheckType.COMPOSITION,
                score=QualityScore(85.0),  # 高スコア、低い改善ポテンシャル
                issues=[
                    QualityIssue(type="composition", message="エラー1", severity=Severity.ERROR),  # 少ないエラー
                ],
            ),
        ]

        priorities = service.calculate_improvement_priority(results)

        # BASIC_STYLEが高い優先度を持つはず
        basic_priority = next(p for p in priorities if p["check_type"] == CheckType.BASIC_STYLE)
        composition_priority = next(p for p in priorities if p["check_type"] == CheckType.COMPOSITION)

        assert basic_priority["priority_score"] > composition_priority["priority_score"]
        assert basic_priority["potential_improvement"] > composition_priority["potential_improvement"]

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-GRADE_THRESHOLDS_CON")
    def test_grade_thresholds_consistency(self) -> None:
        """グレード閾値の一貫性テスト"""
        thresholds = QualityEvaluationService.GRADE_THRESHOLDS

        # グレードが降順に並んでいる
        grades = list(thresholds.keys())
        assert len(grades) == 5

        # 閾値が降順に並んでいる
        for i in range(len(grades) - 1):
            assert thresholds[grades[i]] >= thresholds[grades[i + 1]]

    @pytest.mark.spec("SPEC-QUALITY_EVALUATION_SERVICE-IMPROVEMENT_PLAN_MAX")
    def test_improvement_plan_maximum_steps(self, service: object) -> None:
        """改善計画の最大ステップ数テスト"""

        # 多くのチェックタイプを含む結果
        many_results = []
        for i, check_type in enumerate(CheckType):
            many_results.append(
                QualityCheckResult(
                    check_type=check_type,
                    score=QualityScore(50.0),  # 全て低スコア
                    issues=[
                        QualityIssue(type="test", message=f"エラー{j}", severity=Severity.ERROR) for j in range(i + 1)
                    ],
                )
            )

        plan = service.generate_improvement_plan(many_results, QualityGrade.A)

        # 最大3つのステップまで
        assert len(plan["improvement_steps"]) <= 3
