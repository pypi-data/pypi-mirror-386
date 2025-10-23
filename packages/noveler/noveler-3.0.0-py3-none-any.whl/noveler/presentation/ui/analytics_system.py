"""
データ分析システム

執筆プロセスの統計分析、承認振幅分析、キャラクター個性評価機能を提供。
感情表現多様性分析、読者エンゲージメント予測、品質メトリクス分析を実装。
"""

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from noveler.infrastructure.utils.numpy_compat import get_numpy
from noveler.presentation.shared.shared_utilities import _get_console
from noveler.infrastructure.performance.comprehensive_performance_optimizer import performance_monitor

np = get_numpy()


def get_console():
    return _get_console()


@dataclass
class EmotionProfile:
    """感情プロファイル"""
    character_name: str
    episode_number: int
    positive_score: float
    negative_score: float
    neutral_score: float
    volatility: float  # 感情の変動幅
    complexity: float  # 感情の複雑さ
    dominant_emotions: list[str]
    emotion_transitions: list[tuple[str, str, float]]  # (from, to, strength)


@dataclass
class NarrativeMetrics:
    """物語メトリクス"""
    episode_number: int
    word_count: int
    sentence_count: int
    paragraph_count: int
    dialogue_ratio: float
    description_ratio: float
    action_ratio: float
    pacing_score: float
    readability_score: float
    engagement_score: float


@dataclass
class QualityMetrics:
    """品質メトリクス"""
    episode_number: int
    overall_quality: float
    plot_consistency: float
    character_development: float
    dialogue_quality: float
    description_quality: float
    technical_accuracy: float
    creativity_score: float
    originality_score: float


