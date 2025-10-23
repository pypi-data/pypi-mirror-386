#!/usr/bin/env python3
# File: src/noveler/domain/value_objects/quality_report.py
# Purpose: Model aggregate quality report snapshots for manuscript analysis workflows.
# Context: Consumed by quality services, repositories, and tests requiring mutable report data.

"""品質レポート値オブジェクト

品質チェック結果の要約を保持するデータ構造。
問題エピソードや改善提案を含み、テストでの利便性を考慮して可変とする。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class _SuggestionText(str):
    """UTF-8バイト長を返す文字列サブクラス。"""

    def __len__(self) -> int:  # pragma: no cover - 単純処理
        return len(self.encode("utf-8"))


@dataclass
class QualityReport:
    """品質レポートのスナップショット。"""

    project_name: str
    total_episodes: int
    average_score: float
    problematic_episodes: list[int] | None = None
    suggestions: list[_SuggestionText] | None = None

    def __post_init__(self) -> None:
        if self.problematic_episodes is not None:
            self.problematic_episodes = [int(ep) for ep in self.problematic_episodes]
        if self.suggestions is not None:
            self.suggestions = [_SuggestionText(str(text)) for text in self.suggestions]

    @classmethod
    def from_iterables(
        cls,
        project_name: str,
        total_episodes: int,
        average_score: float,
        problematic_episodes: Iterable[int] | None = None,
        suggestions: Iterable[str] | None = None,
    ) -> "QualityReport":
        return cls(
            project_name=project_name,
            total_episodes=total_episodes,
            average_score=average_score,
            problematic_episodes=list(problematic_episodes) if problematic_episodes is not None else None,
            suggestions=list(suggestions) if suggestions is not None else None,
        )

    def issues_count(self) -> int:
        return len(self.problematic_episodes) if self.problematic_episodes is not None else 0

    def suggestions_count(self) -> int:
        return len(self.suggestions) if self.suggestions is not None else 0

    def __str__(self) -> str:
        return (
            "QualityReport("
            f"project_name='{self.project_name}', "
            f"total_episodes={self.total_episodes}, "
            f"average_score={self.average_score}, "
            f"problematic_episodes={self.problematic_episodes}, "
            f"suggestions={self.suggestions}"
            ")"
        )

    def __repr__(self) -> str:  # pragma: no cover - __str__と同一
        return self.__str__()

    def to_dict(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "total_episodes": self.total_episodes,
            "average_score": self.average_score,
            "problematic_episodes": None if self.problematic_episodes is None else list(self.problematic_episodes),
            "suggestions": None if self.suggestions is None else list(self.suggestions),
        }

    def __hash__(self) -> int:
        problems = None if self.problematic_episodes is None else tuple(self.problematic_episodes)
        suggestions = None if self.suggestions is None else tuple(self.suggestions)
        return hash((self.project_name, self.total_episodes, self.average_score, problems, suggestions))
