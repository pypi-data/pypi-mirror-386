"""Application Use Case: Track Writing Progress
執筆進捗追跡ユースケース

プロジェクト全体の進捗状況を分析・管理
"""

from dataclasses import dataclass
from typing import Any

from noveler.domain.repositories.episode_repository import EpisodeRepository
from noveler.domain.repositories.writing_record_repository import WritingRecordRepository
from noveler.domain.writing.entities import EpisodeStatus


@dataclass(frozen=True)
class ProgressQuery:
    """進捗クエリ"""

    project_id: str
    include_detailed_stats: bool = False


@dataclass
class EpisodeProgress:
    """エピソード進捗情報"""

    episode_number: int
    title: str
    status: EpisodeStatus
    word_count: int
    target_word_count: int
    completion_rate: float
    can_publish: bool


@dataclass
class ProjectProgress:
    """プロジェクト進捗"""

    project_id: str
    total_episodes: int
    completed_episodes: int
    in_progress_episodes: int
    publishable_episodes: int
    completion_rate: float
    total_words: int
    next_episode_to_write: int | None
    episode_details: list[EpisodeProgress]
    writing_velocity: float | None = None  # 文字/日


class TrackWritingProgressUseCase:
    """執筆進捗追跡ユースケース

    ビジネス要求:
    - プロジェクト全体の進捗状況を把握
    - 各エピソードの完成度を分析
    - 執筆ペースの測定
    - 次に取り組むべきエピソードの特定
    """

    def __init__(self, episode_repository: EpisodeRepository, session_repository: WritingRecordRepository) -> None:
        """コンストラクタ。

        進捗追跡に必要なリポジトリを依存性注入で設定する。

        Args:
            episode_repository: エピソードリポジトリ
            session_repository: 執筆セッションリポジトリ
        """
        self.episode_repository = episode_repository
        self.session_repository = session_repository

    def execute(self, query: ProgressQuery) -> ProjectProgress:
        """進捗追跡を実行"""
        # 全エピソード取得
        episodes = self.episode_repository.find_all_by_project(query.project_id)

        if not episodes:
            return self._create_empty_progress(query.project_id)

        # 基本統計計算
        stats = self._calculate_basic_stats(episodes)

        # エピソード詳細情報
        episode_details = []
        if query.include_detailed_stats:
            episode_details = self._create_episode_details(episodes)

        # 執筆速度計算
        writing_velocity = None
        if query.include_detailed_stats:
            writing_velocity = self._calculate_writing_velocity(query.project_id)

        # 次のエピソード特定
        next_episode = self._find_next_episode_to_write(episodes)

        return ProjectProgress(
            project_id=query.project_id,
            total_episodes=stats["total"],
            completed_episodes=stats["completed"],
            in_progress_episodes=stats["in_progress"],
            publishable_episodes=stats["publishable"],
            completion_rate=stats["completion_rate"],
            total_words=stats["total_words"],
            next_episode_to_write=next_episode,
            episode_details=episode_details,
            writing_velocity=writing_velocity,
        )

    def _calculate_basic_stats(self, episodes: list[Any]) -> dict[str, Any]:
        """基本統計を計算"""
        total = len(episodes)
        completed = len([ep for ep in episodes if ep.status in [EpisodeStatus.REVISED, EpisodeStatus.PUBLISHED]])
        in_progress = len([ep for ep in episodes if ep.status == EpisodeStatus.IN_PROGRESS])
        publishable = len([ep for ep in episodes if ep.can_publish()])

        total_words = sum(ep.word_count.value if ep.word_count else 0 for ep in episodes)

        completion_rate = (completed / total) * 100.0 if total > 0 else 0.0

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "publishable": publishable,
            "completion_rate": completion_rate,
            "total_words": total_words,
        }

    def _create_episode_details(self, episodes: list[Any]) -> list[EpisodeProgress]:
        """エピソード詳細情報を作成"""
        details: list[Any] = []

        for episode in sorted(episodes, key=lambda ep: ep.number.value):
            word_count = episode.word_count.value if episode.word_count else 0
            target_count = episode.get_target_word_count()
            completion_rate = episode.get_completion_rate()

            details.append(
                EpisodeProgress(
                    episode_number=episode.episode_number.value,
                    title=episode.title.value if episode.title else "",
                    status=episode.status,
                    word_count=word_count,
                    target_word_count=target_count,
                    completion_rate=completion_rate,
                    can_publish=episode.can_publish(),
                ),
            )

        return details

    def _calculate_writing_velocity(self, project_id: str) -> float | None:
        """執筆速度を計算(文字/日)"""
        try:
            # 過去30日間のセッション取得
            recent_sessions = self.session_repository.find_recent_sessions(
                project_id,
                days=30,
            )

            if not recent_sessions:
                return None

            # 日別の執筆文字数を集計
            daily_words = {}
            for session in recent_sessions:
                date_key = session.date
                if date_key not in daily_words:
                    daily_words[date_key] = 0
                daily_words[date_key] += session.get_total_words_written()

            if not daily_words:
                return None

            # 平均文字数/日を計算
            total_words = sum(daily_words.values())
            days_count = len(daily_words)

            return total_words / days_count

        except (ValueError, ZeroDivisionError):
            return None

    def _find_next_episode_to_write(self, episodes: list[Any]) -> int | None:
        """次に執筆すべきエピソードを特定"""
        # 未執筆エピソードを話数順にソート
        unwritten = [ep for ep in episodes if ep.status == EpisodeStatus.UNWRITTEN]

        if not unwritten:
            return None

        # 最も早い話数を返す
        next_episode = min(unwritten, key=lambda ep: ep.episode_number.value)
        return next_episode.episode_number.value

    def _create_empty_progress(self, project_id: str) -> ProjectProgress:
        """空のプロジェクト用の進捗情報を作成"""
        return ProjectProgress(
            project_id=project_id,
            total_episodes=0,
            completed_episodes=0,
            in_progress_episodes=0,
            publishable_episodes=0,
            completion_rate=0.0,
            total_words=0,
            next_episode_to_write=None,
            episode_details=[],
        )
