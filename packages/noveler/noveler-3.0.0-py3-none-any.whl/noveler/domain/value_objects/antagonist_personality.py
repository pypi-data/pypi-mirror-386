#!/usr/bin/env python3
"""敵キャラクター個性システム関連のValue Objects

A38執筆プロンプトガイドSTEP6で定義される敵キャラクター個性強化システムを実装。
定型的でない個性的な敵キャラを設計するためのデータ構造を提供。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SpeechPattern(Enum):
    """口調パターンの種類"""

    FORMAL_TWISTED = "formal_twisted"  # 堅い敬語を独特に崩す
    DIALECT_MIXED = "dialect_mixed"  # 方言と標準語のミックス
    ARCHAIC_MODERN = "archaic_modern"  # 古語と現代語のミックス
    TECHNICAL_POETIC = "technical_poetic"  # 専門用語と詩的表現
    CHILDISH_WISE = "childish_wise"  # 幼稚語と賢い内容
    BROKEN_ELOQUENT = "broken_eloquent"  # 片言と雄弁のギャップ


class ObsessionCategory(Enum):
    """こだわり・執着のカテゴリ"""

    PERFECTIONISM = "perfectionism"  # 完璧主義
    AESTHETICS = "aesthetics"  # 美学・美意識
    ORDER = "order"  # 秩序・ルール
    EFFICIENCY = "efficiency"  # 効率性
    TRADITION = "tradition"  # 伝統・格式
    KNOWLEDGE = "knowledge"  # 知識・学問
    HONOR = "honor"  # 名誉・誇り
    COLLECTION = "collection"  # 収集・所有
    CONTROL = "control"  # 支配・制御
    PURITY = "purity"  # 純粋性・清廉


class GapType(Enum):
    """ギャップ要素の種類"""

    APPEARANCE_PERSONALITY = "appearance_personality"  # 見た目と中身
    STRENGTH_WEAKNESS = "strength_weakness"  # 強さと弱さ
    PUBLIC_PRIVATE = "public_private"  # 表と裏
    PAST_PRESENT = "past_present"  # 過去と現在
    IDEAL_REALITY = "ideal_reality"  # 理想と現実
    FEAR_BRAVERY = "fear_bravery"  # 恐怖と勇気


@dataclass
class SpeechStyle:
    """個性的な話し方のスタイル定義

    Attributes:
        pattern: 基本的な口調パターン
        endings: 語尾の特徴（例: 〜だからね、〜である故に）
        vocabulary_level: 語彙レベル（1=庶民的 〜 10=高尚）
        special_expressions: 独特な表現・決まり文句
        emotional_variations: 感情による変化パターン
    """

    pattern: SpeechPattern
    endings: list[str] = field(default_factory=list)
    vocabulary_level: int = 5
    special_expressions: list[str] = field(default_factory=list)
    emotional_variations: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """バリデーション"""
        if not 1 <= self.vocabulary_level <= 10:
            msg = f"Vocabulary level must be 1-10, got {self.vocabulary_level}"
            raise ValueError(msg)

    def generate_sample_phrases(self) -> list[str]:
        """サンプル台詞を生成

        Returns:
            この話し方スタイルの特徴を表すサンプル台詞集
        """
        samples = []

        # 基本パターン別のサンプル
        pattern_samples = {
            SpeechPattern.FORMAL_TWISTED: [
                "恐れながら申し上げますが、貴方は間違っているのでは...ないかと思うのですがね",
                "誠に申し訳ございませんが、貴方の理解は浅いと言わざるを得ませんわ",
            ],
            SpeechPattern.DIALECT_MIXED: [
                "おまえさん、それは違うんじゃないか？と私は思うわけでして",
                "まあまあ、そう怒らんでも...というか、怒るような話でもないでしょ",
            ],
            SpeechPattern.ARCHAIC_MODERN: [
                "なんと愚かしき...いや、マジでアホらしいな",
                "申すまでもないが...つまり、当たり前の話だよ",
            ],
            SpeechPattern.TECHNICAL_POETIC: [
                "論理的帰結として...まあ、美しい敗北が見えるね",
                "統計的確率では...ああ、運命が微笑んでいる",
            ],
            SpeechPattern.CHILDISH_WISE: [
                "おかしいよ〜、だって哲学的に考えてみてよ",
                "えー、それって結局存在論的な問題でしょ？",
            ],
            SpeechPattern.BROKEN_ELOQUENT: [
                "ワタシ...言いたいことは...つまり人間の本質とは複雑なる矛盾の集合体であり",
                "アナタ...分からない？...すなわち真理とは常に二律背反的性質を有するのです",
            ],
        }

        samples.extend(pattern_samples.get(self.pattern, ["（サンプルなし）"]))

        # 語尾変化のサンプル
        if self.endings:
            base_phrase = "それは正しくないと思う"
            # 最大3つの変換パターンを生成
            samples.extend(f"{base_phrase.replace('思う', '')}{ending}" for ending in self.endings[:3])

        return samples


@dataclass
class PersonalObsession:
    """個人的なこだわり・執着の定義

    Attributes:
        category: こだわりのカテゴリ
        specific_focus: 具体的な焦点（何にこだわるか）
        manifestation: こだわりの現れ方
        trigger_conditions: こだわりが発動する条件
        intensity_level: こだわりの強度（1=軽いこだわり 〜 10=病的執着）
    """

    category: ObsessionCategory
    specific_focus: str
    manifestation: str
    trigger_conditions: list[str] = field(default_factory=list)
    intensity_level: int = 5

    def __post_init__(self) -> None:
        """バリデーション"""
        if not 1 <= self.intensity_level <= 10:
            msg = f"Intensity level must be 1-10, got {self.intensity_level}"
            raise ValueError(msg)

    def get_behavior_examples(self) -> list[str]:
        """このこだわりに基づく行動例を生成"""
        examples = []

        # カテゴリ別の行動例
        category_behaviors = {
            ObsessionCategory.PERFECTIONISM: [
                f"{self.specific_focus}において、完璧でない部分を見つけると修正せずにいられない",
                f"他者が{self.specific_focus}を雑に扱うのを見ると激怒する",
                f"{self.specific_focus}の基準を満たさない場合、最初からやり直すよう強要する",
            ],
            ObsessionCategory.AESTHETICS: [
                f"{self.specific_focus}の美しさについて長時間語り続ける",
                f"美しくない{self.specific_focus}を見ると機嫌が悪くなる",
                f"{self.specific_focus}の配置や色合いを細かく調整する",
            ],
            ObsessionCategory.ORDER: [
                f"{self.specific_focus}の順序が乱れると即座に整理し直す",
                "ルールを破る者に対して厳しく処罰する",
                f"{self.specific_focus}に関する規則を次々と作り出す",
            ],
        }

        examples.extend(category_behaviors.get(self.category, [f"{self.specific_focus}に関する特殊な行動"]))

        # 強度による行動の変化
        if self.intensity_level >= 8:
            examples.append(f"{self.specific_focus}のためなら他のことを犠牲にしても構わない")
        if self.intensity_level >= 9:
            examples.append(f"{self.specific_focus}を理解しない者は敵だと認識する")

        return examples


@dataclass
class CharacterGap:
    """キャラクターのギャップ要素

    Attributes:
        gap_type: ギャップの種類
        surface_aspect: 表面的な側面（第一印象）
        hidden_aspect: 隠れた側面（真の一面）
        revelation_conditions: ギャップが露呈する条件
        impact_level: ギャップのインパクト（1=些細 〜 10=衝撃的）
    """

    gap_type: GapType
    surface_aspect: str
    hidden_aspect: str
    revelation_conditions: list[str] = field(default_factory=list)
    impact_level: int = 5

    def __post_init__(self) -> None:
        """バリデーション"""
        if not 1 <= self.impact_level <= 10:
            msg = f"Impact level must be 1-10, got {self.impact_level}"
            raise ValueError(msg)

    def get_reveal_scenarios(self) -> list[str]:
        """ギャップが露呈するシナリオ例"""
        scenarios = []

        # 基本的な露呈シナリオ
        scenarios.extend(self.revelation_conditions)

        # ギャップタイプ別の典型的シナリオ
        type_scenarios = {
            GapType.APPEARANCE_PERSONALITY: [
                "普段とは異なる状況に置かれた時",
                "信頼できる相手との一対一の会話",
                "極度のストレス下での反応",
            ],
            GapType.STRENGTH_WEAKNESS: [
                "得意分野以外での挑戦を強いられた時",
                "過去のトラウマに触れる出来事",
                "大切な人が危険にさらされた時",
            ],
            GapType.PUBLIC_PRIVATE: [
                "公の場を離れてプライベートになった時",
                "側近や家族といる時の様子",
                "計画が狂って素が出た時",
            ],
        }

        scenarios.extend(type_scenarios.get(self.gap_type, ["予想外の状況での反応"]))

        return scenarios


@dataclass
class SignatureMoment:
    """印象に残る決めシーン・決め台詞

    Attributes:
        signature_line: 決め台詞
        signature_pose: 決めポーズ・動作
        context: そのシーンの文脈
        effect_description: 読者・他キャラに与える効果
        memorable_elements: 記憶に残る要素の詳細
    """

    signature_line: str
    signature_pose: str = ""
    context: str = ""
    effect_description: str = ""
    memorable_elements: list[str] = field(default_factory=list)

    def get_variation_patterns(self) -> list[str]:
        """決め台詞のバリエーションパターン"""
        variations = [self.signature_line]

        # 基本台詞のバリエーション生成
        if "だ" in self.signature_line:
            variations.append(self.signature_line.replace("だ", "である"))
        if "である" in self.signature_line:
            variations.append(self.signature_line.replace("である", "だ"))

        # 感情的な変化バリエーション
        if self.signature_line:
            variations.append(f"...{self.signature_line}")  # 静かに
            variations.append(f"{self.signature_line}！")  # 強調
            variations.append(f"《{self.signature_line}》")  # 内心

        return variations


@dataclass
class AntagonistPersonality:
    """敵キャラクター個性システムの統合クラス

    A38 STEP6で定義される敵キャラクター個性強化の全要素を統合管理
    """

    character_name: str
    character_role: str  # "主要敵対者", "中ボス", "雑魚敵", "裏切り者"等

    # 核となる個性要素
    speech_style: SpeechStyle
    primary_obsession: PersonalObsession
    main_gap: CharacterGap
    signature_moment: SignatureMoment

    # 補助的個性要素
    secondary_obsessions: list[PersonalObsession] = field(default_factory=list)
    minor_gaps: list[CharacterGap] = field(default_factory=list)
    additional_signatures: list[SignatureMoment] = field(default_factory=list)

    # メタ情報
    uniqueness_score: float = 0.0  # 個性度スコア（0.0-10.0）
    memorability_score: float = 0.0  # 記憶度スコア（0.0-10.0）
    threat_level: int = 5  # 脅威レベル（1-10）

    def calculate_uniqueness_score(self) -> float:
        """個性度スコアを計算

        Returns:
            0.0-10.0の個性度スコア
        """
        score = 0.0

        # 話し方の個性度
        if len(self.speech_style.endings) >= 2:
            score += 2.0
        if len(self.speech_style.special_expressions) >= 3:
            score += 1.5
        if self.speech_style.vocabulary_level >= 8 or self.speech_style.vocabulary_level <= 3:
            score += 1.0  # 極端な語彙レベルにボーナス

        # こだわりの個性度
        if self.primary_obsession.intensity_level >= 8:
            score += 2.0
        if len(self.secondary_obsessions) >= 2:
            score += 1.0

        # ギャップの個性度
        if self.main_gap.impact_level >= 7:
            score += 2.0
        if len(self.minor_gaps) >= 1:
            score += 0.5

        # 決めシーンの個性度
        if len(self.signature_moment.memorable_elements) >= 3:
            score += 1.0

        self.uniqueness_score = min(10.0, score)
        return self.uniqueness_score

    def calculate_memorability_score(self) -> float:
        """記憶度スコアを計算

        Returns:
            0.0-10.0の記憶度スコア
        """
        score = 0.0

        # 決め台詞の記憶度
        if len(self.signature_moment.signature_line) >= 10:  # ある程度の長さ
            score += 2.0
        if any("!" in line for line in self.speech_style.special_expressions):
            score += 1.0  # インパクトのある表現

        # ギャップの記憶度
        total_gap_impact = self.main_gap.impact_level + sum(gap.impact_level for gap in self.minor_gaps)
        score += min(3.0, total_gap_impact * 0.3)

        # こだわりの記憶度
        if self.primary_obsession.intensity_level >= 7:
            score += 2.0

        # 複数要素の相乗効果
        element_count = (
            (1 if len(self.speech_style.endings) >= 2 else 0)
            + (1 if self.primary_obsession.intensity_level >= 6 else 0)
            + (1 if self.main_gap.impact_level >= 6 else 0)
            + (1 if len(self.signature_moment.memorable_elements) >= 2 else 0)
        )
        if element_count >= 3:
            score += 2.0  # 多面的な個性にボーナス

        self.memorability_score = min(10.0, score)
        return self.memorability_score

    def generate_character_profile(self) -> dict[str, Any]:
        """キャラクター設定書を生成

        Returns:
            YAML出力可能な設定書辞書
        """
        # スコア更新
        self.calculate_uniqueness_score()
        self.calculate_memorability_score()

        return {
            "character_name": self.character_name,
            "character_role": self.character_role,
            "personality_system": {
                "speech_style": {
                    "pattern": self.speech_style.pattern.value,
                    "endings": self.speech_style.endings,
                    "vocabulary_level": self.speech_style.vocabulary_level,
                    "special_expressions": self.speech_style.special_expressions,
                    "sample_phrases": self.speech_style.generate_sample_phrases(),
                },
                "primary_obsession": {
                    "category": self.primary_obsession.category.value,
                    "specific_focus": self.primary_obsession.specific_focus,
                    "manifestation": self.primary_obsession.manifestation,
                    "intensity_level": self.primary_obsession.intensity_level,
                    "behavior_examples": self.primary_obsession.get_behavior_examples(),
                },
                "main_gap": {
                    "gap_type": self.main_gap.gap_type.value,
                    "surface_aspect": self.main_gap.surface_aspect,
                    "hidden_aspect": self.main_gap.hidden_aspect,
                    "impact_level": self.main_gap.impact_level,
                    "reveal_scenarios": self.main_gap.get_reveal_scenarios(),
                },
                "signature_moment": {
                    "signature_line": self.signature_moment.signature_line,
                    "signature_pose": self.signature_moment.signature_pose,
                    "context": self.signature_moment.context,
                    "memorable_elements": self.signature_moment.memorable_elements,
                    "variations": self.signature_moment.get_variation_patterns(),
                },
                "metrics": {
                    "uniqueness_score": self.uniqueness_score,
                    "memorability_score": self.memorability_score,
                    "threat_level": self.threat_level,
                    "total_elements": (
                        1 + len(self.secondary_obsessions) + len(self.minor_gaps) + len(self.additional_signatures)
                    ),
                },
            },
        }

    def export_to_yaml_dict(self) -> dict[str, Any]:
        """YAML出力用の辞書を生成

        conversation_design_service.py:319で呼び出される統合エクスポート用メソッド

        Returns:
            YAML出力可能な辞書データ
        """
        return self.generate_character_profile()
