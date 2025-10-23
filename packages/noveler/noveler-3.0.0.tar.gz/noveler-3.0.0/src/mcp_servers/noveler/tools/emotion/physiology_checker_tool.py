"""生理反応検証ツール

感情表現と生理学的反応の整合性を検証し、
医学的に正確で説得力のある感情描写を支援する。
"""

import re
from dataclasses import dataclass
from typing import Any

from .base_emotion_tool import BaseEmotionTool, EmotionIntensity, EmotionToolInput, EmotionToolOutput


@dataclass
class PhysiologicalResponse:
    """生理学的反応データ"""
    response_type: str  # cardiac, respiratory, muscular, neural, hormonal
    description: str
    normal_range: tuple[float, float]  # 正常範囲
    intensity_factor: float  # 感情強度との相関係数


class PhysiologyCheckerTool(BaseEmotionTool):
    """生理反応検証ツール

    感情表現に含まれる生理学的反応の医学的正確性をチェックし、
    感情強度との整合性を検証する。
    """

    def __init__(self) -> None:
        super().__init__("physiology_checker")
        self._initialize_physiological_database()

    def _initialize_tool(self) -> None:
        """ツール初期化"""
        self.logger.info("生理学的反応データベース初期化")

    def _initialize_physiological_database(self) -> None:
        """生理学的反応データベースの初期化"""
        # 感情別の正常な生理反応
        self.emotion_physiology_map = {
            "fear": {
                "heart_rate": (100, 180),  # 心拍数 (bpm)
                "breathing": (20, 40),      # 呼吸数 (per min)
                "blood_pressure": (140, 200), # 収縮期血圧
                "muscle_tension": (0.7, 1.0),  # 筋緊張度
                "cortisol": (1.5, 3.0)      # コルチゾール倍率
            },
            "anger": {
                "heart_rate": (90, 160),
                "breathing": (18, 35),
                "blood_pressure": (150, 210),
                "muscle_tension": (0.8, 1.0),
                "adrenaline": (2.0, 5.0)
            },
            "sadness": {
                "heart_rate": (50, 80),
                "breathing": (8, 15),
                "blood_pressure": (90, 120),
                "muscle_tension": (0.3, 0.6),
                "serotonin": (0.5, 0.8)
            },
            "joy": {
                "heart_rate": (80, 120),
                "breathing": (15, 25),
                "blood_pressure": (110, 140),
                "muscle_tension": (0.4, 0.7),
                "endorphin": (1.5, 3.0)
            }
        }

        # 生理反応検出パターン
        self.physiology_patterns = {
            "heart_rate": [
                r"心拍(?:数)?(?:が)?(.*?)(?:回|拍)",
                r"脈拍(?:が)?(.*?)(?:回|拍)",
                r"ドキドキ",
                r"心臓が(?:激しく|早く|遅く)"
            ],
            "breathing": [
                r"呼吸(?:が)?(.*?)(?:回|回/分)",
                r"息(?:が)?(.*?)(?:荒い|浅い|深い|止まる)",
                r"ハァハァ",
                r"息切れ"
            ],
            "blood_pressure": [
                r"血圧(?:が)?(\d+)/(\d+)",
                r"のぼせ",
                r"顔が赤く",
                r"血の気が引く"
            ],
            "muscle_tension": [
                r"筋肉(?:が)?(.*?)(?:緊張|硬直|こわばる)",
                r"体(?:が)?(.*?)(?:硬く|強張る|震える)",
                r"力が入らない",
                r"脱力"
            ],
            "autonomic": [
                r"汗(?:が)?(.*?)(?:出る|流れる|止まらない)",
                r"震え(?:が)?(.*?)(?:止まらない|激しい)",
                r"寒気",
                r"冷や汗"
            ]
        }

        # 不整合パターン（医学的におかしい組み合わせ）
        self.inconsistent_combinations = [
            ("fear", "heart_rate", 40),  # 恐怖で心拍数40は低すぎる
            ("anger", "blood_pressure", 80),  # 怒りで血圧80は低すぎる
            ("joy", "muscle_tension", 1.0),   # 喜びで筋緊張最大は不自然
            ("sadness", "heart_rate", 150)    # 悲しみで心拍150は高すぎる
        ]

    async def execute(self, input_data: EmotionToolInput) -> EmotionToolOutput:
        """生理反応検証の実行

        Args:
            input_data: 検証対象テキストと感情情報

        Returns:
            生理学的正確性の評価結果
        """
        text = input_data.text
        emotion = input_data.metadata.get("emotion") if input_data.metadata else None
        intensity = input_data.intensity or EmotionIntensity.MODERATE

        # 生理学的反応抽出
        extracted_responses = self._extract_physiological_responses(text)

        # 医学的正確性検証
        accuracy_assessment = self._assess_medical_accuracy(
            extracted_responses, emotion, intensity
        )

        # 不整合箇所検出
        inconsistencies = self._detect_inconsistencies(
            extracted_responses, emotion, intensity
        )

        # 修正提案生成
        corrections = self._generate_corrections(inconsistencies, emotion, intensity)

        # 感情強度との整合性評価
        intensity_alignment = self._evaluate_intensity_alignment(
            extracted_responses, emotion, intensity
        )

        analysis = {
            "extracted_responses": extracted_responses,
            "accuracy_score": accuracy_assessment["score"],
            "medical_accuracy": accuracy_assessment["details"],
            "inconsistencies": inconsistencies,
            "intensity_alignment": intensity_alignment,
            "response_count": len(extracted_responses),
            "coverage_by_type": self._analyze_response_coverage(extracted_responses)
        }

        # 総合スコア計算
        score = (
            accuracy_assessment["score"] * 0.4 +
            intensity_alignment["score"] * 0.3 +
            max(0, 100 - len(inconsistencies) * 20) * 0.3
        )

        return self.create_success_output(
            score=score,
            analysis=analysis,
            suggestions=corrections,
            metadata={
                "emotion_analyzed": emotion,
                "intensity_level": intensity.value if intensity else None,
                "responses_found": len(extracted_responses)
            }
        )

    def _extract_physiological_responses(self, text: str) -> list[dict[str, Any]]:
        """テキストから生理学的反応を抽出

        Args:
            text: 分析対象テキスト

        Returns:
            抽出された生理反応のリスト
        """
        responses = []

        for response_type, patterns in self.physiology_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    responses.append({
                        "type": response_type,
                        "description": match.group(),
                        "position": match.span(),
                        "pattern_matched": pattern,
                        "extracted_value": self._extract_numeric_value(match.group())
                    })

        return responses

    def _extract_numeric_value(self, text: str) -> float | None:
        """テキストから数値を抽出

        Args:
            text: 抽出対象テキスト

        Returns:
            抽出された数値（なければNone）
        """
        numbers = re.findall(r"\d+", text)
        return float(numbers[0]) if numbers else None

    def _assess_medical_accuracy(self, responses: list[dict], emotion: str | None,
                                intensity: EmotionIntensity) -> dict[str, Any]:
        """医学的正確性の評価

        Args:
            responses: 抽出された生理反応
            emotion: 感情タイプ
            intensity: 感情強度

        Returns:
            正確性評価結果
        """
        if not emotion or emotion not in self.emotion_physiology_map:
            return {"score": 50, "details": "感情タイプが特定できません"}

        emotion_norms = self.emotion_physiology_map[emotion]
        accurate_responses = 0
        total_checkable = 0
        details = []

        for response in responses:
            response_type = response["type"]
            value = response["extracted_value"]

            if response_type in emotion_norms and value is not None:
                total_checkable += 1
                normal_range = emotion_norms[response_type]

                # 感情強度による調整
                intensity_factor = intensity.value / 5.0  # 0.2-2.0の範囲に正規化
                adjusted_range = (
                    normal_range[0] * intensity_factor,
                    normal_range[1] * intensity_factor
                )

                if adjusted_range[0] <= value <= adjusted_range[1]:
                    accurate_responses += 1
                    details.append(f"{response_type}: {value} - 正常範囲内")
                else:
                    details.append(f"{response_type}: {value} - 範囲外 (正常: {adjusted_range[0]:.1f}-{adjusted_range[1]:.1f})")

        score = (accurate_responses / max(total_checkable, 1)) * 100 if total_checkable > 0 else 50

        return {
            "score": score,
            "details": details,
            "accurate_count": accurate_responses,
            "total_checked": total_checkable
        }

    def _detect_inconsistencies(self, responses: list[dict], emotion: str | None,
                              intensity: EmotionIntensity) -> list[str]:
        """生理学的不整合の検出

        Args:
            responses: 生理反応
            emotion: 感情タイプ
            intensity: 感情強度

        Returns:
            不整合箇所のリスト
        """
        inconsistencies = []

        # 既知の不整合パターンチェック
        for incons_emotion, incons_type, incons_value in self.inconsistent_combinations:
            if emotion == incons_emotion:
                for response in responses:
                    if (response["type"] == incons_type and
                        response["extracted_value"] is not None and
                        abs(response["extracted_value"] - incons_value) < 10):
                        inconsistencies.append(
                            f"{emotion}の状態で{incons_type}={response['extracted_value']}は医学的に不自然"
                        )

        # 相互矛盾する反応のチェック
        heart_rates = [r["extracted_value"] for r in responses
                      if r["type"] == "heart_rate" and r["extracted_value"]]
        if len(heart_rates) > 1 and max(heart_rates) - min(heart_rates) > 50:
            inconsistencies.append("同一シーン内で心拍数に大きな変動があります")

        return inconsistencies

    def _generate_corrections(self, inconsistencies: list[str], emotion: str | None,
                            intensity: EmotionIntensity) -> list[str]:
        """修正提案の生成

        Args:
            inconsistencies: 不整合箇所
            emotion: 感情タイプ
            intensity: 感情強度

        Returns:
            修正提案のリスト
        """
        corrections = []

        if not emotion:
            return ["感情タイプを明確にして生理反応の妥当性を確認してください"]

        if emotion in self.emotion_physiology_map:
            norms = self.emotion_physiology_map[emotion]
            intensity_factor = intensity.value / 5.0

            for response_type, (min_val, max_val) in norms.items():
                adjusted_min = min_val * intensity_factor
                adjusted_max = max_val * intensity_factor

                if response_type == "heart_rate":
                    corrections.append(
                        f"{emotion}の場合、心拍数は{adjusted_min:.0f}-{adjusted_max:.0f}回/分が適切"
                    )
                elif response_type == "breathing":
                    corrections.append(
                        f"{emotion}の場合、呼吸数は{adjusted_min:.0f}-{adjusted_max:.0f}回/分が適切"
                    )

        # 不整合ごとの具体的修正提案
        for inconsistency in inconsistencies:
            if "心拍" in inconsistency:
                corrections.append("心拍数の描写を感情に適した範囲に調整してください")
            if "血圧" in inconsistency:
                corrections.append("血圧変化の描写を生理学的に適切な範囲に修正してください")

        return corrections[:5]

    def _evaluate_intensity_alignment(self, responses: list[dict], emotion: str | None,
                                    intensity: EmotionIntensity) -> dict[str, Any]:
        """感情強度との整合性評価

        Args:
            responses: 生理反応
            emotion: 感情タイプ
            intensity: 感情強度

        Returns:
            整合性評価結果
        """
        if not responses:
            return {"score": 50, "alignment": "評価不可能"}

        intensity_score = intensity.value  # 1-10
        aligned_responses = 0

        for response in responses:
            value = response.get("extracted_value")
            if value and emotion in self.emotion_physiology_map:
                response_type = response["type"]
                if response_type in self.emotion_physiology_map[emotion]:
                    normal_range = self.emotion_physiology_map[emotion][response_type]
                    expected_value = normal_range[0] + (normal_range[1] - normal_range[0]) * (intensity_score / 10)

                    # 期待値との差異が20%以内なら整合とみなす
                    if abs(value - expected_value) / expected_value <= 0.2:
                        aligned_responses += 1

        alignment_score = (aligned_responses / len(responses)) * 100

        return {
            "score": alignment_score,
            "aligned_count": aligned_responses,
            "total_responses": len(responses),
            "alignment": "良好" if alignment_score >= 70 else "要調整"
        }

    def _analyze_response_coverage(self, responses: list[dict]) -> dict[str, int]:
        """生理反応タイプ別カバレッジ分析

        Args:
            responses: 生理反応リスト

        Returns:
            タイプ別カウント
        """
        coverage = {}
        for response in responses:
            response_type = response["type"]
            coverage[response_type] = coverage.get(response_type, 0) + 1
        return coverage
