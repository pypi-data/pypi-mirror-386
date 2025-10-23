#!/usr/bin/env python3
"""Service responsible for constructing domain entities while preserving purity."""

from noveler.domain.entities.episode import Episode, EpisodeFactory
from noveler.domain.entities.episode_metadata import EpisodeMetadata
from noveler.domain.entities.episode_publisher import EpisodePublisher
from noveler.domain.entities.episode_quality import EpisodeQuality
from noveler.domain.interfaces.logger_service import ILoggerService, NullLoggerService


class DomainEntityFactoryService:
    """Coordinate creation of domain entities with explicit dependency injection."""

    def __init__(self, logger_service: ILoggerService | None = None) -> None:
        """Initialize the factory with an optional logger service."""
        self.logger_service = logger_service or NullLoggerService()

    def create_episode_publisher(self, episode_id: str) -> EpisodePublisher:
        """Instantiate an ``EpisodePublisher`` wired with the configured logger."""
        return EpisodePublisher(episode_id, self.logger_service)

    def create_episode_quality(self, episode_id: str) -> EpisodeQuality:
        """Instantiate an ``EpisodeQuality`` with injected logger dependencies."""
        return EpisodeQuality(episode_id, self.logger_service)

    def create_episode_metadata(self, episode_id: str) -> EpisodeMetadata:
        """Instantiate an ``EpisodeMetadata`` with injected logger dependencies."""
        return EpisodeMetadata(episode_id, self.logger_service)

    def create_episode(self, number: int, title: str, target_words: int = 3000) -> Episode:
        """Create a new ``Episode`` entity and inject its sub-entities."""
        episode = EpisodeFactory.create_new_episode(number, title, target_words)

        # Sub-entitiesのDI注入をApplication層で管理
        self._inject_sub_entities(episode)

        return episode

    def _inject_sub_entities(self, episode: Episode) -> None:
        """Inject dependent sub-entities while keeping domain code infrastructure-free."""
        episode_id = str(episode.number.value)

        # Private fieldsに直接設定（Domain純粋性のため）
        episode._publisher = self.create_episode_publisher(episode_id)
        episode._quality = self.create_episode_quality(episode_id)
        episode._metadata = self.create_episode_metadata(episode_id)
