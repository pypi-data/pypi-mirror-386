#!/usr/bin/env python3
"""視点情報連動型品質評価のドメインテスト

TDD RED段階: 失敗するテストを作成してビジネスルールを明確化


仕様書: SPEC-UNIT-TEST
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path
# PathManager統一パス管理システムを使用(事前にパスを設定)
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/を追加
from noveler.infrastructure.utils.path_manager import ensure_imports

ensure_imports()

from noveler.domain.quality.value_objects import QualityScore
from noveler.domain.quality.viewpoint_entities import (
    ComplexityLevel,
    QualityEvaluationCriteria,
    ViewpointBasedQualityEvaluator,
    ViewpointInfo,
    ViewpointType,
)


class TestViewpointInfo:
    """ViewpointInfoエンティティのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-SINGLE_INTROSPECTIVE")
    def test_single_introspective_requires_dialogue_adjustment(self) -> None:
        """単一視点・内省型は会話比率調整が必要"""
        viewpoint = ViewpointInfo(
            character="カノン",
            viewpoint_type=ViewpointType.SINGLE_INTROSPECTIVE,
            complexity_level=ComplexityLevel.MEDIUM,
            special_conditions=[],
            narrative_focus="inner_thoughts",
        )

        assert viewpoint.requires_dialogue_weight_adjustment() is True
        assert viewpoint.get_dialogue_weight_multiplier() == 0.5

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-HIGH_COMPLEXITY_REQU")
    def test_high_complexity_requires_dialogue_adjustment(self) -> None:
        """複雑度高は会話比率調整が必要"""
        viewpoint = ViewpointInfo(
            character="律",
            viewpoint_type=ViewpointType.SINGLE_INTERACTIVE,
            complexity_level=ComplexityLevel.HIGH,
            special_conditions=["body_swap"],
            narrative_focus="interaction",
        )

        assert viewpoint.requires_dialogue_weight_adjustment() is True
        assert viewpoint.get_dialogue_weight_multiplier() == 0.7

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-SINGLE_INTERACTIVE_N")
    def test_single_interactive_normal_dialogue_weight(self) -> None:
        """単一視点・交流型は通常の会話比率重み"""
        viewpoint = ViewpointInfo(
            character="律",
            viewpoint_type=ViewpointType.SINGLE_INTERACTIVE,
            complexity_level=ComplexityLevel.LOW,
            special_conditions=[],
            narrative_focus="dialogue",
        )

        assert viewpoint.requires_dialogue_weight_adjustment() is False
        assert viewpoint.get_dialogue_weight_multiplier() == 1.0

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-INTROSPECTIVE_REQUIR")
    def test_introspective_requires_narrative_depth_emphasis(self) -> None:
        """内省型は内面描写深度の重視が必要"""
        viewpoint = ViewpointInfo(
            character="カノン",
            viewpoint_type=ViewpointType.SINGLE_INTROSPECTIVE,
            complexity_level=ComplexityLevel.MEDIUM,
            special_conditions=[],
            narrative_focus="inner_thoughts",
        )

        assert viewpoint.requires_narrative_depth_emphasis() is True
        assert viewpoint.get_narrative_depth_weight_multiplier() == 1.5

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-BODY_SWAP_REQUIRES_N")
    def test_body_swap_requires_narrative_depth_emphasis(self) -> None:
        """身体交換時は内面描写深度の重視が必要"""
        viewpoint = ViewpointInfo(
            character="律→カノンBody",
            viewpoint_type=ViewpointType.BODY_SWAP,
            complexity_level=ComplexityLevel.HIGH,
            special_conditions=["body_swap"],
            narrative_focus="body_adaptation",
        )

        assert viewpoint.requires_narrative_depth_emphasis() is True
        assert viewpoint.get_narrative_depth_weight_multiplier() == 1.3

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-BODY_SWAP_REQUIRES_V")
    def test_body_swap_requires_viewpoint_clarity_check(self) -> None:
        """身体交換時は視点の明確さチェックが必要"""
        viewpoint = ViewpointInfo(
            character="律→カノンBody",
            viewpoint_type=ViewpointType.BODY_SWAP,
            complexity_level=ComplexityLevel.HIGH,
            special_conditions=["body_swap"],
            narrative_focus="body_adaptation",
        )

        assert viewpoint.requires_viewpoint_clarity_check() is True

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-MULTIPLE_PERSPECTIVE")
    def test_multiple_perspective_requires_viewpoint_clarity_check(self) -> None:
        """複数視点は視点の明確さチェックが必要"""
        viewpoint = ViewpointInfo(
            character="律&カノン",
            viewpoint_type=ViewpointType.MULTIPLE_PERSPECTIVE,
            complexity_level=ComplexityLevel.MEDIUM,
            special_conditions=["multiple_characters"],
            narrative_focus="shared_experience",
        )

        assert viewpoint.requires_viewpoint_clarity_check() is True


