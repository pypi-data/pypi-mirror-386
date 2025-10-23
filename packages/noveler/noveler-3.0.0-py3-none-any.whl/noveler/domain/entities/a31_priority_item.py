#!/usr/bin/env python3
"""A31重点項目エンティティ

A31チェックリストから抽出された重点項目を管理し、
Claude Code分析への適用可能性を評価するドメインエンティティ。
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from noveler.domain.value_objects.a31_evaluation_category import A31EvaluationCategory


class A31CheckPhase(Enum):
    """A31チェックフェーズ列挙型"""

    PHASE0_AUTO_START = "Phase0_自動執筆開始"
    PHASE1_PLANNING = "Phase1_設計・下書き段階"
    PHASE2_WRITING = "Phase2_執筆段階"
    PHASE3_REVISION = "Phase3_推敲段階"
    PHASE4_QUALITY_CHECK = "Phase4_品質チェック段階"
    PHASE5_COMPLETION = "Phase5_完成処理段階"
    FINAL_CONFIRMATION = "公開前最終確認"

    # A41推敲チェックリスト対応
    STAGE1_TECHNICAL = "Stage1_技術的推敲段階"
    STAGE2_CONTENT = "Stage2_内容的推敲段階"
    STAGE3_READER_OPTIMIZATION = "Stage3_読者体験最適化段階"

    def get_priority_weight(self) -> float:
        """フェーズ別優先度重みを返す"""
        weights = {
            self.PHASE2_WRITING: 0.9,
            self.STAGE2_CONTENT: 0.9,
            self.PHASE3_REVISION: 0.8,
            self.STAGE1_TECHNICAL: 0.8,
            self.STAGE3_READER_OPTIMIZATION: 0.7,
            self.PHASE4_QUALITY_CHECK: 0.7,
            self.PHASE1_PLANNING: 0.6,
            self.PHASE5_COMPLETION: 0.5,
            self.PHASE0_AUTO_START: 0.4,
            self.FINAL_CONFIRMATION: 0.3,
        }
        return weights.get(self, 0.5)

    def get_display_name(self) -> str:
        """表示用フェーズ名を返す"""
        return self.value.replace("_", " ")


class ClaudeAnalysisSuitability(Enum):
    """Claude分析適性レベル"""

    HIGH = "high"  # 高適性：バランス・描写・リズム分析
    MEDIUM = "medium"  # 中適性：構造・統一性チェック
    LOW = "low"  # 低適性：手動確認が適切
    UNSUITABLE = "unsuitable"  # 不適：コマンド実行等

    def is_suitable(self) -> bool:
        """Claude分析に適しているかを判定"""
        return self in [self.HIGH, self.MEDIUM]


@dataclass(frozen=True)
class PriorityItemId:
    """優先度項目ID バリューオブジェクト"""

    value: str

    def __post_init__(self) -> None:
        """ID妥当性検証"""
        if not self.value or not self.value.strip():
            msg = "優先度項目IDは空にできません"
            raise ValueError(msg)

        # A31-XXX または A41-XXX 形式の検証
        if not re.match(r"^A\d{2}-\d{3}$", self.value):
            msg = f"無効な優先度項目ID形式: {self.value}"
            raise ValueError(msg)


class A31PriorityItem:
    """A31重点項目エンティティ

    A31チェックリストから抽出された重点項目を表現し、
    Claude Code分析への適性評価と分析実行管理を担当する。
    """

    def __init__(
        self,
        item_id: PriorityItemId,
        content: str,
        phase: A31CheckPhase,
        category: A31EvaluationCategory,
        priority_score: float,
        item_type: str = "content_quality",
        reference_guides: list[str] | None = None,
        created_at: datetime | None = None,
    ) -> None:
        """A31重点項目初期化

        Args:
            item_id: 項目識別ID
            content: チェック項目内容
            phase: 実行フェーズ
            category: 評価カテゴリ
            priority_score: 優先度スコア (0.0-1.0)
            item_type: 項目タイプ
            reference_guides: 参照ガイド一覧
            created_at: 作成日時

        Raises:
            ValueError: 無効なパラメータの場合
        """
        if not content or not content.strip():
            msg = "チェック項目内容は空にできません"
            raise ValueError(msg)

        if not 0.0 <= priority_score <= 1.0:
            msg = "priority_score は 0.0 から 1.0 の範囲である必要があります"
            raise ValueError(msg)

        self._item_id = item_id
        self._content = content.strip()
        self._phase = phase
        self._category = category
        self._priority_score = priority_score
        self._item_type = item_type
        self._reference_guides = reference_guides or []
        self._created_at = created_at or datetime.now(timezone.utc)

        # Claude分析適性を自動判定
        self._claude_analysis_suitability = self._determine_claude_suitability()

        # メタデータサポート（具体的改善提案等の保存用）
        self._metadata: dict[str, Any] = {}

    @classmethod
    def create(
        cls,
        item_id: str,
        content: str,
        phase: A31CheckPhase,
        category: A31EvaluationCategory,
        priority_score: float,
        **kwargs: Any,
    ) -> "A31PriorityItem":
        """A31重点項目ファクトリーメソッド"""
        priority_id = PriorityItemId(item_id)
        return cls(
            item_id=priority_id,
            content=content,
            phase=phase,
            category=category,
            priority_score=priority_score,
            **kwargs,
        )

    def _determine_claude_suitability(self) -> ClaudeAnalysisSuitability:
        """Claude分析適性を判定"""
        # 高適性項目タイプ
        high_suitability_types = [
            "content_balance",
            "sensory_check",
            "style_variety",
            "readability_check",
            "hook_check",
            "emotional_expression",
        ]

        # 高適性キーワード
        high_keywords = ["バランス", "描写", "五感", "冒頭", "引き込み", "リズム", "感情"]

        if self._item_type in high_suitability_types:
            return ClaudeAnalysisSuitability.HIGH

        content_lower = self._content.lower()
        if any(keyword in content_lower for keyword in high_keywords):
            return ClaudeAnalysisSuitability.HIGH

        # 中適性項目タイプ
        medium_suitability_types = ["character_consistency", "terminology_check", "format_check"]

        if self._item_type in medium_suitability_types:
            return ClaudeAnalysisSuitability.MEDIUM

        # コマンド実行系は不適
        if "novel " in self._content or "コマンド" in self._content:
            return ClaudeAnalysisSuitability.UNSUITABLE

        return ClaudeAnalysisSuitability.LOW

    def is_high_priority(self) -> bool:
        """高優先度項目かを判定（閾値: 0.7）"""
        return self._priority_score >= 0.7

    def is_high_priority_with_bonus(self) -> bool:
        """ボーナス適用後の高優先度判定"""
        return self.calculate_adjusted_priority_score() >= 0.7

    def calculate_adjusted_priority_score(self) -> float:
        """フェーズボーナス適用後の優先度スコアを計算"""
        base_score = self._priority_score
        phase_weight = self._phase.get_priority_weight()

        # Phase2とStage2は特別ボーナス
        bonus = 0.2 if self._phase in [A31CheckPhase.PHASE2_WRITING, A31CheckPhase.STAGE2_CONTENT] else 0.1

        # ウェイトとボーナスを適用
        adjusted_score = base_score + (phase_weight * bonus)
        return min(adjusted_score, 1.0)  # 1.0を超えないよう制限

    def is_claude_suitable(self) -> bool:
        """Claude分析に適しているかを判定"""
        return self._claude_analysis_suitability.is_suitable()

    def generate_claude_prompt_template(self) -> str:
        """Claude分析用プロンプトテンプレートを生成"""
        if not self.is_claude_suitable():
            msg = "この項目はClaude分析に適していません"
            raise ValueError(msg)

        # カテゴリ別の専用プロンプト
        category_prompts = {
            A31EvaluationCategory.CONTENT_BALANCE: self._generate_balance_prompt(),
            A31EvaluationCategory.SENSORY_DESCRIPTION: self._generate_sensory_prompt(),
            A31EvaluationCategory.BASIC_WRITING_STYLE: self._generate_style_prompt(),
            A31EvaluationCategory.CHARACTER_CONSISTENCY: self._generate_character_prompt(),
        }

        specific_prompt = category_prompts.get(self._category, self._generate_generic_prompt())

        return f"""# {self._content}

