"""前話情報コンテキストエンティティ"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from noveler.domain.value_objects.episode_number import EpisodeNumber

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class CharacterState:
    """キャラクター状態情報"""

    character_name: str
    emotional_state: str
    current_relationships: dict[str, str] = field(default_factory=dict)
    character_development_stage: str = ""
    key_attributes: list[str] = field(default_factory=list)

    def to_yaml_dict(self) -> dict[str, Any]:
        """YAML形式の辞書に変換"""
        return {
            "character_name": self.character_name,
            "emotional_state": self.emotional_state,
            "current_relationships": self.current_relationships,
            "character_development_stage": self.character_development_stage,
            "key_attributes": self.key_attributes,
        }


@dataclass
class StoryProgressionState:
    """ストーリー進行状態"""

    main_plot_developments: list[str] = field(default_factory=list)
    subplot_progressions: dict[str, str] = field(default_factory=dict)
    resolved_conflicts: list[str] = field(default_factory=list)
    active_foreshadowing: list[str] = field(default_factory=list)
    story_momentum: str = "normal"  # low, normal, high, climactic

    def to_yaml_dict(self) -> dict[str, Any]:
        """YAML形式の辞書に変換"""
        return {
            "main_plot_developments": self.main_plot_developments,
            "subplot_progressions": self.subplot_progressions,
            "resolved_conflicts": self.resolved_conflicts,
            "active_foreshadowing": self.active_foreshadowing,
            "story_momentum": self.story_momentum,
        }


@dataclass
class TechnicalLearningState:
    """技術学習進捗状態"""

    mastered_concepts: list[str] = field(default_factory=list)
    current_learning_focus: str = ""
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced
    practical_applications: list[str] = field(default_factory=list)
    next_learning_targets: list[str] = field(default_factory=list)

    def to_yaml_dict(self) -> dict[str, Any]:
        """YAML形式の辞書に変換"""
        return {
            "mastered_concepts": self.mastered_concepts,
            "current_learning_focus": self.current_learning_focus,
            "difficulty_level": self.difficulty_level,
            "practical_applications": self.practical_applications,
            "next_learning_targets": self.next_learning_targets,
        }


class PreviousEpisodeContext:
    """前話情報コンテキストエンティティ

    前話から抽出した情報を構造化して保持し、
    次話のプロンプト生成に必要なコンテキストを提供する。
    """

    def __init__(self, current_episode_number: EpisodeNumber) -> None:
        """前話情報コンテキスト初期化

        Args:
            current_episode_number: 現在のエピソード番号
        """
        self.current_episode_number = current_episode_number
        self.previous_episode_number = current_episode_number.previous() if current_episode_number.value > 1 else None
        self.character_states: dict[str, CharacterState] = {}
        self.story_progression = StoryProgressionState()
        self.technical_learning = TechnicalLearningState()
        self.emotional_flow: list[str] = []
        self.unresolved_elements: list[str] = []
        self.scene_continuity_notes: list[str] = []
        self.extracted_at = datetime.now(timezone.utc)
        self.source_manuscript_path: Path | None = None
        self.log_messages: list[dict[str, str]] = []

    def add_character_state(self, character_state: CharacterState) -> None:
        """キャラクター状態を追加

        Args:
            character_state: キャラクター状態情報
        """
        self.character_states[character_state.character_name] = character_state

    def get_character_state(self, character_name: str) -> CharacterState | None:
        """指定キャラクターの状態取得

        Args:
            character_name: キャラクター名

        Returns:
            キャラクター状態情報、または None
        """
        return self.character_states.get(character_name)

    def update_story_progression(self, story_progression: StoryProgressionState) -> None:
        """ストーリー進行状態更新

        Args:
            story_progression: 新しいストーリー進行状態
        """
        self.story_progression = story_progression

    def update_technical_learning(self, technical_learning: TechnicalLearningState) -> None:
        """技術学習状態更新

        Args:
            technical_learning: 新しい技術学習状態
        """
        self.technical_learning = technical_learning

    def add_emotional_flow_element(self, element: str) -> None:
        """感情的流れ要素追加

        Args:
            element: 感情的流れ要素
        """
        self.emotional_flow.append(element)

    def add_unresolved_element(self, element: str) -> None:
        """未解決要素追加

        Args:
            element: 未解決要素
        """
        self.unresolved_elements.append(element)

    def add_scene_continuity_note(self, note: str) -> None:
        """シーン継続性ノート追加

        Args:
            note: シーン継続性ノート
        """
        self.scene_continuity_notes.append(note)

    def get_contextual_summary(self) -> str:
        """コンテキスト要約取得

        Returns:
            前話情報の要約文字列
        """
        if not self.previous_episode_number:
            return "第1話のため前話情報は存在しません。"

        summary_parts = [
            f"前話（第{self.previous_episode_number.value:03d}話）情報:",
            f"主要キャラクター数: {len(self.character_states)}",
            f"ストーリー展開: {self.story_progression.story_momentum}",
            f"技術学習段階: {self.technical_learning.difficulty_level}",
            f"未解決要素: {len(self.unresolved_elements)}件",
        ]

        return "\n".join(summary_parts)

    def has_sufficient_context(self) -> bool:
        """十分なコンテキスト情報があるかチェック

        Returns:
            十分なコンテキスト情報があるかどうか
        """
        return (
            len(self.character_states) > 0
            or len(self.story_progression.main_plot_developments) > 0
            or len(self.technical_learning.mastered_concepts) > 0
        )

    def to_yaml_dict(self) -> dict[str, Any]:
        """YAML形式の辞書に変換

        Returns:
            YAML形式の辞書
        """
        result = {
            "current_episode_number": self.current_episode_number.value,
            "extracted_at": self.extracted_at.isoformat(),
            "character_states": {name: state.to_yaml_dict() for name, state in self.character_states.items()},
            "story_progression": self.story_progression.to_yaml_dict(),
            "technical_learning": self.technical_learning.to_yaml_dict(),
            "emotional_flow": self.emotional_flow,
            "unresolved_elements": self.unresolved_elements,
            "scene_continuity_notes": self.scene_continuity_notes,
        }

        if self.previous_episode_number:
            result["previous_episode_number"] = self.previous_episode_number.value

        if self.source_manuscript_path:
            result["source_manuscript_path"] = str(self.source_manuscript_path)

        return result
