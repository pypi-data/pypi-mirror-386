"""陳腐表現検出ツール

感情表現における定型表現・陳腐化した比喩を検出し、
代替表現を提案する。
"""

import re
from typing import Any

from .base_emotion_tool import BaseEmotionTool, EmotionToolInput, EmotionToolOutput


class CliqueDetectorTool(BaseEmotionTool):
    """陳腐表現検出ツール

    定型的な感情表現パターンを検出し、代替案を提示する。
    五層感情表現システムの各層に対応。
    """

    def __init__(self) -> None:
        super().__init__("cliche_detector")
        self._load_cliche_patterns()

    def _initialize_tool(self) -> None:
        """ツール初期化: 陳腐表現パターンの読み込み"""
        self.logger.info("陳腐表現パターンデータベース初期化")

    def _load_cliche_patterns(self) -> None:
        """陳腐表現パターンの読み込み"""
        # 各感情層別の陳腐表現パターン
        self.cliche_patterns = {
            "physical": [
                r"ドキドキ",
                r"胸がキュン",
                r"震えが止まらない",
                r"血の気が引く",
                r"顔が赤くなる"
            ],
            "visceral": [
                r"胃がキリキリ",
                r"胸が詰まる",
                r"息が詰まる",
                r"心臓が止まりそう"
            ],
            "cardiac": [
                r"心臓が飛び出そう",
                r"息を呑む",
                r"動悸が激しい"
            ],
            "neural": [
                r"頭が真っ白",
                r"混乱する",
                r"思考停止"
            ],
            "metaphorical": [
                r"雲の上",
                r"地の底",
                r"天にも昇る",
                r"針のむしろ"
            ]
        }

        # 代替表現候補
        self.alternatives = {
            "ドキドキ": ["鼓動が早まる", "脈拍が上がる", "リズムが変わる"],
            "胸がキュン": ["胸に痛みが走る", "心臓が収縮する", "胸が締め付けられる"],
            "震えが止まらない": ["体の制御を失う", "四肢に力が入らない", "筋肉が硬直する"],
            "頭が真っ白": ["思考回路が停止する", "認知能力が低下する", "判断力を失う"]
        }

    async def execute(self, input_data: EmotionToolInput) -> EmotionToolOutput:
        """陳腐表現検出の実行

        Args:
            input_data: 分析対象テキストと設定

        Returns:
            検出結果と代替提案
        """
        text = input_data.text
        target_layer = input_data.emotion_layer.value if input_data.emotion_layer else None

        # 陳腐表現検出
        detected_cliches = self._detect_cliches(text, target_layer)

        # 重要度計算
        severity = self._calculate_severity(detected_cliches, len(text))

        # 代替表現生成
        alternatives = self._generate_alternatives(detected_cliches)

        analysis = {
            "cliche_count": len(detected_cliches),
            "flagged_phrases": [item["phrase"] for item in detected_cliches],
            "severity": severity,
            "pattern_distribution": self._analyze_pattern_distribution(detected_cliches),
            "text_length": len(text),
            "cliche_density": len(detected_cliches) / max(len(text), 1) * 1000  # per 1000 chars
        }

        suggestions = [
            f"「{item['phrase']}」→「{alt}」"
            for item in detected_cliches
            for alt in self.alternatives.get(item["phrase"], ["より具体的な表現に変更"])[:2]
        ]

        # スコア計算（低いほど陳腐表現が多い）
        score = max(0, 100 - (len(detected_cliches) * 15))

        return self.create_success_output(
            score=score,
            analysis=analysis,
            suggestions=suggestions,
            metadata={
                "alternatives_provided": len(alternatives),
                "layers_analyzed": target_layer or "all"
            }
        )

    def _detect_cliches(self, text: str, target_layer: str | None = None) -> list[dict[str, Any]]:
        """テキスト内の陳腐表現を検出

        Args:
            text: 分析対象テキスト
            target_layer: 対象感情層（None=全層）

        Returns:
            検出された陳腐表現のリスト
        """
        detected = []

        # 対象層の決定
        layers_to_check = [target_layer] if target_layer else list(self.cliche_patterns.keys())

        for layer in layers_to_check:
            if layer not in self.cliche_patterns:
                continue

            for pattern in self.cliche_patterns[layer]:
                matches = re.finditer(pattern, text)
                for match in matches:
                    detected.append({
                        "phrase": match.group(),
                        "layer": layer,
                        "position": match.span(),
                        "pattern": pattern
                    })

        return detected

    def _calculate_severity(self, cliches: list[dict], text_length: int) -> str:
        """陳腐表現の深刻度を計算

        Args:
            cliches: 検出された陳腐表現
            text_length: テキスト長

        Returns:
            深刻度レベル
        """
        if not cliches:
            return "none"

        density = len(cliches) / max(text_length, 1) * 1000

        if density > 10:
            return "high"
        if density > 5:
            return "medium"
        return "low"

    def _analyze_pattern_distribution(self, cliches: list[dict]) -> dict[str, int]:
        """陳腐表現の層別分布分析

        Args:
            cliches: 検出された陳腐表現

        Returns:
            層別分布
        """
        distribution = {}
        for cliche in cliches:
            layer = cliche["layer"]
            distribution[layer] = distribution.get(layer, 0) + 1
        return distribution

    def _generate_alternatives(self, cliches: list[dict]) -> dict[str, list[str]]:
        """代替表現の生成

        Args:
            cliches: 検出された陳腐表現

        Returns:
            表現別代替候補
        """
        alternatives = {}
        for cliche in cliches:
            phrase = cliche["phrase"]
            if phrase in self.alternatives:
                alternatives[phrase] = self.alternatives[phrase]
        return alternatives
