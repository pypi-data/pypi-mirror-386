#!/usr/bin/env python3
"""NarrativeDepthServicesのユニットテスト

TDD原則に従い、内面描写深度評価サービスのビジネスロジックをテスト


仕様書: SPEC-UNIT-TEST
"""

import pytest

from noveler.domain.services.narrative_depth_services import (
    NarrativeDepthAnalyzer,
    ViewpointAwareEvaluator,
)
from noveler.domain.value_objects.narrative_depth_models import (
    DepthLayer,
    LayerScore,
    NarrativeDepthScore,
    TextSegment,
)


class TestNarrativeDepthAnalyzer:
    """NarrativeDepthAnalyzerのテスト"""

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-INITIALIZE_ANALYZER")
    def test_initialize_analyzer(self) -> None:
        """アナライザーの初期化"""
        # When
        analyzer = NarrativeDepthAnalyzer()

        # Then
        assert analyzer.patterns is not None
        assert len(analyzer.patterns) > 0

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ANALYZE_DEPTH_SIMPLE")
    def test_analyze_depth_simple_text(self) -> None:
        """単純なテキストの深度分析"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        text = "彼は嬉しいと思った。"

        # When
        result = analyzer.analyze_depth(text)

        # Then
        assert isinstance(result, NarrativeDepthScore)
        assert len(result.layer_scores) == 5  # 全ての層が含まれる
        assert all(isinstance(score, LayerScore) for score in result.layer_scores.values())

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ANALYZE_DEPTH_EMPTY_")
    def test_analyze_depth_empty_text(self) -> None:
        """空のテキストの深度分析"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        text = ""

        # When
        result = analyzer.analyze_depth(text)

        # Then
        assert isinstance(result, NarrativeDepthScore)
        # 空のテキストなので全てのスコアは0
        for layer_score in result.layer_scores.values():
            assert layer_score.score == 0.0

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ANALYZE_DEPTH_SENSOR")
    def test_analyze_depth_sensory_layer(self) -> None:
        """感覚層の深度分析"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        text = "心臓が激しく鼓動し、手が震えた。冷たい汗が背中を流れる。"

        # When
        result = analyzer.analyze_depth(text)

        # Then
        sensory_score = result.layer_scores[DepthLayer.SENSORY]
        assert sensory_score.score > 0  # 感覚層のスコアがあること

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ANALYZE_DEPTH_EMOTIO")
    def test_analyze_depth_emotional_layer(self) -> None:
        """感情層の深度分析"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        text = "胸が熱くなる感覚に襲われた。不安と焦燥感が入り混じり、切ない気持ちでいっぱいだった。"

        # When
        result = analyzer.analyze_depth(text)

        # Then
        emotional_score = result.layer_scores[DepthLayer.EMOTIONAL]
        assert emotional_score.score > 0  # 感情層のスコアがあること

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ANALYZE_DEPTH_COGNIT")
    def test_analyze_depth_cognitive_layer(self) -> None:
        """思考層の深度分析"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        text = "もしかして彼女は気づいているのかもしれない。いや、違う。でも、そうだとしたら..."

        # When
        result = analyzer.analyze_depth(text)

        # Then
        cognitive_score = result.layer_scores[DepthLayer.COGNITIVE]
        assert cognitive_score.score > 0  # 思考層のスコアがあること

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ANALYZE_DEPTH_MEMORI")
    def test_analyze_depth_memorial_layer(self) -> None:
        """記憶層の深度分析"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        text = "あの時の記憶が蘇る。5年前の夏、同じような状況だった。でも今は違う。"

        # When
        result = analyzer.analyze_depth(text)

        # Then
        memorial_score = result.layer_scores[DepthLayer.MEMORIAL]
        assert memorial_score.score > 0  # 記憶層のスコアがあること

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ANALYZE_DEPTH_SYMBOL")
    def test_analyze_depth_symbolic_layer(self) -> None:
        """象徴層の深度分析"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        text = "彼女の存在は、まるで夜空に輝く星のようだった。手の届かない光。"

        # When
        result = analyzer.analyze_depth(text)

        # Then
        symbolic_score = result.layer_scores[DepthLayer.SYMBOLIC]
        assert symbolic_score.score > 0  # 象徴層のスコアがあること

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ANALYZE_DEPTH_MULTI_")
    def test_analyze_depth_multi_paragraph(self) -> None:
        """複数段落のテキスト分析"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        text = """彼の心臓が激しく鼓動した。