class TestQualityEvaluationCriteria:
    """QualityEvaluationCriteriaのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-CREATE_STANDARD_CRIT")
    def test_create_standard_criteria(self) -> None:
        """標準的な評価基準の作成"""
        criteria = QualityEvaluationCriteria.create_standard_criteria()

        assert criteria.dialogue_weight == 1.0
        assert criteria.narrative_depth_weight == 1.0
        assert criteria.viewpoint_clarity_weight == 1.0
        assert criteria.basic_style_weight == 1.0
        assert criteria.composition_weight == 1.0

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-CREATE_INTROSPECTIVE")
    def test_create_introspective_adjusted_criteria(self) -> None:
        """内省型視点に調整された評価基準の作成"""
        viewpoint = ViewpointInfo(
            character="カノン",
            viewpoint_type=ViewpointType.SINGLE_INTROSPECTIVE,
            complexity_level=ComplexityLevel.MEDIUM,
            special_conditions=[],
            narrative_focus="inner_thoughts",
        )

        criteria = QualityEvaluationCriteria.create_viewpoint_adjusted_criteria(viewpoint)

        assert criteria.dialogue_weight == 0.5  # 会話比率の重み軽減
        assert criteria.narrative_depth_weight == 1.5  # 内面描写重視
        assert criteria.viewpoint_clarity_weight == 1.0  # 通常
        assert criteria.basic_style_weight == 1.0  # 固定
        assert criteria.composition_weight == 1.0  # 固定

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-CREATE_BODY_SWAP_ADJ")
    def test_create_body_swap_adjusted_criteria(self) -> None:
        """身体交換時に調整された評価基準の作成"""
        viewpoint = ViewpointInfo(
            character="律→カノンBody",
            viewpoint_type=ViewpointType.BODY_SWAP,
            complexity_level=ComplexityLevel.HIGH,
            special_conditions=["body_swap"],
            narrative_focus="body_adaptation",
        )

        criteria = QualityEvaluationCriteria.create_viewpoint_adjusted_criteria(viewpoint)

        assert criteria.dialogue_weight == 0.7  # 複雑度高による調整
        assert criteria.narrative_depth_weight == 1.3  # 身体交換時の内面重視
        assert criteria.viewpoint_clarity_weight == 1.5  # 視点明確さ重視
        assert criteria.basic_style_weight == 1.0  # 固定
        assert criteria.composition_weight == 1.0  # 固定


class TestViewpointBasedQualityEvaluator:
    """ViewpointBasedQualityEvaluatorのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-EVALUATE_QUALITY_WIT")
    def test_evaluate_quality_with_introspective_viewpoint(self) -> None:
        """内省型視点での品質評価"""
        evaluator = ViewpointBasedQualityEvaluator()

        viewpoint = ViewpointInfo(
            character="カノン",
            viewpoint_type=ViewpointType.SINGLE_INTROSPECTIVE,
            complexity_level=ComplexityLevel.MEDIUM,
            special_conditions=[],
            narrative_focus="inner_thoughts",
        )

        # 基本品質スコア(会話比率が低い)
        base_scores = {
            "dialogue_ratio": QualityScore(30.0),  # 会話比率が低い
            "narrative_depth": QualityScore(80.0),  # 内面描写は高い
            "basic_style": QualityScore(85.0),
        }

        adjusted_scores = evaluator.evaluate_quality_with_viewpoint(
            "test",
            viewpoint=viewpoint,
            base_quality_scores=base_scores,
        )

        # 内省型なので会話比率の低さが緩和される(スコア向上)
        assert adjusted_scores["dialogue_ratio"].value > 30.0
        # 内面描写はより厳格に評価される(スコア低下の可能性)
        assert adjusted_scores["narrative_depth"].value <= 80.0
        # その他は変更なし
        assert adjusted_scores["basic_style"].value == 85.0

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-ADJUST_SCORE_WITH_WE")
    def test_adjust_score_with_weight_reduction(self) -> None:
        """重み軽減時のスコア調整"""
        evaluator = ViewpointBasedQualityEvaluator()
        original_score = QualityScore(30.0)  # 低いスコア

        # 重み0.5(重要度下げる)→ スコア緩和(底上げ)
        adjusted_score = evaluator._adjust_score_with_weight(original_score, 0.5)

        assert adjusted_score.value > 30.0  # スコアが向上
        assert adjusted_score.value <= 100.0

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-ADJUST_SCORE_WITH_WE")
    def test_adjust_score_with_weight_increase(self) -> None:
        """重み増加時のスコア調整"""
        evaluator = ViewpointBasedQualityEvaluator()
        original_score = QualityScore(80.0)  # 高いスコア

        # 重み1.5(重要度上げる)→ より厳格評価
        adjusted_score = evaluator._adjust_score_with_weight(original_score, 1.5)

        assert adjusted_score.value <= 80.0  # スコアが低下
        assert adjusted_score.value >= 0.0

    @pytest.mark.spec("SPEC-DOMAIN_VIEWPOINT_QUALITY-GENERATE_VIEWPOINT_C")
    def test_generate_viewpoint_context_message(self) -> None:
        """視点コンテキストメッセージの生成"""
        evaluator = ViewpointBasedQualityEvaluator()

        viewpoint = ViewpointInfo(
            character="カノン",
            viewpoint_type=ViewpointType.SINGLE_INTROSPECTIVE,
            complexity_level=ComplexityLevel.MEDIUM,
            special_conditions=[],
            narrative_focus="inner_thoughts",
        )

        message = evaluator.generate_viewpoint_context_message(viewpoint)

        assert "📌 視点タイプ: 単一視点・内省型" in message
        assert "📌 複雑度: 中" in message
        assert "⚠️ 内省型エピソードのため会話比率は参考値(重み:0.5)" in message
        assert "✨ 内面描写深度を重視して評価(重み:1.5)" in message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
