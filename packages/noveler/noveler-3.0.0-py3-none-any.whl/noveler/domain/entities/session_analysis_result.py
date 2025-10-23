#!/usr/bin/env python3
"""セッション分析結果エンティティ

Claude Codeセッション内での分析実行結果を管理し、
A31チェックリスト統合のためのビジネスロジックを提供する。
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from noveler.domain.entities.a31_priority_item import A31PriorityItem


class AnalysisStatus(Enum):
    """分析ステータス列挙型"""

    PENDING = "pending"  # 分析待機中
    IN_PROGRESS = "in_progress"  # 分析実行中
    COMPLETED = "completed"  # 分析完了
    FAILED = "failed"  # 分析失敗
    PARTIAL = "partial"  # 部分完了


class AnalysisConfidence(Enum):
    """分析信頼度レベル"""

    LOW = "low"  # 信頼度低（手動確認推奨）
    MEDIUM = "medium"  # 信頼度中（注意して適用）
    HIGH = "high"  # 信頼度高（安全に適用可能）
    VERIFIED = "verified"  # 検証済み（完全信頼）


@dataclass(frozen=True)
class SessionAnalysisId:
    """セッション分析ID バリューオブジェクト"""

    value: str

    def __post_init__(self) -> None:
        """ID妥当性検証"""
        if not self.value or not self.value.strip():
            msg = "セッション分析IDは空にできません"
            raise ValueError(msg)


@dataclass(frozen=True)
class AnalysisImprovement:
    """分析改善提案 バリューオブジェクト"""

    original_text: str
    improved_text: str
    improvement_type: str
    confidence: AnalysisConfidence
    reasoning: str

    def __post_init__(self) -> None:
        """改善提案妥当性検証"""
        if not self.original_text.strip() or not self.improved_text.strip():
            msg = "改善提案のテキストは空にできません"
            raise ValueError(msg)

        if self.original_text == self.improved_text:
            msg = "改善前後のテキストが同一です"
            raise ValueError(msg)


@dataclass
class ItemAnalysisResult:
    """項目別分析結果 バリューオブジェクト"""

    priority_item: A31PriorityItem
    analysis_score: float
    status: AnalysisStatus
    confidence: AnalysisConfidence
    improvements: list[AnalysisImprovement]
    issues_found: list[str]
    execution_time: float
    error_message: str | None = None

    def __post_init__(self) -> None:
        """分析結果妥当性検証"""
        if not 0.0 <= self.analysis_score <= 10.0:
            msg = "分析スコアは0.0から10.0の範囲である必要があります"
            raise ValueError(msg)

        if self.execution_time < 0:
            msg = "実行時間は負の値にできません"
            raise ValueError(msg)

    def is_successful(self) -> bool:
        """分析成功判定"""
        return self.status in [AnalysisStatus.COMPLETED, AnalysisStatus.PARTIAL]

    def has_high_confidence(self) -> bool:
        """高信頼度判定"""
        return self.confidence in [AnalysisConfidence.HIGH, AnalysisConfidence.VERIFIED]

    def get_improvement_count(self) -> int:
        """改善提案数取得"""
        return len(self.improvements)

    def get_high_confidence_improvements(self) -> list[AnalysisImprovement]:
        """高信頼度改善提案のみ取得"""
        return [
            improvement
            for improvement in self.improvements
            if improvement.confidence in [AnalysisConfidence.HIGH, AnalysisConfidence.VERIFIED]
        ]


class SessionAnalysisResult:
    """セッション分析結果エンティティ

    Claude Codeセッション内での重点項目分析結果を統合管理し、
    A31チェックリストへの反映とトレーサビリティを提供する。
    """

    def __init__(
        self,
        analysis_id: SessionAnalysisId,
        project_name: str,
        episode_number: int,
        manuscript_path: str,
        total_priority_items: int,
        created_at: datetime | None = None,
    ) -> None:
        """セッション分析結果初期化

        Args:
            analysis_id: 分析セッション識別ID
            project_name: プロジェクト名
            episode_number: エピソード番号
            manuscript_path: 分析対象原稿パス
            total_priority_items: 分析対象重点項目総数
            created_at: 作成日時
        """
        self._analysis_id = analysis_id
        self._project_name = project_name
        self._episode_number = episode_number
        self._manuscript_path = manuscript_path
        self._total_priority_items = total_priority_items
        self._created_at = created_at or datetime.now(timezone.utc)

        # 分析結果管理
        self._item_results: dict[str, ItemAnalysisResult] = {}
        self._overall_status = AnalysisStatus.PENDING
        self._started_at: datetime | None = None
        self._completed_at: datetime | None = None

        # 統計情報
        self._total_execution_time = 0.0
        self._successful_analyses = 0
        self._failed_analyses = 0

    @classmethod
    def create_new(
        cls,
        project_name: str,
        episode_number: int,
        manuscript_path: str,
        total_priority_items: int,
    ) -> "SessionAnalysisResult":
        """新規セッション分析結果作成"""
        analysis_id = SessionAnalysisId(str(uuid.uuid4()))
        return cls(
            analysis_id=analysis_id,
            project_name=project_name,
            episode_number=episode_number,
            manuscript_path=manuscript_path,
            total_priority_items=total_priority_items,
        )

    def start_analysis(self) -> None:
        """分析開始"""
        if self._overall_status != AnalysisStatus.PENDING:
            msg = "分析は既に開始されています"
            raise ValueError(msg)

        self._overall_status = AnalysisStatus.IN_PROGRESS
        self._started_at = datetime.now(timezone.utc)

    def add_item_analysis_result(self, result: ItemAnalysisResult) -> None:
        """項目別分析結果追加"""
        if self._overall_status != AnalysisStatus.IN_PROGRESS:
            msg = "分析が進行中でないため結果を追加できません"
            raise ValueError(msg)

        item_id = result.priority_item.item_id.value
        self._item_results[item_id] = result

        # 統計更新
        self._total_execution_time += result.execution_time
        if result.is_successful():
            self._successful_analyses += 1
        else:
            self._failed_analyses += 1

    def complete_analysis(self) -> None:
        """分析完了"""
        if self._overall_status != AnalysisStatus.IN_PROGRESS:
            msg = "分析が進行中でないため完了できません"
            raise ValueError(msg)

        self._completed_at = datetime.now(timezone.utc)

        # 総合ステータス決定
        if self._failed_analyses == 0:
            self._overall_status = AnalysisStatus.COMPLETED
        elif self._successful_analyses > 0:
            self._overall_status = AnalysisStatus.PARTIAL
        else:
            self._overall_status = AnalysisStatus.FAILED

    def get_completion_rate(self) -> float:
        """完了率計算"""
        if self._total_priority_items == 0:
            return 0.0
        return len(self._item_results) / self._total_priority_items

    def get_success_rate(self) -> float:
        """成功率計算"""
        total_results = len(self._item_results)
        if total_results == 0:
            return 0.0
        return self._successful_analyses / total_results

    def get_average_analysis_score(self) -> float:
        """平均分析スコア計算"""
        successful_results = [result for result in self._item_results.values() if result.is_successful()]

        if not successful_results:
            return 0.0

        total_score = sum(result.analysis_score for result in successful_results)
        return total_score / len(successful_results)

    def get_total_improvements(self) -> int:
        """総改善提案数取得"""
        return sum(result.get_improvement_count() for result in self._item_results.values())

    def get_high_confidence_improvements(self) -> list[tuple[A31PriorityItem, AnalysisImprovement]]:
        """高信頼度改善提案一覧取得"""
        high_confidence_improvements = []

        for result in self._item_results.values():
            for improvement in result.get_high_confidence_improvements():
                high_confidence_improvements.append((result.priority_item, improvement))

        return high_confidence_improvements

    def generate_analysis_summary(self) -> dict[str, Any]:
        """分析サマリー生成"""
        return {
            "analysis_id": self._analysis_id.value,
            "project_name": self._project_name,
            "episode_number": self._episode_number,
            "overall_status": self._overall_status.value,
            "completion_rate": self.get_completion_rate(),
            "success_rate": self.get_success_rate(),
            "average_score": self.get_average_analysis_score(),
            "total_improvements": self.get_total_improvements(),
            "high_confidence_improvements": len(self.get_high_confidence_improvements()),
            "execution_time": self._total_execution_time,
            "created_at": self._created_at.isoformat(),
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
        }

    # プロパティ
    @property
    def analysis_id(self) -> SessionAnalysisId:
        """分析ID"""
        return self._analysis_id

    @property
    def project_name(self) -> str:
        """プロジェクト名"""
        return self._project_name

    @property
    def episode_number(self) -> int:
        """エピソード番号"""
        return self._episode_number

    @property
    def overall_status(self) -> AnalysisStatus:
        """総合ステータス"""
        return self._overall_status

    @property
    def item_results(self) -> dict[str, ItemAnalysisResult]:
        """項目別結果"""
        return self._item_results.copy()

    def __eq__(self, other: object) -> bool:
        """同値性判定（IDベース）"""
        if not isinstance(other, SessionAnalysisResult):
            return False
        return self._analysis_id == other._analysis_id

    def __hash__(self) -> int:
        """ハッシュ値計算（IDベース）"""
        return hash(self._analysis_id)

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return (
            f"SessionAnalysisResult("
            f"id={self._analysis_id.value[:8]}, "
            f"status={self._overall_status.name}, "
            f"completion={self.get_completion_rate():.1%})"
        )