あの時の記憶が蘇る。

もしかして、全ては運命だったのかもしれない。"""

        # When
        result = analyzer.analyze_depth(text)

        # Then
        assert isinstance(result, NarrativeDepthScore)
        # 複数の層でスコアがあること
        scores_with_value = [score for score in result.layer_scores.values() if score.score > 0]
        assert len(scores_with_value) >= 2

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-SEGMENT_TEXT_SINGLE_")
    def test_segment_text_single_paragraph(self) -> None:
        """単一段落のセグメント化"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        text = "これは単一の段落です。"

        # When
        segments = analyzer._segment_text(text)

        # Then
        assert len(segments) == 1
        assert segments[0].content == "これは単一の段落です。"
        assert segments[0].start_position == 0
        assert segments[0].end_position == len(text)

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-SEGMENT_TEXT_MULTIPL")
    def test_segment_text_multiple_paragraphs(self) -> None:
        """複数段落のセグメント化"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        text = "第一段落。\n\n第二段落。\n\n第三段落。"

        # When
        segments = analyzer._segment_text(text)

        # Then
        assert len(segments) == 3
        assert segments[0].content == "第一段落。"
        assert segments[1].content == "第二段落。"
        assert segments[2].content == "第三段落。"

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-SEGMENT_TEXT_WITH_EM")
    def test_segment_text_with_empty_lines(self) -> None:
        """空行を含むテキストのセグメント化"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        text = "段落1。\n\n\n\n段落2。"

        # When
        segments = analyzer._segment_text(text)

        # Then
        assert len(segments) == 2  # 空の段落は無視される

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-CALCULATE_LAYER_SCOR")
    def test_calculate_layer_score_empty_segments(self) -> None:
        """空のセグメントリストでのスコア計算"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        segments = []

        # When
        score = analyzer._calculate_layer_score(segments, DepthLayer.SENSORY)

        # Then
        assert score == 0.0

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-GET_PATTERNS_FOR_LAY")
    def test_get_patterns_for_layer(self) -> None:
        """特定の層のパターン取得"""
        # Given
        analyzer = NarrativeDepthAnalyzer()

        # When
        sensory_patterns = analyzer._get_patterns_for_layer(DepthLayer.SENSORY)
        emotional_patterns = analyzer._get_patterns_for_layer(DepthLayer.EMOTIONAL)

        # Then
        assert all(p.layer == DepthLayer.SENSORY for p in sensory_patterns)
        assert all(p.layer == DepthLayer.EMOTIONAL for p in emotional_patterns)
        assert len(sensory_patterns) > 0
        assert len(emotional_patterns) > 0

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ANALYZE_SEGMENT_WITH")
    def test_analyze_segment_with_matches(self) -> None:
        """マッチするパターンがあるセグメントの分析"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        segment = TextSegment("心臓が鼓動し、震えが止まらない。", 0, 20)
        patterns = analyzer._get_patterns_for_layer(DepthLayer.SENSORY)

        # When
        score = analyzer._analyze_segment(segment, patterns)

        # Then
        assert score > 0  # パターンにマッチするのでスコアが付く

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ANALYZE_SEGMENT_WITH")
    def test_analyze_segment_without_matches(self) -> None:
        """マッチするパターンがないセグメントの分析"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        segment = TextSegment("今日は晴れです。", 0, 10)
        patterns = analyzer._get_patterns_for_layer(DepthLayer.SENSORY)

        # When
        score = analyzer._analyze_segment(segment, patterns)

        # Then
        assert score == 0.0  # パターンにマッチしないのでスコアは0

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-INITIALIZE_PATTERNS_")
    def test_initialize_patterns_coverage(self) -> None:
        """全ての層にパターンが定義されていること"""
        # Given
        analyzer = NarrativeDepthAnalyzer()

        # When
        patterns = analyzer._initialize_patterns()

        # Then
        layers_with_patterns = {p.layer for p in patterns}
        assert layers_with_patterns == set(DepthLayer)  # 全ての層がカバーされている

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ANALYZE_DEPTH_MAX_SC")
    def test_analyze_depth_max_score_limit(self) -> None:
        """スコアが上限を超えないこと"""
        # Given
        analyzer = NarrativeDepthAnalyzer()
        # 多くのパターンにマッチする非常に長いテキスト
        text = "心臓が鼓動し、震えが止まらない。" * 50

        # When
        result = analyzer.analyze_depth(text)

        # Then
        # 各層のスコアは20点を超えない
        for layer_score in result.layer_scores.values():
            assert layer_score.score <= 20.0


class TestViewpointAwareEvaluator:
    """ViewpointAwareEvaluatorのテスト"""

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ADJUST_FOR_VIEWPOINT")
    def test_adjust_for_viewpoint_low_complexity(self) -> None:
        """低複雑度での視点調整"""
        # Given
        evaluator = ViewpointAwareEvaluator()
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(DepthLayer.SENSORY, 10.0),
            DepthLayer.EMOTIONAL: LayerScore(DepthLayer.EMOTIONAL, 10.0),
            DepthLayer.COGNITIVE: LayerScore(DepthLayer.COGNITIVE, 10.0),
            DepthLayer.MEMORIAL: LayerScore(DepthLayer.MEMORIAL, 10.0),
            DepthLayer.SYMBOLIC: LayerScore(DepthLayer.SYMBOLIC, 10.0),
        }
        base_score = NarrativeDepthScore(layer_scores=layer_scores)

        # When
        adjusted = evaluator.adjust_for_viewpoint(base_score, "一人称", "低")

        # Then
        assert adjusted == 50.0  # 基本スコア50 × 1.0 = 50

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ADJUST_FOR_VIEWPOINT")
    def test_adjust_for_viewpoint_medium_complexity(self) -> None:
        """中複雑度での視点調整"""
        # Given
        evaluator = ViewpointAwareEvaluator()
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(DepthLayer.SENSORY, 10.0),
            DepthLayer.EMOTIONAL: LayerScore(DepthLayer.EMOTIONAL, 10.0),
            DepthLayer.COGNITIVE: LayerScore(DepthLayer.COGNITIVE, 10.0),
            DepthLayer.MEMORIAL: LayerScore(DepthLayer.MEMORIAL, 10.0),
            DepthLayer.SYMBOLIC: LayerScore(DepthLayer.SYMBOLIC, 10.0),
        }
        base_score = NarrativeDepthScore(layer_scores=layer_scores)

        # When
        adjusted = evaluator.adjust_for_viewpoint(base_score, "一人称", "中")

        # Then
        assert abs(adjusted - 55.0) < 0.01  # 基本スコア50 × 1.1 = 55

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ADJUST_FOR_VIEWPOINT")
    def test_adjust_for_viewpoint_high_complexity(self) -> None:
        """高複雑度での視点調整"""
        # Given
        evaluator = ViewpointAwareEvaluator()
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(DepthLayer.SENSORY, 10.0),
            DepthLayer.EMOTIONAL: LayerScore(DepthLayer.EMOTIONAL, 10.0),
            DepthLayer.COGNITIVE: LayerScore(DepthLayer.COGNITIVE, 10.0),
            DepthLayer.MEMORIAL: LayerScore(DepthLayer.MEMORIAL, 10.0),
            DepthLayer.SYMBOLIC: LayerScore(DepthLayer.SYMBOLIC, 10.0),
        }
        base_score = NarrativeDepthScore(layer_scores=layer_scores)

        # When
        adjusted = evaluator.adjust_for_viewpoint(base_score, "三人称限定", "高")

        # Then
        assert abs(adjusted - 60.0) < 0.01  # 基本スコア50 × 1.2 = 60

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ADJUST_FOR_VIEWPOINT")
    def test_adjust_for_viewpoint_unknown_complexity(self) -> None:
        """未知の複雑度での視点調整"""
        # Given
        evaluator = ViewpointAwareEvaluator()
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(DepthLayer.SENSORY, 10.0),
            DepthLayer.EMOTIONAL: LayerScore(DepthLayer.EMOTIONAL, 10.0),
            DepthLayer.COGNITIVE: LayerScore(DepthLayer.COGNITIVE, 10.0),
            DepthLayer.MEMORIAL: LayerScore(DepthLayer.MEMORIAL, 10.0),
            DepthLayer.SYMBOLIC: LayerScore(DepthLayer.SYMBOLIC, 10.0),
        }
        base_score = NarrativeDepthScore(layer_scores=layer_scores)

        # When
        adjusted = evaluator.adjust_for_viewpoint(base_score, "一人称", "不明")

        # Then
        assert adjusted == 50.0  # デフォルトは1.0倍

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ADJUST_FOR_VIEWPOINT")
    def test_adjust_for_viewpoint_max_score_cap(self) -> None:
        """調整後スコアが100を超えない"""
        # Given
        evaluator = ViewpointAwareEvaluator()
        # 高いスコアを持つベーススコア
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(DepthLayer.SENSORY, 18.0),
            DepthLayer.EMOTIONAL: LayerScore(DepthLayer.EMOTIONAL, 18.0),
            DepthLayer.COGNITIVE: LayerScore(DepthLayer.COGNITIVE, 18.0),
            DepthLayer.MEMORIAL: LayerScore(DepthLayer.MEMORIAL, 18.0),
            DepthLayer.SYMBOLIC: LayerScore(DepthLayer.SYMBOLIC, 18.0),
        }
        base_score = NarrativeDepthScore(layer_scores=layer_scores)

        # When
        adjusted = evaluator.adjust_for_viewpoint(base_score, "群像", "高")

        # Then
        assert adjusted == 100.0  # 90 * 1.2 = 108だが、100でキャップされる

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_SERVICES-ADJUST_FOR_VIEWPOINT")
    def test_adjust_for_viewpoint_with_bonus(self) -> None:
        """有機的結合ボーナスを含むスコアの調整"""
        # Given
        evaluator = ViewpointAwareEvaluator()
        # 3つ以上の層が60%以上(有機的結合ボーナスあり)
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(DepthLayer.SENSORY, 15.0),  # 75%
            DepthLayer.EMOTIONAL: LayerScore(DepthLayer.EMOTIONAL, 14.0),  # 70%
            DepthLayer.COGNITIVE: LayerScore(DepthLayer.COGNITIVE, 16.0),  # 80%
            DepthLayer.MEMORIAL: LayerScore(DepthLayer.MEMORIAL, 10.0),  # 50%
            DepthLayer.SYMBOLIC: LayerScore(DepthLayer.SYMBOLIC, 8.0),  # 40%
        }
        base_score = NarrativeDepthScore(layer_scores=layer_scores)

        # When
        adjusted = evaluator.adjust_for_viewpoint(base_score, "一人称", "中")

        # Then
        # base_score.total_score = 78.3(ボーナス込み)
        # 78.3 * 1.1 = 86.13
        assert abs(adjusted - 86.13) < 0.01
