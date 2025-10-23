# tests/test_domain_narrative_depth.py
"""内面描写深度評価のドメイン層テスト

仕様書: SPEC-UNIT-TEST
"""

import pytest

from noveler.domain.services.narrative_depth_services import NarrativeDepthAnalyzer, ViewpointAwareEvaluator
from noveler.domain.value_objects.narrative_depth_models import (
    DepthLayer,
    DepthPattern,
    LayerScore,
    NarrativeDepthScore,
    TextSegment,
)


class TestDepthLayer:
    """DepthLayerエンティティのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-ALL_LAYERS_EXIST")
    def test_all_layers_exist(self) -> None:
        """必要な全ての層が定義されている"""
        expected_layers = {"感覚層", "感情層", "思考層", "記憶層", "象徴層"}
        actual_layers = {layer.value for layer in DepthLayer}
        assert actual_layers == expected_layers


class TestLayerScore:
    """LayerScore値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-VALID_SCORE_CREATION")
    def test_valid_score_creation(self) -> None:
        """有効なスコアが正しく作成される"""
        score = LayerScore(layer=DepthLayer.SENSORY, score=15.0)
        assert score.layer == DepthLayer.SENSORY
        assert score.score == 15.0
        assert score.max_score == 20.0
        assert score.percentage == 75.0

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-INVALID_SCORE_RAISES")
    def test_invalid_score_raises_error(self) -> None:
        """無効なスコアでエラーが発生する"""
        with pytest.raises(ValueError, match=".*"):
            LayerScore(layer=DepthLayer.SENSORY, score=-1.0)

        with pytest.raises(ValueError, match=".*"):
            LayerScore(layer=DepthLayer.SENSORY, score=25.0)

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-PERCENTAGE_CALCULATI")
    def test_percentage_calculation(self) -> None:
        """パーセンテージ計算が正しい"""
        score = LayerScore(layer=DepthLayer.EMOTIONAL, score=10.0)
        assert score.percentage == 50.0


class TestNarrativeDepthScore:
    """NarrativeDepthScore集約のテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-COMPLETE_SCORE_CREAT")
    def test_complete_score_creation(self) -> None:
        """全層を含む完全なスコアが作成される"""
        layer_scores = {layer: LayerScore(layer=layer, score=10.0) for layer in DepthLayer}
        depth_score = NarrativeDepthScore(layer_scores=layer_scores)
        assert len(depth_score.layer_scores) == 5

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-INCOMPLETE_LAYERS_RA")
    def test_incomplete_layers_raises_error(self) -> None:
        """不完全な層でエラーが発生する"""
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(layer=DepthLayer.SENSORY, score=10.0),
        }
        with pytest.raises(ValueError, match=".*"):
            NarrativeDepthScore(layer_scores=layer_scores)

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-TOTAL_SCORE_CALCULAT")
    def test_total_score_calculation(self) -> None:
        """総合スコア計算が正しい"""
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(layer=DepthLayer.SENSORY, score=20.0),  # 100% * 0.15 = 15
            DepthLayer.EMOTIONAL: LayerScore(layer=DepthLayer.EMOTIONAL, score=20.0),  # 100% * 0.20 = 20
            DepthLayer.COGNITIVE: LayerScore(layer=DepthLayer.COGNITIVE, score=20.0),  # 100% * 0.30 = 30
            DepthLayer.MEMORIAL: LayerScore(layer=DepthLayer.MEMORIAL, score=20.0),  # 100% * 0.20 = 20
            DepthLayer.SYMBOLIC: LayerScore(layer=DepthLayer.SYMBOLIC, score=20.0),  # 100% * 0.15 = 15
        }
        depth_score = NarrativeDepthScore(layer_scores=layer_scores)
        # 基本スコア: 100 * 1.2(ボーナス) = 120 → 100(上限)
        assert depth_score.total_score == 100.0

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-ORGANIC_COMBINATION_")
    def test_organic_combination_bonus(self) -> None:
        """有機的結合ボーナスが正しく適用される"""
        # 3層以上が60%以上の場合、1.2倍ボーナス
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(layer=DepthLayer.SENSORY, score=16.0),  # 80%
            DepthLayer.EMOTIONAL: LayerScore(layer=DepthLayer.EMOTIONAL, score=16.0),  # 80%
            DepthLayer.COGNITIVE: LayerScore(layer=DepthLayer.COGNITIVE, score=16.0),  # 80%
            DepthLayer.MEMORIAL: LayerScore(layer=DepthLayer.MEMORIAL, score=4.0),  # 20%
            DepthLayer.SYMBOLIC: LayerScore(layer=DepthLayer.SYMBOLIC, score=4.0),  # 20%
        }
        depth_score = NarrativeDepthScore(layer_scores=layer_scores)
        # 基本: 80*0.15 + 80*0.20 + 80*0.30 + 20*0.20 + 20*0.15 = 12+16+24+4+3 = 59
        # ボーナス: 59 * 1.2 = 70.8
        assert depth_score.total_score == 70.8


class TestTextSegment:
    """TextSegment値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-VALID_SEGMENT_CREATI")
    def test_valid_segment_creation(self) -> None:
        """有効なセグメントが作成される"""
        segment = TextSegment(
            content="テストテキスト",
            start_position=0,
            end_position=10,
        )

        assert segment.content == "テストテキスト"
        assert segment.start_position == 0
        assert segment.end_position == 10

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-EMPTY_CONTENT_RAISES")
    def test_empty_content_raises_error(self) -> None:
        """空のコンテンツでエラーが発生する"""
        with pytest.raises(ValueError, match=".*"):
            TextSegment(content="", start_position=0, end_position=0)

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-INVALID_POSITION_RAI")
    def test_invalid_position_raises_error(self) -> None:
        """無効な位置でエラーが発生する"""
        with pytest.raises(ValueError, match=".*"):
            TextSegment(content="test", start_position=-1, end_position=0)

        with pytest.raises(ValueError, match=".*"):
            TextSegment(content="test", start_position=10, end_position=5)


