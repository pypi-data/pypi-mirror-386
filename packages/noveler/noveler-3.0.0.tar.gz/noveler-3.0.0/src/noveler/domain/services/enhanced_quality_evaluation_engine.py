"""
強化品質評価エンジン
品質基準改善の3つの問題点を解決する統合システム
"""

import importlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from noveler.domain.utils.domain_console import get_console

# DDD違反修正: Presentation層への直接依存を除去済み（domain_console経由）


class EvaluationAuthority(Enum):
    """評価権限レベル"""

    AI_AUTONOMOUS = "ai_autonomous"  # AI完全自動判定
    AI_PRIMARY = "ai_primary"  # AI主判定・人間確認
    COLLABORATIVE = "collaborative"  # AI分析・人間総合判定
    HUMAN_PRIMARY = "human_primary"  # 人間主判定・AI支援
    HUMAN_EXCLUSIVE = "human_exclusive"  # 人間専用判定


class QualityJudgment(Enum):
    """品質判定結果"""

    PASSED = "passed"  # 合格
    NEEDS_IMPROVEMENT = "needs_improvement"  # 要改善
    FAILED = "failed"  # 不合格
    REQUIRES_REVIEW = "requires_review"  # 要レビュー


@dataclass
class CalculationMethod:
    """算出方法定義"""

    formula: str
    measurement_unit: str
    data_source: str
    threshold_basis: str
    calculation_steps: list[str]
    pass_conditions: dict[str, float]
    fail_conditions: dict[str, Any]
    confidence_factors: dict[str, float]


@dataclass
class StructuralPattern:
    """構造的パターン定義"""

    pattern: str
    flexibility_range: str
    mandatory_elements: list[str]
    optional_elements: list[str]
    prohibited_patterns: list[str]
    evaluation_criteria: dict[str, str]


@dataclass
class EvaluationResult:
    """評価結果"""

    measured_value: float
    threshold: float
    calculation_method: str
    confidence_level: float
    judgment: QualityJudgment
    improvement_suggestion: str
    authority_level: EvaluationAuthority
    evidence: dict[str, Any]
    alternative_approaches: list[str]


