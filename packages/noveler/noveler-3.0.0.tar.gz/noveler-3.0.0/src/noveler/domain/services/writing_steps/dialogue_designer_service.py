"""Domain.services.writing_steps.dialogue_designer_service
Where: Domain service module implementing a specific writing workflow step.
What: Provides helper routines and data structures for this writing step.
Why: Allows stepwise writing orchestrators to reuse consistent step logic.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""STEP 5: DialogueDesignerService

A38執筆プロンプトガイドのSTEP 5に対応するマイクロサービス。
対話設計・キャラクター音声・会話流れの最適化を担当。
"""

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from noveler.domain.interfaces.logger_service_protocol import ILoggerService

from noveler.domain.services.writing_steps.base_writing_step import BaseWritingStep, WritingStepResponse


@dataclass
class CharacterVoice:
    """キャラクター音声特性"""

    character_name: str

    # 基本特性
    speaking_style: str  # "formal", "casual", "eloquent", "rough"
    vocabulary_level: str  # "simple", "standard", "advanced", "technical"
    sentence_structure: str  # "short", "medium", "long", "varied"

    # 個性的要素
    catchphrases: list[str] = field(default_factory=list)
    speech_patterns: list[str] = field(default_factory=list)
    emotional_expressions: dict[str, str] = field(default_factory=dict)

    # 関係性による変化
    relationship_modifiers: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass
class DialogueExchange:
    """対話交換"""

    exchange_id: str
    participants: list[str]
    primary_purpose: str  # "exposition", "conflict", "development", "emotion"

    # 構造
    opening_line: str = ""
    key_exchanges: list[dict[str, str]] = field(default_factory=list)
    closing_beat: str = ""

    # 技術的要素
    subtext_level: str = "medium"  # "low", "medium", "high"
    tension_progression: list[int] = field(default_factory=list)  # 1-10スケール
    emotional_arc: list[str] = field(default_factory=list)

    # 制約
    estimated_word_count: int = 200
    max_lines_per_character: int = 5


@dataclass
class DialogueScene:
    """対話シーン"""

    scene_id: str
    scene_context: str
    participants: list[str]

    # 対話構成
    dialogue_exchanges: list[DialogueExchange] = field(default_factory=list)
    narrative_beats: list[str] = field(default_factory=list)  # 地の文での間

    # 技術的設定
    dialogue_ratio: float = 0.6  # シーン内での対話の割合
    pacing: str = "medium"  # "fast", "medium", "slow"
    atmosphere: str = "neutral"  # "tense", "relaxed", "emotional"


@dataclass
class DialogueDesignResult:
    """対話設計結果"""

    episode_number: int
    design_confidence: float = 0.0

    # キャラクター音声
    character_voices: list[CharacterVoice] = field(default_factory=list)

    # 対話シーン
    dialogue_scenes: list[DialogueScene] = field(default_factory=list)

    # 実装ガイダンス
    writing_guidelines: list[str] = field(default_factory=list)
    dialogue_techniques: list[str] = field(default_factory=list)
    consistency_points: list[str] = field(default_factory=list)


@dataclass
class DialogueDesignerResponse(WritingStepResponse):
    """対話設計サービス結果"""

    dialogue_result: DialogueDesignResult | None = None

    # パフォーマンス情報
    voice_design_time_ms: float = 0.0
    exchange_planning_time_ms: float = 0.0
    scene_integration_time_ms: float = 0.0

    # 統計情報
    characters_voiced: int = 0
    exchanges_planned: int = 0
    dialogue_scenes_created: int = 0


