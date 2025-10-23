#!/usr/bin/env python3
"""NarrativeDepthModelsのユニットテスト

TDD原則に従い、内面描写深度評価モデルのビジネスロジックをテスト


仕様書: SPEC-UNIT-TEST
"""

import pytest

from noveler.domain.value_objects.narrative_depth_models import (
    DepthLayer,
    DepthPattern,
    LayerScore,
    NarrativeDepthScore,
    TextSegment,
)


class TestDepthLayer:
    """DepthLayerのテスト"""

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-ALL_LAYERS_DEFINED")
    def test_all_layers_defined(self) -> None:
        """全ての深度層が定義されている"""
        # When
        layers = list(DepthLayer)

        # Then
        assert DepthLayer.SENSORY in layers
        assert DepthLayer.EMOTIONAL in layers
        assert DepthLayer.COGNITIVE in layers
        assert DepthLayer.MEMORIAL in layers
        assert DepthLayer.SYMBOLIC in layers
        assert len(layers) == 5

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-LAYER_VALUES")
    def test_layer_values(self) -> None:
        """深度層の値が正しい"""
        assert DepthLayer.SENSORY.value == "感覚層"
        assert DepthLayer.EMOTIONAL.value == "感情層"
        assert DepthLayer.COGNITIVE.value == "思考層"
        assert DepthLayer.MEMORIAL.value == "記憶層"
        assert DepthLayer.SYMBOLIC.value == "象徴層"


class TestLayerScore:
    """LayerScoreのテスト"""

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-CREATE_VALID_LAYER_S")
    def test_create_valid_layer_score(self) -> None:
        """有効なレイヤースコアの作成"""
        # When
        score = LayerScore(layer=DepthLayer.EMOTIONAL, score=15.0)

        # Then
        assert score.layer == DepthLayer.EMOTIONAL
        assert score.score == 15.0
        assert score.max_score == 20.0

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-LAYER_SCORE_PERCENTA")
    def test_layer_score_percentage(self) -> None:
        """パーセンテージ計算"""
        # Given
        score = LayerScore(layer=DepthLayer.COGNITIVE, score=10.0)

        # When
        percentage = score.percentage

        # Then
        assert percentage == 50.0  # 10/20 * 100

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-LAYER_SCORE_FULL_MAR")
    def test_layer_score_full_marks(self) -> None:
        """満点のスコア"""
        # Given
        score = LayerScore(layer=DepthLayer.SYMBOLIC, score=20.0)

        # When/Then
        assert score.percentage == 100.0

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-LAYER_SCORE_ZERO")
    def test_layer_score_zero(self) -> None:
        """ゼロスコア"""
        # Given
        score = LayerScore(layer=DepthLayer.MEMORIAL, score=0.0)

        # When/Then
        assert score.percentage == 0.0

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-INVALID_LAYER_SCORE_")
    def test_invalid_layer_score_negative(self) -> None:
        """負のスコアはエラー"""
        # When/Then
        with pytest.raises(ValueError, match="Score must be between 0 and 20.0"):
            LayerScore(layer=DepthLayer.SENSORY, score=-1.0)

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-INVALID_LAYER_SCORE_")
    def test_invalid_layer_score_over_max(self) -> None:
        """最大値を超えるスコアはエラー"""
        # When/Then
        with pytest.raises(ValueError, match="Score must be between 0 and 20.0"):
            LayerScore(layer=DepthLayer.EMOTIONAL, score=21.0)

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-LAYER_SCORE_IMMUTABI")
    def test_layer_score_immutability(self) -> None:
        """レイヤースコアは不変であること"""
        # Given
        score = LayerScore(layer=DepthLayer.COGNITIVE, score=15.0)

        # When/Then
        with pytest.raises(AttributeError, match=".*"):
            score.score = 18.0