{specific_prompt}

## 期待する分析結果:
    1. 現状評価（1-10点スケール）
2. 具体的問題点の指摘（行番号付き）
3. 改善提案（修正例付き）
4. 改善効果の予測

## 出力形式:
    構造化YAML形式で、定量的評価と具体的提案を含む"""

    def _generate_balance_prompt(self) -> str:
        """バランス分析用プロンプト"""
        return """以下のエピソードの内容バランスを詳細分析してください：

### 分析観点:
    - 会話文と地の文の比率（理想: 30-40% : 60-70%）
- 情報密度の適切性
- 展開テンポの妥当性
- 各シーンの重要度バランス"""

    def _generate_sensory_prompt(self) -> str:
        """感覚描写分析用プロンプト"""
        return """以下のエピソードの五感描写を網羅的に分析してください：

### 分析観点:
    - 視覚・聴覚・触覚・嗅覚・味覚の使用頻度
- 各感覚描写の具体性と効果性
- 感覚配置のバランスと読者没入度への影響
- 技術的メタファーとの融合度"""

    def _generate_style_prompt(self) -> str:
        """文体分析用プロンプト"""
        return """以下のエピソードの文体とリズムを詳細分析してください：

### 分析観点:
    - 文長の変化とリズム感
- 文末表現のバリエーション
- 読みやすさと冒頭引き込み効果
- ジャンル特性との適合性"""

    def _generate_character_prompt(self) -> str:
        """キャラクター描写分析用プロンプト"""
        return """以下のエピソードのキャラクター描写を一貫性の観点から分析してください：

