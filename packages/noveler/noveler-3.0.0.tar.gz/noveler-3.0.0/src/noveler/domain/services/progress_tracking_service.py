"""TDD-driven Progress Tracker
テスト駆動開発による進捗追跡
"""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class WritingProgress:
    """執筆進捗データ"""

    total_episodes: int
    written_episodes: int
    completion_rate: float


class ProgressTracker:
    """進捗追跡クラス(TDD実装)"""

    def calculate_progress(self, plot_episodes: list[dict], written_files: Sequence[str]) -> WritingProgress:
        """執筆進捗を計算"""
        total = len(plot_episodes)
        written = len(written_files)

        completion_rate = 0.0 if total == 0 else round(written / total * 100, 1)

        return WritingProgress(
            total_episodes=total,
            written_episodes=written,
            completion_rate=completion_rate,
        )

    def find_next_episode(self, plot_episodes: list[dict], written_files: Sequence[str]) -> str | None:
        """次に執筆すべきエピソードを特定"""
        written_set = set(written_files)

        for episode in sorted(plot_episodes, key=lambda x: x.get("episode_number", "999")):
            episode_num = str(episode.get("episode_number", ""))
            if episode_num not in written_set:
                return episode_num

        return None

    def estimate_word_count(self, content: str) -> int:
        """文字数を推定(メタ情報除外)"""
        # 実際の小説本文のみを抽出
        lines = content.split("\n")
        novel_lines = []

        for line in lines:
            stripped_line = line.strip()
            # 除外すべき行
            if stripped_line.startswith(("#", "**", "---", "- ")) or stripped_line == "":
                continue
            novel_lines.append(stripped_line)

        # 実際の小説部分のみを結合
        novel_content = "".join(novel_lines)
        return len(novel_content)
