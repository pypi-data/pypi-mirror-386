#!/usr/bin/env python3
"""承認欲求システム関連のValue Objects

A38執筆プロンプトガイドSTEP1で定義される承認欲求追跡システムを実装。
「なろう系」特有の承認欲求の振幅（否定→肯定サイクル）を数値化・可視化する。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ApprovalType(Enum):
    """承認の種類"""

    RECOGNITION = "recognition"  # 認識・理解による承認
    RESPECT = "respect"  # 尊敬による承認
    GRATITUDE = "gratitude"  # 感謝による承認
    ADMIRATION = "admiration"  # 称賛による承認
    TRUST = "trust"  # 信頼による承認
    DEPENDENCE = "dependence"  # 依存による承認


class RejectionType(Enum):
    """拒絶・否定の種類"""

    DOUBT = "doubt"  # 疑念・不信
    DISMISSAL = "dismissal"  # 軽視・無視
    CRITICISM = "criticism"  # 批判・非難
    BETRAYAL = "betrayal"  # 裏切り・背信
    ABANDONMENT = "abandonment"  # 見捨て・放棄
    HOSTILITY = "hostility"  # 敌意・攻撃


@dataclass(frozen=True)
class ApprovalLevel:
    """承認レベル（1-10の数値化）

    Attributes:
        level: 承認度レベル（1=完全拒絶、10=絶対的承認）
        quality: 承認の質的評価
        source: 承認の源泉（誰から）
        context: 承認の文脈・理由
    """

    level: int
    quality: ApprovalType
    source: str
    context: str = ""

    def __post_init__(self) -> None:
        """バリデーション"""
        if not 1 <= self.level <= 10:
            msg = f"ApprovalLevel must be 1-10, got {self.level}"
            raise ValueError(msg)

    @classmethod
    def create_rejection(
        cls, level: int, rejection_type: RejectionType, source: str, context: str = ""
    ) -> "ApprovalLevel":
        """拒絶・否定レベルを作成（レベル1-4）

        Args:
            level: 拒絶度（1=絶対的拒絶、4=軽い否定）
            rejection_type: 拒絶の種類
            source: 拒絶の源泉
            context: 拒絶の文脈

        Returns:
            拒絶を表すApprovalLevel
        """
        if not 1 <= level <= 4:
            msg = f"Rejection level must be 1-4, got {level}"
            raise ValueError(msg)

        # 拒絶タイプを承認タイプにマッピング（逆転表現）
        rejection_to_approval = {
            RejectionType.DOUBT: ApprovalType.TRUST,
            RejectionType.DISMISSAL: ApprovalType.RECOGNITION,
            RejectionType.CRITICISM: ApprovalType.RESPECT,
            RejectionType.BETRAYAL: ApprovalType.TRUST,
            RejectionType.ABANDONMENT: ApprovalType.DEPENDENCE,
            RejectionType.HOSTILITY: ApprovalType.ADMIRATION,
        }

        return cls(
            level=level,
            quality=rejection_to_approval[rejection_type],
            source=source,
            context=f"拒絶:{rejection_type.value} - {context}",
        )

    def is_rejection(self) -> bool:
        """拒絶レベルかどうか判定"""
        return self.level <= 4

    def is_approval(self) -> bool:
        """承認レベルかどうか判定"""
        return self.level >= 7

    def is_neutral(self) -> bool:
        """中立レベルかどうか判定"""
        return 5 <= self.level <= 6

    def export_to_yaml_dict(self) -> dict[str, Any]:
        """YAML出力用の辞書を生成

        conversation_design_service.py:313で呼び出される統合エクスポート用メソッド

        Returns:
            YAML出力可能な辞書データ
        """
        return {
            "level": self.level,
            "quality": self.quality.value,
            "source": self.source,
            "context": self.context,
            "interpretation": {
                "is_rejection": self.is_rejection(),
                "is_approval": self.is_approval(),
                "is_neutral": self.is_neutral(),
                "description": self._get_level_description(),
            },
        }

    def _get_level_description(self) -> str:
        """レベルに応じた説明文を生成"""
        descriptions = {
            1: "絶対的拒絶・完全否定",
            2: "強い拒絶・否定",
            3: "強い拒絶・否定",
            4: "軽い否定・疑問",
            5: "中立・どちらでもない",
            6: "中立・どちらでもない",
            7: "承認・肯定的",
            8: "承認・肯定的",
            9: "強い承認・高評価",
            10: "絶対的承認・完全肯定",
        }
        return descriptions.get(self.level, "未定義レベル")


@dataclass
class ApprovalAmplitude:
    """承認の振幅（否定→肯定の変化幅）

    Attributes:
        valley: 最低谷（否定・拒絶の最低点）
        peak: 最高峰（承認・称賛の最高点）
        amplitude: 振幅（peak.level - valley.level）
        transition_points: 転換点のリスト
    """

    valley: ApprovalLevel
    peak: ApprovalLevel
    transition_points: list[ApprovalLevel] = field(default_factory=list)

    @property
    def amplitude(self) -> int:
        """振幅を計算"""
        return self.peak.level - self.valley.level

    @property
    def impact_score(self) -> float:
        """インパクトスコア（読者感情効果の予想値）

        Returns:
            0.0-10.0のスコア（振幅と質的要素を総合評価）
        """
        # 基本振幅スコア
        amplitude_score = self.amplitude * 1.0

        # 質的ボーナス
        quality_bonus = 0.0
        if self.valley.level <= 2 and self.peak.level >= 8:
            quality_bonus += 2.0  # 極端な変化にボーナス

        if len(self.transition_points) >= 2:
            quality_bonus += 1.0  # 段階的変化にボーナス

        # 源泉の多様性ボーナス
        sources = {self.valley.source, self.peak.source}
        sources.update(tp.source for tp in self.transition_points)
        if len(sources) >= 3:
            quality_bonus += 0.5  # 多様な承認源にボーナス

        return min(10.0, amplitude_score + quality_bonus)

    def add_transition_point(self, approval_level: ApprovalLevel) -> None:
        """転換点を追加（時系列順に維持）"""
        self.transition_points.append(approval_level)
        self.transition_points.sort(key=lambda x: x.level)


@dataclass
class ApprovalCycle:
    """否定→肯定サイクル（STEP2で使用）

    各フェーズでの「拒絶・失敗」から「小さな承認」への転換を管理
    """

    phase_name: str
    cycle_type: str  # "rejection_to_acceptance", "failure_to_success", "doubt_to_trust"

    # サイクルの構成要素
    initial_state: ApprovalLevel  # 初期状態（通常は否定的）
    crisis_point: ApprovalLevel  # 危機点（最も否定的）
    breakthrough: ApprovalLevel  # 突破点（転換の瞬間）
    resolution: ApprovalLevel  # 解決点（小さな承認）

    # メタ情報
    duration: str = "short"  # "short", "medium", "long"
    intensity: str = "low"  # "low", "medium", "high"
    reader_effect: str = ""  # 読者への期待効果

    @property
    def cycle_amplitude(self) -> ApprovalAmplitude:
        """このサイクルの承認振幅を取得"""
        return ApprovalAmplitude(
            valley=self.crisis_point, peak=self.resolution, transition_points=[self.initial_state, self.breakthrough]
        )

    def validate_cycle(self) -> bool:
        """サイクルの妥当性を検証

        Returns:
            正しい否定→肯定の流れになっているか
        """
        levels = [self.initial_state.level, self.crisis_point.level, self.breakthrough.level, self.resolution.level]

        # 危機点が最も低く、解決点が最も高い必要がある
        return (
            self.crisis_point.level == min(levels)
            and self.resolution.level == max(levels)
            and self.resolution.level > self.initial_state.level  # 成長の確認
        )


@dataclass
class EpisodeApprovalSystem:
    """エピソード全体の承認欲求システム

    STEP1で定義される承認欲求レベル、承認獲得度、承認の振幅を統合管理
    """

    episode_number: int

    # STEP1基本要素
    initial_desire_level: int  # 承認欲求レベル（1-10）
    final_acquisition: ApprovalLevel  # 承認獲得度（質と量）
    main_amplitude: ApprovalAmplitude  # 承認の振幅（メイン）

    # STEP2フェーズ別サイクル
    phase_cycles: list[ApprovalCycle] = field(default_factory=list)

    # 補助データ
    secondary_amplitudes: list[ApprovalAmplitude] = field(default_factory=list)
    key_approval_sources: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """初期化後のバリデーション"""
        if not 1 <= self.initial_desire_level <= 10:
            msg = f"Desire level must be 1-10, got {self.initial_desire_level}"
            raise ValueError(msg)

    def add_phase_cycle(self, cycle: ApprovalCycle) -> None:
        """フェーズサイクルを追加"""
        if not cycle.validate_cycle():
            msg = f"Invalid approval cycle for phase {cycle.phase_name}"
            raise ValueError(msg)

        self.phase_cycles.append(cycle)
        self.key_approval_sources.add(cycle.resolution.source)

    def calculate_total_growth(self) -> int:
        """総合成長度を計算

        Returns:
            初期欲求レベルから最終獲得レベルまでの成長幅
        """
        return self.final_acquisition.level - self.initial_desire_level

    def get_reader_satisfaction_score(self) -> float:
        """読者満足度スコア（予測値）

        Returns:
            0.0-10.0のスコア
        """
        # メイン振幅のインパクト
        main_impact = self.main_amplitude.impact_score * 0.6

        # フェーズサイクルの貢献
        cycle_impact = sum(cycle.cycle_amplitude.impact_score for cycle in self.phase_cycles) * 0.2

        # 成長幅ボーナス
        growth_bonus = min(3.0, self.calculate_total_growth() * 0.3)

        # 承認源の多様性ボーナス
        diversity_bonus = min(2.0, len(self.key_approval_sources) * 0.4)

        return min(10.0, main_impact + cycle_impact + growth_bonus + diversity_bonus)

    def export_to_yaml_dict(self) -> dict[str, Any]:
        """YAML出力用の辞書に変換"""
        return {
            "episode_number": self.episode_number,
            "approval_system": {
                "initial_desire_level": self.initial_desire_level,
                "final_acquisition": {
                    "level": self.final_acquisition.level,
                    "quality": self.final_acquisition.quality.value,
                    "source": self.final_acquisition.source,
                    "context": self.final_acquisition.context,
                },
                "main_amplitude": {
                    "valley": {
                        "level": self.main_amplitude.valley.level,
                        "quality": self.main_amplitude.valley.quality.value,
                        "source": self.main_amplitude.valley.source,
                        "context": self.main_amplitude.valley.context,
                    },
                    "peak": {
                        "level": self.main_amplitude.peak.level,
                        "quality": self.main_amplitude.peak.quality.value,
                        "source": self.main_amplitude.peak.source,
                        "context": self.main_amplitude.peak.context,
                    },
                    "amplitude": self.main_amplitude.amplitude,
                    "impact_score": self.main_amplitude.impact_score,
                },
                "phase_cycles": [
                    {
                        "phase_name": cycle.phase_name,
                        "cycle_type": cycle.cycle_type,
                        "initial_level": cycle.initial_state.level,
                        "crisis_level": cycle.crisis_point.level,
                        "breakthrough_level": cycle.breakthrough.level,
                        "resolution_level": cycle.resolution.level,
                        "cycle_amplitude": cycle.cycle_amplitude.amplitude,
                        "duration": cycle.duration,
                        "intensity": cycle.intensity,
                        "reader_effect": cycle.reader_effect,
                    }
                    for cycle in self.phase_cycles
                ],
                "metrics": {
                    "total_growth": self.calculate_total_growth(),
                    "reader_satisfaction_score": self.get_reader_satisfaction_score(),
                    "approval_sources_count": len(self.key_approval_sources),
                    "approval_sources": list(self.key_approval_sources),
                },
            },
        }
