#!/usr/bin/env python3
"""プロット分析エンティティ

プロット分析のライフサイクルを管理する
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from noveler.domain.ai_integration.value_objects.analysis_result import AnalysisResult
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone


@dataclass
class PlotAnalysis:
    """プロット分析エンティティ

    分析の識別子、対象ファイル、分析日時、結果を管理
    """

    id: str
    plot_file_path: str
    created_at: datetime | None = None
    analyzed_at: datetime | None = None
    result: AnalysisResult | None = field(default=None)

    def __post_init__(self) -> None:
        """Ensure temporal metadata is populated for legacy call sites."""
        if self.created_at is None:
            self.created_at = project_now().datetime
        if self.analyzed_at is None:
            self.analyzed_at = self.created_at

    def __hash__(self) -> int:
        """idと分析対象ファイルパスによるハッシュ値を生成"""
        return hash((self.id, self.plot_file_path))

    @classmethod
    def create(cls, plot_file_path: str) -> "PlotAnalysis":
        """新しいプロット分析を作成"""
        now = project_now().datetime
        return cls(
            id=f"analysis_{uuid4().hex[:8]}",
            plot_file_path=plot_file_path,
            created_at=now,
            analyzed_at=now,
            result=None,
        )

    def set_result(self, result: AnalysisResult) -> None:
        """分析結果を設定"""
        if self.result is not None:
            msg = "分析結果は既に設定されています"
            raise ValueError(msg)
        self.result = result

    def is_analyzed(self) -> bool:
        """分析が完了しているかどうか"""
        return self.result is not None

    def get_elapsed_time(self) -> float:
        """分析開始からの経過時間(秒)"""
        reference = self.analyzed_at or project_now().datetime
        return (project_now().datetime - reference).total_seconds()

    def __eq__(self, other: object) -> bool:
        """IDによる同一性判定"""
        if not isinstance(other, PlotAnalysis):
            return False
        return self.id == other.id