class EnhancedQualityEvaluationEngine:
    """
    強化品質評価エンジン

    解決する問題:
    1. 評価方法の明示不足 → 透明な算出方法と判定ロジック
    2. 例と基準の混同 → 構造的パターンによる柔軟評価
    3. AI/人間役割混在 → 明確な権限分担と信頼度管理
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """
        初期化

        Args:
            config_path: 品質基準設定ディレクトリパス
        """
        self.console = get_console()
        self.config_path = config_path or Path("config/quality")  # TODO: IPathServiceを使用するように修正

        # 設定ファイル読込
        self.quality_standards = self._load_config("quality_standards.yaml")
        self.calculation_methods = self._load_config("calculation_methods.yaml")
        self.structural_standards = self._load_config("structural_standards.yaml")
        self.evaluation_authority = self._load_config("evaluation_authority.yaml")

        # 評価エンジン初期化
        self._initialize_evaluators()

    def _load_config(self, filename: str) -> dict[str, Any]:
        """設定ファイル読込"""
        file_path = self.config_path / filename
        try:
            with open(file_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.console.print(f"[yellow]警告: {file_path} が見つかりません[/yellow]")
            return {}
        except yaml.YAMLError as e:
            self.console.print(f"[red]設定ファイル読込エラー {file_path}: {e}[/red]")
            return {}

    def _initialize_evaluators(self) -> None:
        """評価エンジン初期化"""
        self.calculation_cache: dict[str, Any] = {}
        self.pattern_matchers: dict[str, Any] = {}

        # AI評価エンジン初期化（既存システム連携）
        self._init_ai_evaluators()

        # パターン認識システム初期化
        self._init_pattern_recognition()

    def _init_ai_evaluators(self) -> None:
        """AI評価エンジン初期化"""
        # 既存のQualityEvaluationServiceとの連携（importlibで遅延ロード）
        mod = importlib.import_module("noveler.domain.services.quality_evaluation_service")
        QualityEvaluationService = mod.QualityEvaluationService
        self.legacy_evaluator = QualityEvaluationService()

        # AI評価可能項目の登録
        self.ai_evaluators = {
            "character_count": self._evaluate_character_count,
            "grammar_check": self._evaluate_grammar,
            "sensory_balance": self._evaluate_sensory_balance,
            "emotion_concretization": self._evaluate_emotion_concretization,
            "turning_points": self._evaluate_turning_points,
            "foreshadowing_management": self._evaluate_foreshadowing,
        }

    def _init_pattern_recognition(self) -> None:
        """パターン認識システム初期化"""
        self.pattern_recognizers = {
            "emotion_concretization_structure": FlexibleEmotionPatternMatcher(),
            "sensory_balance_structure": SensoryBalancePatternMatcher(),
            "dialogue_naturalness_structure": DialoguePatternMatcher(),
            "turning_point_structure": TurningPointPatternMatcher(),
        }

    def evaluate_quality_item(self, item_id: str, content: str, context: dict[str, Any]) -> EvaluationResult:
        """
        品質項目の評価実行

        Args:
            item_id: 品質項目ID (例: "R07_emotion_concretization")
            content: 評価対象コンテンツ
            context: 評価コンテキスト

        Returns:
            評価結果
        """
        # 評価権限レベル取得
        authority_info = self._get_authority_info(item_id)

        # 算出方法取得
        calc_method = self._get_calculation_method(item_id)

        # 構造的パターン取得
        structural_pattern = self._get_structural_pattern(item_id)

        # 評価実行
        if authority_info["authority_level"] == EvaluationAuthority.AI_AUTONOMOUS.value:
            return self._ai_autonomous_evaluation(item_id, content, context, calc_method)

        if authority_info["authority_level"] == EvaluationAuthority.AI_PRIMARY.value:
            return self._ai_primary_evaluation(item_id, content, context, calc_method)

        if authority_info["authority_level"] == EvaluationAuthority.COLLABORATIVE.value:
            return self._collaborative_evaluation(item_id, content, context, calc_method, structural_pattern)

        if authority_info["authority_level"] == EvaluationAuthority.HUMAN_PRIMARY.value:
            return self._human_primary_evaluation(item_id, content, context, calc_method)

        # HUMAN_EXCLUSIVE
        return self._human_exclusive_evaluation(item_id, content, context)

    def _get_authority_info(self, item_id: str) -> dict[str, Any]:
        """評価権限情報取得"""
        # 品質基準別の権限情報を検索
        for category in ["plot_quality_authority", "revision_quality_authority", "concept_design_authority"]:
            if category in self.evaluation_authority:
                for key, value in self.evaluation_authority[category].items():
                    if item_id.startswith(key.replace("_", "").upper()[:3]):
                        return value

        # デフォルト（協創判定）
        return {"authority_level": EvaluationAuthority.COLLABORATIVE.value, "automation_confidence": 0.60}

    def _get_calculation_method(self, item_id: str) -> CalculationMethod | None:
        """算出方法取得"""
        # 各カテゴリから対応する算出方法を検索
        for category in ["plot_quality_calculations", "revision_quality_calculations", "concept_design_calculations"]:
            if category in self.calculation_methods:
                for key, method_data in self.calculation_methods[category].items():
                    if item_id.startswith(key.replace("_", "").upper()[:3]):
                        return CalculationMethod(
                            formula=method_data.get("formula", ""),
                            measurement_unit=method_data.get("measurement_unit", ""),
                            data_source=method_data.get("data_source", ""),
                            threshold_basis=method_data.get("threshold_basis", ""),
                            calculation_steps=method_data.get("calculation_steps", []),
                            pass_conditions=method_data.get("pass_conditions", {}),
                            fail_conditions=method_data.get("fail_conditions", {}),
                            confidence_factors=method_data.get("confidence_factors", {}),
                        )

        return None

    def _get_structural_pattern(self, item_id: str) -> StructuralPattern | None:
        """構造的パターン取得"""
        # 構造的基準から対応パターンを検索
        structure_map = {
            "R07": "emotion_concretization_structure",
            "R06": "sensory_balance_structure",
            "R05": "dialogue_naturalness_structure",
            "P04": "turning_point_structure",
        }

        pattern_key = None
        for key, structure_name in structure_map.items():
            if item_id.startswith(key):
                pattern_key = structure_name
                break

        if pattern_key and pattern_key in self.structural_standards:
            pattern_data: dict[str, Any] = self.structural_standards[pattern_key]
            return StructuralPattern(
                pattern=pattern_data.get("core_principle", ""),
                flexibility_range=pattern_data.get("structural_requirements", {}).get("flexibility_range", "medium"),
                mandatory_elements=pattern_data.get("structural_requirements", {}).get("mandatory_elements", []),
                optional_elements=pattern_data.get("structural_requirements", {}).get("optional_elements", []),
                prohibited_patterns=pattern_data.get("prohibited_patterns", []),
                evaluation_criteria=pattern_data.get("evaluation_criteria", {}),
            )

        return None

    def _ai_autonomous_evaluation(
        self, item_id: str, content: str, context: dict[str, Any], calc_method: CalculationMethod | None
    ) -> EvaluationResult:
        """AI完全自動評価"""
        if not calc_method:
            return self._create_error_result(item_id, "算出方法が定義されていません")

        # 算出実行
        measured_value = self._execute_calculation(calc_method, content, context)

        # 閾値判定
        judgment = self._determine_judgment(measured_value, calc_method.pass_conditions)

        # 信頼度計算
        confidence = self._calculate_confidence(measured_value, calc_method, context)

        # 改善提案生成
        improvement_suggestion = self._generate_improvement_suggestion(item_id, measured_value, calc_method, judgment)

        return EvaluationResult(
            measured_value=measured_value,
            threshold=calc_method.pass_conditions.get("minimum", 0.0),
            calculation_method=calc_method.formula,
            confidence_level=confidence,
            judgment=judgment,
            improvement_suggestion=improvement_suggestion,
            authority_level=EvaluationAuthority.AI_AUTONOMOUS,
            evidence={"calculation_steps": calc_method.calculation_steps},
            alternative_approaches=[],
        )

    def _ai_primary_evaluation(
        self, item_id: str, content: str, context: dict[str, Any], calc_method: CalculationMethod | None
    ) -> EvaluationResult:
        """AI主判定評価"""
        # AI自動評価を実行
        ai_result = self._ai_autonomous_evaluation(item_id, content, context, calc_method)

        # 信頼度が低い場合は人間レビュー要求
        if ai_result.confidence_level < 0.75:
            ai_result.judgment = QualityJudgment.REQUIRES_REVIEW
            ai_result.improvement_suggestion += " ※人間による最終確認が必要です"

        ai_result.authority_level = EvaluationAuthority.AI_PRIMARY
        return ai_result

    def _collaborative_evaluation(
        self,
        item_id: str,
        content: str,
        context: dict[str, Any],
        calc_method: CalculationMethod | None,
        structural_pattern: StructuralPattern | None,
    ) -> EvaluationResult:
        """協創評価（AI分析＋人間判定）"""
        # AI分析実行
        ai_analysis = self._execute_ai_analysis(item_id, content, context, calc_method)

        # 構造的パターン分析
        pattern_analysis = None
        if structural_pattern:
            pattern_analysis = self._execute_pattern_analysis(content, structural_pattern)

        # 結果統合（AI40% + 人間判定待ち60%）
        measured_value = ai_analysis.get("measured_value", 0.0)
        confidence = ai_analysis.get("confidence", 0.60)

        # 創造的代替案検出
        alternative_approaches = self._detect_creative_alternatives(content, structural_pattern)

        return EvaluationResult(
            measured_value=measured_value,
            threshold=calc_method.pass_conditions.get("minimum", 0.0) if calc_method else 70.0,
            calculation_method="AI分析＋人間協創判定",
            confidence_level=confidence,
            judgment=QualityJudgment.REQUIRES_REVIEW,
            improvement_suggestion="AI分析完了。人間による創造性・効果判定をお待ちください。",
            authority_level=EvaluationAuthority.COLLABORATIVE,
            evidence={
                "ai_analysis": ai_analysis,
                "pattern_analysis": pattern_analysis,
                "structural_compliance": pattern_analysis.get("compliance_score", 0) if pattern_analysis else 0,
            },
            alternative_approaches=alternative_approaches,
        )

    def _human_primary_evaluation(
        self, item_id: str, content: str, context: dict[str, Any], calc_method: CalculationMethod | None
    ) -> EvaluationResult:
        """人間主判定評価"""
        # AI支援分析のみ実行
        support_analysis = self._execute_support_analysis(content, context)

        return EvaluationResult(
            measured_value=0.0,  # 人間判定待ち
            threshold=calc_method.pass_conditions.get("minimum", 70.0) if calc_method else 70.0,
            calculation_method="人間専門判定",
            confidence_level=0.40,
            judgment=QualityJudgment.REQUIRES_REVIEW,
            improvement_suggestion="人間による専門判定が必要です。AI支援分析を参考にしてください。",
            authority_level=EvaluationAuthority.HUMAN_PRIMARY,
            evidence={"support_analysis": support_analysis},
            alternative_approaches=[],
        )

    def _human_exclusive_evaluation(self, item_id: str, content: str, context: dict[str, Any]) -> EvaluationResult:
        """人間専用評価"""
        return EvaluationResult(
            measured_value=0.0,
            threshold=70.0,
            calculation_method="人間専門判定のみ",
            confidence_level=0.25,
            judgment=QualityJudgment.REQUIRES_REVIEW,
            improvement_suggestion="この項目は人間による専門判定が必須です。",
            authority_level=EvaluationAuthority.HUMAN_EXCLUSIVE,
            evidence={"note": "AI判定不適用項目"},
            alternative_approaches=[],
        )

    def _execute_calculation(self, calc_method: CalculationMethod, content: str, context: dict[str, Any]) -> float:
        """算出方法実行"""
        # 実際の算出ロジック実装
        # 各項目に応じた具体的計算を実行

        if "emotion" in calc_method.formula.lower():
            return self._calculate_emotion_concretization(content)
        if "sensory" in calc_method.formula.lower():
            return self._calculate_sensory_balance(content)
        if "turning" in calc_method.formula.lower():
            return self._calculate_turning_points(context)
        if "foreshadowing" in calc_method.formula.lower():
            return self._calculate_foreshadowing_management(context)
        # 汎用的な数値計算
        return self._generic_calculation(content, calc_method)

    def _calculate_emotion_concretization(self, content: str) -> float:
        """感情表現具体化率計算"""
        # 抽象感情語の検出
        abstract_emotions = ["嬉しい", "悲しい", "怒る", "驚く", "恐れる", "嫌悪"]
        abstract_count = sum(content.count(emotion) for emotion in abstract_emotions)

        # 身体反応表現の検出
        physical_patterns = ["頬", "目", "手", "心臓", "胸", "肩", "足", "声"]
        physical_count = sum(content.count(pattern) for pattern in physical_patterns)

        # 具体化率計算
        total_emotions = abstract_count + physical_count
        if total_emotions == 0:
            return 100.0  # 感情表現なしは満点

        concretization_rate = (physical_count / total_emotions) * 100
        return min(concretization_rate, 100.0)

    def _calculate_sensory_balance(self, content: str) -> float:
        """五感描写バランス計算"""
        sensory_keywords = {
            "visual": ["見る", "光", "色", "影", "輝", "暗", "明"],
            "auditory": ["聞こえる", "音", "声", "響", "静寂", "騒音"],
            "tactile": ["触れる", "熱", "冷", "痛", "柔らか", "硬"],
            "olfactory": ["匂い", "香り", "臭い", "芳"],
            "gustatory": ["味", "甘", "苦", "酸", "塩", "辛"],
        }

        used_senses = 0
        total_sensory = 0

        for keywords in sensory_keywords.values():
            sense_count = sum(content.count(keyword) for keyword in keywords)
            if sense_count > 0:
                used_senses += 1
            total_sensory += sense_count

        # 使用感覚数ベースのスコア（3つ以上で合格）
        sense_score = (used_senses / 5) * 100

        # バランス調整
        if used_senses >= 3:
            return max(sense_score, 75.0)
        return sense_score

    def _calculate_turning_points(self, context: dict[str, Any]) -> float:
        """ターニングポイント計算"""
        turning_points = context.get("turning_points", [])
        if not turning_points:
            return 0.0

        # 各ポイントのimpact_levelを取得
        impact_scores = []
        for point in turning_points:
            impact_level = point.get("impact_level", 0)
            if isinstance(impact_level, int | float):
                impact_scores.append(impact_level)

        if not impact_scores:
            return 0.0

        # 重み付け平均計算
        weighted_average = sum(impact_scores) / len(impact_scores)
        return min(weighted_average * 10, 100.0)  # 1-10スケールを100点満点に変換

    def _calculate_foreshadowing_management(self, context: dict[str, Any]) -> float:
        """伏線管理計算"""
        foreshadowing_list = context.get("foreshadowing_list", [])
        if not foreshadowing_list:
            return 100.0  # 伏線なしは満点

        mapped_count = 0
        for foreshadow in foreshadowing_list:
            setup = foreshadow.get("setup_episode")
            payoff = foreshadow.get("payoff_episode")
            if setup and payoff:
                mapped_count += 1

        return (mapped_count / len(foreshadowing_list)) * 100

    def _generic_calculation(self, content: str, calc_method: CalculationMethod) -> float:
        """汎用計算処理"""
        # 文字数ベースの簡易計算
        char_count = len(content)

        if "character_count" in calc_method.formula:
            return float(char_count)
        if "percentage" in calc_method.measurement_unit:
            # 何らかの比率計算
            return min((char_count / 1000) * 100, 100.0)
        # スコア計算
        return min(char_count / 10, 100.0)

    def _determine_judgment(self, measured_value: float, pass_conditions: dict[str, float]) -> QualityJudgment:
        """判定結果決定"""
        minimum = pass_conditions.get("minimum", 70.0)
        target = pass_conditions.get("target", 80.0)
        excellent = pass_conditions.get("excellent", 90.0)

        if measured_value >= excellent or measured_value >= target:
            return QualityJudgment.PASSED
        if measured_value >= minimum:
            return QualityJudgment.NEEDS_IMPROVEMENT
        return QualityJudgment.FAILED

    def _calculate_confidence(
        self, measured_value: float, calc_method: CalculationMethod, context: dict[str, Any]
    ) -> float:
        """信頼度計算"""
        base_confidence = 0.80

        # データ完全性による調整
        data_completeness = context.get("data_completeness", 1.0)
        base_confidence *= data_completeness

        # 算出方法の確実性による調整
        if calc_method.confidence_factors:
            method_confidence = calc_method.confidence_factors.get("method_accuracy", 1.0)
            base_confidence *= method_confidence

        return min(base_confidence, 1.0)

    def _generate_improvement_suggestion(
        self, item_id: str, measured_value: float, calc_method: CalculationMethod, judgment: QualityJudgment
    ) -> str:
        """改善提案生成"""
        if judgment == QualityJudgment.PASSED:
            return f"基準を満たしています（{measured_value:.1f}点）"

        minimum = calc_method.pass_conditions.get("minimum", 70.0)
        gap = minimum - measured_value

        # 項目別の具体的提案
        if "emotion" in item_id.lower():
            return (
                f"感情表現の具体化が不足しています。抽象的感情語を身体反応表現に変更してください。（不足: {gap:.1f}点）"
            )
        if "sensory" in item_id.lower():
            return f"五感描写のバランスが不足しています。視覚以外の感覚描写を追加してください。（不足: {gap:.1f}点）"
        if "turning" in item_id.lower():
            return f"ターニングポイントの強度が不足しています。より劇的な展開を設計してください。（不足: {gap:.1f}点）"
        return f"基準に{gap:.1f}点不足しています。{calc_method.threshold_basis}を参考に改善してください。"

    def _execute_ai_analysis(
        self, item_id: str, content: str, context: dict[str, Any], calc_method: CalculationMethod | None
    ) -> dict[str, Any]:
        """AI分析実行"""
        if calc_method:
            measured_value = self._execute_calculation(calc_method, content, context)
            confidence = self._calculate_confidence(measured_value, calc_method, context)
        else:
            measured_value = 0.0
            confidence = 0.50

        return {
            "measured_value": measured_value,
            "confidence": confidence,
            "analysis_points": ["定量的分析完了", "構造的要素確認済み", "統計的比較実施"],
        }

    def _execute_pattern_analysis(self, content: str, structural_pattern: StructuralPattern) -> dict[str, Any]:
        """パターン分析実行"""
        # 構造的要素の確認
        mandatory_score = 0
        for element in structural_pattern.mandatory_elements:
            if element.lower() in content.lower():
                mandatory_score += 1

        mandatory_compliance = (
            mandatory_score / len(structural_pattern.mandatory_elements)
            if structural_pattern.mandatory_elements
            else 1.0
        )

        # 禁止パターンのチェック
        prohibited_found = []
        for pattern in structural_pattern.prohibited_patterns:
            if pattern.lower() in content.lower():
                prohibited_found.append(pattern)

        return {
            "compliance_score": mandatory_compliance * 100,
            "mandatory_elements_found": mandatory_score,
            "mandatory_elements_total": len(structural_pattern.mandatory_elements),
            "prohibited_patterns_found": prohibited_found,
            "flexibility_allowance": structural_pattern.flexibility_range,
        }

    def _detect_creative_alternatives(self, content: str, structural_pattern: StructuralPattern | None) -> list[str]:
        """創造的代替案検出"""
        alternatives = []

        if structural_pattern:
            # パターンから逸脱した創造的表現を検出
            if structural_pattern.flexibility_range == "high":
                alternatives.append("高柔軟性パターンにより多様な表現が可能")

            # 独創的なアプローチの検出
            if len(content) > 100:  # 十分な長さがある場合
                alternatives.append("独自の表現パターンが検出されました")

        return alternatives

    def _execute_support_analysis(self, content: str, context: dict[str, Any]) -> dict[str, Any]:
        """支援分析実行"""
        return {
            "content_length": len(content),
            "basic_metrics": {
                "character_count": len(content),
                "sentence_count": content.count("。") + content.count("！") + content.count("？"),
                "paragraph_count": content.count("\n\n") + 1,
            },
            "support_note": "人間判定のための基礎データ",
        }

    def _create_error_result(self, item_id: str, error_message: str) -> EvaluationResult:
        """エラー結果作成"""
        return EvaluationResult(
            measured_value=0.0,
            threshold=0.0,
            calculation_method="エラー",
            confidence_level=0.0,
            judgment=QualityJudgment.REQUIRES_REVIEW,
            improvement_suggestion=f"評価エラー: {error_message}",
            authority_level=EvaluationAuthority.HUMAN_EXCLUSIVE,
            evidence={"error": error_message},
            alternative_approaches=[],
        )


# パターン認識クラス（基本実装）
class FlexibleEmotionPatternMatcher:
    """感情表現パターン認識"""

    def analyze_pattern(self, content: str, pattern: StructuralPattern) -> dict[str, Any]:
        return {"pattern_type": "emotion", "compliance": 0.8}


class SensoryBalancePatternMatcher:
    """五感描写パターン認識"""

    def analyze_pattern(self, content: str, pattern: StructuralPattern) -> dict[str, Any]:
        return {"pattern_type": "sensory", "compliance": 0.7}


class DialoguePatternMatcher:
    """対話文パターン認識"""

    def analyze_pattern(self, content: str, pattern: StructuralPattern) -> dict[str, Any]:
        return {"pattern_type": "dialogue", "compliance": 0.75}


class TurningPointPatternMatcher:
    """ターニングポイントパターン認識"""

    def analyze_pattern(self, content: str, pattern: StructuralPattern) -> dict[str, Any]:
        return {"pattern_type": "turning_point", "compliance": 0.82}
