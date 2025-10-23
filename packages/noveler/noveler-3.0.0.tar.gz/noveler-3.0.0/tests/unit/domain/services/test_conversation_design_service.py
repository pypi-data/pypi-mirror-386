#!/usr/bin/env python3
"""会話設計サービスのテストケース"""

import pytest
from unittest.mock import patch

from noveler.domain.services.conversation_design_service import (
    ConversationDesignService,
    EmotionPoint,
    PropLifecycle,
    SceneSetting,
    SensoryTrigger,
)
from noveler.domain.value_objects.conversation_id import ConversationID, DialogueEntry
from src.mcp_servers.noveler.tools.conversation_design_tool import ConversationDesignTool


class TestConversationDesignService:
    """ConversationDesignServiceのテストクラス"""

    @pytest.fixture
    def service(self):
        """テスト用サービスのフィクスチャ"""
        return ConversationDesignService()

    def test_create_conversation_id(self, service):
        """会話ID生成のテスト"""
        conv_id = service.create_conversation_id(1, 2, 3)
        assert conv_id.episode_number == 1
        assert conv_id.scene_number == 2
        assert conv_id.dialogue_number == 3
        assert str(conv_id) == "EP001-SC02-DL003"

    def test_add_dialogue_entry(self, service):
        """会話エントリ追加のテスト"""
        scene_id = "EP001_SC01"
        conv_id = ConversationID(1, 1, 1)
        dialogue = DialogueEntry(
            conversation_id=conv_id,
            sequence=10,
            speaker="主人公",
            text="こんにちは",
            purpose="挨拶",
        )

        # シーンが存在しない場合は自動作成される
        service.add_dialogue_entry(scene_id, dialogue)

        assert scene_id in service.conversation_scenes
        scene = service.conversation_scenes[scene_id]
        assert scene.episode_number == 1
        assert scene.scene_number == 1
        assert len(scene.dialogues) == 1
        assert scene.dialogues[0] == dialogue

    def test_track_emotion(self, service):
        """感情追跡のテスト"""
        trigger_id = ConversationID(1, 1, 1)
        emotion_point = EmotionPoint(
            trigger_id=trigger_id,
            viewpoint="主人公",
            target_character="ヒロイン",
            observation_type="external",
            before_level=3,
            after_level=7,
            emotion_type="喜び",
            expression={"顔": "微笑み", "動作": "手を振る"},
        )

        service.track_emotion(emotion_point)

        assert len(service.emotion_points) == 1
        assert service.emotion_points[0] == emotion_point

    def test_set_scene_setting(self, service):
        """情景設定のテスト"""
        scene_id = "EP001_SC01"
        start_id = ConversationID(1, 1, 1)
        end_id = ConversationID(1, 1, 10)

        setting = SceneSetting(
            scene_id=scene_id,
            location="学校の教室",
            sub_location="窓際の席",
            dialogue_range=(start_id, end_id),
            location_transitions=[
                {"conversation_id": "EP001-SC01-DL005", "to": "廊下"},
            ],
        )

        service.set_scene_setting(scene_id, setting)

        assert scene_id in service.scene_settings
        assert service.scene_settings[scene_id] == setting

    def test_add_sensory_trigger(self, service):
        """感覚トリガー追加のテスト"""
        trigger_id = ConversationID(1, 1, 3)
        sensory_trigger = SensoryTrigger(
            trigger_id=trigger_id,
            sense_type="視覚",
            description="夕日が教室に差し込む",
            intensity=7,
            timing="during",
            purpose="ロマンチックな雰囲気作り",
            linked_emotion="感動",
        )

        service.add_sensory_trigger(sensory_trigger)

        assert len(service.sensory_triggers) == 1
        assert service.sensory_triggers[0] == sensory_trigger

    def test_register_prop(self, service):
        """小道具登録のテスト"""
        prop_id = "PROP001"
        introduced_id = ConversationID(1, 1, 2)

        prop = PropLifecycle(
            prop_id=prop_id,
            name="古い手紙",
            introduced=introduced_id,
            mentioned=[ConversationID(1, 1, 5), ConversationID(1, 2, 1)],
            focused=ConversationID(1, 3, 10),
            emotional_states={"EP001-SC01-DL002": "懐かしさ"},
        )

        service.register_prop(prop_id, prop)

        assert prop_id in service.props
        assert service.props[prop_id] == prop

    def test_get_emotion_for_dialogue(self, service):
        """特定会話の感情ポイント取得テスト"""
        trigger_id1 = ConversationID(1, 1, 1)
        trigger_id2 = ConversationID(1, 1, 2)

        emotion1 = EmotionPoint(
            trigger_id=trigger_id1,
            viewpoint="主人公",
            target_character="ヒロイン",
            observation_type="external",
            before_level=3,
            after_level=5,
            emotion_type="興味",
        )

        emotion2 = EmotionPoint(
            trigger_id=trigger_id2,
            viewpoint="主人公",
            target_character="ヒロイン",
            observation_type="external",
            before_level=5,
            after_level=8,
            emotion_type="好意",
        )

        emotion3 = EmotionPoint(
            trigger_id=trigger_id1,
            viewpoint="ヒロイン",
            target_character="主人公",
            observation_type="internal",
            before_level=2,
            after_level=4,
            emotion_type="緊張",
        )

        service.track_emotion(emotion1)
        service.track_emotion(emotion2)
        service.track_emotion(emotion3)

        # trigger_id1に関連する感情のみ取得
        emotions = service.get_emotion_for_dialogue(trigger_id1)
        assert len(emotions) == 2
        assert emotion1 in emotions
        assert emotion3 in emotions
        assert emotion2 not in emotions

    @patch('src.mcp_servers.noveler.tools.conversation_design_tool.create_path_service')
    def test_export_design_data_filters_episode(self, mock_path_service, service):
        """designツールのエクスポートがエピソードでフィルタリングされるか検証"""

        class _DummyPathService:
            project_root = None

        mock_path_service.return_value = _DummyPathService()
        tool = ConversationDesignTool()
        tool.service = service

        # Episode 1 の会話と感情
        conv_id_ep1 = ConversationID(1, 1, 1)
        service.add_dialogue_entry(
            "EP001_SC01",
            DialogueEntry(
                conversation_id=conv_id_ep1,
                sequence=10,
                speaker="主人公",
                text="こんにちは",
            ),
        )
        service.track_emotion(
            EmotionPoint(
                trigger_id=conv_id_ep1,
                viewpoint="主人公",
                target_character="ヒロイン",
                observation_type="external",
                before_level=3,
                after_level=5,
                emotion_type="興味",
            )
        )

        # Episode 2 のダミーデータ
        conv_id_ep2 = ConversationID(2, 1, 1)
        service.add_dialogue_entry(
            "EP002_SC01",
            DialogueEntry(
                conversation_id=conv_id_ep2,
                sequence=10,
                speaker="ライバル",
                text="邪魔するぞ",
            ),
        )
        service.track_emotion(
            EmotionPoint(
                trigger_id=conv_id_ep2,
                viewpoint="ライバル",
                target_character="主人公",
                observation_type="external",
                before_level=4,
                after_level=2,
                emotion_type="敵意",
            )
        )

        export = tool.export_design_data(1)

        assert export["episode_number"] == 1
        assert all(key.startswith("EP001") for key in export["conversation_scenes"].keys())
        assert all(entry["trigger_id"].startswith("EP001") for entry in export["emotion_points"])


    def test_get_sensory_for_dialogue(self, service):
        """特定会話の感覚トリガー取得テスト"""
        trigger_id = ConversationID(1, 1, 3)

        sensory1 = SensoryTrigger(
            trigger_id=trigger_id,
            sense_type="視覚",
            description="夕日",
            intensity=7,
            timing="during",
            purpose="雰囲気作り",
        )

        sensory2 = SensoryTrigger(
            trigger_id=trigger_id,
            sense_type="聴覚",
            description="鳥の鳴き声",
            intensity=3,
            timing="before",
            purpose="環境描写",
        )

        other_trigger = SensoryTrigger(
            trigger_id=ConversationID(1, 1, 5),
            sense_type="嗅覚",
            description="花の香り",
            intensity=5,
            timing="during",
            purpose="場所の特徴",
        )

        service.add_sensory_trigger(sensory1)
        service.add_sensory_trigger(sensory2)
        service.add_sensory_trigger(other_trigger)

        # trigger_idに関連するトリガーのみ取得
        triggers = service.get_sensory_for_dialogue(trigger_id)
        assert len(triggers) == 2
        assert sensory1 in triggers
        assert sensory2 in triggers
        assert other_trigger not in triggers

    def test_get_props_for_dialogue(self, service):
        """特定会話の小道具取得テスト"""
        conv_id = ConversationID(1, 1, 5)

        prop1 = PropLifecycle(
            prop_id="PROP001",
            name="手紙",
            introduced=conv_id,
        )

        prop2 = PropLifecycle(
            prop_id="PROP002",
            name="鍵",
            mentioned=[ConversationID(1, 1, 3), conv_id],
        )

        prop3 = PropLifecycle(
            prop_id="PROP003",
            name="写真",
            focused=conv_id,
        )

        prop4 = PropLifecycle(
            prop_id="PROP004",
            name="本",
            mentioned=[ConversationID(1, 1, 7)],
        )

        service.register_prop("PROP001", prop1)
        service.register_prop("PROP002", prop2)
        service.register_prop("PROP003", prop3)
        service.register_prop("PROP004", prop4)

        # conv_idに関連する小道具のみ取得
        props = service.get_props_for_dialogue(conv_id)
        assert len(props) == 3
        assert prop1 in props  # introduced
        assert prop2 in props  # mentioned
        assert prop3 in props  # focused
        assert prop4 not in props  # 関係なし

    def test_export_to_yaml(self, service):
        """YAML形式エクスポートのテスト"""
        # テストデータを設定
        scene_id = "EP001_SC01"
        conv_id = ConversationID(1, 1, 1)
        dialogue = DialogueEntry(
            conversation_id=conv_id,
            sequence=10,
            speaker="主人公",
            text="こんにちは",
        )
        service.add_dialogue_entry(scene_id, dialogue)

        emotion = EmotionPoint(
            trigger_id=conv_id,
            viewpoint="主人公",
            target_character="ヒロイン",
            observation_type="external",
            before_level=3,
            after_level=5,
            emotion_type="興味",
        )
        service.track_emotion(emotion)

        # エクスポート実行
        yaml_data = service.export_to_yaml()

        # 構造を確認
        assert "conversation_scenes" in yaml_data
        assert "emotion_points" in yaml_data
        assert "scene_settings" in yaml_data
        assert "sensory_triggers" in yaml_data
        assert "props" in yaml_data

        # 内容を確認
        assert scene_id in yaml_data["conversation_scenes"]
        scene_data = yaml_data["conversation_scenes"][scene_id]
        assert len(scene_data["dialogues"]) == 1
        assert scene_data["dialogues"][0]["conversation_id"] == "EP001-SC01-DL001"

        assert len(yaml_data["emotion_points"]) == 1
        assert yaml_data["emotion_points"][0]["trigger_id"] == "EP001-SC01-DL001"
