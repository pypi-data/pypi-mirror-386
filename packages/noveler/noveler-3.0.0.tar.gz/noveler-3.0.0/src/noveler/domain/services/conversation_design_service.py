"""会話設計サービス

A38執筆プロンプトガイドのSTEP7-11を実装するサービス。
会話ID体系を使用して、会話設計から感情曲線、環境設定まで統合的に管理。
"""

from dataclasses import dataclass, field
from typing import Any

from noveler.domain.value_objects.antagonist_personality import AntagonistPersonality
from noveler.domain.value_objects.approval_system import EpisodeApprovalSystem
from noveler.domain.value_objects.conversation_id import (
    ConversationID,
    ConversationScene,
    DialogueEntry,
)
from noveler.domain.value_objects.dialogue_patterns import (
    DialoguePatternLibrary,
    GenreRecognitionGapPattern,
    KnowledgeGapPattern,
)
from noveler.domain.value_objects.emotion_expression import EmotionExpression, EmotionExpressionLibrary


@dataclass
class EmotionPoint:
    """感情ポイント（STEP8用）

    Attributes:
        trigger_id: トリガーとなる会話ID
        viewpoint: 誰の視点から観察・感知
        target_character: 誰の感情を描写
        observation_type: external（他者観察）/internal（内面描写）/omniscient（全知視点）
        before_level: 会話前の感情レベル（1-10）
        after_level: 会話後の感情レベル（1-10）
        emotion_type: 感情の種類
        expression: 感情表現の詳細
    """

    trigger_id: ConversationID
    viewpoint: str
    target_character: str
    observation_type: str
    before_level: int
    after_level: int
    emotion_type: str
    expression: dict[str, str] = field(default_factory=dict)


@dataclass
class SceneSetting:
    """情景設定（STEP9用）

    Attributes:
        scene_id: シーンID
        location: 具体的な場所
        sub_location: 詳細位置
        dialogue_range: 会話IDの範囲
        location_transitions: 会話IDごとの場所移動
        temporal_tracking: 会話単位の時系列管理
        atmospheric_design: 会話IDベースの環境演出
    """

    scene_id: str
    location: str
    sub_location: str | None = None
    dialogue_range: tuple[ConversationID, ConversationID] = field(default_factory=lambda: (ConversationID(0, 0, 0), ConversationID(0, 0, 0)))
    location_transitions: list[dict[str, Any]] = field(default_factory=list)
    temporal_tracking: list[dict[str, Any]] = field(default_factory=list)
    atmospheric_design: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SensoryTrigger:
    """感覚トリガー（STEP10用）

    Attributes:
        trigger_id: トリガーとなる会話ID
        sense_type: 感覚の種類
        description: 感覚の説明
        intensity: 強度（1-10）
        timing: タイミング（before/during/after）
        purpose: 目的
        linked_emotion: 連動する感情
        character_reaction: キャラクターの反応
    """

    trigger_id: ConversationID
    sense_type: str
    description: str
    intensity: int
    timing: str
    purpose: str
    linked_emotion: str | None = None
    character_reaction: str | None = None


@dataclass
class PropLifecycle:
    """小道具ライフサイクル（STEP11用）

    Attributes:
        prop_id: 小道具ID
        name: 小道具名
        introduced: 初登場の会話ID
        mentioned: 言及された会話IDリスト
        focused: 焦点化された会話ID
        used: 実際に使用された会話ID
        stored: 片付け/保管された会話ID
        emotional_states: 会話IDごとの感情状態
        significance_evolution: 会話進行に応じた意味の変化
    """

    prop_id: str
    name: str
    introduced: ConversationID | None = None
    mentioned: list[ConversationID] = field(default_factory=list)
    focused: ConversationID | None = None
    used: ConversationID | None = None
    stored: ConversationID | None = None
    emotional_states: dict[str, str] = field(default_factory=dict)
    significance_evolution: list[dict[str, Any]] = field(default_factory=list)


