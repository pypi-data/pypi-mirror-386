"""Domain.learning.services
Where: Domain services implementing learning workflows.
What: Manage learning data integration, analytics, and progress updates.
Why: Provide reusable logic for application-layer learning features.
"""

from __future__ import annotations

"""学習機能付き品質チェックドメイン - ドメインサービス"""


import re
import statistics
from dataclasses import dataclass
from typing import Any

from noveler.domain.initialization.value_objects import Genre
from noveler.domain.learning.value_objects import QualityMetric, WritingStyleProfile
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass
class StylePattern:
    """文体パターン"""

    pattern_type: str
    effectiveness_score: float
    confidence_level: float
    sample_count: int


class StyleLearningService:
    """文体学習ドメインサービス

    ビジネスルール:
    - 文体特徴抽出
    - パターン学習・効果測定
    - ジャンル固有特徴学習
    """

    def extract_style_features(self, episode_text: str) -> dict[str, float]:
        """文体特徴抽出"""
        features = {}

        # 基本的な文構造分析
        sentences = self._split_sentences(episode_text)
        features["avg_sentence_length"] = self._calculate_avg_sentence_length(sentences)
        features["sentence_count"] = len(sentences)

        # 会話比率計算
        features["dialogue_ratio"] = self._calculate_dialogue_ratio(episode_text)

        # 疑問文カウント
        features["question_count"] = len(re.findall(r"[?\?]", episode_text))

        # 感情表現カウント
        emotional_patterns = [
            r"[!!]{1,3}",
            r"[。.]{2,}",
            r"[~〜]{1,3}",
            r"(嬉しい|悲しい|怒り|驚き|不安|喜び)",
        ]
        features["emotional_expression_count"] = sum(
            len(re.findall(pattern, episode_text)) for pattern in emotional_patterns
        )

        # 段落数
        features["paragraph_count"] = len([p for p in episode_text.split("\n") if p.strip()])

        # 描写vs行動の比率
        features["descriptive_ratio"] = self._calculate_descriptive_ratio(episode_text)

        return features

    def _split_sentences(self, text: str) -> list[str]:
        """文分割"""
        # 簡略化実装
        sentence_endings = r"[。.!?!?]"
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]

    def _calculate_avg_sentence_length(self, sentences: list[str]) -> float:
        """平均文長計算"""
        if not sentences:
            return 0.0
        return statistics.mean(len(sentence) for sentence in sentences)

    def _calculate_dialogue_ratio(self, text: str) -> float:
        """会話比率計算"""
        # 「」内の文字数を会話として計算
        dialogue_matches = re.findall(r"「([^」]*)」", text)
        dialogue_chars = sum(len(match) for match in dialogue_matches)

        total_chars = len(text)
        if total_chars == 0:
            return 0.0

        return dialogue_chars / total_chars

    def _calculate_descriptive_ratio(self, text: str) -> float:
        """描写比率計算"""
        # 描写的表現のパターン
        descriptive_patterns = [
            r"(美しい|静かな|暖かい|冷たい|大きな|小さな)",  # 形容詞
            r"(〜のような|〜みたいな)",  # 比喩表現
            r"(風が|光が|音が|香りが)",  # 感覚的表現
        ]

        descriptive_count = sum(len(re.findall(pattern, text)) for pattern in descriptive_patterns)

        total_chars = len(text)
        if total_chars == 0:
            return 0.0

        # 描写表現密度として計算
        return min(1.0, descriptive_count / (total_chars / 100))

    def learn_writing_patterns(self, episodes: list[dict[str, Any]]) -> dict[str, Any]:
        """執筆パターン学習"""
        if len(episodes) < 3:
            return {"error": "学習に十分なエピソードがありません"}

        patterns = {}

        # 文長パターン分析
        sentence_lengths = []
        ratings = []

        for episode in episodes:
            features = self.extract_style_features(episode["text"])
            sentence_lengths.append(features["avg_sentence_length"])
            ratings.append(episode.get("rating", 3.0))

        # 最高評価エピソードの特徴を基準とする
        best_rating_idx = ratings.index(max(ratings))
        optimal_length = sentence_lengths[best_rating_idx]

        patterns["sentence_length_preference"] = "short" if optimal_length <= 28 else "long"
        patterns["optimal_sentence_length"] = optimal_length

        # 効果スコア計算(高評価エピソードの特徴との類似度)
        effectiveness = max(ratings) / 5.0  # 5点満点での正規化
        patterns["effectiveness_score"] = effectiveness

        return patterns

    def learn_genre_specific_style(self, episodes: list[dict], genre: str) -> WritingStyleProfile:
        """ジャンル固有文体学習"""
        if len(episodes) < 2:
            msg = "ジャンル学習に十分なデータがありません"
            raise ValueError(msg)

        # ジャンル固有特徴の抽出
        genre_features = {}

        for episode in episodes:
            features = self.extract_style_features(episode["text"])

            # ジャンル固有要素カウント
            if genre == Genre.FANTASY:
                fantasy_elements = len(
                    re.findall(
                        r"(魔法|ドラゴン|魔王|冒険|騎士|魔術師)",
                        episode["text"],
                    ),
                )

                features["fantasy_elements_density"] = fantasy_elements / len(episode["text"]) * 1000

            elif genre == Genre.SCIENCE_FICTION:
                sf_elements = len(
                    re.findall(
                        r"(ロボット|宇宙|未来|科学|技術|AI)",
                        episode["text"],
                    ),
                )

                features["sf_elements_density"] = sf_elements / len(episode["text"]) * 1000

            # 特徴量の平均化
            for feature_name, value in features.items():
                if feature_name not in genre_features:
                    genre_features[feature_name] = []
                genre_features[feature_name].append(value)

        # 平均値計算
        averaged_features = {name: statistics.mean(values) for name, values in genre_features.items()}

        return WritingStyleProfile(
            profile_id=f"genre_{genre.value}_profile",
            features=averaged_features,
            confidence_score=min(0.9, 0.5 + len(episodes) * 0.1),
            sample_count=len(episodes),
            last_updated=project_now().datetime,
            genre=genre.value if hasattr(genre, "value") else str(genre),
        )


