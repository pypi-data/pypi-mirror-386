"""視点情報連動型品質評価ドメインエンティティのテスト

TDD準拠テスト:
    - ViewpointInfo
- QualityEvaluationCriteria
- ViewpointBasedQualityEvaluator


仕様書: SPEC-UNIT-TEST
"""

import pytest
pytestmark = pytest.mark.quality_domain


from noveler.domain.quality.value_objects import QualityScore
from noveler.domain.quality.viewpoint_entities import (
    ComplexityLevel,
    QualityEvaluationCriteria,
    ViewpointBasedQualityEvaluator,
    ViewpointInfo,
    ViewpointType,
)


class TestViewpointInfo:
    """ViewpointInfoのテストクラス"""

    @pytest.fixture
    def introspective_viewpoint(self) -> ViewpointInfo:
        """内省型視点情報"""
        return ViewpointInfo(
            character="主人公",
            viewpoint_type=ViewpointType.SINGLE_INTROSPECTIVE,
            complexity_level=ComplexityLevel.MEDIUM,
            special_conditions=["内面描写重視"],
            narrative_focus="心理描写",
        )

    @pytest.fixture
    def interactive_viewpoint(self) -> ViewpointInfo:
        """交流型視点情報"""
        return ViewpointInfo(
            character="主人公",
            viewpoint_type=ViewpointType.SINGLE_INTERACTIVE,
            complexity_level=ComplexityLevel.LOW,
            special_conditions=["会話中心"],
            narrative_focus="キャラクター間交流",
        )

    @pytest.fixture
    def body_swap_viewpoint(self) -> ViewpointInfo:
        """身体交換視点情報"""
        return ViewpointInfo(
            character="入れ替わり後",
            viewpoint_type=ViewpointType.BODY_SWAP,
            complexity_level=ComplexityLevel.HIGH,
            special_conditions=["視点切り替え", "アイデンティティ混乱"],
            narrative_focus="視点の明確化",
        )

    @pytest.fixture
    def multiple_perspective_viewpoint(self) -> ViewpointInfo:
        """複数視点情報"""
        return ViewpointInfo(
            character="複数キャラ",
            viewpoint_type=ViewpointType.MULTIPLE_PERSPECTIVE,
            complexity_level=ComplexityLevel.HIGH,
            special_conditions=["視点切り替え多用"],
            narrative_focus="多角的描写",
        )

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-VIEWPOINT_INFO_CREAT")
    def test_viewpoint_info_creation(self, introspective_viewpoint: ViewpointInfo) -> None:
        """視点情報作成テスト"""
        assert introspective_viewpoint.character == "主人公"
        assert introspective_viewpoint.viewpoint_type == ViewpointType.SINGLE_INTROSPECTIVE
        assert introspective_viewpoint.complexity_level == ComplexityLevel.MEDIUM
        assert introspective_viewpoint.special_conditions == ["内面描写重視"]
        assert introspective_viewpoint.narrative_focus == "心理描写"

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-REQUIRES_DIALOGUE_WE")
    def test_requires_dialogue_weight_adjustment_introspective(self, introspective_viewpoint: ViewpointInfo) -> None:
        """内省型での会話比率調整必要性テスト"""
        assert introspective_viewpoint.requires_dialogue_weight_adjustment() is True

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-REQUIRES_DIALOGUE_WE")
    def test_requires_dialogue_weight_adjustment_interactive(self, interactive_viewpoint: ViewpointInfo) -> None:
        """交流型での会話比率調整必要性テスト"""
        assert interactive_viewpoint.requires_dialogue_weight_adjustment() is False

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-REQUIRES_DIALOGUE_WE")
    def test_requires_dialogue_weight_adjustment_high_complexity(
        self, multiple_perspective_viewpoint: ViewpointInfo
    ) -> None:
        """高複雑度での会話比率調整必要性テスト"""
        assert multiple_perspective_viewpoint.requires_dialogue_weight_adjustment() is True

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-GET_DIALOGUE_WEIGHT_")
    def test_get_dialogue_weight_multiplier_introspective(self, introspective_viewpoint: ViewpointInfo) -> None:
        """内省型での会話重み倍率テスト"""
        assert introspective_viewpoint.get_dialogue_weight_multiplier() == 0.5

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-GET_DIALOGUE_WEIGHT_")
    def test_get_dialogue_weight_multiplier_interactive(self, interactive_viewpoint: ViewpointInfo) -> None:
        """交流型での会話重み倍率テスト"""
        assert interactive_viewpoint.get_dialogue_weight_multiplier() == 1.0

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-GET_DIALOGUE_WEIGHT_")
    def test_get_dialogue_weight_multiplier_high_complexity(
        self, multiple_perspective_viewpoint: ViewpointInfo
    ) -> None:
        """高複雑度での会話重み倍率テスト"""
        assert multiple_perspective_viewpoint.get_dialogue_weight_multiplier() == 0.7

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-REQUIRES_NARRATIVE_D")
    def test_requires_narrative_depth_emphasis_introspective(self, introspective_viewpoint: ViewpointInfo) -> None:
        """内省型での内面描写重視必要性テスト"""
        assert introspective_viewpoint.requires_narrative_depth_emphasis() is True

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-REQUIRES_NARRATIVE_D")
    def test_requires_narrative_depth_emphasis_body_swap(self, body_swap_viewpoint: ViewpointInfo) -> None:
        """身体交換での内面描写重視必要性テスト"""
        assert body_swap_viewpoint.requires_narrative_depth_emphasis() is True

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-REQUIRES_NARRATIVE_D")
    def test_requires_narrative_depth_emphasis_interactive(self, interactive_viewpoint: ViewpointInfo) -> None:
        """交流型での内面描写重視必要性テスト"""
        assert interactive_viewpoint.requires_narrative_depth_emphasis() is False

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-GET_NARRATIVE_DEPTH_")
    def test_get_narrative_depth_weight_multiplier_introspective(self, introspective_viewpoint: ViewpointInfo) -> None:
        """内省型での内面描写重み倍率テスト"""
        assert introspective_viewpoint.get_narrative_depth_weight_multiplier() == 1.5

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-GET_NARRATIVE_DEPTH_")
    def test_get_narrative_depth_weight_multiplier_body_swap(self, body_swap_viewpoint: ViewpointInfo) -> None:
        """身体交換での内面描写重み倍率テスト"""
        assert body_swap_viewpoint.get_narrative_depth_weight_multiplier() == 1.3

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-GET_NARRATIVE_DEPTH_")
    def test_get_narrative_depth_weight_multiplier_interactive(self, interactive_viewpoint: ViewpointInfo) -> None:
        """交流型での内面描写重み倍率テスト"""
        assert interactive_viewpoint.get_narrative_depth_weight_multiplier() == 1.0

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-REQUIRES_VIEWPOINT_C")
    def test_requires_viewpoint_clarity_check_body_swap(self, body_swap_viewpoint: ViewpointInfo) -> None:
        """身体交換での視点明確さチェック必要性テスト"""
        assert body_swap_viewpoint.requires_viewpoint_clarity_check() is True

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-REQUIRES_VIEWPOINT_C")
    def test_requires_viewpoint_clarity_check_multiple_perspective(
        self, multiple_perspective_viewpoint: ViewpointInfo
    ) -> None:
        """複数視点での視点明確さチェック必要性テスト"""
        assert multiple_perspective_viewpoint.requires_viewpoint_clarity_check() is True

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-REQUIRES_VIEWPOINT_C")
    def test_requires_viewpoint_clarity_check_high_complexity(self, body_swap_viewpoint: ViewpointInfo) -> None:
        """高複雑度での視点明確さチェック必要性テスト"""
        # body_swap_viewpoint は ComplexityLevel.HIGH なので True
        assert body_swap_viewpoint.requires_viewpoint_clarity_check() is True

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-REQUIRES_VIEWPOINT_C")
    def test_requires_viewpoint_clarity_check_simple_case(self, interactive_viewpoint: ViewpointInfo) -> None:
        """単純な場合での視点明確さチェック必要性テスト"""
        # interactive_viewpoint は SINGLE_INTERACTIVE + LOW complexity なので False
        assert interactive_viewpoint.requires_viewpoint_clarity_check() is False


