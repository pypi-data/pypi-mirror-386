#!/usr/bin/env python3

"""Domain.entities.episode
Where: Domain entity representing an episode.
What: Encapsulates episode metadata, content, and status.
Why: Provides a core aggregate for episode-related operations.
"""

from __future__ import annotations

"""エピソードエンティティ

Unitテスト (tests/unit/domain/plot_episode/entities/test_episode.py) に合わせた
ビジネスルールを実装する。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Iterable

from noveler.domain.exceptions import DomainException
from noveler.domain.value_objects.episode_number import EpisodeNumber
from noveler.domain.value_objects.episode_title import EpisodeTitle
from noveler.domain.value_objects.project_time import ProjectTimezone, project_now
from noveler.domain.value_objects.word_count import WordCount
from noveler.domain.value_objects.quality_score import QualityScore

# JSTタイムゾーン (プロジェクト共通)
JST = ProjectTimezone.jst().timezone


class EpisodeStatus(Enum):
    """エピソードステータス"""

    UNWRITTEN = "unwritten"
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEWED = "reviewed"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class Episode:
    """エピソードエンティティ"""

    number: EpisodeNumber
    title: EpisodeTitle
    content: str
    target_words: WordCount = field(default_factory=lambda: WordCount(2000))
    status: EpisodeStatus = field(default=EpisodeStatus.DRAFT)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    version: int = field(default=1)

    word_count: WordCount = field(init=False)
    _quality_score: QualityScore | None = field(default=None, init=False, repr=False)

    created_at: datetime = field(init=False)
    updated_at: datetime = field(init=False)
    completed_at: datetime | None = field(default=None, init=False)
    published_at: datetime | None = field(default=None, init=False)
    archived_at: datetime | None = field(default=None, init=False)

    # 外部責務 (DI用)
    _publisher: Any | None = field(default=None, init=False, repr=False)
    _quality_handler: Any | None = field(default=None, init=False, repr=False)
    _metadata_handler: Any | None = field(default=None, init=False, repr=False)

    _previous_status_before_archive: EpisodeStatus | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        # 型補正
        if isinstance(self.number, int):
            object.__setattr__(self, "number", EpisodeNumber(self.number))
        if isinstance(self.title, str):
            object.__setattr__(self, "title", EpisodeTitle(self.title))
        if isinstance(self.target_words, int):
            object.__setattr__(self, "target_words", WordCount(self.target_words))

        if isinstance(self.tags, Iterable) and not isinstance(self.tags, list):
            object.__setattr__(self, "tags", list(self.tags))
        object.__setattr__(self, "tags", [tag for tag in self.tags if isinstance(tag, str)])
        object.__setattr__(self, "metadata", dict(self.metadata))

        self._validate_invariants()

        now = project_now().datetime.astimezone(JST)
        object.__setattr__(self, "created_at", now)
        object.__setattr__(self, "updated_at", now)
        self.word_count = WordCount(len(self.content))

    # ------------------------------------------------------------------
    # 基本操作
    # ------------------------------------------------------------------
    def _validate_invariants(self) -> None:
        if self.number.value <= 0:
            raise DomainException("エピソード番号は1以上である必要があります", {"episode_number": self.number.value})
        if not self.title.value.strip():
            raise DomainException("タイトルは空にできません", {"title": self.title.value})
        if self.target_words.value <= 0:
            raise DomainException("目標文字数は1以上である必要があります", {"target_words": self.target_words.value})

    def _touch(self) -> None:
        object.__setattr__(self, "updated_at", project_now().datetime.astimezone(JST))

    # ------------------------------------------------------------------
    # 執筆フロー
    # ------------------------------------------------------------------
    def start_writing(self) -> None:
        if self.status in {EpisodeStatus.PUBLISHED, EpisodeStatus.ARCHIVED}:
            raise DomainException("公開済みのエピソードは編集できません", {"status": self.status.value})
        self.status = EpisodeStatus.IN_PROGRESS
        self._touch()

    def update_content(self, content: str) -> None:
        if self.status == EpisodeStatus.PUBLISHED:
            raise DomainException("公開済みのエピソードは編集できません")
        if not content or not content.strip():
            raise DomainException("内容は空にできません")

        self.content = content
        self.word_count = WordCount(len(content))
        self.version += 1
        if self.status == EpisodeStatus.UNWRITTEN:
            self.status = EpisodeStatus.DRAFT
        self._touch()

    def complete(self) -> None:
        if self.status == EpisodeStatus.PUBLISHED:
            raise DomainException("公開済みのエピソードは再完成できません")
        if not self.content.strip():
            raise DomainException("内容が空のエピソードは完成できません")

        self.status = EpisodeStatus.COMPLETED
        self.completed_at = project_now().datetime.astimezone(JST)
        self._touch()

    def review(self) -> None:
        if self.status != EpisodeStatus.COMPLETED:
            raise DomainException("完成したエピソードのみレビュー可能です")
        self.status = EpisodeStatus.REVIEWED
        self._touch()

    # ------------------------------------------------------------------
    # 品質・公開管理
    # ------------------------------------------------------------------
    def set_quality(self, handler: Any) -> None:
        self._quality_handler = handler

    def set_publisher(self, handler: Any) -> None:
        self._publisher = handler

    def set_metadata_handler(self, handler: Any) -> None:
        self._metadata_handler = handler

    def set_quality_score(self, score: float | QualityScore) -> None:
        if self.status == EpisodeStatus.UNWRITTEN:
            raise DomainException("未執筆のエピソードに品質スコアは設定できません")

        if isinstance(score, QualityScore):
            quality = score
        else:
            if not isinstance(score, (int, float)):
                raise DomainException("品質スコアは数値である必要があります", {"score": score})
            numeric = float(score)
            if not 0 <= numeric <= 100:
                raise DomainException("品質スコアは0から100の範囲である必要があります", {"score": score})
            quality = QualityScore(int(round(numeric)))

        self._quality_score = quality
        self._touch()

    @property
    def quality_score(self) -> QualityScore | None:
        return self._quality_score

    @quality_score.setter
    def quality_score(self, score: float | QualityScore) -> None:
        self.set_quality_score(score)

    def can_publish(self) -> bool:
        if self.status not in {EpisodeStatus.COMPLETED, EpisodeStatus.REVIEWED}:
            return False
        if not self.content.strip():
            return False
        if self.word_count.value < 1000:
            return False
        if not self._quality_score or self._quality_score.value < 70:
            return False
        return True

    def publish(self) -> None:
        if self.status not in {EpisodeStatus.COMPLETED, EpisodeStatus.REVIEWED}:
            raise DomainException("完成またはレビュー済みのエピソードのみ公開できます")
        if not self.can_publish():
            raise DomainException("公開条件を満たしていません")

        self.status = EpisodeStatus.PUBLISHED
        self.published_at = project_now().datetime.astimezone(JST)
        self._touch()

    # ------------------------------------------------------------------
    # 品質チェック
    # ------------------------------------------------------------------
    def completion_percentage(self) -> float:
        target = self.target_words.value
        if target <= 0:
            return 0.0
        percentage = (self.word_count.value / target) * 100
        percentage = min(percentage, 100.0)
        return round(percentage, 1)

    def is_ready_for_quality_check(self) -> bool:
        if self.status == EpisodeStatus.UNWRITTEN:
            return False
        if not self.content.strip():
            return False
        return self.word_count.value >= 1000

    def get_quality_check_issues(self) -> list[str]:
        issues: list[str] = []
        if not self.content.strip():
            issues.append("内容が空です")
        if self.word_count.value < 1000:
            issues.append("1000文字未満です")
        if self.status == EpisodeStatus.UNWRITTEN:
            issues.append("未執筆状態です")
        return issues

    # ------------------------------------------------------------------
    # タグ / メタデータ
    # ------------------------------------------------------------------
    def add_tag(self, tag: str) -> None:
        if not tag or not str(tag).strip():
            raise DomainException("タグは空にできません")
        normalized = str(tag).strip()
        if normalized not in self.tags:
            self.tags.append(normalized)
        self._touch()

    def remove_tag(self, tag: str) -> None:
        normalized = str(tag).strip()
        if normalized in self.tags:
            self.tags.remove(normalized)
            self._touch()

    def set_metadata(self, key: str, value: Any) -> None:
        if not key or not str(key).strip():
            raise DomainException("メタデータのキーは空にできません")
        self.metadata[str(key).strip()] = value
        self._touch()

    def get_metadata(self, key: str, default: Any | None = None) -> Any | None:
        return self.metadata.get(key, default)

    # ------------------------------------------------------------------
    # アーカイブ
    # ------------------------------------------------------------------
    def archive(self) -> None:
        if self.status == EpisodeStatus.PUBLISHED:
            raise DomainException("公開済みのエピソードはアーカイブできません")
        if self.status == EpisodeStatus.ARCHIVED:
            return

        self._previous_status_before_archive = self.status
        self.status = EpisodeStatus.ARCHIVED
        self.archived_at = project_now().datetime.astimezone(JST)
        self._touch()

    def restore_from_archive(self) -> None:
        if self.status != EpisodeStatus.ARCHIVED:
            raise DomainException("アーカイブされていないエピソードは復元できません")

        previous = self._previous_status_before_archive or EpisodeStatus.DRAFT
        self.status = previous
        self.archived_at = None
        self._previous_status_before_archive = None
        self._touch()

    # ------------------------------------------------------------------
    # 統計
    # ------------------------------------------------------------------
    def get_writing_statistics(self) -> dict[str, Any]:
        today = project_now().datetime.astimezone(JST)
        days = max(1, (today.date() - self.created_at.date()).days + 1)
        words_per_day = self.word_count.value / days if days else 0

        return {
            "word_count": self.word_count.value,
            "target_words": self.target_words.value,
            "completion_percentage": self.completion_percentage(),
            "version": self.version,
            "writing_days": days,
            "words_per_day": round(words_per_day, 2),
            "status": self.status.value,
            "quality_score": self._quality_score.value if self._quality_score else None,
            "tags": list(self.tags),
            "is_publishable": self.can_publish(),
        }

    # ------------------------------------------------------------------
    # Python Magic Methods
    # ------------------------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Episode):
            return False
        return self.number.value == other.number.value

    def __hash__(self) -> int:
        return hash(self.number.value)

    def __str__(self) -> str:
        return f"Episode({self.number.value})"

    def __repr__(self) -> str:
        return (
            "Episode(number={number}, title='{title}', status={status}, word_count={count})".format(
                number=self.number.value,
                title=self.title.value,
                status=self.status.value,
                count=self.word_count.value,
            )
        )


class EpisodeFactory:
    """Episodeファクトリー"""

    @staticmethod
    def create_new_episode(number: int, title: str, target_words: int = 3000) -> Episode:
        return Episode(
            number=EpisodeNumber(number),
            title=EpisodeTitle(title),
            content="",
            target_words=WordCount(target_words),
            status=EpisodeStatus.UNWRITTEN,
        )

    @staticmethod
    def create_from_template(template: dict[str, Any]) -> Episode:
        tags = template.get("tags", [])
        metadata = template.get("metadata", {})
        episode = Episode(
            number=EpisodeNumber(template["number"]),
            title=EpisodeTitle(template["title"]),
            content=template.get("content", ""),
            target_words=WordCount(template.get("target_words", 3000)),
            status=EpisodeStatus(template.get("status", EpisodeStatus.UNWRITTEN.value)),
            tags=list(tags) if tags else [],
            metadata=dict(metadata) if metadata else {},
        )
        return episode
