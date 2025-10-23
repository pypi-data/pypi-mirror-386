"""Domain.value_objects.episode_completion_data
Where: Domain value object module defining typed data structures.
What: Declares dataclasses and helpers used to pass structured domain data.
Why: Keeps domain data definitions consistent across services and entities.
"""

#!/usr/bin/env python3
from __future__ import annotations

"""エピソード完成データ値オブジェクト
話数管理.yaml自動同期機能のドメイン層
"""


from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from noveler.domain.exceptions import ValidationError
from noveler.domain.value_objects.project_time import ProjectTimezone

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass(frozen=True)
class EpisodeCompletionData:
    """エピソード完成データ値オブジェクト"""

    project_name: str
    episode_number: int
    completion_status: str
    quality_score: float
    quality_grade: str
    word_count: int
    revision_count: int
    completion_date: datetime
    quality_check_results: dict[str, Any]

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.episode_number <= 0:
            msg = "エピソード番号は1以上である必要があります"
            raise ValidationError(msg)

        if not 0 <= self.quality_score <= 100:
            msg = "品質スコアは0から100の範囲である必要があります"
            raise ValidationError(msg)

        if self.word_count < 0:
            msg = "文字数は0以上である必要があります"
            raise ValidationError(msg)

        if self.revision_count < 0:
            msg = "修正回数は0以上である必要があります"
            raise ValidationError(msg)

        # セキュリティ:不正な文字のチェック
        if any(char in self.project_name for char in ["<", ">", "&", '"', "'"]):
            msg = "不正な文字が含まれています"
            raise ValidationError(msg)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "completion_status": self.completion_status,
            "completion_date": self._to_naive_iso(self.completion_date),
            "quality_score": self.quality_score,
            "quality_grade": self.quality_grade,
            "word_count": self.word_count,
            "revision_count": self.revision_count,
            "last_updated": self._to_naive_iso(datetime.now(timezone.utc)),
            "quality_check_results": self.quality_check_results,
        }

    @staticmethod
    def _to_naive_iso(value: datetime) -> str:
        """タイムゾーン情報を持つ場合でもナイーブISO文字列に変換する"""
        dt = value
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.isoformat()
