"""
品質チェックレベルを表現するValue Object

SPEC-STAGE5-SEPARATION対応
Claude Code品質チェック機能でのチェックレベル定義
"""

from dataclasses import dataclass
from enum import Enum


class QualityCheckLevel(Enum):
    """品質チェックのレベル定義"""

    BASIC = "basic"  # 基本的な整合性チェック
    STANDARD = "standard"  # 標準的な品質チェック
    COMPREHENSIVE = "comprehensive"  # 包括的な品質チェック
    CLAUDE_OPTIMIZED = "claude_optimized"  # Claude Code最適化チェック

    def get_check_criteria_count(self) -> int:
        """チェック基準数を取得"""
        criteria_counts = {
            QualityCheckLevel.BASIC: 5,
            QualityCheckLevel.STANDARD: 10,
            QualityCheckLevel.COMPREHENSIVE: 15,
            QualityCheckLevel.CLAUDE_OPTIMIZED: 12,
        }
        return criteria_counts[self]

    def get_estimated_duration_minutes(self) -> int:
        """推定実行時間（分）を取得"""
        duration_map = {
            QualityCheckLevel.BASIC: 5,
            QualityCheckLevel.STANDARD: 10,
            QualityCheckLevel.COMPREHENSIVE: 20,
            QualityCheckLevel.CLAUDE_OPTIMIZED: 15,
        }
        return duration_map[self]

    def is_claude_compatible(self) -> bool:
        """Claude Code互換性判定"""
        return self in [QualityCheckLevel.STANDARD, QualityCheckLevel.CLAUDE_OPTIMIZED]


@dataclass(frozen=True)
class QualityCheckRequest:
    """品質チェック要求を表現するValue Object"""

    episode_number: int
    project_name: str
    plot_file_path: str
    check_level: QualityCheckLevel

    def __post_init__(self) -> None:
        """初期化後のバリデーション"""
        if self.episode_number <= 0:
            msg = f"Episode number must be positive, got: {self.episode_number}"
            raise ValueError(msg)

        if not self.project_name.strip():
            msg = "Project name cannot be empty"
            raise ValueError(msg)

        if not self.plot_file_path.strip():
            msg = "Plot file path cannot be empty"
            raise ValueError(msg)

    def get_quality_focus_areas(self) -> list[str]:
        """品質チェック重点領域を取得"""
        base_areas = ["overall_consistency", "character_consistency", "plot_coherence"]

        if self.check_level == QualityCheckLevel.COMPREHENSIVE:
            base_areas.extend(["technical_accuracy", "emotional_depth", "narrative_flow", "reader_engagement"])
        elif self.check_level == QualityCheckLevel.CLAUDE_OPTIMIZED:
            base_areas.extend(["claude_readability", "prompt_optimization", "context_clarity"])

        return base_areas

    def should_include_examples(self) -> bool:
        """例文含有判定"""
        return self.check_level in [QualityCheckLevel.COMPREHENSIVE, QualityCheckLevel.CLAUDE_OPTIMIZED]

    def get_max_prompt_length(self) -> int:
        """最大プロンプト長を取得"""
        length_limits = {
            QualityCheckLevel.BASIC: 2000,
            QualityCheckLevel.STANDARD: 4000,
            QualityCheckLevel.COMPREHENSIVE: 8000,
            QualityCheckLevel.CLAUDE_OPTIMIZED: 6000,  # Claude Code制限を考慮
        }
        return length_limits[self.check_level]


