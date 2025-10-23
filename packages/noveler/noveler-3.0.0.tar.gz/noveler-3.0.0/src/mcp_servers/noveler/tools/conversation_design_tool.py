#!/usr/bin/env python3
"""会話設計ツール（STEP7-11対応）

A38執筆プロンプトガイドのSTEP7-11を実装するMCPツール。
会話ID体系を使用して、会話設計から感情曲線、環境設定まで統合的に管理。
"""

from typing import Any

from noveler.domain.services.conversation_design_service import (
    ConversationDesignService,
    EmotionPoint,
    PropLifecycle,
    SceneSetting,
    SensoryTrigger,
)
from noveler.domain.value_objects.conversation_id import (
    ConversationID,
    DialogueEntry,
)
from noveler.infrastructure.factories.path_service_factory import create_path_service


class ConversationDesignTool:
    """会話設計ツール（STEP7-11統合管理）"""

    def __init__(self) -> None:
        """初期化"""
        self.service = ConversationDesignService()
        self.path_service = create_path_service()

    def design_conversations(self, episode_number: int, scene_number: int, dialogues: list[dict[str, Any]]) -> dict[str, Any]:
        """STEP7: 会話設計

        Args:
            episode_number: エピソード番号
            scene_number: シーン番号
            dialogues: 会話データのリスト
                - sequence: 表示順序（10刻み）
                - speaker: 発話者
                - text: 台詞内容
                - purpose: 会話の目的（オプション）
                - trigger_id: トリガーとなった会話ID（オプション）

        Returns:
            設計結果
        """
        scene_id = f"EP{episode_number:03d}_SC{scene_number:02d}"

        # 会話エントリを作成
        dialogue_number = 1
        for dialogue_data in dialogues:
            # 会話IDを生成
            conversation_id = ConversationID(episode_number, scene_number, dialogue_number)

            # トリガーIDの処理
            trigger_id = None
            if dialogue_data.get("trigger_id"):
                trigger_parts = dialogue_data["trigger_id"].split("-")
                if len(trigger_parts) == 3:
                    trigger_id = ConversationID.from_string(dialogue_data["trigger_id"])

            # 会話エントリを作成
            dialogue = DialogueEntry(
                conversation_id=conversation_id,
                sequence=dialogue_data.get("sequence", dialogue_number * 10),
                speaker=dialogue_data["speaker"],
                text=dialogue_data["text"],
                trigger_id=trigger_id,
                purpose=dialogue_data.get("purpose"),
                emotion_state=dialogue_data.get("emotion_state"),
            )

            # サービスに追加
            self.service.add_dialogue_entry(scene_id, dialogue)
            dialogue_number += 1

        # 結果を返す
        scene = self.service.conversation_scenes.get(scene_id)
        if scene:
            return {
                "status": "success",
                "scene_id": scene_id,
                "dialogue_count": len(scene.dialogues),
                "dialogue_range": {
                    "start": str(scene.dialogues[0].conversation_id) if scene.dialogues else None,
                    "end": str(scene.dialogues[-1].conversation_id) if scene.dialogues else None,
                },
                "dialogues": [
                    {
                        "conversation_id": str(d.conversation_id),
                        "sequence": d.sequence,
                        "speaker": d.speaker,
                        "text": d.text,
                        "purpose": d.purpose,
                    }
                    for d in scene.dialogues
                ],
            }

        return {"status": "error", "message": "シーン作成に失敗しました"}

    def track_emotions(self, emotions: list[dict[str, Any]]) -> dict[str, Any]:
        """STEP8: 感情曲線追跡

        Args:
            emotions: 感情データのリスト
                - trigger_id: トリガー会話ID（EP001-SC01-DL001形式）
                - viewpoint: 視点キャラクター
                - target_character: 対象キャラクター
                - observation_type: 観察タイプ（internal/external/omniscient）
                - before_level: 会話前の感情レベル（1-10）
                - after_level: 会話後の感情レベル（1-10）
                - emotion_type: 感情の種類
                - expression: 感情表現の詳細

        Returns:
            追跡結果
        """
        for emotion_data in emotions:
            # 会話IDを解析
            trigger_id = ConversationID.from_string(emotion_data["trigger_id"])

            # 感情ポイントを作成
            emotion_point = EmotionPoint(
                trigger_id=trigger_id,
                viewpoint=emotion_data["viewpoint"],
                target_character=emotion_data["target_character"],
                observation_type=emotion_data["observation_type"],
                before_level=emotion_data["before_level"],
                after_level=emotion_data["after_level"],
                emotion_type=emotion_data["emotion_type"],
                expression=emotion_data.get("expression", {}),
            )

            # サービスに追加
            self.service.track_emotion(emotion_point)

        return {
            "status": "success",
            "emotion_count": len(self.service.emotion_points),
            "emotions_tracked": len(emotions),
        }

    def design_scenes(self, scenes: list[dict[str, Any]]) -> dict[str, Any]:
        """STEP9: 情景設計

        Args:
            scenes: 情景データのリスト
                - scene_id: シーンID
                - location: 場所
                - sub_location: 詳細位置（オプション）
                - dialogue_range_start: 開始会話ID
                - dialogue_range_end: 終了会話ID
                - location_transitions: 場所移動リスト
                - temporal_tracking: 時系列管理リスト
                - atmospheric_design: 環境演出リスト

        Returns:
            設計結果
        """
        for scene_data in scenes:
            # 会話IDレンジを解析
            dialogue_range = ()
            if scene_data.get("dialogue_range_start") and scene_data.get("dialogue_range_end"):
                start_id = ConversationID.from_string(scene_data["dialogue_range_start"])
                end_id = ConversationID.from_string(scene_data["dialogue_range_end"])
                dialogue_range = (start_id, end_id)

            # 情景設定を作成
            scene_setting = SceneSetting(
                scene_id=scene_data["scene_id"],
                location=scene_data["location"],
                sub_location=scene_data.get("sub_location"),
                dialogue_range=dialogue_range,
                location_transitions=scene_data.get("location_transitions", []),
                temporal_tracking=scene_data.get("temporal_tracking", []),
                atmospheric_design=scene_data.get("atmospheric_design", []),
            )

            # サービスに登録
            self.service.set_scene_setting(scene_data["scene_id"], scene_setting)

        return {
            "status": "success",
            "scene_count": len(self.service.scene_settings),
            "scenes_designed": len(scenes),
        }

    def design_senses(self, triggers: list[dict[str, Any]]) -> dict[str, Any]:
        """STEP10: 五感描写設計

        Args:
            triggers: 感覚トリガーデータのリスト
                - trigger_id: トリガー会話ID
                - sense_type: 感覚の種類（視覚/聴覚/触覚/嗅覚/味覚）
                - description: 感覚の説明
                - intensity: 強度（1-10）
                - timing: タイミング（before/during/after）
                - purpose: 目的
                - linked_emotion: 連動する感情（オプション）
                - character_reaction: キャラクターの反応（オプション）

        Returns:
            設計結果
        """
        for trigger_data in triggers:
            # 会話IDを解析
            trigger_id = ConversationID.from_string(trigger_data["trigger_id"])

            # 感覚トリガーを作成
            sensory_trigger = SensoryTrigger(
                trigger_id=trigger_id,
                sense_type=trigger_data["sense_type"],
                description=trigger_data["description"],
                intensity=trigger_data["intensity"],
                timing=trigger_data["timing"],
                purpose=trigger_data["purpose"],
                linked_emotion=trigger_data.get("linked_emotion"),
                character_reaction=trigger_data.get("character_reaction"),
            )

            # サービスに追加
            self.service.add_sensory_trigger(sensory_trigger)

        return {
            "status": "success",
            "trigger_count": len(self.service.sensory_triggers),
            "triggers_added": len(triggers),
        }

    def manage_props(self, props: list[dict[str, Any]]) -> dict[str, Any]:
        """STEP11: 小道具・世界観設計

        Args:
            props: 小道具データのリスト
                - prop_id: 小道具ID
                - name: 小道具名
                - introduced: 初登場の会話ID（オプション）
                - mentioned: 言及された会話IDリスト
                - focused: 焦点化された会話ID（オプション）
                - used: 使用された会話ID（オプション）
                - stored: 保管された会話ID（オプション）
                - emotional_states: 感情状態マップ
                - significance_evolution: 意味の変化リスト

        Returns:
            管理結果
        """
        for prop_data in props:
            # 会話IDを解析
            introduced = None
            if prop_data.get("introduced"):
                introduced = ConversationID.from_string(prop_data["introduced"])

            mentioned = [
                ConversationID.from_string(mention_id)
                for mention_id in prop_data.get("mentioned", [])
            ]

            focused = None
            if prop_data.get("focused"):
                focused = ConversationID.from_string(prop_data["focused"])

            used = None
            if prop_data.get("used"):
                used = ConversationID.from_string(prop_data["used"])

            stored = None
            if prop_data.get("stored"):
                stored = ConversationID.from_string(prop_data["stored"])

            # 小道具ライフサイクルを作成
            prop_lifecycle = PropLifecycle(
                prop_id=prop_data["prop_id"],
                name=prop_data["name"],
                introduced=introduced,
                mentioned=mentioned,
                focused=focused,
                used=used,
                stored=stored,
                emotional_states=prop_data.get("emotional_states", {}),
                significance_evolution=prop_data.get("significance_evolution", []),
            )

            # サービスに登録
            self.service.register_prop(prop_data["prop_id"], prop_lifecycle)

        return {
            "status": "success",
            "prop_count": len(self.service.props),
            "props_registered": len(props),
        }

    def get_conversation_context(self, conversation_id: str) -> dict[str, Any]:
        """特定の会話IDに関連する全コンテキストを取得

        Args:
            conversation_id: 会話ID（EP001-SC01-DL001形式）

        Returns:
            コンテキスト情報
        """
        # 会話IDを解析
        conv_id = ConversationID.from_string(conversation_id)

        # 関連情報を収集
        emotions = self.service.get_emotion_for_dialogue(conv_id)
        sensory = self.service.get_sensory_for_dialogue(conv_id)
        props = self.service.get_props_for_dialogue(conv_id)

        return {
            "conversation_id": conversation_id,
            "emotions": [
                {
                    "viewpoint": e.viewpoint,
                    "target": e.target_character,
                    "type": e.observation_type,
                    "before": e.before_level,
                    "after": e.after_level,
                    "emotion": e.emotion_type,
                }
                for e in emotions
            ],
            "sensory": [
                {
                    "sense": s.sense_type,
                    "description": s.description,
                    "intensity": s.intensity,
                    "timing": s.timing,
                }
                for s in sensory
            ],
            "props": [
                {
                    "id": p.prop_id,
                    "name": p.name,
                    "role": self._get_prop_role(p, conv_id),
                }
                for p in props
            ],
        }

    def _get_prop_role(self, prop: PropLifecycle, conversation_id: ConversationID) -> str:
        """小道具の役割を判定"""
        if prop.introduced == conversation_id:
            return "introduced"
        if conversation_id in prop.mentioned:
            return "mentioned"
        if prop.focused == conversation_id:
            return "focused"
        if prop.used == conversation_id:
            return "used"
        if prop.stored == conversation_id:
            return "stored"
        return "related"

    def export_design_data(self, episode_number: int) -> dict[str, Any]:
        """エピソードの設計データをエクスポート

        Args:
            episode_number: エピソード番号

        Returns:
            エクスポートデータ
        """
        # YAMLエクスポート用のデータを取得
        export_data = self.service.export_to_yaml()

        # エピソード番号でフィルタリング
        filtered_data = {
            "episode_number": episode_number,
            "conversation_scenes": {},
            "emotion_points": [],
            "scene_settings": {},
            "sensory_triggers": [],
            "props": export_data.get("props", {}),
        }

        # 該当エピソードのデータのみを抽出
        for scene_id, scene in export_data.get("conversation_scenes", {}).items():
            if scene["episode_number"] == episode_number:
                filtered_data["conversation_scenes"][scene_id] = scene

        for emotion in export_data.get("emotion_points", []):
            if emotion["trigger_id"].startswith(f"EP{episode_number:03d}"):
                filtered_data["emotion_points"].append(emotion)

        for scene_id, setting in export_data.get("scene_settings", {}).items():
            if scene_id.startswith(f"EP{episode_number:03d}"):
                filtered_data["scene_settings"][scene_id] = setting

        for trigger in export_data.get("sensory_triggers", []):
            if trigger["trigger_id"].startswith(f"EP{episode_number:03d}"):
                filtered_data["sensory_triggers"].append(trigger)

        return filtered_data


