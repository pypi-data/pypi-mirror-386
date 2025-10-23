"""表現レベル適性ツール

感情表現が対象読者層・作品ジャンル・文体レベルに
適切かを検証し、一貫性のある文体を支援する。
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .base_emotion_tool import BaseEmotionTool, EmotionToolInput, EmotionToolOutput


class TargetAudience(Enum):
    """対象読者層"""
    TEEN = "teen"          # 10代
    YOUNG_ADULT = "young_adult"  # 20-30代
    ADULT = "adult"        # 成人一般
    SENIOR = "senior"      # シニア
    GENERAL = "general"    # 全年齢


class Genre(Enum):
    """作品ジャンル"""
    ROMANCE = "romance"         # 恋愛
    MYSTERY = "mystery"         # ミステリー
    FANTASY = "fantasy"         # ファンタジー
    SCIFI = "scifi"            # SF
    HORROR = "horror"          # ホラー
    SLICE_OF_LIFE = "slice_of_life"  # 日常系
    HISTORICAL = "historical"   # 時代物
    BUSINESS = "business"      # ビジネス


class FormalityLevel(Enum):
    """文体レベル"""
    CASUAL = "casual"         # カジュアル
    INFORMAL = "informal"     # 非公式
    NEUTRAL = "neutral"       # 中立
    FORMAL = "formal"         # 公式
    LITERARY = "literary"     # 文学的


@dataclass
class RegisterElement:
    """文体要素データ"""
    element_type: str    # vocabulary, grammar, tone, politeness
    content: str
    register_level: str
    appropriateness_score: float
    position: tuple


class RegisterVerifierTool(BaseEmotionTool):
    """表現レベル適性ツール

    感情表現の文体レベルが作品の対象読者層、ジャンル、
    全体の文体設定と適合しているかを検証する。
    """

    def __init__(self) -> None:
        super().__init__("register_verifier")
        self._initialize_register_standards()

    def _initialize_tool(self) -> None:
        """ツール初期化"""
        self.logger.info("文体レベル基準データベース初期化")

    def _initialize_register_standards(self) -> None:
        """文体レベル基準の初期化"""
        # 読者層別の適切な表現レベル
        self.audience_standards = {
            TargetAudience.TEEN: {
                "vocabulary_level": (1, 3),      # 1-5スケール（1:簡単、5:高級）
                "sentence_complexity": (1, 3),   # 文の複雑さ
                "emotional_intensity": (1, 4),   # 感情表現の強度
                "cultural_reference": (1, 2),    # 文化的参照の高度さ
                "preferred_formality": FormalityLevel.CASUAL
            },
            TargetAudience.YOUNG_ADULT: {
                "vocabulary_level": (2, 4),
                "sentence_complexity": (2, 4),
                "emotional_intensity": (2, 5),
                "cultural_reference": (2, 4),
                "preferred_formality": FormalityLevel.INFORMAL
            },
            TargetAudience.ADULT: {
                "vocabulary_level": (3, 5),
                "sentence_complexity": (3, 5),
                "emotional_intensity": (2, 5),
                "cultural_reference": (3, 5),
                "preferred_formality": FormalityLevel.NEUTRAL
            }
        }

        # ジャンル別の文体特徴
        self.genre_standards = {
            Genre.ROMANCE: {
                "emotional_vocabulary": "rich",     # 豊富な感情語彙
                "metaphor_density": "high",         # 比喻密度
                "intimacy_level": "personal",       # 親密度
                "descriptive_detail": "high",       # 描写詳細度
                "preferred_tone": "warm"
            },
            Genre.MYSTERY: {
                "emotional_vocabulary": "restrained",  # 抑制された感情語彙
                "metaphor_density": "medium",
                "intimacy_level": "distant",
                "descriptive_detail": "precise",
                "preferred_tone": "tense"
            },
            Genre.FANTASY: {
                "emotional_vocabulary": "dramatic",
                "metaphor_density": "very_high",
                "intimacy_level": "epic",
                "descriptive_detail": "elaborate",
                "preferred_tone": "grand"
            },
            Genre.SLICE_OF_LIFE: {
                "emotional_vocabulary": "natural",
                "metaphor_density": "low",
                "intimacy_level": "everyday",
                "descriptive_detail": "simple",
                "preferred_tone": "gentle"
            }
        }

        # 語彙レベル判定パターン
        self.vocabulary_patterns = {
            1: [  # 基本語彙
                r"うれしい|かなしい|おこる|こわい|びっくり",
                r"いい|わるい|おおきい|ちいさい",
                r"すき|きらい|たいへん"
            ],
            2: [  # 日常語彙
                r"喜び|悲しみ|怒り|恐怖|驚き",
                r"感動|興奮|不安|期待",
                r"楽しい|つらい|苦しい"
            ],
            3: [  # 一般語彙
                r"歓喜|憂鬱|憤怒|戦慄|愕然",
                r"陶酔|混乱|焦燥|懊悩",
                r"切ない|愛おしい|忌々しい"
            ],
            4: [  # 高級語彙
                r"慚愧|懺悔|慙惶|慟哭|嗚咽",
                r"恍惚|陶然|茫然|唖然",
                r"憤懣|忸怩|慟哭|慨嘆"
            ],
            5: [  # 専門・文学語彙
                r"悄然|愀然|惘然|茫然|怛然",
                r"憮然|慄然|愴然|凄然",
                r"恟々|戦々|兢々|惴々"
            ]
        }

        # 敬語・丁寧語パターン
        self.politeness_patterns = {
            "very_casual": [r"だぜ|だぞ|じゃん|っしょ|やべー"],
            "casual": [r"だね|だよ|でしょ|かな|みたい"],
            "neutral": [r"です|ます|である|だった"],
            "polite": [r"でございます|いらっしゃる|申し上げる"],
            "very_polite": [r"恐れ入ります|失礼いたします|お許しください"]
        }

        # 文体不整合パターン
        self.inconsistency_patterns = [
            (r"でございます", r"だぜ"),    # 超丁寧語と超カジュアルの混在
            (r"申し上げる", r"やべー"),      # 敬語と俗語の混在
            (r"恍惚", r"びっくり"),         # 高級語彙と基本語彙の混在
        ]

    async def execute(self, input_data: EmotionToolInput) -> EmotionToolOutput:
        """表現レベル適性検証の実行

        Args:
            input_data: 検証対象テキストと設定

        Returns:
            適性評価結果と調整提案
        """
        text = input_data.text
        metadata = input_data.metadata or {}

        target_audience = self._parse_enum(metadata.get("target_audience"), TargetAudience)
        genre = self._parse_enum(metadata.get("genre"), Genre)
        formality_level = self._parse_enum(metadata.get("formality_level"), FormalityLevel)

        # 文体要素抽出
        register_elements = self._extract_register_elements(text)

        # 適切性評価
        appropriateness_assessment = self._assess_appropriateness(
            register_elements, target_audience, genre, formality_level
        )

        # レベル不一致検出
        mismatches = self._detect_register_mismatches(
            register_elements, target_audience, genre, formality_level
        )

        # 調整提案生成
        adjustments = self._generate_adjustments(
            mismatches, target_audience, genre, formality_level
        )

        # スタイル一貫性評価
        style_consistency = self._evaluate_style_consistency(register_elements)

        analysis = {
            "appropriateness_score": appropriateness_assessment["score"],
            "vocabulary_level": appropriateness_assessment["vocabulary_analysis"],
            "formality_analysis": appropriateness_assessment["formality_analysis"],
            "genre_alignment": appropriateness_assessment["genre_alignment"],
            "register_mismatches": mismatches,
            "style_consistency": style_consistency,
            "element_count": len(register_elements),
            "register_distribution": self._analyze_register_distribution(register_elements)
        }

        # 総合スコア計算
        score = (
            appropriateness_assessment["score"] * 0.5 +
            style_consistency["score"] * 0.3 +
            max(0, 100 - len(mismatches) * 10) * 0.2
        )

        return self.create_success_output(
            score=score,
            analysis=analysis,
            suggestions=adjustments,
            metadata={
                "target_audience": target_audience.value if target_audience else None,
                "genre": genre.value if genre else None,
                "formality_level": formality_level.value if formality_level else None,
                "elements_analyzed": len(register_elements)
            }
        )


    def _parse_enum(self, value: str | None, enum_class) -> Any | None:
        """文字列をEnumに変換

        Args:
            value: 変換対象文字列
            enum_class: 対象Enumクラス

        Returns:
            Enum値またはNone
        """
        if not value:
            return None
        try:
            return enum_class(value)
        except ValueError:
            return None

    def _extract_register_elements(self, text: str) -> list[RegisterElement]:
        """文体要素の抽出

        Args:
            text: 分析対象テキスト

        Returns:
            抽出された文体要素リスト
        """
        elements = []

        # 語彙レベル抽出
        for level, patterns in self.vocabulary_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    elements.append(RegisterElement(
                        element_type="vocabulary",
                        content=match.group(),
                        register_level=str(level),
                        appropriateness_score=1.0,  # 初期値
                        position=match.span()
                    ))

        # 丁寧語レベル抽出
        for politeness_level, patterns in self.politeness_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    elements.append(RegisterElement(
                        element_type="politeness",
                        content=match.group(),
                        register_level=politeness_level,
                        appropriateness_score=1.0,
                        position=match.span()
                    ))

        return elements

    def _assess_appropriateness(self, elements: list[RegisterElement],
                              target_audience: TargetAudience | None,
                              genre: Genre | None,
                              formality_level: FormalityLevel | None) -> dict[str, Any]:
        """適切性評価

        Args:
            elements: 文体要素
            target_audience: 対象読者層
            genre: ジャンル
            formality_level: 文体レベル

        Returns:
            適切性評価結果
        """
        assessment = {
            "score": 50,  # デフォルト中立スコア
            "vocabulary_analysis": {},
            "formality_analysis": {},
            "genre_alignment": {}
        }

        if not elements:
            return assessment

        # 語彙レベル分析
        vocab_elements = [e for e in elements if e.element_type == "vocabulary"]
        if vocab_elements and target_audience and target_audience in self.audience_standards:
            standards = self.audience_standards[target_audience]
            vocab_range = standards["vocabulary_level"]

            appropriate_vocab = 0
            for element in vocab_elements:
                vocab_level = int(element.register_level)
                if vocab_range[0] <= vocab_level <= vocab_range[1]:
                    appropriate_vocab += 1

            vocab_score = (appropriate_vocab / len(vocab_elements)) * 100
            assessment["vocabulary_analysis"] = {
                "score": vocab_score,
                "appropriate_count": appropriate_vocab,
                "total_count": len(vocab_elements),
                "target_range": vocab_range
            }

        # 丁寧語レベル分析
        politeness_elements = [e for e in elements if e.element_type == "politeness"]
        if politeness_elements and target_audience and target_audience in self.audience_standards:
            preferred_formality = self.audience_standards[target_audience]["preferred_formality"]

            # 簡化した適合度計算
            formality_score = 70  # 基本スコア
            assessment["formality_analysis"] = {
                "score": formality_score,
                "preferred_level": preferred_formality.value,
                "detected_levels": [e.register_level for e in politeness_elements]
            }

        # ジャンル適合性分析
        if genre and genre in self.genre_standards:
            genre_score = 75  # 簡化した計算
            assessment["genre_alignment"] = {
                "score": genre_score,
                "genre_requirements": self.genre_standards[genre]
            }

        # 総合スコア計算
        scores = [
            assessment["vocabulary_analysis"].get("score", 50),
            assessment["formality_analysis"].get("score", 50),
            assessment["genre_alignment"].get("score", 50)
        ]
        assessment["score"] = sum(scores) / len(scores)

        return assessment

    def _detect_register_mismatches(self, elements: list[RegisterElement],
                                  target_audience: TargetAudience | None,
                                  genre: Genre | None,
                                  formality_level: FormalityLevel | None) -> list[str]:
        """レベル不一致の検出

        Args:
            elements: 文体要素
            target_audience: 対象読者層
            genre: ジャンル
            formality_level: 文体レベル

        Returns:
            不一致箇所のリスト
        """
        mismatches = []

        # 内部不整合の検出
        for pattern_pair in self.inconsistency_patterns:
            high_register = pattern_pair[0]
            low_register = pattern_pair[1]

            has_high = any(re.search(high_register, e.content) for e in elements)
            has_low = any(re.search(low_register, e.content) for e in elements)

            if has_high and has_low:
                mismatches.append("高い文体レベルと低い文体レベルが混在しています")

        # 読者層との不適合
        if target_audience == TargetAudience.TEEN:
            high_vocab_elements = [e for e in elements
                                 if e.element_type == "vocabulary" and int(e.register_level) >= 4]
            if high_vocab_elements:
                mismatches.append("10代読者には難しすぎる語彙が使用されています")

        # ジャンルとの不適合
        if genre == Genre.SLICE_OF_LIFE:
            dramatic_elements = [e for e in elements
                               if e.element_type == "vocabulary" and int(e.register_level) >= 4]
            if len(dramatic_elements) > 3:
                mismatches.append("日常系作品にしては劇的すぎる表現が多用されています")

        return mismatches

    def _generate_adjustments(self, mismatches: list[str],
                            target_audience: TargetAudience | None,
                            genre: Genre | None,
                            formality_level: FormalityLevel | None) -> list[str]:
        """調整提案の生成

        Args:
            mismatches: 不一致リスト
            target_audience: 対象読者層
            genre: ジャンル
            formality_level: 文体レベル

        Returns:
            調整提案リスト
        """
        adjustments = []

        # 不一致ごとの具体的提案
        for mismatch in mismatches:
            if "混在" in mismatch:
                adjustments.append("文体レベルを統一してください（丁寧語か casual語のいずれかに統一）")
            if "難しすぎる" in mismatch:
                adjustments.append("より平易な語彙に置き換えてください")
            if "劇的すぎる" in mismatch:
                adjustments.append("日常的で自然な表現に調整してください")

        # 対象読者層に基づく提案
        if target_audience == TargetAudience.TEEN:
            adjustments.append("10代読者向けに、親しみやすい表現を使用してください")
        elif target_audience == TargetAudience.ADULT:
            adjustments.append("成人読者向けに、品格のある表現を心がけてください")

        # ジャンルに基づく提案
        if genre == Genre.ROMANCE:
            adjustments.append("恋愛作品として、感情豊かで親密な表現を活用してください")
        elif genre == Genre.MYSTERY:
            adjustments.append("ミステリー作品として、抑制された緊張感のある表現を使用してください")

        return adjustments[:5]  # 最大5個の提案

    def _evaluate_style_consistency(self, elements: list[RegisterElement]) -> dict[str, Any]:
        """スタイル一貫性の評価

        Args:
            elements: 文体要素

        Returns:
            一貫性評価結果
        """
        if not elements:
            return {"score": 50, "consistency": "評価不可能"}

        # 語彙レベルの標準偏差計算
        vocab_elements = [e for e in elements if e.element_type == "vocabulary"]
        if vocab_elements:
            vocab_levels = [int(e.register_level) for e in vocab_elements]
            vocab_std = self._calculate_std_deviation(vocab_levels)

            # 標準偏差が小さいほど一貫している
            consistency_score = max(0, 100 - vocab_std * 20)
        else:
            consistency_score = 50

        return {
            "score": consistency_score,
            "vocabulary_std": vocab_std if vocab_elements else 0,
            "consistency": "良好" if consistency_score >= 70 else "要改善"
        }

    def _calculate_std_deviation(self, values: list[float]) -> float:
        """標準偏差計算

        Args:
            values: 数値リスト

        Returns:
            標準偏差
        """
        if not values:
            return 0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _analyze_register_distribution(self, elements: list[RegisterElement]) -> dict[str, dict[str, int]]:
        """文体要素分布の分析

        Args:
            elements: 文体要素

        Returns:
            分布分析結果
        """
        distribution = {}

        for element in elements:
            element_type = element.element_type
            level = element.register_level

            if element_type not in distribution:
                distribution[element_type] = {}

            distribution[element_type][level] = distribution[element_type].get(level, 0) + 1

        return distribution