class DialogueDesignerService(BaseWritingStep):
    """STEP 5: 対話設計マイクロサービス

    キャラクター固有の音声特性を設計し、
    シーン内の対話構成を最適化する。
    """

    def __init__(
        self,
        logger_service: ILoggerService = None,
        **kwargs: Any
    ) -> None:
        """対話設計サービス初期化"""
        super().__init__(step_number=5, step_name="dialogue_designer", **kwargs)

        self._logger_service = logger_service

    async def execute(
        self,
        episode_number: int,
        previous_results: dict[int, Any] | None = None
    ) -> DialogueDesignerResponse:
        """対話設計実行"""
        start_time = time.time()

        try:
            if self._logger_service:
                self._logger_service.info(f"STEP 5 対話設計開始: エピソード={episode_number}")

            # 1. 前ステップから設計情報取得
            scene_plan, context_result = self._extract_design_context(previous_results)

            # 2. キャラクター音声設計
            voice_start = time.time()
            character_voices = await self._design_character_voices(
                context_result, scene_plan
            )
            voice_time = (time.time() - voice_start) * 1000

            # 3. 対話交換計画
            exchange_start = time.time()
            dialogue_exchanges = await self._plan_dialogue_exchanges(
                scene_plan, character_voices, context_result
            )
            exchange_time = (time.time() - exchange_start) * 1000

            # 4. シーン統合
            integration_start = time.time()
            dialogue_scenes = await self._integrate_dialogue_scenes(
                scene_plan, dialogue_exchanges, character_voices
            )
            integration_time = (time.time() - integration_start) * 1000

            # 5. 実装ガイダンス生成
            guidelines, techniques, consistency = self._generate_dialogue_guidance(
                character_voices, dialogue_scenes
            )

            # 6. 統合結果作成
            dialogue_result = DialogueDesignResult(
                episode_number=episode_number,
                design_confidence=self._calculate_design_confidence(
                    character_voices, dialogue_scenes
                ),
                character_voices=character_voices,
                dialogue_scenes=dialogue_scenes,
                writing_guidelines=guidelines,
                dialogue_techniques=techniques,
                consistency_points=consistency
            )

            # 7. 成功応答作成
            execution_time = (time.time() - start_time) * 1000

            return DialogueDesignerResponse(
                success=True,
                step_number=5,
                step_name="dialogue_designer",
                execution_time_ms=execution_time,
                dialogue_result=dialogue_result,

                # パフォーマンス情報
                voice_design_time_ms=voice_time,
                exchange_planning_time_ms=exchange_time,
                scene_integration_time_ms=integration_time,

                # 統計情報
                characters_voiced=len(character_voices),
                exchanges_planned=sum(len(scene.dialogue_exchanges)
                                    for scene in dialogue_scenes),
                dialogue_scenes_created=len(dialogue_scenes)
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_message = f"STEP 5 対話設計エラー: {e}"

            if self._logger_service:
                self._logger_service.error(error_message)

            return DialogueDesignerResponse(
                success=False,
                step_number=5,
                step_name="dialogue_designer",
                execution_time_ms=execution_time,
                error_message=error_message
            )

    def _extract_design_context(
        self,
        previous_results: dict[int, Any] | None
    ) -> tuple[Any | None, Any | None]:
        """設計コンテキスト抽出"""
        scene_plan = None
        context_result = None

        if previous_results:
            # STEP 4からシーン設計
            if 4 in previous_results:
                step4_result = previous_results[4]
                if hasattr(step4_result, "design_plan"):
                    scene_plan = step4_result.design_plan

            # STEP 2からコンテキスト
            if 2 in previous_results:
                step2_result = previous_results[2]
                if hasattr(step2_result, "context_result"):
                    context_result = step2_result.context_result

        return scene_plan, context_result

    async def _design_character_voices(
        self,
        context_result: Any | None,
        scene_plan: Any | None
    ) -> list[CharacterVoice]:
        """キャラクター音声設計"""
        character_voices = []

        # コンテキストからキャラクター情報取得
        character_contexts = []
        if context_result and hasattr(context_result, "character_contexts"):
            character_contexts = context_result.character_contexts

        # シーン設計から参加キャラクター取得
        involved_characters = set()
        if scene_plan and hasattr(scene_plan, "scene_blocks"):
            for block in scene_plan.scene_blocks:
                if hasattr(block, "characters_present"):
                    involved_characters.update(block.characters_present)

        # 各キャラクターの音声設計
        for char_context in character_contexts:
            if char_context.character_name in involved_characters:
                voice = await self._create_character_voice(char_context)
                character_voices.append(voice)

        # 不足キャラクターの基本音声作成
        for char_name in involved_characters:
            if not any(voice.character_name == char_name for voice in character_voices):
                basic_voice = self._create_basic_voice(char_name)
                character_voices.append(basic_voice)

        return character_voices

    async def _create_character_voice(self, char_context: Any) -> CharacterVoice:
        """個別キャラクター音声作成"""
        char_name = char_context.character_name
        role = getattr(char_context, "role", "supporting")

        # 役割による基本特性
        voice_settings = self._get_voice_settings_by_role(role)

        # 背景による調整
        background = getattr(char_context, "background_elements", [])
        if background:
            voice_settings = self._adjust_voice_by_background(voice_settings, background)

        # 関係性による変化設定
        relationships = getattr(char_context, "relationships", {})
        relationship_modifiers = {}
        for other_char, relationship in relationships.items():
            relationship_modifiers[other_char] = self._create_relationship_modifier(relationship)

        return CharacterVoice(
            character_name=char_name,
            speaking_style=voice_settings["style"],
            vocabulary_level=voice_settings["vocabulary"],
            sentence_structure=voice_settings["structure"],
            catchphrases=voice_settings.get("catchphrases", []),
            speech_patterns=voice_settings.get("patterns", []),
            emotional_expressions=voice_settings.get("emotions", {}),
            relationship_modifiers=relationship_modifiers
        )

    def _get_voice_settings_by_role(self, role: str) -> dict[str, Any]:
        """役割別音声設定"""
        settings = {
            "protagonist": {
                "style": "casual",
                "vocabulary": "standard",
                "structure": "varied",
                "patterns": ["感情豊かな表現", "決意を示す語調"],
                "emotions": {
                    "determination": "きっと〜するんだ",
                    "surprise": "え？本当に？"
                }
            },
            "antagonist": {
                "style": "formal",
                "vocabulary": "advanced",
                "structure": "long",
                "patterns": ["威圧的な語調", "皮肉な表現"],
                "emotions": {
                    "anger": "ふざけるな",
                    "mockery": "馬鹿らしい"
                }
            },
            "supporting": {
                "style": "casual",
                "vocabulary": "standard",
                "structure": "medium",
                "patterns": ["親しみやすい語調"],
                "emotions": {
                    "concern": "大丈夫？",
                    "encouragement": "頑張って"
                }
            }
        }

        return settings.get(role, settings["supporting"])

    def _adjust_voice_by_background(
        self,
        voice_settings: dict[str, Any],
        background: list[str]
    ) -> dict[str, Any]:
        """背景による音声調整"""
        # 教養・職業による調整
        if any("学者" in bg or "教師" in bg for bg in background):
            voice_settings["vocabulary"] = "advanced"
            voice_settings["structure"] = "long"
        elif any("職人" in bg or "商人" in bg for bg in background):
            voice_settings["style"] = "practical"
            voice_settings["patterns"].append("実用的な表現")
        elif any("貴族" in bg or "王族" in bg for bg in background):
            voice_settings["style"] = "formal"
            voice_settings["vocabulary"] = "eloquent"

        return voice_settings

    def _create_relationship_modifier(self, relationship: str) -> dict[str, str]:
        """関係性修正子作成"""
        modifiers = {
            "親友": {"style": "casual", "tone": "intimate"},
            "恋人": {"style": "gentle", "tone": "affectionate"},
            "敵対": {"style": "cold", "tone": "hostile"},
            "師匠": {"style": "respectful", "tone": "formal"},
            "部下": {"style": "authoritative", "tone": "commanding"}
        }

        return modifiers.get(relationship, {"style": "neutral", "tone": "standard"})

    def _create_basic_voice(self, char_name: str) -> CharacterVoice:
        """基本音声作成（情報不足キャラクター用）"""
        return CharacterVoice(
            character_name=char_name,
            speaking_style="casual",
            vocabulary_level="standard",
            sentence_structure="medium"
        )

    async def _plan_dialogue_exchanges(
        self,
        scene_plan: Any | None,
        character_voices: list[CharacterVoice],
        context_result: Any | None
    ) -> list[DialogueExchange]:
        """対話交換計画"""
        exchanges = []

        if not scene_plan or not hasattr(scene_plan, "scene_blocks"):
            return exchanges

        # 各シーンブロックの対話計画
        for i, block in enumerate(scene_plan.scene_blocks):
            if not hasattr(block, "characters_present") or len(block.characters_present) < 2:
                continue

            # 対話が重要なシーンかチェック
            dialogue_ratio = getattr(block, "dialogue_ratio", 0.3)
            if dialogue_ratio < 0.3:
                continue

            # 対話交換作成
            exchange = await self._create_dialogue_exchange(
                f"exchange_{i+1:02d}",
                block,
                character_voices,
                context_result
            )

            if exchange:
                exchanges.append(exchange)

        return exchanges

    async def _create_dialogue_exchange(
        self,
        exchange_id: str,
        scene_block: Any,
        character_voices: list[CharacterVoice],
        context_result: Any | None
    ) -> DialogueExchange | None:
        """個別対話交換作成"""
        participants = getattr(scene_block, "characters_present", [])
        if len(participants) < 2:
            return None

        # 対話の目的決定
        purpose = self._determine_dialogue_purpose(scene_block, context_result)

        # 推定文字数
        estimated_words = int(getattr(scene_block, "estimated_word_count", 800) *
                            getattr(scene_block, "dialogue_ratio", 0.3))

        # キー交換設計
        key_exchanges = self._design_key_exchanges(
            participants, purpose, character_voices
        )

        # 緊張進行
        tension_level = getattr(scene_block, "tension_level", 5)
        tension_progression = self._design_tension_progression(
            len(key_exchanges), tension_level
        )

        return DialogueExchange(
            exchange_id=exchange_id,
            participants=participants,
            primary_purpose=purpose,
            key_exchanges=key_exchanges,
            estimated_word_count=estimated_words,
            tension_progression=tension_progression,
            emotional_arc=self._determine_emotional_arc(purpose)
        )

    def _determine_dialogue_purpose(
        self,
        scene_block: Any,
        context_result: Any | None
    ) -> str:
        """対話目的決定"""
        primary_purpose = getattr(scene_block, "primary_purpose", "development")

        purpose_mapping = {
            "exposition": "exposition",
            "conflict": "conflict",
            "climax": "conflict",
            "development": "development",
            "resolution": "emotion"
        }

        return purpose_mapping.get(primary_purpose, "development")

    def _design_key_exchanges(
        self,
        participants: list[str],
        purpose: str,
        character_voices: list[CharacterVoice]
    ) -> list[dict[str, str]]:
        """キー交換設計"""
        exchanges = []

        # 目的別交換パターン
        if purpose == "exposition":
            exchanges = [
                {"speaker": participants[0], "content": "状況説明・情報提示"},
                {"speaker": participants[1], "content": "質問・確認"},
                {"speaker": participants[0], "content": "詳細説明・補足"}
            ]
        elif purpose == "conflict":
            exchanges = [
                {"speaker": participants[0], "content": "問題提起・異議"},
                {"speaker": participants[1], "content": "反論・対立"},
                {"speaker": participants[0], "content": "立場明確化"},
                {"speaker": participants[1], "content": "最終的応答"}
            ]
        elif purpose == "development":
            exchanges = [
                {"speaker": participants[0], "content": "提案・意見"},
                {"speaker": participants[1], "content": "反応・検討"},
                {"speaker": participants[0], "content": "展開・発展"}
            ]
        else:  # emotion
            exchanges = [
                {"speaker": participants[0], "content": "感情表現・心情吐露"},
                {"speaker": participants[1], "content": "共感・理解"},
                {"speaker": participants[0], "content": "感謝・絆深化"}
            ]

        return exchanges

    def _design_tension_progression(
        self,
        exchange_count: int,
        base_tension: int
    ) -> list[int]:
        """緊張進行設計"""
        progression = []

        for i in range(exchange_count):
            # 基本的な緊張カーブ
            if i == 0:
                level = base_tension - 1
            elif i == exchange_count - 1:
                level = base_tension + 1
            else:
                level = base_tension + (i - 1)

            progression.append(max(1, min(10, level)))

        return progression

    def _determine_emotional_arc(self, purpose: str) -> list[str]:
        """感情アーク決定"""
        arcs = {
            "exposition": ["curiosity", "understanding", "acceptance"],
            "conflict": ["tension", "escalation", "climax"],
            "development": ["interest", "engagement", "progress"],
            "emotion": ["vulnerability", "connection", "resolution"]
        }

        return arcs.get(purpose, ["neutral", "engagement", "closure"])

    async def _integrate_dialogue_scenes(
        self,
        scene_plan: Any | None,
        dialogue_exchanges: list[DialogueExchange],
        character_voices: list[CharacterVoice]
    ) -> list[DialogueScene]:
        """対話シーン統合"""
        dialogue_scenes = []

        if not scene_plan or not hasattr(scene_plan, "scene_blocks"):
            return dialogue_scenes

        # 各シーンブロックを対話シーンに変換
        exchange_index = 0
        for i, block in enumerate(scene_plan.scene_blocks):
            # 対話比率チェック
            dialogue_ratio = getattr(block, "dialogue_ratio", 0.0)
            if dialogue_ratio < 0.2:
                continue

            scene_id = f"dialogue_scene_{i+1:02d}"
            participants = getattr(block, "characters_present", [])

            # 対応する交換を探索
            scene_exchanges = []
            if exchange_index < len(dialogue_exchanges):
                exchange = dialogue_exchanges[exchange_index]
                if set(exchange.participants).issubset(set(participants)):
                    scene_exchanges.append(exchange)
                    exchange_index += 1

            # 対話シーン作成
            dialogue_scene = DialogueScene(
                scene_id=scene_id,
                scene_context=getattr(block, "primary_purpose", "development"),
                participants=participants,
                dialogue_exchanges=scene_exchanges,
                narrative_beats=self._generate_narrative_beats(block),
                dialogue_ratio=dialogue_ratio,
                pacing=self._determine_scene_pacing(block),
                atmosphere=getattr(block, "emotional_tone", "neutral")
            )

            dialogue_scenes.append(dialogue_scene)

        return dialogue_scenes

    def _generate_narrative_beats(self, scene_block: Any) -> list[str]:
        """地の文ビート生成"""
        beats = []

        # シーン設定による地の文
        location = getattr(scene_block, "location", "")
        if location:
            beats.append(f"場面設定: {location}")

        # 感情・動作の地の文
        emotional_tone = getattr(scene_block, "emotional_tone", "")
        if emotional_tone:
            beats.append(f"雰囲気描写: {emotional_tone}")

        # アクション比率による動作描写
        action_ratio = getattr(scene_block, "action_ratio", 0.0)
        if action_ratio > 0.2:
            beats.append("動作・行動描写")

        return beats

    def _determine_scene_pacing(self, scene_block: Any) -> str:
        """シーンペーシング決定"""
        tension_level = getattr(scene_block, "tension_level", 5)

        if tension_level >= 8:
            return "fast"
        if tension_level <= 3:
            return "slow"
        return "medium"

    def _generate_dialogue_guidance(
        self,
        character_voices: list[CharacterVoice],
        dialogue_scenes: list[DialogueScene]
    ) -> tuple[list[str], list[str], list[str]]:
        """対話ガイダンス生成"""
        guidelines = []
        techniques = []
        consistency = []

        # 基本ガイドライン
        guidelines.extend([
            "各キャラクターの固有音声を維持",
            "対話と地の文のバランス調整",
            "緊張レベルに応じた対話設計"
        ])

        # 技術的手法
        techniques.extend([
            "サブテキストの活用",
            "対話による情報提示",
            "感情表現の多様化",
            "関係性による語調変化"
        ])

        # 一貫性チェック
        consistency.extend([
            "キャラクター固有の語彙・語調維持",
            "関係性に応じた対話スタイル",
            "感情状態と対話内容の整合性"
        ])

        return guidelines, techniques, consistency

    def _calculate_design_confidence(
        self,
        character_voices: list[CharacterVoice],
        dialogue_scenes: list[DialogueScene]
    ) -> float:
        """設計信頼度計算"""
        confidence = 0.0

        # キャラクター音声設計の完成度
        if character_voices:
            confidence += 0.4

        # 対話シーンの設計度
        if dialogue_scenes:
            confidence += 0.6

            # 詳細設計度
            detailed_scenes = sum(1 for scene in dialogue_scenes
                                if scene.dialogue_exchanges)
            if detailed_scenes > 0:
                confidence += 0.3 * (detailed_scenes / len(dialogue_scenes))

        return min(1.0, confidence)
