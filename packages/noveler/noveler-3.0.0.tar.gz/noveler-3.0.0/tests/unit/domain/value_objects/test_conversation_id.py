#!/usr/bin/env python3
"""会話IDのテストケース"""

import pytest

from noveler.domain.value_objects.conversation_id import (
    ConversationID,
    ConversationScene,
    DialogueEntry,
)


pytestmark = pytest.mark.vo_smoke


class TestConversationID:
    """ConversationIDのテストクラス"""

    def test_create_conversation_id(self):
        """会話IDの作成テスト"""
        # 正常ケース
        conv_id = ConversationID(1, 1, 1)
        assert conv_id.episode_number == 1
        assert conv_id.scene_number == 1
        assert conv_id.dialogue_number == 1

    def test_conversation_id_string_format(self):
        """会話IDの文字列フォーマットテスト"""
        conv_id = ConversationID(1, 2, 3)
        assert str(conv_id) == "EP001-SC02-DL003"

    def test_conversation_id_from_string(self):
        """文字列から会話IDを作成するテスト"""
        # 正常ケース
        conv_id = ConversationID.from_string("EP001-SC02-DL003")
        assert conv_id.episode_number == 1
        assert conv_id.scene_number == 2
        assert conv_id.dialogue_number == 3

    def test_conversation_id_from_invalid_string(self):
        """無効な文字列からの会話ID作成テスト"""
        # フォーマットエラー
        with pytest.raises(ValueError):
            ConversationID.from_string("EP001-SC02")

        with pytest.raises(ValueError):
            ConversationID.from_string("INVALID")

        with pytest.raises(ValueError):
            ConversationID.from_string("EP001-SCXX-DL003")

    def test_conversation_id_immutability(self):
        """会話IDの不変性テスト"""
        conv_id = ConversationID(1, 1, 1)

        # frozen=Trueのため、属性の変更はできない
        with pytest.raises(AttributeError):
            conv_id.episode_number = 2


class TestDialogueEntry:
    """DialogueEntryのテストクラス"""

    def test_create_dialogue_entry(self):
        """会話エントリの作成テスト"""
        conv_id = ConversationID(1, 1, 1)
        dialogue = DialogueEntry(
            conversation_id=conv_id,
            sequence=10,
            speaker="主人公",
            text="こんにちは",
            purpose="挨拶",
        )

        assert dialogue.conversation_id == conv_id
        assert dialogue.sequence == 10
        assert dialogue.speaker == "主人公"
        assert dialogue.text == "こんにちは"
        assert dialogue.purpose == "挨拶"
        assert dialogue.trigger_id is None
        assert dialogue.emotion_state is None
        assert dialogue.is_deleted is False

    def test_dialogue_entry_with_trigger(self):
        """トリガー付き会話エントリのテスト"""
        conv_id = ConversationID(1, 1, 2)
        trigger_id = ConversationID(1, 1, 1)

        dialogue = DialogueEntry(
            conversation_id=conv_id,
            sequence=20,
            speaker="ヒロイン",
            text="あなたは誰？",
            trigger_id=trigger_id,
            emotion_state="困惑",
        )

        assert dialogue.trigger_id == trigger_id
        assert dialogue.emotion_state == "困惑"

    def test_dialogue_entry_string_format(self):
        """会話エントリの文字列表現テスト"""
        conv_id = ConversationID(1, 1, 1)
        dialogue = DialogueEntry(
            conversation_id=conv_id,
            sequence=10,
            speaker="主人公",
            text="これは長い台詞です。" * 10,
        )

        str_repr = str(dialogue)
        assert "[EP001-SC01-DL001]" in str_repr
        assert "主人公:" in str_repr
        assert "..." in str_repr  # 50文字でカットされる


class TestConversationScene:
    """ConversationSceneのテストクラス"""

    def test_create_conversation_scene(self):
        """会話シーンの作成テスト"""
        scene = ConversationScene(
            scene_id="EP001_SC01",
            episode_number=1,
            scene_number=1,
            location="学校の教室",
            time="放課後",
            purpose="初対面",
        )

        assert scene.scene_id == "EP001_SC01"
        assert scene.episode_number == 1
        assert scene.scene_number == 1
        assert scene.location == "学校の教室"
        assert scene.time == "放課後"
        assert scene.purpose == "初対面"
        assert len(scene.dialogues) == 0

    def test_add_dialogue_to_scene(self):
        """シーンに会話を追加するテスト"""
        scene = ConversationScene(
            scene_id="EP001_SC01",
            episode_number=1,
            scene_number=1,
        )

        conv_id1 = ConversationID(1, 1, 1)
        dialogue1 = DialogueEntry(
            conversation_id=conv_id1,
            sequence=10,
            speaker="主人公",
            text="こんにちは",
        )

        conv_id2 = ConversationID(1, 1, 2)
        dialogue2 = DialogueEntry(
            conversation_id=conv_id2,
            sequence=20,
            speaker="ヒロイン",
            text="こんにちは",
        )

        scene.add_dialogue(dialogue1)
        scene.add_dialogue(dialogue2)

        assert len(scene.dialogues) == 2
        assert scene.dialogues[0] == dialogue1
        assert scene.dialogues[1] == dialogue2

    def test_get_dialogue_range(self):
        """会話IDレンジの取得テスト"""
        scene = ConversationScene(
            scene_id="EP001_SC01",
            episode_number=1,
            scene_number=1,
        )

        # 会話がない場合
        start, end = scene.get_dialogue_range()
        assert start is None
        assert end is None

        # 会話を追加
        conv_id1 = ConversationID(1, 1, 1)
        dialogue1 = DialogueEntry(
            conversation_id=conv_id1,
            sequence=10,
            speaker="主人公",
            text="最初の台詞",
        )

        conv_id2 = ConversationID(1, 1, 3)
        dialogue2 = DialogueEntry(
            conversation_id=conv_id2,
            sequence=30,
            speaker="ヒロイン",
            text="最後の台詞",
        )

        conv_id3 = ConversationID(1, 1, 2)
        dialogue3 = DialogueEntry(
            conversation_id=conv_id3,
            sequence=20,
            speaker="主人公",
            text="中間の台詞",
        )

        scene.add_dialogue(dialogue1)
        scene.add_dialogue(dialogue2)
        scene.add_dialogue(dialogue3)

        # シーケンス順にソートされる
        start, end = scene.get_dialogue_range()
        assert start == conv_id1  # sequence=10
        assert end == conv_id2     # sequence=30

    def test_remove_dialogue_soft_delete(self):
        """会話のソフトデリートテスト"""
        scene = ConversationScene(
            scene_id="EP001_SC01",
            episode_number=1,
            scene_number=1,
        )

        conv_id = ConversationID(1, 1, 1)
        dialogue = DialogueEntry(
            conversation_id=conv_id,
            sequence=10,
            speaker="主人公",
            text="削除される台詞",
        )

        scene.add_dialogue(dialogue)
        assert dialogue.is_deleted is False

        # ソフトデリート実行
        scene.remove_dialogue(conv_id)
        assert dialogue.is_deleted is True

        # 物理的には残っている
        assert len(scene.dialogues) == 1
        assert scene.dialogues[0].is_deleted is True
