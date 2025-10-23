"""エピソード完了のユースケース"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from noveler.application.use_cases.check_episode_quality import CheckEpisodeQualityCommand
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.writing.entities import Episode, WritingRecord
from noveler.domain.writing.value_objects import WritingPhase

if TYPE_CHECKING:
    from noveler.application.use_cases.check_episode_quality import CheckEpisodeQualityUseCase
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.writing_record_repository import WritingRecordRepository

# JSTタイムゾーン
JST = ProjectTimezone.jst().timezone

# 品質スコア閾値
QUALITY_SCORE_THRESHOLD = 70.0


@dataclass(frozen=True)
class CompleteEpisodeCommand:
    """エピソード完了コマンド"""

    episode_id: str
    perform_quality_check: bool = True
    auto_advance_phase: bool = True


@dataclass(frozen=True)
class CompleteEpisodeResult:
    """エピソード完了結果"""

    success: bool
    episode: Episode | None = None
    quality_score: float | None = None
    message: str | None = None
    error_message: str | None = None


class CompleteEpisodeUseCase:
    """エピソード完了ユースケース"""

    def __init__(
        self,
        episode_repository: "EpisodeRepository",
        writing_record_repository: "WritingRecordRepository",
        quality_check_use_case: "CheckEpisodeQualityUseCase",
    ) -> None:
        self.episode_repository = episode_repository
        self.writing_record_repository = writing_record_repository
        self.quality_check_use_case = quality_check_use_case

    def _find_and_validate_episode(self, episode_id: str) -> Episode | None:
        """エピソードを取得し検証する

        Args:
            episode_id: エピソードID

        Returns:
            エピソード または None
        """
        return self.episode_repository.find_by_id(episode_id)

    def _perform_quality_check(self, command: CompleteEpisodeCommand, episode: Episode) -> CompleteEpisodeResult | None:
        """品質チェックを実行

        Args:
            command: コマンド
            episode: エピソード

        Returns:
            品質チェック結果 または None(続行時)
        """
        if not command.perform_quality_check:
            return None

        quality_result = self.quality_check_use_case.execute(
            CheckEpisodeQualityCommand(
                project_id=episode.project_id,
                episode_id=episode.id,
                content=episode.content,
                auto_fix=False,
            ),
        )

        if not quality_result.success or not quality_result.report:
            return None

        quality_score = quality_result.report.calculate_score().value

        # 品質スコアが低い場合の処理
        if quality_score < QUALITY_SCORE_THRESHOLD and not command.auto_advance_phase:
            message = f"品質スコアが低いです({quality_score:.1f}点)。推敲を推奨します。"
            return CompleteEpisodeResult(
                success=True,
                episode=episode,
                quality_score=quality_score,
                message=message,
            )

        # 品質チェック成功を示す結果を返す
        return CompleteEpisodeResult(
            success=True,
            quality_score=quality_score,
            message="品質チェック成功",
        )

    def _advance_episode_phase(self, episode: Episode) -> None:
        """エピソードのフェーズを進める

        Args:
            episode: エピソード
        """
        current_phase = episode.phase
        episode.advance_phase()

        # 執筆記録を作成
        writing_record = WritingRecord(
            episode_id=episode.id,
            phase=current_phase,
            started_at=episode.updated_at,
            ended_at=project_now().datetime,
            word_count_after=episode.word_count,
            notes=f"{current_phase.value}フェーズ完了",
        )

        # 終了処理
        writing_record.end_session(episode.word_count)
        self.writing_record_repository.save(writing_record)

    def _create_completion_message(self, episode: Episode, quality_score: float) -> str:
        """完了メッセージを作成

        Args:
            episode: エピソード
            quality_score: 品質スコア

        Returns:
            完了メッセージ
        """
        message_parts = self._get_phase_completion_messages(episode.phase)

        if quality_score is not None:
            message_parts.append(f"品質スコア: {quality_score:.1f}")

        return " ".join(message_parts)

    def _get_phase_completion_messages(self, phase: WritingPhase) -> list[str]:
        """フェーズ完了メッセージを取得

        Args:
            phase: 執筆フェーズ

        Returns:
            フェーズ完了メッセージのリスト
        """
        phase_messages = {
            WritingPhase.REVISION: ["下書きが完了しました。推敲フェーズに移行しました。"],
            WritingPhase.FINAL_CHECK: ["推敲が完了しました。最終チェックフェーズに移行しました。"],
            WritingPhase.PUBLISHED: ["最終チェックが完了しました。公開可能な状態です。"],
        }

        return phase_messages.get(phase, [])

    def execute(self, command: CompleteEpisodeCommand) -> CompleteEpisodeResult:
        """エピソード完了処理を実行"""
        try:
            # エピソードを取得・検証
            episode = self._find_and_validate_episode(command.episode_id)
            if not episode:
                return CompleteEpisodeResult(
                    success=False,
                    error_message="エピソードが見つかりません",
                )

            # 品質チェックを実行
            quality_result = self._perform_quality_check(command, episode)
            if quality_result and not quality_result.success:
                return quality_result

            quality_score = quality_result.quality_score if quality_result else None

            # フェーズを進める
            if command.auto_advance_phase:
                self._advance_episode_phase(episode)

            # エピソードを保存
            self.episode_repository.save(episode)

            # 完了メッセージの作成
            message = self._create_completion_message(episode, quality_score)

            return CompleteEpisodeResult(
                success=True,
                episode=episode,
                quality_score=quality_score,
                message=message,
            )

        except Exception as e:
            return CompleteEpisodeResult(
                success=False,
                error_message=f"エピソード完了処理中にエラーが発生しました: {e!s}",
            )