class ConversationDesignService:
    """会話設計サービス（A38 v2.0対応）

    STEP7-11の会話設計から感情曲線、情景設計、五感描写、小道具管理まで統合管理
    """

    def __init__(self) -> None:
        """初期化"""
        # 基本データ
        self.conversation_scenes: dict[str, ConversationScene] = {}
        self.emotion_points: list[EmotionPoint] = []
        self.scene_settings: dict[str, SceneSetting] = {}
        self.sensory_triggers: list[SensoryTrigger] = []
        self.props: dict[str, PropLifecycle] = {}

        # v2.0 新システム
        self.approval_systems: dict[int, EpisodeApprovalSystem] = {}  # エピソード番号をキー
        self.antagonist_personalities: dict[str, AntagonistPersonality] = {}  # キャラクター名をキー
        self.emotion_expressions: EmotionExpressionLibrary = EmotionExpressionLibrary()
        self.dialogue_patterns: DialoguePatternLibrary = DialoguePatternLibrary()

    def create_conversation_id(self, episode_number: int, scene_number: int, dialogue_number: int) -> ConversationID:
        """会話IDを生成"""
        return ConversationID(episode_number, scene_number, dialogue_number)

    def add_dialogue_entry(self, scene_id: str, dialogue: DialogueEntry) -> None:
        """会話エントリを追加"""
        if scene_id not in self.conversation_scenes:
            # シーンが存在しない場合は自動作成
            self.conversation_scenes[scene_id] = ConversationScene(
                scene_id=scene_id,
                episode_number=dialogue.conversation_id.episode_number,
                scene_number=dialogue.conversation_id.scene_number
            )

        self.conversation_scenes[scene_id].add_dialogue(dialogue)

    def track_emotion(self, emotion_point: EmotionPoint) -> None:
        """感情ポイントを追跡"""
        self.emotion_points.append(emotion_point)

    def set_scene_setting(self, scene_id: str, setting: SceneSetting) -> None:
        """情景設定を設定"""
        self.scene_settings[scene_id] = setting

    def add_sensory_trigger(self, trigger: SensoryTrigger) -> None:
        """感覚トリガーを追加"""
        self.sensory_triggers.append(trigger)

    def register_prop(self, prop_id: str, prop: PropLifecycle) -> None:
        """小道具を登録"""
        self.props[prop_id] = prop

    def get_emotion_for_dialogue(self, conversation_id: ConversationID) -> list[EmotionPoint]:
        """特定会話IDに関連する感情ポイントを取得"""
        return [emotion for emotion in self.emotion_points
                if emotion.trigger_id == conversation_id]

    def get_sensory_for_dialogue(self, conversation_id: ConversationID) -> list[SensoryTrigger]:
        """特定会話IDに関連する感覚トリガーを取得"""
        return [trigger for trigger in self.sensory_triggers
                if trigger.trigger_id == conversation_id]

    def get_props_for_dialogue(self, conversation_id: ConversationID) -> list[PropLifecycle]:
        """特定会話IDに関連する小道具を取得"""
        related_props = []
        for prop in self.props.values():
            if (prop.introduced == conversation_id or conversation_id in prop.mentioned or conversation_id in (prop.focused, prop.used, prop.stored)):
                related_props.append(prop)
        return related_props

    # v2.0 新機能メソッド
    def set_episode_approval_system(self, episode_number: int, approval_system: EpisodeApprovalSystem) -> None:
        """エピソードの承認欲求システムを設定"""
        self.approval_systems[episode_number] = approval_system

    def add_antagonist_personality(self, character_name: str, personality: AntagonistPersonality) -> None:
        """敵キャラクター個性を追加"""
        self.antagonist_personalities[character_name] = personality

    def add_emotion_expression(self, emotion_type: str, expression: EmotionExpression) -> None:
        """感情表現を追加"""
        self.emotion_expressions.add_expression(emotion_type, str(expression))

    def add_dialogue_pattern(self, pattern_type: str, pattern: KnowledgeGapPattern | GenreRecognitionGapPattern) -> None:
        """会話パターンを追加"""
        pattern_data = {
            "pattern_id": getattr(pattern, "pattern_id", ""),
            "knowledge_holder": getattr(pattern, "knowledge_holder", ""),
            "naive_character": getattr(pattern, "naive_character", ""),
        }
        self.dialogue_patterns.add_pattern(pattern_type, pattern.pattern_id, pattern_data)

    def get_approval_system(self, episode_number: int) -> EpisodeApprovalSystem | None:
        """エピソードの承認欲求システムを取得"""
        return self.approval_systems.get(episode_number)

    def get_antagonist_personality(self, character_name: str) -> AntagonistPersonality | None:
        """敵キャラクター個性を取得"""
        return self.antagonist_personalities.get(character_name)

    def export_to_yaml(self) -> dict[str, Any]:
        """YAML出力用の辞書形式に変換"""
        # 基本システムのエクスポート
        data: dict[str, Any] = {
            "conversation_scenes": {},
            "emotion_points": [],
            "scene_settings": {},
            "sensory_triggers": [],
            "props": {}
        }

        # 会話シーンのエクスポート
        for scene_id, scene in self.conversation_scenes.items():
            data["conversation_scenes"][scene_id] = {
                "episode_number": scene.episode_number,
                "scene_number": scene.scene_number,
                "location": scene.location,
                "time": scene.time,
                "purpose": scene.purpose,
                "dialogues": [
                    {
                        "conversation_id": str(dialogue.conversation_id),
                        "sequence": dialogue.sequence,
                        "speaker": dialogue.speaker,
                        "text": dialogue.text,
                        "purpose": dialogue.purpose,
                        "trigger_id": str(dialogue.trigger_id) if dialogue.trigger_id else None,
                        "emotion_state": dialogue.emotion_state,
                        "is_deleted": dialogue.is_deleted
                    }
                    for dialogue in scene.dialogues
                ]
            }

        # 感情ポイントのエクスポート
        for emotion in self.emotion_points:
            data["emotion_points"].append({
                "trigger_id": str(emotion.trigger_id),
                "viewpoint": emotion.viewpoint,
                "target_character": emotion.target_character,
                "observation_type": emotion.observation_type,
                "before_level": emotion.before_level,
                "after_level": emotion.after_level,
                "emotion_type": emotion.emotion_type,
                "expression": emotion.expression
            })

        # 情景設定のエクスポート
        for scene_id, setting in self.scene_settings.items():
            data["scene_settings"][scene_id] = {
                "location": setting.location,
                "sub_location": setting.sub_location,
                "dialogue_range_start": str(setting.dialogue_range[0]) if setting.dialogue_range else None,
                "dialogue_range_end": str(setting.dialogue_range[1]) if setting.dialogue_range else None,
                "location_transitions": setting.location_transitions,
                "temporal_tracking": setting.temporal_tracking,
                "atmospheric_design": setting.atmospheric_design
            }

        # 感覚トリガーのエクスポート
        for trigger in self.sensory_triggers:
            data["sensory_triggers"].append({
                "trigger_id": str(trigger.trigger_id),
                "sense_type": trigger.sense_type,
                "description": trigger.description,
                "intensity": trigger.intensity,
                "timing": trigger.timing,
                "purpose": trigger.purpose,
                "linked_emotion": trigger.linked_emotion,
                "character_reaction": trigger.character_reaction
            })

        # 小道具のエクスポート
        for prop_id, prop in self.props.items():
            data["props"][prop_id] = {
                "name": prop.name,
                "introduced": str(prop.introduced) if prop.introduced else None,
                "mentioned": [str(conv_id) for conv_id in prop.mentioned],
                "focused": str(prop.focused) if prop.focused else None,
                "used": str(prop.used) if prop.used else None,
                "stored": str(prop.stored) if prop.stored else None,
                "emotional_states": prop.emotional_states,
                "significance_evolution": prop.significance_evolution
            }

        # v2.0 新システムのエクスポート
        if self.approval_systems:
            data["approval_systems"] = {
                episode_num: system.export_to_yaml_dict()
                for episode_num, system in self.approval_systems.items()
            }

        if self.antagonist_personalities:
            data["antagonist_personalities"] = {
                char_name: personality.export_to_yaml_dict()
                for char_name, personality in self.antagonist_personalities.items()
            }

        if hasattr(self.emotion_expressions, "golden_expressions") and self.emotion_expressions.golden_expressions:
            data["emotion_expressions"] = {
                "golden_patterns": self.emotion_expressions.golden_expressions,
                "forbidden_expressions": self.emotion_expressions.forbidden_expressions
            }

        if hasattr(self.dialogue_patterns, "knowledge_gap_patterns") and self.dialogue_patterns.knowledge_gap_patterns:
            data["dialogue_patterns"] = self.dialogue_patterns.generate_pattern_usage_stats()

        return data
