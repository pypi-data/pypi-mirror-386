"""比喩多様性評価ツール

感情表現における比喩の多様性と独創性を評価し、
創造的で印象的な感情描写を支援する。
"""

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from .base_emotion_tool import BaseEmotionTool, EmotionToolInput, EmotionToolOutput


@dataclass
class MetaphorElement:
    """比喩要素データ構造"""
    metaphor_text: str
    metaphor_type: str  # simile, metaphor, personification, synesthesia
    source_domain: str  # 比喩の起源領域
    target_domain: str  # 比喩の対象領域
    creativity_score: float
    position: tuple


class MetaphorDiversityScorerTool(BaseEmotionTool):
    """比喩多様性評価ツール

    感情表現に使用される比喩の種類、独創性、多様性を評価し、
    より豊かで印象的な感情描写のための提案を行う。
    """

    def __init__(self) -> None:
        super().__init__("metaphor_diversity_scorer")
        self._initialize_metaphor_database()

    def _initialize_tool(self) -> None:
        """ツール初期化"""
        self.logger.info("比喩データベースと評価基準初期化")

    def _initialize_metaphor_database(self) -> None:
        """比喩データベースの初期化"""
        # 比喩パターン検出
        self.metaphor_patterns = {
            "simile": [  # 直喩
                r"(.+?)(?:のような|のように|みたいな|みたいに)(.+)",
                r"(.+?)(?:まるで|あたかも)(.+?)(?:のよう|かのよう)",
                r"(.+?)(?:さながら)(.+)"
            ],
            "metaphor": [  # 隠喩
                r"(.+?)(?:は|が)(.+?)(?:だ|である|です)",
                r"(.+?)(?:という)(.+?)(?:の中で|に包まれて)",
                r"(.+?)(?:と化す|となる|に変わる)"
            ],
            "personification": [  # 擬人法
                r"(風|雨|雲|太陽|月|星)(?:が|は)(.+?)(?:語りかける|笑う|泣く|歌う|踊る)",
                r"(心|胸|魂)(?:が|は)(.+?)(?:叫ぶ|歌う|踊る|泣く|笑う)",
                r"(時間|運命|愛)(?:が|は)(.+?)(?:運ぶ|導く|支配する)"
            ],
            "synesthesia": [  # 共感覚
                r"(.+?)(?:な|の)(音|声|響き)(?:が)(.+?)(?:見える|匂う|味がする)",
                r"(.+?)(?:な|の)(色|光)(?:が)(.+?)(?:聞こえる|響く|歌う)",
                r"(.+?)(?:な|の)(香り|匂い)(?:が)(.+?)(?:見える|光る|響く)"
            ]
        }

        # 起源領域分類（比喩のソース）
        self.source_domains = {
            "nature": ["風", "雨", "雲", "太陽", "月", "星", "海", "山", "川", "花", "樹"],
            "animal": ["鳥", "魚", "猫", "犬", "蝶", "獅子", "鷹", "兎"],
            "weather": ["嵐", "雷", "雪", "霧", "虹", "雨", "晴れ", "曇り"],
            "music": ["音楽", "歌", "リズム", "ハーモニー", "メロディ", "響き"],
            "color": ["赤", "青", "白", "黒", "金", "銀", "虹色", "透明"],
            "texture": ["滑らか", "粗い", "柔らか", "硬い", "冷たい", "熱い"],
            "space": ["宇宙", "星空", "地平線", "天", "地", "無限"],
            "time": ["永遠", "瞬間", "昔", "未来", "今", "時"],
            "architecture": ["城", "橋", "塔", "扉", "窓", "壁"],
            "mythology": ["神", "天使", "悪魔", "精霊", "妖精", "英雄"]
        }

        # 対象領域（感情表現の対象）
        self.target_domains = {
            "emotion": ["愛", "悲しみ", "喜び", "怒り", "恐れ", "希望", "絶望"],
            "mental": ["心", "魂", "思考", "記憶", "夢", "意識"],
            "physical": ["体", "手", "目", "声", "息", "鼓動"],
            "relationship": ["絆", "距離", "関係", "結び", "別れ", "出会い"],
            "time_experience": ["瞬間", "永遠", "過去", "現在", "未来", "時間"],
            "abstract": ["運命", "真実", "秘密", "答え", "問い", "意味"]
        }

        # 一般的な比喩（創造性が低い）
        self.common_metaphors = {
            "心が躍る", "胸が熱い", "血が騒ぐ", "魂が震える",
            "雲の上", "地の底", "天にも昇る", "地に足がつかない",
            "火がつく", "氷のよう", "石のよう", "羽のように"
        }

        # 独創的比喩の評価基準
        self.creativity_factors = {
            "domain_distance": 2.0,      # 起源と対象の領域の距離
            "sensory_mixing": 1.5,       # 感覚の混合（共感覚）
            "conceptual_blend": 1.3,     # 概念の組み合わせ
            "cultural_novelty": 1.2,     # 文化的新奇性
            "linguistic_innovation": 1.8  # 言語的革新性
        }

    async def execute(self, input_data: EmotionToolInput) -> EmotionToolOutput:
        """比喩多様性評価の実行

        Args:
            input_data: 分析対象テキストと設定

        Returns:
            多様性評価結果と改善提案
        """
        text = input_data.text
        comparison_corpus = input_data.metadata.get("comparison_corpus") if input_data.metadata else None
        creativity_threshold = input_data.metadata.get("creativity_threshold", 0.6) if input_data.metadata else 0.6

        # 比喩抽出
        extracted_metaphors = self._extract_metaphors(text)

        # 多様性評価
        diversity_analysis = self._analyze_diversity(extracted_metaphors)

        # 独創性評価
        uniqueness_analysis = self._analyze_uniqueness(extracted_metaphors, comparison_corpus)

        # 過用比喩検出
        overused_analysis = self._detect_overused_metaphors(extracted_metaphors)

        # 新規表現候補生成
        novel_suggestions = self._generate_novel_expressions(
            extracted_metaphors, creativity_threshold
        )

        analysis = {
            "metaphor_count": len(extracted_metaphors),
            "metaphor_types": self._count_metaphor_types(extracted_metaphors),
            "source_domain_distribution": diversity_analysis["source_domains"],
            "target_domain_distribution": diversity_analysis["target_domains"],
            "diversity_score": diversity_analysis["score"],
            "uniqueness_ratio": uniqueness_analysis["ratio"],
            "creativity_average": uniqueness_analysis["average_creativity"],
            "overused_metaphors": overused_analysis,
            "metaphor_density": len(extracted_metaphors) / max(len(text), 1) * 1000  # per 1000 chars
        }

        # 総合スコア計算
        score = min(100,
            diversity_analysis["score"] * 0.4 +
            uniqueness_analysis["ratio"] * 100 * 0.3 +
            uniqueness_analysis["average_creativity"] * 100 * 0.3
        )

        suggestions = self._generate_improvement_suggestions(
            diversity_analysis, uniqueness_analysis, overused_analysis
        )

        return self.create_success_output(
            score=score,
            analysis=analysis,
            suggestions=suggestions + novel_suggestions,
            metadata={
                "metaphors_found": len(extracted_metaphors),
                "novel_expressions_generated": len(novel_suggestions),
                "creativity_threshold": creativity_threshold
            }
        )

    def _extract_metaphors(self, text: str) -> list[MetaphorElement]:
        """テキストから比喩を抽出

        Args:
            text: 分析対象テキスト

        Returns:
            抽出された比喩要素のリスト
        """
        metaphors = []

        for metaphor_type, patterns in self.metaphor_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    source_domain = self._classify_source_domain(match.group())
                    target_domain = self._classify_target_domain(match.group())
                    creativity = self._calculate_creativity_score(
                        match.group(), source_domain, target_domain, metaphor_type
                    )

                    metaphors.append(MetaphorElement(
                        metaphor_text=match.group(),
                        metaphor_type=metaphor_type,
                        source_domain=source_domain,
                        target_domain=target_domain,
                        creativity_score=creativity,
                        position=match.span()
                    ))

        return metaphors

    def _classify_source_domain(self, metaphor_text: str) -> str:
        """比喩の起源領域を分類

        Args:
            metaphor_text: 比喩テキスト

        Returns:
            起源領域名
        """
        for domain, keywords in self.source_domains.items():
            for keyword in keywords:
                if keyword in metaphor_text:
                    return domain
        return "unknown"

    def _classify_target_domain(self, metaphor_text: str) -> str:
        """比喩の対象領域を分類

        Args:
            metaphor_text: 比喩テキスト

        Returns:
            対象領域名
        """
        for domain, keywords in self.target_domains.items():
            for keyword in keywords:
                if keyword in metaphor_text:
                    return domain
        return "unknown"

    def _calculate_creativity_score(self, metaphor_text: str, source_domain: str,
                                  target_domain: str, metaphor_type: str) -> float:
        """比喩の創造性スコア計算

        Args:
            metaphor_text: 比喩テキスト
            source_domain: 起源領域
            target_domain: 対象領域
            metaphor_type: 比喩タイプ

        Returns:
            創造性スコア（0-1）
        """
        base_score = 0.5

        # 一般的比喩の減点
        if any(common in metaphor_text for common in self.common_metaphors):
            base_score *= 0.3

        # 領域間距離による加点
        domain_combinations = {
            ("nature", "emotion"): 0.6,
            ("animal", "mental"): 0.7,
            ("weather", "relationship"): 0.8,
            ("music", "physical"): 0.9,
            ("mythology", "abstract"): 1.0
        }

        domain_pair = (source_domain, target_domain)
        if domain_pair in domain_combinations:
            base_score += domain_combinations[domain_pair] * self.creativity_factors["domain_distance"] * 0.1

        # 比喩タイプによる調整
        type_bonuses = {
            "synesthesia": 0.3,      # 共感覚は高創造性
            "personification": 0.2,  # 擬人法は中創造性
            "metaphor": 0.1,         # 隠喩は低創造性
            "simile": 0.05          # 直喩は最低創造性
        }

        if metaphor_type in type_bonuses:
            base_score += type_bonuses[metaphor_type]

        return min(1.0, base_score)

    def _analyze_diversity(self, metaphors: list[MetaphorElement]) -> dict[str, Any]:
        """比喻多様性の分析

        Args:
            metaphors: 比喩要素リスト

        Returns:
            多様性分析結果
        """
        if not metaphors:
            return {"score": 0, "source_domains": {}, "target_domains": {}}

        # 起源領域の分布
        source_counter = Counter(m.source_domain for m in metaphors)
        target_counter = Counter(m.target_domain for m in metaphors)

        # シャノンエントロピーによる多様性計算
        def calculate_entropy(counter):
            total = sum(counter.values())
            if total == 0:
                return 0
            return -sum((count/total) * math.log2(count/total) for count in counter.values())

        source_entropy = calculate_entropy(source_counter)
        target_entropy = calculate_entropy(target_counter)

        # 最大エントロピーで正規化（0-100スコア）
        max_source_entropy = math.log2(len(self.source_domains))
        max_target_entropy = math.log2(len(self.target_domains))

        diversity_score = (
            (source_entropy / max_source_entropy) * 50 +
            (target_entropy / max_target_entropy) * 50
        )

        return {
            "score": diversity_score,
            "source_domains": dict(source_counter),
            "target_domains": dict(target_counter),
            "source_entropy": source_entropy,
            "target_entropy": target_entropy
        }

    def _analyze_uniqueness(self, metaphors: list[MetaphorElement],
                          comparison_corpus: str | None) -> dict[str, Any]:
        """独創性分析

        Args:
            metaphors: 比喩要素リスト
            comparison_corpus: 比較対象コーパス

        Returns:
            独創性分析結果
        """
        if not metaphors:
            return {"ratio": 0, "average_creativity": 0}

        unique_metaphors = 0
        total_creativity = 0

        for metaphor in metaphors:
            total_creativity += metaphor.creativity_score

            # コーパスとの比較（実装時にはより詳細な比較を行う）
            if comparison_corpus:
                if metaphor.metaphor_text not in comparison_corpus:
                    unique_metaphors += 1
            # コーパスがない場合は創造性スコアで判定
            elif metaphor.creativity_score > 0.6:
                unique_metaphors += 1

        return {
            "ratio": unique_metaphors / len(metaphors),
            "average_creativity": total_creativity / len(metaphors),
            "unique_count": unique_metaphors
        }

    def _detect_overused_metaphors(self, metaphors: list[MetaphorElement]) -> list[str]:
        """過用比喻の検出

        Args:
            metaphors: 比喩要素リスト

        Returns:
            過用比喻のリスト
        """
        metaphor_counts = Counter(m.metaphor_text for m in metaphors)
        overused = []

        for metaphor, count in metaphor_counts.items():
            if count > 2:  # 3回以上使用で過用とみなす
                overused.append(f"「{metaphor}」- {count}回使用")
            elif metaphor in self.common_metaphors:
                overused.append(f"「{metaphor}」- 一般的な表現")

        return overused

    def _generate_novel_expressions(self, existing_metaphors: list[MetaphorElement],
                                  creativity_threshold: float) -> list[str]:
        """新規表現候補の生成

        Args:
            existing_metaphors: 既存比喩
            creativity_threshold: 創造性閾値

        Returns:
            新規表現提案リスト
        """
        suggestions = []

        # 使用されていない起源・対象領域の組み合わせを探す
        used_combinations = {
            (m.source_domain, m.target_domain) for m in existing_metaphors
        }

        novel_combinations = [
            ("music", "physical"),   # 音楽×身体
            ("weather", "mental"),   # 天候×精神
            ("architecture", "emotion"), # 建築×感情
            ("mythology", "time_experience")  # 神話×時間体験
        ]

        for source, target in novel_combinations:
            if (source, target) not in used_combinations:
                suggestions.append(f"{source}領域と{target}領域の比喩表現を試してください")

        # 感覚混合（共感覚）の提案
        if not any(m.metaphor_type == "synesthesia" for m in existing_metaphors):
            suggestions.append("色を音で表現するような共感覚的比喩を追加してください")

        return suggestions[:3]  # 最大3個の提案

    def _count_metaphor_types(self, metaphors: list[MetaphorElement]) -> dict[str, int]:
        """比喩タイプ別カウント

        Args:
            metaphors: 比喩要素リスト

        Returns:
            タイプ別カウント
        """
        return dict(Counter(m.metaphor_type for m in metaphors))

    def _generate_improvement_suggestions(self, diversity_analysis: dict, uniqueness_analysis: dict,
                                        overused_analysis: list[str]) -> list[str]:
        """改善提案の生成

        Args:
            diversity_analysis: 多様性分析結果
            uniqueness_analysis: 独創性分析結果
            overused_analysis: 過用分析結果

        Returns:
            改善提案リスト
        """
        suggestions = []

        # 多様性に基づく提案
        if diversity_analysis["score"] < 30:
            suggestions.append("比喻の起源領域を多様化してください（自然、動物、音楽、神話など）")

        # 独創性に基づく提案
        if uniqueness_analysis["average_creativity"] < 0.4:
            suggestions.append("より独創的な比喻表現を取り入れてください")

        # 過用に基づく提案
        if overused_analysis:
            suggestions.append("繰り返し使用される表現を別の比喻に変更してください")

        return suggestions