class AdaptiveQualityService:
    """適応的品質評価ドメインサービス

    ビジネスルール:
    - 作家固有基準調整
    - リアルタイム学習・基準更新
    - 品質基準最適化
    """

    def adjust_criteria_for_author(
        self, standard_criteria: dict[str, float], author_profile: dict[str, Any]
    ) -> dict[str, float]:
        """作家固有基準調整"""
        adjusted_criteria = standard_criteria.copy()
        modified_keys: set[str] = set()

        # 文長の個人設定反映
        author_avg_length = author_profile.get_feature("avg_sentence_length")
        if author_avg_length > 0:
            if author_avg_length < 25:  # 短文好み:
                adjusted_criteria["sentence_length_tolerance"] = 1.3
                modified_keys.add("sentence_length_tolerance")
            elif author_avg_length > 50:  # 長文好み
                adjusted_criteria["sentence_length_tolerance"] = 0.8
                modified_keys.add("sentence_length_tolerance")

        # 会話比率の個人設定反映
        author_dialogue_ratio = author_profile.get_feature("dialogue_ratio")
        if author_dialogue_ratio > 0.5:  # 会話多用:
            adjusted_criteria["dialogue_ratio_weight"] = 1.2
            modified_keys.add("dialogue_ratio_weight")
        elif author_dialogue_ratio < 0.2:  # 会話少なめ
            adjusted_criteria["dialogue_ratio_weight"] = 0.8
            adjusted_criteria["descriptive_depth_weight"] = 1.2
            modified_keys.update({"dialogue_ratio_weight", "descriptive_depth_weight"})

        if author_profile.confidence_score < 0.5 and modified_keys:
            confidence_multiplier = author_profile.confidence_score
            for key in modified_keys:
                base_value = standard_criteria.get(key, adjusted_criteria[key])
                diff = adjusted_criteria[key] - base_value
                adjusted_criteria[key] = base_value + diff * confidence_multiplier

        return adjusted_criteria

    def update_criteria_from_feedback(self, episode_data: dict[str, Any]) -> dict[str, float]:
        """読者反応からの基準更新"""
        quality_scores = episode_data.get("quality_scores", {})
        reader_feedback = episode_data.get("reader_feedback", {})

        updated_weights = {}

        # 高評価エピソードの特徴を重視
        reader_rating = reader_feedback.get("rating", 3.0)
        if reader_rating >= 4.0:  # 高評価:
            # 該当エピソードの強い品質項目の重みを上げる
            for metric, score in quality_scores.items():
                if score >= 80:  # 高スコア項目:
                    weight_key = f"{metric}_weight"
                    updated_weights[weight_key] = 1.1

        elif reader_rating <= 2.5:  # 低評価
            # 該当エピソードの弱い品質項目の重みを上げる
            for metric, score in quality_scores.items():
                if score < 60:  # 低スコア項目:
                    weight_key = f"{metric}_weight"
                    updated_weights[weight_key] = 1.2  # より重視

        # 信頼度向上の計算
        comments = reader_feedback.get("comments", [])
        positive_keywords = ["読みやすい", "面白い", "続きが気になる", "良い"]
        positive_count = sum(1 for comment in comments for keyword in positive_keywords if keyword in comment)

        updated_weights["confidence_increase"] = positive_count * 0.05

        return updated_weights

    def optimize_quality_standards(
        self, historical_performance: list[dict[str, Any]], current_criteria: dict[str, float]
    ) -> dict[str, float]:
        """品質基準最適化"""
        if len(historical_performance) < 5:
            return current_criteria

        optimized_criteria = current_criteria.copy()

        # パフォーマンス分析
        high_performance_episodes = self._filter_high_performance_episodes(historical_performance)

        if high_performance_episodes:
            quality_patterns = self._analyze_quality_patterns(high_performance_episodes)
            optimized_criteria = self._calculate_optimized_criteria(quality_patterns, optimized_criteria)

        return optimized_criteria

    def _filter_high_performance_episodes(self, historical_performance: list[dict[str, Any]]) -> list[dict]:
        """高パフォーマンスエピソードをフィルタリング"""
        return [ep for ep in historical_performance if ep.get("reader_rating", 0) >= 4.0]

    def _analyze_quality_patterns(self, high_performance_episodes: list[dict]) -> dict:
        """品質パターンを分析"""
        quality_patterns = {}
        for episode in high_performance_episodes:
            for metric, score in episode.get("quality_scores", {}).items():
                if metric not in quality_patterns:
                    quality_patterns[metric] = []
                quality_patterns[metric].append(score)
        return quality_patterns

    def _calculate_optimized_criteria(self, quality_patterns: dict, current_criteria: dict[str, float]) -> dict:
        """最適化された基準を計算"""
        optimized_criteria = current_criteria.copy()

        for metric, scores in quality_patterns.items():
            if len(scores) >= 3:
                optimal_threshold = statistics.mean(scores)
                criteria_key = f"{metric}_target"
                if criteria_key in optimized_criteria:
                    # 現在基準と最適基準の加重平均
                    current_value = optimized_criteria[criteria_key]
                    optimized_criteria[criteria_key] = current_value * 0.7 + optimal_threshold * 0.3

        return optimized_criteria