@dataclass(frozen=True)
class QualityCriterion:
    """品質評価基準を表現するValue Object"""

    criterion_id: str
    name: str
    description: str
    weight: float
    check_method: str

    def __post_init__(self) -> None:
        """初期化後のバリデーション"""
        if not self.criterion_id.strip():
            msg = "Criterion ID cannot be empty"
            raise ValueError(msg)

        if not self.name.strip():
            msg = "Criterion name cannot be empty"
            raise ValueError(msg)

        if not 0.0 <= self.weight <= 1.0:
            msg = f"Weight must be between 0.0 and 1.0, got: {self.weight}"
            raise ValueError(msg)

        if not self.check_method.strip():
            msg = "Check method cannot be empty"
            raise ValueError(msg)

    def is_automated_check(self) -> bool:
        """自動チェック可能判定"""
        automated_methods = ["yaml_structure_check", "required_fields_check", "data_type_validation"]
        return self.check_method in automated_methods

    def requires_claude_analysis(self) -> bool:
        """Claude分析必要判定"""
        claude_methods = [
            "narrative_quality_assessment",
            "character_development_analysis",
            "emotional_depth_evaluation",
            "creative_coherence_check",
        ]
        return self.check_method in claude_methods


def get_standard_quality_criteria() -> list[QualityCriterion]:
    """標準品質評価基準を取得"""
    return [
        QualityCriterion(
            criterion_id="QC001",
            name="全体整合性",
            description="プロット全体の論理的整合性",
            weight=0.2,
            check_method="narrative_coherence_check",
        ),
        QualityCriterion(
            criterion_id="QC002",
            name="キャラクター一貫性",
            description="キャラクター設定・行動の一貫性",
            weight=0.15,
            check_method="character_consistency_check",
        ),
        QualityCriterion(
            criterion_id="QC003",
            name="感情アーク完成度",
            description="感情変化の自然さ・完成度",
            weight=0.15,
            check_method="emotional_arc_analysis",
        ),
        QualityCriterion(
            criterion_id="QC004",
            name="技術要素統合",
            description="技術要素の自然な統合度",
            weight=0.1,
            check_method="technical_integration_check",
        ),
        QualityCriterion(
            criterion_id="QC005",
            name="シーン構成",
            description="シーン構成の適切性",
            weight=0.1,
            check_method="scene_structure_analysis",
        ),
        QualityCriterion(
            criterion_id="QC006",
            name="伏線管理",
            description="伏線の適切な配置・管理",
            weight=0.1,
            check_method="foreshadowing_check",
        ),
        QualityCriterion(
            criterion_id="QC007",
            name="次話連携",
            description="次エピソードへの自然な連携",
            weight=0.1,
            check_method="episode_connection_check",
        ),
        QualityCriterion(
            criterion_id="QC008",
            name="制作指針準拠",
            description="制作指針への準拠度",
            weight=0.1,
            check_method="guideline_compliance_check",
        ),
    ]


def get_claude_optimized_criteria() -> list[QualityCriterion]:
    """Claude Code最適化品質評価基準を取得"""
    standard_criteria = get_standard_quality_criteria()

    # Claude特化の追加基準
    claude_specific = [
        QualityCriterion(
            criterion_id="CC001",
            name="Claude可読性",
            description="Claude Codeでの分析しやすさ",
            weight=0.08,
            check_method="claude_readability_check",
        ),
        QualityCriterion(
            criterion_id="CC002",
            name="コンテキスト明確性",
            description="文脈の明確さ・理解しやすさ",
            weight=0.07,
            check_method="context_clarity_check",
        ),
        QualityCriterion(
            criterion_id="CC003",
            name="構造化表現",
            description="構造化された表現の適切性",
            weight=0.05,
            check_method="structured_expression_check",
        ),
    ]

    # 重みの調整（標準基準を85%に削減してClaude特化分を追加）
    adjusted_standard = []
    for criterion in standard_criteria:
        adjusted_weight = criterion.weight * 0.85  # 15%削減してClaude特化分を追加
        adjusted_standard.append(
            QualityCriterion(
                criterion_id=criterion.criterion_id,
                name=criterion.name,
                description=criterion.description,
                weight=adjusted_weight,
                check_method=criterion.check_method,
            )
        )

    return adjusted_standard + claude_specific
