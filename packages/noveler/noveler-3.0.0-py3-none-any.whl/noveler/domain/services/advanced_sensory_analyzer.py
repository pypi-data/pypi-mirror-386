#!/usr/bin/env python3
"""高精度五感描画分析エンジン

手動Claude Code分析レベルの五感描写分析を実現するドメインサービス。
各五感の具体性、効果的配置、読者体験への影響を定量化・評価。
"""

import re
from dataclasses import dataclass
from typing import Any

from noveler.domain.value_objects.improvement_suggestion import ImprovementSuggestion


@dataclass
class SensoryDetection:
    """五感検出結果"""

    sense_type: str  # visual, auditory, tactile, olfactory, gustatory
    line_number: int
    text_snippet: str
    intensity_score: float  # 描写の強度（0-100）
    specificity_score: float  # 具体性スコア（0-100）
    effectiveness_score: float  # 効果性スコア（0-100）
    keywords_found: list[str]
    context_relevance: float  # 文脈適合性（0-100）


@dataclass
class SensoryAnalysisResult:
    """五感描画分析結果"""

    overall_score: float
    visual_score: float
    auditory_score: float
    tactile_score: float
    olfactory_score: float
    gustatory_score: float
    sensory_balance_score: float  # 五感バランススコア
    immersion_effect_score: float  # 没入効果スコア
    sensory_detections: list[SensoryDetection]
    missing_senses: list[str]  # 不足している感覚
    sensory_density: float  # 五感描写密度
    specific_suggestions: list[ImprovementSuggestion]

    def get_detailed_feedback(self) -> str:
        """詳細フィードバック生成"""
        feedback_parts = []

        # 不足している感覚の指摘
        if self.missing_senses:
            sense_names = {
                "visual": "視覚",
                "auditory": "聴覚",
                "tactile": "触覚",
                "olfactory": "嗅覚",
                "gustatory": "味覚",
            }
            missing_names = [sense_names.get(sense, sense) for sense in self.missing_senses]
            feedback_parts.append(f"不足している感覚: {', '.join(missing_names)}の描写を追加してください。")

        # 五感バランスの評価
        if self.sensory_balance_score < 60:
            feedback_parts.append(
                "五感描写のバランスが偏っています。多様な感覚を組み合わせて豊かな表現を作りましょう。"
            )

        # 没入効果の評価
        if self.immersion_effect_score < 70:
            feedback_parts.append("読者の没入感を高めるため、より具体的で鮮明な五感描写を心がけてください。")

        # 密度の評価
        if self.sensory_density < 0.1:
            feedback_parts.append(
                "五感描写の密度が低いです。適切な箇所に感覚的な表現を加えて臨場感を向上させてください。"
            )

        return (
            " ".join(feedback_parts)
            if feedback_parts
            else "五感描写は良好です。読者の感覚に訴える豊かな表現が使われています。"
        )