class CorrelationAnalysisService:
    """相関分析ドメインサービス

    ビジネスルール:
    - 品質指標と読者反応の相関分析
    - 統計的有意性検証
    - アクション可能な洞察生成
    """

    def analyze_quality_reader_correlation(self, quality_data: list[dict], reader_data: list[dict]) -> list[dict]:
        """品質・読者反応相関分析"""
        if len(quality_data) != len(reader_data) or len(quality_data) < 5:
            return []

        correlations = []

        # 品質メトリック毎の相関分析
        for metric in QualityMetric:
            metric_scores = []
            reader_ratings = []

            for i in range(len(quality_data)):
                quality_score = quality_data[i].get(metric.value, 0)
                reader_rating = reader_data[i].get("rating", 0)

                if quality_score > 0 and reader_rating > 0:
                    metric_scores.append(quality_score)
                    reader_ratings.append(reader_rating)

            if len(metric_scores) >= 5:
                correlation = self._calculate_correlation(metric_scores, reader_ratings)
                significance = self._calculate_significance(correlation, len(metric_scores))

                correlations.append(
                    {
                        "metric": metric,
                        "correlation": correlation,
                        "significance": significance,
                        "sample_size": len(metric_scores),
                        "actionable_insight": self._generate_insight(metric, correlation, significance),
                    }
                )

        return correlations

    def _calculate_correlation(self, x: list[float], y: list[float]) -> float:
        """相関係数計算"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))

        sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(len(x)))
        sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(len(y)))

        if sum_sq_x == 0 or sum_sq_y == 0:
            return 0.0

        denominator = (sum_sq_x * sum_sq_y) ** 0.5
        return numerator / denominator

    def _calculate_significance(self, correlation: float, sample_size: int) -> float:
        """統計的有意性計算(簡略化)"""
        # 簡略化実装:サンプルサイズと相関係数による概算
        if sample_size < 5:
            return 1.0  # 有意でない

        # 概算p値計算
        t_stat = abs(correlation) * ((sample_size - 2) ** 0.5) / ((1 - correlation**2) ** 0.5)

        # 簡略化p値推定
        if t_stat > 2.5:
            return 0.01
        if t_stat > 2.0:
            return 0.05
        if t_stat > 1.5:
            return 0.1
        return 0.2

    def _generate_insight(self, metric: str, correlation: float, significance: float = 0.05) -> str:
        """アクション可能な洞察生成"""
        if significance > 0.05:
            return f"{metric.value}と読者評価の間に有意な関係は見つかりませんでした"

        if correlation > 0.5:
            return f"{metric.value}の向上が読者評価向上に強く寄与しています。この指標を重点的に改善してください"
        if correlation > 0.3:
            return f"{metric.value}の向上が読者評価向上に寄与しています。改善を検討してください"
        if correlation < -0.3:
            return f"{metric.value}の過度な重視が読者評価を下げる可能性があります。バランスを見直してください"
        return f"{metric.value}と読者評価の関係は限定的です"
