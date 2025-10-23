"""Domain.services.narrative_depth_services
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations

"""内面描写深度評価のドメインサービス。

小説の内面描写の深度を分析・評価するためのドメインサービス。
心理描写、感情表現、内面的葛藤などを多層的に評価する。
"""


import re

from noveler.domain.value_objects.narrative_depth_models import (
    DepthLayer,
    DepthPattern,
    LayerScore,
    NarrativeDepthScore,
    TextSegment,
)


class NarrativeDepthAnalyzer:
    """内面描写深度分析のドメインサービス"""

    def __init__(self) -> None:
        self.patterns = self._initialize_patterns()

    def analyze_depth(self, text: str) -> NarrativeDepthScore:
        """テキストの内面描写深度を分析"""
        segments = self._segment_text(text)
        layer_scores = {}

        for layer in DepthLayer:
            score = self._calculate_layer_score(segments, layer)
            layer_scores[layer] = LayerScore(layer=layer, score=score)

        return NarrativeDepthScore(layer_scores=layer_scores)

    def _segment_text(self, text: str) -> list[TextSegment]:
        """テキストを段落単位でセグメント化"""
        paragraphs = text.split("\n\n")
        segments = []
        start_pos = 0

        for paragraph in paragraphs:
            if paragraph.strip():
                end_pos = start_pos + len(paragraph)
                segments.append(
                    TextSegment(
                        content=paragraph.strip(),
                        start_position=start_pos,
                        end_position=end_pos,
                    ),
                )

                start_pos = end_pos + 2  # \n\n分

        return segments

    def _calculate_layer_score(self, segments: list[TextSegment], layer: DepthLayer) -> float:
        """特定の層のスコアを計算"""
        layer_patterns = self._get_patterns_for_layer(layer)
        total_score = 0.0
        total_length = sum(len(segment.content) for segment in segments)

        if total_length == 0:
            return 0.0

        for segment in segments:
            segment_score = self._analyze_segment(segment, layer_patterns)
            # セグメント長による重み付け
            weight = len(segment.content) / total_length
            total_score += segment_score * weight

        # 20点満点にスケーリング
        return min(total_score, 20.0)

    def _get_patterns_for_layer(self, layer: DepthLayer) -> list[DepthPattern]:
        """特定の層のパターンを取得"""
        return [pattern for pattern in self.patterns if pattern.layer == layer]

    def _analyze_segment(self, segment: TextSegment, patterns: list[DepthPattern]) -> float:
        """セグメントの分析"""
        score = 0.0

        for pattern in patterns:
            matches = re.findall(pattern.pattern, segment.content)
            if matches:
                # マッチ数 × 深度レベル × 重み
                pattern_score = len(matches) * pattern.depth_level * pattern.weight
                score += pattern_score

        # セグメント内での密度を考慮
        if len(segment.content) > 0:
            density_factor = min(len(segment.content) / 100, 1.0)
            score *= density_factor

        return score

    def _initialize_patterns(self) -> list[DepthPattern]:
        """評価パターンの初期化"""
        patterns = []

        # 感覚層パターン(五感・身体感覚)
        patterns.extend(
            [
                DepthPattern(r"(震え|痺れ|熱|冷た|重|軽)", DepthLayer.SENSORY, 1),
                DepthPattern(r"(心臓|脈|鼓動|血|汗|涙)", DepthLayer.SENSORY, 2),
                DepthPattern(r"(締め付け|圧迫|解放|緊張|弛緩)", DepthLayer.SENSORY, 2),
                DepthPattern(r"まるで.*?のような(痛み|感覚)", DepthLayer.SENSORY, 3),
            ],
        )

        # 感情層パターン(感情の直接的・間接的表現)
        patterns.extend(
            [
                DepthPattern(r"(嬉しい|悲しい|怖い)", DepthLayer.EMOTIONAL, 1),
                DepthPattern(r"(不安|焦燥|懐かしい|愛しい)", DepthLayer.EMOTIONAL, 2),
                DepthPattern(r"(甘美な|痛いほどの|切ない)", DepthLayer.EMOTIONAL, 3),
                DepthPattern(r"胸が.*?くなる", DepthLayer.EMOTIONAL, 2),
                DepthPattern(r"襲ってくる", DepthLayer.EMOTIONAL, 2),
            ],
        )

        # 思考層パターン(論理的思考・推論・認知プロセス)
        patterns.extend(
            [
                DepthPattern(r"思った|考えた", DepthLayer.COGNITIVE, 1),
                DepthPattern(r"でも.*?違う", DepthLayer.COGNITIVE, 2),
                DepthPattern(r"でも.*?だから", DepthLayer.COGNITIVE, 2),
                DepthPattern(r"いや.*?違う", DepthLayer.COGNITIVE, 2),
                DepthPattern(r"もしかして.*?かも", DepthLayer.COGNITIVE, 2),
                DepthPattern(r"本当は.*?のに", DepthLayer.COGNITIVE, 3),
                DepthPattern(r"もし.*?だとしたら", DepthLayer.COGNITIVE, 3),
            ],
        )

        # 記憶層パターン(時間的・記憶的参照)
        patterns.extend(
            [
                DepthPattern(r"(あの時|昔|思い出)", DepthLayer.MEMORIAL, 2),
                DepthPattern(r"(今は|でも今|なのに)", DepthLayer.MEMORIAL, 1),
                DepthPattern(r"(もし|きっと|いつか)", DepthLayer.MEMORIAL, 1),
                DepthPattern(r".*?年前.*?", DepthLayer.MEMORIAL, 2),
            ],
        )

        # 象徴層パターン(比喩・隠喩・象徴的表現)
        patterns.extend(
            [
                DepthPattern(r"まるで.*?のような", DepthLayer.SYMBOLIC, 2),
                DepthPattern(r"まるで.*?が", DepthLayer.SYMBOLIC, 2),
                DepthPattern(r".*?は.*?だった", DepthLayer.SYMBOLIC, 3),
                DepthPattern(r"値札をつけられた", DepthLayer.SYMBOLIC, 3),
                DepthPattern(r"商品.*?としたら", DepthLayer.SYMBOLIC, 3),
            ],
        )

        return patterns


class ViewpointAwareEvaluator:
    """視点情報を考慮した評価サービス"""

    def adjust_for_viewpoint(
        self, base_score: NarrativeDepthScore, _viewpoint_type: str, complexity_level: str = "低"
    ) -> float:
        """視点情報に基づいてスコアを調整"""
        base_total = base_score.total_score

        # 複雑度による調整
        complexity_adjustments = {
            "低": 1.0,
            "中": 1.1,  # 内省型の場合は少し加点
            "高": 1.2,  # 複雑な視点変更がある場合は大きく加点
        }

        adjustment = complexity_adjustments.get(complexity_level, 1.0)
        adjusted_score = base_total * adjustment

        return min(adjusted_score, 100.0)
