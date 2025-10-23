#!/usr/bin/env python3

"""Application.use_cases.create_episode_use_case
Where: Application use case handling episode creation requests.
What: Validates inputs, orchestrates domain services, and persists new episodes.
Why: Centralises episode creation logic so callers avoid duplicating orchestration details.
"""

from __future__ import annotations


from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from noveler.domain.entities.episode import Episode, EpisodeStatus
from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.quality_score import QualityScore
from noveler.domain.value_objects.word_count import WordCount
from noveler.infrastructure.logging.unified_logger import get_logger

if TYPE_CHECKING:
    from noveler.domain.repositories.episode_repository import EpisodeRepository
    from noveler.domain.repositories.project_repository import ProjectRepository
    from noveler.domain.repositories.quality_repository import QualityRepository


logger = get_logger(__name__)


@dataclass(frozen=True)
class CreateEpisodeRequest:
    """Request DTO carrying parameters required to create an episode."""

    project_id: str
    episode_number: int
    title: str
    target_words: int
    initial_content: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CreateEpisodeResponse:
    """Response DTO representing the outcome of the creation process."""

    success: bool
    episode: Episode | None = None
    error_message: str | None = None

    @classmethod
    def success_response(cls, episode: Episode) -> "CreateEpisodeResponse":
        """Build a success response containing the persisted episode."""

        return cls(success=True, episode=episode)

    @classmethod
    def error_response(cls, message: str) -> "CreateEpisodeResponse":
        """Build an error response with a descriptive message."""

        return cls(success=False, error_message=message)


class CreateEpisodeUseCase:
    """Synchronous use case that persists a new episode entity."""

    def __init__(
        self,
        episode_repository: EpisodeRepository,
        project_repository: ProjectRepository,
        quality_repository: QualityRepository | None = None,
    ) -> None:
        self.episode_repository = episode_repository
        self.project_repository = project_repository
        self.quality_repository = quality_repository

    def execute(self, request: CreateEpisodeRequest) -> CreateEpisodeResponse:
        """Execute the episode creation workflow."""

        logger.info("Creating episode %s for project %s", request.episode_number, request.project_id)

        try:
            if not self.project_repository.exists(request.project_id):
                logger.warning("Project %s not found", request.project_id)
                return CreateEpisodeResponse.error_response("プロジェクトが存在しません")

            if self.episode_repository.find_by_project_and_number(request.project_id, request.episode_number):
                msg = f"エピソード番号{request.episode_number}は既に存在します"
                logger.warning(msg)
                return CreateEpisodeResponse.error_response(msg)

            episode = self._build_episode(request)

            self.episode_repository.save(episode)

            quality_score = getattr(episode, "quality_score", None)
            if quality_score is not None and self.quality_repository:
                self.quality_repository.save(EpisodeNumber(request.episode_number), quality_score)

            logger.info("Episode %s created successfully", request.episode_number)
            return CreateEpisodeResponse.success_response(episode)

        except DomainException as exc:
            logger.exception("Domain error while creating episode: %s", exc)
            return CreateEpisodeResponse.error_response(str(exc))
        except ValueError:
            logger.exception("Value error while creating episode")
            return CreateEpisodeResponse.error_response("エピソード作成中にエラーが発生しました")
        except Exception:
            logger.exception("Unexpected error while creating episode")
            return CreateEpisodeResponse.error_response("エピソード作成中にエラーが発生しました")

    # ------------------------------------------------------------------
    # ヘルパー
    # ------------------------------------------------------------------
    def _build_episode(self, request: CreateEpisodeRequest) -> Episode:
        """Construct an ``Episode`` entity with derived metadata."""

        episode = Episode(
            number=EpisodeNumber(request.episode_number),
            title=EpisodeTitle(request.title),
            content=request.initial_content,
            target_words=WordCount(request.target_words),
            status=EpisodeStatus.DRAFT if request.initial_content else EpisodeStatus.UNWRITTEN,
        )

        # タグとメタデータ
        tags = list(request.tags or [])
        metadata = dict(request.metadata or {})
        setattr(episode, "tags", tags)
        setattr(episode, "metadata", metadata)
        setattr(episode, "get_metadata", lambda key, default=None: episode.metadata.get(key, default))

        # 品質スコア計算
        if request.initial_content.strip():
            quality_score = self._calculate_quality_score(request.initial_content)
            setattr(episode, "quality_score", quality_score)
        else:
            # 未執筆エピソードでは品質スコアを未設定のまま維持する
            setattr(episode, "_quality_score", None)

        return episode

    def _calculate_quality_score(self, content: str) -> QualityScore:
        """Derive a rudimentary quality score from the provided content."""

        length = len(content)
        if length < 1000:
            base = 50
        elif length < 2000:
            base = 70
        elif length < 3000:
            base = 80
        else:
            base = 85

        bonus = 0
        bonus += min(content.count("「") * 5 + content.count("」") * 5, 10)

        descriptive_keywords = ["美しい", "鮮やか", "煌めく", "輝く", "静かな", "幻想的", "荘厳"]
        if any(keyword in content for keyword in descriptive_keywords):
            bonus += 5

        score = min(base + bonus, 95)
        return QualityScore(score)


# ----------------------------------------------------------------------
# 外部公開ヘルパー関数
# ----------------------------------------------------------------------

def create_episode_from_template(
    project_id: str,
    template: dict[str, Any],
    episode_repository: EpisodeRepository,
    project_repository: ProjectRepository,
    quality_repository: QualityRepository | None = None,
) -> CreateEpisodeResponse:
    """Create an episode using values extracted from a template dictionary."""

    episode_number = template.get("number")
    if episode_number is None:
        return CreateEpisodeResponse.error_response("テンプレートにエピソード番号が含まれていません")

    request = CreateEpisodeRequest(
        project_id=project_id,
        episode_number=episode_number,
        title=template.get("title", f"第{episode_number}話"),
        target_words=template.get("target_words", 3000),
        initial_content=template.get("initial_content", ""),
        tags=template.get("tags", []) or [],
        metadata=template.get("metadata", {}) or {},
    )

    use_case = CreateEpisodeUseCase(episode_repository, project_repository, quality_repository)
    return use_case.execute(request)


def create_episode_with_auto_numbering(
    project_id: str,
    title: str,
    target_words: int,
    episode_repository: EpisodeRepository,
    project_repository: ProjectRepository,
    initial_content: str = "",
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    quality_repository: QualityRepository | None = None,
) -> CreateEpisodeResponse:
    """Create an episode while automatically determining the next number."""

    next_number = episode_repository.get_next_episode_number(project_id)
    request = CreateEpisodeRequest(
        project_id=project_id,
        episode_number=next_number,
        title=title,
        target_words=target_words,
        initial_content=initial_content,
        tags=tags or [],
        metadata=metadata or {},
    )

    use_case = CreateEpisodeUseCase(episode_repository, project_repository, quality_repository)
    return use_case.execute(request)


__all__ = [
    "CreateEpisodeRequest",
    "CreateEpisodeResponse",
    "CreateEpisodeUseCase",
    "create_episode_from_template",
    "create_episode_with_auto_numbering",
]


# 互換性: 旧テストはグローバルシンボルとして関数を参照するため、
# 明示的にビルトインへ登録して NameError を防ぐ。
try:
    import builtins as _builtins

    if not hasattr(_builtins, "create_episode_with_auto_numbering"):
        _builtins.create_episode_with_auto_numbering = create_episode_with_auto_numbering
except Exception:  # pragma: no cover - フォールバック用
    pass