# MCPツールとして登録される関数
def design_conversations_tool(episode_number: int, scene_number: int, dialogues: list[dict[str, Any]]) -> dict[str, Any]:
    """STEP7: 会話設計MCPツール"""
    tool = ConversationDesignTool()
    return tool.design_conversations(episode_number, scene_number, dialogues)


def track_emotions_tool(emotions: list[dict[str, Any]]) -> dict[str, Any]:
    """STEP8: 感情曲線追跡MCPツール"""
    tool = ConversationDesignTool()
    return tool.track_emotions(emotions)


def design_scenes_tool(scenes: list[dict[str, Any]]) -> dict[str, Any]:
    """STEP9: 情景設計MCPツール"""
    tool = ConversationDesignTool()
    return tool.design_scenes(scenes)


def design_senses_tool(triggers: list[dict[str, Any]]) -> dict[str, Any]:
    """STEP10: 五感描写設計MCPツール"""
    tool = ConversationDesignTool()
    return tool.design_senses(triggers)


def manage_props_tool(props: list[dict[str, Any]]) -> dict[str, Any]:
    """STEP11: 小道具・世界観設計MCPツール"""
    tool = ConversationDesignTool()
    return tool.manage_props(props)


def get_conversation_context_tool(conversation_id: str) -> dict[str, Any]:
    """会話コンテキスト取得MCPツール"""
    tool = ConversationDesignTool()
    return tool.get_conversation_context(conversation_id)


def export_design_data_tool(episode_number: int) -> dict[str, Any]:
    """設計データエクスポートMCPツール"""
    tool = ConversationDesignTool()
    return tool.export_design_data(episode_number)