class TestDepthPattern:
    """DepthPattern値オブジェクトのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-VALID_PATTERN_CREATI")
    def test_valid_pattern_creation(self) -> None:
        """有効なパターンが作成される"""
        pattern = DepthPattern(
            pattern=r"震え|痺れ",
            layer=DepthLayer.SENSORY,
            depth_level=2,
        )

        assert pattern.pattern == r"震え|痺れ"
        assert pattern.layer == DepthLayer.SENSORY
        assert pattern.depth_level == 2
        assert pattern.weight == 1.0

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-INVALID_DEPTH_LEVEL_")
    def test_invalid_depth_level_raises_error(self) -> None:
        """無効な深度レベルでエラーが発生する"""
        with pytest.raises(ValueError, match=".*"):
            DepthPattern(
                pattern="test",
                layer=DepthLayer.SENSORY,
                depth_level=0,
            )

        with pytest.raises(ValueError, match=".*"):
            DepthPattern(
                pattern="test",
                layer=DepthLayer.SENSORY,
                depth_level=4,
            )

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-INVALID_WEIGHT_RAISE")
    def test_invalid_weight_raises_error(self) -> None:
        """無効な重みでエラーが発生する"""
        with pytest.raises(ValueError, match=".*"):
            DepthPattern(
                pattern="test",
                layer=DepthLayer.SENSORY,
                depth_level=1,
                weight=0,
            )


class TestNarrativeDepthAnalyzer:
    """NarrativeDepthAnalyzerサービスのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-SIMPLE_TEXT_ANALYSIS")
    def test_simple_text_analysis(self) -> None:
        """シンプルなテキストの分析"""
        analyzer = NarrativeDepthAnalyzer()
        text = "震える手でスマホを掴む。不安な気持ちで画面を見つめた。"

        result = analyzer.analyze_depth(text)

        assert isinstance(result, NarrativeDepthScore)
        assert len(result.layer_scores) == 5

        # 感覚層(震える)と感情層(不安)にスコアが入る
        assert result.layer_scores[DepthLayer.SENSORY].score > 0
        assert result.layer_scores[DepthLayer.EMOTIONAL].score > 0

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-EMPTY_TEXT_RETURNS_Z")
    def test_empty_text_returns_zero_score(self) -> None:
        """空のテキストでゼロスコアが返される"""
        analyzer = NarrativeDepthAnalyzer()
        result = analyzer.analyze_depth("")

        for layer_score in result.layer_scores.values():
            assert layer_score.score == 0.0

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-COMPLEX_INNER_DESCRI")
    def test_complex_inner_description(self) -> None:
        """複雑な内面描写の分析"""
        analyzer = NarrativeDepthAnalyzer()
        text = """
        震える手でスマホを掴む。胸が締め付けられるような不安が襲ってくる。
        昔の記憶が蘇ってくる。あの時の彼女の笑顔。でも今は違う。
        まるで氷のような冷たさが心を包んでいる。
        """

        result = analyzer.analyze_depth(text)

        # 全ての層にある程度のスコアが入ることを期待
        assert result.layer_scores[DepthLayer.SENSORY].score > 0  # 震える、締め付け
        assert result.layer_scores[DepthLayer.EMOTIONAL].score > 0  # 不安
        assert result.layer_scores[DepthLayer.COGNITIVE].score > 0  # でも今は違う
        assert result.layer_scores[DepthLayer.MEMORIAL].score > 0  # 昔の記憶
        assert result.layer_scores[DepthLayer.SYMBOLIC].score > 0  # まるで氷のような

        assert result.total_score > 15.0  # 複雑な描写なので適度なスコア