class TestQualityEvaluationCriteria:
    """QualityEvaluationCriteriaのテストクラス"""

    @pytest.fixture
    def standard_criteria(self) -> QualityEvaluationCriteria:
        """標準評価基準"""
        return QualityEvaluationCriteria.create_standard_criteria()

    @pytest.fixture
    def introspective_viewpoint(self) -> ViewpointInfo:
        """内省型視点情報"""
        return ViewpointInfo(
            character="主人公",
            viewpoint_type=ViewpointType.SINGLE_INTROSPECTIVE,
            complexity_level=ComplexityLevel.MEDIUM,
            special_conditions=[],
            narrative_focus="心理描写",
        )

    @pytest.fixture
    def body_swap_viewpoint(self) -> ViewpointInfo:
        """身体交換視点情報"""
        return ViewpointInfo(
            character="入れ替わり後",
            viewpoint_type=ViewpointType.BODY_SWAP,
            complexity_level=ComplexityLevel.HIGH,
            special_conditions=[],
            narrative_focus="視点の明確化",
        )

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-STANDARD_CRITERIA_CR")
    def test_standard_criteria_creation(self, standard_criteria: QualityEvaluationCriteria) -> None:
        """標準評価基準作成テスト"""
        assert standard_criteria.dialogue_weight == 1.0
        assert standard_criteria.narrative_depth_weight == 1.0
        assert standard_criteria.viewpoint_clarity_weight == 1.0
        assert standard_criteria.basic_style_weight == 1.0
        assert standard_criteria.composition_weight == 1.0

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-VIEWPOINT_ADJUSTED_C")
    def test_viewpoint_adjusted_criteria_introspective(self, introspective_viewpoint: ViewpointInfo) -> None:
        """内省型視点調整基準作成テスト"""
        criteria = QualityEvaluationCriteria.create_viewpoint_adjusted_criteria(introspective_viewpoint)

        assert criteria.dialogue_weight == 0.5  # 内省型は会話重視度を下げる
        assert criteria.narrative_depth_weight == 1.5  # 内省型は内面描写を重視
        assert criteria.viewpoint_clarity_weight == 1.0  # 単一視点なので通常
        assert criteria.basic_style_weight == 1.0  # 固定
        assert criteria.composition_weight == 1.0  # 固定

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-VIEWPOINT_ADJUSTED_C")
    def test_viewpoint_adjusted_criteria_body_swap(self, body_swap_viewpoint: ViewpointInfo) -> None:
        """身体交換視点調整基準作成テスト"""
        criteria = QualityEvaluationCriteria.create_viewpoint_adjusted_criteria(body_swap_viewpoint)

        assert criteria.dialogue_weight == 0.7  # 高複雑度で緩和
        assert criteria.narrative_depth_weight == 1.3  # 身体交換で内面描写重視
        assert criteria.viewpoint_clarity_weight == 1.5  # 身体交換で視点明確さ重視
        assert criteria.basic_style_weight == 1.0  # 固定
        assert criteria.composition_weight == 1.0  # 固定

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-VIEWPOINT_ADJUSTED_C")
    def test_viewpoint_adjusted_criteria_interactive_simple(self) -> None:
        """単純な交流型視点調整基準作成テスト"""
        interactive_viewpoint = ViewpointInfo(
            character="主人公",
            viewpoint_type=ViewpointType.SINGLE_INTERACTIVE,
            complexity_level=ComplexityLevel.LOW,
            special_conditions=[],
            narrative_focus="交流",
        )

        criteria = QualityEvaluationCriteria.create_viewpoint_adjusted_criteria(interactive_viewpoint)

        assert criteria.dialogue_weight == 1.0  # 交流型は通常
        assert criteria.narrative_depth_weight == 1.0  # 交流型は通常
        assert criteria.viewpoint_clarity_weight == 1.0  # 単一視点・低複雑度で通常
        assert criteria.basic_style_weight == 1.0  # 固定
        assert criteria.composition_weight == 1.0  # 固定


