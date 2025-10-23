"""会話ID関連のValue Objects

A38執筆プロンプトガイドのSTEP7で定義される会話ID体系を実装。
会話IDはエピソード番号、シーン番号、対話番号から構成される一意の識別子。
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConversationID:
    """会話ID（EP001-SC01-DL001形式）

    Attributes:
        episode_number: エピソード番号
        scene_number: シーン番号
        dialogue_number: 対話番号
    """

    episode_number: int
    scene_number: int
    dialogue_number: int

    def __str__(self) -> str:
        """文字列表現を返す

        Returns:
            EP001-SC01-DL001形式の文字列
        """
        return f"EP{self.episode_number:03d}-SC{self.scene_number:02d}-DL{self.dialogue_number:03d}"

    @classmethod
    def from_string(cls, conversation_id: str) -> "ConversationID":
        """文字列からConversationIDを生成

        Args:
            conversation_id: EP001-SC01-DL001形式の文字列

        Returns:
            ConversationIDインスタンス

        Raises:
            ValueError: 無効な形式の場合
        """
        parts = conversation_id.split("-")
        if len(parts) != 3:
            msg = f"Invalid conversation ID format: {conversation_id}"
            raise ValueError(msg)

        try:
            episode_num = int(parts[0][2:])
            scene_num = int(parts[1][2:])
            dialogue_num = int(parts[2][2:])
        except (ValueError, IndexError) as e:
            msg = f"Invalid conversation ID format: {conversation_id}"
            raise ValueError(msg) from e

        return cls(episode_num, scene_num, dialogue_num)


@dataclass
class DialogueEntry:
    """会話エントリ（STEP7の会話設計で使用）

    Attributes:
        conversation_id: 会話ID
        sequence: 表示順序（10刻みで設定、挿入余地を確保）
        speaker: 発話者
        text: 台詞内容
        trigger_id: トリガーとなった会話ID（オプション）
        purpose: 会話の目的
        emotion_state: 発話時の感情状態（オプション）
        is_deleted: ソフトデリート用フラグ
    """

    conversation_id: ConversationID
    sequence: int
    speaker: str
    text: str
    trigger_id: ConversationID | None = None
    purpose: str | None = None
    emotion_state: str | None = None
    is_deleted: bool = False

    def __str__(self) -> str:
        """文字列表現を返す"""
        return f"[{self.conversation_id}] {self.speaker}: {self.text[:50]}..."


@dataclass
class ConversationScene:
    """会話シーン（複数の会話エントリをグループ化）

    Attributes:
        scene_id: シーンID
        episode_number: エピソード番号
        scene_number: シーン番号
        dialogues: 会話エントリのリスト
        location: シーンの場所
        time: シーンの時刻
        purpose: シーンの目的
    """

    scene_id: str
    episode_number: int
    scene_number: int
    dialogues: list[DialogueEntry] = field(default_factory=list)
    location: str | None = None
    time: str | None = None
    purpose: str | None = None

    def get_dialogue_range(self) -> tuple[ConversationID | None, ConversationID | None]:
        """会話IDの範囲を取得

        Returns:
            (開始ID, 終了ID)のタプル
        """
        if not self.dialogues:
            return (None, None)

        sorted_dialogues = sorted(self.dialogues, key=lambda d: d.sequence)
        return (sorted_dialogues[0].conversation_id, sorted_dialogues[-1].conversation_id)

    def add_dialogue(self, dialogue: DialogueEntry) -> None:
        """会話エントリを追加

        Args:
            dialogue: 追加する会話エントリ
        """
        self.dialogues.append(dialogue)

    def remove_dialogue(self, conversation_id: ConversationID) -> None:
        """会話エントリをソフトデリート

        Args:
            conversation_id: 削除する会話のID
        """
        for dialogue in self.dialogues:
            if dialogue.conversation_id == conversation_id:
                dialogue.is_deleted = True
                break