class TestViewpointAwareEvaluator:
    """ViewpointAwareEvaluatorサービスのテスト"""

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-COMPLEXITY_LEVEL_ADJ")
    def test_complexity_level_adjustment(self) -> None:
        """複雑度レベルによる調整"""
        evaluator = ViewpointAwareEvaluator()

        # ベーススコアを作成
        layer_scores = {layer: LayerScore(layer=layer, score=10.0) for layer in DepthLayer}
        base_score = NarrativeDepthScore(layer_scores=layer_scores)

        # 複雑度「高」での調整
        adjusted = evaluator.adjust_for_viewpoint(base_score, "単一視点", "高")

        # ベーススコア * 1.2
        expected = base_score.total_score * 1.2
        assert adjusted == min(expected, 100.0)

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-SCORE_CAP_AT_100")
    def test_score_cap_at_100(self) -> None:
        """スコアが100を超えない"""
        evaluator = ViewpointAwareEvaluator()

        # 高いベーススコアを作成
        layer_scores = {layer: LayerScore(layer=layer, score=20.0) for layer in DepthLayer}
        base_score = NarrativeDepthScore(layer_scores=layer_scores)

        adjusted = evaluator.adjust_for_viewpoint(base_score, "単一視点", "高")
        assert adjusted == 100.0


# 統合テスト
class TestIntegration:
    """統合テストシナリオ"""

    @pytest.mark.spec("SPEC-DOMAIN_NARRATIVE_DEPTH-EPISODE_001_ANALYSIS")
    def test_episode_001_analysis_scenario(self) -> None:
        """第001話の分析シナリオ"""
        analyzer = NarrativeDepthAnalyzer()
        evaluator = ViewpointAwareEvaluator()

        # 第001話風のテキスト
        text = """
        震える手でスマホを掴む。画面の隅に見慣れない表示があった。
        記憶整合性:100%。まだ100%。でも、これが0%になった時――

        鏡に映る自分に、思わず問いかけた。この顔、この体、この記憶。
        全部自分のものだと信じて疑わなかった。でも、もしこれが誰かに売られる「商品」だとしたら?

        値札をつけられた記憶に、自分という存在の価値はあるの?
        """

        # 1. ドメインサービスで分析
        depth_result = analyzer.analyze_depth(text)

        # 2. 視点情報を考慮して調整
        final_score = evaluator.adjust_for_viewpoint(
            depth_result,
            "単一視点",
            complexity_level="中",
        )

        # 3. 内面描写が豊富なので、まずまずのスコアを期待
        assert depth_result.total_score > 2.0
        assert final_score > depth_result.total_score  # 調整により向上
        assert final_score <= 100.0
