#!/usr/bin/env python3
"""詳細評価セッション エンティティ

A31詳細評価プロセスを管理するメインエンティティ。
手動Claude Code分析と同等の詳細フィードバックを生成する。
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from noveler.domain.entities.category_analysis_result import CategoryAnalysisResult
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.line_specific_feedback import LineSpecificFeedback


class EvaluationSessionStatus(Enum):
    """評価セッション状態"""

    PENDING = "pending"  # 評価待機中
    IN_PROGRESS = "in_progress"  # 評価実行中
    COMPLETED = "completed"  # 評価完了
    FAILED = "failed"  # 評価失敗


class SessionId:
    """セッション識別子バリューオブジェクト"""

    def __init__(self, value: str) -> None:
        """セッションID初期化

        Args:
            value: UUID文字列
        """
        if not value or not isinstance(value, str):
            msg = "セッションIDは空でない文字列である必要があります"
            raise ValueError(msg)
        self._value = value

    @classmethod
    def generate(cls) -> "SessionId":
        """新しいセッションIDを生成

        Returns:
            SessionId: 新しいセッションID
        """
        return cls(str(uuid.uuid4()))

    @property
    def value(self) -> str:
        """セッションID値を取得

        Returns:
            str: セッションID文字列
        """
        return self._value

    def __eq__(self, other: Any) -> bool:
        """等価性比較"""
        if isinstance(other, SessionId):
            return self._value == other._value
        if isinstance(other, str):
            return self._value == other
        return False

    def __hash__(self) -> int:
        """ハッシュ値計算"""
        return hash(self._value)

    def __str__(self) -> str:
        """文字列表現"""
        return self._value


class DetailedEvaluationSession:
    """詳細評価セッション エンティティ

    A31チェックリストに基づく詳細評価プロセスを管理する。
    手動Claude Code分析と同等の詳細度を実現する。
    """

    def __init__(
        self,
        session_id: SessionId,
        project_name: str,
        episode_number: EpisodeNumber,
        episode_content: str,
        created_at: datetime,
        status: EvaluationSessionStatus = EvaluationSessionStatus.PENDING,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        overall_score: float | None = None,
        error_message: str | None = None,
    ) -> None:
        """詳細評価セッション初期化

        Args:
            session_id: セッション識別子
            project_name: プロジェクト名
            episode_number: エピソード番号
            episode_content: エピソード内容
            created_at: 作成日時
            status: 評価状態
            started_at: 開始日時
            completed_at: 完了日時
            overall_score: 総合スコア
            error_message: エラーメッセージ
        """
        self._session_id = session_id
        self._project_name = project_name
        self._episode_number = episode_number
        self._episode_content = episode_content
        self._created_at = created_at
        self._status = status
        self._started_at = started_at
        self._completed_at = completed_at
        self._overall_score = overall_score
        self._error_message = error_message

        # 評価結果コレクション
        self._category_analyses: list[CategoryAnalysisResult] = []
        self._line_feedbacks: list[LineSpecificFeedback] = []

    @classmethod
    def create(
        cls,
        project_name: str,
        episode_number: EpisodeNumber,
        episode_content: str,
    ) -> "DetailedEvaluationSession":
        """新しい詳細評価セッションを作成

        Args:
            project_name: プロジェクト名
            episode_number: エピソード番号
            episode_content: エピソード内容

        Returns:
            DetailedEvaluationSession: 新しいセッション

        Raises:
            ValueError: エピソード内容が空の場合
        """
        if not episode_content or not episode_content.strip():
            msg = "エピソード内容は空にできません"
            raise ValueError(msg)

        return cls(
            session_id=SessionId.generate(),
            project_name=project_name,
            episode_number=episode_number,
            episode_content=episode_content,
            created_at=datetime.now(timezone.utc),
        )

    @classmethod
    def _create_with_id(
        cls,
        session_id: SessionId,
        project_name: str,
        episode_number: EpisodeNumber,
        episode_content: str,
        status: EvaluationSessionStatus,
        created_at: datetime,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        overall_score: float | None = None,
    ) -> "DetailedEvaluationSession":
        """既存IDでセッションを再構築（リポジトリ専用）

        Args:
            session_id: 既存のセッションID
            project_name: プロジェクト名
            episode_number: エピソード番号
            episode_content: エピソード内容
            status: 評価状態
            created_at: 作成日時
            started_at: 開始日時
            completed_at: 完了日時
            overall_score: 総合スコア

        Returns:
            DetailedEvaluationSession: 再構築されたセッション
        """
        return cls(
            session_id=session_id,
            project_name=project_name,
            episode_number=episode_number,
            episode_content=episode_content,
            created_at=created_at,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            overall_score=overall_score,
        )

    def start_evaluation(self) -> None:
        """評価を開始

        Raises:
            ValueError: 既に評価が開始されている場合
        """
        if self._status != EvaluationSessionStatus.PENDING:
            msg = "評価は既に開始されています"
            raise ValueError(msg)

        self._status = EvaluationSessionStatus.IN_PROGRESS
        self._started_at = datetime.now(timezone.utc)

    def add_category_analysis(self, analysis: CategoryAnalysisResult) -> None:
        """カテゴリ分析結果を追加

        Args:
            analysis: カテゴリ分析結果

        Raises:
            ValueError: セッションが失敗状態の場合
        """
        if self._status == EvaluationSessionStatus.FAILED:
            msg = "失敗したセッションには結果を追加できません"
            raise ValueError(msg)

        self._category_analyses.append(analysis)

    def add_line_feedback(self, feedback: LineSpecificFeedback) -> None:
        """行別フィードバックを追加

        Args:
            feedback: 行別フィードバック

        Raises:
            ValueError: セッションが失敗状態の場合
        """
        if self._status == EvaluationSessionStatus.FAILED:
            msg = "失敗したセッションには結果を追加できません"
            raise ValueError(msg)

        self._line_feedbacks.append(feedback)

    def complete_evaluation(self) -> None:
        """評価を完了

        総合スコアを計算し、セッションを完了状態にする。
        """
        if self._category_analyses:
            scores = [analysis.score for analysis in self._category_analyses]
            self._overall_score = sum(scores) / len(scores)
        else:
            self._overall_score = 0.0

        self._status = EvaluationSessionStatus.COMPLETED
        self._completed_at = datetime.now(timezone.utc)

    def fail_evaluation(self, error_message: str) -> None:
        """評価を失敗状態にする

        Args:
            error_message: エラーメッセージ
        """
        self._status = EvaluationSessionStatus.FAILED
        self._error_message = error_message
        self._completed_at = datetime.now(timezone.utc)

    def get_execution_time(self) -> float:
        """実行時間を取得（秒）

        Returns:
            float: 実行時間（秒）、まだ完了していない場合は0.0
        """
        if self._started_at is None or self._completed_at is None:
            return 0.0

        return (self._completed_at - self._started_at).total_seconds()

    # プロパティ
    @property
    def session_id(self) -> SessionId:
        """セッションID"""
        return self._session_id

    @property
    def project_name(self) -> str:
        """プロジェクト名"""
        return self._project_name

    @property
    def episode_number(self) -> EpisodeNumber:
        """エピソード番号"""
        return self._episode_number

    @property
    def episode_content(self) -> str:
        """エピソード内容"""
        return self._episode_content

    @property
    def status(self) -> EvaluationSessionStatus:
        """評価状態"""
        return self._status

    @property
    def created_at(self) -> datetime:
        """作成日時"""
        return self._created_at

    @property
    def started_at(self) -> datetime | None:
        """開始日時"""
        return self._started_at

    @property
    def completed_at(self) -> datetime | None:
        """完了日時"""
        return self._completed_at

    @property
    def overall_score(self) -> float | None:
        """総合スコア"""
        return self._overall_score

    @property
    def error_message(self) -> str | None:
        """エラーメッセージ"""
        return self._error_message

    @property
    def category_analyses(self) -> list[CategoryAnalysisResult]:
        """カテゴリ分析結果リスト"""
        return self._category_analyses.copy()

    @property
    def line_feedbacks(self) -> list[LineSpecificFeedback]:
        """行別フィードバックリスト"""
        return self._line_feedbacks.copy()

    def __eq__(self, other: Any) -> bool:
        """等価性比較"""
        if not isinstance(other, DetailedEvaluationSession):
            return False
        return self._session_id == other._session_id

    def __hash__(self) -> int:
        """ハッシュ値計算"""
        return hash(self._session_id)
