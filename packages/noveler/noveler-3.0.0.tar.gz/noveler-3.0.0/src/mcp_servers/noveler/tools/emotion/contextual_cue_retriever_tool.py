"""文脈手がかり抽出ツール

既存テキストから感情表現に活用可能な文脈要素を抽出し、
感情表現の一貫性とリアリティを向上させる。
"""

import re
from dataclasses import dataclass
from typing import Any

from .base_emotion_tool import BaseEmotionTool, EmotionToolInput, EmotionToolOutput


@dataclass
class ContextualElement:
    """文脈要素データ構造"""
    element_type: str  # setting, character, action, object
    content: str
    relevance_score: float
    position: tuple  # (start, end)
    emotion_potential: str  # どの感情に寄与するか


class ContextualCueRetrieverTool(BaseEmotionTool):
    """文脈手がかり抽出ツール

    周辺テキストから感情表現に活用できる要素を抽出し、
    文脈に一貫した感情描写を支援する。
    """

    def __init__(self) -> None:
        super().__init__("contextual_cue_retriever")
        self._initialize_extraction_patterns()

    def _initialize_tool(self) -> None:
        """ツール初期化"""
        self.logger.info("文脈抽出パターン初期化")

    def _initialize_extraction_patterns(self) -> None:
        """抽出パターンの初期化"""
        # 設定要素パターン
        self.setting_patterns = [
            r"(朝|昼|夕方|夜|深夜)の(.*?)で",
            r"(晴れ|雨|雪|曇り)の(.*?)に",
            r"(静か|騒がしい|暗い|明るい)な(.*?)で",
            r"(暖かい|寒い|涼しい|暑い)(.*?)だった"
        ]

        # キャラクター状態パターン
        self.character_patterns = [
            r"([\w]+)は(疲れて|緊張して|不安で|喜んで|怒って)",
            r"([\w]+)の(表情|目|声|態度)が",
            r"([\w]+)は(座って|立って|歩いて|走って)"
        ]

        # アクションパターン
        self.action_patterns = [
            r"(急いで|ゆっくりと|慎重に|勢いよく)(.*?)した",
            r"(声を上げて|静かに|大きな声で)(.*?)言った",
            r"(優しく|強く|そっと|激しく)(.*?)した"
        ]

        # 感情誘発オブジェクトパターン
        self.object_patterns = [
            r"(手紙|写真|日記|プレゼント|思い出)",
            r"(机|椅子|窓|ドア|鏡)の",
            r"(花|樹|空|星|月)を"
        ]

        # 感情マッピング
        self.emotion_mapping = {
            "朝": ["hope", "fresh", "energy"],
            "夜": ["melancholy", "mystery", "intimacy"],
            "雨": ["sadness", "contemplation", "cleansing"],
            "晴れ": ["joy", "optimism", "clarity"],
            "疲れて": ["exhaustion", "vulnerability"],
            "緊張して": ["anxiety", "anticipation"],
            "手紙": ["nostalgia", "connection", "surprise"],
            "写真": ["memory", "longing", "happiness"]
        }

    async def execute(self, input_data: EmotionToolInput) -> EmotionToolOutput:
        """文脈手がかり抽出の実行

        Args:
            input_data: 分析対象テキストと目標感情

        Returns:
            抽出された文脈要素と活用提案
        """
        context_text = input_data.text
        target_emotion = input_data.metadata.get("target_emotion") if input_data.metadata else None
        scene_setting = input_data.metadata.get("scene_setting") if input_data.metadata else None

        # 文脈要素抽出
        extracted_elements = self._extract_contextual_elements(context_text)

        # 感情アンカー特定
        emotion_anchors = self._identify_emotion_anchors(extracted_elements, target_emotion)

        # 文脈整合性評価
        consistency_score = self._evaluate_consistency(extracted_elements, target_emotion)

        # 強化提案生成
        enhancement_suggestions = self._generate_enhancements(
            extracted_elements, target_emotion, scene_setting
        )

        analysis = {
            "contextual_elements": [
                {
                    "type": elem.element_type,
                    "content": elem.content,
                    "relevance": elem.relevance_score,
                    "emotion_potential": elem.emotion_potential
                }
                for elem in extracted_elements
            ],
            "emotion_anchors": emotion_anchors,
            "consistency_score": consistency_score,
            "element_distribution": self._analyze_element_distribution(extracted_elements),
            "total_elements_found": len(extracted_elements)
        }

        # スコア計算
        score = min(100, consistency_score * 20 + len(emotion_anchors) * 10)

        return self.create_success_output(
            score=score,
            analysis=analysis,
            suggestions=enhancement_suggestions,
            metadata={
                "target_emotion": target_emotion,
                "elements_extracted": len(extracted_elements),
                "anchors_found": len(emotion_anchors)
            }
        )

    def _extract_contextual_elements(self, text: str) -> list[ContextualElement]:
        """テキストから文脈要素を抽出

        Args:
            text: 分析対象テキスト

        Returns:
            抽出された文脈要素リスト
        """
        elements = []

        # 設定要素抽出
        for pattern in self.setting_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                elements.append(ContextualElement(
                    element_type="setting",
                    content=match.group(),
                    relevance_score=0.7,
                    position=match.span(),
                    emotion_potential=self._get_emotion_potential(match.group())
                ))

        # キャラクター状態抽出
        for pattern in self.character_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                elements.append(ContextualElement(
                    element_type="character",
                    content=match.group(),
                    relevance_score=0.8,
                    position=match.span(),
                    emotion_potential=self._get_emotion_potential(match.group())
                ))

        # アクション抽出
        for pattern in self.action_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                elements.append(ContextualElement(
                    element_type="action",
                    content=match.group(),
                    relevance_score=0.6,
                    position=match.span(),
                    emotion_potential=self._get_emotion_potential(match.group())
                ))

        # オブジェクト抽出
        for pattern in self.object_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                elements.append(ContextualElement(
                    element_type="object",
                    content=match.group(),
                    relevance_score=0.5,
                    position=match.span(),
                    emotion_potential=self._get_emotion_potential(match.group())
                ))

        return elements

    def _get_emotion_potential(self, text: str) -> str:
        """テキストの感情誘発可能性を評価

        Args:
            text: 評価対象テキスト

        Returns:
            感情可能性の説明
        """
        for key, emotions in self.emotion_mapping.items():
            if key in text:
                return f"{key} → {', '.join(emotions)}"
        return "neutral"

    def _identify_emotion_anchors(self, elements: list[ContextualElement], target_emotion: str | None) -> list[dict[str, Any]]:
        """感情アンカー（感情の足がかり）を特定

        Args:
            elements: 抽出された文脈要素
            target_emotion: 目標感情

        Returns:
            感情アンカーのリスト
        """
        anchors = []

        for element in elements:
            if target_emotion and target_emotion in element.emotion_potential:
                anchors.append({
                    "element": element.content,
                    "type": element.element_type,
                    "emotion_connection": element.emotion_potential,
                    "strength": element.relevance_score
                })

        # relevance_scoreでソート
        anchors.sort(key=lambda x: x["strength"], reverse=True)
        return anchors[:5]  # 上位5個を返す

    def _evaluate_consistency(self, elements: list[ContextualElement], target_emotion: str | None) -> float:
        """文脈整合性を評価

        Args:
            elements: 文脈要素
            target_emotion: 目標感情

        Returns:
            整合性スコア（0-5）
        """
        if not elements:
            return 0.0

        consistent_elements = 0
        total_weight = 0

        for element in elements:
            total_weight += element.relevance_score
            if target_emotion and target_emotion in element.emotion_potential:
                consistent_elements += element.relevance_score

        if total_weight == 0:
            return 0.0

        return consistent_elements / total_weight * 5

    def _analyze_element_distribution(self, elements: list[ContextualElement]) -> dict[str, int]:
        """要素タイプ別分布の分析

        Args:
            elements: 文脈要素

        Returns:
            タイプ別分布
        """
        distribution = {}
        for element in elements:
            distribution[element.element_type] = distribution.get(element.element_type, 0) + 1
        return distribution

    def _generate_enhancements(self, elements: list[ContextualElement],
                             target_emotion: str | None,
                             scene_setting: str | None) -> list[str]:
        """文脈強化提案の生成

        Args:
            elements: 抽出された要素
            target_emotion: 目標感情
            scene_setting: シーン設定

        Returns:
            強化提案リスト
        """
        suggestions = []

        # 要素タイプ別の提案
        element_types = {elem.element_type for elem in elements}

        if "setting" not in element_types:
            suggestions.append("時間・場所・天候などの設定要素を追加して雰囲気作りを強化")

        if "character" not in element_types:
            suggestions.append("キャラクターの身体状態・表情の描写を追加")

        if "object" not in element_types:
            suggestions.append("感情を象徴する物品・アイテムの配置を検討")

        # 目標感情に基づく提案
        if target_emotion:
            if target_emotion == "sadness":
                suggestions.append("雨・薄暗さ・静寂などの憂鬱要素の活用を検討")
            elif target_emotion == "joy":
                suggestions.append("明るい光・暖かさ・活気のある要素の強調を検討")
            elif target_emotion == "fear":
                suggestions.append("暗闇・静寂・未知の要素で不安感を醸成")

        return suggestions[:5]  # 最大5個の提案