class AdvancedSensoryAnalyzer:
    """高精度五感描画分析エンジン

    手動分析レベルの詳細な五感描写分析を実行。
    各感覚の具体性、効果性、文脈適合性を総合評価。
    """

    def __init__(self) -> None:
        """高精度五感分析エンジン初期化"""
        self._sensory_patterns = self._initialize_sensory_patterns()
        self._context_indicators = self._initialize_context_indicators()
        self._intensity_modifiers = self._initialize_intensity_modifiers()

    def analyze_sensory_descriptions(self, content: str) -> SensoryAnalysisResult:
        """五感描写の詳細分析

        Args:
            content: 分析対象テキスト

        Returns:
            SensoryAnalysisResult: 五感分析結果
        """
        lines = content.split("\n")
        sensory_detections = []

        # 各行で五感描写を検出・分析
        for i, line in enumerate(lines, 1):
            line_detections = self._analyze_line_sensory(i, line, lines)
            sensory_detections.extend(line_detections)

        # 感覚別スコア計算
        sense_scores = self._calculate_sense_scores(sensory_detections)

        # 五感バランス分析
        balance_score = self._calculate_sensory_balance(sense_scores)

        # 没入効果分析
        immersion_score = self._calculate_immersion_effect(sensory_detections, content)

        # 五感密度計算
        sensory_density = self._calculate_sensory_density(sensory_detections, content)

        # 不足感覚特定
        missing_senses = self._identify_missing_senses(sense_scores)

        # 改善提案生成
        suggestions = self._generate_sensory_suggestions(sense_scores, missing_senses, sensory_density, immersion_score)

        # 総合スコア計算
        overall_score = self._calculate_overall_sensory_score(
            sense_scores, balance_score, immersion_score, sensory_density
        )

        return SensoryAnalysisResult(
            overall_score=overall_score,
            visual_score=sense_scores["visual"],
            auditory_score=sense_scores["auditory"],
            tactile_score=sense_scores["tactile"],
            olfactory_score=sense_scores["olfactory"],
            gustatory_score=sense_scores["gustatory"],
            sensory_balance_score=balance_score,
            immersion_effect_score=immersion_score,
            sensory_detections=sensory_detections,
            missing_senses=missing_senses,
            sensory_density=sensory_density,
            specific_suggestions=suggestions,
        )

    def _analyze_line_sensory(self, line_number: int, line: str, all_lines: list[str]) -> list[SensoryDetection]:
        """行単位の五感分析"""
        detections = []
        line = line.strip()

        if not line:
            return detections

        # 各感覚タイプについて分析
        for sense_type, patterns in self._sensory_patterns.items():
            detection = self._detect_sensory_in_line(sense_type, line_number, line, patterns, all_lines)

            if detection:
                detections.append(detection)

        return detections

    def _detect_sensory_in_line(
        self, sense_type: str, line_number: int, line: str, patterns: dict[str, Any], all_lines: list[str]
    ) -> SensoryDetection | None:
        """行内の特定感覚検出"""
        keywords_found = []
        max_intensity = 0.0
        best_snippet = ""

        # キーワードパターンマッチング
        for category, keywords in patterns["keywords"].items():
            for keyword in keywords:
                if keyword in line:
                    keywords_found.append(keyword)
                    # コンテキストスニペット抽出
                    start = max(0, line.find(keyword) - 10)
                    end = min(len(line), line.find(keyword) + len(keyword) + 10)
                    snippet = line[start:end]

                    # 強度計算
                    intensity = self._calculate_keyword_intensity(keyword, line, category, sense_type)

                    if intensity > max_intensity:
                        max_intensity = intensity
                        best_snippet = snippet

        if not keywords_found:
            return None

        # 具体性スコア計算
        specificity_score = self._calculate_specificity_score(line, keywords_found, sense_type)

        # 効果性スコア計算
        effectiveness_score = self._calculate_effectiveness_score(line, keywords_found, sense_type)

        # 文脈適合性計算
        context_relevance = self._calculate_context_relevance(line_number, line, all_lines, sense_type)

        return SensoryDetection(
            sense_type=sense_type,
            line_number=line_number,
            text_snippet=best_snippet,
            intensity_score=max_intensity,
            specificity_score=specificity_score,
            effectiveness_score=effectiveness_score,
            keywords_found=keywords_found,
            context_relevance=context_relevance,
        )

    def _calculate_keyword_intensity(self, keyword: str, line: str, category: str, sense_type: str) -> float:
        """キーワード強度の計算"""
        base_intensity = 50.0

        # カテゴリ別基本強度
        category_weights = {
            "strong": 80.0,  # 強い表現
            "moderate": 60.0,  # 中程度表現
            "subtle": 40.0,  # 微細表現
            "basic": 30.0,  # 基本表現
        }

        base_intensity = category_weights.get(category, 50.0)

        # 修飾語による強度増減
        for modifier, adjustment in self._intensity_modifiers.items():
            if modifier in line:
                base_intensity += adjustment

        # 感覚タイプ別調整
        if sense_type == "visual":
            # 色彩表現は高強度
            if any(color in line for color in ["赤", "青", "緑", "金", "銀", "黒", "白"]):
                base_intensity += 15
        elif sense_type == "auditory":
            # 擬音語は高強度
            if re.search(r"[ァ-ンー]{2,}", line):  # カタカナ擬音:
                base_intensity += 20

        return min(100.0, max(0.0, base_intensity))

    def _calculate_specificity_score(self, line: str, keywords: list[str], sense_type: str) -> float:
        """具体性スコア計算"""
        specificity = 50.0

        # 具体的な修飾語の存在
        specific_modifiers = [
            "鮮やかな",
            "深い",
            "淡い",
            "激しい",
            "微かな",
            "かすかな",
            "強烈な",
            "優しい",
            "鋭い",
            "温かい",
            "冷たい",
            "湿った",
            "乾いた",
        ]

        modifier_count = sum(1 for modifier in specific_modifiers if modifier in line)
        specificity += modifier_count * 10

        # 数値的表現（より具体的）
        if re.search(r"\d+", line):
            specificity += 10

        # 比較表現（具体性を高める）
        comparison_patterns = ["より", "もっと", "まるで", "のような", "みたい"]
        if any(pattern in line for pattern in comparison_patterns):
            specificity += 15

        # 感覚タイプ別具体性チェック
        if sense_type == "visual":
            # 形状・大きさの表現
            if any(shape in line for shape in ["丸い", "四角", "細い", "太い", "大きな", "小さな"]):
                specificity += 10
        elif sense_type == "auditory":
            # 音の性質表現
            if any(quality in line for quality in ["高い", "低い", "大きな", "小さな", "甲高い"]):
                specificity += 10

        return min(100.0, max(0.0, specificity))

    def _calculate_effectiveness_score(self, line: str, keywords: list[str], sense_type: str) -> float:
        """効果性スコア計算"""
        effectiveness = 50.0

        # 感情との結びつき
        emotional_words = [
            "美しい",
            "恐ろしい",
            "心地よい",
            "不快な",
            "懐かしい",
            "新鮮な",
            "驚く",
            "感動",
            "興奮",
            "安らぎ",
            "緊張",
            "ドキドキ",
        ]
        if any(emotion in line for emotion in emotional_words):
            effectiveness += 20

        # 行動との連携
        action_words = ["見る", "聞く", "触る", "嗅ぐ", "味わう", "感じる", "体験"]
        if any(action in line for action in action_words):
            effectiveness += 15

        # キャラクターの反応
        reaction_patterns = ["思った", "した", "なった", "感じた", "気がした"]
        if any(reaction in line for reaction in reaction_patterns):
            effectiveness += 10

        return min(100.0, max(0.0, effectiveness))

    def _calculate_context_relevance(self, line_number: int, line: str, all_lines: list[str], sense_type: str) -> float:
        """文脈適合性計算"""
        relevance = 70.0  # 基本値

        # 前後の文脈チェック
        context_start = max(0, line_number - 3)
        context_end = min(len(all_lines), line_number + 2)
        context_lines = all_lines[context_start:context_end]
        context_text = " ".join(context_lines)

        # 場面設定との適合性
        scene_indicators = self._context_indicators.get("scene_types", {})
        for scene_type, indicators in scene_indicators.items():
            if any(indicator in context_text for indicator in indicators):
                # 感覚と場面の適合性評価
                scene_sense_match = self._get_scene_sense_match(scene_type, sense_type)
                relevance += scene_sense_match
                break

        # 五感描写の集中度（適度な分散が良い）
        nearby_sensory_count = 0
        for context_line in context_lines:
            if context_line != line:
                for patterns in self._sensory_patterns.values():
                    for keywords in patterns["keywords"].values():
                        if any(keyword in context_line for keyword in keywords):
                            nearby_sensory_count += 1

        # 適度な分散を評価
        if nearby_sensory_count > 5:  # 過度に集中:
            relevance -= 10
        elif nearby_sensory_count < 1:  # 孤立
            relevance -= 5

        return min(100.0, max(0.0, relevance))

    def _get_scene_sense_match(self, scene_type: str, sense_type: str) -> float:
        """場面と感覚の適合性評価"""
        # 場面別適合感覚のマッピング
        scene_sense_compatibility = {
            "battle": {"auditory": 15, "visual": 10, "tactile": 10},
            "meal": {"gustatory": 20, "olfactory": 15, "visual": 5},
            "nature": {"visual": 15, "auditory": 10, "olfactory": 10},
            "indoor": {"tactile": 10, "visual": 5, "olfactory": 5},
            "emotional": {"tactile": 10, "visual": 5, "auditory": 5},
        }

        return scene_sense_compatibility.get(scene_type, {}).get(sense_type, 0)

    def _calculate_sense_scores(self, detections: list[SensoryDetection]) -> dict[str, float]:
        """感覚別スコア計算"""
        sense_types = ["visual", "auditory", "tactile", "olfactory", "gustatory"]
        sense_scores = {}

        for sense_type in sense_types:
            sense_detections = [d for d in detections if d.sense_type == sense_type]

            if not sense_detections:
                sense_scores[sense_type] = 0.0
                continue

            # 平均スコア計算（強度、具体性、効果性の加重平均）
            total_score = 0.0
            for detection in sense_detections:
                weighted_score = (
                    detection.intensity_score * 0.3
                    + detection.specificity_score * 0.4
                    + detection.effectiveness_score * 0.3
                )

                total_score += weighted_score

            sense_scores[sense_type] = total_score / len(sense_detections)

        return sense_scores

    def _calculate_sensory_balance(self, sense_scores: dict[str, float]) -> float:
        """五感バランススコア計算"""
        active_senses = [score for score in sense_scores.values() if score > 0]

        if len(active_senses) < 2:
            return 30.0  # 1つ以下の感覚のみ
        if len(active_senses) < 3:
            return 60.0  # 2つの感覚
        if len(active_senses) < 4:
            return 80.0  # 3つの感覚
        if len(active_senses) < 5:
            return 95.0  # 4つの感覚
        return 100.0  # 全ての感覚

    def _calculate_immersion_effect(self, detections: list[SensoryDetection], content: str) -> float:
        """没入効果スコア計算"""
        if not detections:
            return 0.0

        # 効果性スコアの平均
        avg_effectiveness = sum(d.effectiveness_score for d in detections) / len(detections)

        # 五感描写の配置評価（適度な分散）
        line_numbers = [d.line_number for d in detections]
        content_lines = len(content.split("\n"))

        distribution_score = min(100.0, len(set(line_numbers)) / content_lines * 200) if content_lines > 0 else 50.0

        # 感覚の多様性効果
        unique_senses = len({d.sense_type for d in detections})
        diversity_bonus = unique_senses * 10

        immersion_score = avg_effectiveness * 0.6 + distribution_score * 0.3 + diversity_bonus * 0.1

        return min(100.0, max(0.0, immersion_score))

    def _calculate_sensory_density(self, detections: list[SensoryDetection], content: str) -> float:
        """五感描写密度計算"""
        content_length = len(content)
        if content_length == 0:
            return 0.0

        return len(detections) / (content_length / 1000)  # 1000文字あたりの五感描写数

    def _identify_missing_senses(self, sense_scores: dict[str, float]) -> list[str]:
        """不足感覚の特定"""
        return [sense for sense, score in sense_scores.items() if score == 0.0]

    def _generate_sensory_suggestions(
        self, sense_scores: dict[str, float], missing_senses: list[str], sensory_density: float, immersion_score: float
    ) -> list[ImprovementSuggestion]:
        """五感改善提案生成"""
        suggestions = []

        # 不足感覚への提案
        sense_names = {
            "visual": "視覚",
            "auditory": "聴覚",
            "tactile": "触覚",
            "olfactory": "嗅覚",
            "gustatory": "味覚",
        }

        for missing_sense in missing_senses:
            sense_name = sense_names.get(missing_sense, missing_sense)
            examples = self._get_sensory_examples(missing_sense)

            suggestions.append(
                ImprovementSuggestion.create(
                    content=f"{sense_name}描写を追加してください。例: {examples}", suggestion_type="enhancement"
                )
            )

        # 密度向上提案
        if sensory_density < 0.1:
            suggestions.append(
                ImprovementSuggestion.create(
                    content="五感描写の密度を高めてください。読者が場面を体感できるよう、適切な箇所に感覚的表現を追加しましょう。",
                    suggestion_type="enhancement",
                )
            )

        # 没入効果向上提案
        if immersion_score < 70:
            suggestions.append(
                ImprovementSuggestion.create(
                    content="読者の没入感を高めるため、より具体的で鮮明な五感描写を心がけてください。キャラクターの感覚体験を詳細に描写しましょう。",
                    suggestion_type="enhancement",
                )
            )

        return suggestions

    def _get_sensory_examples(self, sense_type: str) -> str:
        """感覚別の例文提供"""
        examples = {
            "visual": "「金色に輝く夕日」「深い青色の空」",
            "auditory": "「かすかな足音」「鳥のさえずり」",
            "tactile": "「ひんやりした風」「ざらざらした手触り」",
            "olfactory": "「花の甘い香り」「焦げた匂い」",
            "gustatory": "「苦い味」「甘酸っぱい果実」",
        }
        return examples.get(sense_type, "具体的な感覚表現")

    def _calculate_overall_sensory_score(
        self, sense_scores: dict[str, float], balance_score: float, immersion_score: float, sensory_density: float
    ) -> float:
        """総合五感スコア計算"""
        # 各感覚の平均スコア
        active_sense_scores = [score for score in sense_scores.values() if score > 0]
        avg_sense_score = sum(active_sense_scores) / len(active_sense_scores) if active_sense_scores else 0.0

        # 密度スコア（適切な範囲での正規化）
        density_score = min(100.0, sensory_density * 100)

        # 加重平均による総合スコア
        overall_score = (
            avg_sense_score * 0.4  # 個別感覚品質
            + balance_score * 0.25  # 五感バランス
            + immersion_score * 0.25  # 没入効果
            + density_score * 0.1  # 描写密度
        )

        return min(100.0, max(0.0, overall_score))

    def _initialize_sensory_patterns(self) -> dict[str, dict[str, Any]]:
        """五感パターン初期化"""
        return {
            "visual": {
                "keywords": {
                    "strong": ["眩しい", "鮮やか", "輝く", "光る", "煌めく", "美しい"],
                    "moderate": ["見える", "色", "形", "影", "光", "明るい", "暗い"],
                    "subtle": ["目", "視線", "ちらっと", "じっと", "眺める"],
                    "basic": ["見る", "見た", "見て"],
                }
            },
            "auditory": {
                "keywords": {
                    "strong": ["轟音", "響く", "鳴り響く", "大きな音", "騒音"],
                    "moderate": ["音", "声", "聞こえる", "響き", "静か"],
                    "subtle": ["ささやき", "つぶやき", "かすか", "微か"],
                    "basic": ["聞く", "聞いた", "聞こえた"],
                }
            },
            "tactile": {
                "keywords": {
                    "strong": ["激痛", "熱い", "冷たい", "ひりひり", "ざらざら"],
                    "moderate": ["触る", "感じる", "温かい", "涼しい", "痛い"],
                    "subtle": ["そっと", "やわらか", "なめらか"],
                    "basic": ["触れる", "手", "指"],
                }
            },
            "olfactory": {
                "keywords": {
                    "strong": ["強烈な匂い", "香ばしい", "芳しい", "悪臭"],
                    "moderate": ["匂い", "香り", "臭い", "嗅ぐ"],
                    "subtle": ["かすかな", "ほのか", "ふわっと"],
                    "basic": ["匂う", "香る"],
                }
            },
            "gustatory": {
                "keywords": {
                    "strong": ["美味しい", "まずい", "甘い", "辛い", "苦い", "酸っぱい"],
                    "moderate": ["味", "舌", "口", "飲む", "食べる"],
                    "subtle": ["ほんのり", "かすかに", "微かに"],
                    "basic": ["味わう", "食べる", "飲む"],
                }
            },
        }

    def _initialize_context_indicators(self) -> dict[str, dict[str, list[str]]]:
        """文脈指標初期化"""
        return {
            "scene_types": {
                "battle": ["戦い", "戦闘", "剣", "魔法", "攻撃", "防御"],
                "meal": ["食事", "料理", "食べる", "飲む", "テーブル", "皿"],
                "nature": ["森", "山", "川", "海", "空", "風", "木", "花"],
                "indoor": ["部屋", "家", "建物", "廊下", "窓", "ドア"],
                "emotional": ["泣く", "笑う", "怒る", "悲しい", "嬉しい", "感動"],
            }
        }

    def _initialize_intensity_modifiers(self) -> dict[str, float]:
        """強度修飾語初期化"""
        return {
            "とても": 10,
            "すごく": 10,
            "非常に": 15,
            "極めて": 20,
            "かなり": 8,
            "やや": 5,
            "少し": 3,
            "わずかに": 2,
            "まったく": 15,
            "全く": 15,
            "ひどく": 12,
            "激しく": 15,
        }
