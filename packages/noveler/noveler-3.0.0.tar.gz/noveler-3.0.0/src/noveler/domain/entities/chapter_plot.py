"""章別プロットエンティティ

SPEC-PLOT-001: Claude Code連携プロット生成システム
"""

from dataclasses import dataclass, field
from typing import Any

from noveler.domain.value_objects.chapter_number import ChapterNumber


@dataclass
class ChapterPlot:
    """章別プロットエンティティ

    章別プロット情報を管理するドメインエンティティ。
    章番号、タイトル、キーイベント、エピソード構成等を含む。
    """

    chapter_number: ChapterNumber
    title: str
    summary: str
    # 互換性フィールド（従来テストとの互換性のためオプション化）
    episode_range: tuple[int, int] | None = None
    key_events: list[str] = field(default_factory=list)
    character_arcs: dict[str, Any] = field(default_factory=dict)
    foreshadowing_elements: dict[str, Any] = field(default_factory=dict)
    # 主要フィールド
    episodes: list[dict[str, Any]] = field(default_factory=list)
    central_theme: str = "General narrative"
    viewpoint_management: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """互換性とデフォルト初期化処理"""
        # episode_range が与えられ、episodes が空なら自動生成
        if not self.episodes and self.episode_range:
            start, end = self.episode_range
            if start <= end:
                self.episodes = [
                    {"episode_number": i, "title": f"第{i:03d}話"} for i in range(start, end + 1)
                ]

    def get_episode_info(self, episode_number: int) -> dict[str, Any] | None:
        """指定されたエピソードの情報を取得

        Args:
            episode_number: エピソード番号

        Returns:
            dict[str, Any] | None: エピソード情報(存在しない場合はNone)
        """
        for episode in self.episodes:
            if episode.get("episode_number") == episode_number:
                return episode
        return None

    def contains_episode(self, episode_number: int) -> bool:
        """指定されたエピソードがこの章に含まれているかチェック

        Args:
            episode_number: エピソード番号

        Returns:
            bool: 含まれている場合True
        """
        return self.get_episode_info(episode_number) is not None

    def get_context_for_episode(self, episode_number: int) -> dict[str, Any] | None:
        """指定されたエピソード用のコンテキスト情報を取得

        Claude Code連携時に使用するコンテキスト情報を構築する。
        章の情報とエピソード固有の情報を組み合わせて返す。

        Args:
            episode_number: エピソード番号

        Returns:
            dict[str, Any] | None: コンテキスト情報(エピソードが存在しない場合はNone)
        """
        episode_info = self.get_episode_info(episode_number)
        if episode_info is None:
            return None

        return {
            "chapter_info": {
                "chapter_number": self.chapter_number.value,
                "title": self.title,
                "summary": self.summary,
                "central_theme": self.central_theme,
                "key_events": self.key_events.copy(),
                "viewpoint_management": self.viewpoint_management.copy(),
            },
            "episode_info": episode_info.copy(),
            "all_episodes": [ep.copy() for ep in self.episodes],
        }

    def get_plot_generation_context(self, episode_number: int) -> dict[str, Any] | None:
        """プロット生成用の詳細コンテキストを取得

        Claude Codeでのプロット生成時に必要な全ての情報を構造化して返す。

        Args:
            episode_number: エピソード番号

        Returns:
            dict[str, Any] | None: プロット生成用コンテキスト
        """
        base_context = self.get_context_for_episode(episode_number)
        if base_context is None:
            return None

        # プロット生成用の追加情報を付与
        base_context["generation_context"] = {
            "target_episode": episode_number,
            "chapter_position": self._get_episode_position_in_chapter(episode_number),
            "previous_episodes": self._get_previous_episodes(episode_number),
            "following_episodes": self._get_following_episodes(episode_number),
        }

        return base_context

    def _get_episode_position_in_chapter(self, episode_number: int) -> dict[str, Any]:
        """章内でのエピソード位置情報を取得"""
        episode_numbers = [ep["episode_number"] for ep in self.episodes if "episode_number" in ep]
        episode_numbers.sort()

        if episode_number not in episode_numbers:
            return {"position": "unknown", "total": len(episode_numbers)}

        position = episode_numbers.index(episode_number) + 1
        return {
            "position": position,
            "total": len(episode_numbers),
            "is_first": position == 1,
            "is_last": position == len(episode_numbers),
        }

    def _get_previous_episodes(self, episode_number: int) -> list[dict[str, Any]]:
        """前のエピソード情報を取得"""
        return [ep for ep in self.episodes if ep.get("episode_number", 0) < episode_number]

    def _get_following_episodes(self, episode_number: int) -> list[dict[str, Any]]:
        """後のエピソード情報を取得"""
        return [ep for ep in self.episodes if ep.get("episode_number", 0) > episode_number]