class TestNarrativeDepthScore:
    """NarrativeDepthScoreのテスト"""

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-CREATE_VALID_NARRATI")
    def test_create_valid_narrative_depth_score(self) -> None:
        """有効な総合スコアの作成"""
        # Given
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(DepthLayer.SENSORY, 10.0),
            DepthLayer.EMOTIONAL: LayerScore(DepthLayer.EMOTIONAL, 12.0),
            DepthLayer.COGNITIVE: LayerScore(DepthLayer.COGNITIVE, 15.0),
            DepthLayer.MEMORIAL: LayerScore(DepthLayer.MEMORIAL, 8.0),
            DepthLayer.SYMBOLIC: LayerScore(DepthLayer.SYMBOLIC, 5.0),
        }

        # When
        depth_score = NarrativeDepthScore(layer_scores=layer_scores)

        # Then
        assert depth_score.layer_scores == layer_scores

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-NARRATIVE_DEPTH_SCOR")
    def test_narrative_depth_score_missing_layer(self) -> None:
        """レイヤーが不足している場合はエラー"""
        # Given
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(DepthLayer.SENSORY, 10.0),
            DepthLayer.EMOTIONAL: LayerScore(DepthLayer.EMOTIONAL, 12.0),
            # COGNITIVEが不足
            DepthLayer.MEMORIAL: LayerScore(DepthLayer.MEMORIAL, 8.0),
            DepthLayer.SYMBOLIC: LayerScore(DepthLayer.SYMBOLIC, 5.0),
        }

        # When/Then
        with pytest.raises(ValueError, match="All depth layers must be included"):
            NarrativeDepthScore(layer_scores=layer_scores)

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-TOTAL_SCORE_WITHOUT_")
    def test_total_score_without_bonus(self) -> None:
        """ボーナスなしの総合スコア計算"""
        # Given
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(DepthLayer.SENSORY, 10.0),  # 50%
            DepthLayer.EMOTIONAL: LayerScore(DepthLayer.EMOTIONAL, 10.0),  # 50%
            DepthLayer.COGNITIVE: LayerScore(DepthLayer.COGNITIVE, 10.0),  # 50%
            DepthLayer.MEMORIAL: LayerScore(DepthLayer.MEMORIAL, 10.0),  # 50%
            DepthLayer.SYMBOLIC: LayerScore(DepthLayer.SYMBOLIC, 10.0),  # 50%
        }
        depth_score = NarrativeDepthScore(layer_scores=layer_scores)

        # When
        total = depth_score.total_score

        # Then
        # 50 * 0.15 + 50 * 0.20 + 50 * 0.30 + 50 * 0.20 + 50 * 0.15 = 50.0
        assert total == 50.0

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-TOTAL_SCORE_WITH_BON")
    def test_total_score_with_bonus(self) -> None:
        """有機的結合ボーナスありの総合スコア計算"""
        # Given
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(DepthLayer.SENSORY, 15.0),  # 75%
            DepthLayer.EMOTIONAL: LayerScore(DepthLayer.EMOTIONAL, 14.0),  # 70%
            DepthLayer.COGNITIVE: LayerScore(DepthLayer.COGNITIVE, 16.0),  # 80%
            DepthLayer.MEMORIAL: LayerScore(DepthLayer.MEMORIAL, 10.0),  # 50%
            DepthLayer.SYMBOLIC: LayerScore(DepthLayer.SYMBOLIC, 8.0),  # 40%
        }
        depth_score = NarrativeDepthScore(layer_scores=layer_scores)

        # When
        total = depth_score.total_score

        # Then
        # Base: 75*0.15 + 70*0.20 + 80*0.30 + 50*0.20 + 40*0.15 = 65.25
        # With 1.2 bonus: 65.25 * 1.2 = 78.3
        assert total == 78.3

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-TOTAL_SCORE_WITH_BON")
    def test_total_score_with_bonus_capped_at_100(self) -> None:
        """ボーナス適用後も100を超えない"""
        # Given
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(DepthLayer.SENSORY, 20.0),  # 100%
            DepthLayer.EMOTIONAL: LayerScore(DepthLayer.EMOTIONAL, 20.0),  # 100%
            DepthLayer.COGNITIVE: LayerScore(DepthLayer.COGNITIVE, 20.0),  # 100%
            DepthLayer.MEMORIAL: LayerScore(DepthLayer.MEMORIAL, 20.0),  # 100%
            DepthLayer.SYMBOLIC: LayerScore(DepthLayer.SYMBOLIC, 20.0),  # 100%
        }
        depth_score = NarrativeDepthScore(layer_scores=layer_scores)

        # When
        total = depth_score.total_score

        # Then
        assert total == 100.0  # 100 * 1.2 = 120, but capped at 100

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-HAS_ORGANIC_COMBINAT")
    def test_has_organic_combination_true(self) -> None:
        """3つ以上の層が60%以上で有機的結合と判定"""
        # Given
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(DepthLayer.SENSORY, 12.0),  # 60%
            DepthLayer.EMOTIONAL: LayerScore(DepthLayer.EMOTIONAL, 13.0),  # 65%
            DepthLayer.COGNITIVE: LayerScore(DepthLayer.COGNITIVE, 14.0),  # 70%
            DepthLayer.MEMORIAL: LayerScore(DepthLayer.MEMORIAL, 8.0),  # 40%
            DepthLayer.SYMBOLIC: LayerScore(DepthLayer.SYMBOLIC, 6.0),  # 30%
        }
        depth_score = NarrativeDepthScore(layer_scores=layer_scores)

        # When/Then
        assert depth_score._has_organic_combination() is True

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-HAS_ORGANIC_COMBINAT")
    def test_has_organic_combination_false(self) -> None:
        """2つ以下の層が60%以上では有機的結合と判定されない"""
        # Given
        layer_scores = {
            DepthLayer.SENSORY: LayerScore(DepthLayer.SENSORY, 12.0),  # 60%
            DepthLayer.EMOTIONAL: LayerScore(DepthLayer.EMOTIONAL, 13.0),  # 65%
            DepthLayer.COGNITIVE: LayerScore(DepthLayer.COGNITIVE, 10.0),  # 50%
            DepthLayer.MEMORIAL: LayerScore(DepthLayer.MEMORIAL, 8.0),  # 40%
            DepthLayer.SYMBOLIC: LayerScore(DepthLayer.SYMBOLIC, 6.0),  # 30%
        }
        depth_score = NarrativeDepthScore(layer_scores=layer_scores)

        # When/Then
        assert depth_score._has_organic_combination() is False