class WritingAnalyticsSystem:
    """執筆分析システム

    執筆データの包括的分析機能を提供。
    感情分析、文体分析、品質評価、読者エンゲージメント予測を統合。
    """

    def __init__(self, project_root: str) -> None:
        self.project_root = Path(project_root)
        self.console = get_console()

        # 分析データ格納
        self.emotion_profiles: dict[int, dict[str, EmotionProfile]] = {}
        self.narrative_metrics: dict[int, NarrativeMetrics] = {}
        self.quality_metrics: dict[int, QualityMetrics] = {}

        # 分析パターン定義
        self.emotion_patterns = {
            "positive": [
                "嬉しい", "楽しい", "幸せ", "満足", "安心", "感謝", "愛", "希望",
                "喜び", "笑", "微笑", "興奮", "感動", "温かい", "優しい"
            ],
            "negative": [
                "悲しい", "辛い", "苦しい", "痛い", "悔しい", "怖い", "不安", "絶望",
                "怒り", "憎しみ", "嫉妬", "孤独", "失望", "焦り", "恐怖"
            ],
            "neutral": [
                "普通", "平静", "冷静", "淡々", "客観的", "事実", "状況", "観察"
            ]
        }

        # キャラクター特徴パターン
        self.character_patterns = {
            "dialogue_markers": ["「", "」", "『", "』", '"', "'"],
            "action_markers": ["動く", "歩く", "走る", "見る", "聞く", "考える"],
            "emotion_markers": ["思う", "感じる", "気持ち", "心", "胸"]
        }

    @performance_monitor
    def analyze_episode_emotions(self, episode_number: int, content: str) -> dict[str, EmotionProfile]:
        """エピソードの感情分析"""
        # テキストを文に分割
        sentences = self._split_into_sentences(content)

        # キャラクター別に分析
        characters = self._extract_characters(content)
        emotion_profiles = {}

        for character in characters:
            profile = self._analyze_character_emotions(character, sentences, episode_number)
            emotion_profiles[character] = profile

        # 結果を保存
        self.emotion_profiles[episode_number] = emotion_profiles

        return emotion_profiles

    @performance_monitor
    def analyze_narrative_structure(self, episode_number: int, content: str) -> NarrativeMetrics:
        """物語構造分析"""
        # 基本統計
        word_count = len(content.replace(" ", "").replace("\n", ""))
        sentences = self._split_into_sentences(content)
        sentence_count = len(sentences)
        paragraph_count = len([p for p in content.split("\n\n") if p.strip()])

        # 文体比率分析
        dialogue_ratio = self._calculate_dialogue_ratio(content)
        description_ratio = self._calculate_description_ratio(content)
        action_ratio = 1.0 - dialogue_ratio - description_ratio

        # ペーシング分析
        pacing_score = self._analyze_pacing(sentences)

        # 読みやすさ分析
        readability_score = self._calculate_readability(content, sentences)

        # エンゲージメント分析
        engagement_score = self._predict_engagement(content, sentences)

        metrics = NarrativeMetrics(
            episode_number=episode_number,
            word_count=word_count,
            sentence_count=sentence_count,
            paragraph_count=paragraph_count,
            dialogue_ratio=dialogue_ratio,
            description_ratio=description_ratio,
            action_ratio=action_ratio,
            pacing_score=pacing_score,
            readability_score=readability_score,
            engagement_score=engagement_score
        )

        self.narrative_metrics[episode_number] = metrics
        return metrics

    @performance_monitor
    def analyze_quality_metrics(self, episode_number: int, content: str, metadata: dict | None = None) -> QualityMetrics:
        """品質メトリクス分析"""
        # プロット一貫性分析
        plot_consistency = self._analyze_plot_consistency(content, episode_number)

        # キャラクター成長分析
        character_development = self._analyze_character_development(content, episode_number)

        # 対話品質分析
        dialogue_quality = self._analyze_dialogue_quality(content)

        # 描写品質分析
        description_quality = self._analyze_description_quality(content)

        # 技術的正確性
        technical_accuracy = self._analyze_technical_accuracy(content)

        # 創造性評価
        creativity_score = self._evaluate_creativity(content)

        # 独創性評価
        originality_score = self._evaluate_originality(content, episode_number)

        # 総合品質スコア
        overall_quality = (
            plot_consistency * 0.2 +
            character_development * 0.2 +
            dialogue_quality * 0.15 +
            description_quality * 0.15 +
            technical_accuracy * 0.1 +
            creativity_score * 0.1 +
            originality_score * 0.1
        )

        metrics = QualityMetrics(
            episode_number=episode_number,
            overall_quality=overall_quality,
            plot_consistency=plot_consistency,
            character_development=character_development,
            dialogue_quality=dialogue_quality,
            description_quality=description_quality,
            technical_accuracy=technical_accuracy,
            creativity_score=creativity_score,
            originality_score=originality_score
        )

        self.quality_metrics[episode_number] = metrics
        return metrics

    @performance_monitor
    def generate_comprehensive_report(self, episode_numbers: list[int]) -> dict[str, Any]:
        """包括的分析レポート生成"""
        report = {
            "analysis_date": datetime.now().isoformat(),
            "episodes_analyzed": episode_numbers,
            "summary": {},
            "emotion_analysis": {},
            "narrative_analysis": {},
            "quality_analysis": {},
            "trends": {},
            "recommendations": []
        }

        # サマリー統計
        report["summary"] = self._generate_summary_statistics(episode_numbers)

        # 感情分析結果
        report["emotion_analysis"] = self._compile_emotion_analysis(episode_numbers)

        # 物語分析結果
        report["narrative_analysis"] = self._compile_narrative_analysis(episode_numbers)

        # 品質分析結果
        report["quality_analysis"] = self._compile_quality_analysis(episode_numbers)

        # トレンド分析
        report["trends"] = self._analyze_trends(episode_numbers)

        # 改善推奨事項
        report["recommendations"] = self._generate_recommendations(episode_numbers)

        return report

    def _split_into_sentences(self, content: str) -> list[str]:
        """文章を文に分割"""
        # 日本語の文区切り文字を使用
        sentences = re.split(r"[。！？\n]", content)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_characters(self, content: str) -> list[str]:
        """キャラクター名を抽出"""
        # 簡易的な実装：会話文から推測
        characters = set()

        # 「」内の話者を推定
        dialogue_pattern = r"「[^」]*」"
        re.findall(dialogue_pattern, content)

        # より高度な分析が必要だが、ここでは基本的な実装
        default_characters = ["主人公", "相手", "語り手"]
        characters.update(default_characters)

        return list(characters)

    def _analyze_character_emotions(self, character: str, sentences: list[str], episode_number: int) -> EmotionProfile:
        """キャラクター感情分析"""
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        emotion_sequence = []

        for sentence in sentences:
            # 感情語の検出
            pos_matches = sum(1 for word in self.emotion_patterns["positive"] if word in sentence)
            neg_matches = sum(1 for word in self.emotion_patterns["negative"] if word in sentence)
            neu_matches = sum(1 for word in self.emotion_patterns["neutral"] if word in sentence)

            positive_count += pos_matches
            negative_count += neg_matches
            neutral_count += neu_matches

            # 感情の推移を記録
            if pos_matches > 0:
                emotion_sequence.append("positive")
            elif neg_matches > 0:
                emotion_sequence.append("negative")
            else:
                emotion_sequence.append("neutral")

        total_emotions = positive_count + negative_count + neutral_count
        if total_emotions == 0:
            total_emotions = 1  # ゼロ除算回避

        # スコア正規化
        positive_score = positive_count / total_emotions
        negative_score = negative_count / total_emotions
        neutral_score = neutral_count / total_emotions

        # 変動幅計算
        volatility = self._calculate_emotion_volatility(emotion_sequence)

        # 複雑さ計算
        complexity = self._calculate_emotion_complexity(emotion_sequence)

        # 主要感情抽出
        dominant_emotions = self._extract_dominant_emotions(sentences)

        # 感情遷移分析
        emotion_transitions = self._analyze_emotion_transitions(emotion_sequence)

        return EmotionProfile(
            character_name=character,
            episode_number=episode_number,
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=neutral_score,
            volatility=volatility,
            complexity=complexity,
            dominant_emotions=dominant_emotions,
            emotion_transitions=emotion_transitions
        )

    def _calculate_dialogue_ratio(self, content: str) -> float:
        """対話比率の計算"""
        dialogue_chars = 0
        total_chars = len(content.replace(" ", "").replace("\n", ""))

        # 「」『』内の文字数をカウント
        dialogue_pattern = r"[「『][^」』]*[」』]"
        dialogues = re.findall(dialogue_pattern, content)
        dialogue_chars = sum(len(d) for d in dialogues)

        return dialogue_chars / max(total_chars, 1)

    def _calculate_description_ratio(self, content: str) -> float:
        """描写比率の計算"""
        # 描写を示すキーワードの出現頻度で推定
        description_words = [
            "見える", "聞こえる", "感じる", "匂い", "色", "形", "大きさ",
            "美しい", "醜い", "暖かい", "冷たい", "明るい", "暗い"
        ]

        description_count = sum(content.count(word) for word in description_words)
        sentences = self._split_into_sentences(content)

        return min(1.0, description_count / max(len(sentences), 1))

    def _analyze_pacing(self, sentences: list[str]) -> float:
        """ペーシング分析"""
        if not sentences:
            return 0.0

        # 文の長さの分散でペーシングを評価
        lengths = [len(s) for s in sentences]

        if len(lengths) < 2:
            return 0.5

        mean_length = sum(lengths) / len(lengths)
        variance = sum((l - mean_length) ** 2 for l in lengths) / len(lengths)

        # 分散が適度な場合（リズムがある）を高評価
        optimal_variance = mean_length * 0.3  # 経験的な値
        return 1.0 - min(1.0, abs(variance - optimal_variance) / optimal_variance)


    def _calculate_readability(self, content: str, sentences: list[str]) -> float:
        """読みやすさ分析"""
        if not sentences:
            return 0.0

        # 平均文長
        avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)

        # 理想的な文長を50文字として評価
        ideal_length = 50
        length_score = 1.0 - min(1.0, abs(avg_sentence_length - ideal_length) / ideal_length)

        # 難解語の使用頻度
        difficult_words = ["従って", "故に", "即ち", "尚且つ", "然しながら"]
        difficult_count = sum(content.count(word) for word in difficult_words)
        difficulty_penalty = min(0.5, difficult_count / max(len(sentences), 1))

        readability = length_score - difficulty_penalty
        return max(0.0, min(1.0, readability))

    def _predict_engagement(self, content: str, sentences: list[str]) -> float:
        """エンゲージメント予測"""
        engagement_factors = {
            "dialogue_presence": self._calculate_dialogue_ratio(content) * 0.3,
            "action_words": self._count_action_words(content) / max(len(sentences), 1) * 0.2,
            "emotion_intensity": self._calculate_emotion_intensity(content) * 0.3,
            "conflict_indicators": self._detect_conflict_indicators(content) * 0.2
        }

        engagement_score = sum(engagement_factors.values())
        return min(1.0, engagement_score)

    def _count_action_words(self, content: str) -> int:
        """アクション語の数"""
        action_words = [
            "走る", "歩く", "跳ぶ", "飛ぶ", "動く", "戦う", "叫ぶ", "泣く",
            "笑う", "投げる", "取る", "握る", "抱く", "押す", "引く"
        ]
        return sum(content.count(word) for word in action_words)

    def _calculate_emotion_intensity(self, content: str) -> float:
        """感情強度の計算"""
        intense_emotions = ["激怒", "絶望", "歓喜", "恐怖", "愛", "憎しみ"]
        intense_count = sum(content.count(emotion) for emotion in intense_emotions)

        sentences = self._split_into_sentences(content)
        return intense_count / max(len(sentences), 1)

    def _detect_conflict_indicators(self, content: str) -> float:
        """対立・葛藤の検出"""
        conflict_words = ["しかし", "だが", "けれども", "対立", "争い", "戦い", "問題", "困難"]
        conflict_count = sum(content.count(word) for word in conflict_words)

        sentences = self._split_into_sentences(content)
        return min(1.0, conflict_count / max(len(sentences), 1))

    def _analyze_plot_consistency(self, content: str, episode_number: int) -> float:
        """プロット一貫性分析"""
        # 基本的な一貫性チェック（より高度な実装が理想）
        consistency_score = 0.8  # デフォルト値

        # 前のエピソードとの整合性チェック（簡易版）
        if episode_number > 1 and (episode_number - 1) in self.quality_metrics:
            prev_metrics = self.quality_metrics[episode_number - 1]
            # 品質の急激な変化をペナルティとして評価
            if abs(prev_metrics.overall_quality - 0.8) > 0.3:
                consistency_score -= 0.2

        return max(0.0, min(1.0, consistency_score))

    def _analyze_character_development(self, content: str, episode_number: int) -> float:
        """キャラクター成長分析"""
        # キャラクター成長を示すキーワード
        growth_indicators = [
            "気づく", "学ぶ", "成長", "変わる", "理解する", "発見する",
            "決意", "決める", "選ぶ", "克服", "挑戦", "向き合う"
        ]

        growth_count = sum(content.count(indicator) for indicator in growth_indicators)
        sentences = self._split_into_sentences(content)

        return min(1.0, growth_count / max(len(sentences) * 0.1, 1))

    def _analyze_dialogue_quality(self, content: str) -> float:
        """対話品質分析"""
        dialogues = re.findall(r"[「『][^」』]*[」』]", content)

        if not dialogues:
            return 0.5  # 対話なしの場合は中間値

        # 対話の多様性（長さのばらつき）
        lengths = [len(d) for d in dialogues]
        avg_length = sum(lengths) / len(lengths)
        variety_score = 1.0 - min(1.0, (max(lengths) - min(lengths)) / max(avg_length, 1))

        # 自然さの評価（基本的な実装）
        natural_score = 0.8  # デフォルト値

        return (variety_score + natural_score) / 2

    def _analyze_description_quality(self, content: str) -> float:
        """描写品質分析"""
        descriptive_adjectives = [
            "美しい", "醜い", "大きい", "小さい", "高い", "低い", "明るい", "暗い",
            "暖かい", "冷たい", "柔らかい", "硬い", "静かな", "騒がしい"
        ]

        adjective_count = sum(content.count(adj) for adj in descriptive_adjectives)
        sentences = self._split_into_sentences(content)

        # 適度な描写語使用を評価
        optimal_ratio = 0.1  # 文あたりの理想的な描写語比率
        actual_ratio = adjective_count / max(len(sentences), 1)

        return 1.0 - min(1.0, abs(actual_ratio - optimal_ratio) / optimal_ratio)

    def _analyze_technical_accuracy(self, content: str) -> float:
        """技術的正確性分析"""
        # 文法的な問題の検出（基本的な実装）
        technical_score = 0.9  # デフォルト値

        # 明らかな文法エラーパターン
        error_patterns = [
            r"。。+",  # 句点の重複
            r"！！+",  # 感嘆符の過度な重複
            r"？？+",  # 疑問符の過度な重複
        ]

        error_count = 0
        for pattern in error_patterns:
            error_count += len(re.findall(pattern, content))

        sentences = self._split_into_sentences(content)
        error_penalty = min(0.3, error_count / max(len(sentences), 1))

        return max(0.0, technical_score - error_penalty)

    def _evaluate_creativity(self, content: str) -> float:
        """創造性評価"""
        creativity_indicators = [
            "想像", "創造", "発明", "新しい", "独特", "独自", "オリジナル",
            "ユニーク", "面白い", "珍しい", "驚く", "意外"
        ]

        creativity_count = sum(content.count(indicator) for indicator in creativity_indicators)
        sentences = self._split_into_sentences(content)

        return min(1.0, creativity_count / max(len(sentences) * 0.05, 1))

    def _evaluate_originality(self, content: str, episode_number: int) -> float:
        """独創性評価"""
        # 他のエピソードとの類似性チェック（簡易版）

        # 使用語彙の多様性
        words = content.split()
        unique_words = len(set(words))
        vocabulary_diversity = unique_words / max(len(words), 1)

        # 語彙多様性を独創性の指標として使用
        return min(1.0, vocabulary_diversity * 2)


    def _calculate_emotion_volatility(self, emotion_sequence: list[str]) -> float:
        """感情変動幅の計算"""
        if len(emotion_sequence) < 2:
            return 0.0

        changes = 0
        for i in range(1, len(emotion_sequence)):
            if emotion_sequence[i] != emotion_sequence[i-1]:
                changes += 1

        return changes / (len(emotion_sequence) - 1)

    def _calculate_emotion_complexity(self, emotion_sequence: list[str]) -> float:
        """感情複雑さの計算"""
        if not emotion_sequence:
            return 0.0

        emotion_types = len(set(emotion_sequence))
        max_types = 3  # positive, negative, neutral

        return emotion_types / max_types

    def _extract_dominant_emotions(self, sentences: list[str]) -> list[str]:
        """主要感情の抽出"""
        emotion_counts = Counter()

        for sentence in sentences:
            for emotion_type, words in self.emotion_patterns.items():
                for word in words:
                    if word in sentence:
                        emotion_counts[emotion_type] += 1

        # 上位3つの感情を返す
        return [emotion for emotion, _ in emotion_counts.most_common(3)]

    def _analyze_emotion_transitions(self, emotion_sequence: list[str]) -> list[tuple[str, str, float]]:
        """感情遷移分析"""
        transitions = []
        transition_counts = defaultdict(int)

        for i in range(1, len(emotion_sequence)):
            transition = (emotion_sequence[i-1], emotion_sequence[i])
            transition_counts[transition] += 1

        total_transitions = len(emotion_sequence) - 1
        for (from_emotion, to_emotion), count in transition_counts.items():
            strength = count / max(total_transitions, 1)
            transitions.append((from_emotion, to_emotion, strength))

        return transitions

    def _generate_summary_statistics(self, episode_numbers: list[int]) -> dict[str, Any]:
        """サマリー統計生成"""
        total_episodes = len(episode_numbers)

        # 基本統計
        avg_quality = 0.0
        avg_word_count = 0.0
        avg_engagement = 0.0

        for ep_num in episode_numbers:
            if ep_num in self.quality_metrics:
                avg_quality += self.quality_metrics[ep_num].overall_quality
            if ep_num in self.narrative_metrics:
                avg_word_count += self.narrative_metrics[ep_num].word_count
                avg_engagement += self.narrative_metrics[ep_num].engagement_score

        if total_episodes > 0:
            avg_quality /= total_episodes
            avg_word_count /= total_episodes
            avg_engagement /= total_episodes

        return {
            "total_episodes": total_episodes,
            "average_quality_score": round(avg_quality, 2),
            "average_word_count": int(avg_word_count),
            "average_engagement_score": round(avg_engagement, 2),
            "analysis_completion_rate": len([ep for ep in episode_numbers if ep in self.quality_metrics]) / max(total_episodes, 1)
        }

    def _compile_emotion_analysis(self, episode_numbers: list[int]) -> dict[str, Any]:
        """感情分析結果コンパイル"""
        emotion_summary = {
            "overall_emotional_tone": "neutral",
            "emotion_volatility_trend": [],
            "character_emotional_profiles": {},
            "dominant_emotion_patterns": []
        }

        all_volatilities = []
        all_emotions = []

        for ep_num in episode_numbers:
            if ep_num in self.emotion_profiles:
                for profile in self.emotion_profiles[ep_num].values():
                    all_volatilities.append(profile.volatility)
                    all_emotions.extend(profile.dominant_emotions)

        if all_volatilities:
            emotion_summary["emotion_volatility_trend"] = all_volatilities

        if all_emotions:
            emotion_counter = Counter(all_emotions)
            emotion_summary["dominant_emotion_patterns"] = emotion_counter.most_common(5)

        return emotion_summary

    def _compile_narrative_analysis(self, episode_numbers: list[int]) -> dict[str, Any]:
        """物語分析結果コンパイル"""
        narrative_summary = {
            "pacing_analysis": [],
            "style_consistency": 0.0,
            "dialogue_description_balance": {},
            "readability_trend": []
        }

        pacing_scores = []
        readability_scores = []
        dialogue_ratios = []
        description_ratios = []

        for ep_num in episode_numbers:
            if ep_num in self.narrative_metrics:
                metrics = self.narrative_metrics[ep_num]
                pacing_scores.append(metrics.pacing_score)
                readability_scores.append(metrics.readability_score)
                dialogue_ratios.append(metrics.dialogue_ratio)
                description_ratios.append(metrics.description_ratio)

        if pacing_scores:
            narrative_summary["pacing_analysis"] = pacing_scores
            narrative_summary["readability_trend"] = readability_scores

            # 一貫性の計算（分散の逆数）
            if len(pacing_scores) > 1:
                pacing_variance = np.var(pacing_scores)
                narrative_summary["style_consistency"] = 1.0 / (1.0 + pacing_variance)

            # バランス分析
            narrative_summary["dialogue_description_balance"] = {
                "average_dialogue_ratio": np.mean(dialogue_ratios),
                "average_description_ratio": np.mean(description_ratios),
                "balance_consistency": 1.0 - np.std(dialogue_ratios) if dialogue_ratios else 0.0
            }

        return narrative_summary

    def _compile_quality_analysis(self, episode_numbers: list[int]) -> dict[str, Any]:
        """品質分析結果コンパイル"""
        quality_summary = {
            "overall_quality_trend": [],
            "quality_categories": {},
            "improvement_areas": [],
            "strength_areas": []
        }

        quality_trends = []
        category_scores = defaultdict(list)

        for ep_num in episode_numbers:
            if ep_num in self.quality_metrics:
                metrics = self.quality_metrics[ep_num]
                quality_trends.append(metrics.overall_quality)

                category_scores["plot_consistency"].append(metrics.plot_consistency)
                category_scores["character_development"].append(metrics.character_development)
                category_scores["dialogue_quality"].append(metrics.dialogue_quality)
                category_scores["description_quality"].append(metrics.description_quality)
                category_scores["technical_accuracy"].append(metrics.technical_accuracy)
                category_scores["creativity_score"].append(metrics.creativity_score)

        if quality_trends:
            quality_summary["overall_quality_trend"] = quality_trends

            # カテゴリ別平均スコア
            for category, scores in category_scores.items():
                quality_summary["quality_categories"][category] = {
                    "average": np.mean(scores),
                    "trend": scores
                }

            # 改善・強化エリアの特定
            avg_scores = {cat: np.mean(scores) for cat, scores in category_scores.items()}
            sorted_categories = sorted(avg_scores.items(), key=lambda x: x[1])

            quality_summary["improvement_areas"] = [cat for cat, score in sorted_categories[:2]]
            quality_summary["strength_areas"] = [cat for cat, score in sorted_categories[-2:]]

        return quality_summary

    def _analyze_trends(self, episode_numbers: list[int]) -> dict[str, Any]:
        """トレンド分析"""
        trends = {
            "quality_improvement_rate": 0.0,
            "engagement_trend": "stable",
            "consistency_score": 0.0,
            "predicted_next_quality": 0.0
        }

        if len(episode_numbers) < 2:
            return trends

        # 品質改善率の計算
        quality_scores = []
        for ep_num in sorted(episode_numbers):
            if ep_num in self.quality_metrics:
                quality_scores.append(self.quality_metrics[ep_num].overall_quality)

        if len(quality_scores) >= 2:
            # 線形回帰による改善率計算
            x = np.arange(len(quality_scores))
            slope = np.polyfit(x, quality_scores, 1)[0]
            trends["quality_improvement_rate"] = slope

            # 次回品質予測
            trends["predicted_next_quality"] = quality_scores[-1] + slope

            # 一貫性スコア
            trends["consistency_score"] = 1.0 - np.std(quality_scores)

        return trends

    def _generate_recommendations(self, episode_numbers: list[int]) -> list[str]:
        """改善推奨事項生成"""
        recommendations = []

        if not episode_numbers:
            return recommendations

        # 品質分析に基づく推奨
        latest_ep = max(episode_numbers)
        if latest_ep in self.quality_metrics:
            metrics = self.quality_metrics[latest_ep]

            if metrics.dialogue_quality < 0.6:
                recommendations.append("対話の自然さと多様性の向上を検討してください")

            if metrics.character_development < 0.5:
                recommendations.append("キャラクターの成長要素を強化することをお勧めします")

            if metrics.creativity_score < 0.5:
                recommendations.append("より創造的な表現や展開を取り入れてみてください")

        # 物語構造に基づく推奨
        if latest_ep in self.narrative_metrics:
            metrics = self.narrative_metrics[latest_ep]

            if metrics.engagement_score < 0.6:
                recommendations.append("読者の関心を引く要素（アクション、対立等）の増加を検討してください")

            if metrics.readability_score < 0.6:
                recommendations.append("文章の長さや構造を調整して読みやすさを向上させてください")

        # 感情分析に基づく推奨
        if latest_ep in self.emotion_profiles:
            avg_volatility = np.mean([profile.volatility for profile in self.emotion_profiles[latest_ep].values()])

            if avg_volatility < 0.3:
                recommendations.append("感情の起伏をより豊かに表現することで物語に深みを加えてください")

        return recommendations if recommendations else ["現在の執筆品質は良好です。この調子で続けてください。"]

    @performance_monitor
    def export_analytics_dashboard(self, episode_numbers: list[int], format: str = "json") -> str:
        """分析ダッシュボードのエクスポート"""
        dashboard_data = {
            "dashboard_type": "writing_analytics",
            "generated_at": datetime.now().isoformat(),
            "episodes": episode_numbers,
            "summary": self._generate_summary_statistics(episode_numbers),
            "detailed_analysis": self.generate_comprehensive_report(episode_numbers),
            "visualization_data": {
                "quality_timeline": [],
                "emotion_heatmap": {},
                "narrative_balance": {},
                "improvement_suggestions": []
            }
        }

        # 可視化用データの準備
        for ep_num in sorted(episode_numbers):
            if ep_num in self.quality_metrics:
                dashboard_data["visualization_data"]["quality_timeline"].append({
                    "episode": ep_num,
                    "quality": self.quality_metrics[ep_num].overall_quality,
                    "components": {
                        "plot": self.quality_metrics[ep_num].plot_consistency,
                        "character": self.quality_metrics[ep_num].character_development,
                        "dialogue": self.quality_metrics[ep_num].dialogue_quality,
                        "description": self.quality_metrics[ep_num].description_quality,
                        "creativity": self.quality_metrics[ep_num].creativity_score
                    }
                })

        if format == "json":
            return json.dumps(dashboard_data, indent=2, ensure_ascii=False, default=str)

        return str(dashboard_data)
