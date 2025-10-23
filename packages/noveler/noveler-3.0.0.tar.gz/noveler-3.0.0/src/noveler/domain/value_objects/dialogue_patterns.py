#!/usr/bin/env python3
"""新規会話パターンシステム関連のValue Objects

A38執筆プロンプトガイドSTEP7で定義される新規会話パターンを実装。
知識差ギャップパターン、ジャンル認識ギャップパターン等の
「なろう系」特有の効果的な会話パターンを体系化。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DialoguePatternType(Enum):
    """会話パターンの種類"""

    MISUNDERSTANDING_GAP = "misunderstanding_gap"  # 勘違いギャップパターン（既存）
    KNOWLEDGE_GAP = "knowledge_gap"  # 知識差ギャップパターン（新規）
    GENRE_RECOGNITION_GAP = "genre_recognition_gap"  # ジャンル認識ギャップパターン（新規）
    INSTANT_DECISION = "instant_decision"  # 即断即決パターン（既存）
    AUTHORITY_DELEGATION = "authority_delegation"  # 権限委譲パターン
    COMPETENCE_GAP = "competence_gap"  # 能力ギャップパターン
    PERSPECTIVE_SHIFT = "perspective_shift"  # 視点転換パターン


class ReaderEffect(Enum):
    """読者への効果"""

    COMEDY = "comedy"  # コメディ効果
    SUPERIORITY_FEELING = "superiority"  # 優越感
    RELATABILITY = "relatability"  # 親近感
    COMMENT_INDUCING = "comment_inducing"  # コメント誘発
    TENSION_RELIEF = "tension_relief"  # 緊張緩和
    ANTICIPATION = "anticipation"  # 期待感
    SATISFACTION = "satisfaction"  # 満足感


@dataclass
class DialogueExchange:
    """会話のやりとり単位

    Attributes:
        speaker: 発言者
        line: 台詞内容
        internal_thought: 内心の思考（地の文用）
        reaction_description: 反応の描写
        timing: タイミング指定
    """

    speaker: str
    line: str
    internal_thought: str = ""
    reaction_description: str = ""
    timing: str = "normal"  # "normal", "pause", "immediate", "overlap"

    def get_full_exchange_text(self) -> str:
        """完全な会話テキストを生成"""
        result = []

        if self.reaction_description:
            result.append(self.reaction_description)

        result.append(f"「{self.line}」")

        if self.internal_thought:
            result.append(f"（{self.internal_thought}）")

        return "".join(result)


@dataclass
class KnowledgeGapPattern:
    """知識差ギャップパターンの実装

    専門知識と素朴な解釈のズレで軽快なコメディを演出。
    読者の優越感と親近感を同時創出、コメント誘発効果+23%。
    """

    pattern_id: str
    knowledge_holder: str  # 知識を持つキャラクター
    naive_character: str  # 素朴な解釈をするキャラクター

    # パターンの核となる要素
    technical_term: str  # 専門用語（例：「SQL」「データベース」）
    naive_interpretation: str  # 素朴な解釈（例：「魔法陣の配列最適化技術」）
    correction_attempt: str  # 修正の試み（例：「データベースの事だよ」）
    further_confusion: str  # さらなる混乱（例：「でーたべーす？新しい料理？」）

    # メタ情報
    knowledge_domain: str = ""  # 知識領域（IT/医学/法律等）
    confusion_level: int = 5  # 混乱度（1-10）
    comedy_intensity: int = 5  # コメディ強度（1-10）

    def generate_exchange_sequence(self) -> list[DialogueExchange]:
        """4段階の会話シーケンスを生成"""
        return [
            DialogueExchange(
                speaker=self.naive_character,
                line=f"え？{self.technical_term}って何の呪文ですか？",
                internal_thought="また知らない単語が出てきた...",
                reaction_description="きょとんとした表情で",
            ),
            DialogueExchange(
                speaker=self.knowledge_holder,
                line=self.naive_interpretation,
                internal_thought="どう説明しようか...",
                reaction_description="困ったような笑顔で",
                timing="pause",
            ),
            DialogueExchange(
                speaker=self.knowledge_holder,
                line=self.correction_attempt,
                internal_thought="まあ、間違いではないけど...",
                reaction_description="苦笑いしながら",
            ),
            DialogueExchange(
                speaker=self.naive_character,
                line=self.further_confusion,
                internal_thought="ますます分からなくなった",
                reaction_description="首をかしげて",
                timing="immediate",
            ),
        ]

    def calculate_effect_score(self) -> dict[ReaderEffect, float]:
        """読者効果スコアを計算"""
        return {
            ReaderEffect.COMEDY: min(10.0, self.comedy_intensity * 1.0),
            ReaderEffect.SUPERIORITY_FEELING: min(10.0, self.confusion_level * 0.8),
            ReaderEffect.RELATABILITY: 7.0,  # 「あるある」感による固定値
            ReaderEffect.COMMENT_INDUCING: 6.5,  # コメント誘発の基本値
            ReaderEffect.TENSION_RELIEF: min(10.0, self.comedy_intensity * 0.9),
        }


@dataclass
class GenreRecognitionGapPattern:
    """ジャンル認識ギャップパターンの実装

    異世界知識vs現代知識の解釈差で「あー、そう来るか」感を創出。
    """

    pattern_id: str
    modern_character: str  # 現代知識を持つキャラクター
    fantasy_character: str  # ファンタジー世界の住人

    # パターンの核となる要素
    modern_concept: str  # 現代概念（例：「電池」「エンジン」）
    fantasy_equivalent: str  # ファンタジー世界の同等品（例：「魔石」「魔動機」）
    recognition_moment: str  # 認識の瞬間（例：「あぁ、この世界の『電池』みたいなもんか」）
    fantasy_confusion: str  # ファンタジー側の困惑（例：「でんち...？」）

    # メタ情報
    conceptual_distance: int = 5  # 概念的距離（1=近い、10=遠い）
    revelation_impact: int = 5  # 気づきのインパクト
    world_building_value: int = 5  # 世界観構築への貢献度

    def generate_exchange_sequence(self) -> list[DialogueExchange]:
        """4段階の認識ギャップシーケンスを生成"""
        return [
            DialogueExchange(
                speaker=self.modern_character,
                line=f"この世界の常識では、{self.fantasy_equivalent}は貴重品なんだろ？",
                internal_thought="まずは相手の世界の常識を確認",
                reaction_description="興味深そうに",
            ),
            DialogueExchange(
                speaker=self.fantasy_character,
                line="はい、一般的には...",
                internal_thought="なぜそんな当然のことを？",
                reaction_description="少し戸惑いながら",
            ),
            DialogueExchange(
                speaker=self.modern_character,
                line=self.recognition_moment,
                internal_thought="なるほど、理解した",
                reaction_description="ひとりでに納得して",
                timing="immediate",
            ),
            DialogueExchange(
                speaker=self.fantasy_character,
                line=self.fantasy_confusion,
                internal_thought="また分からない言葉が...",
                reaction_description="困惑の表情で",
            ),
        ]

    def calculate_effect_score(self) -> dict[ReaderEffect, float]:
        """読者効果スコアを計算"""
        return {
            ReaderEffect.SATISFACTION: min(10.0, self.revelation_impact * 1.2),
            ReaderEffect.SUPERIORITY_FEELING: min(10.0, self.conceptual_distance * 0.7),
            ReaderEffect.ANTICIPATION: min(10.0, self.world_building_value * 0.8),
            ReaderEffect.RELATABILITY: 6.0,  # 「そうそう」という共感
            ReaderEffect.COMEDY: min(10.0, (10 - self.conceptual_distance) * 0.5),
        }


@dataclass
class MisunderstandingGapPattern:
    """勘違いギャップパターン（既存パターンの体系化）

    主人公の真意と周囲の解釈のズレでコメディ効果とテンポ創出。
    """

    pattern_id: str
    protagonist: str  # 主人公
    interpreter: str  # 解釈する側

    # パターンの核となる要素
    true_intention: str  # 主人公の真意（例：「ただの気まぐれ」）
    misinterpreted_meaning: str  # 誤解された意味（例：「慈悲深い判断」）
    gap_revelation: str  # ギャップの露呈（例：「は？俺はただの気まぐれで...」）
    double_down: str  # さらなる誤解（例：「その気まぐれこそが救い」）

    # メタ情報
    misunderstanding_type: str = "positive"  # "positive", "negative", "neutral"
    gap_size: int = 5  # ギャップの大きさ
    tempo_contribution: int = 7  # テンポ向上への貢献

    def generate_exchange_sequence(self) -> list[DialogueExchange]:
        """4段階のギャップシーケンスを生成"""
        return [
            DialogueExchange(
                speaker=self.interpreter,
                line=self.misinterpreted_meaning,
                internal_thought="素晴らしい方だ",
                reaction_description="感激して",
            ),
            DialogueExchange(
                speaker=self.protagonist,
                line=self.gap_revelation,
                internal_thought="なんで大げさに解釈するんだ",
                reaction_description="困惑しながら",
            ),
            DialogueExchange(
                speaker=self.interpreter,
                line=self.double_down,
                internal_thought="ますます素晴らしい",
                reaction_description="より深く感動して",
            ),
            DialogueExchange(
                speaker=self.protagonist,
                line="（もう何も言うまい...）",
                internal_thought="説明するのも疲れた",
                reaction_description="諦めたような表情で",
            ),
        ]


@dataclass
class InstantDecisionPattern:
    """即断即決パターン（既存パターンの体系化）

    主人公は即断、説明は部下に委任の効率的会話構造。
    """

    pattern_id: str
    decision_maker: str  # 決断者（通常は主人公）
    subordinate: str  # 部下・説明役

    # パターンの核となる要素
    quick_decision: str  # 即断内容（例：「税率を下げろ」）
    concern_raising: str  # 懸念提示（例：「しかし収入が...」）
    simple_solution: str  # シンプルな解決策（例：「余計な贅沢を削れ」）
    delegation_phrase: str  # 委任の台詞（例：「詳細はお前が決めろ」）

    # メタ情報
    decision_complexity: int = 5  # 決断の複雑さ
    leadership_impression: int = 8  # リーダーシップの印象
    efficiency_score: int = 9  # 効率性スコア

    def generate_exchange_sequence(self) -> list[DialogueExchange]:
        """3段階の即断シーケンスを生成"""
        return [
            DialogueExchange(
                speaker=self.decision_maker,
                line=self.quick_decision,
                internal_thought="当然のことだ",
                reaction_description="迷いなく",
                timing="immediate",
            ),
            DialogueExchange(
                speaker=self.subordinate,
                line=self.concern_raising,
                internal_thought="現実的な問題が...",
                reaction_description="心配そうに",
            ),
            DialogueExchange(
                speaker=self.decision_maker,
                line=self.simple_solution,
                internal_thought="解決策は簡単だ",
                reaction_description="当然のように",
            ),
        ]


@dataclass
class DialoguePatternLibrary:
    """会話パターンライブラリの統合管理クラス

    A38で定義される全会話パターンを実装・管理
    """

    def __init__(self) -> None:
        """パターンライブラリを初期化"""
        self.knowledge_gap_patterns: dict[str, KnowledgeGapPattern] = {}
        self.genre_gap_patterns: dict[str, GenreRecognitionGapPattern] = {}
        self.misunderstanding_patterns: dict[str, MisunderstandingGapPattern] = {}
        self.instant_decision_patterns: dict[str, InstantDecisionPattern] = {}

        # デフォルトパターンを登録
        self._register_default_patterns()

    def _register_default_patterns(self) -> None:
        """デフォルトの効果的パターンを登録"""
        # 知識差ギャップのサンプル
        self.register_knowledge_gap_pattern(
            KnowledgeGapPattern(
                pattern_id="kg_001",
                knowledge_holder="主人公",
                naive_character="村娘",
                technical_term="SQL",
                naive_interpretation="魔法陣の配列を最適化する技術のことかな？",
                correction_attempt="データベースの事だよ...",
                further_confusion="でーたべーす？新しい料理？",
                knowledge_domain="IT",
                confusion_level=8,
                comedy_intensity=7,
            )
        )

        # ジャンル認識ギャップのサンプル
        self.register_genre_gap_pattern(
            GenreRecognitionGapPattern(
                pattern_id="gr_001",
                modern_character="主人公",
                fantasy_character="執事",
                modern_concept="電池",
                fantasy_equivalent="魔石",
                recognition_moment="じゃあ俺の世界の『電池』みたいなもんか",
                fantasy_confusion="でんち......？",
                conceptual_distance=6,
                revelation_impact=7,
                world_building_value=8,
            )
        )

    def register_knowledge_gap_pattern(self, pattern: KnowledgeGapPattern) -> None:
        """知識差ギャップパターンを登録"""
        self.knowledge_gap_patterns[pattern.pattern_id] = pattern

    def register_genre_gap_pattern(self, pattern: GenreRecognitionGapPattern) -> None:
        """ジャンル認識ギャップパターンを登録"""
        self.genre_gap_patterns[pattern.pattern_id] = pattern

    def add_pattern(self, pattern_type: str, pattern_id: str, pattern_data: dict[str, Any]) -> bool:
        """会話パターンをライブラリに追加

        conversation_design_service.py:215で呼び出されるパターン追加メソッド

        Args:
            pattern_type: パターンタイプ（'knowledge_gap', 'genre_gap'等）
            pattern_id: パターンID
            pattern_data: パターンデータ

        Returns:
            追加成功可否
        """
        try:
            if pattern_type == "knowledge_gap":
                kg_pattern = KnowledgeGapPattern(
                    pattern_id=pattern_id,
                    knowledge_holder=pattern_data.get("knowledge_holder", ""),
                    naive_character=pattern_data.get("naive_character", ""),
                    technical_term=pattern_data.get("technical_term", ""),
                    naive_interpretation=pattern_data.get("naive_interpretation", ""),
                    correction_attempt=pattern_data.get("correction_attempt", ""),
                    further_confusion=pattern_data.get("further_confusion", ""),
                    knowledge_domain=pattern_data.get("knowledge_domain", ""),
                    confusion_level=pattern_data.get("confusion_level", 5),
                    comedy_intensity=pattern_data.get("comedy_intensity", 5),
                )
                self.register_knowledge_gap_pattern(kg_pattern)

            elif pattern_type == "genre_gap":
                gr_pattern = GenreRecognitionGapPattern(
                    pattern_id=pattern_id,
                    modern_character=pattern_data.get("modern_character", ""),
                    fantasy_character=pattern_data.get("fantasy_character", ""),
                    modern_concept=pattern_data.get("modern_concept", ""),
                    fantasy_equivalent=pattern_data.get("fantasy_equivalent", ""),
                    recognition_moment=pattern_data.get("recognition_moment", ""),
                    fantasy_confusion=pattern_data.get("fantasy_confusion", ""),
                    conceptual_distance=pattern_data.get("conceptual_distance", 5),
                    revelation_impact=pattern_data.get("revelation_impact", 5),
                    world_building_value=pattern_data.get("world_building_value", 5),
                )
                self.register_genre_gap_pattern(gr_pattern)

            else:
                return False  # サポートされていないパターンタイプ

            return True

        except Exception:
            return False

    def get_pattern_recommendation(self, characters: list[str], desired_effect: ReaderEffect) -> list[str]:
        """シーンに適したパターンを推奨

        Args:
            characters: 登場キャラクター
            desired_effect: 望む読者効果

        Returns:
            推奨パターンIDのリスト
        """
        recommendations = []

        # 知識差ギャップパターンの推奨
        if desired_effect in [ReaderEffect.COMEDY, ReaderEffect.SUPERIORITY_FEELING]:
            for pattern_id, pattern in self.knowledge_gap_patterns.items():
                if pattern.knowledge_holder in characters and pattern.naive_character in characters:
                    recommendations.append(pattern_id)

        # ジャンル認識ギャップパターンの推奨
        if desired_effect in [ReaderEffect.SATISFACTION, ReaderEffect.ANTICIPATION]:
            genre_pattern: GenreRecognitionGapPattern
            for pattern_id, genre_pattern in self.genre_gap_patterns.items():
                if genre_pattern.modern_character in characters and genre_pattern.fantasy_character in characters:
                    recommendations.append(pattern_id)

        return recommendations

    def generate_pattern_usage_stats(self) -> dict[str, Any]:
        """パターン使用統計を生成"""
        return {
            "total_patterns": (
                len(self.knowledge_gap_patterns)
                + len(self.genre_gap_patterns)
                + len(self.misunderstanding_patterns)
                + len(self.instant_decision_patterns)
            ),
            "knowledge_gap_patterns": len(self.knowledge_gap_patterns),
            "genre_gap_patterns": len(self.genre_gap_patterns),
            "misunderstanding_patterns": len(self.misunderstanding_patterns),
            "instant_decision_patterns": len(self.instant_decision_patterns),
            "average_comedy_score": self._calculate_average_comedy_score(),
            "most_effective_patterns": self._get_most_effective_patterns(),
        }

    def _calculate_average_comedy_score(self) -> float:
        """平均コメディスコアを計算"""
        total_score = 0.0
        total_patterns = 0

        for pattern in self.knowledge_gap_patterns.values():
            effects = pattern.calculate_effect_score()
            total_score += effects.get(ReaderEffect.COMEDY, 0.0)
            total_patterns += 1

        genre_pattern: GenreRecognitionGapPattern
        for genre_pattern in self.genre_gap_patterns.values():
            effects = genre_pattern.calculate_effect_score()
            total_score += effects.get(ReaderEffect.COMEDY, 0.0)
            total_patterns += 1

        return total_score / max(1, total_patterns)

    def _get_most_effective_patterns(self) -> list[str]:
        """最も効果的なパターンを取得"""
        pattern_scores = []

        # 各パターンの総合効果スコアを計算
        for pattern_id, pattern in self.knowledge_gap_patterns.items():
            effects = pattern.calculate_effect_score()
            total_score = sum(effects.values())
            pattern_scores.append((pattern_id, total_score))

        genre_pattern: GenreRecognitionGapPattern
        for pattern_id, genre_pattern in self.genre_gap_patterns.items():
            effects = genre_pattern.calculate_effect_score()
            total_score = sum(effects.values())
            pattern_scores.append((pattern_id, total_score))

        # スコア順にソートして上位3つを返す
        pattern_scores.sort(key=lambda x: x[1], reverse=True)
        return [pattern_id for pattern_id, _ in pattern_scores[:3]]