class TestTextSegment:
    """TextSegmentのテスト"""

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-CREATE_VALID_TEXT_SE")
    def test_create_valid_text_segment(self) -> None:
        """有効なテキストセグメントの作成"""
        # When
        segment = TextSegment(
            content="彼女の瞳に映る夕焼けは、まるで燃え尽きる前の蝋燭のようだった。", start_position=0, end_position=30
        )

        # Then
        assert segment.content == "彼女の瞳に映る夕焼けは、まるで燃え尽きる前の蝋燭のようだった。"
        assert segment.start_position == 0
        assert segment.end_position == 30

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-TEXT_SEGMENT_EMPTY_C")
    def test_text_segment_empty_content(self) -> None:
        """空のコンテンツはエラー"""
        # When/Then
        with pytest.raises(ValueError, match="Content cannot be empty"):
            TextSegment(content="", start_position=0, end_position=0)

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-TEXT_SEGMENT_INVALID")
    def test_text_segment_invalid_start_position(self) -> None:
        """負の開始位置はエラー"""
        # When/Then
        with pytest.raises(ValueError, match="Invalid position range"):
            TextSegment(content="テスト", start_position=-1, end_position=5)

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-TEXT_SEGMENT_INVALID")
    def test_text_segment_invalid_end_position(self) -> None:
        """終了位置が開始位置より小さい場合はエラー"""
        # When/Then
        with pytest.raises(ValueError, match="Invalid position range"):
            TextSegment(content="テスト", start_position=10, end_position=5)

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-TEXT_SEGMENT_IMMUTAB")
    def test_text_segment_immutability(self) -> None:
        """テキストセグメントは不変であること"""
        # Given
        segment = TextSegment(content="テスト", start_position=0, end_position=10)

        # When/Then
        with pytest.raises(AttributeError, match=".*"):
            segment.content = "変更"


class TestDepthPattern:
    """DepthPatternのテスト"""

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-CREATE_VALID_DEPTH_P")
    def test_create_valid_depth_pattern(self) -> None:
        """有効な深度パターンの作成"""
        # When
        pattern = DepthPattern(pattern="(香り|匂い|音|触感|味)", layer=DepthLayer.SENSORY, depth_level=2, weight=1.5)

        # Then
        assert pattern.pattern == "(香り|匂い|音|触感|味)"
        assert pattern.layer == DepthLayer.SENSORY
        assert pattern.depth_level == 2
        assert pattern.weight == 1.5

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-DEPTH_PATTERN_DEFAUL")
    def test_depth_pattern_default_weight(self) -> None:
        """デフォルトの重み"""
        # When
        pattern = DepthPattern(pattern="pattern", layer=DepthLayer.EMOTIONAL, depth_level=1)

        # Then
        assert pattern.weight == 1.0

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-DEPTH_PATTERN_INVALI")
    def test_depth_pattern_invalid_depth_level_low(self) -> None:
        """深度レベルが1未満はエラー"""
        # When/Then
        with pytest.raises(ValueError, match="Depth level must be between 1 and 3"):
            DepthPattern(pattern="pattern", layer=DepthLayer.COGNITIVE, depth_level=0)

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-DEPTH_PATTERN_INVALI")
    def test_depth_pattern_invalid_depth_level_high(self) -> None:
        """深度レベルが3を超えるとエラー"""
        # When/Then
        with pytest.raises(ValueError, match="Depth level must be between 1 and 3"):
            DepthPattern(pattern="pattern", layer=DepthLayer.MEMORIAL, depth_level=4)

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-DEPTH_PATTERN_INVALI")
    def test_depth_pattern_invalid_weight(self) -> None:
        """重みが0以下はエラー"""
        # When/Then
        with pytest.raises(ValueError, match="Weight must be positive"):
            DepthPattern(pattern="pattern", layer=DepthLayer.SYMBOLIC, depth_level=2, weight=0.0)

    @pytest.mark.spec("SPEC-NARRATIVE_DEPTH_MODELS-DEPTH_PATTERN_IMMUTA")
    def test_depth_pattern_immutability(self) -> None:
        """深度パターンは不変であること"""
        # Given
        pattern = DepthPattern(pattern="test", layer=DepthLayer.SENSORY, depth_level=1)

        # When/Then
        with pytest.raises(AttributeError, match=".*"):
            pattern.depth_level = 2