### 分析観点:
    - 各キャラクターの口調・語彙の一貫性
- 性格表現の適切性
- 感情描写の具体性と身体化
- キャラクター間の差別化度"""

    def _generate_generic_prompt(self) -> str:
        """汎用分析プロンプト"""
        return f"""以下のエピソードについて「{self._content}」の観点から詳細分析してください：

### 分析観点:
    - 現状の品質レベル評価
- 改善が必要な具体的箇所
- 読者体験への影響度
- 実装可能な改善策"""

    def to_dict(self) -> dict[str, Any]:
        """辞書形式での出力"""
        return {
            "item_id": self._item_id.value,
            "content": self._content,
            "phase": self._phase.value,
            "category": self._category.value,
            "priority_score": self._priority_score,
            "adjusted_priority_score": self.calculate_adjusted_priority_score(),
            "claude_analysis_suitability": self._claude_analysis_suitability.value,
            "is_high_priority": self.is_high_priority(),
            "is_claude_suitable": self.is_claude_suitable(),
            "item_type": self._item_type,
            "reference_guides": self._reference_guides,
            "created_at": self._created_at.isoformat(),
        }

    # プロパティ
    @property
    def item_id(self) -> PriorityItemId:
        """項目ID"""
        return self._item_id

    @property
    def content(self) -> str:
        """チェック項目内容"""
        return self._content

    @property
    def phase(self) -> A31CheckPhase:
        """実行フェーズ"""
        return self._phase

    @property
    def category(self) -> A31EvaluationCategory:
        """評価カテゴリ"""
        return self._category

    @property
    def priority_score(self) -> float:
        """優先度スコア"""
        return self._priority_score

    @property
    def claude_analysis_suitability(self) -> ClaudeAnalysisSuitability:
        """Claude分析適性"""
        return self._claude_analysis_suitability

    @property
    def created_at(self) -> datetime:
        """作成日時"""
        return self._created_at

    @property
    def metadata(self) -> dict[str, Any]:
        """メタデータ取得"""
        return self._metadata.copy()

    def get_concrete_suggestions(self) -> list[str]:
        """具体的改善提案取得"""
        return self._metadata.get("concrete_suggestions", [])

    def has_concrete_suggestions(self) -> bool:
        """具体的改善提案の有無"""
        return bool(self._metadata.get("concrete_suggestions"))

    def add_metadata(self, key: str, value: Any) -> None:
        """メタデータ追加"""
        self._metadata[key] = value

    # 同値性とハッシュ（IDベース）
    def __eq__(self, other: object) -> bool:
        """同値性判定（IDベース）"""
        if not isinstance(other, A31PriorityItem):
            return False
        return self._item_id == other._item_id

    def __hash__(self) -> int:
        """ハッシュ値計算（IDベース）"""
        return hash(self._item_id)

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return (
            f"A31PriorityItem(id={self._item_id.value}, priority={self._priority_score:.2f}, phase={self._phase.name})"
        )
