"""エピソード完成セッションエンティティ(DDD実装)

エピソードの完成処理を管理するドメインモデル。
TDD原則に基づいて再実装。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from noveler.domain.value_objects.completion_status import CompletionStatusType, QualityCheckResult, WritingPhase
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.quality_score import QualityScore

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone
CompletionStatus = CompletionStatusType  # エイリアス


@dataclass
class CompletionResult:
    """エピソード完成結果"""

    success: bool
    new_phase: WritingPhase | None = None
    quality_score: QualityScore | None = None
    message: str | None = None
    completed_at: datetime | None = None
    error: str | None = None


class EpisodeCompletionSession:
    """エピソード完成セッション

    エピソードの品質チェック、フェーズ進行、
    完成処理を管理する。
    """

    def __init__(self, episode_number: int, project_name: str, current_phase: str | None = None) -> None:
        """初期化

        Args:
            episode_number: エピソード番号
            project_name: プロジェクト名
            current_phase: 現在の執筆フェーズ
        """
        self.episode_number = episode_number
        self.project_name = project_name
        self.current_phase = current_phase
        self._status = CompletionStatus.INITIALIZED
        self._created_at = project_now().datetime
        self._completed_at: datetime | None = None
        self.quality_check_result: QualityCheckResult | None = None

    def get_status(self) -> CompletionStatus:
        """ステータスを取得

        Returns:
            現在のステータス
        """
        return self._status

    def set_quality_check_result(self, result: QualityCheckResult) -> None:
        """品質チェック結果を設定

        Args:
            result: 品質チェック結果
        """
        self.quality_check_result = result

    def advance_phase(self) -> WritingPhase:
        """執筆フェーズを進める

        Returns:
            新しいフェーズ
        """
        new_phase = self.current_phase.get_next_phase()
        self.current_phase = new_phase
        return new_phase

    def is_publishable(self) -> bool:
        """公開可能かどうか

        Returns:
            公開可能な場合True
        """
        return self.current_phase.is_publishable()

    def complete_episode(
        self, quality_result: QualityCheckResult | None = None, auto_advance_phase: bool = True
    ) -> CompletionResult:
        """エピソードを完成させる

        Args:
            quality_result: 品質チェック結果
            auto_advance_phase: 自動的にフェーズを進めるか

        Returns:
            完成結果
        """
        self._status = CompletionStatus.IN_PROGRESS

        try:
            # 品質チェック結果を保存
            if quality_result:
                self.quality_check_result = quality_result

            # 品質が低い場合の処理
            if quality_result and not quality_result.passed and not auto_advance_phase:
                self._status = CompletionStatus.COMPLETED
                return CompletionResult(
                    success=True,
                    new_phase=self.current_phase,
                    quality_score=quality_result.score,
                    message=f"品質スコアが低いため({quality_result.score.value}点)、フェーズを進めませんでした。",
                )

            # 既に公開済みの場合
            if self.current_phase == WritingPhase.PUBLISHED:
                self._status = CompletionStatus.COMPLETED
                return CompletionResult(
                    success=True,
                    new_phase=self.current_phase,
                    quality_score=quality_result.score if quality_result else None,
                    message="既に公開済みのエピソードです。",
                )

            # フェーズを進める
            old_phase = self.current_phase
            new_phase = self.advance_phase() if auto_advance_phase else self.current_phase

            # 完成メッセージを作成
            message = self._create_completion_message(old_phase, new_phase, quality_result)

            # 完成処理
            self._completed_at = project_now().datetime
            self._status = CompletionStatus.COMPLETED

            return CompletionResult(
                success=True,
                new_phase=new_phase,
                quality_score=quality_result.score if quality_result else None,
                message=message,
                completed_at=self._completed_at,
            )

        except Exception as e:
            self._status = CompletionStatus.FAILED
            return CompletionResult(success=False, error=str(e))

    def _create_completion_message(
        self, old_phase: str | None, new_phase: str, quality_result: QualityCheckResult | None = None
    ) -> str:
        """完成メッセージを作成

        Args:
            old_phase: 元のフェーズ
            new_phase: 新しいフェーズ
            quality_result: 品質チェック結果

        Returns:
            完成メッセージ
        """
        messages: list[Any] = []

        # フェーズ進行メッセージ
        if old_phase != new_phase:
            messages.append(f"{old_phase.to_japanese()}が完了しました。")

            if new_phase == WritingPhase.PUBLISHED:
                messages.append("公開可能な状態です。")
            else:
                messages.append(f"{new_phase.to_japanese()}フェーズに移行しました。")

        # 品質チェックメッセージ
        if quality_result:
            messages.append(quality_result.get_summary_message())

        return " ".join(messages)