class TestViewpointBasedQualityEvaluator:
    """ViewpointBasedQualityEvaluatorのテストクラス"""

    @pytest.fixture
    def evaluator(self) -> ViewpointBasedQualityEvaluator:
        """視点ベース品質評価器"""
        return ViewpointBasedQualityEvaluator()

    @pytest.fixture
    def base_quality_scores(self) -> dict[str, QualityScore]:
        """基本品質スコア"""
        return {
            "dialogue_ratio": QualityScore(60.0),
            "narrative_depth": QualityScore(70.0),
            "readability": QualityScore(80.0),
            "basic_style": QualityScore(85.0),
        }

    @pytest.fixture
    def introspective_viewpoint(self) -> ViewpointInfo:
        """内省型視点情報"""
        return ViewpointInfo(
            character="主人公",
            viewpoint_type=ViewpointType.SINGLE_INTROSPECTIVE,
            complexity_level=ComplexityLevel.MEDIUM,
            special_conditions=["内面描写重視"],
            narrative_focus="心理描写",
        )

    @pytest.fixture
    def interactive_viewpoint(self) -> ViewpointInfo:
        """交流型視点情報"""
        return ViewpointInfo(
            character="主人公",
            viewpoint_type=ViewpointType.SINGLE_INTERACTIVE,
            complexity_level=ComplexityLevel.LOW,
            special_conditions=["会話中心"],
            narrative_focus="キャラクター間交流",
        )

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-EVALUATE_QUALITY_WIT")
    def test_evaluate_quality_with_viewpoint_introspective(
        self,
        evaluator: ViewpointBasedQualityEvaluator,
        base_quality_scores: dict[str, QualityScore],
        introspective_viewpoint: ViewpointInfo,
    ) -> None:
        """内省型視点での品質評価テスト"""
        adjusted_scores = evaluator.evaluate_quality_with_viewpoint(
            "テスト文章", introspective_viewpoint, base_quality_scores
        )

        # 会話比率は緩和される(weight=0.5なので底上げ)
        # base_quality_scores["dialogue_ratio"].value == 60.0
        expected_dialogue = min(100.0, 60.0 + (100 - 60.0) * (1.0 - 0.5))  # 60 + 40*0.5 = 80.0
        assert adjusted_scores["dialogue_ratio"].value == expected_dialogue

        # 内面描写深度は厳格化される(weight=1.5なので厳しく)
        # base_quality_scores["narrative_depth"].value == 70.0
        expected_narrative = max(0.0, 70.0 * (2.0 - 1.5))  # 70 * 0.5 = 35.0
        assert adjusted_scores["narrative_depth"].value == expected_narrative

        # その他はそのまま
        assert adjusted_scores["readability"].value == 80.0
        assert adjusted_scores["basic_style"].value == 85.0

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-EVALUATE_QUALITY_WIT")
    def test_evaluate_quality_with_viewpoint_interactive(
        self,
        evaluator: ViewpointBasedQualityEvaluator,
        base_quality_scores: dict[str, QualityScore],
        interactive_viewpoint: ViewpointInfo,
    ) -> None:
        """交流型視点での品質評価テスト"""
        adjusted_scores = evaluator.evaluate_quality_with_viewpoint(
            "テスト文章", interactive_viewpoint, base_quality_scores
        )

        # 交流型では重みが1.0なのでスコアは変更されない
        assert adjusted_scores["dialogue_ratio"].value == 60.0
        assert adjusted_scores["narrative_depth"].value == 70.0
        assert adjusted_scores["readability"].value == 80.0
        assert adjusted_scores["basic_style"].value == 85.0

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-ADJUST_SCORE_WITH_WE")
    def test_adjust_score_with_weight_decrease(self, evaluator: ViewpointBasedQualityEvaluator) -> None:
        """重み減少でのスコア調整テスト"""
        original_score = QualityScore(60.0)
        weight = 0.5  # 重要度を下げる

        adjusted_score = evaluator._adjust_score_with_weight(original_score, weight)

        # 60 + (100-60) * (1-0.5) = 60 + 40*0.5 = 80.0
        assert adjusted_score.value == 80.0

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-ADJUST_SCORE_WITH_WE")
    def test_adjust_score_with_weight_increase(self, evaluator: ViewpointBasedQualityEvaluator) -> None:
        """重み増加でのスコア調整テスト"""
        original_score = QualityScore(70.0)
        weight = 1.5  # 重要度を上げる

        adjusted_score = evaluator._adjust_score_with_weight(original_score, weight)

        # 70 * (2.0-1.5) = 70 * 0.5 = 35.0
        assert adjusted_score.value == 35.0

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-ADJUST_SCORE_WITH_WE")
    def test_adjust_score_with_weight_normal(self, evaluator: ViewpointBasedQualityEvaluator) -> None:
        """通常重みでのスコア調整テスト"""
        original_score = QualityScore(75.0)
        weight = 1.0  # 通常重み

        adjusted_score = evaluator._adjust_score_with_weight(original_score, weight)

        # 重み1.0なので変更なし
        assert adjusted_score.value == 75.0

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-ADJUST_SCORE_WITH_WE")
    def test_adjust_score_with_weight_boundary_conditions(self, evaluator: ViewpointBasedQualityEvaluator) -> None:
        """境界条件でのスコア調整テスト"""
        # 高スコア + 重み減少
        high_score = QualityScore(95.0)
        adjusted_high = evaluator._adjust_score_with_weight(high_score, 0.5)
        expected_high = min(100.0, 95.0 + (100 - 95.0) * 0.5)  # 97.5
        assert adjusted_high.value == expected_high

        # 低スコア + 重み増加
        low_score = QualityScore(10.0)
        adjusted_low = evaluator._adjust_score_with_weight(low_score, 2.0)
        expected_low = max(0.0, 10.0 * (2.0 - 2.0))  # 0.0
        assert adjusted_low.value == expected_low

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-GENERATE_VIEWPOINT_C")
    def test_generate_viewpoint_context_message_introspective(
        self, evaluator: ViewpointBasedQualityEvaluator, introspective_viewpoint: ViewpointInfo
    ) -> None:
        """内省型視点コンテキストメッセージ生成テスト"""
        message = evaluator.generate_viewpoint_context_message(introspective_viewpoint)

        assert "📌 視点タイプ: 単一視点・内省型" in message
        assert "📌 複雑度: 中" in message
        assert "⚠️ 内省型エピソードのため会話比率は参考値(重み:0.5)" in message
        assert "✨ 内面描写深度を重視して評価(重み:1.5)" in message

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-GENERATE_VIEWPOINT_C")
    def test_generate_viewpoint_context_message_body_swap(self, evaluator: ViewpointBasedQualityEvaluator) -> None:
        """身体交換視点コンテキストメッセージ生成テスト"""
        body_swap_viewpoint = ViewpointInfo(
            character="入れ替わり後",
            viewpoint_type=ViewpointType.BODY_SWAP,
            complexity_level=ComplexityLevel.HIGH,
            special_conditions=["視点切り替え"],
            narrative_focus="視点の明確化",
        )

        message = evaluator.generate_viewpoint_context_message(body_swap_viewpoint)

        assert "📌 視点タイプ: 身体交換" in message
        assert "📌 複雑度: 高" in message
        assert "⚠️ 内省型エピソードのため会話比率は参考値(重み:0.7)" in message
        assert "✨ 内面描写深度を重視して評価(重み:1.3)" in message
        assert "🔍 視点の明確さを特に重視して評価" in message

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-GENERATE_VIEWPOINT_C")
    def test_generate_viewpoint_context_message_interactive_simple(
        self, evaluator: ViewpointBasedQualityEvaluator, interactive_viewpoint: ViewpointInfo
    ) -> None:
        """単純な交流型視点コンテキストメッセージ生成テスト"""
        message = evaluator.generate_viewpoint_context_message(interactive_viewpoint)

        assert "📌 視点タイプ: 単一視点・交流型" in message
        assert "📌 複雑度: 低" in message
        # 調整なしなので特別なメッセージはない
        assert "⚠️" not in message
        assert "✨" not in message
        assert "🔍" not in message

    @pytest.mark.spec("SPEC-VIEWPOINT_ENTITIES-EVALUATE_QUALITY_MIS")
    def test_evaluate_quality_missing_scores(
        self, evaluator: ViewpointBasedQualityEvaluator, introspective_viewpoint: ViewpointInfo
    ) -> None:
        """一部スコア不足での品質評価テスト"""
        partial_scores = {
            "readability": QualityScore(80.0),
            "basic_style": QualityScore(85.0),
            # dialogue_ratio と narrative_depth がない
        }

        adjusted_scores = evaluator.evaluate_quality_with_viewpoint(
            "テスト文章", introspective_viewpoint, partial_scores
        )

        # 存在しないスコアは調整されず、存在するスコアはそのまま
        assert adjusted_scores["readability"].value == 80.0
        assert adjusted_scores["basic_style"].value == 85.0
        assert "dialogue_ratio" not in adjusted_scores
        assert "narrative_depth" not in adjusted_scores
